# encoding: utf-8
"""
Stub data for all the tests
"""

stub_classic_success = {
    "email": "user@ads.com",
    "cookie": "50eefa48dc",
    "tmp_cookie": "",
    "openurl_srv": "",
    "openurl_icon": "",
    "loggedin": "1",
    "myadsid": "352401271",
    "lastname": "",
    "firstname": "",
    "fullname": "",
    "message": "LOGGED_IN",
    "request": {
        "man_cookie": "",
        "man_email": "roman.chyla@gmail.com",
        "man_nemail": "",
        "man_passwd": "******",
        "man_npasswd": "",
        "man_vpasswd": "",
        "man_name": "",
        "man_url": "http://adsabs.harvard.edu",
        "man_cmd": "4"
        }
}

stub_classic_unknown_user = {
      "email": "",
      "cookie": "54050f19fa",
      "tmp_cookie": "",
      "openurl_srv": "",
      "openurl_icon": "",
      "loggedin": "0",
      "myadsid": "0",
      "lastname": "",
      "firstname": "",
      "fullname": "",
      "message": "ACCOUNT_NOTFOUND",
      "request": {
          "man_cookie": "",
          "man_email": "roman.chyla@gmail.comssssss",
          "man_nemail": "",
          "man_passwd": "******",
          "man_npasswd": "",
          "man_vpasswd": "",
          "man_name": "",
          "man_url": "",
          "man_cmd": "4"
       }
}

stub_classic_wrong_password = {
      "email": "user@ads.com",
      "cookie": "50eefa48dc",
      "tmp_cookie": "",
      "openurl_srv": "",
      "openurl_icon": "",
      "loggedin": "0",
      "myadsid": "352401271",
      "lastname": "",
      "firstname": "",
      "fullname": "",
      "message": "WRONG_PASSWORD",
      "request": {
          "man_cookie": "",
          "man_email": "user@ads.com",
          "man_nemail": "",
          "man_passwd": "********",
          "man_npasswd": "",
          "man_vpasswd": "",
          "man_name": "",
          "man_url": "",
          "man_cmd": "4"
       }
}

stub_classic_no_cookie = {
    "email": "user@ads.com",
    "tmp_cookie": "",
    "openurl_srv": "",
    "openurl_icon": "",
    "loggedin": "1",
    "myadsid": "352401271",
    "lastname": "",
    "firstname": "",
    "fullname": "",
    "message": "LOGGED_IN",
    "request": {
        "man_cookie": "",
        "man_email": "roman.chyla@gmail.com",
        "man_nemail": "",
        "man_passwd": "******",
        "man_npasswd": "",
        "man_vpasswd": "",
        "man_name": "",
        "man_url": "http://adsabs.harvard.edu",
        "man_cmd": "4"
        }
}

stub_classic_libraries_success = {
    'count': '2',
    'libraries': [
        {
            'desc': 'Description',
            'entries': [
                {
                    'bibcode': '2015MNRAS.446.4239E'
                },
                {
                    'bibcode': '2015A&C....10...61E'
                },
                {
                    'bibcode': '2014A&A...562A.100E'
                },
                {
                    'bibcode': '2013A&A...556A..23E'
                }
            ],
            'lastmod': '01-Dec-2015',
            'name': 'Name'
        }
    ],
    'owner': 'Owner',
    'pubid': 'ID',
    'status': {
        'cookie': 'ef9df8ds',
        'libfile': '/file/on/disk',
        'query_string': 'cookie=ef9df8ds',
        'server': 'server',
        'timestamp': 'Tue Dec  1 11:37:39 2015'
    },
    'uid': 'ID'
}

stub_classic_myads_success = {u'pre_aut,': u'Henneken, Edwin\r\nKurtz, Michael J.\r\nHernquist, L.\r\nIcke, V.\r\nMellema, G.\r\nRosvall, Martin\r\nBergstrom, Carl\r\nNewman, Mark', u'firstname': u'Edwin', u'phy_t1,': u'bibliometrics\r\ninformetrics\r\neigenfactor\r\nrecommendation\r\n=citation\r\n"digital library"', u'ast_t1,': u'bibliometrics\r\ninformetrics\r\neigenfactor\r\nrecommendation\r\n=citation\r\n"digital library"', u'phy_aut,': u'Henneken, Edwin\r\nKurtz, Michael J.\r\nHernquist, L.\r\nIcke, V.\r\nMellema, G.\r\nRosvall, Martin\r\nBergstrom, Carl\r\nNewman, Mark', u'ast_aut,': u'Henneken, Edwin\r\nKurtz, Michael J.\r\nHernquist, L.\r\nIcke, V.\r\nMellema, G.\r\nRosvall, Martin\r\nBergstrom, Carl\r\nNewman, Mark', u'phy_t2,': u'"digital library"\r\n"search engine"\r\n"information retrieval"\r\n', u'email': u'ehenneken@gmail.com', u'pre_t1,': u'bibliometrics\r\ninformetrics\r\neigenfactor\r\nrecommendation\r\n=citation\r\n"digital library"', u'daily_t1,': u'"gamma ray bursts"', u'groups': [u'astro-ph', u'cs', u'gr-qc', u'math-ph'], u'lastname': u'Henneken', u'ast_t2,': u'"digital library"\r\n"search engine"\r\n"information retrieval"\r\n', u'pre_t2,': u'"digital library"\r\n"search engine"\r\n"information retrieval"\r\n', u'id': 2093057}

stub_export_success = '{"msg": "Retrieved 2 abstracts, starting with number 1.  Total number selected: 2.", "export": "@ARTICLE{2015A&C....10...61E,\\n   author = {{Elliott}, J. and {de Souza}, R.~S. and {Krone-Martins}, A. and \\n\\t{Cameron}, E. and {Ishida}, E.~E.~O. and {Hilbe}, J.},\\n    title = \\"{The overlooked potential of Generalized Linear Models in astronomy-II: Gamma regression and photometric redshifts}\\",\\n  journal = {Astronomy and Computing},\\narchivePrefix = \\"arXiv\\",\\n   eprint = {1409.7699},\\n primaryClass = \\"astro-ph.IM\\",\\n keywords = {Techniques: photometric, Methods: statistical, Methods: analytical, Galaxies: distances and redshifts},\\n     year = 2015,\\n    month = apr,\\n   volume = 10,\\n    pages = {61-72},\\n      doi = {10.1016/j.ascom.2015.01.002},\\n   adsurl = {http://adsabs.harvard.edu/abs/2015A%26C....10...61E},\\n  adsnote = {Provided by the SAO/NASA Astrophysics Data System}\\n}\\n\\n@ARTICLE{2015MNRAS.446.4239E,\\n   author = {{Elliott}, J. and {Khochfar}, S. and {Greiner}, J. and {Dalla Vecchia}, C.\\n\\t},\\n    title = \\"{The First Billion Years project: gamma-ray bursts at z $\\\\gt$ 5}\\",\\n  journal = {\\\\mnras},\\narchivePrefix = \\"arXiv\\",\\n   eprint = {1408.2526},\\n primaryClass = \\"astro-ph.HE\\",\\n keywords = {gamma-ray burst: general, galaxies: high-redshift, cosmology: miscellaneous},\\n     year = 2015,\\n    month = feb,\\n   volume = 446,\\n    pages = {4239-4249},\\n      doi = {10.1093/mnras/stu2417},\\n   adsurl = {http://adsabs.harvard.edu/abs/2015MNRAS.446.4239E},\\n  adsnote = {Provided by the SAO/NASA Astrophysics Data System}\\n}\\n\\n"}'

stub_export_success_no_keyword = '{"msg": "Retrieved 2 abstracts, starting with number 1.  Total number selected: 2.", "export": "@ARTICLE{2015A&C....10...61E,\\n   author = {{Elliott}, J. and {de Souza}, R.~S. and {Krone-Martins}, A. and \\n\\t{Cameron}, E. and {Ishida}, E.~E.~O. and {Hilbe}, J.},\\n    title = \\"{The overlooked potential of Generalized Linear Models in astronomy-II: Gamma regression and photometric redshifts}\\",\\n  journal = {Astronomy and Computing},\\narchivePrefix = \\"arXiv\\",\\n   eprint = {1409.7699},\\n primaryClass = \\"astro-ph.IM\\",\\n keywords = {Techniques: photometric, Methods: statistical, Methods: analytical, Galaxies: distances and redshifts},\\n     year = 2015,\\n    month = apr,\\n   volume = 10,\\n    pages = {61-72},\\n      doi = {10.1016/j.ascom.2015.01.002},\\n   adsurl = {http://adsabs.harvard.edu/abs/2015A%26C....10...61E},\\n  adsnote = {Provided by the SAO/NASA Astrophysics Data System}\\n}\\n\\n@ARTICLE{2015MNRAS.446.4239E,\\n   author = {{Elliott}, J. and {Khochfar}, S. and {Greiner}, J. and {Dalla Vecchia}, C.\\n\\t},\\n    title = \\"{The First Billion Years project: gamma-ray bursts at z $\\\\gt$ 5}\\",\\n  journal = {\\\\mnras},\\narchivePrefix = \\"arXiv\\",\\n   eprint = {1408.2526},\\n primaryClass = \\"astro-ph.HE\\",\\n      year = 2015,\\n    month = feb,\\n   volume = 446,\\n    pages = {4239-4249},\\n      doi = {10.1093/mnras/stu2417},\\n   adsurl = {http://adsabs.harvard.edu/abs/2015MNRAS.446.4239E},\\n  adsnote = {Provided by the SAO/NASA Astrophysics Data System}\\n}\\n\\n"}'