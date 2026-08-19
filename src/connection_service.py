from src.opensearch import test_opensearch
from src.postgres import test_postgres


def test_connection(client: dict) -> dict:
    """Direciona a validação conforme o tipo de banco do cliente."""
    db_type = str(client.get("db_type", "")).strip().lower()

    if db_type in {"postgres", "postgresql"}:
        return test_postgres(client)

    if db_type == "opensearch":
        return test_opensearch(client)

    return {
        "status": "ERROR",
        "response": None,
        "time_ms": 0,
        "error": f"Tipo de banco não suportado: {db_type or '<vazio>'}",
    }
