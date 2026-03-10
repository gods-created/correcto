from unittest import TestCase
from fastapi.testclient import TestClient
from main import correcto
from routers.python import task_router

class TestTaskRouter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.task_id = None

    def setUp(self) -> None:
        correcto.include_router(task_router)
        self.client = TestClient(correcto, base_url='http://python.localhost/tasks')

    def test_1_get_route(self):
        request = self.client.get(url='')
        status_code = request.status_code
        response = request.json()

        assert status_code == 200
        assert 'tasks' in response

    def test_2_post_route(self):
        request = self.client.post(
            url='',
            headers={
                'Content-Type': 'application/json'
            },
            json={
                'task_description': 'Test text description',
                'tags': [],
                'return_values': [1]
            }
        )

        status_code = request.status_code
        response = request.json()

        assert status_code == 201
        assert 'task' in response

        type(self).task_id = response['task']['id']

    def test_3_put_route(self):
        request = self.client.put(
            url=f'/{type(self).task_id}',
            headers={
                'Content-Type': 'application/json'
            },
            json={
                'tags': ['while'],
            }
        )

        status_code = request.status_code
        response = request.json()

        assert status_code == 200
        assert 'task' in response
        assert 'while' in response['task']['tags'] 

    def test_4_delete_route(self):
        request = self.client.delete(url=f'/{type(self).task_id}')
        status_code = request.status_code
        response = request.json()

        assert status_code == 200
        assert isinstance(response, dict) == True
         
    
