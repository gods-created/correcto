from unittest import TestCase
from services import get_db_url_service
from configs import TENANTS
from random import choice

class TestGetDBURL(TestCase):
    def setUp(self) -> None:
        self.tenants = [key for key, _ in TENANTS.items()]

    def test_service(self):
        tenant = choice(self.tenants)
        db_url = get_db_url_service(tenant)
        assert db_url is not None
        assert 'sqlite:///' in db_url
