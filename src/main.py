from src.central_database import get_clients
from src.connection_service import test_connection
from src.report import generate_report


def main() -> int:
    print("Buscando clientes no PostgreSQL central...")

    try:
        clients = get_clients()
    except Exception as exc:
        # Não imprime credenciais. O erro normalmente contém apenas host/porta/db.
        print(f"ERRO ao consultar o banco central: {exc}")
        return 2

    print(f"{len(clients)} cliente(s) encontrado(s).")

    results = []

    for client in clients:
        print(
            f"Testando {client['name']} "
            f"({client['db_type']} @ {client['host']}:{client['port']})..."
        )

        result = test_connection(client)

        results.append(
            {
                "client_id": client["id"],
                "client_name": client["name"],
                "db_type": client["db_type"],
                "host": client["host"],
                "port": client["port"],
                "status": result["status"],
                "time_ms": result["time_ms"],
                "response": result["response"],
                "error": result["error"],
            }
        )

    report_path = generate_report(results)

    total = len(results)
    success = sum(1 for item in results if item["status"] == "OK")
    errors = total - success

    print()
    print("=" * 50)
    print("RESULTADO")
    print("=" * 50)
    print(f"Total:   {total}")
    print(f"Sucesso: {success}")
    print(f"Falhas:  {errors}")
    print(f"Relatório: {report_path}")

    # Bom para CI/CD:
    # 0 = todas as conexões OK
    # 1 = uma ou mais conexões falharam
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
