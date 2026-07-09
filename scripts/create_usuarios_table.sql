-- Tabla USUARIOS para Last Mile Delivery
-- Login automatico: usuario+password → empresa+rol
-- Ejecutar en AS/400: RUNQMQM SRC(QTEMP/LM_USUARIOS)

CREATE TABLE TESTLIB.USUARIOS (
    USU_ID         DECIMAL(10,0) NOT NULL GENERATED ALWAYS AS IDENTITY,
    USU_EMP_ID     DECIMAL(5,0)  NOT NULL,
    USU_USUARIO    VARCHAR(30)   NOT NULL,
    USU_PASS       VARCHAR(50)   NOT NULL,
    USU_NOMBRE     VARCHAR(100)  NOT NULL,
    USU_EMAIL      VARCHAR(100),
    USU_TELEFONO   VARCHAR(20),
    USU_ROL        VARCHAR(20)   NOT NULL DEFAULT 'operacion',
    USU_ACTIVO     CHAR(1)       NOT NULL DEFAULT 'S',
    USU_CREATED    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    USU_UPDATED    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (USU_ID)
);

-- Indices
CREATE INDEX TESTLIB.IX_USU_USER ON TESTLIB.USUARIOS (USU_USUARIO);
CREATE INDEX TESTLIB.IX_USU_EMP ON TESTLIB.USUARIOS (USU_EMP_ID);
CREATE INDEX TESTLIB.IX_USU_ROL ON TESTLIB.USUARIOS (USU_ROL);

-- Usuarios de prueba
-- EMP 1: DELIVERY EXPRESS MX
INSERT INTO TESTLIB.USUARIOS (USU_EMP_ID, USU_USUARIO, USU_PASS, USU_NOMBRE, USU_EMAIL, USU_ROL) VALUES
(1, 'admin',     'admin123',  'Administrador',         'admin@delivery.mx',     'admin'),
(1, 'operador',  'oper123',   'Operador General',       'ops@delivery.mx',       'operacion'),
(1, 'chofer1',   'chof123',   'Carlos Rodriguez',      'carlos@delivery.mx',    'chofer'),
(1, 'chofer2',   'chof123',   'Maria Lopez',           'maria@delivery.mx',     'chofer'),
(1, 'cliente1',  'clie123',   'Juan Perez Store',      'juan@perez.mx',         'cliente'),
(1, 'cliente2',  'clie123',   'Ana Garcia Shop',       'ana@garcia.mx',         'cliente');

-- EMP 2: TRANSPORTE RAPIDO SA
INSERT INTO TESTLIB.USUARIOS (USU_EMP_ID, USU_USUARIO, USU_PASS, USU_NOMBRE, USU_EMAIL, USU_ROL) VALUES
(2, 'admin2',    'admin123',  'Admin Transporte Rapido','admin@transporte.mx',   'admin'),
(2, 'ops2',      'oper123',   'Operador TR',            'ops@transporte.mx',     'operacion'),
(2, 'chofer3',   'chof123',   'Pedro Sanchez',         'pedro@transporte.mx',   'chofer'),
(2, 'cliente3',  'clie123',   'Tienda Rodriguez',      'tienda@rodriguez.mx',   'cliente');

-- EMP 3: LOGISTICA INTEGRAL MX
INSERT INTO TESTLIB.USUARIOS (USU_EMP_ID, USU_USUARIO, USU_PASS, USU_NOMBRE, USU_EMAIL, USU_ROL) VALUES
(3, 'admin3',    'admin123',  'Admin Logistica Integral','admin@logistica.mx',    'admin'),
(3, 'ops3',      'oper123',   'Operador LI',            'ops@logistica.mx',      'operacion'),
(3, 'chofer4',   'chof123',   'Roberto Diaz',          'roberto@logistica.mx',  'chofer'),
(3, 'cliente4',  'clie123',   'Comercial Torres',      'torres@comercial.mx',   'cliente');
