# Registro de decisiones

## D-001 — Operaciones exclusivamente no destructivas

- **Fecha:** 2026-07-11
- **Estado:** aceptada
- **Decisión:** importar en modo lectura y producir hallazgos o propuestas inmutables. No implementar
  eliminación, fusión, sobrescritura ni aplicación automática.
- **Motivo:** los contactos son patrimonio digital y un falso positivo puede causar pérdida
  irreversible.

## D-002 — Contratos JSON versionados

- **Fecha:** 2026-07-11
- **Estado:** aceptada
- **Decisión:** mantener `audit` en JSON `1.0` y `analyze` en JSON `2.0`; las capacidades nuevas usan
  contratos independientes.
- **Motivo:** permitir evolución sin romper automatizaciones existentes.

## D-003 — Normalización efímera y explicable

- **Fecha:** 2026-07-11
- **Estado:** aceptada
- **Decisión:** normalizar solo en memoria para comparación o propuesta y conservar siempre el valor
  original, reglas, confianza y riesgo.
- **Motivo:** distinguir análisis reversible de modificación de datos.

## D-004 — Conocimiento local en memoria

- **Fecha:** 2026-07-11
- **Estado:** aceptada
- **Decisión:** los hechos y evidencias iniciales serán deterministas, locales y no persistentes salvo
  reportes solicitados explícitamente. No usar IA generativa ni servicios externos.
- **Motivo:** reducir exposición de información sensible y mantener resultados reproducibles.

