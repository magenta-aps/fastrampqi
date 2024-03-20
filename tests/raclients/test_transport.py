# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any
from typing import Union

import httpx
import pytest
from gql import gql
from gql.transport.exceptions import TransportAlreadyConnected
from gql.transport.exceptions import TransportClosed
from gql.transport.exceptions import TransportProtocolError
from gql.transport.exceptions import TransportServerError
from graphql import DocumentNode
from graphql import ExecutionResult
from graphql import GraphQLError
from graphql import Source
from graphql import SourceLocation
from respx import MockRouter

from raclients.graph.transport import AsyncHTTPXTransport
from raclients.graph.transport import BaseHTTPXTransport
from raclients.graph.transport import HTTPXTransport

url = "https://example.org/gql"


@pytest.fixture
def base_transport() -> BaseHTTPXTransport:
    return BaseHTTPXTransport(
        url=url,
        client_cls=httpx.Client,
    )


@pytest.fixture
def document() -> Union[DocumentNode, Any]:  # mypy thinks gql() returns Any
    return gql(
        """
        query MOQuery {
            users {
                id
            }
        }
        """
    )


@pytest.fixture
def transport() -> HTTPXTransport:
    return HTTPXTransport(url=url)


@pytest.fixture
def async_transport() -> AsyncHTTPXTransport:
    return AsyncHTTPXTransport(url=url)


def test_base_transport_init(base_transport: BaseHTTPXTransport):
    assert base_transport.url == url
    assert base_transport.client_cls == httpx.Client
    assert base_transport.client_args is None
    assert base_transport.client is None


def test_transport_init(transport: HTTPXTransport):
    assert transport.url == url
    assert transport.client_cls == httpx.Client
    assert transport.client_args is None
    assert transport.client is None


def test_async_transport_init(async_transport: AsyncHTTPXTransport):
    assert async_transport.url == url
    assert async_transport.client_cls == httpx.AsyncClient
    assert async_transport.client_args is None
    assert async_transport.client is None


def test_base_transport_connect():
    base_transport = BaseHTTPXTransport(
        url=url,
        client_cls=httpx.Client,
        client_args=dict(
            timeout=42,
        ),
    )
    base_transport._connect()
    assert isinstance(base_transport.client, httpx.Client)
    assert base_transport.session == base_transport.client
    assert base_transport.client.timeout == httpx.Timeout(timeout=42)


def test_transport_connect_close(transport: HTTPXTransport):
    transport.connect()
    assert isinstance(transport.client, httpx.Client)
    transport.close()
    assert transport.client is None


@pytest.mark.asyncio
async def test_async_transport_connect_close(async_transport: AsyncHTTPXTransport):
    await async_transport.connect()
    assert isinstance(async_transport.client, httpx.AsyncClient)
    await async_transport.close()
    assert async_transport.client is None


def test_base_transport_multiple_connect_fails(base_transport: BaseHTTPXTransport):
    base_transport._connect()
    with pytest.raises(TransportAlreadyConnected):
        base_transport._connect()


def test_construct_payload(document: DocumentNode):
    actual = BaseHTTPXTransport._construct_payload(
        document=document,
    )
    expected = {"query": "query MOQuery {\n  users {\n    id\n  }\n}"}
    assert actual == expected


def test_construct_payload_variable_values(document: DocumentNode):
    actual = BaseHTTPXTransport._construct_payload(
        document=document,
        variable_values=dict(
            a=1,
            b="x",
        ),
    )
    expected = {
        "query": "query MOQuery {\n  users {\n    id\n  }\n}",
        "variables": {
            "a": 1,
            "b": "x",
        },
    }
    assert actual == expected


def test_construct_payload_operation_name(document: DocumentNode):
    actual = BaseHTTPXTransport._construct_payload(
        document=document,
        operation_name="please, thank you",
    )
    expected = {
        "query": "query MOQuery {\n  users {\n    id\n  }\n}",
        "operationName": "please, thank you",
    }
    assert actual == expected


def test_decode_response(base_transport: BaseHTTPXTransport):
    response = httpx.Response(
        200,
        json={
            "data": {"a": 1},
        },
    )
    actual = base_transport._decode_response(response)
    expected = ExecutionResult(
        data={"a": 1},
        errors=None,
        extensions=None,
    )
    assert actual == expected


def test_decode_error_response(base_transport: BaseHTTPXTransport):
    response = httpx.Response(
        200,
        json={
            "errors": [{"message": "you"}, {"message": "fail"}],
            "data": None,
            "extensions": None,
        },
    )
    actual = base_transport._decode_response(response)
    expected = ExecutionResult(
        data=None,
        errors=[GraphQLError("you"), GraphQLError("fail")],
        extensions=None,
    )
    assert actual == expected


def test_decode_400(base_transport: BaseHTTPXTransport):
    response = httpx.Response(400, request=httpx.Request("GET", url))
    with pytest.raises(TransportServerError, match="Client error '400 Bad Request"):
        base_transport._decode_response(response)


def test_decode_non_json(base_transport: BaseHTTPXTransport):
    response = httpx.Response(
        200,
        text="wait a minute, this isn't json",
        request=httpx.Request("GET", url),
    )
    with pytest.raises(TransportProtocolError, match="Not a JSON answer"):
        base_transport._decode_response(response)


def test_decode_no_data(base_transport: BaseHTTPXTransport):
    response = httpx.Response(
        200,
        json={
            "wrong": True,
        },
        request=httpx.Request("GET", url),
    )
    with pytest.raises(
        TransportProtocolError, match="No 'data' or 'errors' keys in answer"
    ):
        base_transport._decode_response(response)


def test_transport_execute_fails_disconnected(
    transport: HTTPXTransport, document: DocumentNode
):
    with pytest.raises(TransportClosed):
        transport.execute(document)


@pytest.mark.asyncio
async def test_async_transport_execute_fails_disconnected(
    async_transport: AsyncHTTPXTransport, document: DocumentNode
):
    with pytest.raises(TransportClosed):
        await async_transport.execute(document)


def test_integration_transport_execute(
    transport: HTTPXTransport, document: DocumentNode, respx_mock: MockRouter
):
    respx_mock.post(
        url=url,
        json={"query": "query MOQuery {\n  users {\n    id\n  }\n}"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"a": 1},
            },
        )
    )

    transport.connect()
    actual = transport.execute(document)
    transport.close()
    expected = ExecutionResult(
        data={"a": 1},
        errors=None,
        extensions=None,
    )
    assert actual == expected


@pytest.mark.asyncio
async def test_integration_async_transport_execute(
    async_transport: AsyncHTTPXTransport, document: DocumentNode, respx_mock: MockRouter
):
    respx_mock.post(
        url=url,
        json={"query": "query MOQuery {\n  users {\n    id\n  }\n}"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {"a": 1},
            },
        )
    )

    await async_transport.connect()
    actual = await async_transport.execute(document)
    await async_transport.close()
    expected = ExecutionResult(
        data={"a": 1},
        errors=None,
        extensions=None,
    )
    assert actual == expected


def test_integration_transport_execute_error(
    transport: HTTPXTransport, document: DocumentNode, respx_mock: MockRouter
):
    respx_mock.post(
        url=url,
        json={"query": "query MOQuery {\n  users {\n    id\n  }\n}"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "errors": [
                    {
                        "message": "Cannot query field 'a' on type 'Query'.",
                        "locations": [{"line": 2, "column": 3}],
                        "path": None,
                    }
                ],
            },
        )
    )
    transport.connect()
    result = transport.execute(document)
    transport.close()

    assert result.data is None
    assert isinstance(result.errors, list)
    assert len(result.errors) == 1

    error = result.errors[0]
    assert error.message == "Cannot query field 'a' on type 'Query'."
    assert error.source == Source(body="query MOQuery {\n  users {\n    id\n  }\n}")
    assert error.locations == [SourceLocation(line=2, column=3)]
