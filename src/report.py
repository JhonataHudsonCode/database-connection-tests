from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
REPORTS_DIR = ROOT_DIR / "reports"


def generate_report(results: list[dict]) -> str:
    """Gera um relatório HTML standalone com o resultado da execuçãdo."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    environment = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = environment.get_template("report.html")

    total = len(results)
    success = sum(1 for item in results if item["status"] == "OK")
    errors = total - success
    success_rate = round((success / total) * 100, 2) if total else 0

    valid_times = [
        item["time_ms"]
        for item in results
        if item.get("time_ms") is not None
    ]
    average_time = round(sum(valid_times) / len(valid_times), 2) if valid_times else 0

    now = datetime.now()

    html = template.render(
        execution_date=now.strftime("%d/%m/%Y %H:%M:%S"),
        results=results,
        total=total,
        success=success,
        errors=errors,
        success_rate=success_rate,
        average_time=average_time,
    )

    filename = REPORTS_DIR / (
        f"connection_report_{now.strftime('%Y-%m-%d_%H%M%S')}.html"
    )

    filename.write_text(html, encoding="utf-8")
    return str(filename)
