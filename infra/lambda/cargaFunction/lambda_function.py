import urllib.request
import os
from io import BytesIO
import basedosdados as bd
import pandas as pd
import boto3

#primeval-melody-504216-n5

s3 = boto3.client("s3")
BUCKET = "fiap-tc-fase-2-bkt"

def create_data_folder():
    if not os.path.exists("data"):
        os.makedirs("data")

create_data_folder()


def extract_data(url, filename):
    try:
        urllib.request.urlretrieve(url, filename)
    except Exception as e:
        print(e)

def get_data_to_bigdata(table_id, billing_project_id):
    try:
        df = bd.read_table(dataset_id="br_inep_avaliacao_alfabetizacao",
                      table_id=table_id, 
                      billing_project_id=billing_project_id)
        print(df.head())
        df.to_csv(f"data/{table_id}.csv", index=False)

    except Exception as e:
        print(e)

def upload_to_s3(file_path, bucket, object_name):
    try:
        s3.upload_file(file_path, bucket, object_name)
        print(f"File {file_path} uploaded to S3 bucket {bucket} as {object_name}")
    except Exception as e:
        print(f"Error uploading file to S3: {e}")


#tables = ["municipio", "dicionario", "meta_alfabetizacao_brasil", "meta_alfabetizacao_municipio", "meta_alfabetizacao_uf", "alunos", "uf"]
tables = ["municipio", "dicionario", "uf"]
for table_id in tables:
    print(f"Getting data for table: {table_id}")
    #get_data_to_bigdata(table_id=table_id, billing_project_id="primeval-melody-504216-n5")
    upload_to_s3(file_path=f"data/{table_id}.csv", bucket=BUCKET, object_name=f"{table_id}.csv")
    print(f"Data for table {table_id} saved to data/{table_id}.csv")
    print("\n\n")