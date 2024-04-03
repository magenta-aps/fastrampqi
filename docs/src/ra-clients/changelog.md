<!--
SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

CHANGELOG
=========

3.0.3 - 2022-12-21
------------------

[#53756] Update dependencies

3.0.2 - 2022-12-19
------------------

[#53756] Update dependencies

3.0.1 - 2022-12-14
------------------

fix: [#53756] Add py.typed marker

3.0.0 - 2022-12-14
------------------

feat!: [#53756] Add support for arbitrary token endpoint

BREAKING CHANGE:

This replaces the `auth_server` and `auth_realm` arguments to the authenticated
clients with a single `token_endpoint`. Users can maintain support for Keycloak
by utilising the new `keycloak_token_endpoint` function:
```
AuthenticatedAsyncHTTPXClient(
    client_id="AzureDiamond",
    client_secret="hunter2",
    token_endpoint=keycloak_token_endpoint(
        auth_server=parse_obj_as(AnyHttpUrl, "https://keycloak.example.org/auth"),
        auth_realm="mordor",
    ),
)
```

2.0.2 - 2022-11-04
------------------

[#53470] Bumped dependencies and python to 3.10

2.0.1 - 2022-11-04
------------------

[#xxxxx] Update dependencies

2.0.0 - 2022-10-06
------------------

[#51982] Remove temporary backwards-compatibility fix for breaking change introduced in minor v1.3.0

1.3.4 - 2022-10-06
------------------

[#51982] Add temporary backwards-compatibility fix for breaking change introduced in minor v1.3.0

1.3.3 - 2022-09-17
------------------

[#52316] bump dependencies

1.3.2 - 2022-09-16
------------------

[#52316] bumped dependencies

1.3.1 - 2022-09-10
------------------

[#52084] Bump dependencies

1.3.0 - 2022-09-09
------------------

[#51982] Disable authentication for LoRa ModelClient

1.2.6 - 2022-07-19
------------------

[#51177] Bump dependencies

1.2.5 - 2022-06-21
------------------

[#49604] Bump dependencies

1.2.4 - 2022-03-28
------------------

[#49349] Bump dependencies

1.2.3 - 2022-03-28
------------------

[#49349] Bump dependencies

1.2.2 - 2022-03-28
------------------

[#49349] Bump dependencies

1.2.1 - 2022-02-10
------------------

[#48565] Fix KLEWrite -> KLE

1.2.0 - 2022-02-10
------------------

[#48565] Add support for KLEWrite in MOModelClient

1.1.0 - 2022-01-31
------------------

[#47680] Implement edits for MO ModelClient

1.0.0 - 2022-01-25
------------------

[#48131] Refactor ModelClients
[#47680] Reintroduce ModelClient retrying
[#47680] Reduce default ModelClient chunk size from 100 to 10

0.12.0 - 2022-01-21
-------------------

[#47680] Add support for Association, Leave, Role in ModelClient

0.11.4 - 2022-01-18
-------------------

[#47972] Update dependencies

0.11.3 - 2022-01-12
-------------------

[#47699] Update ramodels

0.11.2 - 2022-01-06
-------------------

[#45480] Update ramodels

0.11.1 - 2022-01-04
-------------------

[#47100] Update ramodels dependency.

0.11.0 - 2021-12-08
-------------------

[#47506] Implement automatic versioning through autopub

