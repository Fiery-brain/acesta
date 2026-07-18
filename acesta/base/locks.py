import hashlib
from contextlib import contextmanager

from django.db import connection as default_connection


class PostgresLockError(RuntimeError):
    pass


class PostgresLockTimeoutError(PostgresLockError):
    pass


def _make_lock_id(key: str) -> int:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=True)


@contextmanager
def postgres_lock(key: str, connection=None):
    connection = connection or default_connection
    lock_id = _make_lock_id(key)
    acquired = False

    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [lock_id])
        acquired = cursor.fetchone()[0]

    if not acquired:
        raise PostgresLockError(f"PostgreSQL advisory lock is already taken: {key}")

    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_id])
