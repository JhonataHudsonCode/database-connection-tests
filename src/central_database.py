import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _optional_sslmode(env_name: str) -> dict:
    sslmode = os.getenv(env_name, "").strip()
    return {"sslmode": sslmode} if sslmode else {}


def get_central_connection():
    """Abre uma conexão com o PostgreSQL central."""
    return psycopg2.connect(
        host=os.getenv("CENTRAL_DB_HOST"),
        port=int(os.getenv("CENTRAL_DB_PORT", "5432")),
        database=os.getenv("CENTRAL_DB_NAME"),
        user=os.getenv("CENTRAL_DB_USER"),
        password=os.getenv("CENTRAL_DB_PASSWORD"),
        connect_timeout=int(os.getenv("CONNECTION_TIMEOUT_SECONDS", "10")),
        **_optional_sslmode("CENTRAL_DB_SSLMODE"),
    )


def _format_server_version(server_version: int) -> str:
    major = server_version // 10000
    minor = (server_version // 100) % 100
    patch = server_version % 100

    if major >= 10:
        return f"{major}.{patch}"

    return f"{major}.{minor}.{patch}"


def _get_connection_details(connection) -> dict:
    dsn_parameters = connection.get_dsn_parameters()
    safe_dsn_keys = ("host", "port", "dbname", "user", "sslmode")
    safe_dsn_parameters = {
        key: dsn_parameters.get(key)
        for key in safe_dsn_keys
        if dsn_parameters.get(key)
    }

    return {
        "dsn": safe_dsn_parameters,
        "encoding": connection.encoding,
        "protocol_version": connection.protocol_version,
        "server_version": _format_server_version(connection.server_version),
        "server_version_number": connection.server_version,
        "status": connection.status,
        "transaction_status": connection.get_transaction_status(),
        "autocommit": connection.autocommit,
        "readonly": connection.readonly,
        "closed": bool(connection.closed),
    }


def validate_central_connection() -> dict:
    """Valida apenas abertura de conexao, sem executar queries."""
    connection = None

    try:
        connection = get_central_connection()
        details = _get_connection_details(connection)

        return {
            "status": "OK",
            "response": "conexao estabelecida",
            "details": details,
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "response": None,
            "details": {},
            "error": str(exc),
        }
    finally:
        if connection is not None:
            connection.close()


def get_clients():
    """
    Busca no PostgreSQL central as credenciais dos bancos dos clientes.

    Ajuste o SELECT e o mapeamento abaixo para refletir a tabela real
    da sua aplicação.
    """
    connection = get_central_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    cliente_nome,
                    db_type,
                    db_host,
                    db_port,
                    db_name,
                    db_user,
                    db_password
                FROM clientes_bancos
                WHERE ativo = TRUE
                ORDER BY cliente_nome
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "db_type": row[2],
                "host": row[3],
                "port": row[4],
                "database": row[5],
                "user": row[6],
                "password": row[7],
            }
            for row in rows
        ]
    finally:
        connection.close()
