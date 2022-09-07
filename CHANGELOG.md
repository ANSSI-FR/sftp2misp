# CHANGELOG

## [1.1.1] 2022-09-07
- Add a verbose command-line option to set logger level at runtime
- The script now download every files in given directories
- Fix the script stopping when encountering a non MISP json file. Instead just log it as an error
- Improved handling of relatives paths for local directory, logging directory and configuration directory


## [1.1.0] 2022-04-22
- Configuration file supports a list of directories
- Add a filter to upload only .json file on disk
- Display an error when incompatible options are given
- Improvement of logging, better categories for each logging type, adding quiet option
- Add a configuration option to bypass proxy access to MISP

## [1.0.0] 2022-03-31
Initial version
