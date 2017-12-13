# encoding: utf-8
"""
Test webservices
"""

import mock
import json
import boto3
import unittest

from moto import mock_s3
from base import TestBaseDatabase
from flask import url_for
from harbour.models import Users
from harbour.http_errors import CLASSIC_AUTH_FAILED, CLASSIC_DATA_MALFORMED, \
    CLASSIC_TIMEOUT, CLASSIC_BAD_MIRROR, CLASSIC_NO_COOKIE, \
    CLASSIC_UNKNOWN_ERROR, NO_CLASSIC_ACCOUNT, NO_TWOPOINTOH_LIBRARIES, \
    NO_TWOPOINTOH_ACCOUNT, TWOPOINTOH_AWS_PROBLEM, EXPORT_SERVICE_FAIL, \
    TWOPOINTOH_WRONG_EXPORT_TYPE
from stub_response import ads_classic_200, ads_classic_unknown_user, \
    ads_classic_wrong_password, ads_classic_no_cookie, ads_classic_fail, \
    ads_classic_libraries_200, export_success, export_success_no_keyword
from httmock import HTTMock
from zipfile import ZipFile
from StringIO import StringIO
from requests.exceptions import Timeout


USER_ID_KEYWORD = 'X-Adsws-Uid'


class TestClassicUser(TestBaseDatabase):
    """
    Tests HTTP end point to obtain the ADS classic user that the user has
    currently stored in the service
    """

    def test_user_successfully_retrieves_ads_classic_settings(self):
        """
        Tests that the user successfully retrieves their settings for the ADS
        Classic service
        """
        # Stub data
        user = Users(
            absolute_uid=10,
            classic_email='user@ads.com',
            classic_cookie='some cookie',
            classic_mirror='mirror.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            # Ask the end point
            url = url_for('classicuser')
            r = self.client.get(url, headers={USER_ID_KEYWORD: 10})

            # Check we get what we expected
            self.assertStatus(r, 200)
            self.assertEqual(r.json['classic_email'], user.classic_email)
            self.assertEqual(r.json['classic_mirror'], user.classic_mirror)
            self.assertEqual(r.json['twopointoh_email'], '')

    def test_get_a_400_when_the_user_does_not_exist(self):
        """
        Test that there is a 400 returned when the user has not saved any ADS
        Classic account to the service
        """
        # Ask the end point
        url = url_for('classicuser')
        r = self.client.get(url, headers={USER_ID_KEYWORD: 10})

        self.assertStatus(r, NO_CLASSIC_ACCOUNT['code'])
        self.assertEqual(r.json['error'], NO_CLASSIC_ACCOUNT['message'])


class TestAllowedMirrors(TestBaseDatabase):
    """
    Tests HTTP end point to obtain the ADS classic user that the user has
    currently stored in the service
    """

    def test_user_successfully_retrieves_a_list_of_classic_mirrors(self):
        """
        Tests that a user can successfully retrieve a list of available ADS
        Classic mirrors, that are valid for this service.
        """
        url = url_for('allowedmirrors')
        r = self.client.get(url)

        # Check we get what we expected
        self.assertStatus(r, 200)
        self.assertListEqual(r.json, self.app.config['ADS_CLASSIC_MIRROR_LIST'])


class TestAuthenticateUserClassic(TestBaseDatabase):
    """
    Tests http endpoints
    """

    def test_user_authentication_success(self):
        """
        Tests the end point of a user authenticating their ADS credentials via
        the web app
        """

        # 1. The user fills in their credentials
        # 2. The user submits their credentials to the end point
        url = url_for('authenticateuserclassic')

        with HTTMock(ads_classic_200):
            r = self.client.post(
                url,
                data=self.stub_user_data,
                headers={USER_ID_KEYWORD: 10}
            )

        self.assertStatus(r, 200)

        self.assertEqual(
            r.json['classic_email'],
            self.stub_user_data['classic_email']
        )
        self.assertTrue(r.json['classic_authed'])

        user = Users.query.filter(Users.absolute_uid == 10).one()
        self.assertEqual(
            user.classic_email,
            self.stub_user_data['classic_email']
        )
        self.assertEqual(
            user.classic_mirror,
            self.stub_user_data['classic_mirror']
        )
        self.assertIsInstance(user.classic_cookie, unicode)

    def test_user_authentication_success_if_user_already_exists(self):
        """
        Tests the end point of a user authenticating their ADS credentials via
        the web app, assuming that they have previously set something before
        """
        # Stub out the user in the database
        user = Users(
            absolute_uid=10,
            classic_email='before@ads.com',
            classic_cookie='some cookie',
            classic_mirror='other.mirror.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            # 1. The user fills in their credentials
            # 2. The user submits their credentials to the end point
            url = url_for('authenticateuserclassic')

            with HTTMock(ads_classic_200):
                r = self.client.post(
                    url,
                    data=self.stub_user_data,
                    headers={USER_ID_KEYWORD: 10}
                )

            self.assertStatus(r, 200)

            self.assertEqual(
                r.json['classic_email'],
                self.stub_user_data['classic_email']
            )
            self.assertTrue(r.json['classic_authed'])

            r_user = Users.query.filter(Users.absolute_uid == 10).one()

            self.assertEqual(
                r_user.classic_email,
                self.stub_user_data['classic_email']
            )
            self.assertEqual(
                r_user.classic_mirror,
                self.stub_user_data['classic_mirror']
            )
            self.assertIsInstance(r_user.classic_cookie, unicode)

    def test_user_authentication_fails_when_user_already_exists(self):
        """
        Tests the end point of a user authenticating their ADS credentials via
        the web app, assuming that they have previously set something before.
        This is the scenario in which there is a failure, the credentials remain
        the same in the database
        """
        # Stub out the user in the database
        user = Users(
            absolute_uid=10,
            classic_email='before@ads.com',
            classic_cookie='some cookie',
            classic_mirror='other.mirror.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            # 1. The user fills in their credentials
            # 2. The user submits their credentials to the end point
            url = url_for('authenticateuserclassic')

            possible_failures = [
                ads_classic_fail,
                ads_classic_no_cookie,
                ads_classic_unknown_user,
                ads_classic_wrong_password
            ]
            for fail_response in possible_failures:
                with HTTMock(fail_response):
                    self.client.post(
                        url,
                        data=self.stub_user_data,
                        headers={USER_ID_KEYWORD: 10}
                    )

                r_user = Users.query.filter(Users.absolute_uid == 10).one()
                self.assertEqual(r_user, user)

    def test_user_authentication_unknown_user(self):
        """
        Tests the end point of a user authenticating their ADS credentials via
        the web app
        """
        url = url_for('authenticateuserclassic')

        with HTTMock(ads_classic_unknown_user):
            r = self.client.post(url, data=self.stub_user_data)

        self.assertStatus(r, CLASSIC_AUTH_FAILED['code'])
        self.assertEqual(r.json['error'], CLASSIC_AUTH_FAILED['message'])

    def test_user_authentication_wrong_password(self):
        """
        Tests the end point of a user authenticating their ADS credentials via
        the web app
        """
        url = url_for('authenticateuserclassic')

        with HTTMock(ads_classic_wrong_password):
            r = self.client.post(url, data=self.stub_user_data)

        self.assertStatus(r, CLASSIC_AUTH_FAILED['code'])
        self.assertEqual(r.json['error'], CLASSIC_AUTH_FAILED['message'])

    @mock.patch('harbour.views.requests.post')
    def test_ads_classic_timeout(self, mocked_post):
        """
        Test that the service catches timeouts and returns a HTTP error response
        """
        mocked_post.side_effect = Timeout

        url = url_for('authenticateuserclassic')
        r = self.client.post(url, data=self.stub_user_data)

        self.assertStatus(r, CLASSIC_TIMEOUT['code'])
        self.assertEqual(r.json['error'], CLASSIC_TIMEOUT['message'])

    def test_missing_data_given_fails(self):
        """
        Pass data that is missing content that is needed
        """
        url = url_for('authenticateuserclassic')

        data1 = {'classic_email': 'email'}
        data2 = {'classic_password': 'password'}
        data3 = {'classic_mirror': 'mirror'}
        data4 = {'classic_password': 'password', 'classic_mirror': 'mirror'}
        data5 = {'classic_email': 'email', 'classic_password': 'password'}
        data6 = {'cassic_email': 'email', 'clasic_mirror': 'mirror'}
        data7 = {}
        data_list = [data1, data2, data3, data4, data5, data6, data7]

        for data in data_list:
            r = self.client.post(url, data=data)
            self.assertStatus(r, CLASSIC_DATA_MALFORMED['code'])
            self.assertEqual(r.json['error'], CLASSIC_DATA_MALFORMED['message'])

    def test_mismatching_emails_on_auth(self):
        """
        Just a sanity check that if the e-mail sent, and the e-mail returned
        after authentification, match one another
        """
        # 1. The user fills in their credentials
        user_data = self.stub_user_data.copy()
        user_data['classic_email'] = 'different@email.com'

        # 2. The user submits their credentials to the end point
        url = url_for('authenticateuserclassic')

        with HTTMock(ads_classic_200):
            r = self.client.post(url, data=user_data)

        self.assertStatus(r, CLASSIC_AUTH_FAILED['code'])
        self.assertEqual(r.json['error'], CLASSIC_AUTH_FAILED['message'])

    def test_incorrect_mirror_given(self):
        """
        Tests that an HTTP error is given if the mirror site is not known
        """
        # 1. The user fills in their credentials
        user_data = self.stub_user_data.copy()
        user_data['classic_mirror'] = 'nonexistentmirror'

        # 2. The user submits their credentials to the end point
        url = url_for('authenticateuserclassic')
        r = self.client.post(url, data=user_data)

        self.assertStatus(r, CLASSIC_BAD_MIRROR['code'])
        self.assertEqual(r.json['error'], CLASSIC_BAD_MIRROR['message'])

    def test_classic_does_not_return_cookie(self):
        """
        In the (unlikely) scenario that ADS Classic does not return a cookie for
        the user, we need to handle that
        """
        url = url_for('authenticateuserclassic')
        with HTTMock(ads_classic_no_cookie):
            r = self.client.post(url, data=self.stub_user_data)
        self.assertStatus(r, CLASSIC_NO_COOKIE['code'])
        self.assertEqual(r.json['error'], CLASSIC_NO_COOKIE['message'])

    def test_ads_classic_any_non_unknown_response(self):
        """
        Test that the error message for an unknown error from myADS is returned.
        When we know the exact errors, this message can be updated to be more
        specific
        """
        url = url_for('authenticateuserclassic')

        with HTTMock(ads_classic_fail):
            r = self.client.post(url, data=self.stub_user_data)

        self.assertStatus(r, CLASSIC_UNKNOWN_ERROR['code'])
        self.assertIn(CLASSIC_UNKNOWN_ERROR['message'], r.json['error'])

        self.assertIn('ads_classic', r.json)
        self.assertIn('message', r.json['ads_classic'])
        self.assertIn('status_code', r.json['ads_classic'])


class TestAuthenticateUserTwoPointOh(TestBaseDatabase):
    """
    Tests http endpoints
    """

    def test_user_authentication_success(self):
        """
        Tests the end point of a user authenticating their ADS credentials via
        the web app
        """

        # 1. The user fills in their credentials
        # 2. The user submits their credentials to the end point
        url = url_for('authenticateusertwopointoh')

        with HTTMock(ads_classic_200):
            r = self.client.post(
                url,
                data=self.stub_user_data_2p0,
                headers={USER_ID_KEYWORD: 10}
            )

        self.assertStatus(r, 200)

        self.assertEqual(
            r.json['twopointoh_email'],
            self.stub_user_data_2p0['twopointoh_email']
        )
        self.assertTrue(r.json['twopointoh_authed'])

        user = Users.query.filter(Users.absolute_uid == 10).one()
        self.assertEqual(
            user.twopointoh_email,
            self.stub_user_data_2p0['twopointoh_email']
        )

    def test_user_authentication_success_if_user_already_exists(self):
        """
        Tests the end point of a user authenticating their ADS 2.0 credentials via
        the web app, assuming that they have previously set something before
        """
        # Stub out the user in the database
        user = Users(
            absolute_uid=10,
            twopointoh_email='before@ads.com',
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            # 1. The user fills in their credentials
            # 2. The user submits their credentials to the end point
            url = url_for('authenticateusertwopointoh')

            with HTTMock(ads_classic_200):
                r = self.client.post(
                    url,
                    data=self.stub_user_data_2p0,
                    headers={USER_ID_KEYWORD: 10}
                )

            self.assertStatus(r, 200)

            self.assertEqual(
                r.json['twopointoh_email'],
                self.stub_user_data_2p0['twopointoh_email']
            )
            self.assertTrue(r.json['twopointoh_authed'])

            r_user = Users.query.filter(Users.absolute_uid == 10).one()

            self.assertEqual(
                r_user.twopointoh_email,
                self.stub_user_data_2p0['twopointoh_email']
            )

    def test_user_authentication_fails_when_user_already_exists(self):
        """
        Tests the end point of a user authenticating their ADS credentials via
        the web app, assuming that they have previously set something before.
        This is the scenario in which there is a failure, the credentials remain
        the same in the database
        """
        # Stub out the user in the database
        user = Users(
            absolute_uid=10,
            twopointoh_email='before@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            # 1. The user fills in their credentials
            # 2. The user submits their credentials to the end point
            url = url_for('authenticateusertwopointoh')

            possible_failures = [
                ads_classic_fail,
                ads_classic_unknown_user,
                ads_classic_wrong_password
            ]
            for fail_response in possible_failures:
                with HTTMock(fail_response):
                    self.client.post(
                        url,
                        data=self.stub_user_data_2p0,
                        headers={USER_ID_KEYWORD: 10}
                    )

                r_user = Users.query.filter(Users.absolute_uid == 10).one()
                self.assertEqual(r_user.twopointoh_email, 'before@ads.com')

    def test_user_authentication_unknown_user(self):
        """
        Tests the end point of a user authenticating their ADS credentials via
        the web app
        """
        url = url_for('authenticateusertwopointoh')

        with HTTMock(ads_classic_unknown_user):
            r = self.client.post(url, data=self.stub_user_data_2p0)

        self.assertStatus(r, CLASSIC_AUTH_FAILED['code'])
        self.assertEqual(r.json['error'], CLASSIC_AUTH_FAILED['message'])

    def test_user_authentication_wrong_password(self):
        """
        Tests the end point of a user authenticating their ADS credentials via
        the web app
        """
        url = url_for('authenticateusertwopointoh')

        with HTTMock(ads_classic_wrong_password):
            r = self.client.post(url, data=self.stub_user_data_2p0)

        self.assertStatus(r, CLASSIC_AUTH_FAILED['code'])
        self.assertEqual(r.json['error'], CLASSIC_AUTH_FAILED['message'])

    @mock.patch('harbour.views.requests.post')
    def test_ads_classic_timeout(self, mocked_post):
        """
        Test that the service catches timeouts and returns a HTTP error response
        """
        mocked_post.side_effect = Timeout

        url = url_for('authenticateusertwopointoh')
        r = self.client.post(url, data=self.stub_user_data_2p0)

        self.assertStatus(r, CLASSIC_TIMEOUT['code'])
        self.assertEqual(r.json['error'], CLASSIC_TIMEOUT['message'])

    def test_missing_data_given_fails(self):
        """
        Pass data that is missing content that is needed
        """
        url = url_for('authenticateusertwopointoh')

        data1 = {'twopointoh_email': 'email'}
        data2 = {'twopointoh_password': 'password'}
        data3 = {}
        data_list = [data1, data2, data3]

        for data in data_list:
            r = self.client.post(url, data=data)
            self.assertStatus(r, CLASSIC_DATA_MALFORMED['code'])
            self.assertEqual(r.json['error'], CLASSIC_DATA_MALFORMED['message'])

    def test_mismatching_emails_on_auth(self):
        """
        Just a sanity check that if the e-mail sent, and the e-mail returned
        after authentification, match one another
        """
        # 1. The user fills in their credentials
        user_data = self.stub_user_data_2p0.copy()
        user_data['twopointoh_email'] = 'different@email.com'

        # 2. The user submits their credentials to the end point
        url = url_for('authenticateusertwopointoh')

        with HTTMock(ads_classic_200):
            r = self.client.post(url, data=user_data)

        self.assertStatus(r, CLASSIC_AUTH_FAILED['code'])
        self.assertEqual(r.json['error'], CLASSIC_AUTH_FAILED['message'])

    def test_ads_classic_any_non_unknown_response(self):
        """
        Test that the error message for an unknown error from myADS is returned.
        When we know the exact errors, this message can be updated to be more
        specific
        """
        url = url_for('authenticateusertwopointoh')

        with HTTMock(ads_classic_fail):
            r = self.client.post(url, data=self.stub_user_data_2p0)

        self.assertStatus(r, CLASSIC_UNKNOWN_ERROR['code'])
        self.assertIn(CLASSIC_UNKNOWN_ERROR['message'], r.json['error'])

        self.assertIn('ads_classic', r.json)
        self.assertIn('message', r.json['ads_classic'])
        self.assertIn('status_code', r.json['ads_classic'])


class TestADSTwoPointOhLibraries(TestBaseDatabase):
    """
    Tests the libraries end point that returns the libraries from ADS 2.0
    that belong to a user
    """

    @mock_s3
    def create_app(self):
        """
        Create the wsgi application
        """
        # Setup S3 mock data
        TestADSTwoPointOhLibraries.helper_s3_mock_setup()

        # Setup the app
        app_ = super(TestADSTwoPointOhLibraries, self).create_app()

        return app_

    @staticmethod
    def helper_s3_mock_setup():
        """
        Setup the S3 buckets required for tests
        """
        # Stub data needed for create app
        stub_mongogut_users = {
            'user@ads.com': 'cb16a523-cdba-406b-bfff-edfd428248be.json'
        }
        stub_mongogut_library = [
                {
                    'name': 'Name',
                    'description': 'Description',
                    'documents': [
                        '2015MNRAS.446.4239E', '2015A&C....10...61E',
                        '2014A&A...562A.100E', '2013A&A...556A..23E'
                    ]
                }
            ]

        s3_resource = boto3.resource('s3')
        s3_resource.create_bucket(Bucket='adsabs-mongogut')
        bucket = s3_resource.Bucket('adsabs-mongogut')

        # First is libraries
        bucket.put_object(
            Key='users.json',
            Body=json.dumps(stub_mongogut_users)
        )

        # Second is the libraries
        bucket.put_object(
            Key='cb16a523-cdba-406b-bfff-edfd428248be.json',
            Body=json.dumps(stub_mongogut_library)
        )

    @mock_s3
    def test_get_libraries_end_point(self):
        """
        Test the workflow of successfully retrieving a set of ADS 2.0 libraries
        """
        # Setup S3 mock data
        TestADSTwoPointOhLibraries.helper_s3_mock_setup()

        # Expected stub data
        stub_get_libraries = {
            'libraries': [
                {
                    'name': 'Name',
                    'description': 'Description',
                    'documents': [
                        '2015MNRAS.446.4239E', '2015A&C....10...61E',
                        '2014A&A...562A.100E', '2013A&A...556A..23E'
                    ]
                }
            ]
        }

        # 1. The user is identified via header information
        # - Generate dummy user in database
        # - Give the header the correct information
        user = Users(
            absolute_uid=10,
            twopointoh_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            url = url_for('twopointohlibraries', uid=10)
            r = self.client.get(url)

            self.assertStatus(r, 200)
            self.assertEqual(r.json['libraries'], stub_get_libraries['libraries'])

    def test_get_libraries_end_point_when_no_user(self):
        """
        Test when this user does not have any libraries
        """
        # 1. The user is identified via header information
        # - Generate dummy user in database
        # - Give the header the correct information
        user = Users(
            absolute_uid=10,
            twopointoh_email='user_no_library@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            url = url_for('twopointohlibraries', uid=10)
            r = self.client.get(url)

            self.assertStatus(r, NO_TWOPOINTOH_LIBRARIES['code'])
            self.assertEqual(r.json['error'], NO_TWOPOINTOH_LIBRARIES['message'])

    def test_get_libraries_end_point_when_no_user_but_is_classic(self):
        """
        Test when this user does not have any libraries, but has Classic account
        """
        # 1. The user is identified via header information
        # - Generate dummy user in database
        # - Give the header the correct information
        user = Users(
            absolute_uid=10,
            classic_cookie='ef9df8ds',
            classic_mirror='mirror.com',
            classic_email='user_no_library@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            url = url_for('twopointohlibraries', uid=10)
            r = self.client.get(url)

            self.assertStatus(r, NO_TWOPOINTOH_ACCOUNT['code'])
            self.assertEqual(r.json['error'], NO_TWOPOINTOH_ACCOUNT['message'])

    def test_get_libraries_end_point_when_no_classic_auth(self):
        """
        Test when this user has not got an associated ADS 2.0 (classic) account
        """
        url = url_for('twopointohlibraries', uid=10)
        r = self.client.get(url)

        self.assertStatus(r, NO_TWOPOINTOH_ACCOUNT['code'])
        self.assertEqual(r.json['error'], NO_TWOPOINTOH_ACCOUNT['message'])

    @mock.patch('harbour.app.boto3.resource')
    def test_get_libraries_end_point_when_aws_s3_error(self, mock_resource):
        """
        Test when this user has not associated any ADS 2.0 (classic) account
        """
        mock_resource.side_effect = Exception('Custom Error')

        user = Users(
            absolute_uid=10,
            twopointoh_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            url = url_for('twopointohlibraries', uid=10)
            r = self.client.get(url)

            self.assertStatus(r, TWOPOINTOH_AWS_PROBLEM['code'])
            self.assertEqual(r.json['error'], TWOPOINTOH_AWS_PROBLEM['message'])

    def test_get_libraries_end_point_when_users_have_not_loaded(self):
        """
        Test when this user has not got an associated ADS 2.0 (classic) account
        """
        self.assertTrue(self.app.config['ADS_TWO_POINT_OH_LOADED_USERS'])
        self.app.config['ADS_TWO_POINT_OH_LOADED_USERS'] = False

        url = url_for('twopointohlibraries', uid=10)
        r = self.client.get(url)

        self.assertStatus(r, TWOPOINTOH_AWS_PROBLEM['code'])
        self.assertEqual(r.json['error'], TWOPOINTOH_AWS_PROBLEM['message'])


class TestExportADSTwoPointOhLibraries(TestBaseDatabase):
    """
    Tests the end point that facilitates the export of libraries from ADS 2.0
    to external third-party software.
    """
    @staticmethod
    def helper_s3_mock_setup():
        """
        Setup the S3 buckets required for tests
        """
        # Stub data needed for create app
        stub_mongogut_users = {
            'user@ads.com': 'cb16a523-cdba-406b-bfff-edfd428248be.json'
        }
        # stub_mongogut_library = [
        #         {
        #             'name': 'Name',
        #             'description': 'Description',
        #             'documents': {
        #                 '2015MNRAS.446.4239E': {
        #                     'tags': ['tag1', 'tag2'],
        #                     'notes': ['note1', 'note2']
        #                 },
        #                 '2015A&C....10...61E': {
        #                     'tags': [],
        #                     'notes': []
        #                 }
        #             }
        #         },
        #         {
        #             'name': 'Name2',
        #             'description': 'Description2',
        #             'documents': {
        #                 '2015MNRAS.446.4239E': {
        #                     'tags': [],
        #                     'notes': []
        #                 },
        #                 '2015A&C....10...61E': {
        #                     'tags': [],
        #                     'notes': []
        #                 }
        #             }
        #         }
        #     ]
        # zip_io = StringIO()
        # zip_file = ZipFile(zip_io, 'a')
        # zip_file.writestr('Name.bib', 'keywords = {tag1, tag2}\nnotes = {note1, note2}')
        # zip_file.writestr('Name2.bib', '\nnotes')
        # zip_file.close()
        # zip_io.seek(0)

        s3_resource = boto3.resource('s3')
        s3_resource.create_bucket(Bucket='adsabs-mongogut')
        bucket = s3_resource.Bucket('adsabs-mongogut')

        # First is libraries
        bucket.put_object(
            Key='users.json',
            Body=json.dumps(stub_mongogut_users)
        )

        # Second is the libraries
        # bucket.put_object(
        #     Key='cb16a523-cdba-406b-bfff-edfd428248be.zotero.zip',
        #     Body=zip_io.getvalue()
        # )

    @mock_s3
    def create_app(self):
        """
        Create the wsgi application
        """
        # Setup S3 mock data
        TestExportADSTwoPointOhLibraries.helper_s3_mock_setup()

        # Setup the app
        app_ = super(TestExportADSTwoPointOhLibraries, self).create_app()
        return app_

    @mock_s3
    @unittest.skip('Deprecated')
    def test_get_zotero_export_successfully(self):
        """
        Test that a user can get the expected zotero export. They press a
        button, which results in a zip file being returned. Within the zip file
        is a list of files, each one is a .bib file that corresponds to a
        library that a user had.
        """
        # Stub out the user in the database
        user = Users(
            absolute_uid=10,
            twopointoh_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            # Setup S3 storage
            TestExportADSTwoPointOhLibraries.helper_s3_mock_setup()

            url = url_for('exporttwopointohlibraries', export='zotero')

            with HTTMock(export_success):
                r = self.client.get(
                    url,
                    headers={USER_ID_KEYWORD: user.absolute_uid}
                )

            self.assertStatus(r, 200)
            self.assertIn('Content-Disposition', r.headers)
            self.assertEqual(
                r.headers['Content-Disposition'],
                'attachment; filename=user_zotero.zip'
            )

            zip_file = ZipFile(StringIO(r.get_data()))
            zip_content = {name: zip_file.read(name) for name in zip_file.namelist()}
            self.assertEqual(
                zip_content.keys(),
                ['Name.bib', 'Name2.bib']
            )

            self.assertIn('tag1, tag2', zip_content['Name.bib'])
            self.assertIn('notes = {note1, note2}', zip_content['Name.bib'])

            self.assertNotIn('tag1', zip_content['Name2.bib'],)
            self.assertNotIn('notes =', zip_content['Name2.bib'])

    @mock_s3
    @unittest.skip('Deprecated')
    def test_get_zotero_export_successfully_when_no_keyword(self):
        """
        Test that a user can get the expected zotero export. They press a
        button, which results in a zip file being returned. Within the zip file
        is a list of files, each one is a .bib file that corresponds to a
        library that a user had.
        """
        # Stub out the user in the database
        user = Users(
            absolute_uid=10,
            twopointoh_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            # Setup S3 storage
            TestExportADSTwoPointOhLibraries.helper_s3_mock_setup()

            url = url_for('exporttwopointohlibraries', export='zotero')

            with HTTMock(export_success_no_keyword):
                r = self.client.get(
                    url,
                    headers={USER_ID_KEYWORD: user.absolute_uid}
                )

            self.assertStatus(r, 200)
            self.assertIn('Content-Disposition', r.headers)
            self.assertEqual(
                r.headers['Content-Disposition'],
                'attachment; filename=user_zotero.zip'
            )

            zip_file = ZipFile(StringIO(r.get_data()))
            zip_content = {name: zip_file.read(name) for name in zip_file.namelist()}
            self.assertEqual(
                zip_content.keys(),
                ['Name.bib', 'Name2.bib']
            )

            self.assertIn('keywords = {tag1, tag2}', zip_content['Name.bib'],)
            self.assertIn('notes = {note1, note2}', zip_content['Name.bib'])

            self.assertNotIn('tag1', zip_content['Name2.bib'],)
            self.assertNotIn('notes =', zip_content['Name2.bib'])

    @mock.patch('harbour.views.boto3.client')
    def test_get_export_end_point_when_aws_s3_error(self, mock_resource):
        """
        Test when there is an issue loading/accessing S3 storage
        """
        mock_resource.side_effect = Exception('Custom Error')

        user = Users(
            absolute_uid=10,
            twopointoh_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            url = url_for('exporttwopointohlibraries', export='zotero')
            r = self.client.get(url, headers={USER_ID_KEYWORD: user.absolute_uid})

            self.assertStatus(r, TWOPOINTOH_AWS_PROBLEM['code'])
            self.assertEqual(r.json['error'], TWOPOINTOH_AWS_PROBLEM['message'])

    def test_get_libraries_end_point_when_users_have_not_loaded(self):
        """
        Test when this user has not got an associated ADS 2.0 (classic) account
        """
        self.assertTrue(self.app.config['ADS_TWO_POINT_OH_LOADED_USERS'])
        self.app.config['ADS_TWO_POINT_OH_LOADED_USERS'] = False

        url = url_for('exporttwopointohlibraries', export='zotero')
        r = self.client.get(url, headers={USER_ID_KEYWORD: 10})

        self.assertStatus(r, TWOPOINTOH_AWS_PROBLEM['code'])
        self.assertEqual(r.json['error'], TWOPOINTOH_AWS_PROBLEM['message'])

    def test_user_requests_wrong_export_type(self):
        """
        The user should not receive anything if they request an export format
        that does not exist
        """
        url = url_for('exporttwopointohlibraries', export='fudge')
        r = self.client.get(url, headers={USER_ID_KEYWORD: 10})

        self.assertStatus(r, 400)
        self.assertEqual(
            r.json['error'],
            TWOPOINTOH_WRONG_EXPORT_TYPE['message']
        )

    @mock_s3
    def test_get_temporary_url_on_export(self):
        """
        The user should receive a temporary url when asking for an export
        """
        # Stub out the user in the database
        user = Users(
            absolute_uid=10,
            twopointoh_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            # Setup S3 storage
            TestExportADSTwoPointOhLibraries.helper_s3_mock_setup()

            url = url_for('exporttwopointohlibraries', export='zotero')
            r = self.client.get(url, headers={USER_ID_KEYWORD: 10})
            self.assertIn(
                'https://adsabs-mongogut.s3.amazonaws.com/cb16a523-cdba-406b-bfff-edfd428248be.zotero.zip',
                r.json['url'],
            )


class TestClassicLibraries(TestBaseDatabase):
    """
    Tests the libraries end point that returns the libraries from ADS classic
    that belong to a user
    """
    def test_get_libraries_end_point(self):
        """
        Test the workflow of successfully retrieving a set of classic libraries
        """
        stub_get_libraries = {
            'libraries': [
                {
                    'name': 'Name',
                    'description': 'Description',
                    'documents': [
                        '2015MNRAS.446.4239E', '2015A&C....10...61E',
                        '2014A&A...562A.100E', '2013A&A...556A..23E'
                    ]
                }
            ]
        }

        # 1. The user is identified via header information
        # - Generate dummy user in database
        # - Give the header the correct information
        user = Users(
            absolute_uid=10,
            classic_cookie='ef9df8ds',
            classic_mirror='mirror.com',
            classic_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            # 2. The database is checked to see if the user exists, and the cookie
            # retrieved
            #  3. The ADS Classic end point is contacted, returning a 200, and the
            # content returned
            url = url_for('classiclibraries', uid=10)
            with HTTMock(ads_classic_libraries_200):
                r = self.client.get(url)
            self.assertStatus(r, 200)
            self.assertEqual(r.json['libraries'], stub_get_libraries['libraries'])

    def test_get_libraries_when_the_user_does_not_exist(self):
        """
        Test that when a user does not exist within the database, that the
        libraries end point returns a known error message
        """
        url = url_for('classiclibraries', uid=10)
        r = self.client.get(url)

        self.assertStatus(r, NO_CLASSIC_ACCOUNT['code'])
        self.assertEqual(r.json['error'], NO_CLASSIC_ACCOUNT['message'])

    def test_get_libraries_end_point_when_no_user_but_is_twopointoh(self):
        """
        Test when this user does not have a Classic account, but a 2.0 account
        """
        # 1. The user is identified via header information
        # - Generate dummy user in database
        # - Give the header the correct information
        user = Users(
            absolute_uid=10,
            twopointoh_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            url = url_for('classiclibraries', uid=10)
            r = self.client.get(url)

            self.assertStatus(r, NO_CLASSIC_ACCOUNT['code'])
            self.assertEqual(r.json['error'], NO_CLASSIC_ACCOUNT['message'])

    @mock.patch('harbour.views.requests.get')
    def test_get_libraries_when_ads_classic_timesout(self, mocked_get):
        """
        Test that if ADS Classic times out before finishing the request, that
        the libraries end point returns a known error
        """
        user = Users(
            absolute_uid=10,
            classic_cookie='ef9df8ds',
            classic_mirror='mirror.com',
            classic_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            mocked_get.side_effect = Timeout

            url = url_for('classiclibraries', uid=10)

            r = self.client.get(url)

            self.assertStatus(r, CLASSIC_TIMEOUT['code'])
            self.assertEqual(r.json['error'], CLASSIC_TIMEOUT['message'])

    def test_get_libraries_when_ads_classic_returns_non_200(self):
        """
        Tests that the expected response is returned when ADS classic returns a
        non-200 response
        """
        user = Users(
            absolute_uid=10,
            classic_cookie='ef9df8ds',
            classic_mirror='mirror.com',
            classic_email='user@ads.com'
        )
        with self.app.session_scope() as session:
            session.add(user)
            session.commit()

            url = url_for('classiclibraries', uid=10)
            with HTTMock(ads_classic_fail):
                r = self.client.get(url, headers={USER_ID_KEYWORD: 10})

            self.assertStatus(r, CLASSIC_UNKNOWN_ERROR['code'])
            self.assertEqual(r.json['error'], CLASSIC_UNKNOWN_ERROR['message'])
