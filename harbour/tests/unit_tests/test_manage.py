"""
Tests the methods within the flask-script file manage.py
"""

from base import TestBaseDatabase
from harbour.manage import CreateDatabase
from harbour.models import Base, Users
from sqlalchemy import create_engine


class TestManagePy(TestBaseDatabase):
    """
    Class for testing the behaviour of the custom manage scripts
    """

    def test_create_database(self):
        """
        Tests the CreateDatabase action. This should create all the tables
        that should exist in the database.
        """

        # Setup the tables
        CreateDatabase.run(app=self.app)
        engine = create_engine(TestManagePy.postgresql_url)
        connection = engine.connect()

        for model in [Users]:
            exists = engine.dialect.has_table(connection, model.__tablename__)
            self.assertTrue(exists)

        # Clean up the tables
        Base.metadata.drop_all(bind=engine)
