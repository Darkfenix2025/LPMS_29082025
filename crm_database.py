import psycopg2
import psycopg2.extras  # Para obtener resultados como diccionarios
import configparser
import os
import time  # Para timestamps
import datetime  # Para fechas de audiencias
import logging

# Configurar logging para operaciones de base de datos
logging.basicConfig(level=logging.INFO)
db_logger = logging.getLogger('crm_database')

# Nombre del archivo de la base de datos (ya no se usa con PostgreSQL)
DATABASE_FILE = 'crm_legal_db.db'

def get_db_config():
    """Lee el archivo config.ini y devuelve los parámetros de la BD."""
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    if 'postgresql' in config:
        return config['postgresql']
    else:
        raise Exception("No se encontró la sección [postgresql] en config.ini")

def connect_db():
    """Establece una conexión con la base de datos PostgreSQL."""
    try:
        params = get_db_config()
        conn = psycopg2.connect(**params)
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al conectar a PostgreSQL: {error}")
        return None


def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """
    Función auxiliar para ejecutar consultas SQL de manera simplificada.
    
    Args:
        query (str): Consulta SQL a ejecutar
        params (tuple): Parámetros para la consulta
        fetch_one (bool): Si True, retorna solo un registro
        fetch_all (bool): Si True, retorna todos los registros
    
    Returns:
        list/dict/None: Resultados de la consulta
    """
    conn = connect_db()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params or ())
            
            if fetch_one:
                result = cur.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                rows = cur.fetchall()
                return [dict(row) for row in rows]
            else:
                # Para INSERT/UPDATE/DELETE que no necesitan fetch
                conn.commit()
                return cur.rowcount
                
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error ejecutando consulta: {e}")
        return None
    finally:
        conn.close()
        
def get_parties_by_case_id(caso_id):
    """
    Obtiene todas las partes (parties) asociadas a un caso.
    Función de compatibilidad que retorna datos en formato esperado por el código legacy.

    Args:
        caso_id (int): ID del caso

    Returns:
        list: Lista de diccionarios con información de las partes
    """
    try:
        # Usar la función existente get_roles_by_case_id y adaptar el formato
        roles_data = get_roles_by_case_id(caso_id)

        parties = []
        for role in roles_data:
            # Adaptar el formato esperado por el código legacy
            party = {
                'id': role.get('rol_id'),
                'case_id': role.get('caso_id'),
                'contacto_id': role.get('contacto_id'),
                'rol': role.get('rol_principal'),  # Cambiar rol_principal a rol
                'rol_secundario': role.get('rol_secundario'),
                'representa_a_id': role.get('representa_a_id'),
                'datos_bancarios': role.get('datos_bancarios'),
                'notas_del_rol': role.get('notas_del_rol'),
                'created_at': role.get('rol_created_at'),
                # Información del contacto
                'nombre_completo': role.get('nombre_completo'),
                'es_persona_juridica': role.get('es_persona_juridica'),
                'dni': role.get('dni'),
                'cuit': role.get('cuit'),
                'domicilio_real': role.get('domicilio_real'),
                'domicilio_legal': role.get('domicilio_legal'),
                'email': role.get('email'),
                'telefono': role.get('telefono'),
                'notas_generales': role.get('notas_generales'),
                'contacto_created_at': role.get('contacto_created_at'),
                'orden_rol': role.get('orden_rol')
            }
            parties.append(party)

        return parties

    except Exception as e:
        print(f"Error al obtener partes para caso ID {caso_id}: {e}")
        return []


def get_roles_by_case_id(caso_id):
    """
    Obtiene todos los roles asociados a un caso con información de contactos.

    Args:
        caso_id (int): ID del caso

    Returns:
        list: Lista de diccionarios con datos combinados de roles_en_caso y contactos
    """
    query = """
        SELECT 
            r.id AS rol_id,
            r.caso_id,
            r.contacto_id,
            r.rol_principal,
            r.rol_secundario,
            r.representa_a_id,
            r.datos_bancarios,
            r.notas_del_rol,
            r.created_at AS rol_created_at,
            c.nombre_completo,
            c.es_persona_juridica,
            c.dni,
            c.cuit,
            c.domicilio_real,
            c.domicilio_legal,
            c.email,
            c.telefono,
            c.notas_generales
        FROM roles_en_caso r
        JOIN contactos c ON r.contacto_id = c.id
        WHERE r.caso_id = %s
        ORDER BY r.rol_principal, c.nombre_completo
    """
    try:
        roles = execute_query(query, (caso_id,), fetch_all=True)
        return roles if roles else []
    except Exception as e:
        print(f"Error al obtener roles para caso ID {caso_id}: {e}")
        return []
        
        

def create_tables():
    """Crea las tablas en la base de datos PostgreSQL si no existen."""
    commands = (
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            direccion TEXT,
            email TEXT,
            whatsapp TEXT,
            created_at BIGINT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS casos (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
            numero_expediente TEXT,
            anio_caratula TEXT,
            caratula TEXT NOT NULL,
            juzgado TEXT,
            jurisdiccion TEXT,
            etapa_procesal TEXT,
            notas TEXT,
            ruta_carpeta TEXT,
            ruta_carpeta_movimientos TEXT,
            ruta_vector_db TEXT,
            estado_indexacion TEXT DEFAULT 'No Indexado',
            inactivity_threshold_days INTEGER DEFAULT 30,
            inactivity_enabled INTEGER DEFAULT 1,
            created_at BIGINT,
            last_activity_timestamp BIGINT,
            last_inactivity_notification_timestamp BIGINT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS contactos (
            id SERIAL PRIMARY KEY,
            nombre_completo TEXT NOT NULL,
            es_persona_juridica BOOLEAN DEFAULT FALSE,
            dni TEXT,
            cuit TEXT,
            domicilio_real TEXT,
            domicilio_legal TEXT,
            email TEXT,
            telefono TEXT,
            notas_generales TEXT,
            created_at BIGINT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS roles_en_caso (
            id SERIAL PRIMARY KEY,
            caso_id INTEGER NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
            contacto_id INTEGER NOT NULL REFERENCES contactos(id) ON DELETE CASCADE,
            rol_principal TEXT NOT NULL, -- Ej: 'Actor', 'Demandado', 'Abogado', 'Perito'
            rol_secundario TEXT, -- Ej: 'Apoderado', 'Patrocinante'
            representa_a_id INTEGER REFERENCES roles_en_caso(id) ON DELETE SET NULL, -- Se referencia a sí misma
            datos_bancarios TEXT, -- Un campo flexible para CBU, Alias, etc.
            notas_del_rol TEXT,
            created_at BIGINT,
            UNIQUE (caso_id, contacto_id, rol_principal) -- Evita duplicar el mismo rol para la misma persona en un caso
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS etapas_procesales (
            id SERIAL PRIMARY KEY,
            nombre_etapa TEXT NOT NULL UNIQUE,
            orden INTEGER DEFAULT 0
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS partes_intervinientes (
            id SERIAL PRIMARY KEY,
            caso_id INTEGER NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
            nombre TEXT NOT NULL,
            tipo TEXT, -- Ej: 'Actora', 'Demandada', 'Tercero', 'Abogado Actora', etc.
            rol_procesal TEXT, -- Ej: 'Requirente', 'Requerida' (para mediaciones)
            dni TEXT,
            cuit TEXT,
            domicilio TEXT,
            contacto TEXT, -- Email o teléfono
            banco TEXT,
            cbu TEXT,
            alias_cbu TEXT,
            notas TEXT,
            created_at BIGINT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS audiencias (
            id SERIAL PRIMARY KEY,
            caso_id INTEGER NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
            fecha DATE NOT NULL,
            hora TIME,
            descripcion TEXT NOT NULL,
            link TEXT,
            recordatorio_activo BOOLEAN DEFAULT FALSE,
            recordatorio_minutos INTEGER DEFAULT 15,
            created_at BIGINT
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_audiencias_fecha ON audiencias (fecha);",
        "CREATE INDEX IF NOT EXISTS idx_audiencias_caso_id ON audiencias (caso_id);",
        """
        CREATE TABLE IF NOT EXISTS actividades_caso (
            id SERIAL PRIMARY KEY,
            caso_id INTEGER NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
            fecha_hora TIMESTAMP NOT NULL,
            tipo_actividad TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            creado_por TEXT,
            referencia_documento TEXT
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_actividades_caso_id_fecha ON actividades_caso (caso_id, fecha_hora DESC);",
        """
        CREATE TABLE IF NOT EXISTS tareas (
            id SERIAL PRIMARY KEY,
            caso_id INTEGER REFERENCES casos(id) ON DELETE SET NULL,
            descripcion TEXT NOT NULL,
            fecha_creacion TIMESTAMP NOT NULL,
            fecha_vencimiento DATE,
            prioridad TEXT DEFAULT 'Media',
            estado TEXT NOT NULL DEFAULT 'Pendiente',
            notas TEXT,
            es_plazo_procesal BOOLEAN DEFAULT FALSE,
            recordatorio_activo BOOLEAN DEFAULT FALSE,
            recordatorio_dias_antes INTEGER DEFAULT 1,
            fecha_ultima_notificacion TIMESTAMP
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_tareas_caso_id ON tareas (caso_id);",
        "CREATE INDEX IF NOT EXISTS idx_tareas_fecha_vencimiento ON tareas (fecha_vencimiento);",
        "CREATE INDEX IF NOT EXISTS idx_tareas_estado ON tareas (estado);",
        """
        CREATE TABLE IF NOT EXISTS etiquetas (
            id_etiqueta SERIAL PRIMARY KEY,
            nombre_etiqueta TEXT NOT NULL UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS cliente_etiquetas (
            cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
            etiqueta_id INTEGER NOT NULL REFERENCES etiquetas(id_etiqueta) ON DELETE CASCADE,
            PRIMARY KEY (cliente_id, etiqueta_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS caso_etiquetas (
            caso_id INTEGER NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
            etiqueta_id INTEGER NOT NULL REFERENCES etiquetas(id_etiqueta) ON DELETE CASCADE,
            PRIMARY KEY (caso_id, etiqueta_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS datos_usuario (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nombre_abogado TEXT,
            matricula_nacion TEXT,
            matricula_pba TEXT,
            matricula_federal TEXT,
            domicilio_procesal_caba TEXT,
            zona_notificacion TEXT,
            domicilio_procesal_pba TEXT,
            telefono_estudio TEXT,
            email_estudio TEXT,
            cuit TEXT,
            legajo_prev TEXT,
            domicilio_electronico_pba TEXT,
            cuenta_bancaria_honorarios TEXT, -- Campo nuevo y más genérico
            otros_datos TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS modelos_escritos (
            id SERIAL PRIMARY KEY,
            nombre_modelo TEXT NOT NULL UNIQUE,
            categoria TEXT, -- Ej: 'Civil', 'Laboral', 'Mediación'
            ruta_plantilla TEXT NOT NULL, -- Ruta al archivo .docx
            descripcion TEXT,
            created_at BIGINT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS movimientos_cuenta (
            id SERIAL PRIMARY KEY,
            caso_id INTEGER NOT NULL REFERENCES casos(id) ON DELETE CASCADE,
            fecha DATE NOT NULL,
            concepto TEXT NOT NULL,
            tipo_movimiento TEXT NOT NULL CHECK (tipo_movimiento IN ('Ingreso', 'Gasto')),
            monto NUMERIC(12, 2) NOT NULL CHECK (monto > 0),
            notas TEXT,
            created_at BIGINT
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_movimientos_caso_id ON movimientos_cuenta (caso_id);",
        "CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_cuenta (fecha DESC);",
        """
        CREATE TABLE IF NOT EXISTS prospectos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            contacto TEXT,
            fecha_primera_consulta DATE NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Consulta Inicial',
            convertido_a_cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
            fecha_conversion DATE,
            notas_generales TEXT,
            created_at BIGINT
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_prospectos_estado ON prospectos (estado);",
        "CREATE INDEX IF NOT EXISTS idx_prospectos_fecha_consulta ON prospectos (fecha_primera_consulta);",
        """
        CREATE TABLE IF NOT EXISTS consultas (
            id SERIAL PRIMARY KEY,
            prospecto_id INTEGER NOT NULL REFERENCES prospectos(id) ON DELETE CASCADE,
            fecha_consulta DATE NOT NULL,
            relato_original_cliente TEXT,
            hechos_reformulados_ia TEXT,
            encuadre_legal_preliminar TEXT,
            resultado_consulta TEXT,
            created_at BIGINT
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_consultas_prospecto_id ON consultas (prospecto_id);",
        "CREATE INDEX IF NOT EXISTS idx_consultas_fecha ON consultas (fecha_consulta DESC);",
    )

    conn = None
    try:
        conn = connect_db()
        if conn:
            with conn.cursor() as cur:
                print("Creando/Verificando tablas principales...")
                for command in commands:
                    cur.execute(command)
                
                # --- Poblar la tabla de etapas si está vacía ---
                cur.execute("SELECT COUNT(*) FROM etapas_procesales")
                if cur.fetchone()[0] == 0:
                    print("Poblando 'etapas_procesales' con datos iniciales...")
                    etapas_iniciales = [
                        ('Etapa Administrativa', 10), ('Mediación / Conciliación Previa', 20),
                        ('Interposición de Demanda', 30), ('Contestación de Demanda', 40),
                        ('Apertura a Prueba', 50), ('Producción de Prueba', 60),
                        ('Alegatos', 70), ('Llamamiento de Autos para Sentencia', 80),
                        ('Sentencia de Primera Instancia', 90), ('Apelación / Recurso', 100),
                        ('Sentencia de Cámara', 110), ('Ejecución de Sentencia', 120),
                        ('Archivo', 999), ('Otro', 1000)
                    ]
                    for etapa, orden in etapas_iniciales:
                        cur.execute("INSERT INTO etapas_procesales (nombre_etapa, orden) VALUES (%s, %s)", (etapa, orden))

                # --- Asegurar que la fila de usuario exista ---
                cur.execute("SELECT COUNT(*) FROM datos_usuario")
                if cur.fetchone()[0] == 0:
                    print("Insertando fila inicial en 'datos_usuario'...")
                    cur.execute("INSERT INTO datos_usuario (id) VALUES (1)")

            conn.commit()
            print("Esquema de base de datos completo creado/verificado con éxito")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al crear tablas: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# --- Funciones CRUD para Datos de Usuario ---

def get_datos_usuario():
    conn = connect_db()
    datos = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM datos_usuario WHERE id = 1")
                row = cur.fetchone()
                if row:
                    datos = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener datos del usuario: {e}")
        finally:
            conn.close()
    return datos

def save_datos_usuario(**kwargs):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                # Construir la parte SET de la consulta dinámicamente
                campos_a_actualizar = {k: v for k, v in kwargs.items() if k != 'id'}
                
                if not campos_a_actualizar:
                    print("Advertencia: No se proporcionaron campos para actualizar en save_datos_usuario.")
                    return False

                set_clause = ", ".join([f"{key} = %s" for key in campos_a_actualizar.keys()])
                valores = list(campos_a_actualizar.values())
                
                sql = f"UPDATE datos_usuario SET {set_clause} WHERE id = 1"
                
                cur.execute(sql, valores)
                conn.commit()
                if cur.rowcount > 0:
                    print("Datos del usuario guardados con éxito.")
                    success = True
                else:
                    print("Datos del usuario no necesitaron actualización o no se encontró la fila (id=1).")
                    success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al guardar datos del usuario: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

# --- Funciones CRUD para Clientes ---

def add_client(nombre, direccion="", email="", whatsapp=""):
    sql = """INSERT INTO clientes(nombre, direccion, email, whatsapp, created_at)
            VALUES(%s, %s, %s, %s, %s) RETURNING id;"""
    conn = None
    new_id = None
    try:
        conn = connect_db()
        if conn:
            with conn.cursor() as cur:
                cur.execute(sql, (nombre, direccion, email, whatsapp, int(time.time())))
                # CORRECCIÓN: Extraer el valor de la tupla
                res = cur.fetchone()
                if res:
                    new_id = res[0]
                conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al agregar cliente: {error}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()
    return new_id

def get_clients():
    conn = connect_db()
    clients = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT id, nombre, direccion, email, whatsapp, created_at FROM clientes ORDER BY nombre')
                rows = cur.fetchall()
                clients = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener clientes: {e}")
        finally:
            conn.close()
    return clients

def get_client_by_id(client_id):
    conn = connect_db()
    client_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT id, nombre, direccion, email, whatsapp, created_at FROM clientes WHERE id = %s', (client_id,))
                row = cur.fetchone()
                if row:
                    client_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener cliente por ID {client_id}: {e}")
        finally:
            conn.close()
    return client_data

def update_client(client_id, nombre, direccion, email, whatsapp):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE clientes
                    SET nombre = %s, direccion = %s, email = %s, whatsapp = %s
                    WHERE id = %s
                ''', (nombre, direccion, email, whatsapp, client_id))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar cliente ID {client_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def delete_client(client_id):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM clientes WHERE id = %s', (client_id,))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar cliente ID {client_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

# --- Funciones CRUD para Contactos ---

def add_contacto(nombre_completo, es_persona_juridica=False, dni="", cuit="", domicilio_real="", domicilio_legal="", email="", telefono="", notas_generales=""):
    """
    Agrega un nuevo contacto a la base de datos.

    Args:
        nombre_completo (str): Nombre completo del contacto (obligatorio)
        es_persona_juridica (bool): Si es persona jurídica
        dni (str): DNI del contacto
        cuit (str): CUIT del contacto
        domicilio_real (str): Domicilio real
        domicilio_legal (str): Domicilio legal
        email (str): Email del contacto
        telefono (str): Teléfono del contacto
        notas_generales (str): Notas generales

    Returns:
        int: ID del contacto creado o None si falla
    """
    if not nombre_completo or not nombre_completo.strip():
        print("Error: El nombre completo del contacto es obligatorio")
        return None

    conn = connect_db()
    new_id = None
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO contactos (nombre_completo, es_persona_juridica, dni, cuit, domicilio_real, domicilio_legal, email, telefono, notas_generales, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (nombre_completo.strip(), es_persona_juridica, dni.strip(), cuit.strip(), domicilio_real.strip(), domicilio_legal.strip(), email.strip(), telefono.strip(), notas_generales.strip(), int(time.time())))
                new_id = cur.fetchone()[0]
                conn.commit()
                print(f"Contacto '{nombre_completo}' agregado exitosamente con ID: {new_id}")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al agregar contacto: {e}")
            conn.rollback()
        finally:
            conn.close()
    return new_id

def get_contactos():
    """
    Obtiene todos los contactos de la base de datos ordenados por nombre completo.

    Returns:
        list: Lista de diccionarios con todos los contactos
    """
    conn = connect_db()
    contactos = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM contactos ORDER BY nombre_completo ASC')
                rows = cur.fetchall()
                contactos = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener contactos: {e}")
        finally:
            conn.close()
    return contactos

def get_contacto_by_id(contacto_id):
    """
    Obtiene un contacto específico por su ID.

    Args:
        contacto_id (int): ID del contacto

    Returns:
        dict: Datos del contacto o None si no existe
    """
    conn = connect_db()
    contacto_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM contactos WHERE id = %s', (contacto_id,))
                row = cur.fetchone()
                if row:
                    contacto_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener contacto por ID {contacto_id}: {e}")
        finally:
            conn.close()
    return contacto_data

def update_contacto(contacto_id, nombre_completo=None, es_persona_juridica=None, dni=None, cuit=None, domicilio_real=None, domicilio_legal=None, email=None, telefono=None, notas_generales=None):
    """
    Actualiza un contacto existente.

    Args:
        contacto_id (int): ID del contacto
        nombre_completo (str): Nuevo nombre completo (opcional)
        es_persona_juridica (bool): Nuevo valor para persona jurídica (opcional)
        dni (str): Nuevo DNI (opcional)
        cuit (str): Nuevo CUIT (opcional)
        domicilio_real (str): Nuevo domicilio real (opcional)
        domicilio_legal (str): Nuevo domicilio legal (opcional)
        email (str): Nuevo email (opcional)
        telefono (str): Nuevo teléfono (opcional)
        notas_generales (str): Nuevas notas generales (opcional)

    Returns:
        bool: True si la actualización fue exitosa
    """
    campos_a_actualizar = {}
    if nombre_completo is not None:
        campos_a_actualizar['nombre_completo'] = nombre_completo.strip()
    if es_persona_juridica is not None:
        campos_a_actualizar['es_persona_juridica'] = es_persona_juridica
    if dni is not None:
        campos_a_actualizar['dni'] = dni.strip()
    if cuit is not None:
        campos_a_actualizar['cuit'] = cuit.strip()
    if domicilio_real is not None:
        campos_a_actualizar['domicilio_real'] = domicilio_real.strip()
    if domicilio_legal is not None:
        campos_a_actualizar['domicilio_legal'] = domicilio_legal.strip()
    if email is not None:
        campos_a_actualizar['email'] = email.strip()
    if telefono is not None:
        campos_a_actualizar['telefono'] = telefono.strip()
    if notas_generales is not None:
        campos_a_actualizar['notas_generales'] = notas_generales.strip()

    if not campos_a_actualizar:
        print("Advertencia: No se proporcionaron campos para actualizar")
        return False

    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                set_clause = ", ".join([f"{key} = %s" for key in campos_a_actualizar.keys()])
                valores = list(campos_a_actualizar.values()) + [contacto_id]

                sql = f"UPDATE contactos SET {set_clause} WHERE id = %s"
                cur.execute(sql, valores)
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"Contacto ID {contacto_id} actualizado exitosamente")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar contacto ID {contacto_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def delete_contacto(contacto_id):
    """
    Elimina un contacto de la base de datos.
    ADVERTENCIA: Esto también eliminará todos los roles asociados debido a CASCADE.

    Args:
        contacto_id (int): ID del contacto a eliminar

    Returns:
        bool: True si la eliminación fue exitosa
    """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                # Verificar si el contacto tiene roles asociados
                cur.execute("SELECT COUNT(*) FROM roles_en_caso WHERE contacto_id = %s", (contacto_id,))
                roles_count = cur.fetchone()[0]

                if roles_count > 0:
                    print(f"ADVERTENCIA: El contacto ID {contacto_id} tiene {roles_count} roles asociados que serán eliminados.")

                cur.execute("DELETE FROM contactos WHERE id = %s", (contacto_id,))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"Contacto ID {contacto_id} eliminado correctamente")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar contacto ID {contacto_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

# --- Funciones CRUD para Etapas Procesales ---

def get_todas_las_etapas():
    """Obtiene todas las etapas procesales ordenadas por el campo 'orden'."""
    conn = connect_db()
    etapas = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT nombre_etapa FROM etapas_procesales ORDER BY orden, nombre_etapa ASC")
                rows = cur.fetchall()
                etapas = [row['nombre_etapa'] for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener etapas procesales: {e}")
        finally:
            conn.close()
    return etapas

# --- Funciones CRUD para Casos ---

def add_case(cliente_id, caratula, numero_expediente="", anio_caratula="", juzgado="", jurisdiccion="", etapa_procesal="", notas="", ruta_carpeta="", inactivity_threshold_days=30, inactivity_enabled=1):
    conn = connect_db()
    new_id = None
    if conn:
        try:
            with conn.cursor() as cur:
                timestamp = int(time.time())
                cur.execute('''
                    INSERT INTO casos (cliente_id, numero_expediente, anio_caratula, caratula, juzgado, jurisdiccion, etapa_procesal, notas, ruta_carpeta, inactivity_threshold_days, inactivity_enabled, created_at, last_activity_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (cliente_id, numero_expediente, anio_caratula, caratula, juzgado, jurisdiccion, etapa_procesal, notas, ruta_carpeta, inactivity_threshold_days, inactivity_enabled, timestamp, timestamp))
                new_id = cur.fetchone()[0]
                conn.commit()
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al agregar caso: {e}")
            conn.rollback()
        finally:
            conn.close()
    return new_id

def get_cases_for_inactivity_check():
    """
    Obtiene casos que están habilitados para el chequeo de inactividad,
    cuyo umbral de inactividad ha sido superado desde la última actividad,
    y que no han sido notificados hoy sobre esta inactividad.
    """
    conn = connect_db()
    cases_to_notify = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                today_start_timestamp = int(datetime.datetime.combine(datetime.date.today(), datetime.time.min).timestamp())
                current_timestamp = int(time.time())

                cur.execute('''
                    SELECT id, caratula, cliente_id, last_activity_timestamp, inactivity_threshold_days
                    FROM casos
                    WHERE inactivity_enabled = 1
                      AND (last_activity_timestamp + (inactivity_threshold_days * 24 * 60 * 60)) < %s
                      AND (last_inactivity_notification_timestamp IS NULL OR last_inactivity_notification_timestamp < %s)
                ''', (current_timestamp, today_start_timestamp))
                rows = cur.fetchall()
                cases_to_notify = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener casos para chequeo de inactividad: {e}")
        finally:
            conn.close()
    return cases_to_notify

def update_case_inactivity_notified(case_id):
    """ Actualiza el timestamp de la última notificación de inactividad para un caso. """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                timestamp = int(time.time())
                cur.execute('''
                    UPDATE casos
                    SET last_inactivity_notification_timestamp = %s
                    WHERE id = %s
                ''', (timestamp, case_id))
                conn.commit()
                success = cur.rowcount > 0
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar timestamp de notificación de inactividad para caso ID {case_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def get_cases_by_client(cliente_id):
    """
    Obtiene todos los casos asociados a un cliente específico.

    Args:
        cliente_id (int): ID del cliente

    Returns:
        list: Lista de diccionarios con información de casos, o None si hay error
    """
    # Validar parámetro de entrada
    if cliente_id is None or cliente_id == "":
        db_logger.error(f"Error: cliente_id inválido: {cliente_id}")
        return None

    # Convertir a entero si es necesario
    try:
        cliente_id = int(cliente_id)
    except (ValueError, TypeError):
        db_logger.error(f"Error: cliente_id debe ser un número entero válido: {cliente_id}")
        return None

    if cliente_id <= 0:
        db_logger.error(f"Error: cliente_id debe ser un número positivo: {cliente_id}")
        return None

    db_logger.info(f"Consultando casos para cliente ID: {cliente_id}")

    conn = connect_db()
    if not conn:
        db_logger.error("Error: No se pudo establecer conexión con la base de datos")
        return None

    cases = []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Verificar que el cliente existe
            cur.execute("SELECT id, nombre FROM clientes WHERE id = %s", (cliente_id,))
            cliente_row = cur.fetchone()
            if not cliente_row:
                db_logger.warning(f"Cliente ID {cliente_id} no encontrado en la base de datos")
                return []  # Retornar lista vacía, no None, ya que el cliente no existe pero no es un error de BD

            cliente_nombre = cliente_row['nombre']
            db_logger.info(f"Cliente encontrado: {cliente_nombre} (ID: {cliente_id})")

            # Ejecutar consulta principal
            cur.execute('''
                SELECT ca.*, cl.nombre as nombre_cliente
                FROM casos ca
                JOIN clientes cl ON ca.cliente_id = cl.id
                WHERE ca.cliente_id = %s
                ORDER BY ca.caratula ASC
            ''', (cliente_id,))

            rows = cur.fetchall()
            cases = [dict(row) for row in rows]

            db_logger.info(f"Encontrados {len(cases)} casos para cliente {cliente_nombre} (ID: {cliente_id})")

            # Log de casos encontrados (solo en modo debug)
            if cases:
                for case in cases[:3]:  # Log solo los primeros 3 casos
                    db_logger.debug(f"  Caso: {case.get('caratula', 'Sin carátula')} (ID: {case.get('id', 'N/A')})")
                if len(cases) > 3:
                    db_logger.debug(f"  ... y {len(cases) - 3} casos más")

    except psycopg2.OperationalError as e:
        db_logger.error(f"Error operacional de PostgreSQL al obtener casos para cliente {cliente_id}: {e}")
        return None
    except psycopg2.ProgrammingError as e:
        db_logger.error(f"Error de programación SQL al obtener casos para cliente {cliente_id}: {e}")
        return None
    except psycopg2.DataError as e:
        db_logger.error(f"Error de datos al obtener casos para cliente {cliente_id}: {e}")
        return None
    except (Exception, psycopg2.DatabaseError) as e:
        db_logger.error(f"Error general al obtener casos para cliente {cliente_id}: {e}")
        import traceback
        db_logger.error(f"Traceback completo: {traceback.format_exc()}")
        return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                db_logger.warning(f"Error al cerrar conexión de base de datos: {close_error}")

    return cases

def get_case_by_id(case_id):
    conn = connect_db()
    case_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT ca.*, cl.nombre as nombre_cliente
                    FROM casos ca
                    JOIN clientes cl ON ca.cliente_id = cl.id
                    WHERE ca.id = %s
                ''', (case_id,))
                row = cur.fetchone()
                if row:
                    case_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener caso por ID {case_id}: {e}")
        finally:
            conn.close()
    return case_data

def update_case(case_id, caratula, numero_expediente, anio_caratula, juzgado, jurisdiccion, etapa_procesal, notas, ruta_carpeta, inactivity_threshold_days, inactivity_enabled):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE casos
                    SET caratula = %s, numero_expediente = %s, anio_caratula = %s, juzgado = %s,
                        jurisdiccion = %s, etapa_procesal = %s, notas = %s, ruta_carpeta = %s,
                        inactivity_threshold_days = %s, inactivity_enabled = %s 
                    WHERE id = %s
                ''', (caratula, numero_expediente, anio_caratula, juzgado, jurisdiccion, etapa_procesal, notas, ruta_carpeta, inactivity_threshold_days, inactivity_enabled, case_id))
                conn.commit()
                if cur.rowcount > 0:
                    update_last_activity(case_id)
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar caso ID {case_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def delete_case(case_id):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM casos WHERE id = %s', (case_id,))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar caso ID {case_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def update_case_folder(case_id, folder_path):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('UPDATE casos SET ruta_carpeta = %s WHERE id = %s', (folder_path, case_id))
                conn.commit()
                if cur.rowcount > 0:
                    update_last_activity(case_id)
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar ruta de carpeta para caso ID {case_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def update_etapa_procesal(case_id, nueva_etapa):
    """
    Updates only the process stage (etapa_procesal) for a specific case.
    
    Args:
        case_id (int): The ID of the case to update
        nueva_etapa (str): The new process stage value
        
    Returns:
        bool: True if successful, False otherwise
    """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('UPDATE casos SET etapa_procesal = %s WHERE id = %s', (nueva_etapa, case_id))
                conn.commit()
                if cur.rowcount > 0:
                    update_last_activity(case_id)
                    success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar etapa procesal para caso ID {case_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def update_last_activity(case_id):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                timestamp = int(time.time())
                cur.execute('UPDATE casos SET last_activity_timestamp = %s WHERE id = %s', (timestamp, case_id))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar timestamp de actividad para caso ID {case_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

# --- Funciones para Reportes ---

def get_casos_para_reporte(cliente_id=None):
    """
    Obtiene casos activos para generar reportes.
    Excluye casos archivados e incluye información del cliente via JOIN.
    
    Args:
        cliente_id (int, optional): ID del cliente para filtrar. Si es None, obtiene todos los casos.
    
    Returns:
        list: Lista de diccionarios con información de casos activos
    """
    conn = connect_db()
    casos = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if cliente_id:
                    cur.execute('''
                        SELECT ca.id as caso_id, ca.numero_expediente, ca.anio_caratula, 
                               ca.caratula, ca.juzgado, ca.etapa_procesal, ca.notas,
                               cl.nombre as nombre_cliente
                        FROM casos ca
                        JOIN clientes cl ON ca.cliente_id = cl.id
                        WHERE ca.cliente_id = %s 
                          AND (ca.etapa_procesal != 'Archivo' OR ca.etapa_procesal IS NULL)
                        ORDER BY cl.nombre, ca.caratula ASC
                    ''', (cliente_id,))
                else:
                    cur.execute('''
                        SELECT ca.id as caso_id, ca.numero_expediente, ca.anio_caratula, 
                               ca.caratula, ca.juzgado, ca.etapa_procesal, ca.notas,
                               cl.nombre as nombre_cliente
                        FROM casos ca
                        JOIN clientes cl ON ca.cliente_id = cl.id
                        WHERE (ca.etapa_procesal != 'Archivo' OR ca.etapa_procesal IS NULL)
                        ORDER BY cl.nombre, ca.caratula ASC
                    ''')
                rows = cur.fetchall()
                casos = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener casos para reporte: {e}")
        finally:
            conn.close()
    return casos

def get_ultimo_movimiento_por_caso_id(caso_id):
    """
    Obtiene el último movimiento procesal de un caso.
    
    Args:
        caso_id (int): ID del caso
    
    Returns:
        str: Último movimiento formateado como "DD-MM-YYYY: [Descripción]" 
             o "Sin movimientos registrados" si no hay actividades
    """
    conn = connect_db()
    ultimo_movimiento = "Sin movimientos registrados"
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT fecha_hora, descripcion
                    FROM actividades_caso
                    WHERE caso_id = %s
                    ORDER BY fecha_hora DESC
                    LIMIT 1
                ''', (caso_id,))
                row = cur.fetchone()
                if row:
                    fecha_hora = row['fecha_hora']
                    descripcion = row['descripcion']
                    
                    # Formatear la fecha como DD-MM-YYYY (manejar string y datetime)
                    try:
                        if isinstance(fecha_hora, str):
                            # Intentar parsear string a datetime
                            if 'T' in fecha_hora:
                                fecha_dt = datetime.datetime.fromisoformat(fecha_hora.replace('T', ' '))
                            else:
                                fecha_dt = datetime.datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
                            fecha_formateada = fecha_dt.strftime("%d-%m-%Y")
                        else:
                            # Ya es datetime
                            fecha_formateada = fecha_hora.strftime("%d-%m-%Y")
                        
                        ultimo_movimiento = f"{fecha_formateada}: {descripcion}"
                    except (ValueError, AttributeError) as e:
                        # Si falla el formateo, usar descripción sin fecha
                        ultimo_movimiento = f"Fecha inválida: {descripcion}"
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener último movimiento para caso ID {caso_id}: {e}")
        finally:
            conn.close()
    return ultimo_movimiento

# --- Funciones CRUD para Actividades del Caso ---

def add_actividad_caso(caso_id, fecha_hora, tipo_actividad, descripcion, creado_por=None, referencia_documento=None):
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO actividades_caso (caso_id, fecha_hora, tipo_actividad, descripcion, creado_por, referencia_documento)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                ''', (caso_id, fecha_hora, tipo_actividad, descripcion, creado_por, referencia_documento))
                new_id = cur.fetchone()[0]
                conn.commit()
                update_last_activity(caso_id)
                return new_id
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al agregar actividad al caso ID {caso_id}: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def get_actividades_by_caso_id(caso_id, order_desc=True):
    conn = connect_db()
    actividades = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                order_direction = "DESC" if order_desc else "ASC"
                sql = f'''
                    SELECT id, caso_id, fecha_hora, tipo_actividad, descripcion, creado_por, referencia_documento 
                    FROM actividades_caso 
                    WHERE caso_id = %s 
                    ORDER BY fecha_hora {order_direction}
                '''
                cur.execute(sql, (caso_id,))
                rows = cur.fetchall()
                actividades = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener actividades para el caso ID {caso_id}: {e}")
        finally:
            conn.close()
    return actividades

def get_actividad_by_id(actividad_id):
    conn = connect_db()
    actividad_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT id, caso_id, fecha_hora, tipo_actividad, descripcion, creado_por, referencia_documento 
                    FROM actividades_caso 
                    WHERE id = %s
                ''', (actividad_id,))
                row = cur.fetchone()
                if row:
                    actividad_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener actividad por ID {actividad_id}: {e}")
        finally:
            conn.close()
    return actividad_data

def update_actividad_caso(actividad_id, tipo_actividad, descripcion, referencia_documento=None):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT caso_id FROM actividades_caso WHERE id = %s', (actividad_id,))
                row_check = cur.fetchone()

                cur.execute('''
                    UPDATE actividades_caso
                    SET tipo_actividad = %s,
                        descripcion = %s,
                        referencia_documento = %s 
                    WHERE id = %s
                ''', (tipo_actividad, descripcion, referencia_documento, actividad_id))
                conn.commit()
                if cur.rowcount > 0 and row_check:
                    update_last_activity(row_check['caso_id'])
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar actividad ID {actividad_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def delete_actividad_caso(actividad_id):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT caso_id FROM actividades_caso WHERE id = %s', (actividad_id,))
                row_check = cur.fetchone()

                cur.execute('DELETE FROM actividades_caso WHERE id = %s', (actividad_id,))
                conn.commit()
                if cur.rowcount > 0 and row_check:
                    update_last_activity(row_check['caso_id'])
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar actividad ID {actividad_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

# --- Funciones CRUD para Tareas ---

def add_tarea(descripcion, caso_id=None, fecha_vencimiento=None, prioridad='Media', estado='Pendiente', notas=None, es_plazo_procesal=0, recordatorio_activo=0, recordatorio_dias_antes=1):
    """ Agrega una nueva tarea. """
    conn = connect_db()
    new_id = None
    if conn:
        try:
            with conn.cursor() as cur:
                fecha_creacion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Validar fecha_vencimiento
                if fecha_vencimiento:
                    try:
                        fecha_venc_dt = datetime.datetime.strptime(fecha_vencimiento, "%Y-%m-%d %H:%M:%S")
                        fecha_vencimiento = fecha_venc_dt.strftime("%Y-%m-%d")
                    except ValueError:
                        try:
                            fecha_venc_dt = datetime.datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
                            fecha_vencimiento = fecha_venc_dt.strftime("%Y-%m-%d")
                        except ValueError:
                            print(f"Advertencia: Formato de fecha_vencimiento ('{fecha_vencimiento}') no válido. Se guardará como NULL.")
                            fecha_vencimiento = None
                
                cur.execute('''
                    INSERT INTO tareas (caso_id, descripcion, fecha_creacion, fecha_vencimiento, prioridad, estado, notas, es_plazo_procesal, recordatorio_activo, recordatorio_dias_antes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (caso_id, descripcion, fecha_creacion, fecha_vencimiento, prioridad, estado, notas, es_plazo_procesal, recordatorio_activo, recordatorio_dias_antes))
                new_id = cur.fetchone()[0]
                conn.commit()
                if new_id and caso_id:
                    update_last_activity(caso_id)
                print(f"Tarea ID {new_id} ('{descripcion[:30]}...') agregada.")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al agregar tarea: {e}")
            conn.rollback()
        finally:
            conn.close()
    return new_id

def get_tarea_by_id(tarea_id):
    """ Obtiene una tarea específica por su ID. """
    conn = connect_db()
    tarea_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM tareas WHERE id = %s", (tarea_id,))
                row = cur.fetchone()
                if row:
                    tarea_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener tarea por ID {tarea_id}: {e}")
        finally:
            conn.close()
    return tarea_data

def get_tareas_by_caso_id(caso_id, incluir_completadas=False, orden="fecha_vencimiento_asc"):
    """ Obtiene todas las tareas para un caso específico. """
    conn = connect_db()
    tareas = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                sql = "SELECT * FROM tareas WHERE caso_id = %s"
                params = [caso_id]

                if not incluir_completadas:
                    sql += " AND estado NOT IN (%s, %s)"
                    params.extend(["Completada", "Cancelada"])
                
                if orden == "fecha_vencimiento_asc":
                    sql += " ORDER BY CASE WHEN fecha_vencimiento IS NULL THEN 1 ELSE 0 END, fecha_vencimiento ASC, CASE prioridad WHEN 'Alta' THEN 1 WHEN 'Media' THEN 2 WHEN 'Baja' THEN 3 ELSE 4 END ASC"
                elif orden == "prioridad":
                    sql += " ORDER BY CASE prioridad WHEN 'Alta' THEN 1 WHEN 'Media' THEN 2 WHEN 'Baja' THEN 3 ELSE 4 END ASC, CASE WHEN fecha_vencimiento IS NULL THEN 1 ELSE 0 END, fecha_vencimiento ASC"

                cur.execute(sql, params)
                rows = cur.fetchall()
                tareas = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener tareas para el caso ID {caso_id}: {e}")
        finally:
            conn.close()
    return tareas

def update_tarea(tarea_id, descripcion, fecha_vencimiento=None, prioridad=None, estado=None, notas=None, es_plazo_procesal=None, recordatorio_activo=None, recordatorio_dias_antes=None):
    """ Actualiza una tarea existente. Solo actualiza los campos que se proporcionan (no son None). """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Obtener datos actuales y caso_id para actualizar last_activity
                current_tarea = get_tarea_by_id(tarea_id)
                if not current_tarea:
                    print(f"Error: Tarea ID {tarea_id} no encontrada para actualizar.")
                    return False

                # Construir consulta de actualización dinámicamente
                campos_actualizar = []
                valores = []
                
                if descripcion is not None:
                    campos_actualizar.append("descripcion = %s")
                    valores.append(descripcion)
                
                if fecha_vencimiento is not None:
                    if fecha_vencimiento:
                        try:
                            fecha_venc_dt = datetime.datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
                            fecha_vencimiento = fecha_venc_dt.strftime("%Y-%m-%d")
                        except ValueError:
                            print(f"Advertencia: Formato de fecha_vencimiento ('{fecha_vencimiento}') no válido.")
                            fecha_vencimiento = None
                    campos_actualizar.append("fecha_vencimiento = %s")
                    valores.append(fecha_vencimiento)
                
                if prioridad is not None:
                    campos_actualizar.append("prioridad = %s")
                    valores.append(prioridad)
                
                if estado is not None:
                    campos_actualizar.append("estado = %s")
                    valores.append(estado)
                
                if notas is not None:
                    campos_actualizar.append("notas = %s")
                    valores.append(notas)
                
                if es_plazo_procesal is not None:
                    campos_actualizar.append("es_plazo_procesal = %s")
                    valores.append(es_plazo_procesal)
                
                if recordatorio_activo is not None:
                    campos_actualizar.append("recordatorio_activo = %s")
                    valores.append(recordatorio_activo)
                
                if recordatorio_dias_antes is not None:
                    campos_actualizar.append("recordatorio_dias_antes = %s")
                    valores.append(recordatorio_dias_antes)

                if not campos_actualizar:
                    print("Advertencia: No se proporcionaron campos para actualizar en update_tarea.")
                    return True

                valores.append(tarea_id)
                sql = f"UPDATE tareas SET {', '.join(campos_actualizar)} WHERE id = %s"
                
                cur.execute(sql, valores)
                conn.commit()
                
                if cur.rowcount > 0 and current_tarea.get('caso_id'):
                    update_last_activity(current_tarea['caso_id'])
                
                success = True
                print(f"Tarea ID {tarea_id} actualizada.")
                
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar tarea ID {tarea_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def delete_tarea(tarea_id):
    """ Elimina una tarea. """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT caso_id FROM tareas WHERE id = %s', (tarea_id,))
                row_check = cur.fetchone()

                cur.execute('DELETE FROM tareas WHERE id = %s', (tarea_id,))
                conn.commit()
                
                if cur.rowcount > 0:
                    if row_check and row_check['caso_id']:
                        update_last_activity(row_check['caso_id'])
                    success = True
                    print(f"Tarea ID {tarea_id} eliminada.")
                else:
                    print(f"Advertencia: Tarea ID {tarea_id} no encontrada para eliminar.")
                    
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar tarea ID {tarea_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

# --- Funciones CRUD para Audiencias ---

def add_audiencia(caso_id, fecha, hora, descripcion, link="", recordatorio_activo=False, recordatorio_minutos=15):
    conn = connect_db()
    new_id = None
    if conn:
        try:
            with conn.cursor() as cur:
                timestamp = int(time.time())
                cur.execute('''
                    INSERT INTO audiencias (caso_id, fecha, hora, descripcion, link, recordatorio_activo, recordatorio_minutos, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (caso_id, fecha, hora, descripcion, link, int(recordatorio_activo), recordatorio_minutos, timestamp))
                new_id = cur.fetchone()[0]
                conn.commit()
                update_last_activity(caso_id)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al agregar audiencia: {e}")
            conn.rollback()
        finally:
            conn.close()
    return new_id

def get_audiencias():
    conn = connect_db()
    audiencias = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT a.*, c.caratula, cl.nombre as nombre_cliente
                    FROM audiencias a
                    JOIN casos c ON a.caso_id = c.id
                    JOIN clientes cl ON c.cliente_id = cl.id
                    ORDER BY a.fecha, a.hora
                ''')
                rows = cur.fetchall()
                audiencias = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener audiencias: {e}")
        finally:
            conn.close()
    return audiencias

def get_audiencias_by_date_range(fecha_inicio, fecha_fin):
    conn = connect_db()
    audiencias = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT a.*, c.caratula, cl.nombre as nombre_cliente
                    FROM audiencias a
                    JOIN casos c ON a.caso_id = c.id
                    JOIN clientes cl ON c.cliente_id = cl.id
                    WHERE a.fecha BETWEEN %s AND %s
                    ORDER BY a.fecha, a.hora
                ''', (fecha_inicio, fecha_fin))
                rows = cur.fetchall()
                audiencias = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener audiencias por rango de fechas: {e}")
        finally:
            conn.close()
    return audiencias

def get_audiencia_by_id(audiencia_id):
    conn = connect_db()
    audiencia_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT a.*, c.caratula, cl.nombre as nombre_cliente
                    FROM audiencias a
                    JOIN casos c ON a.caso_id = c.id
                    JOIN clientes cl ON c.cliente_id = cl.id
                    WHERE a.id = %s
                ''', (audiencia_id,))
                row = cur.fetchone()
                if row:
                    audiencia_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener audiencia por ID {audiencia_id}: {e}")
        finally:
            conn.close()
    return audiencia_data

def update_audiencia(audiencia_id, fecha, hora, descripcion, link="", recordatorio_activo=False, recordatorio_minutos=15):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT caso_id FROM audiencias WHERE id = %s', (audiencia_id,))
                row_check = cur.fetchone()

                cur.execute('''
                    UPDATE audiencias
                    SET fecha = %s, hora = %s, descripcion = %s, link = %s,
                        recordatorio_activo = %s, recordatorio_minutos = %s
                    WHERE id = %s
                ''', (fecha, hora, descripcion, link, int(recordatorio_activo), recordatorio_minutos, audiencia_id))
                conn.commit()
                
                if cur.rowcount > 0 and row_check:
                    update_last_activity(row_check['caso_id'])
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar audiencia ID {audiencia_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def delete_audiencia(audiencia_id):
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT caso_id FROM audiencias WHERE id = %s', (audiencia_id,))
                row_check = cur.fetchone()

                cur.execute('DELETE FROM audiencias WHERE id = %s', (audiencia_id,))
                conn.commit()
                
                if cur.rowcount > 0 and row_check:
                    update_last_activity(row_check['caso_id'])
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar audiencia ID {audiencia_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def es_audiencia_vencida(fecha, hora):
    """
    Determina si una audiencia ya pasó su fecha y hora.
    
    Args:
        fecha: Fecha de la audiencia (date object o string)
        hora: Hora de la audiencia (time object o string)
        
    Returns:
        bool: True si la audiencia ya pasó
    """
    try:
        # Import date utilities here to avoid circular imports
        import date_utils
        
        # Use the improved date utility function with 5-minute grace period
        return date_utils.DateFormatter.is_date_expired(fecha, hora)
        
    except Exception as e:
        print(f"Error al validar si audiencia está vencida: {e}")
        # En caso de error, ser conservador y no considerar vencida
        return False

def get_audiencias_con_recordatorio_activo():
    """
    Obtiene audiencias que tienen recordatorio activo para verificar notificaciones.
    Filtra automáticamente audiencias vencidas usando optimización SQL y validación adicional.
    """
    conn = connect_db()
    audiencias = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Optimized query: filter at SQL level for better performance
                # Get audiencias from today onwards, then filter by time in Python for today's audiencias
                cur.execute('''
                    SELECT a.*, c.caratula, cl.nombre as nombre_cliente
                    FROM audiencias a
                    JOIN casos c ON a.caso_id = c.id
                    JOIN clientes cl ON c.cliente_id = cl.id
                    WHERE a.recordatorio_activo = 1 
                      AND a.fecha::date >= CURRENT_DATE
                    ORDER BY a.fecha, a.hora
                ''')
                rows = cur.fetchall()
                audiencias_candidatas = [dict(row) for row in rows]
                
                # Additional filtering for today's audiencias considering time
                audiencias = []
                audiencias_filtradas_por_hora = 0
                audiencias_futuras = 0
                
                for audiencia in audiencias_candidatas:
                    # Use improved date utility function for expiration check
                    if not es_audiencia_vencida(audiencia['fecha'], audiencia['hora']):
                        audiencias.append(audiencia)
                        # Count future vs today audiencias for logging
                        fecha_aud = audiencia['fecha']
                        if isinstance(fecha_aud, str):
                            try:
                                fecha_aud = datetime.datetime.strptime(fecha_aud, '%Y-%m-%d').date()
                            except ValueError:
                                pass
                        
                        if isinstance(fecha_aud, datetime.date) and fecha_aud > datetime.date.today():
                            audiencias_futuras += 1
                    else:
                        audiencias_filtradas_por_hora += 1
                
                # Enhanced logging for debugging
                total_candidatas = len(audiencias_candidatas)
                total_validas = len(audiencias)
                
                db_logger.info(f"Audiencias con recordatorio: {total_candidatas} candidatas, {total_validas} válidas")
                
                if total_validas > 0:
                    print(f"[DB] [OK] {total_validas} audiencias con recordatorio activo validas")
                    print(f"    - {audiencias_futuras} futuras, {total_validas - audiencias_futuras} para hoy")
                    if audiencias_filtradas_por_hora > 0:
                        print(f"    - {audiencias_filtradas_por_hora} filtradas por hora vencida")
                else:
                    print("[DB] ⚠ No se encontraron audiencias con recordatorio activo válidas")
                    if audiencias_filtradas_por_hora > 0:
                        print(f"    - {audiencias_filtradas_por_hora} audiencias de hoy ya vencidas")
                    if total_candidatas == 0:
                        print("    - No hay audiencias con recordatorio activo en la base de datos")
                    
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"[ERROR] Error al obtener audiencias con recordatorio activo: {e}")
            db_logger.error(f"Error in get_audiencias_con_recordatorio_activo: {e}")
            
            # Fallback query without date filtering - create new cursor
            try:
                print("[DB] Intentando consulta fallback sin filtro de fecha...")
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as fallback_cur:
                    fallback_cur.execute('''
                        SELECT a.*, c.caratula, cl.nombre as nombre_cliente
                        FROM audiencias a
                        JOIN casos c ON a.caso_id = c.id
                        JOIN clientes cl ON c.cliente_id = cl.id
                        WHERE a.recordatorio_activo = 1
                        ORDER BY a.fecha, a.hora
                    ''')
                    rows = fallback_cur.fetchall()
                    all_audiencias = [dict(row) for row in rows]
                    
                    # Filter expired audiencias manually
                    audiencias = []
                    for audiencia in all_audiencias:
                        if not es_audiencia_vencida(audiencia['fecha'], audiencia['hora']):
                            audiencias.append(audiencia)
                    
                    print(f"[DB] Consulta fallback exitosa: {len(audiencias)} audiencias válidas de {len(all_audiencias)} totales")
                
            except (Exception, psycopg2.DatabaseError) as e2:
                print(f"[ERROR] Error en consulta fallback: {e2}")
                db_logger.error(f"Error in fallback query: {e2}")
                
        finally:
            conn.close()
    
    return audiencias

def get_audiencias_proximas(dias_adelante=7):
    """Obtiene audiencias próximas en los próximos N días"""
    conn = connect_db()
    audiencias = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT a.*, c.caratula, cl.nombre as nombre_cliente
                    FROM audiencias a
                    JOIN casos c ON a.caso_id = c.id
                    JOIN clientes cl ON c.cliente_id = cl.id
                    WHERE a.fecha BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
                    ORDER BY a.fecha, a.hora
                ''', (dias_adelante,))
                rows = cur.fetchall()
                audiencias = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener audiencias próximas: {e}")
        finally:
            conn.close()
    return audiencias

def get_tareas_para_notificacion():
    """Obtiene tareas que necesitan notificación de recordatorio"""
    conn = connect_db()
    tareas = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Obtener fecha actual para comparaciones
                fecha_hoy = datetime.date.today()
                
                cur.execute('''
                    SELECT t.*, c.caratula, cl.nombre as nombre_cliente
                    FROM tareas t
                    LEFT JOIN casos c ON t.caso_id = c.id
                    LEFT JOIN clientes cl ON c.cliente_id = cl.id
                    WHERE t.recordatorio_activo = 1
                      AND t.estado NOT IN ('Completada', 'Cancelada')
                      AND t.fecha_vencimiento IS NOT NULL
                      AND (
                          t.fecha_ultima_notificacion IS NULL 
                          OR DATE(t.fecha_ultima_notificacion) < %s
                      )
                      AND CAST(t.fecha_vencimiento AS DATE) >= %s
                    ORDER BY t.fecha_vencimiento
                ''', (fecha_hoy, fecha_hoy))
                rows = cur.fetchall()
                
                # Filtrar tareas que realmente necesitan notificación según días de anticipación
                tareas_filtradas = []
                for row in rows:
                    tarea = dict(row)
                    fecha_vencimiento = tarea['fecha_vencimiento']
                    dias_antes = tarea.get('recordatorio_dias_antes', 1) or 1
                    
                    try:
                        # Convertir fecha_vencimiento a date
                        if isinstance(fecha_vencimiento, str):
                            # Manejar formato ISO con tiempo
                            if 'T' in fecha_vencimiento:
                                fecha_vencimiento = datetime.datetime.fromisoformat(fecha_vencimiento.replace('T', ' ')).date()
                            else:
                                fecha_vencimiento = datetime.datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
                        elif isinstance(fecha_vencimiento, datetime.datetime):
                            fecha_vencimiento = fecha_vencimiento.date()
                        
                        # Calcular fecha de notificación
                        fecha_notificacion = fecha_vencimiento - datetime.timedelta(days=dias_antes)
                        
                        # Solo notificar si:
                        # 1. Hoy es la fecha de notificación o después
                        # 2. La tarea no ha vencido hace más de 30 días (evitar notificaciones de tareas muy vencidas)
                        dias_desde_vencimiento = (fecha_hoy - fecha_vencimiento).days
                        
                        if (fecha_hoy >= fecha_notificacion and 
                            dias_desde_vencimiento <= 30):  # Máximo 30 días después del vencimiento
                            tareas_filtradas.append(tarea)
                            
                    except (ValueError, TypeError) as e:
                        print(f"Error procesando fecha de tarea ID {tarea['id']}: {e}")
                        continue
                
                tareas = tareas_filtradas
                
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener tareas para notificación: {e}")
        finally:
            conn.close()
    return tareas

def update_fecha_ultima_notificacion_tarea(tarea_id):
    """Actualiza la fecha de última notificación de una tarea"""
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                fecha_actual = datetime.datetime.now()
                cur.execute('''
                    UPDATE tareas 
                    SET fecha_ultima_notificacion = %s 
                    WHERE id = %s
                ''', (fecha_actual, tarea_id))
                conn.commit()
                success = cur.rowcount > 0
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar fecha de notificación de tarea ID {tarea_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

# --- (OBSOLETO) Funciones CRUD para Partes Intervinientes ---
# Estas funciones interactúan con la tabla `partes_intervinientes` que ha sido reemplazada 
# por el sistema `contactos` + `roles_en_caso`. Se mantienen para consulta pero no deben usarse en código nuevo.

def add_parte_interviniente(*args, **kwargs):
    """
    ⚠️ FUNCIÓN OBSOLETA - NO USAR EN CÓDIGO NUEVO ⚠️
    
    Esta función ha sido reemplazada por el nuevo sistema de contactos y roles.
    Se mantiene solo para compatibilidad temporal.
    
    MIGRACIÓN REQUERIDA:
    ==================
    
    ANTES (obsoleto):
    parte_id = add_parte_interviniente({
        'caso_id': 1,
        'nombre': 'Juan Pérez',
        'tipo': 'Actor',
        'dni': '12345678',
        'email': 'juan@example.com'
    })
    
    DESPUÉS (nuevo sistema):
    # 1. Buscar contacto existente
    contactos = search_contactos('Juan Pérez')
    if contactos:
        contacto_id = contactos[0]['id']
    else:
        # 2. Crear nuevo contacto
        contacto_id = add_contacto({
            'nombre_completo': 'Juan Pérez',
            'dni': '12345678',
            'email': 'juan@example.com'
        })
    
    # 3. Asignar rol en caso
    rol_id = add_rol_a_caso({
        'caso_id': 1,
        'contacto_id': contacto_id,
        'rol_principal': 'Actor'
    })
    
    BENEFICIOS DEL NUEVO SISTEMA:
    - Reutilización de contactos entre casos
    - Soporte para jerarquías de representación
    - Mejor integridad de datos
    - Búsquedas más eficientes
    
    Ver documentación: docs/DEVELOPER_GUIDE_PARTES.md
    """
    import warnings
    import traceback
    import logging
    import inspect
    
    # Obtener información del caller
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    line_number = frame.f_lineno
    function_name = frame.f_code.co_name
    
    # Log detallado para tracking
    logging.warning(
        f"LEGACY FUNCTION USAGE: add_parte_interviniente called from "
        f"{filename}:{line_number} in function '{function_name}'"
    )
    
    # Warning visible para el desarrollador
    warnings.warn(
        "add_parte_interviniente is deprecated. Use add_contacto + add_rol_a_caso instead. "
        "See docs/DEVELOPER_GUIDE_PARTES.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Mensaje detallado en consola
    print("\n" + "🚨" * 20)
    print("FUNCIÓN OBSOLETA DETECTADA: add_parte_interviniente")
    print("🚨" * 20)
    print(f"📍 Llamada desde: {filename}:{line_number}")
    print(f"📍 Función: {function_name}")
    print("\n📖 GUÍA DE MIGRACIÓN:")
    print("   1. Usar search_contactos() para buscar contacto existente")
    print("   2. Si no existe, usar add_contacto() para crear")
    print("   3. Usar add_rol_a_caso() para asignar rol")
    print("\n📚 Documentación: docs/DEVELOPER_GUIDE_PARTES.md")
    print("🚨" * 50 + "\n")
    
    return None

def get_partes_by_caso_id(*args, **kwargs):
    """
    ⚠️ FUNCIÓN OBSOLETA - NO USAR EN CÓDIGO NUEVO ⚠️
    
    Esta función ha sido reemplazada por get_roles_by_caso_id que proporciona
    datos jerárquicos completos y mejor rendimiento.
    
    MIGRACIÓN REQUERIDA:
    ==================
    
    ANTES (obsoleto):
    partes = get_partes_by_caso_id(caso_id)
    for parte in partes:
        print(parte['nombre'], parte['tipo'])
    
    DESPUÉS (nuevo sistema):
    roles = get_roles_by_caso_id(caso_id, incluir_jerarquia=True)
    for rol in roles:
        print(rol['nombre_completo'], rol['rol_principal'])
        if rol['representa_a_id']:
            print(f"  Representa a: {rol['nombre_representado']}")
    
    NUEVAS CARACTERÍSTICAS:
    - Información jerárquica de representación
    - Datos completos del contacto incluidos
    - Mejor rendimiento con consultas optimizadas
    - Soporte para filtrado y ordenamiento
    
    Ver documentación: docs/DEVELOPER_GUIDE_PARTES.md
    """
    import warnings
    import logging
    import inspect
    
    # Obtener información del caller
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    line_number = frame.f_lineno
    function_name = frame.f_code.co_name
    
    # Log detallado para tracking
    logging.warning(
        f"LEGACY FUNCTION USAGE: get_partes_by_caso_id called from "
        f"{filename}:{line_number} in function '{function_name}'"
    )
    
    # Warning visible para el desarrollador
    warnings.warn(
        "get_partes_by_caso_id is deprecated. Use get_roles_by_caso_id instead. "
        "See docs/DEVELOPER_GUIDE_PARTES.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Mensaje detallado en consola
    print("\n" + "🚨" * 20)
    print("FUNCIÓN OBSOLETA DETECTADA: get_partes_by_caso_id")
    print("🚨" * 20)
    print(f"📍 Llamada desde: {filename}:{line_number}")
    print(f"📍 Función: {function_name}")
    print("\n📖 GUÍA DE MIGRACIÓN:")
    print("   Reemplazar por: get_roles_by_caso_id(caso_id)")
    print("   Incluye jerarquía: get_roles_by_caso_id(caso_id, incluir_jerarquia=True)")
    print("\n📚 Documentación: docs/DEVELOPER_GUIDE_PARTES.md")
    print("🚨" * 50 + "\n")
    
    return []

def get_parte_by_id(*args, **kwargs):
    """
    ⚠️ FUNCIÓN OBSOLETA - NO USAR EN CÓDIGO NUEVO ⚠️
    
    Esta función ha sido reemplazada por consultas más eficientes usando
    get_roles_by_caso_id o búsquedas directas por ID.
    
    MIGRACIÓN REQUERIDA:
    ==================
    
    ANTES (obsoleto):
    parte = get_parte_by_id(parte_id)
    
    DESPUÉS (nuevo sistema):
    # Opción 1: Si tienes el caso_id
    roles = get_roles_by_caso_id(caso_id)
    rol = next((r for r in roles if r['id'] == rol_id), None)
    
    # Opción 2: Consulta directa (más eficiente)
    rol = execute_query('''
        SELECT r.*, c.* FROM roles_en_caso r
        JOIN contactos c ON r.contacto_id = c.id
        WHERE r.id = ?
    ''', (rol_id,))
    
    # Opción 3: Para contactos
    contacto = get_contacto_by_id(contacto_id)
    
    BENEFICIOS DEL NUEVO SISTEMA:
    - Consultas más eficientes
    - Datos jerárquicos incluidos
    - Mejor separación de responsabilidades
    
    Ver documentación: docs/DEVELOPER_GUIDE_PARTES.md
    """
    import warnings
    import logging
    import inspect
    
    # Obtener información del caller
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    line_number = frame.f_lineno
    function_name = frame.f_code.co_name
    
    # Log detallado para tracking
    logging.warning(
        f"LEGACY FUNCTION USAGE: get_parte_by_id called from "
        f"{filename}:{line_number} in function '{function_name}'"
    )
    
    # Warning visible para el desarrollador
    warnings.warn(
        "get_parte_by_id is deprecated. Use get_roles_by_caso_id or direct queries instead. "
        "See docs/DEVELOPER_GUIDE_PARTES.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Mensaje detallado en consola
    print("\n" + "🚨" * 20)
    print("FUNCIÓN OBSOLETA DETECTADA: get_parte_by_id")
    print("🚨" * 20)
    print(f"📍 Llamada desde: {filename}:{line_number}")
    print(f"📍 Función: {function_name}")
    print("\n📖 GUÍA DE MIGRACIÓN:")
    print("   Para roles: get_roles_by_caso_id(caso_id)")
    print("   Para contactos: get_contacto_by_id(contacto_id)")
    print("   Para consulta directa: usar execute_query con JOIN")
    print("\n📚 Documentación: docs/DEVELOPER_GUIDE_PARTES.md")
    print("🚨" * 50 + "\n")
    
    return None

def update_parte_interviniente(*args, **kwargs):
    """
    ⚠️ FUNCIÓN OBSOLETA - NO USAR EN CÓDIGO NUEVO ⚠️
    
    Esta función ha sido reemplazada por funciones especializadas que separan
    la actualización de datos del contacto y del rol.
    
    MIGRACIÓN REQUERIDA:
    ==================
    
    ANTES (obsoleto):
    success = update_parte_interviniente(parte_id, {
        'nombre': 'Juan Pérez Actualizado',
        'email': 'nuevo@example.com',
        'tipo': 'Actor',
        'datos_bancarios': 'CBU: 123456'
    })
    
    DESPUÉS (nuevo sistema):
    # 1. Actualizar datos del contacto
    success_contacto = update_contacto(contacto_id, {
        'nombre_completo': 'Juan Pérez Actualizado',
        'email': 'nuevo@example.com'
    })
    
    # 2. Actualizar datos específicos del rol
    success_rol = update_rol(rol_id, {
        'rol_principal': 'Actor',
        'datos_bancarios': 'CBU: 123456'
    })
    
    VENTAJAS DEL NUEVO SISTEMA:
    - Separación clara entre datos del contacto y del rol
    - Actualizaciones más granulares y eficientes
    - Mejor control de validaciones
    - Cambios en contacto se reflejan en todos sus roles
    
    Ver documentación: docs/DEVELOPER_GUIDE_PARTES.md
    """
    import warnings
    import logging
    import inspect
    
    # Obtener información del caller
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    line_number = frame.f_lineno
    function_name = frame.f_code.co_name
    
    # Log detallado para tracking
    logging.warning(
        f"LEGACY FUNCTION USAGE: update_parte_interviniente called from "
        f"{filename}:{line_number} in function '{function_name}'"
    )
    
    # Warning visible para el desarrollador
    warnings.warn(
        "update_parte_interviniente is deprecated. Use update_contacto + update_rol instead. "
        "See docs/DEVELOPER_GUIDE_PARTES.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Mensaje detallado en consola
    print("\n" + "🚨" * 20)
    print("FUNCIÓN OBSOLETA DETECTADA: update_parte_interviniente")
    print("🚨" * 20)
    print(f"📍 Llamada desde: {filename}:{line_number}")
    print(f"📍 Función: {function_name}")
    print("\n📖 GUÍA DE MIGRACIÓN:")
    print("   Para datos del contacto: update_contacto(contacto_id, datos)")
    print("   Para datos del rol: update_rol(rol_id, datos)")
    print("\n📚 Documentación: docs/DEVELOPER_GUIDE_PARTES.md")
    print("🚨" * 50 + "\n")
    
    return False

def delete_parte_interviniente(*args, **kwargs):
    """
    ⚠️ FUNCIÓN OBSOLETA - NO USAR EN CÓDIGO NUEVO ⚠️
    
    Esta función ha sido reemplazada por funciones más específicas que permiten
    eliminar roles o contactos de manera granular.
    
    MIGRACIÓN REQUERIDA:
    ==================
    
    ANTES (obsoleto):
    success = delete_parte_interviniente(parte_id)
    
    DESPUÉS (nuevo sistema):
    # Opción 1: Eliminar solo el rol del caso (más común)
    success = delete_rol(rol_id)
    # El contacto se mantiene para reutilización en otros casos
    
    # Opción 2: Eliminar contacto completamente (¡CUIDADO!)
    # Esto eliminará el contacto y TODOS sus roles en TODOS los casos
    success = delete_contacto(contacto_id)
    
    # Opción 3: Verificar antes de eliminar
    roles_contacto = execute_query('''
        SELECT COUNT(*) FROM roles_en_caso WHERE contacto_id = ?
    ''', (contacto_id,))[0][0]
    
    if roles_contacto == 1:
        # Solo tiene un rol, seguro eliminar contacto
        delete_contacto(contacto_id)
    else:
        # Tiene múltiples roles, solo eliminar este rol
        delete_rol(rol_id)
    
    IMPORTANTE:
    - delete_rol(): Elimina solo la participación en un caso específico
    - delete_contacto(): Elimina el contacto y TODOS sus roles
    
    Ver documentación: docs/DEVELOPER_GUIDE_PARTES.md
    """
    import warnings
    import logging
    import inspect
    
    # Obtener información del caller
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    line_number = frame.f_lineno
    function_name = frame.f_code.co_name
    
    # Log detallado para tracking
    logging.warning(
        f"LEGACY FUNCTION USAGE: delete_parte_interviniente called from "
        f"{filename}:{line_number} in function '{function_name}'"
    )
    
    # Warning visible para el desarrollador
    warnings.warn(
        "delete_parte_interviniente is deprecated. Use delete_rol or delete_contacto instead. "
        "See docs/DEVELOPER_GUIDE_PARTES.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Mensaje detallado en consola
    print("\n" + "🚨" * 20)
    print("FUNCIÓN OBSOLETA DETECTADA: delete_parte_interviniente")
    print("🚨" * 20)
    print(f"📍 Llamada desde: {filename}:{line_number}")
    print(f"📍 Función: {function_name}")
    print("\n📖 GUÍA DE MIGRACIÓN:")
    print("   Para eliminar rol: delete_rol(rol_id)")
    print("   Para eliminar contacto: delete_contacto(contacto_id)")
    print("   ⚠️  CUIDADO: delete_contacto elimina TODOS los roles del contacto")
    print("\n📚 Documentación: docs/DEVELOPER_GUIDE_PARTES.md")
    print("🚨" * 50 + "\n")
    
    return False


# --- Utilidades para Tracking de Funciones Legacy ---

def get_legacy_function_usage_report():
    """
    Genera un reporte de uso de funciones legacy basado en los logs.
    
    Returns:
        dict: Reporte con estadísticas de uso de funciones obsoletas
    """
    import logging
    import os
    from collections import defaultdict
    from datetime import datetime
    
    # Buscar logs de funciones legacy
    legacy_usage = defaultdict(list)
    
    # Intentar leer logs recientes
    log_files = ['debug_log.txt', 'app.log', 'crm.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'LEGACY FUNCTION USAGE:' in line:
                            # Extraer información del log
                            parts = line.split('LEGACY FUNCTION USAGE: ')
                            if len(parts) > 1:
                                function_info = parts[1].strip()
                                function_name = function_info.split(' called from')[0]
                                legacy_usage[function_name].append(line.strip())
            except Exception as e:
                logging.warning(f"Error leyendo log {log_file}: {e}")
    
    # Generar reporte
    report = {
        'timestamp': datetime.now().isoformat(),
        'legacy_functions_detected': len(legacy_usage),
        'total_calls': sum(len(calls) for calls in legacy_usage.values()),
        'functions': {}
    }
    
    for function_name, calls in legacy_usage.items():
        report['functions'][function_name] = {
            'call_count': len(calls),
            'recent_calls': calls[-5:],  # Últimas 5 llamadas
            'migration_priority': 'HIGH' if len(calls) > 10 else 'MEDIUM' if len(calls) > 3 else 'LOW'
        }
    
    return report


def log_legacy_usage_summary():
    """
    Imprime un resumen del uso de funciones legacy.
    """
    report = get_legacy_function_usage_report()
    
    print("\n" + "📊" * 20)
    print("REPORTE DE FUNCIONES LEGACY")
    print("📊" * 20)
    print(f"Fecha: {report['timestamp']}")
    print(f"Funciones legacy detectadas: {report['legacy_functions_detected']}")
    print(f"Total de llamadas: {report['total_calls']}")
    
    if report['functions']:
        print("\nFUNCIONES MÁS USADAS:")
        sorted_functions = sorted(
            report['functions'].items(), 
            key=lambda x: x[1]['call_count'], 
            reverse=True
        )
        
        for func_name, data in sorted_functions:
            priority_emoji = "🔴" if data['migration_priority'] == 'HIGH' else "🟡" if data['migration_priority'] == 'MEDIUM' else "🟢"
            print(f"  {priority_emoji} {func_name}: {data['call_count']} llamadas ({data['migration_priority']} priority)")
    
    print("\n📚 Para migrar estas funciones, consultar:")
    print("   docs/DEVELOPER_GUIDE_PARTES.md")
    print("📊" * 50 + "\n")


def create_legacy_migration_guide():
    """
    Crea una guía de migración personalizada basada en el uso actual.
    """
    report = get_legacy_function_usage_report()
    
    if not report['functions']:
        print("✅ No se detectaron funciones legacy en uso.")
        return
    
    guide_content = f"""# Guía de Migración Personalizada
Generada automáticamente el {report['timestamp']}

## Resumen
- Funciones legacy detectadas: {report['legacy_functions_detected']}
- Total de llamadas: {report['total_calls']}

## Funciones a Migrar (por prioridad)

"""
    
    # Ordenar por prioridad y frecuencia
    sorted_functions = sorted(
        report['functions'].items(),
        key=lambda x: (
            {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[x[1]['migration_priority']],
            x[1]['call_count']
        ),
        reverse=True
    )
    
    for func_name, data in sorted_functions:
        priority_icon = "🔴" if data['migration_priority'] == 'HIGH' else "🟡" if data['migration_priority'] == 'MEDIUM' else "🟢"
        
        guide_content += f"""### {priority_icon} {func_name}
- **Prioridad**: {data['migration_priority']}
- **Llamadas detectadas**: {data['call_count']}
- **Migración**: Ver docs/DEVELOPER_GUIDE_PARTES.md

"""
    
    guide_content += """
## Próximos Pasos
1. Revisar cada función marcada como HIGH priority
2. Consultar la documentación técnica para patrones de migración
3. Actualizar el código usando las nuevas funciones
4. Probar exhaustivamente después de cada migración
5. Ejecutar este reporte nuevamente para verificar progreso

Para más detalles, consultar: docs/DEVELOPER_GUIDE_PARTES.md
"""
    
    # Guardar guía
    try:
        with open('MIGRATION_GUIDE_CUSTOM.md', 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print(f"📝 Guía de migración personalizada creada: MIGRATION_GUIDE_CUSTOM.md")
    except Exception as e:
        print(f"Error creando guía: {e}")
        print("Contenido de la guía:")
        print(guide_content)

# --- Funciones de Utilidad para Migración ---

def get_legacy_usage_stats():
    """
    Devuelve estadísticas sobre el uso de funciones obsoletas.
    Útil para monitorear el progreso de la migración.
    """
    # Esta función podría expandirse para leer logs o contadores
    return {
        'message': 'Monitoreo de funciones obsoletas activo',
        'recommendation': 'Migrar a las nuevas funciones CRUD para contactos y roles'
    }

def validate_database_schema():
    """
    Valida que el esquema de la base de datos tenga las tablas necesarias
    para el nuevo modelo relacional.
    """
    conn = connect_db()
    if not conn:
        db_logger.error("No se pudo conectar a la base de datos para validar esquema")
        return False
    
    required_tables = ['contactos', 'roles_en_caso']
    missing_tables = []
    
    try:
        with conn.cursor() as cur:
            for table in required_tables:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (table,))
                exists = cur.fetchone()[0]
                if not exists:
                    missing_tables.append(table)
        
        if missing_tables:
            db_logger.error(f"Faltan las siguientes tablas: {missing_tables}")
            return False
        else:
            db_logger.info("[OK] Esquema de base de datos validado correctamente.")
            return True
            
    except (Exception, psycopg2.DatabaseError) as e:
        db_logger.error(f"Error validando esquema de base de datos: {e}")
        return False
    finally:
        conn.close()

def validate_database_connection():
    """
    Valida que la conexión a la base de datos funcione correctamente.
    Devuelve un diccionario con el estado de la validación.
    """
    validation_result = {
        'connection': False,
        'schema': False,
        'permissions': False,
        'errors': []
    }
    
    try:
        # Probar conexión básica
        conn = connect_db()
        if not conn:
            validation_result['errors'].append("No se pudo establecer conexión con la base de datos")
            return validation_result
        
        validation_result['connection'] = True
        
        with conn.cursor() as cur:
            # Probar permisos básicos
            try:
                cur.execute("SELECT 1")
                validation_result['permissions'] = True
            except Exception as e:
                validation_result['errors'].append(f"Error de permisos: {e}")
            
            # Validar esquema
            if validate_database_schema():
                validation_result['schema'] = True
            else:
                validation_result['errors'].append("Esquema de base de datos incompleto")
        
        conn.close()
        
    except Exception as e:
        validation_result['errors'].append(f"Error inesperado: {e}")
    
    return validation_result

# --- NUEVO MODELO RELACIONAL: Contactos y Roles ---

# --- Funciones CRUD para Contactos ---

def add_contacto(datos_contacto):
    """
    Agrega un nuevo contacto al directorio central con validación robusta.
    `datos_contacto` es un diccionario con las claves correspondientes a las columnas de la tabla `contactos`.
    Devuelve el ID del nuevo contacto o None si falla.
    """
    # Validación previa de entrada
    if not datos_contacto or not isinstance(datos_contacto, dict):
        db_logger.error("Error: datos_contacto debe ser un diccionario no vacío")
        return None
    
    # Validar campo obligatorio
    nombre = datos_contacto.get('nombre_completo', '').strip()
    if not nombre:
        db_logger.error("Error: El campo 'nombre_completo' es obligatorio y no puede estar vacío")
        return None
    
    # Validar longitud del nombre
    if len(nombre) < 2:
        db_logger.error("Error: El nombre debe tener al menos 2 caracteres")
        return None
    
    if len(nombre) > 255:
        db_logger.error("Error: El nombre no puede exceder 255 caracteres")
        return None
    
    # Validar formato de email si se proporciona
    email = datos_contacto.get('email', '').strip()
    if email and '@' not in email:
        db_logger.warning(f"Advertencia: El email '{email}' no parece tener un formato válido")
    
    # Validar DNI si se proporciona
    dni = datos_contacto.get('dni', '').strip()
    if dni and not dni.replace('.', '').replace('-', '').isdigit():
        db_logger.warning(f"Advertencia: El DNI '{dni}' contiene caracteres no numéricos")
    
    # Validar CUIT si se proporciona
    cuit = datos_contacto.get('cuit', '').strip()
    if cuit and not cuit.replace('-', '').isdigit():
        db_logger.warning(f"Advertencia: El CUIT '{cuit}' contiene caracteres no numéricos")

    conn = connect_db()
    new_id = None
    if not conn:
        db_logger.error("Error: No se pudo establecer conexión con la base de datos")
        return None
    
    try:
        # Filtrar solo las claves que pertenecen a la tabla
        columnas_validas = [
            'nombre_completo', 'es_persona_juridica', 'dni', 'cuit', 
            'domicilio_real', 'domicilio_legal', 'email', 'telefono', 'notas_generales'
        ]
        
        # Construir la consulta dinámicamente con datos limpios
        columnas = []
        valores = []
        
        for col in columnas_validas:
            if col in datos_contacto:
                valor = datos_contacto[col]
                # Limpiar strings
                if isinstance(valor, str):
                    valor = valor.strip()
                    # No agregar campos vacíos excepto nombre_completo
                    if valor or col == 'nombre_completo':
                        columnas.append(col)
                        valores.append(valor)
                else:
                    columnas.append(col)
                    valores.append(valor)

        columnas.append('created_at')
        valores.append(int(time.time()))
        
        sql = f"INSERT INTO contactos ({', '.join(columnas)}) VALUES ({', '.join(['%s'] * len(valores))}) RETURNING id;"

        with conn.cursor() as cur:
            cur.execute(sql, valores)
            new_id = cur.fetchone()[0]
            conn.commit()
            db_logger.info(f"Contacto '{nombre}' agregado exitosamente con ID: {new_id}")
            
    except psycopg2.IntegrityError as e:
        db_logger.error(f"Error de integridad al agregar contacto: {e}")
        conn.rollback()
    except psycopg2.DataError as e:
        db_logger.error(f"Error de datos al agregar contacto: {e}")
        conn.rollback()
    except (Exception, psycopg2.DatabaseError) as error:
        db_logger.error(f"Error inesperado al agregar contacto: {error}")
        conn.rollback()
    finally:
        conn.close()
        
    return new_id

def update_contacto(contacto_id, datos_contacto):
    """
    Actualiza un contacto existente.
    `datos_contacto` es un diccionario con las claves a actualizar.
    """
    conn = connect_db()
    success = False
    if not conn:
        return False

    columnas_validas = [
        'nombre_completo', 'es_persona_juridica', 'dni', 'cuit', 
        'domicilio_real', 'domicilio_legal', 'email', 'telefono', 'notas_generales'
    ]
    
    # Construir la cláusula SET dinámicamente
    set_parts = [f"{col} = %s" for col in datos_contacto if col in columnas_validas]
    valores = [datos_contacto[col] for col in datos_contacto if col in columnas_validas]
    
    if not set_parts:
        print("Advertencia: No se proporcionaron campos válidos para actualizar el contacto.")
        return False

    valores.append(contacto_id)
    sql = f"UPDATE contactos SET {', '.join(set_parts)} WHERE id = %s;"

    try:
        with conn.cursor() as cur:
            cur.execute(sql, valores)
            conn.commit()
            success = cur.rowcount > 0
            if success:
                db_logger.info(f"Contacto ID {contacto_id} actualizado correctamente.")
    except (Exception, psycopg2.DatabaseError) as error:
        db_logger.error(f"Error al actualizar contacto ID {contacto_id}: {error}")
        conn.rollback()
    finally:
        conn.close()
        
    return success

def search_contactos(termino_busqueda, filtros=None, limite=50):
    """
    Búsqueda avanzada de contactos con múltiples criterios y filtros.
    
    Args:
        termino_busqueda (str): Término de búsqueda principal
        filtros (dict): Filtros adicionales como {'es_persona_juridica': True, 'tiene_email': True}
        limite (int): Número máximo de resultados a devolver
    
    Returns:
        list: Lista de contactos encontrados
    """
    if not termino_busqueda or not isinstance(termino_busqueda, str):
        return []
    
    termino_busqueda = termino_busqueda.strip()
    if not termino_busqueda:
        return []

    conn = connect_db()
    contactos = []
    if not conn:
        db_logger.error("No se pudo conectar a la base de datos para búsqueda")
        return contactos

    try:
        # Verificar si es búsqueda por ID exacto
        if termino_busqueda.startswith('id:'):
            try:
                contacto_id = int(termino_busqueda[3:])
                contacto = get_contacto_by_id(contacto_id)
                return [contacto] if contacto else []
            except ValueError:
                db_logger.warning(f"ID inválido en búsqueda: {termino_busqueda}")
                return []

        # Construir consulta SQL dinámica
        where_conditions = []
        params = []
        
        # Búsqueda principal por texto
        search_conditions = [
            "nombre_completo ILIKE %s",
            "dni ILIKE %s", 
            "cuit ILIKE %s",
            "email ILIKE %s",
            "telefono ILIKE %s"
        ]
        
        # Búsqueda fuzzy mejorada
        param_like = f"%{termino_busqueda}%"
        param_start = f"{termino_busqueda}%"
        param_exact = termino_busqueda
        
        # Agregar condiciones de búsqueda principal
        where_conditions.append(f"({' OR '.join(search_conditions)})")
        params.extend([param_like, param_like, param_like, param_like, param_like])
        
        # Aplicar filtros adicionales
        if filtros:
            if 'es_persona_juridica' in filtros:
                where_conditions.append("es_persona_juridica = %s")
                params.append(filtros['es_persona_juridica'])
            
            if 'tiene_email' in filtros and filtros['tiene_email']:
                where_conditions.append("email IS NOT NULL AND email != ''")
            
            if 'tiene_telefono' in filtros and filtros['tiene_telefono']:
                where_conditions.append("telefono IS NOT NULL AND telefono != ''")
            
            if 'tiene_dni' in filtros and filtros['tiene_dni']:
                where_conditions.append("dni IS NOT NULL AND dni != ''")
            
            if 'tiene_cuit' in filtros and filtros['tiene_cuit']:
                where_conditions.append("cuit IS NOT NULL AND cuit != ''")

        # Construir consulta completa
        sql = f"""
            SELECT *, 
                   CASE 
                       WHEN nombre_completo ILIKE %s THEN 1
                       WHEN nombre_completo ILIKE %s THEN 2
                       WHEN dni = %s OR cuit = %s THEN 3
                       WHEN email ILIKE %s THEN 4
                       ELSE 5
                   END as relevancia_score
            FROM contactos 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY relevancia_score, nombre_completo
            LIMIT %s;
        """
        
        # Parámetros para el scoring de relevancia
        relevancia_params = [param_start, param_like, param_exact, param_exact, param_like]
        all_params = relevancia_params + params + [limite]

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, all_params)
            rows = cur.fetchall()
            contactos = [dict(row) for row in rows]
            
        db_logger.info(f"Búsqueda de contactos: '{termino_busqueda}' - {len(contactos)} resultados")
        
    except (Exception, psycopg2.DatabaseError) as e:
        db_logger.error(f"Error al buscar contactos: {e}")
    finally:
        conn.close()
        
    return contactos

def search_contactos_fuzzy(termino_busqueda, umbral_similitud=0.3):
    """
    Búsqueda fuzzy de contactos usando similitud de texto.
    Útil para encontrar contactos con nombres similares o con errores tipográficos.
    """
    if not termino_busqueda or len(termino_busqueda) < 2:
        return []

    conn = connect_db()
    contactos = []
    if not conn:
        return contactos

    try:
        # Usar la extensión pg_trgm si está disponible para búsqueda fuzzy
        sql = """
            SELECT *, 
                   similarity(nombre_completo, %s) as similitud_nombre,
                   similarity(COALESCE(email, ''), %s) as similitud_email
            FROM contactos 
            WHERE similarity(nombre_completo, %s) > %s
               OR similarity(COALESCE(email, ''), %s) > %s
               OR nombre_completo ILIKE %s
            ORDER BY 
                GREATEST(
                    similarity(nombre_completo, %s),
                    similarity(COALESCE(email, ''), %s)
                ) DESC,
                nombre_completo
            LIMIT 20;
        """
        
        param_like = f"%{termino_busqueda}%"
        params = [
            termino_busqueda, termino_busqueda,  # Para similarity
            termino_busqueda, umbral_similitud,  # Umbral nombre
            termino_busqueda, umbral_similitud,  # Umbral email
            param_like,  # ILIKE fallback
            termino_busqueda, termino_busqueda   # Para ORDER BY
        ]

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            contactos = [dict(row) for row in rows]
            
    except psycopg2.Error as e:
        # Si pg_trgm no está disponible, usar búsqueda normal
        db_logger.warning(f"Búsqueda fuzzy no disponible, usando búsqueda normal: {e}")
        return search_contactos(termino_busqueda)
    except Exception as e:
        db_logger.error(f"Error en búsqueda fuzzy: {e}")
    finally:
        conn.close()
        
    return contactos

def get_contactos_recientes(limite=10):
    """
    Obtiene los contactos creados más recientemente.
    Útil para mostrar contactos recientes en la interfaz.
    """
    conn = connect_db()
    contactos = []
    if not conn:
        return contactos

    try:
        sql = """
            SELECT * FROM contactos 
            ORDER BY created_at DESC 
            LIMIT %s;
        """

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limite,))
            rows = cur.fetchall()
            contactos = [dict(row) for row in rows]
            
    except (Exception, psycopg2.DatabaseError) as e:
        db_logger.error(f"Error al obtener contactos recientes: {e}")
    finally:
        conn.close()
        
    return contactos

def get_contactos_mas_usados(limite=10):
    """
    Obtiene los contactos que más se usan en casos (tienen más roles asignados).
    """
    conn = connect_db()
    contactos = []
    if not conn:
        return contactos

    try:
        sql = """
            SELECT c.*, COUNT(r.id) as total_roles
            FROM contactos c
            LEFT JOIN roles_en_caso r ON c.id = r.contacto_id
            GROUP BY c.id
            ORDER BY total_roles DESC, c.nombre_completo
            LIMIT %s;
        """

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limite,))
            rows = cur.fetchall()
            contactos = [dict(row) for row in rows]
            
    except (Exception, psycopg2.DatabaseError) as e:
        db_logger.error(f"Error al obtener contactos más usados: {e}")
    finally:
        conn.close()
        
    return contactos

def get_contacto_by_id(contacto_id):
    """
    Obtiene un contacto específico por su ID.
    Devuelve un diccionario con los datos del contacto o None si no se encuentra.
    """
    conn = connect_db()
    contacto_data = None
    if not conn:
        return None

    sql = "SELECT * FROM contactos WHERE id = %s;"
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (contacto_id,))
            row = cur.fetchone()
            if row:
                contacto_data = dict(row)
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error al obtener contacto por ID {contacto_id}: {e}")
    finally:
        conn.close()
        
    return contacto_data

def delete_contacto(contacto_id):
    """
    Elimina un contacto del directorio central.
    ADVERTENCIA: Esto también eliminará todos los roles asociados debido a CASCADE.
    """
    conn = connect_db()
    success = False
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            # Verificar si el contacto tiene roles activos
            cur.execute("SELECT COUNT(*) FROM roles_en_caso WHERE contacto_id = %s", (contacto_id,))
            roles_count = cur.fetchone()[0]
            
            if roles_count > 0:
                print(f"ADVERTENCIA: El contacto ID {contacto_id} tiene {roles_count} roles activos que serán eliminados.")
            
            cur.execute("DELETE FROM contactos WHERE id = %s", (contacto_id,))
            conn.commit()
            success = cur.rowcount > 0
            if success:
                print(f"Contacto ID {contacto_id} eliminado correctamente.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al eliminar contacto ID {contacto_id}: {error}")
        conn.rollback()
    finally:
        conn.close()
        
    return success

def count_casos_por_contacto_id(contacto_id):
    """
    Cuenta el número total de casos distintos donde aparece un contacto.
    
    Args:
        contacto_id (int): ID del contacto para contar casos
        
    Returns:
        int: Número de casos distintos, 0 si no se encuentra ninguno o en caso de error
    """
    if not contacto_id:
        return 0
        
    conn = connect_db()
    if not conn:
        return 0

    sql = """
        SELECT COUNT(DISTINCT r.caso_id) 
        FROM roles_en_caso r 
        WHERE r.contacto_id = %s
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (contacto_id,))
            result = cur.fetchone()
            return result[0] if result else 0
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error al contar casos para contacto ID {contacto_id}: {e}")
        return 0
    finally:
        conn.close()

def get_casos_y_roles_por_contacto_id(contacto_id):
    """
    Obtiene todos los casos y roles para un contacto específico.
    
    Args:
        contacto_id (int): ID del contacto para obtener casos
        
    Returns:
        list: Lista de diccionarios con información de casos y roles.
              Cada diccionario contiene: caso_id, caratula, numero_expediente,
              rol_principal, rol_secundario, notas_del_rol
    """
    if not contacto_id:
        return []
        
    conn = connect_db()
    if not conn:
        return []

    sql = """
        SELECT 
            r.caso_id,
            c.caratula,
            c.numero_expediente,
            r.rol_principal,
            r.rol_secundario,
            r.notas_del_rol
        FROM roles_en_caso r
        JOIN casos c ON r.caso_id = c.id
        WHERE r.contacto_id = %s
        ORDER BY c.caratula, r.rol_principal
    """
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (contacto_id,))
            rows = cur.fetchall()
            return [dict(row) for row in rows] if rows else []
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error al obtener casos y roles para contacto ID {contacto_id}: {e}")
        return []
    finally:
        conn.close()

# --- Funciones para Representación Múltiple ---

def is_multiple_representation_role(rol_data):
    """
    Determina si un rol es parte de una representación múltiple.
    
    Args:
        rol_data (dict): Datos del rol
        
    Returns:
        bool: True si es parte de una representación múltiple
    """
    # Un rol es de representación múltiple si:
    # 1. Es abogado o apoderado
    # 2. Tiene notas que indican representación múltiple
    # 3. O si hay otros roles del mismo contacto en el mismo caso
    
    if not rol_data:
        return False
    
    rol_principal = rol_data.get('rol_principal', '')
    if rol_principal not in ['Abogado', 'Apoderado']:
        return False
    
    # Verificar si las notas indican representación múltiple
    notas = rol_data.get('notas_del_rol', '') or ''
    if 'REPRESENTACION_MULTIPLE' in notas.upper():
        return True
    
    return False

def validate_multiple_representation_consistency(caso_id):
    """
    Valida la consistencia de las representaciones múltiples en un caso.
    Retorna un diccionario con errores encontrados y sugerencias de corrección.
    """
    conn = connect_db()
    if not conn:
        return {'error': 'No se pudo conectar a la base de datos'}
    
    validation_results = {
        'errors': [],
        'warnings': [],
        'orphaned_representations': [],
        'inconsistent_groups': [],
        'suggestions': []
    }
    
    try:
        with conn.cursor() as cur:
            # Obtener todos los roles del caso
            cur.execute("""
                SELECT r.id, r.contacto_id, r.rol_principal, r.notas_del_rol, r.representa_a_id,
                       c.nombre_completo
                FROM roles_en_caso r
                JOIN contactos c ON r.contacto_id = c.id
                WHERE r.caso_id = %s
            """, (caso_id,))
            
            roles = cur.fetchall()
            
            # Analizar representaciones múltiples
            multiple_rep_groups = {}
            orphaned_reps = []
            
            for rol_id, contacto_id, rol_principal, notas, representa_a_id, nombre in roles:
                notas = notas or ''
                
                # Verificar representaciones múltiples
                if 'REPRESENTACION_MULTIPLE' in notas:
                    import re
                    group_match = re.search(r'REPRESENTACION_MULTIPLE:([^:]+):([^]]+)', notas)
                    
                    if group_match:
                        rep_type = group_match.group(1)  # PRIMARY o SECONDARY
                        group_id = group_match.group(2)
                        
                        if group_id not in multiple_rep_groups:
                            multiple_rep_groups[group_id] = {
                                'primary': None,
                                'secondary': [],
                                'lawyer_name': None
                            }
                        
                        if rep_type == 'PRIMARY':
                            if multiple_rep_groups[group_id]['primary'] is not None:
                                validation_results['errors'].append(
                                    f"Grupo {group_id}: Múltiples roles PRIMARY encontrados"
                                )
                            multiple_rep_groups[group_id]['primary'] = rol_id
                            multiple_rep_groups[group_id]['lawyer_name'] = nombre
                        elif rep_type == 'SECONDARY':
                            multiple_rep_groups[group_id]['secondary'].append(rol_id)
                    else:
                        validation_results['warnings'].append(
                            f"Rol {rol_id} ({nombre}): Nota de representación múltiple malformada"
                        )
                
                # Verificar representaciones huérfanas
                if representa_a_id:
                    # Verificar que el rol representado existe
                    represented_exists = any(r[0] == representa_a_id for r in roles)
                    if not represented_exists:
                        orphaned_reps.append({
                            'rol_id': rol_id,
                            'nombre': nombre,
                            'representa_a_id_inexistente': representa_a_id
                        })
            
            # Validar grupos de representación múltiple
            for group_id, group_data in multiple_rep_groups.items():
                if group_data['primary'] is None:
                    validation_results['errors'].append(
                        f"Grupo {group_id}: No se encontró rol PRIMARY"
                    )
                
                if not group_data['secondary']:
                    validation_results['warnings'].append(
                        f"Grupo {group_id}: No hay roles SECONDARY (representación múltiple sin representados)"
                    )
            
            # Registrar representaciones huérfanas
            validation_results['orphaned_representations'] = orphaned_reps
            
            # Generar sugerencias
            if orphaned_reps:
                validation_results['suggestions'].append(
                    "Ejecutar limpieza de representaciones huérfanas con clean_orphaned_representations()"
                )
            
            if validation_results['errors']:
                validation_results['suggestions'].append(
                    "Revisar y corregir manualmente los grupos de representación múltiple inconsistentes"
                )
    
    except Exception as e:
        validation_results['error'] = f"Error durante validación: {str(e)}"
    finally:
        conn.close()
    
    return validation_results

def clean_orphaned_representations(caso_id):
    """
    Limpia representaciones huérfanas en un caso específico.
    """
    conn = connect_db()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Limpiar representa_a_id que apuntan a roles inexistentes
            cur.execute("""
                UPDATE roles_en_caso 
                SET representa_a_id = NULL 
                WHERE caso_id = %s 
                AND representa_a_id NOT IN (
                    SELECT id FROM roles_en_caso WHERE caso_id = %s
                )
            """, (caso_id, caso_id))
            
            cleaned_count = cur.rowcount
            conn.commit()
            
            print(f"Limpiadas {cleaned_count} representaciones huérfanas en caso {caso_id}")
            return True
            
    except Exception as e:
        print(f"Error limpiando representaciones huérfanas: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def fix_duplicate_multiple_representations(caso_id):
    """
    Corrige representaciones múltiples duplicadas en un caso específico.
    Convierte múltiples roles del mismo abogado en un rol principal + roles shadow.
    """
    conn = connect_db()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Encontrar abogados con múltiples roles en el mismo caso
            cur.execute("""
                SELECT contacto_id, COUNT(*) as role_count
                FROM roles_en_caso 
                WHERE caso_id = %s 
                AND rol_principal IN ('Abogado', 'Apoderado')
                GROUP BY contacto_id
                HAVING COUNT(*) > 1
            """, (caso_id,))
            
            duplicate_lawyers = cur.fetchall()
            
            if not duplicate_lawyers:
                print(f"No se encontraron representaciones múltiples duplicadas en caso {caso_id}")
                return True
            
            print(f"Encontrados {len(duplicate_lawyers)} abogados con roles duplicados en caso {caso_id}")
            
            for contacto_id, role_count in duplicate_lawyers:
                print(f"Corrigiendo abogado contacto_id {contacto_id} con {role_count} roles")
                
                # Obtener todos los roles de este abogado en el caso
                cur.execute("""
                    SELECT id, rol_principal, rol_secundario, representa_a_id, notas_del_rol
                    FROM roles_en_caso 
                    WHERE caso_id = %s AND contacto_id = %s
                    ORDER BY id
                """, (caso_id, contacto_id))
                
                lawyer_roles = cur.fetchall()
                
                if len(lawyer_roles) <= 1:
                    continue
                
                # Usar el primer rol como principal
                primary_role = lawyer_roles[0]
                primary_id, rol_principal, rol_secundario, _, notas_existentes = primary_role
                
                # Generar group_id
                group_id = get_representation_group_id(contacto_id, caso_id)
                
                # Recopilar información de representaciones
                represented_parties = []
                roles_to_delete = []
                
                for role_id, _, _, representa_a_id, _ in lawyer_roles:
                    if representa_a_id:
                        # Obtener información de la parte representada
                        cur.execute("""
                            SELECT r.id, c.nombre_completo, r.rol_principal
                            FROM roles_en_caso r
                            JOIN contactos c ON r.contacto_id = c.id
                            WHERE r.id = %s
                        """, (representa_a_id,))
                        
                        party_info = cur.fetchone()
                        if party_info:
                            represented_parties.append({
                                'party_id': representa_a_id,
                                'party_name': party_info[1],
                                'party_role': party_info[2]
                            })
                    
                    # Marcar roles secundarios para eliminación
                    if role_id != primary_id:
                        roles_to_delete.append(role_id)
                
                if not represented_parties:
                    print(f"No se encontraron representaciones para contacto_id {contacto_id}")
                    continue
                
                # Actualizar el rol principal
                notas_representacion = f"[REPRESENTACION_MULTIPLE:PRIMARY:{group_id}]\n"
                notas_representacion += f"Representa a {len(represented_parties)} parte(s):\n"
                
                for party in represented_parties:
                    notas_representacion += f"- {party['party_name']} ({party['party_role']}) [ID:{party['party_id']}]\n"
                
                new_notas = f"{notas_existentes or ''}\n{notas_representacion}".strip()
                
                cur.execute("""
                    UPDATE roles_en_caso 
                    SET representa_a_id = NULL, notas_del_rol = %s
                    WHERE id = %s
                """, (new_notas, primary_id))
                
                # Crear roles shadow
                for party in represented_parties:
                    shadow_data = {
                        'caso_id': caso_id,
                        'contacto_id': contacto_id,
                        'rol_principal': rol_principal,
                        'rol_secundario': rol_secundario,
                        'representa_a_id': party['party_id'],
                        'notas_del_rol': f"[REPRESENTACION_MULTIPLE:SECONDARY:{group_id}] Shadow role for {party['party_name']}"
                    }
                    
                    shadow_role_id = add_rol_a_caso(shadow_data)
                    if shadow_role_id:
                        print(f"Creado rol shadow {shadow_role_id} para {party['party_name']}")
                
                # Eliminar roles duplicados
                for role_id in roles_to_delete:
                    cur.execute("DELETE FROM roles_en_caso WHERE id = %s", (role_id,))
                    print(f"Eliminado rol duplicado {role_id}")
                
                print(f"Corregido abogado contacto_id {contacto_id}: 1 rol principal + {len(represented_parties)} roles shadow")
            
            conn.commit()
            print(f"Corrección completada para caso {caso_id}")
            return True
            
    except Exception as e:
        print(f"Error corrigiendo representaciones duplicadas: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_representation_group_id(contacto_id, caso_id):
    """
    Genera un ID único para un grupo de representación múltiple.
    
    Args:
        contacto_id (int): ID del contacto (abogado)
        caso_id (int): ID del caso
        
    Returns:
        str: ID único del grupo de representación
    """
    import time
    timestamp = int(time.time())
    return f"multi_rep_{contacto_id}_{caso_id}_{timestamp}"

def get_multiple_representations_for_lawyer(contacto_id, caso_id):
    """
    Obtiene todas las representaciones de un abogado en un caso específico.
    
    Args:
        contacto_id (int): ID del contacto (abogado)
        caso_id (int): ID del caso
        
    Returns:
        list: Lista de roles que representa este abogado
    """
    if not contacto_id or not caso_id:
        return []
        
    conn = connect_db()
    if not conn:
        return []

    sql = """
        SELECT 
            r.id as rol_id,
            r.representa_a_id,
            represented.rol_principal as represented_role,
            represented.rol_secundario as represented_secondary_role,
            c.nombre_completo as represented_name
        FROM roles_en_caso r
        LEFT JOIN roles_en_caso represented ON r.representa_a_id = represented.id
        LEFT JOIN contactos c ON represented.contacto_id = c.id
        WHERE r.contacto_id = %s 
        AND r.caso_id = %s 
        AND r.rol_principal IN ('Abogado', 'Apoderado')
        AND r.representa_a_id IS NOT NULL
        ORDER BY represented.rol_principal, c.nombre_completo
    """
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (contacto_id, caso_id))
            rows = cur.fetchall()
            return [dict(row) for row in rows] if rows else []
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error al obtener representaciones múltiples para contacto {contacto_id} en caso {caso_id}: {e}")
        return []
    finally:
        conn.close()

def detect_multiple_representations_in_case(caso_id):
    """
    Detecta todos los casos de representación múltiple en un caso basándose en las notas del rol.
    Funciona con la nueva estructura donde hay un rol principal y roles shadow.
    
    Args:
        caso_id (int): ID del caso
        
    Returns:
        dict: Diccionario con contacto_id como clave y lista de representaciones como valor
    """
    if not caso_id:
        return {}
        
    conn = connect_db()
    if not conn:
        return {}

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Buscar roles principales de representación múltiple
            cur.execute("""
                SELECT 
                    r.contacto_id,
                    r.id as rol_id,
                    r.rol_principal,
                    r.notas_del_rol,
                    c.nombre_completo as lawyer_name
                FROM roles_en_caso r
                JOIN contactos c ON r.contacto_id = c.id
                WHERE r.caso_id = %s
                AND r.rol_principal IN ('Abogado', 'Apoderado')
                AND r.notas_del_rol LIKE '%REPRESENTACION_MULTIPLE:PRIMARY:%'
            """, (caso_id,))
            
            primary_roles = cur.fetchall()
            multiple_reps = {}
            
            for primary_role in primary_roles:
                contacto_id = primary_role['contacto_id']
                notas = primary_role['notas_del_rol'] or ''
                
                # Extraer group_id
                import re
                group_match = re.search(r'REPRESENTACION_MULTIPLE:PRIMARY:([^]]+)', notas)
                if not group_match:
                    continue
                
                group_id = group_match.group(1)
                
                # Buscar roles shadow asociados a este grupo
                cur.execute("""
                    SELECT 
                        r.id as shadow_rol_id,
                        r.representa_a_id,
                        represented.rol_principal as represented_role,
                        represented_contact.nombre_completo as represented_name
                    FROM roles_en_caso r
                    LEFT JOIN roles_en_caso represented ON r.representa_a_id = represented.id
                    LEFT JOIN contactos represented_contact ON represented.contacto_id = represented_contact.id
                    WHERE r.caso_id = %s 
                    AND r.contacto_id = %s
                    AND r.notas_del_rol LIKE %s
                """, (caso_id, contacto_id, f'%REPRESENTACION_MULTIPLE:SECONDARY:{group_id}%'))
                
                shadow_roles = cur.fetchall()
                
                # Construir lista de representaciones
                representations = []
                for shadow in shadow_roles:
                    if shadow['representa_a_id'] and shadow['represented_name']:
                        representations.append({
                            'rol_id': shadow['shadow_rol_id'],
                            'represented_role': shadow['represented_role'],
                            'represented_name': shadow['represented_name'],
                            'represents_id': shadow['representa_a_id'],
                            'is_secondary': True
                        })
                
                # Si no hay roles shadow, intentar extraer de las notas del rol principal
                if not representations:
                    # Parsear las notas para extraer representaciones
                    lines = notas.split('\n')
                    for line in lines:
                        if '[ID:' in line and ']' in line:
                            # Extraer información de la línea como "- Nombre (Rol) [ID:123]"
                            match = re.search(r'-\s*(.+?)\s*\((.+?)\)\s*\[ID:(\d+)\]', line)
                            if match:
                                name, role, party_id = match.groups()
                                representations.append({
                                    'rol_id': primary_role['rol_id'],
                                    'represented_role': role.strip(),
                                    'represented_name': name.strip(),
                                    'represents_id': int(party_id),
                                    'is_secondary': False
                                })
                
                if representations:
                    multiple_reps[contacto_id] = {
                        'lawyer_name': primary_role['lawyer_name'],
                        'representations': representations,
                        'is_multiple': True,
                        'primary_role_id': primary_role['rol_id'],
                        'group_id': group_id
                    }
            
            return multiple_reps
            
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error al detectar representaciones múltiples en caso {caso_id}: {e}")
        return {}
    finally:
        conn.close()

def validate_multiple_representation_request(contacto_id, caso_id, represented_party_ids):
    """
    Valida una solicitud de representación múltiple.
    
    Args:
        contacto_id (int): ID del contacto (abogado)
        caso_id (int): ID del caso
        represented_party_ids (list): Lista de IDs de roles a representar
        
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    if not contacto_id:
        errors.append("ID de contacto requerido")
    
    if not caso_id:
        errors.append("ID de caso requerido")
    
    if not represented_party_ids or len(represented_party_ids) < 1:
        errors.append("Debe seleccionar al menos una parte para representar")
    
    if len(represented_party_ids) < 2:
        errors.append("Para representación múltiple, debe seleccionar al menos 2 partes")
    
    # Validar que las partes existen y son representables
    if represented_party_ids:
        conn = connect_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Verificar que todos los roles existen en el caso
                    placeholders = ','.join(['%s'] * len(represented_party_ids))
                    sql = f"""
                        SELECT id, rol_principal, contacto_id
                        FROM roles_en_caso 
                        WHERE id IN ({placeholders}) AND caso_id = %s
                    """
                    cur.execute(sql, represented_party_ids + [caso_id])
                    existing_roles = cur.fetchall()
                    
                    if len(existing_roles) != len(represented_party_ids):
                        errors.append("Algunos roles seleccionados no existen en este caso")
                    
                    # Verificar que son roles representables
                    for role in existing_roles:
                        if role[1] not in ['Actor', 'Demandado', 'Tercero']:
                            errors.append(f"No se puede representar a un {role[1]}")
                        
                        # Verificar que no se está auto-representando
                        if role[2] == contacto_id:
                            errors.append("Un abogado no puede representarse a sí mismo")
                            
            except Exception as e:
                errors.append(f"Error al validar roles: {str(e)}")
            finally:
                conn.close()
    
    return len(errors) == 0, errors

def create_multiple_representations(contacto_id, caso_id, rol_data, represented_party_ids):
    """
    Crea un abogado con representaciones múltiples usando UN SOLO ROL.
    
    Args:
        contacto_id (int): ID del contacto (abogado)
        caso_id (int): ID del caso
        rol_data (dict): Datos del rol del abogado
        represented_party_ids (list): Lista de IDs de roles a representar
        
    Returns:
        dict: Información del rol creado con detalles de representaciones
    """
    # Validar la solicitud
    is_valid, errors = validate_multiple_representation_request(contacto_id, caso_id, represented_party_ids)
    if not is_valid:
        print(f"Error en validación de representación múltiple: {errors}")
        return None
    
    conn = connect_db()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            # Generar ID de grupo para esta representación múltiple
            group_id = get_representation_group_id(contacto_id, caso_id)
            
            # Preparar datos del rol principal (UN SOLO ROL para el abogado)
            role_data = rol_data.copy()
            role_data['caso_id'] = caso_id
            role_data['contacto_id'] = contacto_id
            
            # Para representaciones múltiples, no usar representa_a_id en el rol principal
            # En su lugar, usar las notas para indicar las representaciones múltiples
            role_data['representa_a_id'] = None
            
            # Crear lista de partes representadas para las notas
            represented_details = []
            for party_id in represented_party_ids:
                party_info = get_role_details(party_id)
                if party_info:
                    represented_details.append({
                        'party_id': party_id,
                        'party_name': party_info.get('nombre_completo', 'N/A'),
                        'party_role': party_info.get('rol_principal', 'N/A')
                    })
            
            # Crear notas detalladas de representación múltiple
            notas_existentes = role_data.get('notas_del_rol', '') or ''
            notas_representacion = f"[REPRESENTACION_MULTIPLE:PRIMARY:{group_id}]\n"
            notas_representacion += f"Representa a {len(represented_party_ids)} parte(s):\n"
            
            for detail in represented_details:
                notas_representacion += f"- {detail['party_name']} ({detail['party_role']}) [ID:{detail['party_id']}]\n"
            
            role_data['notas_del_rol'] = f"{notas_existentes}\n{notas_representacion}".strip()
            
            # Crear el rol principal del abogado
            primary_role_id = add_rol_a_caso(role_data)
            
            if not primary_role_id:
                print("Error al crear el rol principal del abogado")
                return None
            
            # Crear roles "shadow" para cada parte representada (para mantener las relaciones)
            shadow_roles = []
            for i, party_id in enumerate(represented_party_ids):
                shadow_data = {
                    'caso_id': caso_id,
                    'contacto_id': contacto_id,
                    'rol_principal': rol_data.get('rol_principal', 'Abogado'),
                    'rol_secundario': rol_data.get('rol_secundario', ''),
                    'representa_a_id': party_id,
                    'notas_del_rol': f"[REPRESENTACION_MULTIPLE:SECONDARY:{group_id}] Shadow role for {represented_details[i]['party_name']}"
                }
                
                shadow_role_id = add_rol_a_caso(shadow_data)
                if shadow_role_id:
                    shadow_roles.append({
                        'rol_id': shadow_role_id,
                        'party_id': party_id,
                        'party_name': represented_details[i]['party_name'],
                        'party_role': represented_details[i]['party_role']
                    })
                else:
                    print(f"Advertencia: No se pudo crear rol shadow para party_id {party_id}")
            
            print(f"Creado abogado con representaciones múltiples: rol principal {primary_role_id}, {len(shadow_roles)} roles shadow")
            
            return {
                'primary_role_id': primary_role_id,
                'group_id': group_id,
                'total_representations': len(represented_party_ids),
                'represented_parties': represented_details,
                'shadow_roles': shadow_roles,
                'success': True
            }
            
    except Exception as e:
        print(f"Error al crear representaciones múltiples: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()
    
    return None

def get_multiple_representations(rol_id):
    """
    Obtiene todas las partes representadas por un rol de abogado específico.
    
    Args:
        rol_id (int): ID del rol del abogado
        
    Returns:
        dict: Información de representaciones múltiples
    """
    if not rol_id:
        return None
        
    conn = connect_db()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Obtener información del rol del abogado
            cur.execute("""
                SELECT r.*, c.nombre_completo as lawyer_name
                FROM roles_en_caso r
                JOIN contactos c ON r.contacto_id = c.id
                WHERE r.id = %s
            """, (rol_id,))
            
            lawyer_role = cur.fetchone()
            if not lawyer_role:
                return None
            
            # Verificar si es un rol de representación múltiple
            notas = lawyer_role.get('notas_del_rol', '') or ''
            if 'REPRESENTACION_MULTIPLE' not in notas:
                # Es una representación simple
                if lawyer_role.get('representa_a_id'):
                    cur.execute("""
                        SELECT r.*, c.nombre_completo as party_name
                        FROM roles_en_caso r
                        JOIN contactos c ON r.contacto_id = c.id
                        WHERE r.id = %s
                    """, (lawyer_role['representa_a_id'],))
                    
                    party = cur.fetchone()
                    if party:
                        return {
                            'is_multiple': False,
                            'lawyer_name': lawyer_role['lawyer_name'],
                            'lawyer_role_id': rol_id,
                            'represented_parties': [{
                                'party_id': party['id'],
                                'party_name': party['party_name'],
                                'party_role': party['rol_principal']
                            }]
                        }
                return None
            
            # Es representación múltiple - extraer group_id
            import re
            group_match = re.search(r'REPRESENTACION_MULTIPLE:[^:]+:([^]]+)', notas)
            if not group_match:
                return None
            
            group_id = group_match.group(1)
            
            # Obtener todos los roles del mismo grupo
            cur.execute("""
                SELECT 
                    r.id as lawyer_role_id,
                    r.representa_a_id,
                    party_r.rol_principal as party_role,
                    party_c.nombre_completo as party_name
                FROM roles_en_caso r
                LEFT JOIN roles_en_caso party_r ON r.representa_a_id = party_r.id
                LEFT JOIN contactos party_c ON party_r.contacto_id = party_c.id
                WHERE r.contacto_id = %s 
                AND r.caso_id = %s
                AND r.notas_del_rol LIKE %s
                AND r.representa_a_id IS NOT NULL
                ORDER BY party_r.rol_principal, party_c.nombre_completo
            """, (lawyer_role['contacto_id'], lawyer_role['caso_id'], f'%{group_id}%'))
            
            representations = cur.fetchall()
            
            represented_parties = []
            for rep in representations:
                if rep['representa_a_id']:
                    represented_parties.append({
                        'party_id': rep['representa_a_id'],
                        'party_name': rep['party_name'],
                        'party_role': rep['party_role'],
                        'lawyer_role_id': rep['lawyer_role_id']
                    })
            
            return {
                'is_multiple': True,
                'group_id': group_id,
                'lawyer_name': lawyer_role['lawyer_name'],
                'lawyer_contact_id': lawyer_role['contacto_id'],
                'case_id': lawyer_role['caso_id'],
                'total_representations': len(represented_parties),
                'represented_parties': represented_parties
            }
            
    except Exception as e:
        print(f"Error al obtener representaciones múltiples para rol {rol_id}: {e}")
        return None
    finally:
        conn.close()

def update_multiple_representations(primary_role_id, new_represented_party_ids):
    """
    Actualiza las partes representadas por un abogado con representación múltiple.
    
    Args:
        primary_role_id (int): ID del rol principal del abogado
        new_represented_party_ids (list): Nueva lista de IDs de partes a representar
        
    Returns:
        bool: True si la actualización fue exitosa
    """
    if not primary_role_id or not new_represented_party_ids:
        return False
    
    # Obtener información actual de representaciones
    current_info = get_multiple_representations(primary_role_id)
    if not current_info:
        return False
    
    conn = connect_db()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Si es representación múltiple, eliminar todos los roles del grupo
            if current_info['is_multiple']:
                group_id = current_info['group_id']
                
                # Eliminar todos los roles del grupo
                cur.execute("""
                    DELETE FROM roles_en_caso 
                    WHERE contacto_id = %s 
                    AND caso_id = %s 
                    AND notas_del_rol LIKE %s
                """, (current_info['lawyer_contact_id'], current_info['case_id'], f'%{group_id}%'))
            else:
                # Es representación simple, eliminar solo el rol actual
                cur.execute("DELETE FROM roles_en_caso WHERE id = %s", (primary_role_id,))
            
            # Obtener datos del rol original para recrear
            cur.execute("""
                SELECT r.*, c.nombre_completo
                FROM roles_en_caso r
                JOIN contactos c ON r.contacto_id = c.id
                WHERE r.contacto_id = %s AND r.caso_id = %s
                AND r.rol_principal IN ('Abogado', 'Apoderado')
                LIMIT 1
            """, (current_info['lawyer_contact_id'], current_info['case_id']))
            
            # Si no hay rol base, usar datos por defecto
            rol_data = {
                'rol_principal': 'Abogado',
                'rol_secundario': '',
                'datos_bancarios': '',
                'notas_del_rol': ''
            }
            
            # Crear nuevas representaciones
            result = create_multiple_representations(
                current_info['lawyer_contact_id'],
                current_info['case_id'],
                rol_data,
                new_represented_party_ids
            )
            
            if result and result.get('success'):
                conn.commit()
                return True
            else:
                conn.rollback()
                return False
                
    except Exception as e:
        print(f"Error al actualizar representaciones múltiples: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return False

def get_role_details(rol_id):
    """
    Obtiene detalles completos de un rol específico.
    
    Args:
        rol_id (int): ID del rol
        
    Returns:
        dict: Detalles del rol incluyendo información del contacto
    """
    if not rol_id:
        return None
        
    conn = connect_db()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT r.*, c.nombre_completo, c.dni, c.cuit, c.es_persona_juridica
                FROM roles_en_caso r
                JOIN contactos c ON r.contacto_id = c.id
                WHERE r.id = %s
            """, (rol_id,))
            
            result = cur.fetchone()
            return dict(result) if result else None
            
    except Exception as e:
        print(f"Error al obtener detalles del rol {rol_id}: {e}")
        return None
    finally:
        conn.close()

# --- Funciones CRUD para Roles en Caso ---

def _validate_no_circular_reference(conn, representa_a_id, caso_id, visited=None):
    """
    Función auxiliar para validar que no se creen referencias circulares en representa_a_id.
    """
    if visited is None:
        visited = set()
    
    if representa_a_id in visited:
        return False  # Referencia circular detectada
    
    visited.add(representa_a_id)
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT representa_a_id FROM roles_en_caso WHERE id = %s AND caso_id = %s",
                (representa_a_id, caso_id)
            )
            result = cur.fetchone()
            
            if result and result[0]:
                return _validate_no_circular_reference(conn, result[0], caso_id, visited)
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error validando referencia circular: {e}")
        return False
    
    return True

def _validate_no_circular_reference_for_update(conn, representa_a_id, caso_id, current_rol_id, visited=None):
    """
    Función auxiliar para validar referencias circulares en actualizaciones.
    Excluye el rol actual de la validación.
    """
    if visited is None:
        visited = set()
    
    if representa_a_id == current_rol_id:
        return False  # Un rol no puede representarse a sí mismo
    
    if representa_a_id in visited:
        return False  # Referencia circular detectada
    
    visited.add(representa_a_id)
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT representa_a_id FROM roles_en_caso WHERE id = %s AND caso_id = %s",
                (representa_a_id, caso_id)
            )
            result = cur.fetchone()
            
            if result and result[0]:
                return _validate_no_circular_reference_for_update(conn, result[0], caso_id, current_rol_id, visited)
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error validando referencia circular en actualización: {e}")
        return False
    
    return True

def _is_multiple_representation_request(datos_rol):
    """
    Detecta si una solicitud de rol es parte de una representación múltiple.
    
    Args:
        datos_rol (dict): Datos del rol a crear
        
    Returns:
        bool: True si es parte de representación múltiple
    """
    notas = datos_rol.get('notas_del_rol', '') or ''
    return '[REPRESENTACION_MULTIPLE:' in notas

def add_rol_a_caso(datos_rol):
    """
    Asigna un rol a un contacto en un caso específico con validación completa.
    `datos_rol` es un diccionario con las claves de la tabla `roles_en_caso`.
    Devuelve el ID del nuevo rol o None si falla.
    """
    # Validación previa de entrada
    if not datos_rol or not isinstance(datos_rol, dict):
        db_logger.error("Error: datos_rol debe ser un diccionario no vacío")
        return None

    # Validar campos obligatorios
    campos_obligatorios = ['caso_id', 'contacto_id', 'rol_principal']
    for campo in campos_obligatorios:
        if campo not in datos_rol or datos_rol[campo] is None:
            db_logger.error(f"Error: El campo '{campo}' es obligatorio")
            return None
    
    # Validar tipos de datos
    try:
        caso_id = int(datos_rol['caso_id'])
        contacto_id = int(datos_rol['contacto_id'])
    except (ValueError, TypeError):
        db_logger.error("Error: caso_id y contacto_id deben ser números enteros")
        return None
    
    # Validar rol principal
    rol_principal = datos_rol['rol_principal'].strip()
    if not rol_principal:
        db_logger.error("Error: rol_principal no puede estar vacío")
        return None
    
    roles_validos = ['Actor', 'Demandado', 'Abogado', 'Apoderado', 'Perito', 'Tercero', 'Testigo']
    if rol_principal not in roles_validos:
        db_logger.warning(f"Advertencia: '{rol_principal}' no está en la lista de roles estándar: {roles_validos}")

    conn = connect_db()
    new_id = None
    if not conn:
        db_logger.error("Error: No se pudo establecer conexión con la base de datos")
        return None

    try:
        with conn.cursor() as cur:
            # Validar que el caso existe
            cur.execute("SELECT id FROM casos WHERE id = %s", (caso_id,))
            if not cur.fetchone():
                db_logger.error(f"Error: No existe un caso con ID {caso_id}")
                return None
            
            # Validar que el contacto existe
            cur.execute("SELECT id FROM contactos WHERE id = %s", (contacto_id,))
            if not cur.fetchone():
                db_logger.error(f"Error: No existe un contacto con ID {contacto_id}")
                return None
            
            # Validar duplicados (mismo contacto, mismo rol principal en el mismo caso)
            # EXCEPCIÓN: Permitir múltiples roles para Abogados y Apoderados (representación múltiple)
            if rol_principal not in ['Abogado', 'Apoderado']:
                cur.execute("""
                    SELECT id FROM roles_en_caso 
                    WHERE caso_id = %s AND contacto_id = %s AND rol_principal = %s
                """, (caso_id, contacto_id, rol_principal))
                
                if cur.fetchone():
                    db_logger.error(f"Error: El contacto {contacto_id} ya tiene el rol '{rol_principal}' en el caso {caso_id}")
                    return None
            else:
                # Para Abogados y Apoderados, verificar si es representación múltiple válida
                # Solo permitir si tiene representa_a_id diferente o es parte de representación múltiple
                if not datos_rol.get('representa_a_id') and not _is_multiple_representation_request(datos_rol):
                    cur.execute("""
                        SELECT id FROM roles_en_caso 
                        WHERE caso_id = %s AND contacto_id = %s AND rol_principal = %s
                        AND representa_a_id IS NULL
                    """, (caso_id, contacto_id, rol_principal))
                    
                    if cur.fetchone():
                        db_logger.error(f"Error: El contacto {contacto_id} ya tiene el rol '{rol_principal}' sin representación en el caso {caso_id}")
                        return None
            
            # Validar referencias circulares si se especifica representa_a_id
            representa_a_id = datos_rol.get('representa_a_id')
            if representa_a_id:
                try:
                    representa_a_id = int(representa_a_id)
                    if not _validate_no_circular_reference(conn, representa_a_id, caso_id):
                        db_logger.error("Error: La asignación de representación crearía una referencia circular")
                        return None
                    
                    # Validar que el rol a representar existe en el mismo caso
                    cur.execute("SELECT id FROM roles_en_caso WHERE id = %s AND caso_id = %s", (representa_a_id, caso_id))
                    if not cur.fetchone():
                        db_logger.error(f"Error: No existe un rol con ID {representa_a_id} en el caso {caso_id}")
                        return None
                        
                except (ValueError, TypeError):
                    db_logger.error("Error: representa_a_id debe ser un número entero")
                    return None

            # Preparar datos para inserción
            columnas_validas = [
                'caso_id', 'contacto_id', 'rol_principal', 'rol_secundario', 
                'representa_a_id', 'datos_bancarios', 'notas_del_rol'
            ]
            
            columnas = []
            valores = []
            
            for col in columnas_validas:
                if col in datos_rol and datos_rol[col] is not None:
                    valor = datos_rol[col]
                    # Limpiar strings
                    if isinstance(valor, str):
                        valor = valor.strip()
                        if valor:  # Solo agregar si no está vacío
                            columnas.append(col)
                            valores.append(valor)
                    else:
                        columnas.append(col)
                        valores.append(valor)

            columnas.append('created_at')
            valores.append(int(time.time()))

            sql = f"INSERT INTO roles_en_caso ({', '.join(columnas)}) VALUES ({', '.join(['%s'] * len(valores))}) RETURNING id;"
            
            cur.execute(sql, valores)
            new_id = cur.fetchone()[0]
            conn.commit()
            
            # Actualizar actividad del caso
            update_last_activity(caso_id)
            db_logger.info(f"Rol '{rol_principal}' agregado exitosamente al caso {caso_id} con ID: {new_id}")
            
    except psycopg2.IntegrityError as e:
        db_logger.error(f"Error de integridad al agregar rol: {e}")
        conn.rollback()
    except psycopg2.DataError as e:
        db_logger.error(f"Error de datos al agregar rol: {e}")
        conn.rollback()
    except (Exception, psycopg2.DatabaseError) as error:
        db_logger.error(f"Error inesperado al agregar rol: {error}")
        conn.rollback()
    finally:
        conn.close()
        
    return new_id

def get_roles_by_caso_id(caso_id, incluir_jerarquia=True):
    """
    Obtiene todos los roles de un caso con información jerárquica optimizada.
    
    Args:
        caso_id (int): ID del caso
        incluir_jerarquia (bool): Si incluir información de jerarquía de representación
    
    Returns:
        list: Lista de roles con información completa y jerárquica
    """
    if not caso_id:
        db_logger.warning("get_roles_by_caso_id llamado sin caso_id")
        return []

    conn = connect_db()
    roles = []
    if not conn:
        db_logger.error("No se pudo conectar a la base de datos para obtener roles")
        return roles

    try:
        # Consulta optimizada con información jerárquica
        if incluir_jerarquia:
            sql = """
                WITH RECURSIVE jerarquia_roles AS (
                    -- Roles principales (no representan a nadie)
                    SELECT 
                        r.id as rol_id, r.caso_id, r.contacto_id, r.rol_principal, r.rol_secundario, 
                        r.representa_a_id, r.datos_bancarios, r.notas_del_rol, r.created_at as rol_created_at,
                        c.nombre_completo, c.es_persona_juridica, c.dni, c.cuit, c.domicilio_real,
                        c.domicilio_legal, c.email, c.telefono, c.notas_generales, c.created_at as contacto_created_at,
                        0 as nivel_jerarquia,
                        ARRAY[r.id] as ruta_jerarquia,
                        NULL::text as representado_nombre
                    FROM roles_en_caso r
                    JOIN contactos c ON r.contacto_id = c.id
                    WHERE r.caso_id = %s AND r.representa_a_id IS NULL
                    
                    UNION ALL
                    
                    -- Roles que representan a otros (recursivo)
                    SELECT 
                        r.id as rol_id, r.caso_id, r.contacto_id, r.rol_principal, r.rol_secundario, 
                        r.representa_a_id, r.datos_bancarios, r.notas_del_rol, r.created_at as rol_created_at,
                        c.nombre_completo, c.es_persona_juridica, c.dni, c.cuit, c.domicilio_real,
                        c.domicilio_legal, c.email, c.telefono, c.notas_generales, c.created_at as contacto_created_at,
                        jr.nivel_jerarquia + 1,
                        jr.ruta_jerarquia || r.id,
                        jr.nombre_completo as representado_nombre
                    FROM roles_en_caso r
                    JOIN contactos c ON r.contacto_id = c.id
                    JOIN jerarquia_roles jr ON r.representa_a_id = jr.rol_id
                    WHERE r.caso_id = %s
                )
                SELECT 
                    *,
                    CASE 
                        WHEN rol_principal = 'Actor' THEN 1
                        WHEN rol_principal = 'Demandado' THEN 2
                        WHEN rol_principal = 'Tercero' THEN 3
                        WHEN rol_principal = 'Abogado' THEN 4
                        WHEN rol_principal = 'Apoderado' THEN 5
                        WHEN rol_principal = 'Perito' THEN 6
                        ELSE 7
                    END as orden_rol
                FROM jerarquia_roles
                ORDER BY orden_rol, nivel_jerarquia, nombre_completo;
            """
            params = (caso_id, caso_id)
        else:
            # Consulta simple sin jerarquía para mejor rendimiento
            sql = """
                SELECT 
                    r.id as rol_id, r.caso_id, r.contacto_id, r.rol_principal, r.rol_secundario, 
                    r.representa_a_id, r.datos_bancarios, r.notas_del_rol, r.created_at as rol_created_at,
                    c.nombre_completo, c.es_persona_juridica, c.dni, c.cuit, c.domicilio_real,
                    c.domicilio_legal, c.email, c.telefono, c.notas_generales, c.created_at as contacto_created_at,
                    CASE 
                        WHEN r.rol_principal = 'Actor' THEN 1
                        WHEN r.rol_principal = 'Demandado' THEN 2
                        WHEN r.rol_principal = 'Tercero' THEN 3
                        WHEN r.rol_principal = 'Abogado' THEN 4
                        WHEN r.rol_principal = 'Apoderado' THEN 5
                        WHEN r.rol_principal = 'Perito' THEN 6
                        ELSE 7
                    END as orden_rol
                FROM roles_en_caso r
                JOIN contactos c ON r.contacto_id = c.id
                WHERE r.caso_id = %s
                ORDER BY orden_rol, c.nombre_completo;
            """
            params = (caso_id,)

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            roles = [dict(row) for row in rows]
            
        db_logger.info(f"Obtenidos {len(roles)} roles para caso {caso_id}")
        
    except (Exception, psycopg2.DatabaseError) as e:
        db_logger.error(f"Error al obtener roles para el caso ID {caso_id}: {e}")
    finally:
        conn.close()
        
    return roles

def get_roles_estadisticas_caso(caso_id):
    """
    Obtiene estadísticas de roles para un caso específico.
    Útil para mostrar resúmenes rápidos.
    """
    conn = connect_db()
    stats = {}
    if not conn:
        return stats

    try:
        sql = """
            SELECT 
                rol_principal,
                COUNT(*) as cantidad,
                COUNT(CASE WHEN representa_a_id IS NOT NULL THEN 1 END) as representantes,
                COUNT(CASE WHEN c.es_persona_juridica = true THEN 1 END) as personas_juridicas
            FROM roles_en_caso r
            JOIN contactos c ON r.contacto_id = c.id
            WHERE r.caso_id = %s
            GROUP BY rol_principal
            ORDER BY rol_principal;
        """

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (caso_id,))
            rows = cur.fetchall()
            
            stats = {
                'por_rol': {row['rol_principal']: dict(row) for row in rows},
                'total_roles': sum(row['cantidad'] for row in rows),
                'total_representantes': sum(row['representantes'] for row in rows),
                'total_personas_juridicas': sum(row['personas_juridicas'] for row in rows)
            }
            
    except (Exception, psycopg2.DatabaseError) as e:
        db_logger.error(f"Error al obtener estadísticas de roles para caso {caso_id}: {e}")
    finally:
        conn.close()
        
    return stats

def validate_jerarquia_roles(caso_id):
    """
    Valida la integridad de la jerarquía de roles en un caso.
    Detecta referencias circulares y roles huérfanos.
    """
    conn = connect_db()
    problemas = []
    if not conn:
        return ["Error de conexión a base de datos"]

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Detectar referencias circulares
            sql_circular = """
                WITH RECURSIVE ciclos AS (
                    SELECT id, representa_a_id, ARRAY[id] as ruta
                    FROM roles_en_caso 
                    WHERE caso_id = %s AND representa_a_id IS NOT NULL
                    
                    UNION ALL
                    
                    SELECT r.id, r.representa_a_id, c.ruta || r.id
                    FROM roles_en_caso r
                    JOIN ciclos c ON r.id = c.representa_a_id
                    WHERE r.caso_id = %s AND r.id = ANY(c.ruta)
                )
                SELECT DISTINCT ruta FROM ciclos WHERE array_length(ruta, 1) > 1;
            """
            
            cur.execute(sql_circular, (caso_id, caso_id))
            ciclos = cur.fetchall()
            
            for ciclo in ciclos:
                problemas.append(f"Referencia circular detectada en roles: {ciclo['ruta']}")
            
            # Detectar roles huérfanos (representa_a_id apunta a rol inexistente)
            sql_huerfanos = """
                SELECT r1.id, r1.representa_a_id
                FROM roles_en_caso r1
                LEFT JOIN roles_en_caso r2 ON r1.representa_a_id = r2.id AND r2.caso_id = %s
                WHERE r1.caso_id = %s 
                  AND r1.representa_a_id IS NOT NULL 
                  AND r2.id IS NULL;
            """
            
            cur.execute(sql_huerfanos, (caso_id, caso_id))
            huerfanos = cur.fetchall()
            
            for huerfano in huerfanos:
                problemas.append(f"Rol {huerfano['id']} referencia rol inexistente {huerfano['representa_a_id']}")
                
    except (Exception, psycopg2.DatabaseError) as e:
        problemas.append(f"Error al validar jerarquía: {e}")
    finally:
        conn.close()
        
    return problemas

def update_rol(rol_id, datos_rol):
    """
    Actualiza un rol existente en un caso.
    """
    conn = connect_db()
    success = False
    if not conn:
        return False

    columnas_validas = [
        'rol_principal', 'rol_secundario', 'representa_a_id', 
        'datos_bancarios', 'notas_del_rol'
    ]
    
    set_parts = [f"{col} = %s" for col in datos_rol if col in columnas_validas]
    valores = [datos_rol[col] for col in datos_rol if col in columnas_validas]
    
    if not set_parts:
        print("Advertencia: No se proporcionaron campos válidos para actualizar el rol.")
        return False

    try:
        with conn.cursor() as cur:
            # Obtener caso_id para validaciones
            cur.execute("SELECT caso_id FROM roles_en_caso WHERE id = %s", (rol_id,))
            res = cur.fetchone()
            caso_id = res[0] if res else None
            
            if not caso_id:
                print(f"Error: No se encontró el rol ID {rol_id}")
                return False

            # Validar referencias circulares si se está actualizando representa_a_id
            if 'representa_a_id' in datos_rol and datos_rol['representa_a_id']:
                # Crear una copia temporal para validar sin incluir el rol actual
                temp_visited = {rol_id}  # Excluir el rol actual de la validación
                if not _validate_no_circular_reference_for_update(conn, datos_rol['representa_a_id'], caso_id, rol_id):
                    print("Error: La actualización de representación crearía una referencia circular.")
                    return False

            valores.append(rol_id)
            sql = f"UPDATE roles_en_caso SET {', '.join(set_parts)} WHERE id = %s;"
            
            cur.execute(sql, valores)
            conn.commit()
            success = cur.rowcount > 0
            if success:
                update_last_activity(caso_id)
                print(f"Rol ID {rol_id} actualizado correctamente.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al actualizar rol ID {rol_id}: {error}")
        conn.rollback()
    finally:
        conn.close()
        
    return success

def delete_rol(rol_id):
    """
    Elimina un rol de un caso, incluyendo limpieza de representaciones múltiples.
    """
    conn = connect_db()
    success = False
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            # Obtener información del rol antes de eliminarlo
            cur.execute("""
                SELECT caso_id, contacto_id, rol_principal, notas_del_rol, representa_a_id 
                FROM roles_en_caso 
                WHERE id = %s
            """, (rol_id,))
            rol_info = cur.fetchone()
            
            if not rol_info:
                print(f"Rol ID {rol_id} no encontrado.")
                return False
            
            caso_id, contacto_id, rol_principal, notas_del_rol, representa_a_id = rol_info
            notas_del_rol = notas_del_rol or ''
            
            # Verificar si es un rol con representaciones múltiples
            is_multiple_rep = 'REPRESENTACION_MULTIPLE' in notas_del_rol
            
            if is_multiple_rep and rol_principal in ['Abogado', 'Apoderado']:
                print(f"Eliminando abogado con representaciones múltiples: {rol_id}")
                
                # Extraer group_id de las notas
                import re
                group_match = re.search(r'REPRESENTACION_MULTIPLE:[^:]+:([^]]+)', notas_del_rol)
                
                if group_match:
                    group_id = group_match.group(1)
                    print(f"Limpiando grupo de representación múltiple: {group_id}")
                    
                    # Encontrar todos los roles relacionados con este grupo
                    cur.execute("""
                        SELECT id, notas_del_rol, representa_a_id 
                        FROM roles_en_caso 
                        WHERE caso_id = %s 
                        AND (notas_del_rol LIKE %s OR notas_del_rol LIKE %s)
                    """, (caso_id, f'%REPRESENTACION_MULTIPLE:PRIMARY:{group_id}%', f'%REPRESENTACION_MULTIPLE:SECONDARY:{group_id}%'))
                    
                    related_roles = cur.fetchall()
                    
                    # Limpiar las notas de representación múltiple de los roles relacionados
                    for related_rol_id, related_notas, related_representa_a_id in related_roles:
                        if related_rol_id != rol_id:  # No procesar el rol que se va a eliminar
                            # Limpiar las notas de representación múltiple
                            cleaned_notas = re.sub(r'\[REPRESENTACION_MULTIPLE:[^]]+\]', '', related_notas or '')
                            cleaned_notas = re.sub(r'\n+', '\n', cleaned_notas).strip()
                            
                            # Si este rol tenía representa_a_id, limpiarlo también
                            new_representa_a_id = None
                            if related_representa_a_id == rol_id:
                                # Este rol representaba al rol que se está eliminando, limpiar la relación
                                new_representa_a_id = None
                            else:
                                new_representa_a_id = related_representa_a_id
                            
                            # Actualizar el rol relacionado
                            cur.execute("""
                                UPDATE roles_en_caso 
                                SET notas_del_rol = %s, representa_a_id = %s 
                                WHERE id = %s
                            """, (cleaned_notas if cleaned_notas else None, new_representa_a_id, related_rol_id))
                            
                            print(f"Limpiado rol relacionado ID {related_rol_id}")
            
            # Limpiar cualquier rol que tenga representa_a_id apuntando al rol que se elimina
            cur.execute("""
                UPDATE roles_en_caso 
                SET representa_a_id = NULL 
                WHERE representa_a_id = %s AND caso_id = %s
            """, (rol_id, caso_id))
            
            affected_representations = cur.rowcount
            if affected_representations > 0:
                print(f"Limpiadas {affected_representations} relaciones de representación huérfanas")
            
            # Finalmente, eliminar el rol principal
            cur.execute("DELETE FROM roles_en_caso WHERE id = %s", (rol_id,))
            success = cur.rowcount > 0
            
            if success:
                conn.commit()
                if caso_id:
                    update_last_activity(caso_id)
                print(f"Rol ID {rol_id} eliminado del caso con limpieza completa de representaciones.")
            else:
                conn.rollback()
                print(f"No se pudo eliminar el rol ID {rol_id}")
                
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al eliminar rol ID {rol_id}: {error}")
        if conn:
            conn.rollback()
        success = False
    finally:
        if conn:
            conn.close()
        
    return success


# --- Funciones CRUD para Etiquetas ---

def add_etiqueta(nombre_etiqueta):
    """Agrega una nueva etiqueta o devuelve el ID si ya existe. Lógica robusta."""
    nombre_etiqueta_lower = nombre_etiqueta.strip().lower()
    if not nombre_etiqueta_lower: return None

    conn = None
    etiqueta_id = None
    try:
        conn = connect_db()
        if conn:
            with conn.cursor() as cur:
                # 1. Verificar si ya existe
                cur.execute("SELECT id_etiqueta FROM etiquetas WHERE nombre_etiqueta = %s", (nombre_etiqueta_lower,))
                res = cur.fetchone()
                if res:
                    etiqueta_id = res[0]
                else:
                    # 2. Si no existe, insertarla
                    cur.execute("INSERT INTO etiquetas (nombre_etiqueta) VALUES (%s) RETURNING id_etiqueta", (nombre_etiqueta_lower,))
                    res_insert = cur.fetchone()
                    if res_insert:
                        etiqueta_id = res_insert[0]
                conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error en add_etiqueta: {error}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()
    return etiqueta_id

def get_etiquetas():
    """Obtiene todas las etiquetas."""
    conn = connect_db()
    etiquetas = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM etiquetas ORDER BY nombre_etiqueta')
                rows = cur.fetchall()
                etiquetas = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener etiquetas: {e}")
        finally:
            conn.close()
    return etiquetas

def asignar_etiqueta_a_cliente(cliente_id, etiqueta_id):
    """Asigna una etiqueta a un cliente."""
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO cliente_etiquetas (cliente_id, etiqueta_id) VALUES (%s, %s) ON CONFLICT DO NOTHING', (cliente_id, etiqueta_id))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al asignar etiqueta {etiqueta_id} al cliente {cliente_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def quitar_etiqueta_de_cliente(cliente_id, etiqueta_id):
    """Quita una etiqueta de un cliente."""
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM cliente_etiquetas WHERE cliente_id = %s AND etiqueta_id = %s', (cliente_id, etiqueta_id))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al quitar etiqueta {etiqueta_id} del cliente {cliente_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def get_etiquetas_de_cliente(cliente_id):
    """Obtiene todas las etiquetas de un cliente."""
    conn = connect_db()
    etiquetas = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT e.id_etiqueta, e.nombre_etiqueta
                    FROM etiquetas e
                    JOIN cliente_etiquetas ce ON e.id_etiqueta = ce.etiqueta_id
                    WHERE ce.cliente_id = %s
                    ORDER BY e.nombre_etiqueta
                ''', (cliente_id,))
                rows = cur.fetchall()
                etiquetas = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener etiquetas del cliente {cliente_id}: {e}")
        finally:
            conn.close()
    return etiquetas

def asignar_etiqueta_a_caso(caso_id, etiqueta_id):
    """Asigna una etiqueta a un caso."""
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO caso_etiquetas (caso_id, etiqueta_id) VALUES (%s, %s) ON CONFLICT DO NOTHING', (caso_id, etiqueta_id))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al asignar etiqueta {etiqueta_id} al caso {caso_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def quitar_etiqueta_de_caso(caso_id, etiqueta_id):
    """Quita una etiqueta de un caso."""
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM caso_etiquetas WHERE caso_id = %s AND etiqueta_id = %s', (caso_id, etiqueta_id))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al quitar etiqueta {etiqueta_id} del caso {caso_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def get_etiquetas_de_caso(caso_id):
    """Obtiene todas las etiquetas de un caso."""
    conn = connect_db()
    etiquetas = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT e.id_etiqueta, e.nombre_etiqueta
                    FROM etiquetas e
                    JOIN caso_etiquetas ce ON e.id_etiqueta = ce.etiqueta_id
                    WHERE ce.caso_id = %s
                    ORDER BY e.nombre_etiqueta
                ''', (caso_id,))
                rows = cur.fetchall()
                etiquetas = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener etiquetas del caso {caso_id}: {e}")
        finally:
            conn.close()
    return etiquetas

# --- Funciones CRUD para Modelos de Escritos ---

def add_modelo_escrito(nombre_modelo, categoria, ruta_plantilla, descripcion=""):
    """Agrega un nuevo modelo de escrito."""
    conn = connect_db()
    new_id = None
    if conn:
        try:
            with conn.cursor() as cur:
                timestamp = int(time.time())
                cur.execute('''
                    INSERT INTO modelos_escritos (nombre_modelo, categoria, ruta_plantilla, descripcion, created_at)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                ''', (nombre_modelo, categoria, ruta_plantilla, descripcion, timestamp))
                new_id = cur.fetchone()[0]
                conn.commit()
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al agregar modelo de escrito: {e}")
            conn.rollback()
        finally:
            conn.close()
    return new_id

def get_modelos_escritos():
    """Obtiene todos los modelos de escritos."""
    conn = connect_db()
    modelos = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM modelos_escritos ORDER BY categoria, nombre_modelo')
                rows = cur.fetchall()
                modelos = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener modelos de escritos: {e}")
        finally:
            conn.close()
    return modelos

def get_modelo_escrito_by_id(modelo_id):
    """Obtiene un modelo de escrito por su ID."""
    conn = connect_db()
    modelo_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM modelos_escritos WHERE id = %s', (modelo_id,))
                row = cur.fetchone()
                if row:
                    modelo_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener modelo de escrito por ID {modelo_id}: {e}")
        finally:
            conn.close()
    return modelo_data

def update_modelo_escrito(modelo_id, nombre_modelo, categoria, ruta_plantilla, descripcion):
    """Actualiza un modelo de escrito."""
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE modelos_escritos
                    SET nombre_modelo = %s, categoria = %s, ruta_plantilla = %s, descripcion = %s
                    WHERE id = %s
                ''', (nombre_modelo, categoria, ruta_plantilla, descripcion, modelo_id))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar modelo de escrito ID {modelo_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def delete_modelo_escrito(modelo_id):
    """Elimina un modelo de escrito."""
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM modelos_escritos WHERE id = %s', (modelo_id,))
                conn.commit()
                success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar modelo de escrito ID {modelo_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def get_fechas_con_audiencias():
    """Obtiene una lista de todas las fechas que tienen al menos una audiencia."""
    conn = None
    fechas = []
    try:
        conn = connect_db()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT fecha FROM audiencias ORDER BY fecha;")
                rows = cur.fetchall()
                # PostgreSQL returns dates as strings in YYYY-MM-DD format
                # We need to handle both string and date object cases for compatibility
                for row in rows:
                    fecha_value = row[0]
                    if fecha_value is not None:
                        if hasattr(fecha_value, 'strftime'):
                            # It's a date object, convert to string
                            fechas.append(fecha_value.strftime('%Y-%m-%d'))
                        elif isinstance(fecha_value, str):
                            # It's already a string, use as-is (should be in YYYY-MM-DD format)
                            fechas.append(fecha_value.strip())
                        else:
                            # Fallback: convert to string
                            fecha_str = str(fecha_value)
                            if fecha_str and fecha_str != 'None':
                                fechas.append(fecha_str)
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al obtener fechas con audiencias: {error}")
    finally:
        if conn: conn.close()
    return fechas

def get_audiencias_by_fecha(fecha):
    """Obtiene todas las audiencias para una fecha específica."""
    sql = """
        SELECT a.*, ca.caratula as caso_caratula
        FROM audiencias a
        JOIN casos ca ON a.caso_id = ca.id
        WHERE a.fecha = %s
        ORDER BY a.hora;
    """
    conn = None
    audiencias = []
    try:
        conn = connect_db()
        if conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (fecha,))
                audiencias = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al obtener audiencias por fecha: {error}")
    finally:
        if conn: conn.close()
    return audiencias

# --- Funciones CRUD para Movimientos de Cuenta ---

def add_movimiento(datos_movimiento):
    """
    Agrega un nuevo movimiento financiero a un caso.
    
    Args:
        datos_movimiento (dict): Diccionario con los datos del movimiento
            - caso_id (int): ID del caso
            - fecha (str): Fecha en formato YYYY-MM-DD
            - concepto (str): Descripción del movimiento
            - tipo_movimiento (str): 'Ingreso' o 'Gasto'
            - monto (float/Decimal): Monto del movimiento
            - notas (str, opcional): Notas adicionales
    
    Returns:
        int: ID del movimiento creado o None si hay error
    """
    conn = connect_db()
    new_id = None
    if conn:
        try:
            with conn.cursor() as cur:
                timestamp = int(time.time())
                cur.execute('''
                    INSERT INTO movimientos_cuenta (caso_id, fecha, concepto, tipo_movimiento, monto, notas, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (
                    datos_movimiento['caso_id'],
                    datos_movimiento['fecha'],
                    datos_movimiento['concepto'],
                    datos_movimiento['tipo_movimiento'],
                    datos_movimiento['monto'],
                    datos_movimiento.get('notas', ''),
                    timestamp
                ))
                new_id = cur.fetchone()[0]
                conn.commit()
                
                # Actualizar la actividad del caso
                update_last_activity(datos_movimiento['caso_id'])
                
                # Agregar actividad al caso
                tipo_actividad = "Movimiento Financiero"
                descripcion = f"{datos_movimiento['tipo_movimiento']}: {datos_movimiento['concepto']} - ${datos_movimiento['monto']}"
                add_actividad_caso(
                    datos_movimiento['caso_id'],
                    datetime.datetime.now(),
                    tipo_actividad,
                    descripcion,
                    "Sistema",
                    f"movimiento_id:{new_id}"
                )
                
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al agregar movimiento: {e}")
            conn.rollback()
        finally:
            conn.close()
    return new_id

def get_movimientos_by_caso_id(caso_id, order_desc=True, limit=None, offset=0):
    """
    Obtiene todos los movimientos financieros de un caso con paginación opcional.
    
    Args:
        caso_id (int): ID del caso
        order_desc (bool): Si True, ordena por fecha descendente
        limit (int, optional): Límite de registros a obtener
        offset (int): Número de registros a saltar
    
    Returns:
        list: Lista de diccionarios con los movimientos
    """
    conn = connect_db()
    movimientos = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                order_direction = "DESC" if order_desc else "ASC"
                sql = f'''
                    SELECT id, caso_id, fecha, concepto, tipo_movimiento, monto, notas, created_at
                    FROM movimientos_cuenta 
                    WHERE caso_id = %s 
                    ORDER BY fecha {order_direction}, created_at {order_direction}
                '''
                
                params = [caso_id]
                
                # Add pagination if specified
                if limit is not None:
                    sql += " LIMIT %s"
                    params.append(limit)
                    
                if offset > 0:
                    sql += " OFFSET %s"
                    params.append(offset)
                
                cur.execute(sql, params)
                rows = cur.fetchall()
                movimientos = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener movimientos para el caso ID {caso_id}: {e}")
        finally:
            conn.close()
    return movimientos

def get_movimientos_count_by_caso_id(caso_id):
    """
    Obtiene el número total de movimientos para un caso.
    
    Args:
        caso_id (int): ID del caso
    
    Returns:
        int: Número total de movimientos
    """
    conn = connect_db()
    count = 0
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT COUNT(*) 
                    FROM movimientos_cuenta 
                    WHERE caso_id = %s
                ''', (caso_id,))
                result = cur.fetchone()
                count = result[0] if result else 0
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al contar movimientos para el caso ID {caso_id}: {e}")
        finally:
            conn.close()
    return count

def get_movimiento_by_id(movimiento_id):
    """
    Obtiene un movimiento específico por su ID.
    
    Args:
        movimiento_id (int): ID del movimiento
    
    Returns:
        dict: Datos del movimiento o None si no existe
    """
    conn = connect_db()
    movimiento_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT id, caso_id, fecha, concepto, tipo_movimiento, monto, notas, created_at
                    FROM movimientos_cuenta 
                    WHERE id = %s
                ''', (movimiento_id,))
                row = cur.fetchone()
                if row:
                    movimiento_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener movimiento por ID {movimiento_id}: {e}")
        finally:
            conn.close()
    return movimiento_data

def update_movimiento(movimiento_id, datos_movimiento):
    """
    Actualiza un movimiento financiero existente.
    
    Args:
        movimiento_id (int): ID del movimiento a actualizar
        datos_movimiento (dict): Nuevos datos del movimiento
    
    Returns:
        bool: True si la actualización fue exitosa
    """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                # Obtener el caso_id antes de actualizar para la actividad
                cur.execute('SELECT caso_id FROM movimientos_cuenta WHERE id = %s', (movimiento_id,))
                row = cur.fetchone()
                if not row:
                    return False
                caso_id = row[0]
                
                cur.execute('''
                    UPDATE movimientos_cuenta
                    SET fecha = %s, concepto = %s, tipo_movimiento = %s, monto = %s, notas = %s
                    WHERE id = %s
                ''', (
                    datos_movimiento['fecha'],
                    datos_movimiento['concepto'],
                    datos_movimiento['tipo_movimiento'],
                    datos_movimiento['monto'],
                    datos_movimiento.get('notas', ''),
                    movimiento_id
                ))
                conn.commit()
                if cur.rowcount > 0:
                    update_last_activity(caso_id)
                    
                    # Agregar actividad al caso
                    tipo_actividad = "Movimiento Financiero Actualizado"
                    descripcion = f"{datos_movimiento['tipo_movimiento']}: {datos_movimiento['concepto']} - ${datos_movimiento['monto']}"
                    add_actividad_caso(
                        caso_id,
                        datetime.datetime.now(),
                        tipo_actividad,
                        descripcion,
                        "Sistema",
                        f"movimiento_id:{movimiento_id}"
                    )
                    success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar movimiento ID {movimiento_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def delete_movimiento(movimiento_id):
    """
    Elimina un movimiento financiero.
    
    Args:
        movimiento_id (int): ID del movimiento a eliminar
    
    Returns:
        bool: True si la eliminación fue exitosa
    """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                # Obtener datos del movimiento antes de eliminarlo para la actividad
                cur.execute('SELECT caso_id, concepto, tipo_movimiento, monto FROM movimientos_cuenta WHERE id = %s', (movimiento_id,))
                row = cur.fetchone()
                if not row:
                    return False
                caso_id, concepto, tipo_movimiento, monto = row
                
                cur.execute('DELETE FROM movimientos_cuenta WHERE id = %s', (movimiento_id,))
                conn.commit()
                if cur.rowcount > 0:
                    update_last_activity(caso_id)
                    
                    # Agregar actividad al caso
                    tipo_actividad = "Movimiento Financiero Eliminado"
                    descripcion = f"{tipo_movimiento} eliminado: {concepto} - ${monto}"
                    add_actividad_caso(
                        caso_id,
                        datetime.datetime.now(),
                        tipo_actividad,
                        descripcion,
                        "Sistema",
                        f"movimiento_eliminado_id:{movimiento_id}"
                    )
                    success = True
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar movimiento ID {movimiento_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    return success

def get_saldo_caso(caso_id):
    """
    Calcula el saldo actual de un caso (ingresos - gastos).
    
    Args:
        caso_id (int): ID del caso
    
    Returns:
        Decimal: Saldo actual del caso
    """
    conn = connect_db()
    saldo = 0
    if conn:
        try:
            with conn.cursor() as cur:
                # Calcular total de ingresos
                cur.execute('''
                    SELECT COALESCE(SUM(monto), 0) 
                    FROM movimientos_cuenta 
                    WHERE caso_id = %s AND tipo_movimiento = 'Ingreso'
                ''', (caso_id,))
                total_ingresos = cur.fetchone()[0]
                
                # Calcular total de gastos
                cur.execute('''
                    SELECT COALESCE(SUM(monto), 0) 
                    FROM movimientos_cuenta 
                    WHERE caso_id = %s AND tipo_movimiento = 'Gasto'
                ''', (caso_id,))
                total_gastos = cur.fetchone()[0]
                
                saldo = total_ingresos - total_gastos
                
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al calcular saldo para el caso ID {caso_id}: {e}")
        finally:
            conn.close()
    return saldo

def get_total_ingresos_caso(caso_id):
    """
    Calcula el total de ingresos de un caso.
    
    Args:
        caso_id (int): ID del caso
    
    Returns:
        Decimal: Total de ingresos del caso
    """
    conn = connect_db()
    total = 0
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT COALESCE(SUM(monto), 0) 
                    FROM movimientos_cuenta 
                    WHERE caso_id = %s AND tipo_movimiento = 'Ingreso'
                ''', (caso_id,))
                total = cur.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al calcular total de ingresos para el caso ID {caso_id}: {e}")
        finally:
            conn.close()
    return total

def get_total_gastos_caso(caso_id):
    """
    Calcula el total de gastos de un caso.
    
    Args:
        caso_id (int): ID del caso
    
    Returns:
        Decimal: Total de gastos del caso
    """
    conn = connect_db()
    total = 0
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT COALESCE(SUM(monto), 0) 
                    FROM movimientos_cuenta 
                    WHERE caso_id = %s AND tipo_movimiento = 'Gasto'
                ''', (caso_id,))
                total = cur.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al calcular total de gastos para el caso ID {caso_id}: {e}")
        finally:
            conn.close()
    return total

def get_resumen_financiero_caso(caso_id):
    """
    Obtiene un resumen financiero completo de un caso.
    
    Args:
        caso_id (int): ID del caso
    
    Returns:
        dict: Resumen con totales, saldo y estadísticas
    """
    conn = connect_db()
    resumen = {
        'total_ingresos': 0,
        'total_gastos': 0,
        'saldo_actual': 0,
        'cantidad_movimientos': 0,
        'ultimo_movimiento': None
    }
    
    if conn:
        try:
            with conn.cursor() as cur:
                # Obtener totales y estadísticas en una sola consulta
                cur.execute('''
                    SELECT 
                        COALESCE(SUM(CASE WHEN tipo_movimiento = 'Ingreso' THEN monto ELSE 0 END), 0) as total_ingresos,
                        COALESCE(SUM(CASE WHEN tipo_movimiento = 'Gasto' THEN monto ELSE 0 END), 0) as total_gastos,
                        COUNT(*) as cantidad_movimientos,
                        MAX(fecha) as ultimo_movimiento
                    FROM movimientos_cuenta 
                    WHERE caso_id = %s
                ''', (caso_id,))
                
                row = cur.fetchone()
                if row:
                    resumen['total_ingresos'] = row[0]
                    resumen['total_gastos'] = row[1]
                    resumen['saldo_actual'] = row[0] - row[1]  # ingresos - gastos
                    resumen['cantidad_movimientos'] = row[2]
                    resumen['ultimo_movimiento'] = row[3]
                    
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener resumen financiero para el caso ID {caso_id}: {e}")
        finally:
            conn.close()
    
    return resumen

# --- Función de inicialización ---

if __name__ == "__main__":
    create_tables()
    print("Base de datos PostgreSQL inicializada correctamente.")

# --- Funciones CRUD para Prospectos ---

def add_prospecto(nombre, contacto="", fecha_primera_consulta=None, notas_generales=""):
    """
    Agrega un nuevo prospecto al sistema.
    
    Args:
        nombre (str): Nombre del prospecto (obligatorio)
        contacto (str): Información de contacto (email, teléfono, etc.)
        fecha_primera_consulta (date): Fecha de la primera consulta (por defecto hoy)
        notas_generales (str): Notas generales sobre el prospecto
    
    Returns:
        int: ID del nuevo prospecto o None si falla
    """
    if not nombre or not nombre.strip():
        print("Error: El nombre del prospecto es obligatorio")
        return None
    
    if fecha_primera_consulta is None:
        fecha_primera_consulta = datetime.date.today()
    
    conn = connect_db()
    new_id = None
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO prospectos (nombre, contacto, fecha_primera_consulta, notas_generales, created_at)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                ''', (nombre.strip(), contacto.strip(), fecha_primera_consulta, notas_generales.strip(), int(time.time())))
                new_id = cur.fetchone()[0]
                conn.commit()
                print(f"Prospecto '{nombre}' agregado exitosamente con ID: {new_id}")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al agregar prospecto: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    return new_id

def get_todos_los_prospectos():
    """
    Obtiene todos los prospectos del sistema ordenados por fecha de primera consulta.
    
    Returns:
        list: Lista de diccionarios con información de prospectos
    """
    conn = connect_db()
    prospectos = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT p.*, 
                           c.nombre as cliente_convertido_nombre
                    FROM prospectos p
                    LEFT JOIN clientes c ON p.convertido_a_cliente_id = c.id
                    ORDER BY p.fecha_primera_consulta DESC, p.nombre ASC
                ''')
                rows = cur.fetchall()
                prospectos = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener prospectos: {e}")
        finally:
            conn.close()
    
    return prospectos

def get_prospecto_by_id(prospecto_id):
    """
    Obtiene un prospecto específico por su ID.
    
    Args:
        prospecto_id (int): ID del prospecto
    
    Returns:
        dict: Datos del prospecto o None si no se encuentra
    """
    conn = connect_db()
    prospecto_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT p.*, 
                           c.nombre as cliente_convertido_nombre
                    FROM prospectos p
                    LEFT JOIN clientes c ON p.convertido_a_cliente_id = c.id
                    WHERE p.id = %s
                ''', (prospecto_id,))
                row = cur.fetchone()
                if row:
                    prospecto_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener prospecto por ID {prospecto_id}: {e}")
        finally:
            conn.close()
    
    return prospecto_data

def update_prospecto_estado(prospecto_id, nuevo_estado):
    """
    Actualiza el estado de un prospecto.
    
    Args:
        prospecto_id (int): ID del prospecto
        nuevo_estado (str): Nuevo estado ('Consulta Inicial', 'En Análisis', 'Convertido', 'Desestimado')
    
    Returns:
        bool: True si la actualización fue exitosa
    """
    estados_validos = ['Consulta Inicial', 'En Análisis', 'Convertido', 'Desestimado']
    if nuevo_estado not in estados_validos:
        print(f"Error: Estado '{nuevo_estado}' no es válido. Estados válidos: {estados_validos}")
        return False
    
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE prospectos 
                    SET estado = %s 
                    WHERE id = %s
                ''', (nuevo_estado, prospecto_id))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"Estado del prospecto ID {prospecto_id} actualizado a '{nuevo_estado}'")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar estado del prospecto ID {prospecto_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    return success

def marcar_prospecto_como_convertido(prospecto_id, cliente_id):
    """
    Marca un prospecto como convertido y lo vincula con el cliente creado.
    
    Args:
        prospecto_id (int): ID del prospecto
        cliente_id (int): ID del cliente al que se convirtió
    
    Returns:
        bool: True si la conversión fue exitosa
    """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                # Verificar que el cliente existe
                cur.execute("SELECT id FROM clientes WHERE id = %s", (cliente_id,))
                if not cur.fetchone():
                    print(f"Error: No existe un cliente con ID {cliente_id}")
                    return False
                
                # Actualizar el prospecto
                cur.execute('''
                    UPDATE prospectos 
                    SET estado = 'Convertido', 
                        convertido_a_cliente_id = %s, 
                        fecha_conversion = %s 
                    WHERE id = %s
                ''', (cliente_id, datetime.date.today(), prospecto_id))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"Prospecto ID {prospecto_id} marcado como convertido al cliente ID {cliente_id}")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al marcar prospecto como convertido: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    return success


def update_prospecto_conversion(prospecto_id, cliente_id=None, fecha_conversion=None, nuevo_estado=None):
    """
    Actualiza la información de conversión de un prospecto.
    
    Args:
        prospecto_id (int): ID del prospecto
        cliente_id (int, optional): ID del cliente (None para revertir)
        fecha_conversion (date, optional): Fecha de conversión (None para revertir)
        nuevo_estado (str, optional): Nuevo estado del prospecto
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    conn = connect_db()
    if conn is None:
        return False
    
    success = False
    try:
        with conn.cursor() as cur:
            # Construir la consulta dinámicamente según los parámetros
            set_clauses = []
            params = []
            
            if cliente_id is not None:
                set_clauses.append("convertido_a_cliente_id = %s")
                params.append(cliente_id)
            else:
                set_clauses.append("convertido_a_cliente_id = NULL")
            
            if fecha_conversion is not None:
                set_clauses.append("fecha_conversion = %s")
                params.append(fecha_conversion)
            else:
                set_clauses.append("fecha_conversion = NULL")
            
            if nuevo_estado is not None:
                set_clauses.append("estado = %s")
                params.append(nuevo_estado)
            
            params.append(prospecto_id)
            
            query = f'''
                UPDATE prospectos 
                SET {', '.join(set_clauses)}
                WHERE id = %s
            '''
            
            cur.execute(query, params)
            conn.commit()
            success = cur.rowcount > 0
            
            if success:
                action = "convertido" if cliente_id else "revertido"
                print(f"Prospecto ID {prospecto_id} {action} exitosamente")
                
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error al actualizar conversión del prospecto: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return success


def get_casos_by_cliente_id(cliente_id):
    """
    Obtiene todos los casos asociados a un cliente.
    
    Args:
        cliente_id (int): ID del cliente
        
    Returns:
        list: Lista de casos del cliente
    """
    conn = connect_db()
    if conn is None:
        return []
    
    casos = []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('''
                SELECT id, numero_expediente, caratula, juzgado, 
                       etapa_procesal, estado_indexacion, created_at
                FROM casos 
                WHERE cliente_id = %s
                ORDER BY created_at DESC
            ''', (cliente_id,))
            
            casos = [dict(row) for row in cur.fetchall()]
            
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error al obtener casos del cliente {cliente_id}: {e}")
    finally:
        conn.close()
    
    return casos


def delete_cliente(cliente_id):
    """
    Elimina un cliente de la base de datos.
    CUIDADO: Esta operación eliminará también todos los casos y datos relacionados.
    
    Args:
        cliente_id (int): ID del cliente a eliminar
        
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    conn = connect_db()
    if conn is None:
        return False
    
    success = False
    try:
        with conn.cursor() as cur:
            # Verificar que el cliente existe
            cur.execute('SELECT id FROM clientes WHERE id = %s', (cliente_id,))
            if not cur.fetchone():
                print(f"Cliente ID {cliente_id} no existe")
                return False
            
            # Eliminar el cliente (CASCADE eliminará casos relacionados)
            cur.execute('DELETE FROM clientes WHERE id = %s', (cliente_id,))
            conn.commit()
            success = cur.rowcount > 0
            
            if success:
                print(f"Cliente ID {cliente_id} eliminado exitosamente")
                
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error al eliminar cliente {cliente_id}: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return success


def add_cliente_from_conversion(nombre, direccion="", email="", whatsapp="", convertido_de_prospecto_id=None, fecha_conversion=None):
    """
    Agrega un nuevo cliente con información de conversión desde prospecto.
    
    Args:
        nombre (str): Nombre del cliente
        direccion (str): Dirección del cliente
        email (str): Email del cliente
        whatsapp (str): WhatsApp del cliente
        convertido_de_prospecto_id (int, optional): ID del prospecto original
        fecha_conversion (date, optional): Fecha de conversión
        
    Returns:
        int: ID del cliente creado, None si falla
    """
    conn = connect_db()
    if conn is None:
        return None
    
    cliente_id = None
    try:
        with conn.cursor() as cur:
            # Insertar el cliente
            cur.execute('''
                INSERT INTO clientes (nombre, direccion, email, whatsapp, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (nombre, direccion, email, whatsapp, int(datetime.datetime.now().timestamp())))
            
            result = cur.fetchone()
            if result:
                cliente_id = result[0]
                conn.commit()
                print(f"Cliente creado desde conversión: ID {cliente_id}, Prospecto origen: {convertido_de_prospecto_id}")
            
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error al crear cliente desde conversión: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return cliente_id

def update_prospecto(prospecto_id, nombre=None, contacto=None, notas_generales=None):
    """
    Actualiza los datos de un prospecto.
    
    Args:
        prospecto_id (int): ID del prospecto
        nombre (str): Nuevo nombre (opcional)
        contacto (str): Nueva información de contacto (opcional)
        notas_generales (str): Nuevas notas generales (opcional)
    
    Returns:
        bool: True si la actualización fue exitosa
    """
    # Construir la consulta dinámicamente
    campos_a_actualizar = {}
    if nombre is not None:
        campos_a_actualizar['nombre'] = nombre.strip()
    if contacto is not None:
        campos_a_actualizar['contacto'] = contacto.strip()
    if notas_generales is not None:
        campos_a_actualizar['notas_generales'] = notas_generales.strip()
    
    if not campos_a_actualizar:
        print("Advertencia: No se proporcionaron campos para actualizar")
        return False
    
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                set_clause = ", ".join([f"{key} = %s" for key in campos_a_actualizar.keys()])
                valores = list(campos_a_actualizar.values()) + [prospecto_id]
                
                sql = f"UPDATE prospectos SET {set_clause} WHERE id = %s"
                cur.execute(sql, valores)
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"Prospecto ID {prospecto_id} actualizado exitosamente")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar prospecto ID {prospecto_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    return success

def delete_prospecto(prospecto_id):
    """
    Elimina un prospecto del sistema.
    ADVERTENCIA: Esto también eliminará todas las consultas asociadas debido a CASCADE.
    
    Args:
        prospecto_id (int): ID del prospecto a eliminar
    
    Returns:
        bool: True si la eliminación fue exitosa
    """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                # Verificar si el prospecto tiene consultas
                cur.execute("SELECT COUNT(*) FROM consultas WHERE prospecto_id = %s", (prospecto_id,))
                consultas_count = cur.fetchone()[0]
                
                if consultas_count > 0:
                    print(f"ADVERTENCIA: El prospecto ID {prospecto_id} tiene {consultas_count} consultas que serán eliminadas.")
                
                cur.execute("DELETE FROM prospectos WHERE id = %s", (prospecto_id,))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"Prospecto ID {prospecto_id} eliminado correctamente")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar prospecto ID {prospecto_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    return success

# --- Funciones CRUD para Consultas ---

def add_consulta(prospecto_id, fecha_consulta=None, relato_original_cliente="", hechos_reformulados_ia="", encuadre_legal_preliminar="", resultado_consulta=""):
    """
    Agrega una nueva consulta para un prospecto.
    
    Args:
        prospecto_id (int): ID del prospecto (obligatorio)
        fecha_consulta (date): Fecha de la consulta (por defecto hoy)
        relato_original_cliente (str): Relato original del cliente
        hechos_reformulados_ia (str): Hechos reformulados por IA
        encuadre_legal_preliminar (str): Encuadre legal preliminar
    
    Returns:
        int: ID de la nueva consulta o None si falla
    """
    if not prospecto_id:
        print("Error: El ID del prospecto es obligatorio")
        return None
    
    if fecha_consulta is None:
        fecha_consulta = datetime.date.today()
    
    conn = connect_db()
    new_id = None
    if conn:
        try:
            with conn.cursor() as cur:
                # Verificar que el prospecto existe
                cur.execute("SELECT id FROM prospectos WHERE id = %s", (prospecto_id,))
                if not cur.fetchone():
                    print(f"Error: No existe un prospecto con ID {prospecto_id}")
                    return None
                
                cur.execute('''
                    INSERT INTO consultas (prospecto_id, fecha_consulta, relato_original_cliente, 
                                         hechos_reformulados_ia, encuadre_legal_preliminar, resultado_consulta, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (prospecto_id, fecha_consulta, relato_original_cliente.strip(), 
                      hechos_reformulados_ia.strip(), encuadre_legal_preliminar.strip(), resultado_consulta.strip(), int(time.time())))
                new_id = cur.fetchone()[0]
                conn.commit()
                print(f"Consulta agregada exitosamente con ID: {new_id}")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al agregar consulta: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    return new_id

def get_consultas_by_prospecto_id(prospecto_id):
    """
    Obtiene todas las consultas de un prospecto ordenadas por fecha.
    
    Args:
        prospecto_id (int): ID del prospecto
    
    Returns:
        list: Lista de diccionarios con información de consultas
    """
    conn = connect_db()
    consultas = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT c.*, p.nombre as prospecto_nombre
                    FROM consultas c
                    JOIN prospectos p ON c.prospecto_id = p.id
                    WHERE c.prospecto_id = %s
                    ORDER BY c.fecha_consulta DESC, c.created_at DESC
                ''', (prospecto_id,))
                rows = cur.fetchall()
                consultas = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener consultas del prospecto ID {prospecto_id}: {e}")
        finally:
            conn.close()
    
    return consultas

def get_consulta_by_id(consulta_id):
    """
    Obtiene una consulta específica por su ID.
    
    Args:
        consulta_id (int): ID de la consulta
    
    Returns:
        dict: Datos de la consulta o None si no se encuentra
    """
    conn = connect_db()
    consulta_data = None
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT c.*, p.nombre as prospecto_nombre, p.contacto as prospecto_contacto
                    FROM consultas c
                    JOIN prospectos p ON c.prospecto_id = p.id
                    WHERE c.id = %s
                ''', (consulta_id,))
                row = cur.fetchone()
                if row:
                    consulta_data = dict(row)
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener consulta por ID {consulta_id}: {e}")
        finally:
            conn.close()
    
    return consulta_data

def update_consulta(consulta_id, relato_original_cliente=None, hechos_reformulados_ia=None, encuadre_legal_preliminar=None, resultado_consulta=None):
    """
    Actualiza una consulta existente.
    
    Args:
        consulta_id (int): ID de la consulta
        relato_original_cliente (str): Nuevo relato original (opcional)
        hechos_reformulados_ia (str): Nuevos hechos reformulados por IA (opcional)
        encuadre_legal_preliminar (str): Nuevo encuadre legal preliminar (opcional)
    
    Returns:
        bool: True si la actualización fue exitosa
    """
    # Construir la consulta dinámicamente
    campos_a_actualizar = {}
    if relato_original_cliente is not None:
        campos_a_actualizar['relato_original_cliente'] = relato_original_cliente.strip()
    if hechos_reformulados_ia is not None:
        campos_a_actualizar['hechos_reformulados_ia'] = hechos_reformulados_ia.strip()
    if encuadre_legal_preliminar is not None:
        campos_a_actualizar['encuadre_legal_preliminar'] = encuadre_legal_preliminar.strip()
    if resultado_consulta is not None:
        campos_a_actualizar['resultado_consulta'] = resultado_consulta.strip()
    
    if not campos_a_actualizar:
        print("Advertencia: No se proporcionaron campos para actualizar")
        return False
    
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                set_clause = ", ".join([f"{key} = %s" for key in campos_a_actualizar.keys()])
                valores = list(campos_a_actualizar.values()) + [consulta_id]
                
                sql = f"UPDATE consultas SET {set_clause} WHERE id = %s"
                cur.execute(sql, valores)
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"Consulta ID {consulta_id} actualizada exitosamente")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al actualizar consulta ID {consulta_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    return success

def mark_consulta_as_exported(consulta_id, ruta_archivo):
    """
    Marca una consulta como exportada y guarda la ruta del archivo.
    
    Args:
        consulta_id (int): ID de la consulta
        ruta_archivo (str): Ruta del archivo exportado
    
    Returns:
        bool: True si la actualización fue exitosa
    """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                import datetime
                fecha_exportacion = datetime.datetime.now()
                
                cur.execute('''
                    UPDATE consultas 
                    SET exportado = TRUE, 
                        fecha_exportacion = %s, 
                        ruta_archivo_exportado = %s 
                    WHERE id = %s
                ''', (fecha_exportacion, ruta_archivo, consulta_id))
                
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"Consulta ID {consulta_id} marcada como exportada: {ruta_archivo}")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al marcar consulta como exportada ID {consulta_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    return success

def get_consultas_with_ai_analysis(prospecto_id=None):
    """
    Obtiene consultas que tienen análisis de IA.
    
    Args:
        prospecto_id (int): ID del prospecto (opcional, si no se especifica obtiene todas)
    
    Returns:
        list: Lista de consultas con análisis IA
    """
    conn = connect_db()
    consultas = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if prospecto_id:
                    cur.execute('''
                        SELECT c.*, p.nombre as prospecto_nombre
                        FROM consultas c
                        JOIN prospectos p ON c.prospecto_id = p.id
                        WHERE c.prospecto_id = %s 
                        AND c.hechos_reformulados_ia IS NOT NULL 
                        AND c.hechos_reformulados_ia != ''
                        ORDER BY c.fecha_consulta DESC
                    ''', (prospecto_id,))
                else:
                    cur.execute('''
                        SELECT c.*, p.nombre as prospecto_nombre
                        FROM consultas c
                        JOIN prospectos p ON c.prospecto_id = p.id
                        WHERE c.hechos_reformulados_ia IS NOT NULL 
                        AND c.hechos_reformulados_ia != ''
                        ORDER BY c.fecha_consulta DESC
                    ''')
                
                rows = cur.fetchall()
                consultas = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener consultas con análisis IA: {e}")
        finally:
            conn.close()
    
    return consultas

def delete_consulta(consulta_id):
    """
    Elimina una consulta del sistema.
    
    Args:
        consulta_id (int): ID de la consulta a eliminar
    
    Returns:
        bool: True si la eliminación fue exitosa
    """
    conn = connect_db()
    success = False
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM consultas WHERE id = %s", (consulta_id,))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"Consulta ID {consulta_id} eliminada correctamente")
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al eliminar consulta ID {consulta_id}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    return success

def get_prospectos_por_estado(estado):
    """
    Obtiene prospectos filtrados por estado.
    
    Args:
        estado (str): Estado a filtrar ('Consulta Inicial', 'En Análisis', 'Convertido', 'Desestimado')
    
    Returns:
        list: Lista de prospectos con el estado especificado
    """
    conn = connect_db()
    prospectos = []
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT p.*, 
                           c.nombre as cliente_convertido_nombre,
                           COUNT(cons.id) as total_consultas
                    FROM prospectos p
                    LEFT JOIN clientes c ON p.convertido_a_cliente_id = c.id
                    LEFT JOIN consultas cons ON p.id = cons.prospecto_id
                    WHERE p.estado = %s
                    GROUP BY p.id, c.nombre
                    ORDER BY p.fecha_primera_consulta DESC, p.nombre ASC
                ''', (estado,))
                rows = cur.fetchall()
                prospectos = [dict(row) for row in rows]
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener prospectos por estado '{estado}': {e}")
        finally:
            conn.close()
    
    return prospectos

def get_estadisticas_prospectos():
    """
    Obtiene estadísticas generales sobre los prospectos.
    
    Returns:
        dict: Diccionario con estadísticas de prospectos
    """
    conn = connect_db()
    estadisticas = {
        'total_prospectos': 0,
        'por_estado': {},
        'convertidos_mes_actual': 0,
        'consultas_mes_actual': 0
    }
    
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Total de prospectos
                cur.execute("SELECT COUNT(*) as total FROM prospectos")
                estadisticas['total_prospectos'] = cur.fetchone()['total']
                
                # Prospectos por estado
                cur.execute('''
                    SELECT estado, COUNT(*) as cantidad 
                    FROM prospectos 
                    GROUP BY estado
                ''')
                for row in cur.fetchall():
                    estadisticas['por_estado'][row['estado']] = row['cantidad']
                
                # Convertidos en el mes actual
                cur.execute('''
                    SELECT COUNT(*) as cantidad 
                    FROM prospectos 
                    WHERE estado = 'Convertido' 
                    AND EXTRACT(YEAR FROM fecha_conversion) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND EXTRACT(MONTH FROM fecha_conversion) = EXTRACT(MONTH FROM CURRENT_DATE)
                ''')
                estadisticas['convertidos_mes_actual'] = cur.fetchone()['cantidad']
                
                # Consultas en el mes actual
                cur.execute('''
                    SELECT COUNT(*) as cantidad 
                    FROM consultas 
                    WHERE EXTRACT(YEAR FROM fecha_consulta) = EXTRACT(YEAR FROM CURRENT_DATE)
                    AND EXTRACT(MONTH FROM fecha_consulta) = EXTRACT(MONTH FROM CURRENT_DATE)
                ''')
                estadisticas['consultas_mes_actual'] = cur.fetchone()['cantidad']
                
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"Error al obtener estadísticas de prospectos: {e}")
        finally:
            conn.close()
    
    return estadisticas