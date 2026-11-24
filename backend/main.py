from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3

import pyodbc
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_BACKEND = os.getenv("COMEDOR_DB_BACKEND", "sqlserver").strip().lower()
DB_PATH = Path(__file__).with_name("comedor.db")
SQLSERVER_CONNECTION = os.getenv(
    "COMEDOR_SQLSERVER_CONNECTION",
    "DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=.\SQLEXPRESS;DATABASE=ComedorParroquial;"
    "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;",
)


class QueryResult:
    def __init__(self, cursor):
        self.cursor = cursor

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def lastrowid(self):
        return getattr(self.cursor, "lastrowid", None)

    def _as_dict(self, row):
        if row is None:
            return None
        columns = [column[0] for column in self.cursor.description]
        return dict(zip(columns, row))

    def fetchone(self):
        return self._as_dict(self.cursor.fetchone())

    def fetchall(self):
        return [self._as_dict(row) for row in self.cursor.fetchall()]


class DatabaseSession:
    def __init__(self):
        self.is_sqlite = DB_BACKEND == "sqlite"
        if self.is_sqlite:
            self.connection = sqlite3.connect(DB_PATH)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
        elif DB_BACKEND == "sqlserver":
            self.connection = pyodbc.connect(SQLSERVER_CONNECTION, timeout=5)
        else:
            raise RuntimeError("COMEDOR_DB_BACKEND debe ser 'sqlserver' o 'sqlite'.")

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        try:
            if exception_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
        finally:
            self.connection.close()

    def execute(self, sql, args=()):
        cursor = self.connection.cursor()
        cursor.execute(sql, args)
        return QueryResult(cursor)

    def executemany(self, sql, args):
        cursor = self.connection.cursor()
        cursor.executemany(sql, args)
        return QueryResult(cursor)


def connect():
    return DatabaseSession()


def init_db():
    with connect() as db:
        if db.is_sqlite:
            db.connection.executescript("""
            CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
                unit TEXT NOT NULL, stock REAL NOT NULL CHECK(stock >= 0),
                minimum REAL NOT NULL CHECK(minimum >= 0));
            CREATE TABLE IF NOT EXISTS activities(
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, date TEXT NOT NULL DEFAULT '',
                owner TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Pendiente');
            CREATE TABLE IF NOT EXISTS movements(
                id INTEGER PRIMARY KEY,
                item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
                item_name TEXT NOT NULL, kind TEXT NOT NULL,
                quantity REAL NOT NULL CHECK(quantity > 0), reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL);
            """)
        else:
            db.execute("""
                IF OBJECT_ID(N'dbo.items', N'U') IS NULL
                CREATE TABLE dbo.items (
                    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                    name NVARCHAR(60) NOT NULL,
                    category NVARCHAR(40) NOT NULL,
                    unit NVARCHAR(20) NOT NULL,
                    stock DECIMAL(12,2) NOT NULL CHECK (stock >= 0),
                    minimum DECIMAL(12,2) NOT NULL CHECK (minimum >= 0));
            """)
            db.execute("""
                IF OBJECT_ID(N'dbo.activities', N'U') IS NULL
                CREATE TABLE dbo.activities (
                    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                    name NVARCHAR(80) NOT NULL,
                    [date] NVARCHAR(10) NOT NULL DEFAULT N'',
                    owner NVARCHAR(60) NOT NULL DEFAULT N'',
                    status NVARCHAR(20) NOT NULL DEFAULT N'Pendiente',
                    CHECK (status IN (N'Pendiente', N'En curso', N'Completada')));
            """)
            db.execute("""
                IF OBJECT_ID(N'dbo.movements', N'U') IS NULL
                CREATE TABLE dbo.movements (
                    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                    item_id INT NOT NULL REFERENCES dbo.items(id),
                    item_name NVARCHAR(60) NOT NULL,
                    kind NVARCHAR(10) NOT NULL CHECK (kind IN (N'Entrada', N'Salida')),
                    quantity DECIMAL(12,2) NOT NULL CHECK (quantity > 0),
                    reason NVARCHAR(100) NOT NULL DEFAULT N'',
                    created_at DATETIMEOFFSET(0) NOT NULL);
            """)

        if db.execute("SELECT COUNT(*) AS count FROM items").fetchone()["count"] == 0:
            db.executemany(
                "INSERT INTO items(name,category,unit,stock,minimum) VALUES(?,?,?,?,?)",
                [("Arroz", "Abarrotes", "kg", 12, 5),
                 ("Lentejas", "Abarrotes", "kg", 3, 4),
                 ("Aceite", "Abarrotes", "L", 6, 2),
                 ("Fideos", "Abarrotes", "kg", 8, 3),
                 ("Atún", "Conservas", "latas", 18, 6)],
            )
        if db.execute("SELECT COUNT(*) AS count FROM activities").fetchone()["count"] == 0:
            db.execute(
                "INSERT INTO activities(name,date,owner,status) VALUES(?,?,?,?)",
                ("Organizar menú semanal", "", "Coordinación", "Pendiente"),
            )


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="API del Comedor Parroquial", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


class ItemIn(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    category: str = Field(min_length=2, max_length=40)
    unit: str = Field(min_length=1, max_length=20)
    stock: float = Field(ge=0, le=1000000)
    minimum: float = Field(ge=0, le=1000000)


class ActivityIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    date: str = Field(default="", max_length=10)
    owner: str = Field(default="", max_length=60)
    status: str = Field(default="Pendiente", pattern="^(Pendiente|En curso|Completada)$")


class MoveIn(BaseModel):
    item_id: int = Field(gt=0)
    kind: str = Field(pattern="^(Entrada|Salida)$")
    quantity: float = Field(gt=0, le=1000000)
    reason: str = Field(default="", max_length=100)


def rows(sql, args=()):
    with connect() as db:
        return db.execute(sql, args).fetchall()


def insert_and_get(db, table, columns, values):
    column_list = ",".join(columns)
    placeholders = ",".join("?" for _ in values)
    if db.is_sqlite:
        result = db.execute(
            f"INSERT INTO {table}({column_list}) VALUES({placeholders})", values
        )
        return db.execute(
            f"SELECT * FROM {table} WHERE id=?", (result.lastrowid,)
        ).fetchone()
    if table == "movements":
        result = db.execute(
            f"INSERT INTO {table}({column_list}) OUTPUT INSERTED.id VALUES({placeholders})",
            values,
        )
        inserted_id = result.fetchone()["id"]
        return db.execute(
            """SELECT id, item_id, item_name, kind, quantity, reason,
                      CONVERT(NVARCHAR(40), created_at, 127) AS created_at
               FROM movements WHERE id=?""",
            (inserted_id,),
        ).fetchone()
    return db.execute(
        f"INSERT INTO {table}({column_list}) OUTPUT INSERTED.* VALUES({placeholders})",
        values,
    ).fetchone()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Comedor Parroquial", "database": DB_BACKEND}


@app.get("/api/items")
def list_items():
    return rows("SELECT * FROM items ORDER BY name")


@app.post("/api/items", status_code=201)
def create_item(data: ItemIn):
    with connect() as db:
        return insert_and_get(db, "items", list(data.model_dump()), tuple(data.model_dump().values()))


@app.put("/api/items/{item_id}")
def update_item(item_id: int, data: ItemIn):
    with connect() as db:
        cur = db.execute(
            "UPDATE items SET name=?,category=?,unit=?,stock=?,minimum=? WHERE id=?",
            (*data.model_dump().values(), item_id),
        )
        if not cur.rowcount:
            raise HTTPException(404, "Insumo no encontrado")
        return db.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()


@app.delete("/api/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    with connect() as db:
        try:
            cur = db.execute("DELETE FROM items WHERE id=?", (item_id,))
        except (sqlite3.IntegrityError, pyodbc.IntegrityError):
            raise HTTPException(409, "El insumo tiene movimientos registrados; consérvalo para mantener el historial")
        if not cur.rowcount:
            raise HTTPException(404, "Insumo no encontrado")


@app.get("/api/activities")
def list_activities():
    return rows("SELECT * FROM activities ORDER BY id DESC")


@app.post("/api/activities", status_code=201)
def create_activity(data: ActivityIn):
    with connect() as db:
        return insert_and_get(db, "activities", list(data.model_dump()), tuple(data.model_dump().values()))


@app.put("/api/activities/{activity_id}")
def update_activity(activity_id: int, data: ActivityIn):
    with connect() as db:
        cur = db.execute(
            "UPDATE activities SET name=?,date=?,owner=?,status=? WHERE id=?",
            (*data.model_dump().values(), activity_id),
        )
        if not cur.rowcount:
            raise HTTPException(404, "Actividad no encontrada")
        return db.execute("SELECT * FROM activities WHERE id=?", (activity_id,)).fetchone()


@app.delete("/api/activities/{activity_id}", status_code=204)
def delete_activity(activity_id: int):
    with connect() as db:
        cur = db.execute("DELETE FROM activities WHERE id=?", (activity_id,))
        if not cur.rowcount:
            raise HTTPException(404, "Actividad no encontrada")


@app.get("/api/movements")
def list_movements():
    if DB_BACKEND == "sqlite":
        return rows("SELECT * FROM movements ORDER BY id DESC LIMIT 200")
    return rows("""SELECT TOP 200 id, item_id, item_name, kind, quantity, reason,
                       CONVERT(NVARCHAR(40), created_at, 127) AS created_at
                FROM movements ORDER BY id DESC""")


@app.post("/api/movements", status_code=201)
def create_movement(data: MoveIn):
    with connect() as db:
        item = db.execute("SELECT * FROM items WHERE id=?", (data.item_id,)).fetchone()
        if not item:
            raise HTTPException(404, "Insumo no encontrado")
        current_stock = float(item["stock"])
        new_stock = current_stock + data.quantity if data.kind == "Entrada" else current_stock - data.quantity
        if new_stock < 0:
            raise HTTPException(409, "La salida supera el stock disponible")
        db.execute("UPDATE items SET stock=? WHERE id=?", (round(new_stock, 2), data.item_id))
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return insert_and_get(
            db,
            "movements",
            ["item_id", "item_name", "kind", "quantity", "reason", "created_at"],
            (data.item_id, item["name"], data.kind, data.quantity, data.reason, stamp),
        )


@app.post("/api/demo/reset")
def reset_demo():
    with connect() as db:
        db.execute("DELETE FROM movements")
        db.execute("DELETE FROM activities")
        db.execute("DELETE FROM items")
        db.executemany(
            "INSERT INTO items(name,category,unit,stock,minimum) VALUES(?,?,?,?,?)",
            [("Arroz", "Abarrotes", "kg", 12, 5),
             ("Lentejas", "Abarrotes", "kg", 3, 4),
             ("Aceite", "Abarrotes", "L", 6, 2),
             ("Fideos", "Abarrotes", "kg", 8, 3),
             ("Atún", "Conservas", "latas", 18, 6)],
        )
        db.execute(
            "INSERT INTO activities(name,date,owner,status) VALUES(?,?,?,?)",
            ("Organizar menú semanal", "", "Coordinación", "Pendiente"),
        )
    return {"status": "reset"}



