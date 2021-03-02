# encoding: utf-8
import os

# must be here for adsmutils to override it using env vars
# but if left empty (resolving to False) it won't be used
SERVICE_TOKEN = None


LOG_STDOUT = True
ADS_CLASSIC_URL = 'http://{mirror}'
ADS_CLASSIC_LIBRARIES_URL = 'http://{mirror}/cookie={cookie}'
ADS_CLASSIC_MYADS_URL = 'http://{mirror}?{email}'
ADS_CLASSIC_MIRROR_LIST = [
    'astrobib.u-strasbg.fr',
    'ads.nao.ac.jp',
    'ads.astro.puc.cl',
    'esoads.eso.org',
    'ukads.nottingham.ac.uk',
    'ads.iucaa.ernet.in',
    'ads.inasan.ru',
    'ads.bao.ac.cn',
    'ads.mao.kiev.ua',
    'ads.ari.uni-heidelberg.de',
    'ads.arsip.lipi.go.id',
    'ads.on.br',
    'saaoads.chpc.ac.za',
    'adsabs.harvard.edu'
]
ADS_TWO_POINT_OH_S3_MONGO_BUCKET = 'adsabs-mongogut'
ADS_TWO_POINT_OH_LOADED_USERS = False
ADS_TWO_POINT_OH_USERS = {}
ADS_TWO_POINT_OH_MIRROR = 'adsabs.harvard.edu'

SQLALCHEMY_DATABASE_URI = ""
SQLALCHEMY_TRACK_MODIFICATIONS = False

HARBOUR_EXPORT_SERVICE_URL = 'http://fakeapi.adsabs.harvard.edu/v1/export'
HARBOUR_EXPORT_TYPES = ['zotero', 'mendeley']

ENVIRONMENT = os.getenv('ENVIRONMENT', 'staging').lower()
