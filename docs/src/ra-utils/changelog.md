<!--
SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

CHANGELOG
=========

1.9.3 - 2023-02-09
------------------

[#53496] Fix missing args and kwargs in ESR

1.9.2 - 2023-02-09
------------------

[#53496] DIPEX compatible version

1.9.1 - 2023-02-09
------------------

[#53496] downgraded more-itertools

1.9.0 - 2023-02-09
------------------

[#53496] Added wrapper function to ensure single instance

1.8.0 - 2023-02-01
------------------

feat: [#52218] introduce StructuredUrl

1.7.1 - 2022-12-19
------------------

[#53763] Update dependencies

1.7.0 - 2022-12-13
------------------

[#52137] Add sentry_dsn to jobsettings

1.6.0 - 2022-12-12
------------------

[#54135] Configure `structlog` in `JobSettings.start_logging_based_on_settings`

1.5.0 - 2022-12-02
------------------

[#53614] Add `ra_utils.tdqm_wrapper`

1.4.1 - 2022-11-23
------------------

[#53630] Fixes auth settings

1.4.0 - 2022-11-21
------------------

[#53630] Add default settings for auth

1.3.2 - 2022-11-04
------------------

[#xxxxx] downgrade structlog to allow dipex to use this

1.3.1 - 2022-11-04
------------------

[#xxxxx] Fix release to pypi

1.3.0 - 2022-11-04
------------------

[#53219] Add `JobSettings` base class for defining settings of an OS2MO/DIPEX integration.

1.2.1 - 2022-09-16
------------------

[#52316] bumped dependencies

1.2.0 - 2022-07-04
------------------

[#48869] Introduce with_concurrency decorator and gather_with_concurrency function.

1.1.0 - 2022-06-17
------------------

[#xxxxx] Adds sentry_init function to allow easy setup of sentry in python programs

1.0.0 - 2022-03-14
------------------

[#49146] Bump version to 1.0.0

0.6.0 - 2022-03-10
------------------

[#49146] Use default path if settings.json not found via CWD

0.5.0 - 2021-12-08
------------------

[#47505] Implement automatic versioning through autopub

<!-- TODO: FIX CHANGELOG FROM HERE -->

## Version 0.4.0, 2021-08-02

### New features
* [#44153] Added this documentation:
    `NEWS.rst` version file has been crated and back-populated it using the git history.
    A 'pages' deployment step has been added to CI to deploy documentation to Gitlab pages.
    An entire documentation setup using `mkdocs` has been added.
    Several modules have had their documentation expanded upon.

* [#44153] Added `attrdict.attrdict`:
    A constructor function for `AttrDict`'s.

* [#44153] Marked `transpose_dict.transpose_dict` as broken:
    An issue was detected during the developers day, and a PR is in progress.

* [#44153] Added gitlab PR review tables:
    The ones used by OS2mo were added verbatim.

* [#44153] Added `syncable.Syncable`:
    A mixin helper class to support synchronized use of async classes.


## Version 0.3.1, 2021-07-21

### New features
* [#44587] Added `load_settings.load_setting`:
    A function to load a single setting from the json settings file.


## Version 0.3.0, 2021-07-16

### New features
* [#44669] Added `headers.TokenSettings`:
    A `pydantic` settings class for obtaining session headers to access OS2mo, supports both `python3-saml` and `Keycloak`.
    This also added `requests` and `types-requests` as optional dependencies.
    Additionally a poetry command to install dependencies for `headers` was also added, such that its dependencies can now be installed using either `ra_utils[all]` or `ra_utils[headers]`.


## Version 0.2.0, 2021-07-06

### New features
* [#43255] Added `poetry` install targets for `jinja` and `pydantic`:
    Such that they can now be installed using either `ra_utils[all]` or `ra_utils[pydantic]` / `ra_utils[jinja]` respectively.

* [#43255] Added a 100% test coverage requirement to CI:
    This should ensure that all code is tested, additionally a lot of tests were added.
    This also added `coverage` / `pytest-cov` as a development dependencies.

* [#43255] Added new `hypothesis` testing profiles:
    Seperate profiles for CI, deep testing and local development has been made.

* [#43255] Added `attrdict.AttrDict`:
    A class wrapper around `dict` that enables dot.notation access for a dict object.

* [#43255] Added `generate_uuid.generate_uuid` and `generate_uuid.uuid_generator`:
    A group of functions to enable reproducable UUID generation from seeds and values.

* [#43255] Added `semantic_version_type.SemanticVersion` and `semantic_version_type.SemanticVersionModel`:
    A `pydantic` field and a models for validating semantic versions.
    This also added `pydantic` as an optional dependency.

* [#43422] Added `strategies.not_from_regex`:
    A `hypothesis` strategy for generating strings that do not match a given regex.


## Version 0.1.0, 2021-05-28

Initial release.

Setup the entire project, including, but not limited to: linting, testing, CI pipeline with deployment to PyPI.
Most of the features added are simply extracted from DIPEX.

### New features

* [#43255] Added `apply.apply`:
    A function decorator to apply a tuple to function.

* [#43255] Added `async_to_sync.async_to_sync`:
    A function decorator to run an async coroutine to completion.

* [#43255] Added `catchtime.catchtime`:
    A context manager to measure time within the context.

* [#43255] Added `deprecation.deprecated`:
    A function decorator to mark a function as deprecated.

* [#43255] Added `jinja_filter.jinja_filter`, `jinja_filter.create_filter` and `jinja_filter.create_filters`:
    A group of functions to create boolean filters based on `jinja2` templates.
    This also added `jinja2` as an optional dependency.

* [#43255] Added `lazy_dict.LazyEval`, `lazy_dict.LazyEvalDerived`, `lazy_dict.LazyEvalBare` and `lazy_dict.LazyDict`:
    A group of classes and functions to enable lazily evaluated dictionaries.

* [#43255] Added `load_settings.load_settings`:
    A function to load settings from a json file on disk.

* [#43255] Added `multiple_replace.multiple_replace_compile`, `multiple_replace.multiple_replace_run` and `multiple_replace.multiple_replace`:
    A group of functions to do multiple replacements in a single string.

* [#43255] Added `transpose_dict.transpose_dict`:
    A function to transpose a dictionary turing keys into values and vice versa.
