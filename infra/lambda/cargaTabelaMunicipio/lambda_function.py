import requests
import pandas as pd

url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

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

print(municipios.head())