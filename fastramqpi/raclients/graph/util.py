# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import itertools
from typing import Any
from typing import AsyncIterator
from typing import Optional

from gql.client import AsyncClientSession
from graphql import DocumentNode
from graphql import GraphQLError
from graphql import Source
from graphql import SourceLocation
from tenacity import Retrying
from tenacity import stop_after_attempt
from tenacity import wait_random_exponential


def graphql_error_from_dict(d: dict, query: Optional[str] = None) -> GraphQLError:
    """
    Construct GraphQLError from error dict returned from the server.

    Args:
        d: Error dict.
        query: Original request query. Optional, but allows for better error messages.
    """
    error = GraphQLError(
        message=d["message"],
        # nodes=d.get("nodes"),
        source=Source(body=query) if query is not None else None,
        positions=d.get("positions"),
        path=d.get("path"),
        extensions=d.get("extensions"),
    )

    # For some reason, GraphQLError doesn't take locations in the constructor
    if error.locations is None and "locations" in d:
        error.locations = [SourceLocation(**loc) for loc in d["locations"]]

    return error


async def execute_paged(
    gql_session: AsyncClientSession,
    document: DocumentNode,
    variable_values: Optional[dict[str, Any]] = None,
    per_page: int = 100,
    **kwargs: Any,
) -> AsyncIterator[dict[str, Any]]:
    """Execute a paged GraphQL query, yielding objects.

    Args:
        gql_session: The GQL client session to execute the query on.
        document: GQL document. The query must be defined with variables `$limit` and
            `$offset`, and pass them to the operation, which must be aliased to `page`.
        variable_values: Optional variable values to be used in the query.
        per_page: Number of objects to request per page.
        **kwargs: Additional keyword arguments passed to session.execute()

    Example usage::

        async with GraphQLClient(...) as session:
            query = gql(
                '''
                query PagedQuery($limit: int, $offset: int, $from_date: DateTime) {
                  page: employees(limit: $limit, offset: $offset, from_date: $from_date) {
                    uuid
                  }
                }
            '''
            )
            variables = {
                "from_date": "2001-09-11",
            }
            async for obj in execute_paged(session, query, variable_values=variables):
                print(obj)

    Yields: Objects from pages.
    """
    for offset in itertools.count(step=per_page):
        for attempt in Retrying(
            wait=wait_random_exponential(multiplier=2, max=30),
            stop=stop_after_attempt(3),
        ):
            with attempt:
                result = await gql_session.execute(
                    document,
                    variable_values=dict(
                        limit=per_page,
                        offset=offset,
                        **(variable_values or {}),
                    ),
                    # Return `result` instead of `result.data` so we can access extensions
                    get_execution_result=True,
                    **kwargs,
                )
        for obj in result.data["page"]:
            yield obj
        if result.extensions and result.extensions.get("__page_out_of_range"):
            return
