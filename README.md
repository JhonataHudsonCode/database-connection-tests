# Database Connection Tests

Automação em Python para validar conexões de clientes armazenadas em um
PostgreSQL central.

Fluxo:

1. Conecta no PostgreSQL central.
2. Busca clientes ativos e suas credenciais.
3. Identifica se o destino é PostgreSQL ou OpenSearch.
4. Valida a conexão.
5. Gera relatório HTML standalone em `reports/`.
6. Retorna exit code `1` se existir qualquer falha, facilitando uso em CI/CD.

## Requisitos

- Python 3.10+
- Acesso de rede ao PostgreSQL central
- Acesso de rede aos PostgreSQL/OpenSearch dos clientes

## Instalação

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuração

Edite o `.env` na raiz do projeto.

Nunca commite credenciais reais. O arquivo `.env` já está no `.gitignore`.

## Estrutura esperada no PostgreSQL central

Por padrão, `src/central_database.py` espera uma tabela parecida com:

```sql
CREATE TABLE clientes_bancos (
    id BIGSERIAL PRIMARY KEY,
    cliente_nome VARCHAR(255) NOT NULL,
    db_type VARCHAR(50) NOT NULL,
    db_host VARCHAR(255) NOT NULL,
    db_port INTEGER NOT NULL,
    db_name VARCHAR(255),
    db_user VARCHAR(255) NOT NULL,
    db_password VARCHAR(255) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE
);
```

Valores esperados em `db_type`:

- `postgres` ou `postgresql`
- `opensearch`

Se a sua tabela real possuir outros nomes de colunas, ajuste somente o SELECT
e o mapeamento em `src/central_database.py`.

## Executar e gerar relatório HTML

```bash
python -m src.main
```

O resultado será salvo, por exemplo, como:

```text
reports/connection_report_2026-08-18_161500.html
```

Exit codes:

- `0`: todas as conexões passaram.
- `1`: pelo menos uma conexão de cliente falhou.
- `2`: falha ao consultar o banco PostgreSQL central.

## Executar com Pytest

```bash
pytest
```

O Pytest primeiro valida o PostgreSQL central e depois executa um subteste para
cada cliente. Uma falha em um cliente não interrompe os demais.

## Como cada conexão é validada

### PostgreSQL

A automação abre a conexão e executa:

```sql
SELECT 1;
```

### OpenSearch

A automação executa `client.info()` para confirmar serviço e autenticação.
Depois tenta consultar `_cluster/health`.

Se o usuário não possuir permissão para `_cluster/health`, mas `client.info()`
funcionar, a conexão ainda é considerada válida.

## Segurança

- Senhas não são incluídas no relatório.
- As funções tentam mascarar a senha caso ela apareça em uma exceção.
- Não compartilhe `.env` com credenciais reais.
- Em produção, prefira Secret Manager/Vault em vez de senha em texto puro.
