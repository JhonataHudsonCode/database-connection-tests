import pytest

from src.central_database import get_clients, validate_central_connection
from src.connection_service import test_connection
from src.opensearch import list_opensearch_indices
from src.postgres import list_postgres_databases


REQUIRED_CLIENT_KEYS = {
    "id",
    "name",
    "db_type",
    "host",
    "port",
    "database",
    "user",
    "password",
}


def _assert_client_payload(client):
    if not isinstance(client, dict):
        pytest.fail(
            "Cada cliente precisa ser um dicionario. "
            f"Valor recebido: {client!r} ({type(client).__name__})",
            pytrace=False,
        )

    missing_keys = REQUIRED_CLIENT_KEYS - set(client)
    if missing_keys:
        pytest.fail(
            "Cliente retornado pelo banco central esta sem campos obrigatorios: "
            f"{sorted(missing_keys)}. Cliente: {client!r}",
            pytrace=False,
        )


def _assert_clients_payload(items):
    if not isinstance(items, list):
        pytest.fail(
            "get_clients() deve retornar uma lista de clientes. "
            f"Valor recebido: {items!r} ({type(items).__name__})",
            pytrace=False,
        )

    for client in items:
        _assert_client_payload(client)


def _client_db_type(client):
    _assert_client_payload(client)
    return str(client.get("db_type", "")).strip().lower()


def _client_label(client, database_type=None):
    _assert_client_payload(client)
    db_type = database_type or client["db_type"]
    return f"{client['name']} | {db_type} | {client['host']}:{client['port']}"


def _filter_clients_by_type(clients, valid_types):
    _assert_clients_payload(clients)
    return [
        client
        for client in clients
        if _client_db_type(client) in valid_types
    ]


@pytest.fixture(scope="session")
def clients():
    try:
        items = get_clients()
    except Exception as exc:
        pytest.fail(
            f"Não foi possível buscar os clientes no banco central: {exc}",
            pytrace=False,
        )

    _assert_clients_payload(items)

    if not items:
        pytest.fail(
            "Nenhum cliente ativo foi retornado pelo banco central.",
            pytrace=False,
        )

    return items


@pytest.fixture(scope="session")
def postgres_clients(clients):
    items = _filter_clients_by_type(clients, {"postgres", "postgresql"})

    if not items:
        pytest.skip("Nenhum cliente PostgreSQL ativo foi retornado pelo banco central.")

    return items


@pytest.fixture(scope="session")
def opensearch_clients(clients):
    items = _filter_clients_by_type(clients, {"opensearch"})

    if not items:
        pytest.skip("Nenhum cliente OpenSearch ativo foi retornado pelo banco central.")

    return items


def _assert_postgres_database_listing(client):
    label = _client_label(client, "PostgreSQL")
    result = list_postgres_databases(client)

    print(f"{label} | bancos: {result.get('databases', [])}")

    assert result["status"] == "OK", (
        f"Nao foi possivel listar bancos PostgreSQL em {label}. "
        f"Erro: {result['error']}"
    )
    print(f"{label} | conexao estabelecida")
    assert result["databases"], f"Nenhum banco PostgreSQL foi listado em {label}."


def _assert_opensearch_index_listing(client):
    label = _client_label(client, "OpenSearch")
    result = list_opensearch_indices(client)

    print(f"{label} | indices: {result.get('indices', [])}")

    assert result["status"] == "OK", (
        f"Autenticacao/listagem de indices OpenSearch falhou em {label}. "
        f"Erro: {result['error']}"
    )
    print(f"{label} | conexao estabelecida")
    assert result["indices"] is not None, (
        f"OpenSearch autenticou em {label}, mas nao retornou listagem de indices."
    )


@pytest.mark.integration
def test_central_database_connection():
    """Valida explicitamente se o PostgreSQL central está acessível."""
    result = validate_central_connection()

    assert result["status"] == "OK", (
        "Conexao com PostgreSQL central nao estabelecida. "
        f"Erro: {result['error']}"
    )
    print("PostgreSQL central | conexao estabelecida")
    print(f"PostgreSQL central | detalhes: {result['details']}")


@pytest.mark.integration
@pytest.mark.skip(reason="Etapa atual valida apenas conexao, sem queries.")
def test_client_database_connections(clients, subtests):
    """
    Executa um subteste para cada cliente.

    Uma falha não interrompe a validação dos demais clientes.
    """
    for client in clients:
        label = _client_label(client)

        with subtests.test(msg=label):
            result = test_connection(client)

            assert result["status"] == "OK", (
                f"Falha de conexão em {label}. "
                f"Erro: {result['error']}"
            )


@pytest.mark.integration
@pytest.mark.skip(reason="Etapa atual valida apenas conexao, sem queries.")
def test_postgres_database_listing(postgres_clients, subtests):
    """Lista os bancos visiveis em cada conexao PostgreSQL."""
    for client in postgres_clients:
        label = _client_label(client, "PostgreSQL")

        with subtests.test(msg=label):
            _assert_postgres_database_listing(client)


@pytest.mark.integration
@pytest.mark.skip(reason="Etapa atual valida apenas conexao, sem queries.")
def test_opensearch_authentication_and_index_listing(opensearch_clients, subtests):
    """Valida autenticacao e lista indices visiveis em cada OpenSearch."""
    for client in opensearch_clients:
        label = _client_label(client, "OpenSearch")

        with subtests.test(msg=label):
            _assert_opensearch_index_listing(client)


@pytest.mark.integration
@pytest.mark.skip(reason="Etapa atual valida apenas conexao, sem queries.")
def test_postgres_database_listing_and_opensearch_index_listing(
    postgres_clients,
    opensearch_clients,
    subtests,
):
    """Executa a listagem PostgreSQL e a listagem de indices OpenSearch."""
    for client in postgres_clients:
        label = _client_label(client, "PostgreSQL")

        with subtests.test(msg=label):
            _assert_postgres_database_listing(client)

    for client in opensearch_clients:
        label = _client_label(client, "OpenSearch")

        with subtests.test(msg=label):
            _assert_opensearch_index_listing(client)
