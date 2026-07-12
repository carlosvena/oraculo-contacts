# Changelog

Los cambios relevantes de ORÁCULO CONTACTS se documentan aquí siguiendo una adaptación de
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado semántico.

## [Unreleased]

Sin cambios todavía.

## [0.5.0] - 2026-07-12

### Added

- Importación local de Google Contacts CSV con encabezados en español e inglés.
- Importación tolerante de vCard 3.0 y 4.0 con advertencias parciales.
- Asistente visual con detección de formato, validación y vista previa enmascarada.
- Búsqueda local por nombre, organización, teléfono y correo; nuevos filtros reales.
- Workspace local opt-in con checksum y omisión de notas.
- Informes de diagnóstico JSON y HTML enmascarados por defecto.
- `VERIFICAR_ORACULO.bat` para diagnóstico de instalación en Windows.

## [0.4.0] - 2026-07-11

### Added

- Aplicación visual local en español basada en Streamlit.
- Dashboard de métricas, explorador con filtros y ficha individual.
- Centro de posibles duplicados con comparación segura.
- Plan de mejora con decisiones guardadas únicamente durante la sesión.
- Demo de 12 contactos ficticios y carga JSON enteramente en memoria.
- Comando `oraculo-contacts ui` e instaladores de doble clic para Windows.

## [0.3.0] - 2026-07-11

### Added

- Propuestas inmutables de normalización de nombres, correos y teléfonos argentinos.
- Clasificación conservadora de móviles, fijos, 0800, 0810 y desconocidos.
- Modelos de hechos, evidencias y procedencia con registro exclusivamente en memoria.
- Motor determinista de recomendaciones y planes de acción no ejecutables.
- Comando `recommend` con salidas de consola y JSON `3.0`.

## [0.2.0] - 2026-07-11

### Added

- Análisis de completitud, consistencia y score de calidad.
- Detección explicable de posibles duplicados por nombre, correo y teléfono.
- Priorización de oportunidades y salidas de consola y JSON `2.0` mediante `analyze`.

## [0.1.0] - 2026-07-11

### Added

- Importación JSON de solo lectura y auditoría inicial.
- Reportes de consola y JSON `1.0` mediante `audit`.
- Arquitectura limpia, CLI, logging y pruebas automatizadas.
