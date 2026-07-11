# Aplicación visual local

ORÁCULO CONTACTS 0.4 ofrece una interfaz en español que se ejecuta en la computadora y se abre en el
navegador. No requiere administrador, cuenta, nube ni base de datos.

## Instalación en Windows

Haga doble clic en `INSTALAR_ORACULO.bat`. El instalador crea `.venv` dentro del proyecto e instala el
paquete con Streamlit. Es seguro repetirlo: reutiliza el entorno y actualiza lo necesario.

Si Python no está disponible, muestra un mensaje claro. Requiere Python 3.11 o posterior y conexión a
Internet durante la instalación.

## Inicio con doble clic

Haga doble clic en `INICIAR_ORACULO.bat`. Se abre la aplicación en el navegador. Mantenga la ventana
de consola abierta mientras usa ORÁCULO; cerrarla detiene el servidor local.

## Inicio por consola

```powershell
.\.venv\Scripts\activate
oraculo-contacts ui
```

Streamlit utiliza normalmente `http://localhost:8501`. Ningún dato sale de la computadora por una
función de ORÁCULO.

## Datos de demostración

La opción predeterminada carga 12 contactos ficticios con casos completos e incompletos, nombres
similares, correos y teléfonos duplicados, favoritos, cumpleaños, notas, direcciones, 0800, 0810,
líneas fijas y celulares argentinos. Los dominios usan `example.test`.

## Cargar un JSON

En la barra lateral seleccione “Cargar archivo JSON” y elija el archivo. La interfaz valida UTF-8 y el
esquema; los errores aparecen en español. El contenido se mantiene en memoria: ORÁCULO no escribe,
renombra ni modifica el archivo.

## Pantallas

- **Resumen:** once tarjetas con volumen, campos presentes, calidad, duplicados e inconsistencias.
- **Contactos:** buscador, filtros, tabla enmascarada y ficha individual. Las notas completas están
  cerradas por defecto dentro de un desplegable protegido.
- **Posibles duplicados:** confianza, motivos, campos coincidentes y comparación lado a lado. Nunca
  ofrece una acción de fusión.
- **Plan de mejora:** recomendaciones priorizadas y estado de revisión. Las selecciones se guardan
  solo durante la sesión y no ejecutan cambios.

## Garantías y límites

- Modo exclusivamente de solo lectura.
- Correos y teléfonos aparecen parcialmente ocultos en vistas generales.
- Favoritos, cumpleaños y notas se muestran únicamente en la ficha individual; las notas están
  ocultas hasta abrir su desplegable.
- Las heurísticas pueden producir falsos positivos y siempre requieren revisión humana.
- No hay autenticación, nube, base de datos, sincronización, APIs externas ni aplicación de cambios.
