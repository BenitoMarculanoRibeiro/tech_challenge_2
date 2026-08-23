import requests
import pandas as pd
import json
import boto3
from io import BytesIO

s3 = boto3.client('s3')

BUCKET = 'tc2-bronze'
PREFIX = 'municipio_ibge/'

url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

key = f"{PREFIX}municipios_ibge.parquet"

def lambda_handler(event, context):
    try:
        resposta = requests.get(url)
        resposta.raise_for_status()

        dados = resposta.json()

        print(f"Quantidade de registros retornados: {len(dados)}")

        # O json_normalize navega automaticamente pelas chaves aninhadas usando pontos
        df_raw = pd.json_normalize(dados)

        # Seleciona e renomeia apenas as colunas necessárias
        municipios = pd.DataFrame({
            "id_municipio": df_raw["id"].astype(str),
            "nome_municipio": df_raw["nome"],
            "sigla_uf": df_raw["microrregiao.mesorregiao.UF.sigla"]
        })

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