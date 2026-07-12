# Arquitectura del Sprint 1

ORÁCULO CONTACTS aplica una variante pragmática de arquitectura limpia:

- `domain`: entidades inmutables, hallazgos y reglas puras de auditoría.
- `application`: orquestación del caso de uso y puertos de entrada/salida.
- `infrastructure`: lectura JSON y escritura explícita de reportes.
- `presentation`: CLI y renderizado de consola.

Las dependencias apuntan hacia el dominio. El auditor no conoce archivos, JSON ni terminales. El
importador devuelve tuplas inmutables y abre el origen con `"r"`. La única escritura habilitada es
la de un reporte nuevo solicitado mediante `--output`; nunca se escribe en la ruta de entrada.

## Reglas del auditor

El Sprint 1 detecta nombres vacíos, teléfonos y correos inválidos, contactos sin vías de contacto y
posibles duplicados por correo o teléfono normalizados. Un duplicado es una advertencia para revisión
humana, no una orden de fusión.

## Evolución prevista

Los puertos permiten incorporar importadores adicionales, políticas configurables y nuevas salidas
sin acoplar el dominio. Cualquier integración futura debe mantener la frontera de solo lectura y el
tratamiento protegido de favoritos, cumpleaños y notas.

## Sprint 2: análisis de calidad

`AnalyzeContactQuality` usa el mismo puerto de importación de solo lectura. El dominio produce un
`QualityReport` inmutable con evaluaciones por contacto, candidatos a duplicado y oportunidades
priorizadas. La normalización es una función pura: crea representaciones temporales únicamente para
comparar y no forma parte del modelo persistente ni de los reportes.

El comando `audit` y su contrato JSON `1.0` permanecen sin cambios. El nuevo comando `analyze`
publica un contrato JSON `2.0`, lo que mantiene compatibilidad con consumidores del Sprint 1.

## Versión 0.3: motor de mejora segura

El dominio agrega tres capacidades independientes y componibles:

- `proposals` produce propuestas inmutables con valor original, valor sugerido, reglas, confianza y
  riesgo. Nunca recibe funciones de escritura ni opera sobre campos protegidos.
- `knowledge` representa hechos, evidencias y procedencia en un registro en memoria. No posee
  adaptador de persistencia ni llamadas externas.
- `recommendations` reutiliza `analyze_quality` y las propuestas para crear un `ActionPlan` ordenado.
  El plan no ofrece métodos de ejecución o aplicación.

`RecommendContactImprovements` orquesta el caso de uso y los adaptadores de presentación publican el
contrato JSON `3.0` o consola. Los contratos JSON `1.0` y `2.0` no fueron modificados.


