# ORÁCULO CONTACTS

Auditor local de contactos, seguro y estrictamente de solo lectura. Importa una copia JSON,
detecta problemas de calidad y genera reportes en consola o JSON sin modificar, eliminar ni
fusionar contactos.

## Principios de seguridad

- El archivo de origen se abre exclusivamente en modo lectura.
- Ningún caso de uso expone operaciones de escritura sobre contactos.
- No existen fusiones automáticas: los posibles duplicados son solo hallazgos.
- Favoritos, cumpleaños y notas se preservan como datos protegidos y nunca se incluyen en los
  detalles de los reportes.
- Los reportes identifican registros por un ID opaco o su posición, no vuelcan datos sensibles.

## Requisitos e instalación

Python 3.11 o posterior.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Uso

```bash
oraculo-contacts audit examples/contacts.sample.json
oraculo-contacts audit examples/contacts.sample.json --format json
oraculo-contacts audit examples/contacts.sample.json --format json --output reports/audit.json
oraculo-contacts --verbose audit examples/contacts.sample.json
oraculo-contacts analyze examples/contacts.sample.json
oraculo-contacts analyze examples/contacts.sample.json --format json --output reports/quality.json
```

El formato de entrada se documenta en [docs/json-format.md](docs/json-format.md). Los códigos de
salida son `0` para una auditoría ejecutada correctamente, `2` para entradas o argumentos inválidos
y `1` para fallos inesperados.

## Desarrollo

```bash
ruff check .
ruff format --check .
pytest --cov
```

La arquitectura separa dominio, casos de uso, adaptadores de infraestructura y presentación CLI.
Las decisiones y límites están en [docs/architecture.md](docs/architecture.md). El análisis avanzado,
su score y sus niveles de confianza se describen en
[docs/quality-analysis.md](docs/quality-analysis.md).

## Licencia

MIT. Consulte [LICENSE](LICENSE).
