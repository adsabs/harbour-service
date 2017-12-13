"""
General manage commands for the harbour-service
"""
import os
import sys
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_HOME)

from flask.ext.script import Manager, Command
from flask.ext.migrate import Migrate, MigrateCommand
from models import Base
from harbour.app import create_app

# Load the app with the factory
app = create_app()


class CreateDatabase(Command):
    """
    Creates the database based on models.py
    """
    @staticmethod
    def run(app=app):
        """
        Creates the database in the application context
        :return: no return
        """
        with app.app_context():
            Base.metadata.create_all(bind=app.db.engine)


# Set up the alembic migration
migrate = Migrate(app, app.db, compare_type=True)

# Setup the command line arguments using Flask-Script
manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('createdb', CreateDatabase())

if __name__ == '__main__':
    manager.run()
