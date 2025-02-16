# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import ast
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from textwrap import dedent
from zoneinfo import ZoneInfo

import graphql as gql
import pytest
from more_itertools import one

from fastramqpi.ariadne import parse_graphql_datetime
from fastramqpi.ariadne import UnsetInputTypesPlugin


def test_parse_graphql_datetime_datetime() -> None:
    """Test that a datetime's timezone is unmodified."""
    cairo = ZoneInfo("Africa/Cairo")
    dt = datetime(2010, 10, 31, 0, 0, 0, tzinfo=cairo)
    assert parse_graphql_datetime(dt).tzinfo == cairo


def test_parse_graphql_datetime_only_copenhagen_offset() -> None:
    """Test that the function only casts Copenhagen UTC offsets to Copenhagen."""
    assert parse_graphql_datetime("2010-10-31T00:00:00+10:00").tzinfo == timezone(
        timedelta(hours=10)
    )


def test_parse_graphql_datetime_str() -> None:
    """Test that the function correctly outputs Europe/Copenhagen timezones."""
    timestamp = "2010-10-31T00:00:00+02:00"
    utc_offset = datetime.fromisoformat(timestamp)
    copenhagen = parse_graphql_datetime(timestamp)
    assert copenhagen.tzinfo == ZoneInfo("Europe/Copenhagen")
    assert copenhagen.isoformat() == utc_offset.isoformat()

    one_day = timedelta(days=1)
    assert (copenhagen + one_day).isoformat() == "2010-11-01T00:00:00+01:00"
    assert (utc_offset + one_day).isoformat() == "2010-11-01T00:00:00+02:00"


@pytest.fixture
def inputs_module() -> ast.Module:
    # Minimal example AST as generated before the plugin runs
    return ast.parse(
        dedent(
            """
        from typing import Optional
        from uuid import UUID

        from .base_model import BaseModel

        class EmployeeFilter(BaseModel):
            # ...
            uuids: list[UUID] | None = None

        class ManagerFilter(BaseModel):
            # ...
            employee: Optional["EmployeeFilter"]

        class RAValidityInput(BaseModel):
            # ...
            from_: datetime | None = Field(alias="from")
            to: datetime

        class AddressCreateInput(BaseModel):
            # ...
            validity: "Optional[RAValidityInput]"
        """
        )
    )


@pytest.fixture
def graphql_schema() -> gql.GraphQLSchema:
    graphql_ast = gql.parse(
        dedent(
            """
        scalar UUID
        scalar DateTime

        input EmployeeFilter {
          "..."
          uuids: [UUID!] = null
        }

        input ManagerFilter {
          "..."
          employee: EmployeeFilter
        }

        input RAValidityInput {
          "..."
          from: DateTime
          to: DateTime!
        }

        input AddressCreateInput {
          "..."
          validity: RAValidityInput
        }
    """
        )
    )
    schema = gql.build_ast_schema(graphql_ast)
    return schema


def test_plugin_add_import(inputs_module: ast.Module) -> None:
    """Test that our plugin adds imports as expected."""
    plugin = UnsetInputTypesPlugin(gql.GraphQLSchema(), {})

    updated = plugin.generate_inputs_module(inputs_module)
    # Find all `from x import y` statements in the generated module
    imports = [
        statement for statement in updated.body if isinstance(statement, ast.ImportFrom)
    ]
    # Deconstruct `from x import y,z` into `[(x, y), (x,z)]`
    import_names = [
        (import_.module, alias.name) for import_ in imports for alias in import_.names
    ]
    assert import_names == [
        ("base_model", "UnsetType"),
        ("base_model", "UNSET"),
        ("typing", "Optional"),
        ("uuid", "UUID"),
        ("base_model", "BaseModel"),
    ]


def test_plugin_field_transformation_uuid_unaffected(
    inputs_module: ast.Module,
    graphql_schema: gql.GraphQLSchema,
) -> None:
    """Test that our plugin keeps default fields unaffected."""
    plugin = UnsetInputTypesPlugin(graphql_schema, {})

    # Extract the AST node for the EmployeeFilter
    employee_filter_ast = inputs_module.body[3]
    assert isinstance(employee_filter_ast, ast.ClassDef)
    assert employee_filter_ast.name == "EmployeeFilter"
    # Extract the AST node for the uuids assignment
    uuids_assignment = one(employee_filter_ast.body)
    assert isinstance(uuids_assignment, ast.AnnAssign)
    assert isinstance(uuids_assignment.target, ast.Name)
    assert uuids_assignment.target.id == "uuids"
    assert isinstance(uuids_assignment.value, ast.Constant)
    assert uuids_assignment.value.value is None

    # Extract the GraphQL node for the Employee Filter
    employee_filter_gql = graphql_schema.type_map["EmployeeFilter"]
    assert isinstance(employee_filter_gql, gql.GraphQLInputObjectType)
    # Extract the AST node for the uuids assignment
    uuids_input_gql = employee_filter_gql.fields["uuids"]
    assert isinstance(uuids_input_gql, gql.GraphQLInputField)

    # Run the plugin, and check the output is unaffected
    updated = plugin.generate_input_field(
        field_implementation=uuids_assignment,
        input_field=uuids_input_gql,
        field_name="uuids",
    )
    assert updated == uuids_assignment


def test_plugin_field_transformation_alias_unaffected(
    inputs_module: ast.Module,
    graphql_schema: gql.GraphQLSchema,
) -> None:
    """Test that our plugin keeps default fields unaffected."""
    plugin = UnsetInputTypesPlugin(graphql_schema, {})

    # Extract the AST node for the ManagerTerminateInput
    ra_validity_input_ast = inputs_module.body[5]
    assert isinstance(ra_validity_input_ast, ast.ClassDef)
    assert ra_validity_input_ast.name == "RAValidityInput"
    # Extract the AST node for the from assignment
    from_assignment, to_assignment = ra_validity_input_ast.body
    assert isinstance(from_assignment, ast.AnnAssign)
    assert isinstance(from_assignment.target, ast.Name)
    assert from_assignment.target.id == "from_"
    # Check value
    assert isinstance(from_assignment.value, ast.Call)
    assert isinstance(from_assignment.value.func, ast.Name)
    assert from_assignment.value.func.id == "Field"
    # alias keyword
    alias = one(from_assignment.value.keywords)
    assert isinstance(alias, ast.keyword)
    assert alias.arg == "alias"
    assert isinstance(alias.value, ast.Constant)
    assert alias.value.value == "from"

    # Extract the GraphQL node for the Employee Filter
    ra_validity_input_gql = graphql_schema.type_map["RAValidityInput"]
    assert isinstance(ra_validity_input_gql, gql.GraphQLInputObjectType)
    # Extract the AST node for the uuids assignment
    from_input_gql = ra_validity_input_gql.fields["from"]
    assert isinstance(from_input_gql, gql.GraphQLInputField)

    # Run the plugin, and check the output is unaffected
    updated = plugin.generate_input_field(
        field_implementation=from_assignment,
        input_field=from_input_gql,
        field_name="from",
    )
    assert updated == from_assignment


def test_plugin_field_transformation_unrelated_unaffected(
    inputs_module: ast.Module,
    graphql_schema: gql.GraphQLSchema,
) -> None:
    """Test that our plugin keeps unrealted fields unaffected."""
    plugin = UnsetInputTypesPlugin(graphql_schema, {})

    # Extract the AST node for the ManagerTerminateInput
    ra_validity_input_ast = inputs_module.body[5]
    assert isinstance(ra_validity_input_ast, ast.ClassDef)
    assert ra_validity_input_ast.name == "RAValidityInput"
    # Extract the AST node for the from assignment
    from_assignment, to_assignment = ra_validity_input_ast.body
    assert isinstance(to_assignment, ast.AnnAssign)
    assert isinstance(to_assignment.target, ast.Name)
    assert to_assignment.target.id == "to"
    # Check value
    assert to_assignment.value is None

    # Extract the GraphQL node for the Employee Filter
    ra_validity_input_gql = graphql_schema.type_map["RAValidityInput"]
    assert isinstance(ra_validity_input_gql, gql.GraphQLInputObjectType)
    # Extract the AST node for the uuids assignment
    to_input_gql = ra_validity_input_gql.fields["to"]
    assert isinstance(to_input_gql, gql.GraphQLInputField)

    # Run the plugin, and check the output is unaffected
    updated = plugin.generate_input_field(
        field_implementation=to_assignment,
        input_field=to_input_gql,
        field_name="to",
    )
    assert updated == to_assignment


def test_plugin_field_transformation_employee_transformed(
    inputs_module: ast.Module,
    graphql_schema: gql.GraphQLSchema,
) -> None:
    """Test that our plugin transforms fields as expected."""
    plugin = UnsetInputTypesPlugin(graphql_schema, {})

    # Extract the AST node for the ManagerFilter
    manager_filter_ast = inputs_module.body[4]
    assert isinstance(manager_filter_ast, ast.ClassDef)
    assert manager_filter_ast.name == "ManagerFilter"
    # Extract the AST node for the employee assignment
    employee_assignment = one(manager_filter_ast.body)
    assert isinstance(employee_assignment, ast.AnnAssign)
    assert isinstance(employee_assignment.target, ast.Name)
    assert employee_assignment.target.id == "employee"
    assert isinstance(employee_assignment.annotation, ast.Subscript)
    assert isinstance(employee_assignment.annotation.slice, ast.Constant)
    assert employee_assignment.annotation.slice.value == "EmployeeFilter"
    assert isinstance(employee_assignment.annotation.value, ast.Name)
    assert employee_assignment.annotation.value.id == "Optional"

    # Extract the GraphQL node for the Manager Filter
    manager_filter_gql = graphql_schema.type_map["ManagerFilter"]
    assert isinstance(manager_filter_gql, gql.GraphQLInputObjectType)
    # Extract the AST node for the employee assignment
    employee_input_gql = manager_filter_gql.fields["employee"]
    assert isinstance(employee_input_gql, gql.GraphQLInputField)

    # Run the plugin, and check the output
    updated = plugin.generate_input_field(
        field_implementation=employee_assignment,
        input_field=employee_input_gql,
        field_name="employee",
    )
    assert isinstance(updated.target, ast.Name)
    assert updated.target.id == "employee"

    assert isinstance(updated.annotation, ast.BinOp)
    assert updated.annotation.left == employee_assignment.annotation
    assert isinstance(updated.annotation.op, ast.BitOr)
    assert isinstance(updated.annotation.right, ast.Name)
    assert updated.annotation.right.id == "UnsetType"

    assert isinstance(updated.value, ast.Name)
    assert updated.value.id == "UNSET"


def test_plugin_field_transformation_address_transformed(
    inputs_module: ast.Module,
    graphql_schema: gql.GraphQLSchema,
) -> None:
    """Test that our plugin transforms fields as expected."""
    plugin = UnsetInputTypesPlugin(graphql_schema, {})

    # Extract the AST node for the ManagerFilter
    address_create_input_ast = inputs_module.body[6]
    assert isinstance(address_create_input_ast, ast.ClassDef)
    assert address_create_input_ast.name == "AddressCreateInput"
    # Extract the AST node for the validity assignment
    validity_assignment = one(address_create_input_ast.body)
    assert isinstance(validity_assignment, ast.AnnAssign)
    assert isinstance(validity_assignment.target, ast.Name)
    assert validity_assignment.target.id == "validity"
    assert isinstance(validity_assignment.annotation, ast.Constant)
    assert validity_assignment.annotation.value == "Optional[RAValidityInput]"

    # Extract the GraphQL node for the Manager Filter
    address_create_input_gql = graphql_schema.type_map["AddressCreateInput"]
    assert isinstance(address_create_input_gql, gql.GraphQLInputObjectType)
    # Extract the AST node for the validity assignment
    validity_input_gql = address_create_input_gql.fields["validity"]
    assert isinstance(validity_input_gql, gql.GraphQLInputField)

    # Run the plugin, and check the output
    updated = plugin.generate_input_field(
        field_implementation=validity_assignment,
        input_field=validity_input_gql,
        field_name="validity",
    )
    assert isinstance(updated.target, ast.Name)
    assert updated.target.id == "validity"

    assert isinstance(updated.annotation, ast.Name)
    assert updated.annotation.id == '"Optional[RAValidityInput] | UnsetType"'

    assert isinstance(updated.value, ast.Name)
    assert updated.value.id == "UNSET"


def test_plugin_commentor(graphql_schema: gql.GraphQLSchema) -> None:
    plugin = UnsetInputTypesPlugin(graphql_schema, {})
    result = plugin.generate_inputs_code("")
    assert result == "# This file has been modified by the UnsetInputTypesPlugin\n"
