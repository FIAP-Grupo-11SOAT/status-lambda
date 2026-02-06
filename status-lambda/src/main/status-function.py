import os
import json
import logging
import boto3
import urllib.request
import urllib.parse
import urllib.error
import base64
from datetime import timezone
from decimal import Decimal

# Exemplo de evento teste
# {
#   "queryStringParameters": {
#     "email": "teste@fiap.com.br",
#     "upload_id": "a8da122788884fe1b4c7b916032b8586"
#   }
# }

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get('TABLE')

def lambda_handler(event, context):
    """Handler Lambda para listar arquivos processados.

    Retorna lista em português com: filename, size, created_at, download_url
    """
    if not TABLE_NAME:
        return responder(500, {'success': False, 'message': 'Variável de ambiente TABLE não configurada'})

    email = validar_jwt_cognito(event)
    if not email:
        return responder(401, {'success': False, 'message': 'Acesso não autorizado: Falha na validação do token'})

    _, upload_id = obter_filtros(event)
    logger.info(f"Iniciando listagem de arquivos. Email: {email}, UploadId: {upload_id}")

    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(TABLE_NAME)

        items = buscar_registros(table, email, upload_id)
        results = processar_resultados(items)
        return responder(200, {'files': results, 'total': len(results)})

    except Exception as e:
        logger.exception('Erro ao listar registros DynamoDB')
        return responder(500, {'success': False, 'message': 'Erro ao listar registros: ' + str(e)})


def obter_filtros(event):
    """Extrai email e upload_id da query string, se existirem."""
    params = event.get('queryStringParameters') or {}
    email = params.get('email')
    upload_id = params.get('upload_id')
    if not upload_id:
        upload_id = None
    return email, upload_id


def buscar_registros(table, email, upload_id):
    """Busca registros no DynamoDB, filtrando por email e/ou upload_id."""
    if email and upload_id:
        from boto3.dynamodb.conditions import Key
        resp = table.query(KeyConditionExpression=Key('idEmail').eq(email) & Key('idUpload').eq(upload_id))
    elif email:
        from boto3.dynamodb.conditions import Key
        resp = table.query(KeyConditionExpression=Key('idEmail').eq(email))
    else:
        resp = table.scan()
    return resp.get('Items') or []


def processar_resultados(items):
    """Formata a lista de itens."""
    results = []
    for it in items:
       

        email_val = it.get('idEmail')
        upload_id = it.get('idUpload')

        results.append({
            'email': email_val,
            'upload_id': upload_id,
            'status': it.get('status')
        })
    return results


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def responder(status_code, body_dict):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body_dict, cls=DecimalEncoder)
    }

def validar_jwt_cognito(event):
    # 1. Configurações do Cognito (Substitua pelos seus dados)
    DOMAIN = "hackaton-11soat-auth-v2.auth.us-east-1.amazoncognito.com"
    CLIENT_ID = "458sg2qduaf2ssokfrpl40p80f"
    REDIRECT_URI = "https://example.com/callback"
    
    params = event.get('queryStringParameters') or {}
    code = params.get('code')
    
    if not code:
        return None

    # 3. Preparar a chamada para trocar o CODE por TOKENS
    token_url = f"https://{DOMAIN}/oauth2/token"

    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }

    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        # 4. Fazer a requisição POST
        req = urllib.request.Request(token_url, data=encoded_data, headers=headers)
        with urllib.request.urlopen(req) as response:
            res_body = response.read()
            tokens = json.loads(res_body.decode('utf-8'))

            # O 'id_token' contém os dados do perfil do usuário
            id_token = tokens.get('id_token')

            # 5. Decodificar o ID Token para ver os dados (Email, Sub, etc)
            # O ID Token é um JWT. A parte do meio (índice 1) contém os dados.
            payload_b64 = id_token.split('.')[1]
            # Adiciona padding se necessário para o base64
            payload_json = base64.b64decode(payload_b64 + '===').decode('utf-8')
            user_data = json.loads(payload_json)
            user_email = user_data.get('email')
            logger.info(f"Email: {user_email}")

            return user_email

    except urllib.error.HTTPError as e:
        error_details = e.read().decode()
        logger.error(f"Erro detalhado do Cognito: {error_details}")
        return None