# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from _pytest.monkeypatch import MonkeyPatch
from pydantic.v1 import BaseSettings
from pydantic.v1 import Field
from pydantic.v1 import ValidationError

from fastramqpi.ra_utils.structured_url import StructuredUrl


def _assert_parsed(structured_url: StructuredUrl) -> None:
    assert (
        structured_url.url
        == "https://username:password@example.com:1234/valid?a=b#here"
    )
    assert structured_url.url.scheme == "https"
    assert structured_url.scheme == "https"
    assert structured_url.url.user == "username"
    assert structured_url.user == "username"
    assert structured_url.url.password == "password"
    assert structured_url.password is not None
    assert structured_url.password.get_secret_value() == "password"
    assert structured_url.url.host == "example.com"
    assert structured_url.host == "example.com"
    assert structured_url.url.port == "1234"
    assert structured_url.port == 1234
    assert structured_url.url.path == "/valid"
    assert structured_url.path == "/valid"
    assert structured_url.url.query == "a=b"
    assert structured_url.query == {"a": "b"}
    assert structured_url.url.fragment == "here"
    assert structured_url.fragment == "here"


def test_can_provide_url_directly() -> None:
    structured_url = StructuredUrl(
        url="https://username:password@example.com:1234/valid?a=b#here"
    )
    _assert_parsed(structured_url)


def test_can_provide_url_indirectly() -> None:
    structured_url = StructuredUrl(  # type: ignore[call-arg]
        scheme="https",
        user="username",
        password="password",
        host="example.com",
        port="1234",
        path="/valid",
        query={"a": "b"},
        fragment="here",
    )
    _assert_parsed(structured_url)


def test_that_passwords_are_url_encoded() -> None:
    structured_url = StructuredUrl(  # type: ignore[call-arg]
        scheme="https",
        user="user@domain.com",
        password="p@ssword",
        host="example.com",
    )
    assert structured_url.url == "https://user%40domain.com:p%40ssword@example.com"


def test_no_args_not_ok() -> None:
    with pytest.raises(ValidationError):
        StructuredUrl()  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        StructuredUrl(scheme="http")  # type: ignore[call-arg]
    StructuredUrl(scheme="http", host="a")  # type: ignore[call-arg]


def _assert_parsed_minimal(structured_url: StructuredUrl) -> None:
    assert structured_url.url == "http://a"
    assert structured_url.url.scheme == "http"
    assert structured_url.scheme == "http"
    assert structured_url.url.host == "a"
    assert structured_url.host == "a"
    assert structured_url.query == {}

    none_fields = {"user", "password", "port", "path", "fragment"}
    for key in none_fields:
        assert getattr(structured_url.url, key) is None
        assert getattr(structured_url, key) is None


def test_minimal_url_directly_ok() -> None:
    structured_url = StructuredUrl(url="http://a")
    _assert_parsed_minimal(structured_url)


def test_minimal_url_indirectly_ok() -> None:
    structured_url = StructuredUrl(scheme="http", host="a")  # type: ignore[call-arg]
    _assert_parsed_minimal(structured_url)


def test_url_is_conflicts_with_others() -> None:
    # Conflicting information here, url always wins
    with pytest.raises(ValidationError):
        StructuredUrl(url="https://b", scheme="http", host="a")


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://username:password@example.com/mypath#here?now=1",
        "postgresql://username:password@db/mydb",
        "postgresql+asyncpg://username:password@db/mydb",
    ],
)
def test_that_urls_are_ok(url: str) -> None:
    StructuredUrl(url=url)


@pytest.mark.parametrize(
    "url",
    [
        "sqlite+aiosqlite:///:memory:",
        "sqlite:///db.sqlite3",
        "sqlite+aiosqlite:///db.sqlite3",
        "sqlite:////C:/db.sqlite3",
        "sqlite+aiosqlite:////tmp/db.sqlite3",
    ],
)
def test_that_urls_are_rejected(url: str) -> None:
    with pytest.raises(ValidationError):
        StructuredUrl(url=url)


class Settings(BaseSettings):
    class Config:
        env_nested_delimiter = "__"

    database: StructuredUrl = Field(default_factory=StructuredUrl)  # type: ignore[arg-type]


def test_settings_missing_scheme() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert "scheme is required" in str(exc_info.value)


def test_settings_bad_scheme(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE__SCHEME", "postgresql://")
    monkeypatch.setenv("DATABASE__HOST", "database.example.org")
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert (
        "URL invalid, extra characters found after valid URL: '://database.example.org'"
        in str(exc_info.value)
    )


def test_settings_bad_path(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE__SCHEME", "postgresql")
    monkeypatch.setenv("DATABASE__HOST", "database.example.org")
    monkeypatch.setenv("DATABASE__PORT", "5432")
    monkeypatch.setenv("DATABASE__PATH", "mox")
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert "URL invalid, extra characters found after valid URL: 'mox'" in str(
        exc_info.value
    )


def test_settings(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE__SCHEME", "postgresql")
    monkeypatch.setenv("DATABASE__USER", "AzureDiamond")
    monkeypatch.setenv("DATABASE__PASSWORD", "hunter2")
    monkeypatch.setenv("DATABASE__HOST", "database.example.org")
    monkeypatch.setenv("DATABASE__PORT", "5432")
    monkeypatch.setenv("DATABASE__PATH", "/mox")
    monkeypatch.setenv("DATABASE__QUERY", '{"sslmode": "require"}')
    Settings()
