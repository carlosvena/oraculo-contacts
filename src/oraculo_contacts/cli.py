"""Punto de entrada de la interfaz de línea de comandos."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from oraculo_contacts.application.use_cases import AuditContacts
from oraculo_contacts.exceptions import OraculoError
from oraculo_contacts.infrastructure.json_importer import JsonContactImporter
from oraculo_contacts.infrastructure.json_reporter import render_json, write_json_report
from oraculo_contacts.logging_config import configure_logging
from oraculo_contacts.presentation.console_reporter import render_console

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Construir el contrato público de argumentos de la CLI."""
    parser = argparse.ArgumentParser(
        prog="oraculo-contacts",
        description="Audita copias JSON de contactos sin modificar ni fusionar datos.",
    )
    parser.add_argument("--verbose", action="store_true", help="Activa logs operativos detallados.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="Audita un archivo JSON en modo solo lectura.")
    audit.add_argument("source", type=Path, help="Ruta del archivo JSON de contactos.")
    audit.add_argument(
        "--format",
        choices=("console", "json"),
        default="console",
        help="Formato del reporte enviado a stdout (predeterminado: console).",
    )
    audit.add_argument(
        "--output",
        type=Path,
        help="Escribe un reporte JSON en esta ruta; nunca puede ser la ruta de entrada.",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Ejecutar la CLI y devolver un código de salida estable."""
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    try:
        if args.command == "audit":
            LOGGER.info("Iniciando auditoría desde una fuente JSON.")
            report = AuditContacts(JsonContactImporter()).execute(args.source)
            if args.output is not None:
                write_json_report(report, args.output, args.source)
                LOGGER.info("Reporte JSON escrito correctamente.")
            output = render_json(report) if args.format == "json" else render_console(report)
            sys.stdout.write(output)
            LOGGER.info(
                "Auditoría finalizada: %d contactos, %d hallazgos.",
                report.contacts_scanned,
                len(report.findings),
            )
            return 0
    except OraculoError as error:
        LOGGER.error("%s", error)
        return 2
    except Exception:
        LOGGER.exception("Fallo inesperado durante la auditoría.")
        return 1
    return 1


def main() -> None:
    """Ejecutar como comando instalado."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
