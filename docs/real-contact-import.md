# Importar contactos reales de forma segura

## Exportar desde Google

En Google Contacts use **Exportar** y elija **CSV de Google** o **vCard**. ORÁCULO no requiere acceso a
la cuenta ni credenciales: trabaja exclusivamente con el archivo que usted selecciona.

## Formatos soportados

- JSON de ORÁCULO.
- Google Contacts CSV con encabezados habituales en español o inglés.
- `.vcf` y `.vcard` versiones 3.0 y 4.0 dentro de límites razonables.

Se reconocen nombres, organización, cargo, cumpleaños, notas, etiquetas, teléfonos, correos y
direcciones. Múltiples valores se conservan. Columnas o propiedades desconocidas se informan y las
filas recuperables continúan disponibles.

## Flujo visual

La pantalla inicial ofrece datos de demostración, CSV de Google y VCF. Antes de analizar muestra
nombre, tamaño, formato, válidos, advertencias, rechazos, campos y una vista previa de hasta diez
contactos con teléfonos y correos enmascarados. Cancelar descarta todo el estado de importación.

Después de confirmar, la búsqueda por nombre, organización, teléfono o correo ocurre localmente. Los
filtros incluyen organización, etiqueta, favorito, cumpleaños, calidad y presencia de teléfono,
correo o dirección.

## Sesión y privacidad

Por defecto todo vive en memoria y se descarta al cerrar. “Cerrar sesión y borrar datos temporales”
limpia el estado y cachés de Streamlit sin tocar el archivo fuente.

“Guardar sesión local” requiere ruta y confirmación. La ruta debe estar fuera del repositorio. Se
guarda checksum SHA-256, fecha y una copia local; las notas se omiten porque pueden contener secretos.
No existe nube ni sincronización.

## Informes

Los informes JSON y HTML incluyen diagnóstico, duplicados, inconsistencias, recomendaciones,
advertencias, fecha y versión. Correos, teléfonos, direcciones y notas se enmascaran por defecto. La
opción para incluirlos completos está desactivada y presenta una advertencia visible.

## Límites

- No se interpretan todas las extensiones propietarias de vCard.
- Quoted-printable se conserva como texto y genera advertencia para revisión.
- Los cumpleaños ambiguos o incompletos no se inventan.
- ORÁCULO nunca aplica recomendaciones, fusiona ni elimina contactos.
