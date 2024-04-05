<!--
SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

CHANGELOG
=========

## 9.3.0 (2024-03-20)

### Features

- [#59372] add caching to from_context

> This commit adds caching to the `from_context` dependency injection
> helper, the motivation behind this change is easing testing when using
> Annotated types, depending on `from_context` functions.
> 
> For example, imagine we have a dependency alike this:
> ```python
> GQLClient = Annotated[_GQLClient, Depends(from_context("graphql_client"))]
> ```
> 
> Now imagine that we wish to replace the GraphQL client with an `AsyncMock`
> in our test-suite, to do this we will use `app.dependency_overrides`:
> ```python
>     mock = AsyncMock()
>     def mocker():
>       return mock
>     app.dependency_overrides[from_context("graphql_client")] = mocker
> ```
> However this example depends on multiple calls to `from_context`
> returning the **exact same** inner-function every time, as otherwise the
> dependency override will not hit.
> 
> Caching the `from_context` function ensures that we always get the
> **exact same** inner-function as a result.

  
## 9.2.0 (2024-03-20)

### Features

- [#59497] introduce AcknowledgeMessage exception

> This commit introduces the `AcknowledgeMessage` exception type, which
> when raised ensures that the current AMQP message should be
> acknowledged.
> 
> This functionality is useful to acknowledge a message from deep within
> application code.

  
## 9.1.1 (2024-01-03)

### Bug Fixes

- [#58342] bump fastapi

> https://github.com/tiangolo/fastapi/blob/a4aa79e0b4cacc6b428d415d04d234a
> 8c77af9d5/fastapi/routing.py#L222-L225

  
## 9.1.0 (2023-09-13)

### Features

- [#57272] allow publishing to a specific exchange

> This is particularly useful as it allows publishing to individual
> _queues_ by using the empty exchange ("").

  
## 9.0.2 (2023-07-27)

### Bug Fixes

- [#53863] use jsonable_encoder

> This allows publishing (more) arbitrary objects.

  
## 9.0.1 (2023-07-24)

### Bug Fixes

- [#56918] get_url()
  
## 9.0.0 (2023-06-02)

### Features

- :warning: [#51925] remove sleep_on_error

> BREAKING CHANGE:
> 
> No one used sleep_on_error to sleep on errors. We used it to limit the
> number of errors and stop the integrations from spamming logs.
> RateLimit should be a drop-in replacement for SleepOnError.

- [#51925] rate-limit dependency

> This supersedes the SleepOnError dependency: rate-limiting is always
> what we truly wanted, and SleepOnError is confusing to use - especially
> during development - as all exceptions are delayed by 30 seconds (by
> default).

  
## 8.4.3 (2023-06-02)

### Build improvements

- **deps**: bump prometheus-client from 0.16.0 to 0.17.0

> Bumps [prometheus-client](https://github.com/prometheus/client_python) from 0.16.0 to 0.17.0.
> - [Release notes](https://github.com/prometheus/client_python/releases)
> - [Commits](https://github.com/prometheus/client_python/compare/v0.16.0...v0.17.0)

  
## 8.4.2 (2023-06-02)

### Build improvements

- **deps**: bump pydantic from 1.10.7 to 1.10.8

> Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.7 to 1.10.8.
> - [Release notes](https://github.com/pydantic/pydantic/releases)
> - [Changelog](https://github.com/pydantic/pydantic/blob/v1.10.8/HISTORY.md)
> - [Commits](https://github.com/pydantic/pydantic/compare/v1.10.7...v1.10.8)

  
## 8.4.1 (2023-06-02)

### Build improvements

- **deps**: bump fastapi from 0.95.1 to 0.95.2

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.95.1 to 0.95.2.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.95.1...0.95.2)

  
## 8.4.0 (2023-05-22)

### Features

- [#51925] make queues quorum by default

> The queue type has been changed from 'classic' to 'quorum'[1]. The
> primary motivation is to ensure messages are rejected to the _back_ of
> the queue. This allows us to consume as many messages as possible,
> instead of blocking on the first unprocessable one.
> 
> Even though RabbitMQ queues cannot change their type, but can only be
> set on declaration time, the change is not breaking. This is because
> queues are migrated on a best-effort basis, i.e. if they are empty, and
> thus able to be re-created on startup. Non-empty queues can be deleted
> manually using the following commands:
> ```
> docker exec msg_broker rabbitmqctl list_queues
> docker exec msg_broker rabbitmqctl delete_queue
> ```
> 
> [1] https://www.rabbitmq.com/quorum-queues.html

 
### Chores

- [#53725] remove darglint

> The project has been archived on GitHub.

  
## 8.3.1 (2023-05-17)

### Bug Fixes

- [#55546] fix type for the new amqp system
  
## 8.3.0 (2023-05-11)

### Features

- [#53725] (re)introduce handle_exclusively as function decorator

> Based on the deleted code in 90e63b2e21cd080354093e32c3cd6b07b424a4e9.

  
## 8.2.2 (2023-05-09)

### Bug Fixes

- bump structlog
  
## 8.2.1 (2023-04-18)

### Build improvements

- **deps**: bump ra-utils from 1.13.0 to 1.13.3
  
## 8.2.0 (2023-04-18)

### Features

- [#55697] adjust fastramqpi to the new amqp system
  
## 8.1.2 (2023-04-15)

### Build improvements

- **deps**: bump ra-utils from 1.12.8 to 1.13.0

> Bumps [ra-utils](https://magenta.dk/) from 1.12.8 to 1.13.0.

  
## 8.1.1 (2023-04-15)

### Build improvements

- **deps**: bump fastapi from 0.95.0 to 0.95.1

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.95.0 to 0.95.1.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.95.0...0.95.1)

  
## 8.1.0 (2023-04-11)

### Features

- add SleepOnError as annotated type
  
## 8.0.1 (2023-03-24)

### Build improvements

- **deps**: bump pydantic from 1.10.6 to 1.10.7

> Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.6 to 1.10.7.
> - [Release notes](https://github.com/pydantic/pydantic/releases)
> - [Changelog](https://github.com/pydantic/pydantic/blob/v1.10.7/HISTORY.md)
> - [Commits](https://github.com/pydantic/pydantic/compare/v1.10.6...v1.10.7)

  
## 8.0.0 (2023-03-22)

### Features

- :warning: [#53725] Make `handle_exclusively` dependency injectable

> BREAKING CHANGE:
> 
> Previously, `handle_exclusively` was a function wrapper. Now, it is to
> be used a dependency.
> 
> Previously:
> ```python
> @handle_exclusively(key=lambda x, y: x)
> async def f(x, y):
>     pass
> ```
> 
> Now:
> ```python
> async def handler(
>     _: Annotated[None, Depends(handle_exclusively(get_routing_key))],
>     msg: Annotated[Message, Depends(handle_exclusively(get_message))],
> ):
>     pass
> ```

- :warning: [#53725] Make `sleep_on_error` dependency injectable

> BREAKING CHANGE:
> 
> Previously, `sleep_on_error` was a function decorator. Now, it is to
> be used a dependency.
> 
> Previously:
> ```python
> @sleep_on_error(delay=10)
> async def f():
>     pass
> ```
> 
> Now:
> ```python
> async def f(_: Annotated[None, Depends(sleep_on_error(delay=10))]):
>     pass
> ```

- :warning: [#53725] Remove `message2json`

> BREAKING CHANGE:
> 
> `message2model` has been superseded by `get_payload_as_type`.

- :warning: [#53725] Remove `message2model`

> BREAKING CHANGE:
> 
> `message2model` has been superseded by `get_payload_as_type`.

- :warning: [#53725] Remove `context_extractor`

> BREAKING CHANGE:
> 
> `context_extractor` has been superseded by `from_context`.

- :warning: [#53725] Dependency Injection

> BREAKING CHANGE:
> 
> `MORoutingKey`, and its `ServiceType`, `ObjectType`, and `RequestType`
> have been removed in favour of a simple `MORoutingKey` literal. This is
> done in preparation of the AMQP redesign[1], which will replace the
> routing key with a simple object type. Users should use e.g.
> `@router.register("employee.it.create")` where they previously used
> `@router.register(ServiceType.EMPLOYEE, ObjectType.IT, RequestType.CREATE)`
> or any similar previously-supported variation.
> 
> The AMQP callback handlers now support FastAPI dependency injection[2].
> Previously, handlers were required to be specified with `**kwargs` to
> ensure forwards compatibility, and the design was based around ignoring
> any unused arguments. The new design allows handlers to request exactly
> the data that they need, as seen with FastAPI dependencies or PyTest
> fixtures.
> 
> A callback using the old syntax might have looked like:
> ```python
> async def callback(
>     mo_routing_key: MORoutingKey, payload: PayloadType, **kwargs: Any
> ):
>     ...
> ```
> whereas the new syntax supports the following:
> ```python
> async def callback(mo_routing_key: MORoutingKey, payload: PayloadType):
>     ...
> ```
> 
> Experienced FastAPI developers might wonder how this works without the
> `Depends` function. Indeed, this less verbose pattern was introduced in
> FastAPI v0.95[3], and works by defining the dependency directly on the
> type using the `Annotated` mechanism from PEP593[4]. For example:
> ```python
> MORoutingKey = Annotated[MORoutingKey, Depends(get_routing_key)]
> PayloadType = Annotated[PayloadType, Depends(get_payload_as_type(PayloadType))]
> ```
> whereby making the previous example equivalent to
> ```python
> async def callback(
>     mo_routing_key: MORoutingKey = Depends(get_routing_key),
>     payload: PayloadType = Depends(get_payload_as_type(PayloadType))
> ):
>     ...
> ```
> 
> Wrappers for `MORoutingKey`, `PayloadType` and others have been added to
> the `ramqp.depends` and `ramqp.mo` modules for convenience.
> 
> The `MOAMQPSystem` and associated objects have moved namespace from
> `ramqp.mo.{amqp,models}` to `ramqp.mo`.
> 
> The `MOAMQPSystem` no longer automatically applies `handle_exclusively`
> to callback handlers.
> 
> [1] https://rammearkitektur.docs.magent.dk/decision-logs/2023/amqp-redesign.html
> [2] https://fastapi.tiangolo.com/tutorial/dependencies
> [3] https://fastapi.tiangolo.com/release-notes/#0950
> [4] https://peps.python.org/pep-0593/

 
### Chores

- [#53725] Add routing key to test for coverage
- [#53725] Move `handle_exclusively` to depends.py
- [#53725] Move `sleep_on_error` to depends.py
- **docs**: [#53725] Add a thin Context section to the README
- **docs**: [#53725] Remove 'FastAPI and Additional Context' section

> It's good advice, but ultimately more relevant to FastRAMQPI and already
> outdated in regard to best practices.

  
## 7.0.4 (2023-03-22)

### Build improvements

- **deps**: bump aio-pika from 9.0.4 to 9.0.5
  
## 7.0.3 (2023-03-22)

### Build improvements

- **deps**: bump pydantic from 1.10.5 to 1.10.6
  
## 7.0.2 (2023-03-22)

### Build improvements

- **deps**: bump ra-utils from 1.12.4 to 1.12.6

> Bumps [ra-utils](https://magenta.dk/) from 1.12.4 to 1.12.6.

  
## 7.0.1 (2023-03-20)

### Build improvements

- **deps**: bump fastapi from 0.94.0 to 0.95.0

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.94.0 to 0.95.0.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.94.0...0.95.0)

  
## 7.0.0 (2023-03-20)

### Features

- :warning: [#53725] Don't read environment variables

> BREAKING CHANGE:
> 
> The library will no longer implicitly read settings from the
> environment. Users should explicitly pass settings to the instantiation
> of the library instead.
> 
> Before:
> ```python
> with AMQPSystem() as amqp_system:
>     ...
> ```
> 
> Now:
> ```python
> settings = AMQPConnectionSettings(url=..., queue_prefix="my-program")
> with AMQPSystem(settings=settings) as amqp_system:
>     ...
> ```
> 
> In most cases, `AMQPConnectionSettings` is probably initialised by being
> included in the `BaseSettings` of the application using the library. The
> `url` parameter of the `AMQPConnectionSettings` object can be given as a
> single URL string or as individual structured fields.
> 
> Consider the following:
> ```python
> class Settings(BaseSettings):
>     amqp: AMQPConnectionSettings
> 
>     class Config:
>         env_nested_delimiter = "__"
> 
> settings = Settings()
> ```
> The above would work with either multiple structured environment
> variables
> ```
> AMQP__URL__SCHEME=amqp
> AMQP__URL__USER=guest
> AMQP__URL__PASSWORD=guest
> AMQP__URL__HOST=msg_broker
> AMQP__URL__PORT=5672
> AMQP__URL__VHOST=os2mo
> ```
> or a single URL definition
> ```
> AMQP__URL=amqp://guest:guest@msg_broker:5672/os2mo
> ```

  
## 6.9.5 (2023-03-13)

### Build improvements

- **deps**: bump aio-pika from 9.0.4 to 9.0.5

> Bumps [aio-pika](https://github.com/mosquito/aio-pika) from 9.0.4 to 9.0.5.
> - [Release notes](https://github.com/mosquito/aio-pika/releases)
> - [Changelog](https://github.com/mosquito/aio-pika/blob/master/CHANGELOG.md)
> - [Commits](https://github.com/mosquito/aio-pika/compare/9.0.4...9.0.5)

  
## 6.9.4 (2023-03-13)

### Build improvements

- **deps**: bump ra-utils from 1.12.2 to 1.12.5

> Bumps [ra-utils](https://magenta.dk/) from 1.12.2 to 1.12.5.

  
## 6.9.3 (2023-03-13)

### Build improvements

- **deps**: bump pydantic from 1.10.5 to 1.10.6

> Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.5 to 1.10.6.
> - [Release notes](https://github.com/pydantic/pydantic/releases)
> - [Changelog](https://github.com/pydantic/pydantic/blob/v1.10.6/HISTORY.md)
> - [Commits](https://github.com/pydantic/pydantic/compare/v1.10.5...v1.10.6)

  
## 6.9.2 (2023-03-13)

### Build improvements

- **deps**: bump fastapi from 0.93.0 to 0.94.0

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.93.0 to 0.94.0.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.93.0...0.94.0)

  
## 6.9.1 (2023-03-08)

### Chores

- **deps**: [#53725] Bump dependencies
  
## 6.9.0 (2023-03-07)

### Features

- enable auto-merge on dependabot
  
## 6.8.1 (2023-02-26)

### Build improvements

- **deps**: bump ra-utils from 1.11.13 to 1.11.15

> Bumps [ra-utils](https://magenta.dk/) from 1.11.13 to 1.11.15.

  
## 6.8.0 (2023-02-25)

### Features

- [#52218] added several callback decorator utilities

> The added utilities are:
> 
> * context_extractor:
>   A callback decorator to explode the callback context onto the callback
>   function as kwargs.
> 
> * message2model:
>   A callback decorator to intelligently parse AMQP message bodies as
>   pydantic models. This is achieved using function signature
>   introspection.
> 
> * message2json:
>   A callback decorator to parse AMQP message bodies as json to dicts.
> 
> Additionally examples were added to the RejectMessage and RequeueMessage
> exceptions, and they were also included in the __init__.py file.
> 
> Finally new testing utilities were introduced to facility better testing
> in the future.

  
## 6.7.9 (2023-02-24)

### Code Refactor

- [#52218] manual fulfillment of new pre-commit requirements
 
### Build improvements

- **deps**: bump ra-utils from 1.11.3 to 1.11.13

> Bumps [ra-utils](https://magenta.dk/) from 1.11.3 to 1.11.13.

 
### Style

- [#52218] update and expand pre-commit, style code
  
## 6.7.8 (2023-02-21)

### Build improvements

- **deps**: bump aio-pika from 9.0.2 to 9.0.4

> Bumps [aio-pika](https://github.com/mosquito/aio-pika) from 9.0.2 to 9.0.4.
> - [Release notes](https://github.com/mosquito/aio-pika/releases)
> - [Changelog](https://github.com/mosquito/aio-pika/blob/master/CHANGELOG.md)
> - [Commits](https://github.com/mosquito/aio-pika/compare/9.0.2...9.0.4)

  
## 6.7.7 (2023-02-16)

### Build improvements

- **deps**: bump ra-utils from 1.9.0 to 1.11.3

> Bumps [ra-utils](https://magenta.dk/) from 1.9.0 to 1.11.3.

  
## 6.7.6 (2023-02-16)

### Build improvements

- **deps**: bump aio-pika from 9.0.1 to 9.0.2

> Bumps [aio-pika](https://github.com/mosquito/aio-pika) from 9.0.1 to 9.0.2.
> - [Release notes](https://github.com/mosquito/aio-pika/releases)
> - [Changelog](https://github.com/mosquito/aio-pika/blob/master/CHANGELOG.md)
> - [Commits](https://github.com/mosquito/aio-pika/compare/9.0.1...9.0.2)

  
## 6.7.5 (2023-02-16)

### Build improvements

- **deps**: bump pydantic from 1.10.4 to 1.10.5

> Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.4 to 1.10.5.
> - [Release notes](https://github.com/pydantic/pydantic/releases)
> - [Changelog](https://github.com/pydantic/pydantic/blob/v1.10.5/HISTORY.md)
> - [Commits](https://github.com/pydantic/pydantic/compare/v1.10.4...v1.10.5)

  
## 6.7.4 (2023-02-14)

### Build improvements

- **deps**: bump aio-pika from 8.3.0 to 9.0.1

> Bumps [aio-pika](https://github.com/mosquito/aio-pika) from 8.3.0 to 9.0.1.
> - [Release notes](https://github.com/mosquito/aio-pika/releases)
> - [Changelog](https://github.com/mosquito/aio-pika/blob/master/CHANGELOG.md)
> - [Commits](https://github.com/mosquito/aio-pika/commits)

- **deps**: bump fastapi from 0.91.0 to 0.92.0

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.91.0 to 0.92.0.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.91.0...0.92.0)

- **deps**: bump fastapi from 0.89.1 to 0.91.0

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.89.1 to 0.91.0.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.89.1...0.91.0)

- **deps**: bump ra-utils from 1.8.0 to 1.9.0

> Bumps [ra-utils](https://magenta.dk/) from 1.8.0 to 1.9.0.

 
### CI improvements

- [#52164] Delete .releaserc.yaml
  
## 6.7.3 (2023-02-01)

### Build improvements

- **deps**: bump prometheus-client from 0.15.0 to 0.16.0

> Bumps [prometheus-client](https://github.com/prometheus/client_python) from 0.15.0 to 0.16.0.
> - [Release notes](https://github.com/prometheus/client_python/releases)
> - [Commits](https://github.com/prometheus/client_python/compare/v0.15.0...v0.16.0)

- **deps**: bump aio-pika from 8.2.3 to 8.3.0

> Bumps [aio-pika](https://github.com/mosquito/aio-pika) from 8.2.3 to 8.3.0.
> - [Release notes](https://github.com/mosquito/aio-pika/releases)
> - [Changelog](https://github.com/mosquito/aio-pika/blob/master/CHANGELOG.md)
> - [Commits](https://github.com/mosquito/aio-pika/compare/8.2.3...8.3.0)

- **deps**: bump pydantic from 1.10.2 to 1.10.4

> Bumps [pydantic](https://github.com/pydantic/pydantic) from 1.10.2 to 1.10.4.
> - [Release notes](https://github.com/pydantic/pydantic/releases)
> - [Changelog](https://github.com/pydantic/pydantic/blob/v1.10.4/HISTORY.md)
> - [Commits](https://github.com/pydantic/pydantic/compare/v1.10.2...v1.10.4)

- **deps**: bump fastapi from 0.88.0 to 0.89.1

> Bumps [fastapi](https://github.com/tiangolo/fastapi) from 0.88.0 to 0.89.1.
> - [Release notes](https://github.com/tiangolo/fastapi/releases)
> - [Commits](https://github.com/tiangolo/fastapi/compare/0.88.0...0.89.1)

 
### CI improvements

- [#52218] Add no-interrupt CI template
 
### Chores

- **deps**: [#51128] update dependencies
- [#52218] release dependabot chores
- [#53471] use POETRY 1.3.2
- [#53471] add dependabot
- [#53471] remove duplicate dependency
  
## 6.7.2 (2022-12-20)

### Bug Fixes

- [#53763] Release updated dependencies
 
### Build improvements

- [#53763] Update dependencies
 
### Chores

- [#52916] Fix pyproject
- [#52916] Fix CI
  
## 6.7.1 (2022-10-12)

### Bug Fixes

- [#52084] sleep_on_error: ACTUALLY reraise error after sleeping 🤦

> Who the fuck writes a unittest that doesn't actually test properly..

  
## 6.7.0 (2022-10-04)

### Features

- [#52332] Sleep on errors to avoid race-conditions
  
## 6.6.3 (2022-09-23)

### Bug Fixes

- [#51949] Fix leak of `handle_exclusively` locks
  
## 6.6.2 (2022-09-16)

### Bug Fixes

- [#52316] ignore_processed to support manual (n)ack/reject

> See:
> * https://aio-pika.readthedocs.io/en/latest/apidoc.html#aio_pika.IncomingMessage.process
> * https://github.com/mosquito/aio-pika/issues/189#issuecomment-463782240
> For details.

 
### Chores

- [#52316] bump dependency versions
  
## 6.6.1 (2022-09-10)

### Bug Fixes

- [#52084] Allow using TypedDict as context
  
## 6.6.0 (2022-09-07)

### Features

- [#52332] fix pypi release
  
## 6.5.0 (2022-09-07)

### Bug Fixes

- [#52332] fix conventional commit tag version
  
## v1.0.0 (2022-09-07)

### Features

- [#52332] introduce RejectMessage and RequeueMessage exceptions

> Apply 1 suggestion(s) to 1 file(s)
> 
> Apply 1 suggestion(s) to 1 file(s)

- [#52332] introduce conventional commits
 
### Test improvements

- [#52332] modify (mo)amqp_test to support multiple messages
 
### Chores

- [#52332] upgrade dependencies
- [#xxxxx] update pip version
- [#xxxxx] update reuse version

## 6.4.1 (2022-08-17)

- [#51802] Pass `*args` to handle_exclusively key function

## 6.4.0 (2022-08-17)

- [#51802] Add handle_exclusively utility function to avoid race conditions

## 6.3.0 (2022-08-16)

- [#48869] Made prefetch_count configurable

## 6.2.0 (2022-08-16)

- [#46148] Introduce more connection event metrics

## 6.1.0 (2022-07-05)

- [#49162] Support Any object as routing key

## 6.0.0 (2022-06-28)

- [#50111] Remove 'AMQP_' prefix from connection settings

## 5.0.0 (2022-06-28)

- [#50111] Allow overriding context
- [#50111] Implement Router
- [#50111] Take settings, router, and context explicitly
- [#50111] PublishMixin

## 4.0.0 (2022-06-24)

- [#50111] Take settings arguments on init instead of start
- [#50111] Add context

## 3.1.1 (2022-06-22)

- [#49604] Bump versions

## 3.1.0 (2022-06-22)

- [#49604] Context Manager

## 3.0.0 (2022-06-01)

- [#49706] Add individual amqp_scheme, amqp_host, amqp_user, amqp_password, amqp_port, amqp_vhost fields.

> Before, the AMQP server could only be configured using the `amqp_url` setting.
> Now, AMQP connection settings can alternatively be set individually using
> `amqp_x` variables. Additionally, `queue_prefix` was renamed to
> `amqp_queue_prefix` for consistency.

## 2.0.1 (2022-06-01)

- [#50496] Fix typing

## 2.0.0 (2022-05-18)

- [#49896] Modified the MO callback function parameters and loosed the MOAMQP interface a bit.

> Before the MO Callback function had this signature:
> ```
> Callable[[ServiceType, ObjectType, RequestType, PayloadType], Awaitable]
> ```
> While now it has this signature:
> ```
> Callback[[MORoutingKey, PayloadType], Awaitable]
> ```
>
> Before MOAMQP's `register` and `publish_message` had very a strict interface,
> while now the interface is looser using overloaded methods.

## 1.3.1 (2022-05-05)

- [#49896] Hotfix bug introduced by restructure metrics and add publish metrics

## 1.3.0 (2022-05-04)

- [#49896] Restructure metrics and add publish metrics

## 1.2.0 (2022-05-04)

- [#49896] Added healthcheck endpoint

## 1.1.1 (2022-04-25)

- [#49706] Fix MO AMQP routing key to correspond with MOs

## 1.1.0 (2022-04-20)

- [#49610] MOAMQPSystem register non-unique wrappers

## 1.0.0 (2022-04-12)

- [#49610] Initial release

## 0.1.2 (2022-04-04)

- [#49610] Testing autopub

## 0.1.1 (2022-04-03)

- Manual release

## 0.1.0 (2022-04-03)

- Manual release
