# django-pg-set

Temporarily SET PostgreSQL GUCs within a Django scope.

Provides two decorator/context managers:

- **`pg_set`** — issues `SET <name> = <value>` on entry and `RESET <name>` on exit.
- **`atomic_set`** — wraps the scope in `atomic()` and uses `SET LOCAL`, which automatically reverts when the transaction ends.

## Installation

```bash
pip install django-pg-set
```

## Usage

### `pg_set` — session-level SET / RESET

```python
from pg_set_django import pg_set

# Single GUC, as a context manager:
with pg_set("work_mem", "256MB"):
    MyModel.objects.complex_query()

# Multiple GUCs:
with pg_set([("work_mem", "256MB"), ("statement_timeout", "30s")]):
    MyModel.objects.complex_query()

# Specify database connection:
with pg_set("work_mem", "256MB", using="analytics"):
    MyModel.objects.using("analytics").complex_query()

# As a decorator:
@pg_set("work_mem", "256MB")
def my_view(request):
    ...
```

On exit, `pg_set` issues `RESET <name>` for each GUC, restoring it to the server's configured default. If a `RESET` fails, a `RuntimeWarning` is emitted and cleanup continues.

### `atomic_set` — transaction-level SET LOCAL

```python
from pg_set_django import atomic_set

# Wraps the scope in a transaction and issues SET LOCAL:
with atomic_set("work_mem", "256MB"):
    MyModel.objects.complex_query()

# Multiple GUCs:
with atomic_set([("work_mem", "256MB"), ("statement_timeout", "30s")]):
    MyModel.objects.complex_query()

# As a decorator:
@atomic_set("work_mem", "256MB")
def my_view(request):
    ...
```

`atomic_set` opens a transaction via Django's `atomic()` and issues`SET LOCAL` for each GUC. The settings automatically revert when the transaction commits or rolls back — no explicit `RESET` is needed.

Note that this takes no pains to ensure you are running on a PostgreSQL backend.

## Parameters

Both `pg_set` and `atomic_set` accept the same parameters:

| Parameter | Description |
|-----------|-------------|
| `name, value` | A single GUC name and value as two positional arguments. |
| `iterable` | An iterable of `(name, value)` tuples for multiple GUCs. |
| `using` | Django database alias (default: `"default"`). |

## When to use which

| | `pg_set` | `atomic_set` |
|---|---|---|
| **Mechanism** | `SET` / `RESET` | `SET LOCAL` inside `atomic()` |
| **Scope** | Session (connection) | Transaction |
| **Cleanup** | Explicit `RESET` on exit | Automatic on `COMMIT` / `ROLLBACK` |
| **Use when** | You don't want or need a transaction | You want GUC changes tied to a transaction |

## Requirements

- Python 3.10+
- Django 4.2+
- PostgreSQL with psycopg2 or psycopg3

## License

PostgreSQL License. See [LICENSE](LICENSE) for details.
