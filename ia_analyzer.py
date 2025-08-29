# ia_analyzer.py (Versión Final Sincronizada)

import os
import glob
import logging
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
try:
    from langchain_chroma import Chroma
    print("[IA Analyzer] Using langchain-chroma (recommended)")
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
        print("[IA Analyzer] Using langchain-community Chroma (legacy)")
    except ImportError:
        print("[IA Analyzer] Error: Could not import Chroma vectorstore")
        Chroma = None
import warnings
# Suppress deprecation warnings for cleaner output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from langchain_huggingface import HuggingFaceEmbeddings as SentenceTransformerEmbeddings
    print("[IA Analyzer] Using langchain-huggingface (recommended)")
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings as SentenceTransformerEmbeddings
        print("[IA Analyzer] Using langchain-community embeddings (legacy)")
    except ImportError:
        print("[IA Analyzer] Warning: Could not import HuggingFace embeddings. IA functionality may be limited.")
        SentenceTransformerEmbeddings = None
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import requests
import time

# --- CONFIGURACIÓN PARA IA LOCAL ---
# Ya no se requieren API keys externas - usando Ollama local
print("[IA Analyzer] [LOCAL] Configurado para IA local con Ollama")

# Configuración por defecto para Ollama
DEFAULT_OLLAMA_MODEL = "gpt-oss:20b"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 30  # segundos


VECTOR_DB_BASE_DIR = "vector_databases"
if not os.path.exists(VECTOR_DB_BASE_DIR):
    os.makedirs(VECTOR_DB_BASE_DIR)

def check_ollama_service():
    """
    Verifica si el servicio Ollama está disponible y funcionando.
    
    Returns:
        tuple: (is_available, status_message)
    """
    try:
        print("[IA Analyzer] [SEARCH] Verificando disponibilidad del servicio Ollama...")
        
        # Verificar si el servicio está corriendo
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            print(f"[IA Analyzer] [OK] Servicio Ollama disponible")
            print(f"[IA Analyzer] [LIST] Modelos disponibles: {model_names}")

            # Verificar si el modelo por defecto está disponible
            if DEFAULT_OLLAMA_MODEL in model_names:
                print(f"[IA Analyzer] [OK] Modelo '{DEFAULT_OLLAMA_MODEL}' disponible")
                return True, f"Servicio Ollama disponible con modelo {DEFAULT_OLLAMA_MODEL}"
            else:
                available_models = ", ".join(model_names) if model_names else "ninguno"
                warning_msg = f"Modelo '{DEFAULT_OLLAMA_MODEL}' no encontrado. Disponibles: {available_models}"
                print(f"[IA Analyzer] [WARN] {warning_msg}")
                return False, warning_msg
        else:
            error_msg = f"Servicio Ollama respondió con código {response.status_code}"
            print(f"[IA Analyzer] [ERROR] {error_msg}")
            return False, error_msg

    except requests.exceptions.ConnectionError:
        error_msg = "No se pudo conectar al servicio Ollama. ¿Está ejecutándose 'ollama serve'?"
        print(f"[IA Analyzer] [ERROR] {error_msg}")
        return False, error_msg
    except requests.exceptions.Timeout:
        error_msg = "Timeout al conectar con Ollama"
        print(f"[IA Analyzer] [ERROR] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Error inesperado verificando Ollama: {str(e)}"
        print(f"[IA Analyzer] [ERROR] {error_msg}")
        return False, error_msg

def initialize_ollama_llm(model_name=None, temperature=0.3):
    """
    Inicializa el LLM de Ollama con manejo robusto de errores.
    
    Args:
        model_name (str): Nombre del modelo a usar (por defecto DEFAULT_OLLAMA_MODEL)
        temperature (float): Temperatura para la generación
        
    Returns:
        tuple: (llm_instance, success, error_message)
    """
    if model_name is None:
        model_name = DEFAULT_OLLAMA_MODEL
    
    try:
        print(f"[IA Analyzer] [AI] Inicializando LLM con modelo: {model_name}")

        # Verificar servicio primero
        is_available, status_msg = check_ollama_service()
        if not is_available:
            return None, False, status_msg

        # Crear instancia del LLM
        llm = Ollama(
            model=model_name,
            temperature=temperature,
            base_url=OLLAMA_BASE_URL,
            timeout=OLLAMA_TIMEOUT
        )

        # Probar con una consulta simple
        print(f"[IA Analyzer] [TEST] Probando conexión con consulta simple...")
        test_response = llm.invoke("Responde solo 'OK' si puedes procesar este mensaje.")

        if test_response and len(test_response.strip()) > 0:
            print(f"[IA Analyzer] [OK] LLM inicializado correctamente")
            print(f"[IA Analyzer] [CONFIG] Configuración: modelo={model_name}, temperatura={temperature}")
            return llm, True, "LLM inicializado exitosamente"
        else:
            error_msg = "El modelo no respondió correctamente a la prueba"
            print(f"[IA Analyzer] [ERROR] {error_msg}")
            return None, False, error_msg

    except Exception as e:
        error_msg = f"Error inicializando LLM: {str(e)}"
        print(f"[IA Analyzer] [ERROR] {error_msg}")
        return None, False, error_msg

def get_available_models():
    """
    Obtiene la lista de modelos disponibles en Ollama.
    
    Returns:
        list: Lista de nombres de modelos disponibles
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [model.get('name', '') for model in models]
        return []
    except Exception as e:
        print(f"[IA Analyzer] Error obteniendo modelos: {e}")
        return []

def create_embedding_function():
    """Create embedding function with comprehensive error handling.
    if SentenceTransformerEmbeddings is None:
        raise ImportError("SentenceTransformerEmbeddings not available. Please install sentence-transformers: pip install sentence-transformers")
    
    if Chroma is None:
        raise ImportError("Chroma vectorstore not available. Please install langchain-chroma: pip install langchain-chroma")
    
    try:
        print("[IA Analyzer] Creating embedding function...")
        embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        print("[IA Analyzer] ✓ Embedding function created successfully")
        return embedding_function
    except Exception as e:
        print(f"[IA Analyzer] ✗ Error creating embedding function: {e}")
        raise
    """
    """Crea y devuelve la función de embeddings, especificando el dispositivo."""
    print("[IA Analyzer] [BRAIN] Creando función de embeddings...")
    try:
        # --- CORRECCIÓN CLAVE ---
        # Le decimos explícitamente al modelo que se cargue en la CPU.
        # Esto evita el error de la "meta tensor copy".
        model_kwargs = {'device': 'cpu'}

        embedding_function = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs=model_kwargs
        )
        print("[IA Analyzer] [OK] Función de embeddings creada con éxito.")
        return embedding_function

    except Exception as e:
        print(f"[IA Analyzer] [ERROR] Error creating embedding function: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_dependencies():
    """Verify that all required dependencies are available."""
    missing_deps = []
    
    if SentenceTransformerEmbeddings is None:
        missing_deps.append("sentence-transformers (pip install sentence-transformers)")
    
    if Chroma is None:
        missing_deps.append("langchain-chroma (pip install langchain-chroma)")
    
    if missing_deps:
        error_msg = "Missing required dependencies:\n" + "\n".join(f"- {dep}" for dep in missing_deps)
        raise ImportError(error_msg)
    
    return True

# --- Funciones Principales ---

def preparar_y_concatenar_movimientos(directorio_movimientos, id_caso):
    # Esta función ya es correcta
    print(f"[IA Analyzer] Buscando movimientos para caso {id_caso} en: {directorio_movimientos}")
    # ... (el resto de esta función no necesita cambios, puedes dejar la tuya)
    if not os.path.isdir(directorio_movimientos): return None
    lista_archivos = glob.glob(os.path.join(directorio_movimientos, "*.txt"))
    if not lista_archivos: return None
    lista_archivos.sort()
    contenido_completo = ""
    for archivo_path in lista_archivos:
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                contenido_completo += f.read() + "\n\n--- FIN DE MOVIMIENTO ---\n\n"
        except UnicodeDecodeError:
            try:
                with open(archivo_path, 'r', encoding='latin-1') as f:
                    contenido_completo += f.read() + "\n\n--- FIN DE MOVIMIENTO ---\n\n"
            except Exception as e_latin1:
                 print(f"[IA Analyzer] Error irrecuperable leyendo {archivo_path}: {e_latin1}")
    if not contenido_completo.strip(): return None
    temp_dir = "temp_ia"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    ruta_archivo_concatenado = os.path.join(temp_dir, f"caso_{id_caso}_completo.txt")
    with open(ruta_archivo_concatenado, 'w', encoding='utf-8') as f:
        f.write(contenido_completo)
    print(f"[IA Analyzer] {len(lista_archivos)} movimientos concatenados en: {ruta_archivo_concatenado}")
    return ruta_archivo_concatenado


def indexar_expediente(client, ruta_archivo_fuente, id_caso):
    """Index a case file with comprehensive error handling and progress tracking."""
    print(f"[IA Analyzer] [START] Iniciando indexación para caso {id_caso}...")

    try:
        # Verify dependencies first
        verify_dependencies()

        # Check if source file exists
        if not os.path.exists(ruta_archivo_fuente):
            raise FileNotFoundError(f"Source file not found: {ruta_archivo_fuente}")

        print(f"[IA Analyzer] [DOC] Cargando documento: {ruta_archivo_fuente}")
        loader = TextLoader(ruta_archivo_fuente, encoding='utf-8')
        documents = loader.load()

        if not documents:
            raise ValueError("No documents loaded from source file")

        print(f"[IA Analyzer] [CUT] Dividiendo texto en chunks...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        docs_divididos = text_splitter.split_documents(documents)

        if not docs_divididos:
            raise ValueError("No text chunks created from documents")

        print(f"[IA Analyzer] [STATS] Creados {len(docs_divididos)} chunks de texto")

        print(f"[IA Analyzer] [BRAIN] Creando función de embeddings...")
        embedding_function = create_embedding_function()

        nombre_coleccion = f"caso_{id_caso}_{hash(ruta_archivo_fuente)}"
        print(f"[IA Analyzer] [FOLDER] Nombre de colección: {nombre_coleccion}")

        # Clean up existing collection
        try:
            client.delete_collection(name=nombre_coleccion)
            print(f"[IA Analyzer] [DELETE] Colección existente eliminada")
        except Exception as e:
            print(f"[IA Analyzer] [INFO] Info de eliminación: {e}")

        print(f"[IA Analyzer] [BUILD] Creando vector store...")
        db = Chroma(client=client, collection_name=nombre_coleccion, embedding_function=embedding_function)

        print(f"[IA Analyzer] [ADD] Agregando documentos al vector store...")
        db.add_documents(docs_divididos)

        # Verify the collection
        count = client.get_collection(name=nombre_coleccion).count()
        print(f"[IA Analyzer] [OK] Indexación completada exitosamente!")
        print(f"[IA Analyzer] [GROWTH] Colección '{nombre_coleccion}' contiene {count} items")

        return nombre_coleccion

    except Exception as e:
        print(f"[IA Analyzer] [ERROR] ERROR durante la indexación: {e}")
        import traceback
        traceback.print_exc()
        return None


def consultar_expediente(client, nombre_coleccion, prompt_usuario):
    """Query the indexed case with comprehensive error handling."""
    print(f"[IA Analyzer] [SEARCH] Consultando colección: {nombre_coleccion}")

    try:
        # Verify dependencies
        verify_dependencies()

        # Check if collection exists
        try:
            collection = client.get_collection(name=nombre_coleccion)
            count = collection.count()
            print(f"[IA Analyzer] [STATS] Colección encontrada con {count} items")
        except Exception as e:
            raise ValueError(f"Collection '{nombre_coleccion}' not found or inaccessible: {e}")

        print(f"[IA Analyzer] [BRAIN] Creando función de embeddings...")
        embedding_function = create_embedding_function()

        print(f"[IA Analyzer] [BUILD] Conectando al vector store...")
        db = Chroma(client=client, collection_name=nombre_coleccion, embedding_function=embedding_function)

        print(f"[IA Analyzer] [SEARCH] Configurando retriever...")
        retriever = db.as_retriever(search_kwargs={"k": 5})

        print(f"[IA Analyzer] [AI] Inicializando LLM local (Ollama)...")
        llm, success, error_msg = initialize_ollama_llm()

        if not success:
            print(f"[IA Analyzer] [ERROR] ERROR: {error_msg}")
            print(f"[IA Analyzer] [INFO] Asegúrese de que Ollama esté ejecutándose: 'ollama serve'")
            print(f"[IA Analyzer] [INFO] Y que el modelo '{DEFAULT_OLLAMA_MODEL}' esté disponible")
            raise ConnectionError(f"Servicio Ollama no disponible: {error_msg}")

        print(f"[IA Analyzer] [CHAIN] Creando cadena QA...")
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        print(f"[IA Analyzer] [CHAT] Enviando consulta: '{prompt_usuario[:50]}...'")
        respuesta = qa_chain.invoke(prompt_usuario)

        print(f"[IA Analyzer] [OK] Consulta completada exitosamente")
        return respuesta

    except Exception as e:
        print(f"[IA Analyzer] [ERROR] ERROR durante la consulta: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Ocurrió un error al consultar la IA: {e}"}


def debug_retriever(client, nombre_coleccion, prompt_usuario):
    """
    Función de depuración para revisar fragmentos relevantes sin costo de IA.
    """
    import logging
    
    logging.info(f"Depurando colección: {nombre_coleccion}")
    try:
        embedding_function = create_embedding_function()
        db = Chroma(client=client, collection_name=nombre_coleccion, embedding_function=embedding_function)
        logging.info(f"Colección '{nombre_coleccion}' cargada. Items: {db._collection.count()}")
        
        retriever = db.as_retriever(search_kwargs={"k": 5})
        logging.info(f"Buscando fragmentos relevantes para: '{prompt_usuario[:50]}...'")
        
        documentos_relevantes = retriever.invoke(prompt_usuario)
        logging.info(f"Se encontraron {len(documentos_relevantes)} fragmentos relevantes.")
        
        resultado_debug = f"--- MODO DEPURACIÓN (SIN COSTO) ---\nColección: '{nombre_coleccion}'\n\n"
        for i, doc in enumerate(documentos_relevantes):
            resultado_debug += f"--- Fragmento {i+1} ---\n{doc.page_content}\n\n"
        return resultado_debug
    except Exception as e:
        logging.error(f"Error en debug_retriever: {e}")
        return f"Error durante la depuración: {e}"

def diagnosticar_sistema():
    """Diagnose the IA Analyzer system health with local AI support."""
    print("\n" + "="*60)
    print("[CONFIG] DIAGNOSTICO DEL SISTEMA IA ANALYZER (LOCAL)")
    print("="*60)

    try:
        # Check dependencies
        print("[LIST] Verificando dependencias...")
        verify_dependencies()
        print("[OK] Todas las dependencias están disponibles")

        # Test embedding creation
        print("[BRAIN] Probando creación de embeddings...")
        embedding_function = create_embedding_function()
        print("[OK] Función de embeddings creada exitosamente")

        # Test ChromaDB client
        print("[DB] Probando cliente ChromaDB...")
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(
            path=VECTOR_DB_BASE_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        print("[OK] Cliente ChromaDB funcionando correctamente")

        # Test Ollama connection
        print("[AI] Probando conexión con Ollama...")
        llm, success, error_msg = initialize_ollama_llm()
        if not success:
            print(f"[ERROR] Error conectando con Ollama: {error_msg}")
            print("[INFO] Asegúrese de ejecutar: 'ollama serve' y tener el modelo disponible")
            print("[INFO] Para instalar el modelo: 'ollama pull gpt-oss-20b'")
            return False
        print("[OK] Conexión con Ollama exitosa")

        # Test basic vectorization
        print("[TEST] Probando vectorización básica...")
        test_docs = [{"page_content": "Documento de prueba", "metadata": {}}]

        from langchain_core.documents import Document
        docs = [Document(page_content=doc["page_content"], metadata=doc["metadata"]) for doc in test_docs]

        test_collection = "diagnostic_test"
        try:
            client.delete_collection(name=test_collection)
        except:
            pass

        db = Chroma(client=client, collection_name=test_collection, embedding_function=embedding_function)
        db.add_documents(docs)

        count = client.get_collection(name=test_collection).count()
        print(f"[OK] Vectorización básica exitosa: {count} documentos indexados")

        # Clean up
        client.delete_collection(name=test_collection)

        print("\n[SUCCESS] DIAGNOSTICO COMPLETADO: Sistema IA local funcionando correctamente")
        return True

    except Exception as e:
        print(f"\n[ERROR] DIAGNOSTICO FALLO: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    except Exception as e:
        logging.error(f"Error durante la depuración: {e}")
        import traceback
        traceback.print_exc()
        return f"Ocurrió un error durante la depuración: {e}"

def migrate_to_local_ai():
    """
    Función de migración que verifica y configura el sistema para IA local.
    
    Returns:
        tuple: (success, message, recommendations)
    """
    print("\n" + "="*60)
    print("[MIGRATE] MIGRACION A IA LOCAL")
    print("="*60)

    recommendations = []

    try:
        # 1. Verificar disponibilidad de Ollama
        print("[1] Verificando servicio Ollama...")
        is_available, status_msg = check_ollama_service()

        if not is_available:
            return False, f"Servicio Ollama no disponible: {status_msg}", [
                "Instalar Ollama desde https://ollama.ai/",
                "Ejecutar 'ollama serve' para iniciar el servicio",
                f"Instalar el modelo: 'ollama pull {DEFAULT_OLLAMA_MODEL}'"
            ]

        print("[OK] Servicio Ollama disponible")

        # 2. Verificar modelo específico
        print("[2] Verificando modelo específico...")
        models = get_available_models()
        if DEFAULT_OLLAMA_MODEL not in models:
            return False, f"Modelo {DEFAULT_OLLAMA_MODEL} no disponible", [
                f"Instalar el modelo: 'ollama pull {DEFAULT_OLLAMA_MODEL}'",
                "Verificar que la descarga se completó correctamente"
            ]

        print(f"[OK] Modelo {DEFAULT_OLLAMA_MODEL} disponible")

        # 3. Probar inicialización completa
        print("[3] Probando inicialización completa...")
        llm, success, error_msg = initialize_ollama_llm()

        if not success:
            return False, f"Error en inicialización: {error_msg}", [
                "Reiniciar el servicio Ollama",
                "Verificar recursos del sistema (RAM, CPU)",
                "Comprobar logs de Ollama para errores"
            ]

        print("[OK] Inicialización exitosa")

        # 4. Verificar dependencias de embeddings
        print("[4] Verificando dependencias de embeddings...")
        try:
            embedding_function = create_embedding_function()
            print("[OK] Función de embeddings creada")
        except Exception as e:
            return False, f"Error en embeddings: {e}", [
                "Instalar sentence-transformers: pip install sentence-transformers",
                "Verificar conexión a internet para descarga de modelos",
                "Comprobar espacio en disco disponible"
            ]

        # 5. Verificar ChromaDB
        print("[5] Verificando base de datos vectorial...")
        try:
            import chromadb
            from chromadb.config import Settings
            client = chromadb.PersistentClient(
                path=VECTOR_DB_BASE_DIR,
                settings=Settings(anonymized_telemetry=False)
            )
            print("[OK] ChromaDB funcionando")
        except Exception as e:
            return False, f"Error en ChromaDB: {e}", [
                "Instalar chromadb: pip install chromadb",
                "Verificar permisos de escritura en directorio",
                "Comprobar espacio en disco disponible"
            ]

        # 6. Prueba de integración completa
        print("[6] Prueba de integración completa...")
        try:
            # Crear una pequeña base de conocimiento de prueba
            test_content = """
            Este es un documento de prueba para verificar el funcionamiento
            del sistema de IA local. Contiene información sobre procesos legales
            y procedimientos judiciales básicos.
            """

            # Crear archivo temporal
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(test_content)
                temp_file = f.name

            # Indexar
            collection_name = indexar_expediente(client, temp_file, "test_migration")

            if collection_name:
                # Consultar
                result = consultar_expediente(client, collection_name, "¿Qué contiene este documento?")

                if result and not result.get('error'):
                    print("[OK] Integración completa exitosa")

                    # Limpiar
                    try:
                        client.delete_collection(name=collection_name)
                        os.unlink(temp_file)
                    except:
                        pass
                else:
                    return False, "Error en consulta de prueba", [
                        "Verificar configuración de Ollama",
                        "Comprobar recursos del sistema",
                        "Revisar logs para errores específicos"
                    ]
            else:
                return False, "Error en indexación de prueba", [
                    "Verificar función de embeddings",
                    "Comprobar ChromaDB",
                    "Revisar permisos de archivos"
                ]

        except Exception as e:
            return False, f"Error en prueba de integración: {e}", [
                "Ejecutar diagnóstico completo del sistema",
                "Verificar todas las dependencias",
                "Comprobar configuración paso a paso"
            ]

        # Generar recomendaciones de optimización
        recommendations = [
            "Sistema migrado exitosamente a IA local",
            "Ya no se requieren API keys externas",
            f"Modelo {DEFAULT_OLLAMA_MODEL} configurado y funcionando",
            "Considerar ajustar temperatura según necesidades específicas",
            "Monitorear uso de recursos del sistema durante operación"
        ]

        return True, "Migración a IA local completada exitosamente", recommendations

    except Exception as e:
        return False, f"Error inesperado durante migración: {e}", [
            "Ejecutar diagnóstico del sistema",
            "Verificar instalación de dependencias",
            "Consultar logs para más detalles"
        ]