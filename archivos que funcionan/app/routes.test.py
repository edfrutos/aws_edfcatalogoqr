import unittest
from flask import url_for
from app import create_app
from app.models import Container
from app.extensions import db
from mongoengine.connection import disconnect

class TestPrintDetail(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        disconnect()

if __name__ == '__main__':
    unittest.main()
