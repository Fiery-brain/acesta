from django.db import connection
from django.test import TransactionTestCase

from acesta.base.locks import postgres_lock
from acesta.base.locks import PostgresLockError


class PostgresLockTest(TransactionTestCase):
    def setUp(self):
        self.second_connection = connection.copy()
        self.addCleanup(self.second_connection.close)

    def test_same_key_cannot_be_taken_by_another_connection(self):
        with postgres_lock("test-lock"):
            with self.assertRaises(PostgresLockError):
                with postgres_lock("test-lock", connection=self.second_connection):
                    pass

    def test_lock_is_available_after_context_exit(self):
        with postgres_lock("reusable-lock"):
            pass

        with postgres_lock("reusable-lock", connection=self.second_connection):
            pass

    def test_different_keys_do_not_conflict(self):
        with postgres_lock("first-lock"):
            with postgres_lock("second-lock", connection=self.second_connection):
                pass

    def test_lock_is_released_after_exception(self):
        with self.assertRaises(ValueError):
            with postgres_lock("exception-lock"):
                raise ValueError("boom")

        with postgres_lock("exception-lock", connection=self.second_connection):
            pass
