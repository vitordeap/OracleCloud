# OracleCloud

Guia para simulação de um Kafka Cluster utilizando o Event Hub da Oracle Cloud.

#### PARTE 1 - Enviar mensagens para o Cluster.

1.1- O Producer enviará mensagens para o cluster. Os parâmetros devem ser alterados no arquivo 'kakfa_producer.py':

	-Dados: o formato dos dados enviados é json. Alterar a estrutura dos dados conforme desejado ou apontar para um arquivo json.

	-URL: o URL segue o padrão <BASE_PATH>/topics/<TOPIC_NAME>. Pode ser verificado no tópico criado dentro do Event Hub.

	-USER_PASS: usuário e senha no formato 'usuario:senha' que tem acesso ao cluster configurado.

1.2- Executar o arquivo 'kafka_producer.py'. Cada vez que o arquivo for executado, uma mensagem será enviada.


#### PARTE 2 - Criar grupo de consumidores do Cluster.

2.1- Será necessário criar um grupo de consumidores do cluster. Os parâmetros devem ser alterados no arquivo 'kafka_consumer-group-creation.py'

	-Dados: NÃO MUDAR

	-URL: o formato apresentado é do padrão <BASE_PATH>/consumers/oehcs-consumer-group
	Alterar somente o <BASE_PATH>

2.2- Executar o arquvio 'kafka_consumer-group_creation.py'. A resposta do request HTTP trará algumas informações.
	
	-A informação 'base_uri' é extremamente importante, pois é neste link que o consumidor poderá consumir as mensagens. Salve este link.

#### PARTE 3 - Consumir mensagens do Cluster.

3.1- Alterar os parâmetros do arquivo 'kakfa_consumer.py'

	-TopicName: mudar o nome do topico no formato json.

	-BaseURI: alterar o baseURI para a informação obtida quando foi criado o grupo de consumidores.

3.2- Executar o arquivo 'kafka_consumer.py' para receber as mensagens.







