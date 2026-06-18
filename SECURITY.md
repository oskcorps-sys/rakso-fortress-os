# Políticas de Seguridad de RAKSO Fortress OS

## Filosofía
En RAKSO, la seguridad y la integridad del Kernel son nuestra máxima prioridad. Cualquier código que vulnere nuestra arquitectura será tratado como un incidente crítico (Nivel de Alerta Fénix). Seguimos rigurosamente la gobernanza de SDD+.

## Versiones Soportadas
Actualmente solo proporcionamos parches de seguridad para las siguientes versiones de la rama principal:

| Versión | Estado de Soporte |
| ------- | ----------------- |
| > 1.0.x | :white_check_mark: Soportada |
| < 1.0   | :x: Obsoleta (Ramas Legacy/Comprometidas) |

## Reporte de Vulnerabilidades
Si crees haber encontrado una vulnerabilidad, por favor **NO la hagas pública** creando un issue en GitHub. 

Envía un reporte detallado cifrado por GPG a nuestro equipo de seguridad:
`security@oskcorps-sys.local`

Fingerprint GPG:
`XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX`

### Tiempo de Respuesta
- Acuse de recibo: 24 horas.
- Triaje inicial y parche en rama oculta: 72 horas.
- Despliegue de actualización y divulgación pública: 7 días.

## Reglas Inquebrantables de Desarrollo
Todos los contribuidores deben apegarse a nuestro `SECURITY_CONTRACT.yaml` o sus Pull Requests serán cerrados de forma automatizada por nuestros agentes de seguridad (SAST). 
- Queda **estrictamente prohibido** instalar binarios con `chmod u+s`.
- Queda **estrictamente prohibida** la descarga de dependencias externas sin validación de integridad (`SHA-256`).
