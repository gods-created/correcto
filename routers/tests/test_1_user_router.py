from fastapi.testclient import TestClient
from unittest import TestCase
from main import correcto
from routers.python import user_router
from faker import Faker

class TestUserRouter(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user_id = None

    def setUp(self) -> None:
        correcto.include_router(user_router)
        self.client = TestClient(correcto, base_url='http://python.testserver')

        self.faker = Faker()
        self.fullname = self.faker.name()
        self.email = self.faker.email()
    
    def test_1_get_route(self):
        request = self.client.get(
            url='/users'
        )
        status_code = request.status_code
        response = request.json()
        assert status_code == 200
        assert 'users' in response

    def test_2_post_route(self):
        request = self.client.post(
            url='/users',
            headers={
                'Content-Type': 'application/json'
            },
            json={
                'fullname': self.fullname,
                'email': self.email
            }
        )
        status_code = request.status_code
        response = request.json()
        assert status_code == 201
        assert 'user' in response

        type(self).user_id = response['user']['id']

    def test_3_put_route(self):
        email = self.faker.email()
        request = self.client.put(
            url=f'/users/{type(self).user_id}',
            headers={'Content-Type': 'application/json'},
            json={'email': email}
        )
        status_code = request.status_code
        response = request.json()
        assert status_code == 200
        assert 'user' in response
        assert response['user']['email'] == email

    def test_4_delete_route(self):
        request = self.client.delete(
            url=f'/users/{type(self).user_id}',
        )

        status_code = request.status_code
        response = request.json()
        assert status_code == 200
        assert not response

    def tearDown(self) -> None:
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        pass