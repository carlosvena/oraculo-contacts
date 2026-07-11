# Formato JSON de entrada

La raíz puede ser una lista de contactos o un objeto con la clave `contacts`. Cada contacto admite:

```json
{
  "id": "c-001",
  "display_name": "Ada Lovelace",
  "given_name": "Ada",
  "family_name": "Lovelace",
  "emails": ["ada@example.test"],
  "phones": ["+54 11 5555 0101"],
  "favorite": true,
  "birthday": "1815-12-10",
  "notes": "Dato protegido"
}
```

Los campos desconocidos se ignoran. `emails` y `phones` deben ser listas de cadenas; `birthday` usa
ISO `AAAA-MM-DD`; `favorite` es booleano. Los datos protegidos se cargan para preservación semántica,
pero jamás se muestran en hallazgos.

