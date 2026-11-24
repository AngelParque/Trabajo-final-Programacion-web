# Instrucciones para agentes

## Proyecto

Aplicación local para un comedor parroquial. El frontend usa Angular standalone y el backend FastAPI usa SQL Server Express en `localhost\SQLEXPRESS`, base `ComedorParroquial`, por defecto. SQLite en `backend/comedor.db` sigue disponible para desarrollo.

## Estructura

- `backend/main.py`: rutas de API, validación Pydantic y acceso a datos.
- `backend/requirements.txt`: dependencias Python, incluido `pyodbc`.
- `backend/sqlserver_schema.sql`: creación de base y esquema de SQL Server.
- `frontend/src/app/`: componentes, vistas y rutas Angular.
- `frontend/src/styles.css` y `frontend/src/app/app.css`: estilos globales y de la aplicación.
- `frontend/proxy.conf.json`: proxy de `/api` al backend en desarrollo.

## Convenciones

- Mantén la interfaz, los mensajes y los datos de ejemplo en español.
- Conserva la separación: Angular consume la API; FastAPI implementa las reglas de negocio y persistencia.
- Valida entradas en modelos Pydantic y conserva las restricciones de stock no negativo y el historial de movimientos.
- Usa consultas parametrizadas. Respeta las claves foráneas y evita eliminar insumos con movimientos asociados.
- No agregues datos personales reales de beneficiarios. El prototipo no implementa autenticación ni está preparado para producción.
- No borres datos existentes salvo que la tarea lo requiera explícitamente. `POST /api/demo/reset` reinicializa los datos de demostración.
- No edites archivos generados o dependencias instaladas, como `frontend/node_modules/`, `frontend/dist/`, `frontend/.angular/` o `backend/__pycache__/`.
- Mantén los cambios acotados a la tarea y sigue el estilo existente.

## Comandos útiles

Desde `frontend/`: `npm start`, `npm run build`, `npm test`.

Desde `backend/` con su entorno Python activado:

- `pip install -r requirements.txt`
- `uvicorn main:app --reload`

SQL Server debe estar activo. La conexión predeterminada es `localhost\SQLEXPRESS` con autenticación de Windows. El backend crea tablas faltantes y carga datos de ejemplo al iniciar.
