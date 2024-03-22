# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from unittest import TestCase
from uuid import UUID

from hypothesis import given
from hypothesis.strategies import text

from fastramqpi.ra_utils.generate_uuid import _generate_uuid
from fastramqpi.ra_utils.generate_uuid import generate_uuid
from fastramqpi.ra_utils.generate_uuid import uuid_generator


class test_generate_uuid(TestCase):
    @given(text(), text())
    def test_generate_uuid(self, base: str, value: str) -> None:
        uuid1 = generate_uuid(base, value)
        _generate_uuid.cache_clear()
        uuid2 = generate_uuid(base, value)
        _generate_uuid.cache_clear()
        uuid3 = generate_uuid(base, value + "A different string")
        assert uuid1 == uuid2
        assert uuid1 != uuid3
        assert isinstance(uuid1, UUID)

    @given(text(), text())
    def test_create_generator(self, base: str, value: str) -> None:
        gen = uuid_generator(base)
        uuid1 = gen(value)
        uuid2 = gen(value)
        assert uuid1 == uuid2
        assert uuid_generator(value) != gen(value + "Another string")
        assert isinstance(uuid1, UUID)

    @given(text(), text())
    def test_generator_output(self, base: str, value: str) -> None:
        assert generate_uuid(base, value) == uuid_generator(base)(value)

    def test_predictable_outputs(self) -> None:
        gen = uuid_generator("kommune")
        uuid1 = gen("key1")
        uuid2 = gen("key2")
        assert uuid1 == UUID("fd995619-6f00-cf70-2569-b3f578d9c0da")
        assert uuid2 == UUID("673e80c5-ae64-632e-4a50-fb2f082f8989")

        uuid3 = generate_uuid("kommune", "key3")
        uuid4 = generate_uuid("kommune", "key4")
        assert uuid3 == UUID("eda99313-033b-50ee-6485-0b0ba30a5f62")
        assert uuid4 == UUID("3e4fbcd4-83d4-976c-3838-f077e9b39129")
