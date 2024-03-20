# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from gql import gql
from graphql import Source
from graphql import SourceLocation
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from respx import MockRouter

from fastramqpi.raclients.graph.client import GraphQLClient
from fastramqpi.raclients.graph.util import execute_paged
from fastramqpi.raclients.graph.util import graphql_error_from_dict

url = parse_obj_as(AnyHttpUrl, "https://os2mo.example.org/gql")


def test_graphql_error_from_dict() -> None:
    query = """
        query Query {
          a {
            b {
              c
            }
          }
        }
    """
    error = {
        "message": "Cannot query field 'a' on type 'Query'.",
        "locations": [{"line": 2, "column": 3}],
        "path": None,
    }
    graphql_error = graphql_error_from_dict(error, query)
    assert graphql_error.message == "Cannot query field 'a' on type 'Query'."
    assert graphql_error.source == Source(body=query)
    assert graphql_error.locations == [SourceLocation(line=2, column=3)]


@pytest.mark.asyncio
async def test_execute_paged(
    client_params: dict, token_mock: str, respx_mock: MockRouter
) -> None:
    def mock(limit: int, offset: int, page: list[int], out_of_range: bool) -> None:
        respx_mock.post(
            url=url,
            json__variables={
                "limit": limit,
                "offset": offset,
                "from_date": "2001-09-11",
            },
        ).respond(
            json={
                "data": {"page": page},
                "extensions": {"__page_out_of_range": out_of_range},
            }
        )

    mock(limit=2, offset=0, page=[1, 2], out_of_range=False)
    mock(limit=2, offset=2, page=[3], out_of_range=False)
    # MO can return empty pages, even though we are not at the end ;)
    mock(limit=2, offset=4, page=[], out_of_range=False)
    mock(limit=2, offset=6, page=[4], out_of_range=False)
    mock(limit=2, offset=8, page=[], out_of_range=True)

    async with GraphQLClient(url=url, **client_params) as session:
        query = gql(
            """
            query PagedQuery($limit: int, $offset: int, $from_date: DateTime) {
              page: employees(limit: $limit, offset: $offset, from_date: $from_date) {
                uuid
              }
            }
        """
        )
        variables = {
            "from_date": "2001-09-11",
        }
        objects = [
            obj
            async for obj in execute_paged(
                session, query, variable_values=variables, per_page=2
            )
        ]

        assert objects == [1, 2, 3, 4]
