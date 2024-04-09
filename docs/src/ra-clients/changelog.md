<!--
SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

CHANGELOG
=========

## 3.3.5 (2024-03-19)

### Bug Fixes

- [#60205] update httpx and respx

## 3.3.4 (2024-03-19)

### Bug Fixes

- [#60205] don't use httpx with httpcore with random feature branch

## 3.3.3 (2024-02-29)

### Bug Fixes

- [#59890] retry execute_paged

## 3.3.2 (2023-11-22)

### Bug Fixes

- [#57426] timeout issues

> We're experiencing timeout errors in various integrations, but it does
> not look like we ever send the request to OS2mo/Keycloak/etc. This MR
> bumps httpx to a patched version which in turn depends on patched
> version of httpcore which includes
> https://github.com/encode/httpcore/pull/802, which I suspect is our
> issue.
>
> Another related issue has also been fixed
> (https://github.com/encode/httpcore/pull/641), and is already included
> in httpcore 0.18.0.


## 3.3.1 (2023-10-06)

### Bug Fixes

- [#56520] keep file extensions

## 3.3.0 (2023-10-06)

### Features

- [#56520] force file upload

> This will overwrite a file if it already exists. This is fine, as *all*
> integrations that use the query dir overwrites the file.


## 3.2.1 (2023-10-06)

### Bug Fixes

- [#56520] imports

## 3.2.0 (2023-10-05)

### Features

- [#56520] module to help dipex upload files

### Chores

- [#xxxxx] satisfy mypy

## 3.1.12 (2023-07-06)

### Build improvements

- **deps**: [security] bump pymdown-extensions from 9.10 to 10.0

## 3.1.11 (2023-07-06)

### Build improvements

- **deps**: bump gql from 3.4.0 to 3.4.1

> Bumps [gql](https://github.com/graphql-python/gql) from 3.4.0 to 3.4.1.
> - [Release notes](https://github.com/graphql-python/gql/releases)
> - [Commits](https://github.com/graphql-python/gql/compare/v3.4.0...v3.4.1)


## 3.1.10 (2023-07-06)

### Build improvements

- **deps**: bump httpx from 0.24.0 to 0.24.1

> Bumps [httpx](https://github.com/encode/httpx) from 0.24.0 to 0.24.1.
> - [Release notes](https://github.com/encode/httpx/releases)
> - [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
> - [Commits](https://github.com/encode/httpx/compare/0.24.0...0.24.1)


## 3.1.9 (2023-07-06)

### Build improvements

- **deps**: [security] bump cryptography from 39.0.2 to 41.0.0

> Bumps [cryptography](https://github.com/pyca/cryptography) from 39.0.2 to 41.0.0. **This update includes a security fix.**
> - [Release notes](https://github.com/pyca/cryptography/releases)
> - [Changelog](https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst)
> - [Commits](https://github.com/pyca/cryptography/compare/39.0.2...41.0.0)


## 3.1.8 (2023-07-06)

### Build improvements

- **deps**: bump authlib from 1.2.0 to 1.2.1

> Bumps [authlib](https://github.com/lepture/authlib) from 1.2.0 to 1.2.1.
> - [Release notes](https://github.com/lepture/authlib/releases)
> - [Changelog](https://github.com/lepture/authlib/blob/master/docs/changelog.rst)
> - [Commits](https://github.com/lepture/authlib/compare/v1.2.0...v1.2.1)


## 3.1.7 (2023-07-06)

### Build improvements

- **deps**: bump fastapi from 0.95.1 to 0.99.1

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.95.1 to 0.99.1.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.95.1...0.99.1)


## 3.1.6 (2023-07-06)

### Build improvements

- **deps**: bump ramodels from 19.0.0 to 22.7.2

> Bumps [ramodels](https://magenta.dk/) from 19.0.0 to 22.7.2.


## 3.1.5 (2023-07-06)

### Build improvements

- **deps**: bump pydantic from 1.10.5 to 1.10.11

> Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.5 to 1.10.11.
> - [Release notes](https://github.com/pydantic/pydantic/releases)
> - [Changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
> - [Commits](https://github.com/pydantic/pydantic/compare/v1.10.5...v1.10.11)


## 3.1.4 (2023-04-19)

### Build improvements

- **deps**: bump ramodels from 18.5.2 to 19.0.0

> Bumps [ramodels](https://magenta.dk/) from 18.5.2 to 19.0.0.


### Chores

- [#53506] enable automerge

## 3.1.3 (2023-04-15)

### Build improvements

- **deps**: bump structlog from 22.3.0 to 23.1.0

> Bumps [structlog](https://github.com/hynek/structlog) from 22.3.0 to 23.1.0.
> - [Release notes](https://github.com/hynek/structlog/releases)
> - [Changelog](https://github.com/hynek/structlog/blob/main/CHANGELOG.md)
> - [Commits](https://github.com/hynek/structlog/compare/22.3.0...23.1.0)


## 3.1.2 (2023-04-15)

### Build improvements

- **deps**: bump httpx from 0.23.3 to 0.24.0

> Bumps [httpx](https://github.com/encode/httpx) from 0.23.3 to 0.24.0.
> - [Release notes](https://github.com/encode/httpx/releases)
> - [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
> - [Commits](https://github.com/encode/httpx/compare/0.23.3...0.24.0)


## 3.1.1 (2023-04-15)

### Build improvements

- **deps**: bump fastapi from 0.92.0 to 0.95.1

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.92.0 to 0.95.1.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.92.0...0.95.1)


## 3.1.0 (2023-03-31)

### Features

- [#53354] Implement `execute_paged`

## 3.0.5 (2023-03-07)

### Bug Fixes

- [#53725] Test conventional commit release

### CI improvements

- [#53725] Replace Autopub with Conventional commits

## 3.0.4 (2023-03-07)

### Build improvements

- **deps**: bump ramodels from 15.5.0 to 15.13.0

> Bumps [ramodels](https://magenta.dk/) from 15.5.0 to 15.13.0.

- **deps**: bump fastapi from 0.88.0 to 0.89.1

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.88.0 to 0.89.1.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.88.0...0.89.1)

- **deps**: bump pydantic from 1.10.2 to 1.10.4

> Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.2 to 1.10.4.
> - [Release notes](https://github.com/pydantic/pydantic/releases)
> - [Changelog](https://github.com/pydantic/pydantic/blob/v1.10.4/HISTORY.md)
> - [Commits](https://github.com/pydantic/pydantic/compare/v1.10.2...v1.10.4)

- **deps**: bump httpx from 0.23.1 to 0.23.3

> Bumps [httpx](https://github.com/encode/httpx) from 0.23.1 to 0.23.3.
> - [Release notes](https://github.com/encode/httpx/releases)
> - [Changelog](https://github.com/encode/httpx/blob/master/CHANGELOG.md)
> - [Commits](https://github.com/encode/httpx/compare/0.23.1...0.23.3)


### CI improvements

- [#53725] Replace Autopub with Conventional commits

### Chores

- [#53725] Update dependencies

## 3.0.3 (2022-12-21)

### Bug Fixes

- [#53756] Update dependencies

> Use `^` to allow more flexibility in `ramodels` version.

## 3.0.2 (2022-12-19)

### Bug Fixes

- [#53756] Update dependencies
- [#53756] Update dependencies

## 3.0.1 (2022-12-14)

### Bug Fixes

- [#53756] Add py.typed marker

## 3.0.0 (2022-12-14)

### Features

- :warning: [#53756] Add support for arbitrary token endpoint

> BREAKING CHANGE:
>
> This replaces the `auth_server` and `auth_realm` arguments to the
> authenticated clients with a single `token_endpoint`. Users can maintain
> support for Keycloak by utilising the new `keycloak_token_endpoint`
> function:
> ```
> AuthenticatedAsyncHTTPXClient(
>     client_id="AzureDiamond",
>     client_secret="hunter2",
>     token_endpoint=keycloak_token_endpoint(
>         auth_server=parse_obj_as(AnyHttpUrl, "https://keycloak.example.org/auth"),
>         auth_realm="mordor",
>     ),
> )
> ```
>
> The interface for GraphQLClient and MO ModelClient has been maintained.

## 2.0.2 (2022-11-04)

- [#53470] Bumped dependencies and python to 3.10

## 2.0.1 (2022-11-04)

- [#xxxxx] Update dependencies

## 2.0.0 (2022-10-06)

- [#51982] Remove temporary backwards-compatibility fix for breaking change introduced in minor v1.3.0

## 1.3.4 (2022-10-06)

- [#51982] Add temporary backwards-compatibility fix for breaking change introduced in minor v1.3.0

## 1.3.3 (2022-09-17)

- [#52316] bump dependencies

## 1.3.2 (2022-09-16)

- [#52316] bumped dependencies

## 1.3.1 (2022-09-10)

- [#52084] Bump dependencies

## 1.3.0 (2022-09-09)

- [#51982] Disable authentication for LoRa ModelClient

## 1.2.6 (2022-07-19)

- [#51177] Bump dependencies

## 1.2.5 (2022-06-21)

- [#49604] Bump dependencies

## 1.2.4 (2022-03-28)

- [#49349] Bump dependencies

## 1.2.3 (2022-03-28)

- [#49349] Bump dependencies

## 1.2.2 (2022-03-28)

- [#49349] Bump dependencies

## 1.2.1 (2022-02-10)

- [#48565] Fix KLEWrite -> KLE

## 1.2.0 (2022-02-10)

- [#48565] Add support for KLEWrite in MOModelClient

## 1.1.0 (2022-01-31)

- [#47680] Implement edits for MO ModelClient

## 1.0.0 (2022-01-25)

- [#48131] Refactor ModelClients
- [#47680] Reintroduce ModelClient retrying
- [#47680] Reduce default ModelClient chunk size from 100 to 10

## 0.12.0 (2022-01-21)

- [#47680] Add support for Association, Leave, Role in ModelClient

## 0.11.4 (2022-01-18)

- [#47972] Update dependencies

## 0.11.3 (2022-01-12)

- [#47699] Update ramodels

## 0.11.2 (2022-01-06)

- [#45480] Update ramodels

## 0.11.1 (2022-01-04)

- [#47100] Update ramodels dependency.

## 0.11.0 (2021-12-08)

- [#47506] Implement automatic versioning through autopub

## 0.10.1 (2021-11-23)

## 0.10.0 (2021-11-19)

## 0.9.0 (2021-11-18)

## 0.8.2 (2021-11-12)

## 0.8.1 (2021-11-10)

## 0.8.0 (2021-11-04)

## 0.7.3 (2021-11-03)

## 0.7.2 (2021-11-03)

## 0.4.5 (2021-10-18)

## 0.4.4 (2021-09-22)

## 0.4.3 (2021-09-09)

## 0.4.2 (2021-09-09)

## 0.4.1 (2021-07-16)

## 0.4.0 (2021-07-16)

## 0.3.4 (2021-07-01)

## 0.3.3 (2021-07-01)

## 0.3.2 (2021-07-01)

## 0.3.1 (2021-06-25)

## 0.3.0 (2021-06-24)

## 0.2.0 (2021-06-24)

## 0.1.8 (2021-06-15)
