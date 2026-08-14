import urllib.request
import os
from io import BytesIO
import basedosdados as bd
import pandas as pd
import boto3

#primeval-melody-504216-n5
s3 = boto3.client("s3")
BUCKET = "fiap-tc-fase-2-bkt"
BILLING_PROJECT_ID = "primeval-melody-504216-n5"

def handler(event, context):
    key = event["Records"][0]["s3"]["object"]["key"]
    filename = os.path.basename(key)
    local_output = f"/tmp/{filename.replace('.csv', '.parquet')}"

    try:

        # Check /tmp space (10 GB limit)
        tmp_usage = sum(
            os.path.getsize(f"/tmp/{f}")
            for f in os.listdir("/tmp") if os.path.isfile(f"/tmp/{f}")
        )
        if tmp_usage > 9 * 1024**3:  # 9 GB safety margin
            raise RuntimeError("Approaching /tmp storage limit")

        #tables = ["municipio", "dicionario", "meta_alfabetizacao_brasil", "meta_alfabetizacao_municipio", "meta_alfabetizacao_uf", "alunos", "uf"]
        tables = ["municipio", "dicionario", "uf"]
        for table_id in tables:
            print(f"Getting data for table: {table_id}")

            df = bd.read_table(dataset_id="br_inep_avaliacao_alfabetizacao",
                        table_id=table_id, 
                        billing_project_id=BILLING_PROJECT_ID)

            parquet_buffer = BytesIO()
            df.to_parquet(parquet_buffer)


            df.to_parquet(local_output, engine="pyarrow", compression="snappy")

            # Upload result back to S3
            output_key = key.replace("raw/", "processed/").replace(".csv", ".parquet")
            s3.upload_file(local_output, BUCKET, output_key)

            return {"status": "success", "output_key": output_key}

    finally:
        # Clean up /tmp
        if os.path.exists(local_output):
            print(local_output)