import unittest
from unittest import TestCase
from fastapi.testclient import TestClient
from main import correcto
from routers.python import admin_router
from faker import Faker

class TestAdminRouter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        faker = Faker()
        cls.admin_data = {
            'email': faker.email(),
            'password': faker.password()
        }
        cls.token = None
    
    def setUp(self) -> None:
        correcto.include_router(admin_router)
        self.client = TestClient(
            app=correcto,
            base_url='http://python.localhost/admins'
        )

    def test_1_sign_up_method(self):
        request = self.client.post(
            url='/sign_up',
            headers={
                'Content-Type': 'application/json',
                'Cache-Control': 'public, max-age=604800'
            },
            json=type(self).admin_data
        )

        status_code = request.status_code
        assert status_code == 201

    def test_2_sign_in_method(self):
        request = self.client.post(
            url='/sign_in',
            headers={
                'Content-Type': 'application/json',
                'Cache-Control': 'public, max-age=604800'
            },
            json=type(self).admin_data
        )

        status_code = request.status_code
        response = request.json()

        assert status_code == 200
        assert 'token' in response

        type(self).token = response['token']

    def test_3_check_token_method(self):
        request = self.client.get(url=f'/check_token/{type(self).token}')
        status_code = request.status_code
        response = request.json()
        assert status_code == 200
        assert 'access' in response
        assert response['access'] == True

    def test_4_delete_admin_method(self):
        email = type(self).admin_data.get('email')
        request = self.client.delete(url=f'/delete/{email}')
        assert request.status_code == 200