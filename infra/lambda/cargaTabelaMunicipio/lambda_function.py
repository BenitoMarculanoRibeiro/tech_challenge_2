import requests
import pandas as pd
import json
import boto3
from io import BytesIO

s3 = boto3.client('s3')

BUCKET = 'tc2-bronze'
PREFIX = 'municipiosIBGE/'

url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

key = f"{PREFIX}municipiosIBGE.parquet"

def lambda_handler(event, context):
    try:
        resposta = requests.get(url)
        resposta.raise_for_status()

        dados = resposta.json()

        print(f"Quantidade de registros retornados: {len(dados)}")

        municipios = pd.DataFrame([
            {
                "id_municipio": str(municipio["id"]),
                "nome_municipio": municipio["nome"]
            }
            for municipio in dados
        ])

        parquet_buffer = BytesIO()
        municipios.to_parquet(parquet_buffer)
        
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=parquet_buffer.getvalue()
        )    

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Tabela de municipios do IBGE processada e salva no S3 com sucesso',
                'bucket': BUCKET,
                'tables': key
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