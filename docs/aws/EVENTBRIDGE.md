# EventBridge no projeto

O **Amazon EventBridge** é utilizado na prova de conceito para permitir o
acionamento da Lambda de metas por meio de eventos.

A regra utiliza o event bus padrão e corresponde ao seguinte padrão:

```json
{
  "source": ["com.tc2"],
  "detail-type": ["metas"]
}
```

Eventos que correspondem a esse padrão são encaminhados para a Lambda `metas`.

A Lambda processa os dados recebidos, grava o resultado na camada Bronze e
inicia a Step Function responsável pela continuidade do pipeline.

Esse fluxo permite demonstrar uma alternativa de ingestão orientada a eventos,
complementar ao endpoint `POST /metas` disponibilizado pelo API Gateway.