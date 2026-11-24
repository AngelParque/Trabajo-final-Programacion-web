# Comedor organizado — prototipo funcional

Prototipo académico para el Comedor Parroquial Nuestra Señora de la Merced. La interfaz Angular consume una API FastAPI que guarda los datos en SQL Server Express.

## Requisitos

- Node.js 20.19+ o 22.12+ y npm.
- Bootstrap 5.3.9 se carga desde CDN.
- Python 3.10 o superior.
- SQL Server Express en ejecución y Microsoft ODBC Driver 18 for SQL Server.

## Iniciar en Windows (PowerShell)

Desde la carpeta del proyecto, abre dos terminales.

Terminal 1, API:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

La conexión predeterminada usa autenticación de Windows contra `localhost\SQLEXPRESS`, base `ComedorParroquial`. Ejecuta `backend/sqlserver_schema.sql` en SSMS si la base todavía no existe. Al iniciar, el backend crea las tablas que falten y carga datos ficticios si las tablas están vacías.

Terminal 2, Angular:

```powershell
cd frontend
npm install
npm start
```

Abre <http://localhost:4200>. La documentación interactiva de la API está en <http://127.0.0.1:8000/docs>.

## Funcionalidades

- Resumen de insumos y alertas de stock bajo.
- Crear, editar, buscar y eliminar productos.
- Registrar entradas y salidas; el servidor impide que una salida deje stock negativo.
- Crear, editar y eliminar actividades con fecha, responsable y estado.
- Historial de hasta 200 movimientos.
- Restablecimiento de datos ficticios para volver al estado inicial de la demo.

## Estructura

- `frontend/src/`: aplicación Angular standalone y estilos adaptables a móvil.
- Bootstrap 5.3.9: estilos y bundle JavaScript incluidos desde jsDelivr en `src/index.html`; detalles propios en `src/app/app.css`.
- `backend/main.py`: API REST, validación, persistencia y datos iniciales.
- `backend/sqlserver_schema.sql`: creación de la base y esquema de SQL Server.
- `backend/comedor.db`: alternativa SQLite, activable con `COMEDOR_DB_BACKEND=sqlite`.
- `frontend/proxy.conf.json`: reenvía `/api` al servidor local durante desarrollo.

## Configuración y cuidado de datos

- El backend usa SQL Server por defecto. `COMEDOR_SQLSERVER_CONNECTION` permite especificar otra cadena ODBC.
- Para usar SQLite en desarrollo, establece `$env:COMEDOR_DB_BACKEND='sqlite'` antes de iniciar Uvicorn.
- Los datos iniciales son ficticios. El prototipo no implementa autenticación, copias de seguridad ni despliegue productivo; no ingreses datos personales de beneficiarios.

## Licencias y originalidad

La aplicación y el código de este prototipo se elaboraron para el proyecto académico. Angular, FastAPI y pyodbc son dependencias de terceros bajo sus licencias respectivas.


