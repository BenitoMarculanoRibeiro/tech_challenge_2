import json
import boto3
import os
import tempfile
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import uuid
 
stepfunctions = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]
 
s3 = boto3.client('s3')
 
BUCKET = os.environ["BRONZE_BUCKET"]
PREFIX = 'meta_alfabetizacao_brasil/'
 
 
def lambda_handler(event, context):
    try:
        # Extrai o metas do evento (ajuste conforme a estrutura real do seu event)
        # Exemplos comuns:
        # metas = event.get('detail', {}).get('detail', {})
        # ou metas = event.get('metas', {})
        # ou metas = event  (se o próprio event for o payload)
        print(event)
        metas = event.get('detail', {}).get('detail', event.get('metas', event))
       
        if not metas:
            raise ValueError("Nenhum dado 'metas' encontrado no evento")
 
        # Converte para DataFrame
        # Se metas for um dicionário único → transforma em lista de 1 registro
        if isinstance(metas, dict):
            df = pd.DataFrame([metas])
        elif isinstance(metas, list):
            df = pd.DataFrame(metas)
        else:
            raise ValueError(f"Formato de 'metas' não suportado: {type(metas)}")
 
        # Gera nome do arquivo com timestamp
        filename = f"meta_alfabetizacao_brasil.parquet"
        s3_key = f"{PREFIX}metas/{filename}"
 
        # Escreve o Parquet em um arquivo temporário
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
            tmp_path = tmp.name
            df.to_parquet(tmp_path, engine='pyarrow', index=False)
 
        # Faz upload para o S3
        s3.upload_file(tmp_path, BUCKET, s3_key)
 
        # Remove o arquivo temporário
        os.unlink(tmp_path)
 
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"realtime-{uuid.uuid4()}",
            input=json.dumps({
                "origem": "api-gateway",
                "evento": event
            })
        )
 
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Metas convertidas para Parquet e salvas no S3 com sucesso',
                'bucket': BUCKET,
                'key': s3_key,
                'rows': len(df),
                "executionArn": response["executionArn"]
            }, ensure_ascii=False)
        }
 
    except Exception as e:
        print(f"Erro: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            }, ensure_ascii=False)
        }
 
