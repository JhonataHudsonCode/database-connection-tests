import pytest

from src.central_database import get_central_connection, get_clients
from src.connection_service import test_connection


@pytest.fixture(scope="session")
def clients():
    try:
        items = get_clients()
    except Exception as exc:
        pytest.fail(
            f"Não foi possível buscar os clientes no banco central: {exc}",
            pytrace=False,
        )

    if not items:
        pytest.fail(
            "Nenhum cliente ativo foi retornado pelo banco central.",
            pytrace=False,
        )

    return items


@pytest.mark.integration
def test_central_database_connection():
    """Valida explicitamente se o PostgreSQL central está acessível."""
    connection = None

    try:
        connection = get_central_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
    finally:
        if connection is not None:
            connection.close()


@pytest.mark.integration
def test_client_database_connections(clients, subtests):
    """
    Executa um subteste para cada cliente.

    Uma falha não interrompe a validação dos demais clientes.
    """
    for client in clients:
        label = (
            f"{client['name']} | {client['db_type']} | "
            f"{client['host']}:{client['port']}"
        )

        with subtests.test(msg=label):
            result = test_connection(client)

            assert result["status"] == "OK", (
                f"Falha de conexão em {label}. "
                f"Erro: {result['error']}"
            )
