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
