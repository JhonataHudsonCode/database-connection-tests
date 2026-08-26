import os
import time

import psycopg2


def _redact_error(message: str, password: str | None) -> str:
    """Evita que uma senha apareça acidentalmente em logs/relatórios."""
    if password:
        return message.replace(password, "***")
    return message


def test_postgres(config: dict) -> dict:
    """
    Valida conectividade + autenticação no PostgreSQL do cliente
    executando SELECT 1.
    """
    start = time.perf_counter()
    connection = None
    sslmode = os.getenv("POSTGRES_CLIENT_SSLMODE", "").strip()

    connection_args = {
        "host": config["host"],
        "port": int(config["port"]),
        "database": config["database"],
        "user": config["user"],
        "password": config["password"],
        "connect_timeout": int(os.getenv("CONNECTION_TIMEOUT_SECONDS", "10")),
    }

    if sslmode:
        connection_args["sslmode"] = sslmode

    try:
        connection = psycopg2.connect(**connection_args)

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "status": "OK",
            "response": f"SELECT 1 = {result[0]}",
            "time_ms": round(elapsed, 2),
            "error": None,
        }

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000

        return {
            "status": "ERROR",
            "response": None,
            "time_ms": round(elapsed, 2),
            "error": _redact_error(str(exc), config.get("password")),
        }

    finally:
        if connection is not None:
            connection.close()


def list_postgres_databases(config: dict) -> dict:
    """Lista bancos de dados visiveis na conexao PostgreSQL do cliente."""
    start = time.perf_counter()
    connection = None
    sslmode = os.getenv("POSTGRES_CLIENT_SSLMODE", "").strip()

    connection_args = {
        "host": config["host"],
        "port": int(config["port"]),
        "database": config["database"],
        "user": config["user"],
        "password": config["password"],
        "connect_timeout": int(os.getenv("CONNECTION_TIMEOUT_SECONDS", "10")),
    }

    if sslmode:
        connection_args["sslmode"] = sslmode

    try:
        connection = psycopg2.connect(**connection_args)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT datname
                FROM pg_database
                WHERE datistemplate = FALSE
                ORDER BY datname
                """
            )
            databases = [row[0] for row in cursor.fetchall()]

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "status": "OK",
            "response": f"databases={', '.join(databases)}",
            "time_ms": round(elapsed, 2),
            "databases": databases,
            "error": None,
        }

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000

        return {
            "status": "ERROR",
            "response": None,
            "time_ms": round(elapsed, 2),
            "databases": [],
            "error": _redact_error(str(exc), config.get("password")),
        }

    finally:
        if connection is not None:
            connection.close()
