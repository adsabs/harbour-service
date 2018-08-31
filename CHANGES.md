# Change Log
All notable changes to the config fileswill be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [1.0.15] - 2018-08-31

* Removed unnecessary requirements

## [1.0.14] - 2018-08-10

* Updated adsmutils requirement

## [1.0.13] - 2018-08-06

* Enabled JSON stdout logging and HTTP connection pool

## [1.0.12] - 2017-12-26

* Updated db objects after migration to ADSFlask

## [1.0.11] - 2017-12-14

* Migrated to ADSFlask

## [1.0.10] - 2017-12-12
 
  * Requirements.txt update and microservice migrated to ADSFlask from adsmutils

## [1.0.9] - 2016-06-17

  * Further config changes due to randomness of deployment

## [1.0.8] - 2016-06-17

  * Changed default config

## [1.0.7] - 2016-06-17

### Changes

  * Modified the authentication end points to use params keywords when building the URL rather than doing it manual. This removes any encoding errors that may occur when building the URL manually.


## [1.0.6] - 2016-04-21

### Changes
  
  * Zip files are now created offline and are served as static files.
  * AWS S3 temporary URLs are given to download statically created files.
  * ADS Classic may or may not give the description of a library, fix added.

## [1.0.5] - 2016-03-11
### Added

  * Authentication end point of ADS 2.0 users, stores email on success

### Changes

  * End points updated to have separate classic and 2.0 auth end points
  * Extra logic added due to the exta fields in the model
  * Models updated to include ADS 2.0 e-mail - migration of database
  * README.md updated for new end point names

## [1.0.4] - 2016-03-09
### Added
  
  * Ability to export ADS2.0 library to Zotero format, in a zip file
  * Tests included

## [1.0.3] - 2016-03-01
### Added

  * Ability to import ADS2.0 libraries from flat files from AWS S3
  * Tests for the new end points

### Changed
  * Naming of the end points

## [1.0.2] - 2015-12-08
### Added

  * A new end point that returns the list of mirrors this service allows
  * Tests for the new end point

### Changed

  * Updated documentation on the workflow

## [1.0.1] - 2015-12-07
### Added

  * CHANGES.md file
  * Migration and database creation scripts
  * File for base class for tests
  * Tests for manage scripts

### Changed

  * Renamed some of the configuration keys

## [1.0.0] - 2015-12-07
### Added

  * First release of harbour service


