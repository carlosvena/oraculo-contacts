# Constitución de ORÁCULO CONTACTS

## Misión y visión

ORÁCULO CONTACTS ayuda a comprender, preservar y mejorar colecciones de contactos mediante análisis
locales, deterministas y explicables. Su visión es convertirse en una herramienta confiable para el
cuidado a largo plazo del patrimonio digital personal, donde cada cambio permanezca bajo control
humano y pueda justificarse con evidencia.

## Principios inviolables

1. **Preservación antes que automatización.** Un contacto es patrimonio digital. El sistema nunca
   elimina, fusiona, sobrescribe ni modifica automáticamente un contacto o su archivo de origen.
2. **Información protegida.** Favoritos, cumpleaños y notas son campos protegidos. Nunca se cambian
   mediante normalización o recomendación, ni se exponen en logs o reportes salvo que un contrato
   futuro lo autorice de forma explícita, segura y consentida.
3. **Propuestas, no ejecuciones.** Toda mejora es una propuesta inmutable. La aprobación y aplicación
   quedan fuera del alcance hasta que exista un flujo humano explícito y auditable.
4. **Explicabilidad.** Toda detección, propuesta y recomendación incluye motivos, reglas, confianza y
   riesgo suficientes para que una persona pueda evaluarla.
5. **Normalización temporal.** Los valores normalizados solo existen en memoria para comparar o
   proponer. Nunca sustituyen al valor original sin aprobación explícita.
6. **Evidencia antes que suposición.** Los hechos distinguen origen, evidencia, fecha, confianza y
   estado confirmado o inferido. La ausencia de evidencia no se convierte en certeza.
7. **Privacidad local.** No se realizan llamadas externas con datos de contactos. Está prohibido subir
   contactos reales, archivos CSV o VCF, copias, exportaciones, respaldos o información privada al
   repositorio, issues, Pull Requests, fixtures, logs o documentación.

## Ingeniería y compatibilidad

- Los contratos públicos existentes mantienen compatibilidad hacia atrás. Los JSON `1.0` de `audit`
  y `2.0` de `analyze` no se alteran de forma incompatible.
- La arquitectura limpia separa dominio, aplicación, infraestructura y presentación. El dominio no
  depende de archivos, CLI, red ni frameworks.
- Todo código de producción es tipado, documentado, pequeño y orientado a un propósito real.
- Las entidades y resultados del dominio son inmutables siempre que sea razonable.
- Cada cambio funcional incluye pruebas unitarias y, cuando cruza adaptadores, pruebas de integración
  o CLI. Ruff, formato y toda la suite deben aprobarse.
- La cobertura nunca puede ser inferior a la cobertura vigente en `main` al comenzar el cambio. Una
  excepción exige decisión documentada y revisión explícita.
- Los commits son pequeños, descriptivos y de alcance coherente. Todo cambio llega a `main` mediante
  Pull Request revisable; no se reescribe historial compartido ni se usa force push.

## Reglas para Codex y futuros agentes

1. Leer este documento antes de diseñar o modificar el proyecto.
2. Limitarse al repositorio y preservar cambios ajenos del usuario.
3. No inventar permisos, fuentes, datos ni requisitos. Declarar supuestos y detenerse cuando cambien
   el alcance, la privacidad o la seguridad.
4. No implementar eliminación, fusión, sobrescritura o aplicación automática de propuestas.
5. No registrar ni serializar valores protegidos o información personal fuera de una salida pedida
   explícitamente y respaldada por un contrato seguro.
6. Utilizar solamente datos ficticios inequívocos (`example.test`, identificadores opacos y números
   reservados o sintéticos) en pruebas y ejemplos.
7. Verificar inmutabilidad, clasificación telefónica conservadora y compatibilidad de contratos.
8. Ejecutar las comprobaciones de la Definition of Done antes de publicar.
9. Toda exportación corregida debe ser un archivo nuevo con manifiesto; nunca se sobrescribe el origen.
10. Favoritos, cumpleaños, notas, fotografías, identificadores externos y etiquetas sensibles quedan
    bloqueados frente a operaciones masivas.

## Definition of Done

Un cambio está terminado solamente cuando:

- satisface el alcance aceptado sin esqueletos vacíos ni código demostrativo;
- preserva contactos, campos protegidos y archivos de origen;
- toda conclusión relevante tiene motivo, evidencia o regla, confianza y riesgo cuando corresponda;
- Ruff check y Ruff format check son correctos;
- todas las pruebas pasan y la cobertura no retrocede;
- los comandos afectados se prueban con datos ficticios;
- la documentación, arquitectura, changelog y decisiones relevantes están actualizados;
- el árbol de trabajo queda limpio, los commits son revisables y existe un Pull Request;
- no se incluyeron contactos reales, CSV, VCF, copias, secretos ni información privada.
