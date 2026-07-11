# Contribuir a ORÁCULO CONTACTS

Toda contribución debe cumplir [ORACULO.md](ORACULO.md). Nunca incluya contactos reales, CSV, VCF,
copias, exportaciones, respaldos, secretos o información privada.

## Flujo

1. Cree una rama desde `main` actualizada.
2. Implemente un cambio acotado respetando arquitectura limpia y compatibilidad.
3. Use datos claramente ficticios y preserve la inmutabilidad de contactos.
4. Ejecute:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov
```

5. Actualice documentación, changelog y registro de decisiones cuando corresponda.
6. Cree commits pequeños y descriptivos y abra un Pull Request. No use force push sobre historial
   compartido.

## Pull Requests

El PR debe explicar qué cambia, por qué, impacto, riesgos y validaciones. Debe confirmar que no ejecuta
recomendaciones ni expone campos protegidos, que los contratos previos siguen compatibles y que la
cobertura no disminuye.

