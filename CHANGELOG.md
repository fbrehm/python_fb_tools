# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-03-13

### Added

* Adding `src/fb_tools/cfg_options/*py` modules for encapsulation options of
  the different config parsers and generators.
* Adding exception classes `ConfigDetectionError`, `ConfigWrongTypeError`,
  `InputFileError`, `InputFileNotExistingError` and `InputFileNotReadableError`
  to module `src/fb_tools/errors.py`.
* Adding classes `InputFileOptionAction`, `OutputFileOptionAction`, `NonNegativeIntegerOptionAction`
  and `RangeOptionAction` to `src/fb_tools/argparse_actions.py`.
* Adding `src/fb_tools/any_config.py` for class `AnyConfigHandler` for reading and writing
  arbitrary configuration files.
* Adding module `src/fb_tools/application/cfg_converter.py` for class `CfgConvertApplication`
  for providing the script config-convert.
* Adding tests fo AnyConfigHandler and CfgConvertApplication.

### Changed

* Using `AnyConfigHandler` in class `BaseMultiConfig` to read configuration files.
* Extending function `pp` in module `src/fb_tools/common.py` for using terminal width.
* Removing BOM on reading text files in class `HandlingObject`.

### Removed

* Removing module `src/fb_tools/multi_config/read.py`, because it was substituted
  by class `AnyConfigHandler`.

## [2.9.5] - 2026-02-24

### Changed

* Renamed directory `test` => `tests` to avoid confusion with git branch **test**.

## [2.9.4] - 2026-02-23

### Changed

* Non change release for triggering build pipelines.

## [2.9.3] - 2026-02-06

### Changed

* Non change release for triggering build pipelines.

## [2.9.2] - 2025-11-24

### Fixed

* Fixing syntax error in `src/fb_tools/xlate.py`.

## [2.9.1] - 2025-10-31

### Fixed

* Fixing `src/fb_tools/xlate.py` for conflicting semver dependency.

## [2.9.0] - 2025-10-27

### Added

* Adding pyproject.toml

### Changed

* Renaming directory `lib` => `src`.
* Updating for new directory structure.
* Changing Github workflow `build-packages` and and .gitlab-ci.yaml to new
  shared workfloww.
* Exec black on all Python sources
* Moving all application modules into `src/fb_tools/application` and
  make entrypoints of them.

### Removed

* Removing setup.py, requirements-test*.txt, get-debian*, get-rpm-*
  and all in bin-build.

## [2.8.1] - 2025-06-13

### Changed

* Allowing wider range of domain part of mailaddresses.
* Updating translations.
* Setting copyright year to 2025.

## [2.8.0] - 2024-11-02

### Added

* Adding constant `RE_FIRST_LINE` to module `fb_tools.common`.
* Adding classes GenericSocketError, SocketReadTimeoutError and
  SocketWriteTimeoutError to module `fb_tools.errors`.
* Adding module `fb_tools.socket_obj` with abstract class `GenericSocket`.
* Adding module `fb_tools.socket_obj.tcp` for classes `TcpSocket`,
  `TcpSocketError` and `CouldNotOpenTcpSocketError`.
* Adding module `fb_tools.socket_obj.unix` for classes `UnixSocketError`,
  `NoSocketFileError`, `NoPermissionsToSocketError` and `UnixSocket`.
* Adding test scripts `test/test_35_sockets.py`,
  `test/test_36_unixsocket.py` and `test/test_37_tcpsocket.py` for testing
  the latter modules and classes.

### Changed

* Extending method `get_address()` of class HandlingObject in module
  `fb_tools.handling_obj`.
* Substituting frank.brehm@pixelpark.com by frank@brehm-online.com in
  script and module documentations.
* Extending module documentation.

## [2.7.0] - 2024-08-15

### Added

* Adding exception `ExitAppError`.
* Adding option to disable secure TLS verification in HTTPS of DynDNS
  requests.
* Adding option to method `get_password()` to class HandlingObject for
  raising an ExitAppError instead of exiting on KeyboardInterrupt.
* Adding script bin/show-spinner and its application module
  `fb_tools.show_spinner_app`.

## [2.6.3] - 2024-07-25

### Fixed

* Fixing search for locales dir in `lib/fb_tools/xlate.py`.

## [2.6.2] - 2024-07-21

### Added

* Adding module `fb_tools.spinner`.

## [2.6.1] - 2021-07-01

### Changed

* Setting shared Gitlab workflow to branch main.

## [2.6.0] - 2024-06-30

### Added

* Adding workflow build-packages using a shared workflow.
* Adding symlink `lib/fb_tools/collections.py` => `lib/fb_tools/colcts.py`
  for backword compatibility.

### Changed

* Formatting output list in `lib/fb_tools/xlate.py`.
* Deactivating Github workflow packages.
* Fixing template.spec and .gitlab-ci.yml.
* Renaming `lib/fb_tools/collections.py` => `lib/fb_tools/colcts.py`.

## [2.5.3] - 2024-05-28

### Fixed

* Fixing `lib/fb_tools/handling_obj.py`.

## [2.5.2} - 2024-05-15

### Changed

* Updating .gitlab-ci.yml to the latest version of Digitas packaging tools.

### Fixed

* Fixing and testing property `address_family` and method
  `get_address_famlily_int()` of HandlingObject.

## [2.5.1] - 2024-04-13

### Changed

* Extending pattern for username in mailaddresses.

## [2.5.0] - 2024-03-14

### Added

* Adding methods `line()` and `empty_line()` to HandlingObject.
* Implementing update of all domains in UpdateDdnsApplication.
* Adding and testing function timeinterval2delta() to `fb_toolds.common`
* Implementing reading and writing a status file in UpdateDdnsStatus

### Changed

* Reorganing exception classes, adding ne exception classes
* Refactoring modules `fb_tools.ddns` and `fb_tools.ddns.config` for using
  MultiConfig

### Fixed

* Fixing FbConfigApplication in module `fb_tools.cfg_app` some test
  scripts

### Removed

* Removing method `empty_line()` from BaseDdnsApplication - it's now in
  a parent class.

## [2.4.2] - 2024-02-28

### Changed

* Changing logging behaviour of `get-file-to-remove`.

## [2.4.1] - 2024-02-06

### Fixed

* Fixing tests for class HandlingObject.

## [2.4.0} - 2024-02-06

### Added

* Adding property `address_family` and method `get_address()` to class HandlingObject.

### Changed

* Updating translations.

### Fixed

* Fixing Github workflow.

## [2.3.5] - 2024-02-04

### Fixed

* Fixing Github workflow.

## [2.3.4} - 2024-02-04

### Added

* Adding tests for Python 3.12 to CI tests.
* Adding distros Debian 13 (trixie) and Ubuntu 24.04 (Noble Numbat) to
  Github workflow packages for building OS packages.

### Changed

* Simplyfying init of some classes.
* Using Python 3.12 for CI linter tests.
* Updating external Guthub actions.

### Removed

* Removing deprecated OS versions Ubuntu 18.04 (Bionic Beaver) and
  Enterprise Linux 7 from Github workflow.

## [2.3.3] - 2023-10-09

### Changed

* Simplyfication init of different application classes.
* Applying flake8 rules to differenbt test scripts.

### Fixed

* Fixing `lib/fb_tools/cfg_app.py` for additional config file.

## [2.3.2] - 2023-10-06

### Fixed

* Fixing runtime error in `lib/fb_tools/multi_config/files.py`.

## [2.3.1] - 2023-10-06

### Added

* Adding test script for importing application modules
* Adding class property to BaseApplication whether `init_logging` should
  executed or not.
* Adding possibility to assining testing command line arguments to
  BaseApplication.

### Fixwd

* Fixing internal imports.
* Fixing deprecated imports.

## [2.3.0] - 2023-10-05

### Added

* Adding possibility in module `fb_tools.multi_config` to read all
  config files in a directory named by the config file stem.

### Changed

* Moving all exception classes from module `fb_tools.multi_config` to
  `fb_tools.errors`.
* Splitting module `fb_tools.multi_config` into different mixin modules.
* Expanding tests for class `BaseMultiConfig`.
* Updating translations.

### Fixwd

* Fixing Github workflow for linting.

## [2.2.5] - 2023-07-19

### Added

* Adding Debian 12 (bookworm) for building binary packages on Github.

### Changed

* Better search for localisation files.
* Disable false shellcheck error.

## [2.2.4] - 2023-06-13

### Changed

* Making command line option `--quiet` optional.

## [2.2.3] - 2023-05-31

### Changed

* Applying additional linter tests to Github workflow.
* Fixing countless linter errors.
* Updating copyright year where applicable.

## [2.2.2] - 2023-02-06

### Added

* Adding quiet as an init parameter for application objects.

### Changed

* Do not update all pip modules in `.gitlab-ci.yml`.
* Updating containers in `.github/workflows/packages.yaml`.
* Updating list of shellscripts in `.gitlab-ci.yml`.
* Changing version of used shared pipeline.

### Fixed

* Fixing get-debian-release for shellcheck errors.

## [2.2.1] - 2022-12-30

### Added

* Adding signing of all Debian packages in Githaub workflow

### Changed

* Using shared pipelines in .gitlab-ci.yml
* Updating package dependencies in template.spec and debian/control

## [2.2.0] - 2022-11-22

### Changed

* Renaming locale definitions `de_DE` => and `en_US` => en.
* Changing `LOCALE_DIR` in `lib/fb_tools/xlate.py`.
* Updating setup files.

### Fixed

* Fixing `lib/fb_tools/ddns/__init__.py` for strange encoding.

## [2.1.2] - 2022-11-02

### Fixed

* Fixing and updating setup files.

## [2.1.1] - 2022-11-01

### Changed

* Extending tests in CI jobs by Python 3.11.

### Fixed

* Fixing imports in `lib/fb_tools/cfg_app.py`.

## [2.1.0] - 2022-10-14

### Added

* Adding common commandline options for assumed answers.
* Adding class TimeoutOptionAction to module `fb_tools.argparse_actions`.
* Adding exceptions AbortAppError and TimeoutOnPromptError to module `fb_tools.errors`.
* Adding properties `prompt_timeout` and `init_yes_no_lists` and methods `get_password()`
  and `ask_for_yes_or_no()` to class HandlingObject in module `fb_tools.handling_obj`.
* Adding optional common commandline option for the timeout of console input.

### Changed

* Updating documentation in all Python modules.
* Making visibiliy of some common options optional.

## [2.0.3] - 2022-09-21

### Changed

* Changes on help display of command line options.

## [2.0.2] - 2022-08-30

### Removed

* Removing last dependencies to pyvmomi.

## [2.0.1] - 2022-07-27

### Changed

* Refactoring `.gitlab-ci.yml`.

## [2.0.0] - 2022-07-27

### Changed

* Applying flake8 rules to setup.py.
* Generating man pages of scripts in bin/ in all CI environments.

### Removed

* Removing all VSpere modules and applications in favor of the
  separate Python package `fb_vmware`.



