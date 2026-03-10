from unittest import TestCase
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import correcto
from routers.python import solution_router
from loguru import logger
from serializers import SolutionSerializer

class TestSolutionRouter(TestCase):
    def setUp(self) -> None:
        correcto.include_router(solution_router)
        self.client = TestClient(
            app=correcto,
            base_url='http://python.localhost/solutions'
        )

    def test_1_get_route(self):
        request = self.client.get(url='')
        status_code = request.status_code
        response = request.json()

        assert status_code == 200
        assert 'solutions' in response

    def test_2_post_route(self):
        request = self.client.post(
            url='',
            files={
                'file': ('test.py', b'hello world', 'text/plain')
            },
            data={
                'user_id': 1,
                'task_id': 1
            }
        )
        status_code = request.status_code
        response = request.json()

        assert status_code == 422
        assert 'err_description' in response
        assert response['err_description'] == 'Task or user doesn\'t exist'

    def test_3_delete_route(self):
        logs = []
        logger.add(
            sink=logs.append,
            level='ERROR',
            format='{message}'
        )

        request = self.client.delete(url='/0')
        status_code = request.status_code
        response = request.json()

        assert status_code == 200
        assert isinstance(response, dict) == True
        assert 'Exception: Solution didn\'t find\n' in logs
        logger.remove()
    
    def test_4_check_method(self):
        checker = db_url = MagicMock()
        serializer = SolutionSerializer(
            data={'id': '0'},
            db_url=db_url
        )
        response = serializer.check(checker)

        assert isinstance(response, dict) == True 
        assert 'err_description' in response
        assert response['err_description'] == 'Solution didn\'t find'

    def test_5_check_route(self):
        request = self.client.post(
            url='/check/0'
        )
        status = request.status_code
        response = request.json()
        assert status == 422
        assert 'err_description' in response
        assert response['err_description'] == 'Solution didn\'t find'