import json
import os
import boto3
from io import BytesIO
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
 
s3 = boto3.client('s3')
 
BUCKET = os.environ["BRONZE_BUCKET"]
 
tables = ["municipio", "dicionario", "meta_alfabetizacao_brasil", "meta_alfabetizacao_municipio", "meta_alfabetizacao_uf", "alunos", "uf"]
 
def get_google_credentials():
    ssm = boto3.client("ssm")

    response = ssm.get_parameter(
        Name=os.environ["GOOGLE_CREDENTIALS_PARAMETER"],
        WithDecryption=True
    )

    google_credentials_json = json.loads(
        response["Parameter"]["Value"]
    )

    credentials = service_account.Credentials.from_service_account_info(
        google_credentials_json
    )

    return credentials

def get_data_to_bigdata(table_id, key):
    credentials = get_google_credentials()

    client = bigquery.Client(
        credentials=credentials,
        project=credentials.project_id
    )
    query = f"SELECT * FROM basedosdados.br_inep_avaliacao_alfabetizacao.{table_id}"
   
    # Otimização: usa a Storage API do Google Cloud se instalada (mais rápida)
    query_job = client.query(query)
    df = query_job.to_dataframe(create_bqstorage_client=True)
 
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer, engine="pyarrow", compression="snappy")
    parquet_buffer.seek(0)
 
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=parquet_buffer.getvalue()
    )
 
    # Cria o buffer parquet
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer, engine="pyarrow", compression="snappy")
   
    # Volta o ponteiro para o início do buffer (obrigatório!)
    parquet_buffer.seek(0)
 
    # Faz upload para o S3
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=parquet_buffer.getvalue()
    )
   
    print(f"Arquivo {key} gravado com sucesso no S3")
 
def lambda_handler(event, context):
    try:
        for table_id in tables:
            key = f"{table_id}/{table_id}.parquet"
            print(f"Processando tabela: {table_id}")
            get_data_to_bigdata(table_id, key)
       
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Arquivos processados e salvos no S3 com sucesso',
                'bucket': BUCKET,
                'tables': tables
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
