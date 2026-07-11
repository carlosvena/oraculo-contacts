# Análisis de calidad

El comando `analyze` evalúa una copia JSON de forma local y no destructiva. Todos los resultados son
recomendaciones para revisión humana: el sistema no modifica, elimina ni fusiona contactos.

## Score y completitud

La completitud asigna hasta 100 puntos: nombre utilizable (35), al menos una vía de contacto (40),
cumpleaños presente (15) y notas presentes (10). La presencia se considera sin publicar el contenido
protegido. El score resta penalizaciones por inconsistencias: error 18, advertencia 10 e informativo 4,
con límites de 0 a 100. El score general es el promedio redondeado; una colección vacía devuelve 100
como valor neutral, no como afirmación de calidad de datos.

## Posibles duplicados

Se comparan pares por:

- correo idéntico después de recortar espacios y normalizar mayúsculas;
- teléfono idéntico después de conservar solo dígitos y retirar el prefijo argentino;
- similitud de nombre sin diacríticos, espacios redundantes ni puntuación.

La evidencia por nombre solamente requiere al menos 90% de similitud. Cada candidato contiene los
campos que coincidieron, motivos legibles, confianza entre 0 y 1, severidad y la recomendación expresa
de revisar sin fusionar automáticamente. Los valores normalizados nunca se guardan ni se muestran.

## Teléfonos

La clasificación es deliberadamente conservadora. Los prefijos `0800` y `0810` se clasifican como
líneas de servicio; los números nacionales sin marcador móvil explícito se consideran fijos o
desconocidos. Ninguno se etiqueta como celular. Esta clasificación no cambia el número original.

## Inconsistencias y prioridades

Se detectan nombres visibles incompatibles con sus componentes, correos o teléfonos repetidos dentro
del mismo contacto y formatos inválidos. Las oportunidades se ordenan primero por severidad y luego
de manera determinista por referencia. Favoritos, cumpleaños y notas nunca se vuelcan en las salidas.

