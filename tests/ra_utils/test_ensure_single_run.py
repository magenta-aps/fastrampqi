# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import prometheus_client.exposition
from parameterized import parameterized

import fastramqpi.ra_utils.ensure_single_run as esr


def is_lock_taken(lock_name: str):
    return esr._is_lock_taken(lock_name=lock_name)


def lock_test(lock_name: str, lock_content: str):
    with open(lock_name, "w") as lock:
        lock.write(lock_content)
        lock.flush()

    locked = is_lock_taken(lock_name=lock_name)

    os.remove(lock_name)

    return locked


def compare_reg_content(
    registry: prometheus_client.CollectorRegistry, expected_locked: bool
):
    prom_str = str(prometheus_client.exposition.generate_latest(registry))

    if expected_locked:
        assert "mo_return_code 1.0" in prom_str
    else:
        assert "mo_return_code 0.0" in prom_str

    assert "HELP mo_end_time" in prom_str


class TestEnsureSingleRun(unittest.TestCase):
    lock_name_global = "test_lock"
    str1 = "hej"
    str2 = "bye"

    def input_func(self) -> str:
        return self.str1

    def input_func_fail(self):
        raise NotImplementedError

    @parameterized.expand(
        [
            ("", False),
            ("\n", False),
            ("hej", True),
            (" hej", True)  # it os often just tested if the first char is a
            # whitespace, this test the case where a whitespace is accidentally
            # put in as the first char
        ]
    )
    def test_lock(self, lock_content: str, expected: bool):
        assert (
            lock_test(lock_name=self.lock_name_global, lock_content=lock_content)
            is expected
        )

    @patch("prometheus_client.exposition.pushadd_to_gateway")
    def test_single_run(self, mock_gateway: MagicMock):
        retval = esr.ensure_single_run(
            func=self.input_func, lock_name=self.lock_name_global
        )
        assert retval == self.str1
        mock_gateway.assert_called_once()
        reg: prometheus_client.CollectorRegistry = mock_gateway.call_args[1]["registry"]
        compare_reg_content(registry=reg, expected_locked=False)

    @patch("prometheus_client.exposition.pushadd_to_gateway")
    def test_multi_run(self, mock_gateway: MagicMock):
        # open( , "x") creates a file, and throws an error if the file already exist.
        # If the file already exists something has gone wrong somewhere as the tests,
        # and code, should always clean up after itself
        #
        # This test simulates a running instance is already occurring by taking the
        # lock, and then trying to run, which should fail
        with open(self.lock_name_global, "x") as lock:
            lock.write(self.str2)
            lock.flush()

        assert is_lock_taken(lock_name=self.lock_name_global)
        with self.assertRaises(expected_exception=esr.LockTaken):
            esr.ensure_single_run(func=self.input_func, lock_name=self.lock_name_global)

        os.remove(self.lock_name_global)
        mock_gateway.assert_called_once()
        reg: prometheus_client.CollectorRegistry = mock_gateway.call_args[1]["registry"]
        compare_reg_content(registry=reg, expected_locked=True)

    # Test that if the input function fails we get the right error back and the
    # lock is cleared
    @patch("prometheus_client.exposition.pushadd_to_gateway")
    def test_error_run(self, mock_gateway: MagicMock):
        with self.assertRaises(expected_exception=NotImplementedError):
            esr.ensure_single_run(
                func=self.input_func_fail, lock_name=self.lock_name_global
            )

        assert not esr._is_lock_taken(self.lock_name_global)
        mock_gateway.assert_called_once()
        reg: prometheus_client.CollectorRegistry = mock_gateway.call_args[1]["registry"]
        compare_reg_content(registry=reg, expected_locked=False)

    # Test the teh code runs successfully, even if there is no connection to prometheus
    def test_no_prometheus_connect(self):
        retval = esr.ensure_single_run(
            func=self.input_func, lock_name=self.lock_name_global
        )
        assert retval == self.str1
