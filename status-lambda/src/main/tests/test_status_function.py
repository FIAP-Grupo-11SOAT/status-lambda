# c:\Users\Dev\Desktop\status-lambda\status-lambda\src\main\tests\test_status_function.py

import unittest
import json
import os
import sys
import importlib.util
from unittest.mock import MagicMock, patch
from decimal import Decimal

# Configuração para importar o módulo 'status-function.py' que possui hífen no nome
# O arquivo está um nível acima deste teste (../status-function.py)
CURRENT_DIR = os.path.dirname(__file__)
SRC_FILE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'status-function.py'))

spec = importlib.util.spec_from_file_location("status_function", SRC_FILE_PATH)
status_function = importlib.util.module_from_spec(spec)
sys.modules["status_function"] = status_function
spec.loader.exec_module(status_function)

class TestStatusFunction(unittest.TestCase):

    def setUp(self):
        # Configura variáveis de ambiente padrão para os testes
        self.env_patcher = patch.dict(os.environ, {'TABLE': 'TestTable'})
        self.env_patcher.start()
        # Atualiza a variável global do módulo, pois ela é lida na importação
        status_function.TABLE_NAME = 'TestTable'

    def tearDown(self):
        self.env_patcher.stop()

    @patch('status_function.autenticar_usuario')
    @patch('boto3.resource')
    def test_lambda_handler_success_scan(self, mock_resource, mock_auth):
        """Testa listagem completa (agora Query por email) quando sem filtros."""
        # Mock da autenticação
        mock_auth.return_value = ('teste@fiap.com.br', None)

        # Mock do DynamoDB
        mock_table = MagicMock()
        mock_dynamo = MagicMock()
        mock_resource.return_value = mock_dynamo
        mock_dynamo.Table.return_value = mock_table
        
        # Mock da resposta do Scan (agora Query)
        mock_table.query.return_value = {
            'Items': [
                {
                    'idEmail': 'teste@fiap.com.br',
                    'idUpload': '12345',
                    'status': 'concluido'
                }
            ]
        }

        event = {}
        context = {}
        
        response = status_function.lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        
        self.assertEqual(body['total'], 1)
        self.assertEqual(body['files'][0]['email'], 'teste@fiap.com.br')
        
        # Verifica se chamou query (pois email está presente)
        mock_table.query.assert_called_once()

    @patch('status_function.autenticar_usuario')
    @patch('boto3.resource')
    def test_lambda_handler_success_query_filters(self, mock_resource, mock_auth):
        """Testa busca filtrada (Query) quando email e upload_id são fornecidos."""
        mock_auth.return_value = ('teste@fiap.com.br', None)
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_table.query.return_value = {'Items': []}

        event = {
            'queryStringParameters': {
                'email': 'teste@fiap.com.br',
                'upload_id': 'abc-123'
            }
        }
        
        status_function.lambda_handler(event, {})
        
        # Verifica se chamou query (e não scan)
        mock_table.query.assert_called_once()

    @patch('status_function.autenticar_usuario')
    @patch('boto3.resource')
    def test_lambda_handler_success_query_email_only(self, mock_resource, mock_auth):
        """Testa busca filtrada (Query) quando upload_id é vazio ou null."""
        mock_auth.return_value = ('teste@fiap.com.br', None)
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_table.query.return_value = {'Items': []}

        event = {
            'queryStringParameters': {
                'email': 'teste@fiap.com.br',
                'upload_id': ''
            }
        }
        
        status_function.lambda_handler(event, {})
        
        # Verifica se chamou query
        mock_table.query.assert_called_once()

    def test_lambda_handler_missing_table_env(self):
        """Testa erro quando a variável de ambiente TABLE não está definida."""
        # Remove a variável TABLE temporariamente
        status_function.TABLE_NAME = None
        
        response = status_function.lambda_handler({}, {})
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertFalse(body['success'])
        self.assertIn('Variável de ambiente TABLE não configurada', body['message'])

    @patch('status_function.logger')
    @patch('status_function.autenticar_usuario')
    @patch('boto3.resource')
    def test_lambda_handler_dynamodb_exception(self, mock_resource, mock_auth, mock_logger):
        """Testa tratamento de exceção ao acessar o DynamoDB."""
        mock_auth.return_value = ('teste@fiap.com.br', None)
        mock_resource.side_effect = Exception("Erro de conexão")
        
        response = status_function.lambda_handler({}, {})
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('Erro ao listar registros', body['message'])

if __name__ == '__main__':
    unittest.main()
