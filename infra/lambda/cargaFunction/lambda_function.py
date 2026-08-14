
import json
import boto3
import os
import tempfile
import pandas as pd
from google.cloud import bigquery
import pyarrow as pa
import pyarrow.parquet as pq

s3 = boto3.client('s3')

BUCKET = 'fiap-tc-fase-2-bkt'
PREFIX = 'bronze/'

# Caminho correto do arquivo de credenciais
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/var/task/gac.json"

tables = ["municipio", "dicionario", "meta_alfabetizacao_brasil", "meta_alfabetizacao_municipio", "meta_alfabetizacao_uf", "alunos", "uf"]

CHUNK_SIZE = 10000


def _bigquery_field_to_arrow(field):
    field_type = field.field_type.upper()
    if field_type == 'STRING':
        return pa.large_string()
    if field_type == 'BYTES':
        return pa.binary()
    if field_type == 'INTEGER':
        return pa.int64()
    if field_type == 'FLOAT':
        return pa.float64()
    if field_type in {'NUMERIC', 'BIGNUMERIC', 'DECIMAL'}:
        return pa.float64()
    if field_type == 'BOOLEAN':
        return pa.bool_()
    if field_type == 'TIMESTAMP':
        return pa.timestamp('us')
    if field_type == 'DATE':
        return pa.date32()
    if field_type == 'DATETIME':
        return pa.timestamp('us')
    if field_type == 'TIME':
        return pa.large_string()
    if field_type == 'GEOGRAPHY':
        return pa.large_string()
    if field_type == 'RECORD':
        return pa.struct([
            pa.field(subfield.name, _bigquery_field_to_arrow(subfield), nullable=(subfield.mode != 'REQUIRED'))
            for subfield in field.fields
        ])
    return pa.large_string()


def _bigquery_schema_to_arrow(bq_schema):
    return pa.schema([
        pa.field(field.name, _bigquery_field_to_arrow(field), nullable=(field.mode != 'REQUIRED'))
        for field in bq_schema
    ])


def get_data_to_bigdata(table_id, key):
    client = bigquery.Client()

    query = f"SELECT * FROM basedosdados.br_inep_avaliacao_alfabetizacao.{table_id}"
    query_job = client.query(query)
    result = query_job.result(page_size=CHUNK_SIZE)

    local_file = tempfile.NamedTemporaryFile(prefix=f"{table_id}_", suffix=".parquet", delete=False)
    local_file_path = local_file.name
    local_file.close()

    writer = None
    try:
        bq_schema = getattr(result, 'schema', None) or getattr(query_job, 'schema', None)
        if bq_schema is None:
            raise RuntimeError('Não foi possível recuperar o schema do BigQuery para a tabela.')

        arrow_schema = _bigquery_schema_to_arrow(bq_schema)

        for chunk_index, df_chunk in enumerate(result.to_dataframe_iterable(), start=1):
            if df_chunk.empty:
                continue

            df_chunk = df_chunk.reset_index(drop=True)
            for field_name in arrow_schema.names:
                if field_name not in df_chunk.columns:
                    df_chunk[field_name] = pd.NA

            df_chunk = df_chunk[arrow_schema.names]
            table = pa.Table.from_pandas(df_chunk, schema=arrow_schema, preserve_index=False)

            if writer is None:
                writer = pq.ParquetWriter(local_file_path, arrow_schema, compression="snappy")

            writer.write_table(table)
            print(f"Chunk {chunk_index} escrito em {local_file_path}")

        if writer is None:
            raise ValueError(f"Nenhum dado retornado para a tabela {table_id}")

        with open(local_file_path, "rb") as f:
            s3.put_object(
                Bucket=BUCKET,
                Key=key,
                Body=f
            )

        print(f"Arquivo {key} gravado com sucesso no S3")
        return key
    finally:
        if writer is not None:
            writer.close()
        if os.path.exists(local_file_path):
            os.remove(local_file_path)

def lambda_handler(event, context):
    try:
        upload_results = {}
        for table_id in tables:
            key = f"{PREFIX}{table_id}.parquet"
            print(f"Processando tabela: {table_id}")
            uploaded_key = get_data_to_bigdata(table_id, key)
            upload_results[table_id] = uploaded_key
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Arquivos processados e salvos no S3 com sucesso',
                'bucket': BUCKET,
                'tables': upload_results
            })
        }
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }