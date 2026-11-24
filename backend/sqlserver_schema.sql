/* Esquema inicial para Microsoft SQL Server.
   Ejecutar completo en SQL Server Management Studio o sqlcmd con permisos para crear bases de datos. */
IF DB_ID(N'ComedorParroquial') IS NULL
BEGIN
    CREATE DATABASE [ComedorParroquial];
END;
GO

USE [ComedorParroquial];
GO

IF OBJECT_ID(N'dbo.items', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.items (
        id       INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_items PRIMARY KEY,
        name     NVARCHAR(60) NOT NULL,
        category NVARCHAR(40) NOT NULL,
        unit     NVARCHAR(20) NOT NULL,
        stock    DECIMAL(12,2) NOT NULL,
        minimum  DECIMAL(12,2) NOT NULL,
        CONSTRAINT CK_items_stock_nonnegative CHECK (stock >= 0),
        CONSTRAINT CK_items_minimum_nonnegative CHECK (minimum >= 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.activities', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.activities (
        id     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_activities PRIMARY KEY,
        name   NVARCHAR(80) NOT NULL,
        [date] NVARCHAR(10) NOT NULL CONSTRAINT DF_activities_date DEFAULT N'',
        owner  NVARCHAR(60) NOT NULL CONSTRAINT DF_activities_owner DEFAULT N'',
        status NVARCHAR(20) NOT NULL CONSTRAINT DF_activities_status DEFAULT N'Pendiente',
        CONSTRAINT CK_activities_status CHECK (status IN (N'Pendiente', N'En curso', N'Completada'))
    );
END;
GO

IF OBJECT_ID(N'dbo.movements', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.movements (
        id         INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_movements PRIMARY KEY,
        item_id    INT NOT NULL,
        item_name  NVARCHAR(60) NOT NULL,
        kind       NVARCHAR(10) NOT NULL,
        quantity   DECIMAL(12,2) NOT NULL,
        reason     NVARCHAR(100) NOT NULL CONSTRAINT DF_movements_reason DEFAULT N'',
        created_at DATETIMEOFFSET(0) NOT NULL,
        CONSTRAINT FK_movements_items FOREIGN KEY (item_id) REFERENCES dbo.items(id) ON DELETE NO ACTION,
        CONSTRAINT CK_movements_kind CHECK (kind IN (N'Entrada', N'Salida')),
        CONSTRAINT CK_movements_quantity_positive CHECK (quantity > 0)
    );
END;
GO

/* Carga los mismos datos ficticios del prototipo solo si las tablas están vacías. */
IF NOT EXISTS (SELECT 1 FROM dbo.items)
BEGIN
    INSERT INTO dbo.items (name, category, unit, stock, minimum)
    VALUES (N'Arroz',N'Abarrotes',N'kg',12,5),
           (N'Lentejas',N'Abarrotes',N'kg',3,4),
           (N'Aceite',N'Abarrotes',N'L',6,2),
           (N'Fideos',N'Abarrotes',N'kg',8,3),
           (N'Atún',N'Conservas',N'latas',18,6);
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.activities)
BEGIN
    INSERT INTO dbo.activities (name, [date], owner, status)
    VALUES (N'Organizar menú semanal',N'',N'Coordinación',N'Pendiente');
END;
GO
