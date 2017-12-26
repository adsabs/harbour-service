"""
Base properties for all of the unit tests that are shared between each file
"""
import testing.postgresql

from flask_testing import TestCase
from harbour import app

from harbour.models import Base


class TestBase(TestCase):
    """
    Base class, bear minimal
    """
    def create_app(self):
        """
        Create the wsgi application
        """
        a = app.create_app(**{
               'CLASSIC_LOGGING': {},
               'ADS_CLASSIC_MIRROR_LIST': ['mirror.com', 'other.mirror.com'],
               'ADS_TWO_POINT_OH_MIRROR': 'mirror.com',
               'SQLALCHEMY_DATABASE_URI': TestBaseDatabase.postgresql_url,
               'SQLALCHEMY_ECHO': True,
               'TESTING': True,
               'PROPAGATE_EXCEPTIONS': True,
               'TRAP_BAD_REQUEST_ERRORS': True,
               'SOLR_SERVICE_DISALLOWED_FIELDS': ['full', 'bar']
            })
        return a


class TestBaseDatabase(TestBase):
    """
    Base test class for when databases are being used.
    """
    postgresql_url_dict = {
        'port': 1234,
        'host': '127.0.0.1',
        'user': 'postgres',
        'database': 'test'
    }
    postgresql_url = 'postgresql://{user}@{host}:{port}/{database}'\
        .format(
            user=postgresql_url_dict['user'],
            host=postgresql_url_dict['host'],
            port=postgresql_url_dict['port'],
            database=postgresql_url_dict['database']
        )

    @classmethod
    def setUpClass(cls):
        cls.postgresql = \
            testing.postgresql.Postgresql(**cls.postgresql_url_dict)

    @classmethod
    def tearDownClass(cls):
        cls.postgresql.stop()

    def setUp(self):
        """
        Set up the database for use
        """
        Base.metadata.create_all(bind=self.app.db.engine)
        self.stub_user_data = {
            'classic_email': 'user@ads.com',
            'classic_password': 'password',
            'classic_mirror': 'mirror.com'
        }

        self.stub_user_data_2p0= {
            'twopointoh_email': 'user@ads.com',
            'twopointoh_password': 'password',
        }

    def tearDown(self):
        """
        Remove/delete the database and the relevant connections
        """
        self.app.db.session.remove()
        Base.metadata.drop_all(bind=self.app.db.engine)
