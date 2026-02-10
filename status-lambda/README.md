# Status Lambda

Este projeto contém o código-fonte e os arquivos de suporte para uma aplicação serverless que você pode implantar com o Terraform. Ele foi projetado para verificar o status de uploads de arquivos.

## Descrição

A função Lambda `status-function` é acionada por uma requisição HTTP via API Gateway. Ela consulta uma tabela no DynamoDB para recuperar o status de um processo de upload de arquivo com base no e-mail do usuário e/ou no ID do upload.

## Arquitetura

A aplicação utiliza os seguintes recursos da AWS:

*   **AWS Lambda**: Executa o código da função `status-function.py`.
*   **Amazon API Gateway**: Fornece um endpoint HTTP para acionar a função Lambda.
*   **Amazon DynamoDB**: Armazena os metadados e o status dos uploads de arquivos.
*   **Terraform**: Provisiona e gerencia a infraestrutura da AWS.

## Pré-requisitos

Para construir e implantar esta aplicação, você precisa das seguintes ferramentas:

*   [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)
*   [AWS CLI](https://aws.amazon.com/cli/)
*   [Python](https://www.python.org/downloads/)

## Implantação

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd status-lambda
    ```

2.  **Configure suas credenciais da AWS:**
    Certifique-se de que suas credenciais da AWS estejam configuradas corretamente para que o Terraform possa provisionar os recursos.

3.  **Implante com o Terraform:**
    Navegue até o diretório `infra` e execute os seguintes comandos:
    ```bash
    cd infra
    terraform init
    terraform plan
    terraform apply
    ```
    O Terraform irá provisionar a função Lambda, a tabela do DynamoDB e o API Gateway.

## Como Usar

Após a implantação, o Terraform exibirá a URL do endpoint do API Gateway. Você pode usar essa URL para verificar o status de um upload.

**Exemplo de Requisição:**

Você pode fazer uma requisição GET para o endpoint, passando `email` e/ou `upload_id` como parâmetros de consulta:

```bash
curl "https://<API_GATEWAY_URL>/status?email=teste@fiap.com.br&upload_id=a8da122788884fe1b4c7b916032b8586"
```

**Parâmetros de Consulta:**

*   `email` (opcional): O e-mail associado ao upload.
*   `upload_id` (opcional): O ID exclusivo do upload.

Se nenhum parâmetro for fornecido, a função retornará todos os registros da tabela.

**Exemplo de Resposta:**

```json
{
  "files": [
    {
      "email": "teste@fiap.com.br",
      "upload_id": "a8da122788884fe1b4c7b916032b8586",
      "status": "COMPLETED"
    }
  ],
  "total": 1
}
```

## Variáveis de Ambiente

A função Lambda espera a seguinte variável de ambiente:

*   `TABLE`: O nome da tabela do DynamoDB onde os status dos uploads são armazenados. Esta variável é configurada automaticamente pelo Terraform durante a implantação.
