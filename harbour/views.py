# encoding: utf-8
"""
Views
"""
import re
import json
import boto3
import requests
import traceback

from utils import get_post_data, err
from flask import current_app, request, send_file
from flask_restful import Resource
from flask_discoverer import advertise
from client import client
from models import Users
from zipfile import ZipFile
from StringIO import StringIO
from http_errors import CLASSIC_AUTH_FAILED, CLASSIC_DATA_MALFORMED, \
    CLASSIC_TIMEOUT, CLASSIC_BAD_MIRROR, CLASSIC_NO_COOKIE, \
    CLASSIC_UNKNOWN_ERROR, NO_CLASSIC_ACCOUNT, NO_TWOPOINTOH_ACCOUNT, \
    NO_TWOPOINTOH_LIBRARIES, TWOPOINTOH_AWS_PROBLEM, EXPORT_SERVICE_FAIL, \
    TWOPOINTOH_WRONG_EXPORT_TYPE
from sqlalchemy.orm.exc import NoResultFound

USER_ID_KEYWORD = 'X-Adsws-Uid'


class BaseView(Resource):
    """
    A base view class to keep a single version of common functions used between
    all of the views.
    """
    @staticmethod
    def helper_get_user_id():
        """
        Helper function: get the user id from the header, otherwise raise
        a key error exception
        :return: unique API user ID
        """
        try:
            return int(request.headers[USER_ID_KEYWORD])

        except KeyError:
            current_app.logger.error('No username passed')
            raise

        except ValueError:
            current_app.logger.error('Unknow error with API')
            raise


class ClassicUser(BaseView):
    """
    End point to collect the user's ADS Classic information currently stored in
    the database
    """

    decorators = [advertise('scopes', 'rate_limit')]
    scopes = ['user']
    rate_limit = [1000, 60*60*24]

    def get(self):
        """
        HTTP GET request that returns the information currently stored about the
        user's ADS Classic settings, currently stored in the service database.

        Return data (on success)
        ------------------------
        classic_email: <string> ADS Classic e-mail of the user
        classic_mirror: <string> ADS Classic mirror this user belongs to

        HTTP Responses:
        --------------
        Succeed authentication: 200
        User unknown/wrong password/failed authentication: 404

        Any other responses will be default Flask errors
        """

        absolute_uid = self.helper_get_user_id()

        try:
            with current_app.session_scope() as session:
                user = session.query(Users).filter(Users.absolute_uid == absolute_uid).one()
                return {
                    'classic_email': user.classic_email,
                    'classic_mirror': user.classic_mirror,
                    'twopointoh_email': user.twopointoh_email
                }, 200
        except NoResultFound:
            return err(NO_CLASSIC_ACCOUNT)


class AllowedMirrors(BaseView):
    """
    End point that returns the allowed list of mirror sites for either ADS
    classic utilities or BEER/ADS2.0 utilities.
    """

    decorators = [advertise('scopes', 'rate_limit')]
    scopes = []
    rate_limit = [1000, 60*60*24]

    def get(self):
        """
        HTTP GET request that returns the list of mirror sites that can be used
        with this end point. Any end points not listed by this method cannot be
        used for any of the other methods related to this service.

        Return data (on success)
        ------------------------
        list[<string>]
        eg., list of mirrors, ['site1', 'site2', ...., 'siteN']


        HTTP Responses:
        --------------
        Succeed authentication: 200

        Any other responses will be default Flask errors
        """

        return current_app.config.get('ADS_CLASSIC_MIRROR_LIST', [])


class TwoPointOhLibraries(BaseView):
    """
    End point to collect the user's ADS 2.0 libraries with the MongoDB dump
    in a flat-file on S3 storage

    Note: ADS 2.0 user accounts are tied to ADS Classic accounts. Therefore,
    a user will need to regisiter their ADS Classic/2.0 account on this service
    for them to also be able to access the ADS 2.0 libraries.
    """
    decorators = [advertise('scopes', 'rate_limit')]
    scopes = ['adsws:internal']
    rate_limit = [1000, 60*60*24]

    @staticmethod
    def get_s3_library(library_file_name):
        """
        Get the JSON MongoDB dump of the ADS 2.0 library of a specific user.
        These files are stored on S3.

        :param library_file_name: name of library file
        :type library_file_name: str

        :return: dict
        """
        s3_resource = boto3.resource('s3')
        bucket = s3_resource.Object(
            current_app.config['ADS_TWO_POINT_OH_S3_MONGO_BUCKET'],
            library_file_name
        )
        body = bucket.get()['Body']
        library_data = StringIO()
        for chunk in iter(lambda: body.read(1024), b''):
            library_data.write(chunk)

        library = json.loads(library_data.getvalue())

        return library

    def get(self, uid):
        """
        HTTP GET request that finds the libraries within ADS 2.0 for that user.

        :param uid: user ID for the API
        :type uid: int

        Return data (on success)
        ------------------------
        libraries: <list<dict>> a list of dictionaries, that contains the
        following for each library entry:
            name: <string> name of the library
            description: <string> description of the library
            documents: <list<string>> list of documents

        HTTP Responses:
        --------------
        Succeed getting libraries: 200
        User does not have a classic/ADS 2.0 account: 400
        User does not have any libraries in their ADS 2.0 account: 400
        Unknown error: 500

        Any other responses will be default Flask errors
        """
        with current_app.session_scope() as session:
            if not current_app.config['ADS_TWO_POINT_OH_LOADED_USERS']:
                current_app.logger.error(
                    'Users from MongoDB have not been loaded into the app'
                )
                return err(TWOPOINTOH_AWS_PROBLEM)

            try:
                user = session.query(Users).filter(Users.absolute_uid == uid).one()

                # Have they got an email for ADS 2.0?
                if not user.twopointoh_email:
                    raise NoResultFound

            except NoResultFound:
                current_app.logger.warning(
                    'User does not have an associated ADS 2.0 account'
                )
                return err(NO_TWOPOINTOH_ACCOUNT)

            library_file_name = current_app.config['ADS_TWO_POINT_OH_USERS'].get(
                user.twopointoh_email,
                None
            )

            if not library_file_name:
                current_app.logger.warning(
                    'User does not have any libraries in ADS 2.0'
                )
                return err(NO_TWOPOINTOH_LIBRARIES)

            try:
                library = TwoPointOhLibraries.get_s3_library(library_file_name)
            except Exception as error:
                current_app.logger.error(
                    'Unknown error with AWS: {}'.format(error)
                )
                return err(TWOPOINTOH_AWS_PROBLEM)

            return {'libraries': library}, 200


class ExportTwoPointOhLibraries(BaseView):
    """
    End point to return ADS 2.0 libraries in a format that users can use to
    import them to other services. Currently, the following third-party
    services are supported:
      - Zotero (https://www.zotero.org/)
      - Papers (http://www.papersapp.com/)
      - Mendeley (https://www.mendeley.com/)
    """

    decorators = [advertise('scopes', 'rate_limit')]
    scopes = ['user']
    rate_limit = [1000, 60*60*24]

    def get(self, export):
        """
        HTTP GET request that collects a users ADS 2.0 libraries from the flat
        files on S3. It returns a file for download of the .bib format.

        :param export: service to export to
        :type export: str

        Return data (on success)
        ------------------------
        BibTeX file (.bib)

        HTTP Responses:
        --------------
        Succeed getting libraries: 200
        User does not have a classic/ADS 2.0 account: 400
        User does not have any libraries in their ADS 2.0 account: 400
        Unknown error: 500

        Any other responses will be default Flask errors
        """
        with current_app.session_scope() as session:
            if export not in current_app.config['HARBOUR_EXPORT_TYPES']:
                return err(TWOPOINTOH_WRONG_EXPORT_TYPE)

            if not current_app.config['ADS_TWO_POINT_OH_LOADED_USERS']:
                current_app.logger.error(
                    'Users from MongoDB have not been loaded into the app'
                )
                return err(TWOPOINTOH_AWS_PROBLEM)

            absolute_uid = self.helper_get_user_id()

            try:
                user = session.query(Users).filter(Users.absolute_uid == absolute_uid).one()

                # Have they got an email for ADS 2.0?
                if not user.twopointoh_email:
                    raise NoResultFound

            except NoResultFound:
                current_app.logger.warning(
                    'User does not have an associated ADS Classic/2.0 account'
                )
                return err(NO_TWOPOINTOH_ACCOUNT)

            library_file_name = current_app.config['ADS_TWO_POINT_OH_USERS'].get(
                user.twopointoh_email,
                None
            )

            if not library_file_name:
                current_app.logger.warning(
                    'User does not have any libraries in ADS 2.0'
                )
                return err(NO_TWOPOINTOH_LIBRARIES)

            try:
                s3 = boto3.client('s3')
                s3_presigned_url = s3.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': current_app.config['ADS_TWO_POINT_OH_S3_MONGO_BUCKET'],
                        'Key': library_file_name.replace('.json', '.{}.zip'.format(export))
                    },
                    ExpiresIn=1800
                )
            except Exception as error:
                current_app.logger.error(
                    'Unknown error with AWS: {}'.format(error)
                )
                return err(TWOPOINTOH_AWS_PROBLEM)

            return {'url': s3_presigned_url}, 200


class ClassicLibraries(BaseView):
    """
    End point to collect the user's ADS classic libraries with the external ADS
    Classic end point
    """

    decorators = [advertise('scopes', 'rate_limit')]
    scopes = ['adsws:internal']
    rate_limit = [1000, 60*60*24]

    def get(self, uid):
        """
        HTTP GET request that contacts the ADS Classic libraries end point to
        obtain all the libraries relevant to that user.

        :param uid: user ID for the API
        :type uid: int

        Return data (on success)
        ------------------------
        libraries: <list<dict>> a list of dictionaries, that contains the
        following for each library entry:
            name: <string> name of the library
            description: <string> description of the library
            documents: <list<string>> list of documents

        HTTP Responses:
        --------------
        Succeed getting libraries: 200
        User does not have a classic account: 400
        ADS Classic give unknown messages: 500
        ADS Classic times out: 504

        Any other responses will be default Flask errors
        """
        with current_app.session_scope() as session:
            try:
                user = session.query(Users).filter(Users.absolute_uid == uid).one()
                if not user.classic_email:
                    raise NoResultFound
            except NoResultFound:
                current_app.logger.warning(
                    'User does not have an associated ADS Classic account'
                )
                return err(NO_CLASSIC_ACCOUNT)

            url = current_app.config['ADS_CLASSIC_LIBRARIES_URL'].format(
                mirror=user.classic_mirror,
                cookie=user.classic_cookie
            )
            current_app.logger.debug('Obtaining libraries via: {}'.format(url))
            try:
                response = current_app.client.get(url)
            except requests.exceptions.Timeout:
                current_app.logger.warning(
                    'ADS Classic timed out before finishing: {}'.format(url)
                )
                return err(CLASSIC_TIMEOUT)

            if response.status_code != 200:
                current_app.logger.info(
                    'ADS Classic returned an unkown status code: "{}" [code: {}]'
                    .format(response.text, response.status_code)
                )
                return err(CLASSIC_UNKNOWN_ERROR)

            data = response.json()

            libraries = [dict(
                name=i['name'],
                description=i.get('desc', ''),
                documents=[j['bibcode'] for j in i['entries']]
            ) for i in data['libraries']]

            return {'libraries': libraries}, 200


class AuthenticateUserClassic(BaseView):
    """
    End point to authenticate the user's ADS classic credentials with the
    external ADS Classic end point
    """

    decorators = [advertise('scopes', 'rate_limit')]
    scopes = ['user']
    rate_limit = [1000, 60*60*24]

    def post(self):
        """
        HTTP POST request that receives the user's ADS Classic credentials, and
        then contacts the Classic system to check that what the user provided is
        indeed valid. If valid, the users ID is stored within the myADS service
        store.

        Post body:
        ----------
        KEYWORD, VALUE
        classic_email: <string> ADS Classic e-mail of the user
        classic_password: <string> ADS Classic password of the user
        classic_mirror: <string> ADS Classic mirror this user belongs to

        Return data (on success):
        -------------------------
        classic_authed: <boolean> were they authenticated
        classic_email: <string> e-mail that authenticated correctly
        classic_mirror: <string> ADS Classic mirror this user selected

        HTTP Responses:
        --------------
        Succeed authentication: 200
        Bad/malformed data: 400
        User unknown/wrong password/failed authentication: 404
        ADS Classic give unknown messages: 500
        ADS Classic times out: 504

        Any other responses will be default Flask errors
        """
        post_data = get_post_data(request)
        with current_app.session_scope() as session:
            # Collect the username, password from the request
            try:
                classic_email = post_data['classic_email']
                classic_password = post_data['classic_password']
                classic_mirror = post_data['classic_mirror']
            except KeyError:
                current_app.logger.warning(
                    'User did not provide a required key: {}'
                    .format(traceback.print_exc())
                )
                return err(CLASSIC_DATA_MALFORMED)

            # Check that the mirror exists and not man-in-the-middle
            if classic_mirror not in current_app.config['ADS_CLASSIC_MIRROR_LIST']:
                current_app.logger.warning(
                    'User "{}" tried to use a mirror that does not exist: "{}"'
                    .format(classic_email, classic_mirror)
                )
                return err(CLASSIC_BAD_MIRROR)

            # Create the correct URL
            url = current_app.config['ADS_CLASSIC_URL'].format(
                mirror=classic_mirror,
            )
            params = {
                'man_cmd': 'elogin',
                'man_email': classic_email,
                'man_passwd': classic_password
            }

            # Authenticate
            current_app.logger.info(
                'User "{email}" trying to authenticate at mirror "{mirror}"'
                .format(email=classic_email, mirror=classic_mirror)
            )
            try:
                response = current_app.client.post(
                    url,
                    params=params
                )
            except requests.exceptions.Timeout:
                current_app.logger.warning(
                    'ADS Classic end point timed out, returning to user'
                )
                return err(CLASSIC_TIMEOUT)

            if response.status_code >= 500:
                message, status_code = err(CLASSIC_UNKNOWN_ERROR)
                message['ads_classic'] = {
                    'message': response.text,
                    'status_code': response.status_code
                }
                current_app.logger.warning(
                    'ADS Classic has responded with an unknown error: {}'
                    .format(response.text)
                )
                return message, status_code

            # Sanity check the response
            email = response.json()['email']
            if email != classic_email:
                current_app.logger.warning(
                    'User email "{}" does not match ADS return email "{}"'
                    .format(classic_email, email)
                )
                return err(CLASSIC_AUTH_FAILED)

            # Respond to the user based on whether they were successful or not
            if response.status_code == 200 \
                    and response.json()['message'] == 'LOGGED_IN' \
                    and int(response.json()['loggedin']):
                current_app.logger.info(
                    'Authenticated successfully "{email}" at mirror "{mirror}"'
                    .format(email=classic_email, mirror=classic_mirror)
                )

                # Save cookie in myADS
                try:
                    cookie = response.json()['cookie']
                except KeyError:
                    current_app.logger.warning(
                        'Classic returned no cookie, cannot continue: {}'
                        .format(response.json())
                    )
                    return err(CLASSIC_NO_COOKIE)

                absolute_uid = self.helper_get_user_id()
                try:
                    user = session.query(Users).filter(
                        Users.absolute_uid == absolute_uid
                    ).one()

                    current_app.logger.info('User already exists in database')
                    user.classic_mirror = classic_mirror
                    user.classic_cookie = cookie
                    user.classic_email = classic_email
                except NoResultFound:
                    current_app.logger.info('Creating entry in database for user')
                    user = Users(
                        absolute_uid=absolute_uid,
                        classic_cookie=cookie,
                        classic_email=classic_email,
                        classic_mirror=classic_mirror
                    )

                    session.add(user)

                session.commit()
                current_app.logger.info(
                    'Successfully saved content for "{}" to database: {{"cookie": "{}"}}'
                    .format(classic_email, '*'*len(user.classic_cookie))
                )

                return {
                    'classic_email': email,
                    'classic_mirror': classic_mirror,
                    'classic_authed': True
                }, 200

            else:
                current_app.logger.warning(
                    'Credentials for "{email}" did not succeed at mirror "{mirror}"'
                    .format(email=classic_email, mirror=classic_mirror)
                )
                return err(CLASSIC_AUTH_FAILED)


class AuthenticateUserTwoPointOh(BaseView):
    """
    End point to authenticate the user's ADS 2.0 credentials with the
    external ADS Classic end point (2.0 and Classic accounts are on ADS 2.0,
    interchangable)
    """

    decorators = [advertise('scopes', 'rate_limit')]
    scopes = ['user']
    rate_limit = [1000, 60*60*24]

    def post(self):
        """
        HTTP POST request that receives the user's ADS 2.0 credentials, and
        then contacts the Classic system to check that what the user provided
        is indeed valid. If valid, the users ID is stored.

        Post body:
        ----------
        KEYWORD, VALUE
        twopointoh_email: <string> ADS 2.0 e-mail of the user
        twopointoh_password: <string> ADS 2.0 password of the user

        Return data (on success):
        -------------------------
        twopointoh_authed: <boolean> were they authenticated
        twopointoh_email: <string> e-mail that authenticated correctly

        HTTP Responses:
        --------------
        Succeed authentication: 200
        Bad/malformed data: 400
        User unknown/wrong password/failed authentication: 404
        ADS Classic give unknown messages: 500
        ADS Classic times out: 504

        Any other responses will be default Flask errors
        """
        post_data = get_post_data(request)

        # Collect the username, password from the request
        try:
            twopointoh_email = post_data['twopointoh_email']
            twopointoh_password = post_data['twopointoh_password']
        except KeyError:
            current_app.logger.warning(
                'User did not provide a required key: {}'
                .format(traceback.print_exc())
            )
            return err(CLASSIC_DATA_MALFORMED)

        # Create the correct URL
        url = current_app.config['ADS_CLASSIC_URL'].format(
            mirror=current_app.config['ADS_TWO_POINT_OH_MIRROR'],
        )
        params = {
            'man_cmd': 'elogin',
            'man_email': twopointoh_email,
            'man_passwd': twopointoh_password
        }

        # Authenticate
        current_app.logger.info(
            'User "{email}" trying to authenticate"'
            .format(email=twopointoh_email)
        )
        try:
            response = current_app.client.post(
                url,
                params=params
            )
        except requests.exceptions.Timeout:
            current_app.logger.warning(
                'ADS Classic end point timed out, returning to user'
            )
            return err(CLASSIC_TIMEOUT)

        if response.status_code >= 500:
            message, status_code = err(CLASSIC_UNKNOWN_ERROR)
            message['ads_classic'] = {
                'message': response.text,
                'status_code': response.status_code
            }
            current_app.logger.warning(
                'ADS Classic has responded with an unknown error: {}'
                .format(response.text)
            )
            return message, status_code

        # Sanity check the response
        email = response.json()['email']
        if email != twopointoh_email:
            current_app.logger.warning(
                'User email "{}" does not match ADS return email "{}"'
                .format(twopointoh_email, email)
            )
            return err(CLASSIC_AUTH_FAILED)

        # Respond to the user based on whether they were successful or not
        if response.status_code == 200 \
                and response.json()['message'] == 'LOGGED_IN' \
                and int(response.json()['loggedin']):
            current_app.logger.info(
                'Authenticated successfully "{email}"'
                .format(email=twopointoh_email)
            )

            absolute_uid = self.helper_get_user_id()
            with current_app.session_scope() as session:
                try:
                    user = session.query(Users).filter(
                        Users.absolute_uid == absolute_uid
                    ).one()

                    current_app.logger.info('User already exists in database')
                    user.twopointoh_email = twopointoh_email
                except NoResultFound:
                    current_app.logger.info('Creating entry in database for user')
                    user = Users(
                        absolute_uid=absolute_uid,
                        twopointoh_email=twopointoh_email
                    )
                    session.add(user)
                session.commit()

                current_app.logger.info(
                    'Successfully saved content for "{}" to database'
                    .format(twopointoh_email)
                )

                return {
                    'twopointoh_email': email,
                    'twopointoh_authed': True
                }, 200
            return err(HARBOUR_SERVICE_FAIL)
        else:
            current_app.logger.warning(
                'ADS 2.0 credentials for "{email}" did not succeed"'
                .format(email=twopointoh_email)
            )
            return err(CLASSIC_AUTH_FAILED)

class ClassicMyADS(BaseView):
    """
    End point to collect the user's ADS classic libraries with the external ADS
    Classic end point
    """

    decorators = [advertise('scopes', 'rate_limit')]
    scopes = ['adsws:internal']
    rate_limit = [1000, 60*60*24]

    def get(self, uid):
        """
        HTTP GET request that contacts the ADS Classic myADS end point to
        obtain all the libraries relevant to that user.

        :param uid: user ID for the API
        :type uid: int

        Return data (on success)
        ------------------------
        

        HTTP Responses:
        --------------
        Succeed getting libraries: 200
        User does not have a classic account: 400
        ADS Classic give unknown messages: 500
        ADS Classic times out: 504

        Any other responses will be default Flask errors
        """
        data = {}
        with current_app.session_scope() as session:
            try:
                user = session.query(Users).filter(Users.absolute_uid == uid).one()
                if not user.classic_email:
                    raise NoResultFound
            except NoResultFound:
                current_app.logger.warning(
                    'User does not have an associated ADS Classic account'
                )
                return err(NO_CLASSIC_ACCOUNT)

            url = current_app.config['ADS_CLASSIC_MYADS_URL'].format(
                mirror='adsabs.harvard.edu',
                email=user.classic_email
            )

            current_app.logger.debug('Obtaining libraries via: {}'.format(url))
            try:
                response = current_app.client.get(url)
            except requests.exceptions.Timeout:
                current_app.logger.warning(
                    'ADS Classic timed out before finishing: {}'.format(url)
                )
                return err(CLASSIC_TIMEOUT)

            if response.status_code != 200:
                current_app.logger.warning(
                    'ADS Classic returned an unkown status code: "{}" [code: {}]'
                    .format(response.text, response.status_code)
                )
                return err(CLASSIC_UNKNOWN_ERROR)

            data = response.json()

            return data, 200
