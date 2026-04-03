import functools
import warnings
from contextlib import contextmanager

from django.db import connections, transaction


@contextmanager
def _pg_set_context(settings, using):
    """Core context manager: SET each GUC, yield, then RESET each."""
    conn = connections[using]
    conn.ensure_connection()

    applied = []
    try:
        with conn.cursor() as cursor:
            for name, value in settings:
                cursor.execute(f"SET {name} = %s", [value])
                applied.append(name)
        yield
    finally:
        with conn.cursor() as cursor:
            for name in reversed(applied):
                try:
                    cursor.execute(f"RESET {name}")
                except Exception as exc:
                    warnings.warn(
                        f"pg_set: failed to RESET {name}: {exc}",
                        RuntimeWarning,
                        stacklevel=2,
                    )


def _normalize_settings(args):
    """Normalize the flexible call signatures into a list of (name, value) tuples.

    Accepts:
        ("name", "value")           -> single GUC
        (iterable_of_tuples,)       -> multiple GUCs
    """
    if len(args) == 2 and isinstance(args[0], str):
        return [(args[0], args[1])]

    if len(args) == 1:
        items = list(args[0])
        if not items:
            return []
        return [(name, value) for name, value in items]

    raise TypeError(
        "pg_set expects either (name, value) or (iterable_of_tuples,). "
        f"Got {len(args)} arguments."
    )


class _PgSet:
    """Decorator / context manager that temporarily SETs PostgreSQL GUCs."""

    def __init__(self, *args, using="default"):
        self._settings = _normalize_settings(args)
        self._using = using

    def __enter__(self):
        self._cm = _pg_set_context(self._settings, self._using)
        return self._cm.__enter__()

    def __exit__(self, *exc_info):
        return self._cm.__exit__(*exc_info)

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with _pg_set_context(self._settings, self._using):
                return func(*args, **kwargs)

        return wrapper


def pg_set(*args, **kwargs):
    """Temporarily SET PostgreSQL GUCs within a scope.

    Usage:
        # Single GUC, as context manager:
        with pg_set("work_mem", "256MB"):
            ...

        # Multiple GUCs:
        with pg_set([("work_mem", "256MB"), ("statement_timeout", "30s")]):
            ...

        # Specify database connection:
        with pg_set("work_mem", "256MB", using="other_db"):
            ...

        # As a decorator:
        @pg_set("work_mem", "256MB")
        def my_view(request):
            ...
    """
    return _PgSet(*args, **kwargs)


@contextmanager
def _atomic_set_context(settings, using):
    """Core context manager: atomic() + SET LOCAL each GUC."""
    conn = connections[using]
    with transaction.atomic(using=using):
        conn.ensure_connection()
        with conn.cursor() as cursor:
            for name, value in settings:
                cursor.execute(f"SET LOCAL {name} = %s", [value])
        yield


class _AtomicSet:
    """Decorator / context manager that wraps atomic() with SET LOCAL GUCs."""

    def __init__(self, *args, using="default"):
        self._settings = _normalize_settings(args)
        self._using = using

    def __enter__(self):
        self._cm = _atomic_set_context(self._settings, self._using)
        return self._cm.__enter__()

    def __exit__(self, *exc_info):
        return self._cm.__exit__(*exc_info)

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with _atomic_set_context(self._settings, self._using):
                return func(*args, **kwargs)

        return wrapper


def atomic_set(*args, **kwargs):
    """Wrap a scope in atomic() with SET LOCAL for PostgreSQL GUCs.

    The GUCs are automatically reverted when the transaction ends —
    no RESET is needed.

    Usage:
        # Single GUC, as context manager:
        with atomic_set("work_mem", "256MB"):
            ...

        # Multiple GUCs:
        with atomic_set([("work_mem", "256MB"), ("statement_timeout", "30s")]):
            ...

        # Specify database connection:
        with atomic_set("work_mem", "256MB", using="other_db"):
            ...

        # As a decorator:
        @atomic_set("work_mem", "256MB")
        def my_view(request):
            ...
    """
    return _AtomicSet(*args, **kwargs)
