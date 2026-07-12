# Exportación segura

ORÁCULO genera archivos nuevos JSON, CSV compatible con Google Contacts o vCard 4.0. Conserva datos
no modificados y aplica únicamente propuestas aprobadas a una copia en memoria. Nunca sobrescribe un
archivo existente.

Cada exportación crea un manifiesto JSON con nombre y checksum del origen, nombre y checksum de la
salida, decisiones, campos protegidos, versión, fecha y advertencias.

