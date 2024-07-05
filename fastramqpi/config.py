# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
"""Settings handling."""
from pydantic import ConfigDict, AnyHttpUrl
from pydantic import BaseModel
from pydantic import Field
from pydantic import parse_obj_as
from pydantic import SecretStr

from .ramqp.config import AMQPConnectionSettings
from pydantic_settings import BaseSettings, SettingsConfigDict


# pylint: disable=too-few-public-methods
class FastAPIIntegrationSystemSettings(BaseSettings):
    """Settings for the FastAPIIntegrationSystem framework."""
    model_config = SettingsConfigDict(frozen=True)

    # We assume these will be set by the docker build process,
    # and as such will contain release information at runtime.
    commit_tag: str = Field("HEAD", description="Git commit tag.")
    commit_sha: str = Field("HEAD", description="Git commit SHA.")

    log_level: str = Field("INFO", description="Log level to configure.")
    dap: bool = Field(False, description="Whether to enable debugging")

    enable_metrics: bool = Field(True, description="Whether to enable metrics.")


# pylint: disable=too-few-public-methods
class DatabaseSettings(BaseModel):
    """Settings for the postgresql database connection."""

    user: str
    password: str
    host: str
    port: int = 5432
    name: str


# pylint: disable=too-few-public-methods
class ClientSettings(BaseSettings):
    """Settings for the connection to OS2mo."""
    model_config = SettingsConfigDict(frozen=True)

    mo_url: AnyHttpUrl = Field(
        parse_obj_as(AnyHttpUrl, "http://mo-service:5000"),
        description="Base URL for OS2mo.",
    )

    client_id: str = Field(..., description="Client ID for OIDC client.")
    client_secret: SecretStr = Field(..., description="Client Secret for OIDC client.")
    auth_server: AnyHttpUrl = Field(
        parse_obj_as(AnyHttpUrl, "http://keycloak-service:8080/auth"),
        description="Base URL for OIDC server (Keycloak).",
    )
    auth_realm: str = Field("mo", description="Realm to authenticate against")
    graphql_timeout: int = Field(120, description="Timeout for GraphQL queries")


# pylint: disable=too-few-public-methods
class Settings(FastAPIIntegrationSystemSettings, ClientSettings):
    """Settings for the FastRAMQPI framework."""
    model_config = ConfigDict(frozen=True, env_nested_delimiter="__")

    amqp: AMQPConnectionSettings
    database: DatabaseSettings | None
