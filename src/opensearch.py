import os
import time
import warnings

from opensearchpy import OpenSearch
from urllib3.exceptions import InsecureRequestWarning


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _redact_error(message: str, password: str | None) -> str:
    """Evita que uma senha apareça acidentalmente em logs/relatórios."""
    if password:
        return message.replace(password, "***")
    return message


def test_opensearch(config: dict) -> dict:
    """
    Valida conectividade + autenticação no OpenSearch.

    Primeiro chama GET / (client.info). Depois tenta obter cluster health.
    Se o usuário não tiver permissão de cluster health, a conexão continua
    sendo considerada válida porque o GET / já confirmou serviço/autenticação.
    """
    start = time.perf_counter()
    client = None

    use_ssl = _as_bool(os.getenv("OPENSEARCH_USE_SSL"), True)
    verify_certs = _as_bool(os.getenv("OPENSEARCH_VERIFY_CERTS"), True)
    ca_certs = os.getenv("OPENSEARCH_CA_CERTS", "").strip() or None

    if use_ssl and not verify_certs:
        warnings.filterwarnings("ignore", category=InsecureRequestWarning)

    client_args = {
        "hosts": [{"host": config["host"], "port": int(config["port"])}],
        "http_auth": (config["user"], config["password"]),
        "use_ssl": use_ssl,
        "verify_certs": verify_certs,
        "timeout": int(os.getenv("CONNECTION_TIMEOUT_SECONDS", "10")),
    }

    if ca_certs:
        client_args["ca_certs"] = ca_certs

    try:
        client = OpenSearch(**client_args)

        info = client.info()
        cluster_name = info.get("cluster_name", "desconhecido")
        version = info.get("version", {}).get("number", "desconhecida")

        health_status = "sem permissão/indisponível"
        try:
            health = client.cluster.health()
            health_status = health.get("status", "desconhecido")
        except Exception:
            # A conexão já foi validada pelo client.info().
            # Alguns usuários podem não ter permissão para _cluster/health.
            pass

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "status": "OK",
            "response": (
                f"cluster={cluster_name} | version={version} | "
                f"health={health_status}"
            ),
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
        if client is not None:
            client.close()


def list_opensearch_indices(config: dict) -> dict:
    """Valida autenticacao no OpenSearch e lista indices visiveis."""
    start = time.perf_counter()
    client = None

    use_ssl = _as_bool(os.getenv("OPENSEARCH_USE_SSL"), True)
    verify_certs = _as_bool(os.getenv("OPENSEARCH_VERIFY_CERTS"), True)
    ca_certs = os.getenv("OPENSEARCH_CA_CERTS", "").strip() or None

    if use_ssl and not verify_certs:
        warnings.filterwarnings("ignore", category=InsecureRequestWarning)

    client_args = {
        "hosts": [{"host": config["host"], "port": int(config["port"])}],
        "http_auth": (config["user"], config["password"]),
        "use_ssl": use_ssl,
        "verify_certs": verify_certs,
        "timeout": int(os.getenv("CONNECTION_TIMEOUT_SECONDS", "10")),
    }

    if ca_certs:
        client_args["ca_certs"] = ca_certs

    try:
        client = OpenSearch(**client_args)

        info = client.info()
        cluster_name = info.get("cluster_name", "desconhecido")
        indices_response = client.cat.indices(format="json")
        indices = sorted(
            item.get("index", "")
            for item in indices_response
            if item.get("index")
        )

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "status": "OK",
            "response": (
                f"cluster={cluster_name} | "
                f"indices={', '.join(indices) if indices else '<nenhum>'}"
            ),
            "time_ms": round(elapsed, 2),
            "indices": indices,
            "error": None,
        }

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000

        return {
            "status": "ERROR",
            "response": None,
            "time_ms": round(elapsed, 2),
            "indices": [],
            "error": _redact_error(str(exc), config.get("password")),
        }

    finally:
        if client is not None:
            client.close()
