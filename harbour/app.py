# encoding: utf-8
"""
Application factory
"""

import json
import boto3
import logging.config

from flask import Flask
from flask.ext.watchman import Watchman
from flask_restful import Api
from flask_discoverer import Discoverer
from views import AuthenticateUserClassic, AuthenticateUserTwoPointOh, \
    AllowedMirrors, ClassicLibraries, ClassicUser, TwoPointOhLibraries, \
    ExportTwoPointOhLibraries

from models import db
from StringIO import StringIO


def create_app():
    """
    Create the application and return it to the user
    :return: application
    """

    app = Flask(__name__, static_folder=None)
    app.url_map.strict_slashes = False

    # Load config and logging
    load_config(app)
    logging.config.dictConfig(
        app.config['HARBOUR_LOGGING']
    )

    load_s3(app)

    # Register extensions
    watchman = Watchman(app, version=dict(scopes=['']))
    api = Api(app)
    Discoverer(app)
    db.init_app(app)

    # Add the end resource end points
    api.add_resource(AuthenticateUserClassic, '/auth/classic', methods=['POST'])
    api.add_resource(AuthenticateUserTwoPointOh, '/auth/twopointoh', methods=['POST'])

    api.add_resource(
        ClassicLibraries,
        '/libraries/classic/<int:uid>',
        methods=['GET']
    )
    api.add_resource(
        TwoPointOhLibraries,
        '/libraries/twopointoh/<int:uid>',
        methods=['GET']
    )

    api.add_resource(
        ExportTwoPointOhLibraries,
        '/export/twopointoh/<export>',
        methods=['GET']
    )

    api.add_resource(ClassicUser, '/user', methods=['GET'])
    api.add_resource(AllowedMirrors, '/mirrors', methods=['GET'])

    return app


def load_s3(app):
    """
    Loads relevant data from S3 that is needed

    :param app: flask.Flask application instance
    """
    try:
        s3_resource = boto3.resource('s3')
        bucket = s3_resource.Object(
            app.config['ADS_TWO_POINT_OH_S3_MONGO_BUCKET'],
            'users.json'
        )
        body = bucket.get()['Body']

        user_data = StringIO()
        for chunk in iter(lambda: body.read(1024), b''):
            user_data.write(chunk)

        users = json.loads(user_data.getvalue())
        app.config['ADS_TWO_POINT_OH_USERS'] = users
        app.config['ADS_TWO_POINT_OH_LOADED_USERS'] = True
    except Exception as error:
        app.logger.warning('Could not load users database: {}'.format(error))


def load_config(app):
    """
    Loads configuration in the following order:
        1. config.py
        2. local_config.py (ignore failures)
    :param app: flask.Flask application instance
    :return: None
    """

    app.config.from_pyfile('config.py')

    try:
        app.config.from_pyfile('local_config.py')
    except IOError:
        app.logger.warning('Could not load local_config.py')
if __name__ == '__main__':
    running_app = create_app()
    running_app.run(debug=True, use_reloader=False)
