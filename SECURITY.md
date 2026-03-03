# Política de Seguridad

## Versiones soportadas

| Versión | Soporte          |
|---------|------------------|
| main    | ✅ Activo        |
| < main  | ❌ Sin soporte   |

## Reportar una vulnerabilidad

**NO abras un issue público** para reportar vulnerabilidades de seguridad.

En su lugar:

1. Envía un correo a los maintainers del proyecto con el asunto
   `[SECURITY] ESPAlert — <descripción breve>`.
2. Incluye:
   - Descripción detallada de la vulnerabilidad.
   - Pasos para reproducirla.
   - Impacto potencial.
   - Posible solución (si la conoces).
3. Recibirás una respuesta en un plazo máximo de **72 horas**.

## Prácticas de seguridad del proyecto

- Las claves API y secretos **nunca** se almacenan en el repositorio.
- Todas las contraseñas se hashean con **bcrypt**.
- Los tokens JWT tienen expiración configurable.
- La API implementa rate limiting con **SlowAPI + Redis**.
- Las cabeceras de seguridad (HSTS, CSP, X-Frame-Options) se configuran
  tanto en el middleware de FastAPI como en Nginx.
- Los datos de usuario cumplen con la **RGPD/LOPDGDD** (endpoints de
  exportación y eliminación de datos).
- Los contenedores Docker ejecutan con usuario **no-root** (`appuser`).

## Divulgación responsable

Seguimos una política de divulgación coordinada. Agradecemos que nos
des tiempo razonable para corregir la vulnerabilidad antes de hacerla
pública.

Todos los reportes de seguridad válidos serán reconocidos en el
archivo CHANGELOG o en los créditos del release correspondiente.
