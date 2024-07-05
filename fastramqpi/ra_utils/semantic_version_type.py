# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import re
from functools import lru_cache
from typing import Any
from typing import Dict
from typing import Pattern

from pydantic import BaseModel
from pydantic import GetCoreSchemaHandler
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from pydantic_core import CoreSchema


# Regex from https://semver.org/
_semver_regex = (
    # Version part
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    # Prerelease part
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    # Build metadata
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


@lru_cache
def get_regex() -> Pattern:
    return re.compile(_semver_regex)


class SemanticVersion(str):
    """Pydantic field model for validating semantic versioning.

    See: <a href="https://semver.org/">semver.org</a> for details.

    Example:
        ```Python
        version = "1.1.2+meta-valid"
        SemanticVersion.validate(version)
        ```
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls.validate, handler(str))

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema["examples"] = (["0.1.0", "1.0.0-alpha", "1.0.0-alpha+001"],)
        json_schema["pattern"] = _semver_regex
        return json_schema

    @classmethod
    # TODO[pydantic]: We couldn't refactor `__modify_schema__`, please create the `__get_pydantic_json_schema__` manually.
    # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
    def __modify_schema__(cls, field_schema: Dict) -> None:
        field_schema.update(
            pattern=_semver_regex,
        )

    @classmethod
    def validate(cls, v: Any) -> "SemanticVersion":
        """Validate that `v` is a valid semantic version.

        Args:
            v: Value to validate against semver regex.

        Raises:
            TypeError: If `v` is not a string
            ValueError: If `v` does not match the semver regex.

        Returns:
            Validated field model.
        """
        if not isinstance(v, str):
            raise TypeError("string required")
        m = get_regex().fullmatch(v)
        if not m:
            raise ValueError("invalid semver format")
        return cls(v)

    def __repr__(self) -> str:
        return f"SemanticVersion({super().__repr__()})"


class SemanticVersionModel(BaseModel):
    """Pydantic model for validating semantic versioning.

    See: <a href="https://semver.org/">semver.org</a> for details.

    Example:
        ```Python
        version = "1.1.2+meta-valid"
        SemanticVersionModel(__root__=version)
        ```

    Example:
        ```Python
        schema = SemanticVersionModel.schema()
        print(json.dumps(schema))
        ```
        Which yields:
        ```Json
        {
            "title": "SemanticVersionModel",
            "description": "...",
            "pattern": "^(?P<major>0|[1-9]\\d*)...$",
            "examples": [
                "0.1.0",
                "1.0.0-alpha",
                "1.0.0-alpha+001"
            ],
            "type": "string"
        }
        ```
    """

    __root__: SemanticVersion
