from unittest import TestCase
from fastapi.testclient import TestClient
from main import correcto
from routers.python import routers
from faker import Faker
from textwrap import dedent
from os import remove
from os.path import exists

class TestPythonRouter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        faker = Faker()

        cls.user = {
            'email': faker.email(),
            'fullname': faker.user_name()
        }

        cls.task = {
            'task_description': faker.text(),
            'tags': ['while'],
            'return_values': [None]
        }

        cls.file_name = 'test.py'
        cls.file_content = dedent('''
            i = 10
            while i > 0:
                print(i)
                i = i - 1
        ''').strip()

        cls.file = (cls.file_name, cls.file_content.encode('utf-8'), 'text/plain')

        cls.solution_id = None 

    def setUp(self) -> None:
        for router in routers:
            correcto.include_router(router)

        self.client = TestClient(
            app=correcto,
            base_url='http://python.localhost:8001'
        )

    def test_1_create_task(self):
        response = self.client.post(
            url='/tasks',
            headers={'Content-Type': 'application/json'},
            json={**type(self).task}
        )

        status_code = response.status_code
        assert status_code == 201

        json_response = response.json()
        assert 'task' in json_response

        task = json_response['task']
        type(self).task['id'] = task['id']

        assert True
    
    def test_2_create_user(self):
        response = self.client.post(
            url='/users',
            headers={'Content-Type': 'application/json'},
            json={**type(self).user}
        )

        status_code = response.status_code
        assert status_code == 201

        json_response = response.json()
        assert 'user' in json_response

        user = json_response['user']
        type(self).user['id'] = user['id']

        assert True

    def test_3_create_solution(self):
        user_id = type(self).user.get('id')
        task_id = type(self).task.get('id')

        response = self.client.post(
            url='/solutions',
            files={
                'file': type(self).file
            },
            data={
              'user_id': user_id,
              'task_id': task_id
            }
        )

        status_code = response.status_code
        assert status_code == 201

        json_response = response.json()
        assert 'solution' in json_response

        solution = json_response['solution']
        type(self).solution_id = solution['id']

        assert True

    def test_4_check_solution(self):
        response = self.client.get(url=f'/solutions/check/{type(self).solution_id}')
        status_code = response.status_code
        assert status_code == 200

        json_response = response.json()
        assert 'solution' in json_response

        solution = json_response['solution']
        assert 'mark' in solution

        mark = solution['mark']
        assert mark == 1.0

    def test_5_delete_solution(self):
        request = self.client.delete(url=f'/solutions/{type(self).solution_id}')
        assert request.status_code == 200

    def test_6_delete_user(self):
        user_id = type(self).user['id']
        request = self.client.delete(url=f'/users/{user_id}')
        assert request.status_code == 200

    def test_7_delete_task(self):
        task_id = type(self).task['id']
        request = self.client.delete(url=f'/tasks/{task_id}')
        assert request.status_code == 200

    def test_8_delete_file(self):
        file_name = type(self).file_name
        if exists(file_name):
            remove(file_name)

        assert True