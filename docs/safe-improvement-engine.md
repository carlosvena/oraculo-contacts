# Motor de mejora segura v0.3

## Propuestas de normalización

Los normalizadores devuelven `NormalizationProposal`, nunca un `Contact`. Cada propuesta conserva el
valor original y sugerido, motivo, confianza, riesgo y reglas. Nombres reciben colapso de espacios y
capitalización conservadora; correos reciben NFKC, recorte exterior y dominio en minúsculas solo si la
sintaxis básica es válida.

Los teléfonos se interpretan de forma conservadora para Argentina. `0800` y `0810` se conservan como
líneas de servicio, el marcador nacional móvil `9` es obligatorio para clasificar celular, los números
nacionales plausibles sin ese marcador se tratan como fijos y el resto como desconocido. No se
inventan dígitos, áreas ni tipos. Favoritos, cumpleaños y notas no entran al normalizador.

## Evidencia y procedencia

`KnowledgeRegistry` mantiene hechos y evidencias durante la ejecución. Un hecho no puede registrarse
si falta su evidencia y distingue `confirmed` de `inferred`. Cada procedencia conserva fuente, fecha
UTC y método. No existe persistencia implícita, IA generativa ni comunicación externa.

## Recomendaciones

El motor reutiliza el análisis de calidad y las propuestas existentes. La prioridad se calcula como:

```text
beneficio × confianza × penalización_de_riesgo × penalización_de_esfuerzo
```

El resultado resume problemas, oportunidades, minutos estimados, riesgo, explicación y nombres de
campos protegidos presentes. Mostrar el nombre de un campo protegido no expone su valor. El JSON `3.0`
puede incluir valores originales y propuestos no protegidos porque es un reporte explícito solicitado
por el usuario. Ninguna salida ejecuta recomendaciones ni modifica el archivo importado.

## Límites

Las reglas son heurísticas deterministas, no verificaciones de identidad. La clasificación telefónica
no cubre toda la numeración argentina y los scores requieren calibración con datos sintéticos más
amplios. Toda propuesta y candidato requiere revisión humana.

