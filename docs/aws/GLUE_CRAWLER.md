# Glue Crawler e Data Catalog

O database chama-se `tc2-glue-database-table`. O crawler aponta somente para
`s3://<GOLD_BUCKET>/indicador_uf/`, utilizando esse prefixo como fonte para
catalogação. Ele atualiza a tabela `indicador_uf`; exclusões são apenas
registradas para evitar remoção silenciosa de schema.

Execute o crawler após uma Gold bem-sucedida e valide a tabela no Data Catalog
ou no Athena.