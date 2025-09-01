import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# --- CONFIGURACIÓN (sin cambios) ---
home_dir = os.path.expanduser('~')
directorio_descargas = os.path.join(home_dir, "Descargas_Expedientes")

if not os.path.exists(directorio_descargas):
    os.makedirs(directorio_descargas)
    print(f"Se ha creado la carpeta: {directorio_descargas}")

chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
  "download.default_directory": directorio_descargas,
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "plugins.always_open_pdf_externally": True
})

# --- INICIO DEL SCRAPPER ---
driver = None
try:
    driver = webdriver.Chrome(options=chrome_options)
    url = "https://scw.pjn.gov.ar/scw"
    driver.get(url)
    driver.maximize_window()

    print("="*50)
    print("ACCIÓN REQUERIDA: Ingresa los datos, completa el captcha y consulta el expediente.")
    print("Cuando la página del expediente haya cargado, vuelve aquí y presiona 'Enter'.")
    print("="*50)
    input()

    # --- FASE 1: DESCARGAR ACTUACIONES RECIENTES ---
    print("\n--- FASE 1: Descargando actuaciones recientes ---")
    pagina_actual = 1
    
    while True:
        print(f"\nProcesando página RECIENTE {pagina_actual}...")
        time.sleep(2)
        
        selector_docs_xpath = "//a[contains(@href, 'download=true')]"
        lista_de_documentos = driver.find_elements(By.XPATH, selector_docs_xpath)

        if not lista_de_documentos:
            print("No se encontraron documentos descargables en esta página.")
        else:
            print(f"Se encontraron {len(lista_de_documentos)} documentos. Descargando...")
            for i in range(len(lista_de_documentos)):
                try:
                    doc_a_descargar = driver.find_elements(By.XPATH, selector_docs_xpath)[i]
                    print(f"  -> Descargando documento {i+1}...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", doc_a_descargar)
                    time.sleep(0.5)
                    doc_a_descargar.click()
                    time.sleep(4)
                except Exception as e:
                    print(f"    Error al descargar el documento {i+1}. Motivo: {e}")
        
        try:
            selector_siguiente_xpath = "//a[.//span[@title='Siguiente']]"
            boton_siguiente = driver.find_element(By.XPATH, selector_siguiente_xpath)
            print(f"Pasando a la página reciente siguiente...")
            driver.execute_script("arguments[0].click();", boton_siguiente)
            pagina_actual += 1
            time.sleep(4)
        except NoSuchElementException:
            print("\nFin de las actuaciones recientes.")
            break

    # --- FASE 2: DESCARGAR ACTUACIONES HISTÓRICAS ---
    print("\n--- FASE 2: Buscando y descargando actuaciones históricas ---")
    try:
        # Hacemos clic en el botón "Ver históricas"
        selector_historicas = "//a[contains(., 'Ver históricas')]"
        boton_historicas = driver.find_element(By.XPATH, selector_historicas)
        
        print("Haciendo clic en 'Ver históricas' y esperando que cargue...")
        driver.execute_script("arguments[0].click();", boton_historicas)
        time.sleep(5) # Damos tiempo extra para que cargue el contenido histórico

        # Reiniciamos el bucle de paginación para las páginas históricas
        pagina_actual = 1
        while True:
            print(f"\nProcesando página HISTÓRICA {pagina_actual}...")
            time.sleep(2)
            
            selector_docs_xpath = "//a[contains(@href, 'download=true')]"
            lista_de_documentos = driver.find_elements(By.XPATH, selector_docs_xpath)

            if not lista_de_documentos:
                print("No se encontraron documentos descargables en esta página.")
            else:
                print(f"Se encontraron {len(lista_de_documentos)} documentos. Descargando...")
                for i in range(len(lista_de_documentos)):
                    try:
                        doc_a_descargar = driver.find_elements(By.XPATH, selector_docs_xpath)[i]
                        print(f"  -> Descargando documento {i+1}...")
                        driver.execute_script("arguments[0].scrollIntoView(true);", doc_a_descargar)
                        time.sleep(0.5)
                        doc_a_descargar.click()
                        time.sleep(4)
                    except Exception as e:
                        print(f"    Error al descargar el documento {i+1}. Motivo: {e}")
            
            try:
                selector_siguiente_xpath = "//a[.//span[@title='Siguiente']]"
                boton_siguiente = driver.find_element(By.XPATH, selector_siguiente_xpath)
                print(f"Pasando a la página histórica siguiente...")
                driver.execute_script("arguments[0].click();", boton_siguiente)
                pagina_actual += 1
                time.sleep(4)
            except NoSuchElementException:
                print("\nFin de las actuaciones históricas.")
                break

    except NoSuchElementException:
        print("No se encontró el botón 'Ver históricas'. El script ha finalizado con las actuaciones recientes.")

finally:
    if driver:
        print("\nDescarga de todo el expediente (recientes e históricas) finalizada.")
        print(f"Los archivos se guardaron en: {directorio_descargas}")
        print("El navegador se cerrará en 10 segundos.")
        time.sleep(10)
        driver.quit()