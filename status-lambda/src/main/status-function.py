import os
import json
import logging
import boto3
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

    email, upload_id = obter_filtros(event)
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
    return params.get('email'), params.get('upload_id')


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
