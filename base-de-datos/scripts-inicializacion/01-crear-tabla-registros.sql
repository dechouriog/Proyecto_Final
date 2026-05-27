-- ----------------------------------------------------------------------------
-- Script de inicialización de la base de datos.
-- Se ejecuta automáticamente la primera vez que arranca el contenedor MySQL,
-- gracias al volumen montado en /docker-entrypoint-initdb.d
--
-- Crea la tabla principal donde se guardan los registros de los usuarios
-- interesados en estudiar una de las cuatro carreras de pregrado.
-- ----------------------------------------------------------------------------

-- Tabla de registros de interesados
-- La ciudad tiene 10 comunas (numeradas 1-10 según consigna).
-- Las carreras son: Medicina, Ingeniería, Abogacía, Licenciatura.
CREATE TABLE IF NOT EXISTS registros_interesados (
    id_registro       INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo   VARCHAR(150)  NOT NULL,
    numero_comuna     TINYINT       NOT NULL,
    carrera_interes   VARCHAR(50)   NOT NULL,
    fecha_ingreso     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    servidor_origen   VARCHAR(50)   NULL,    -- Para auditar qué web server registró el dato

    -- Validaciones a nivel de BD
    CONSTRAINT chk_comuna_valida
        CHECK (numero_comuna BETWEEN 1 AND 10),
    CONSTRAINT chk_carrera_valida
        CHECK (carrera_interes IN ('Medicina', 'Ingenieria', 'Abogacia', 'Licenciatura'))
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

-- Índices para acelerar las consultas del servicio de estadísticas
CREATE INDEX idx_comuna  ON registros_interesados (numero_comuna);
CREATE INDEX idx_carrera ON registros_interesados (carrera_interes);
CREATE INDEX idx_fecha   ON registros_interesados (fecha_ingreso);
