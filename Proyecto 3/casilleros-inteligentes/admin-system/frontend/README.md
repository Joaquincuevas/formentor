# Sistema de Administración — Frontend (React + Vite + Axios)

Dashboard web para administradores y superusuario.

## Instalación y ejecución

```bash
cd admin-system/frontend
npm install
npm run dev        # http://localhost:5173
```

El backend debe estar corriendo en `http://localhost:8000` (configurable con la
variable de entorno `VITE_API_URL`).

## Vistas (las que pide el enunciado)

- **Login** con Google (modo dev: ingresa el email). Usuarios demo: `admin` (superusuario)
  y `demo@uandes.cl` (usuario).
- **Dashboard usuario**: aperturas por día (7 días) + 3 métricas (casillero más usado,
  ratio de rechazos, controladores en línea).
- **Dashboard superusuario**: usuarios/controladores/casilleros activos, aperturas 7 días
  y 4 métricas adicionales.
- **Controladores**: índice de controladores y sus casilleros, estado de conexión,
  añadir controlador (sincronización), añadir casillero, y editar clave/dueño
  (selector visual de los 4 gestos).
- **Modelos** (superusuario): CRUD de modelos de gestos.

## Build de producción

```bash
npm run build      # genera dist/
```
