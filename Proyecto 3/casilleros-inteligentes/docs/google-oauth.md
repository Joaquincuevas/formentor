# Login con Google (OAuth) — configuración

El Sistema de Administración soporta login real con cuentas de Google usando
**Google Identity Services** (el botón oficial de "Iniciar sesión con Google").

- El **frontend** muestra el botón de Google, recibe un `id_token` (un JWT firmado
  por Google) y lo manda al backend.
- El **backend** verifica ese `id_token` contra Google (`google-auth`): comprueba la
  firma, la expiración, el emisor y que el `aud` coincida con **nuestro Client ID**.
  Si es válido, extrae el email y crea/loguea al usuario.

Mientras **no** haya un Client ID configurado, el sistema cae a un **modo de
desarrollo** que acepta el email directo (para poder probar sin montar OAuth).

## Cómo obtener el Client ID (una sola vez)

Esto requiere tu cuenta de Google — hazlo tú en la consola de Google Cloud:

1. Entra a <https://console.cloud.google.com/> y crea un proyecto (o usa uno).
2. **APIs y servicios → Pantalla de consentimiento OAuth**: tipo "Externo", pon un
   nombre de app y tu correo. Agrega tu correo como usuario de prueba.
3. **APIs y servicios → Credenciales → Crear credenciales → ID de cliente de OAuth**.
   - Tipo de aplicación: **Aplicación web**.
   - **Orígenes de JavaScript autorizados**: agrega `http://localhost:5173`
     (y la URL real cuando despliegues).
   - No necesitas "URI de redireccionamiento" para el flujo de Identity Services.
4. Copia el **Client ID** (algo como `123456-abcd.apps.googleusercontent.com`).

## Cómo activarlo

**Backend** — define la variable de entorno antes de levantar Django:

```bash
export GOOGLE_OAUTH_CLIENT_ID="TU_CLIENT_ID.apps.googleusercontent.com"
cd admin-system/backend && source .venv/bin/activate
python manage.py runserver 8090
```

**Frontend** — no requiere cambios: consulta el Client ID desde el backend
(`GET /api/auth/config/`) y muestra el botón de Google automáticamente.

## Cómo verificar

- `curl http://localhost:8090/api/auth/config/` debe devolver tu `google_client_id`
  y `dev_login: false`.
- En <http://localhost:5173> debe aparecer el botón oficial de Google en vez del
  campo de email.

## Notas

- El Client ID es **público** por diseño (va en el HTML del frontend); no es un
  secreto. El *Client Secret* NO se usa en este flujo y no debe subirse al repo.
- El backend guarda `google-auth` en `requirements.txt`.
