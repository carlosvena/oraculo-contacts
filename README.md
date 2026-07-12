# ORÁCULO CONTACTS

Auditor local de contactos, seguro y estrictamente de solo lectura. Importa una copia JSON,
detecta problemas de calidad y genera reportes en consola o JSON sin modificar, eliminar ni
fusionar contactos.

## Abrir la aplicación visual

En Windows, la forma más simple es:

1. Hacer doble clic en `INSTALAR_ORACULO.bat` una sola vez.
2. Hacer doble clic en `INICIAR_ORACULO.bat` cada vez que quiera usar la aplicación.

También puede iniciarse por consola:

```bash
python -m pip install -e ".[ui]"
oraculo-contacts ui
```

La aplicación abre en el navegador y permite probar 12 contactos ficticios o importar una exportación
de Google Contacts en CSV, vCard 3.0/4.0 o JSON. Incluye resumen visual, explorador, candidatos a
duplicado, plan de mejora e informes JSON/HTML enmascarados. Todo funciona localmente y en modo solo
lectura.

`VERIFICAR_ORACULO.bat` ofrece un diagnóstico rápido en español si necesitás comprobar Python,
instalación, datos de demostración y disponibilidad del puerto local.

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
oraculo-contacts recommend examples/contacts.sample.json
oraculo-contacts recommend examples/contacts.sample.json --format json --output reports/plan.json
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
Las propuestas, evidencia local y planes no ejecutables de v0.3 se documentan en
[docs/safe-improvement-engine.md](docs/safe-improvement-engine.md).
La interfaz visual y sus garantías se describen en [docs/visual-app.md](docs/visual-app.md).
La importación de contactos reales y privacidad local se detallan en
[docs/real-contact-import.md](docs/real-contact-import.md).

## Licencia

MIT. Consulte [LICENSE](LICENSE).
