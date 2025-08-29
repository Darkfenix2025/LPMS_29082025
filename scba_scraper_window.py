# scba_scraper.py (Versión v3.0 - "El Lector")

import customtkinter as ctk
import threading
import time
import os
import sys  # <--- ¡AÑADE ESTA LÍNEA!
import re # Módulo para limpieza de texto
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import WebDriverException, NoSuchElementException #Agregado por Copilot


class TextboxRedirector:
    def __init__(self, textbox): self.textbox = textbox
    def write(self, text): self.textbox.after(0, self._insert_text, text)
    def _insert_text(self, text): self.textbox.insert(ctk.END, text); self.textbox.see(ctk.END)
    def flush(self): pass

class SCBAScraperWindow(ctk.CTkToplevel): # Hereda de CTkToplevel
    def __init__(self, parent): # Acepta parent
        super().__init__(parent) # Llama al __init__ de CTkToplevel
        self.title("SCBA MEV - Asistente de Extracción v3.0")
        self.geometry("800x500")
        self.parent = parent # Guardar referencia al parent si es necesario para algo

        self.driver = None
        self.worker_thread = None
        self.protocol("WM_DELETE_WINDOW", self.safe_close)
        self.log_file_name = "extracted_links_scba.log" # Considerar hacerlo específico de la instancia o configurable
        
        # Directorio de descarga por defecto
        self.default_download_dir = os.path.join(os.path.expanduser('~'), "Descargas_SCBA_Texto")
        self.current_download_dir = self.default_download_dir # Directorio actual, puede ser cambiado

        # --- Creación de Widgets ---
        self.main_frame=ctk.CTkFrame(self);self.main_frame.pack(pady=10,padx=20,fill="x") # Menos pady superior
        self.start_button=ctk.CTkButton(self.main_frame,text="1. Iniciar Navegador",command=self.start_browser_thread);self.start_button.pack(side="left",padx=5,pady=10) # Reducido padx
        self.download_button=ctk.CTkButton(self.main_frame,text="2. Extraer Textos",command=self.start_extraction_thread,state="disabled");self.download_button.pack(side="left",padx=5,pady=10) # Reducido padx
        
        # Botón para cambiar directorio de descarga
        self.change_dir_button = ctk.CTkButton(self.main_frame, text="Cambiar Carpeta", command=self.change_download_directory, width=120)
        self.change_dir_button.pack(side="left", padx=5, pady=10)
        
        self.close_button=ctk.CTkButton(self.main_frame,text="Cerrar",command=self.safe_close,fg_color="firebrick");self.close_button.pack(side="right",padx=5,pady=10) # Reducido padx
        
        # Etiqueta para mostrar directorio de descarga actual
        self.dir_label_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dir_label_frame.pack(pady=(0,5), padx=20, fill="x")
        ctk.CTkLabel(self.dir_label_frame, text="Guardando en:").pack(side="left")
        self.current_dir_label = ctk.CTkLabel(self.dir_label_frame, text=self.current_download_dir, anchor="w")
        self.current_dir_label.pack(side="left", fill="x", expand=True, padx=(5,0))

        self.log_textbox=ctk.CTkTextbox(self,state="normal",wrap="word");self.log_textbox.pack(pady=(0,10),padx=20,fill="both",expand=True) # Reducido pady superior
        
        # Guardar la referencia original de stdout para restaurarla si es necesario,
        # aunque para un Toplevel puede no ser estrictamente necesario si se maneja bien el cierre.
        self.original_stdout = sys.stdout 
        sys.stdout = TextboxRedirector(self.log_textbox)
        print("Bienvenido. Haz clic en 'Iniciar Navegador'.")
        print(f"Directorio de descarga actual: {self.current_download_dir}")


    def change_download_directory(self):
        new_dir = ctk.filedialog.askdirectory(title="Seleccionar Carpeta de Descarga para SCBA", initialdir=self.current_download_dir)
        if new_dir:
            self.current_download_dir = new_dir
            self.current_dir_label.configure(text=self.current_download_dir)
            print(f"Directorio de descarga cambiado a: {self.current_download_dir}")
            # Recrear el directorio si no existe (aunque askdirectory usualmente devuelve uno existente)
            if not os.path.exists(self.current_download_dir):
                try:
                    os.makedirs(self.current_download_dir)
                    print(f"Directorio creado: {self.current_download_dir}")
                except Exception as e:
                    print(f"Error al crear directorio {self.current_download_dir}: {e}")
                    # Podríamos revertir al directorio anterior o mostrar un error más prominente
        else:
            print("Cambio de directorio cancelado.")

    def open_browser(self):
        try:
            if not os.path.exists(self.current_download_dir): os.makedirs(self.current_download_dir) # Usar current_download_dir
            
            # Configuración de opciones de Chrome para Selenium (ejemplo)
            chrome_options = Options()
            # chrome_options.add_argument("--headless") # Descomentar para modo headless
            # chrome_options.add_argument("--disable-gpu") # Necesario para headless en algunos sistemas
            # Considerar añadir más opciones si son necesarias (ej. user-agent)

            self.driver = webdriver.Chrome(options=chrome_options) # Pasar opciones aquí
            self.driver.get("https://mev.scba.gov.ar/loguin.asp")
            self.driver.maximize_window()
            print("\nNavegador listo! Navega hasta la página de 'Pasos Procesales'.")
            print(f"Los textos se guardarán en: {self.current_download_dir}") # Usar current_download_dir
            self.download_button.configure(state="normal")
        except WebDriverException as e:
            if "net::ERR_CONNECTION_REFUSED" in str(e) or "This version of ChromeDriver only supports Chrome version" in str(e):
                 logging.error(f"Problema con ChromeDriver o conexión: {e}")
                 logging.error("Por favor, asegúrate de que ChromeDriver esté instalado y sea compatible con tu versión de Chrome.")
                 logging.error("Puedes descargarlo desde: https://chromedriver.chromium.org/downloads")
            else:
                logging.error(f"No se pudo iniciar el navegador: {e}")
            self.start_button.configure(state="normal",text="1. Iniciar Navegador") # Reactivar botón
        except Exception as e: # Captura más general
            logging.error(f"Error inesperado iniciando navegador: {type(e).__name__}: {e}")
            self.start_button.configure(state="normal",text="1. Iniciar Navegador")


    def start_browser_thread(self):
        self.start_button.configure(state="disabled",text="Navegador Abierto...")
        self.worker_thread = threading.Thread(target=self.open_browser); self.worker_thread.start()

    def start_extraction_thread(self):
        if not self.driver or not self.is_driver_active():
            print("\nError: El navegador no está iniciado.");self.start_button.configure(state="normal",text="1. Iniciar Navegador");return
        self.download_button.configure(state="disabled",text="Extrayendo...")
        self.worker_thread = threading.Thread(target=self.extract_documents); self.worker_thread.start()

    # --- ¡NUEVO! Método de extracción precisa ---
    def extraer_datos_quirurgicamente(self):
        """
        Extrae la información clave de la página de proveído de la MEV
        utilizando selectores HTML específicos para máxima precisión.
        """
        info_consolidada = []
        try:
            celdas_referencias = self.driver.find_elements(By.XPATH, "//td[@class='fondoceleste']")
            for celda in celdas_referencias:
                texto_celda = celda.text
                if "Funcionario Firmante" in texto_celda: info_consolidada.append(f"[Funcionario Firmante]: {texto_celda.split(':', 1)[1].strip()}")
                elif "Fecha de Libramiento:" in texto_celda: info_consolidada.append(f"[Fecha de Libramiento]: {texto_celda.split(':', 1)[1].strip()}")
        except Exception as e:
            print(f"Aviso: No se pudieron extraer metadatos. Error: {e}")

        try:
            texto_principal_div = self.driver.find_element(By.ID, "contenidoTxt")
            texto_principal = texto_principal_div.text
            marcador_inicio = "------- Para copiar y pegar el texto seleccione desde aquí (sin incluir esta línea) -------"
            marcador_fin = "------- Para copiar y pegar el texto seleccione hasta aquí (sin incluir esta línea) -------"
            texto_principal = texto_principal.replace(marcador_inicio, "").replace(marcador_fin, "")
            info_consolidada.append("\n--- TEXTO DEL PROVEÍDO ---\n")
            info_consolidada.append(texto_principal.strip())
        except NoSuchElementException:
            print("ERROR: No se encontró el contenedor de texto principal (id='contenidoTxt').")
            return "ERROR: Contenido no encontrado"
            
        return "\n".join(info_consolidada)
    #-------------------------------------------------------

    def extract_documents(self):
        try:
            print("\n--------------------------------------------------")
            print("Iniciando proceso de extracción de textos...")
            extracted_urls = set()
            try:
                with open(self.log_file_name, 'r', encoding='utf-8') as f: # Especificar encoding
                    extracted_urls = set(f.read().splitlines())
                print(f"Se cargaron {len(extracted_urls)} URLs desde el log.")
            except FileNotFoundError:
                print("No se encontró un log previo.")

            selector_xpath = "//a[contains(@href, 'proveido.asp')]"
            
            links = self.driver.find_elements(By.XPATH, selector_xpath)
            urls_to_process = [link.get_attribute('href') for link in links]

            if not urls_to_process:
                print("No se encontraron enlaces de proveídos en la página."); return

            print(f"Se encontraron {len(urls_to_process)} documentos para extraer.")
            new_extractions = 0

            for i, url in enumerate(urls_to_process):
                if not self.is_driver_active(): # Chequear antes de cada acción
                    logging.error("El navegador se cerró inesperadamente.")
                    break
                if url in extracted_urls:
                    logging.debug(f"({i+1}/{len(urls_to_process)}) Saltando, ya extraído: {url.split('?')[1] if '?' in url else url[-20:]}")
                    continue
                
                logging.info(f"({i+1}/{len(urls_to_process)}) Extrayendo: {url.split('?')[1] if '?' in url else url[-20:]} ...")
                
                self.driver.get(url)
                time.sleep(0.5) # Pequeña pausa para carga de página
                
                page_text = self.extraer_datos_quirurgicamente()
                
                query_part = url.split('?')[1] if '?' in url else url.split('/')[-1]
                filename_safe_part = re.sub(r'[^\w\-_\. ]', '_', query_part)
                filename = f"proveido_{filename_safe_part}.txt"
                file_path = os.path.join(self.current_download_dir, filename) # Usar current_download_dir

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(page_text)
                
                print(f"   -> Guardado como: {filename}")

                if not self.is_driver_active(): break # Chequear después de guardar
                self.driver.back()
                time.sleep(1) 

                new_extractions += 1
                with open(self.log_file_name, 'a', encoding='utf-8') as f: f.write(url + '\n') # Especificar encoding
                extracted_urls.add(url)
            
            print(f"\n¡Extracción de lote finalizada! Se extrajeron {new_extractions} nuevos textos.")

        except WebDriverException as e:
             logging.error(f"Error Selenium durante la extracción: {type(e).__name__} - {e}")
        except Exception as e:
            logging.error(f"Error inesperado durante la extracción: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc() # Imprimir traceback completo para errores inesperados
        finally:
            if self.is_driver_active(): self.download_button.configure(state="normal", text="2. Extraer Textos")
            else: self.download_button.configure(state="disabled", text="Navegador cerrado")
            print("Proceso finalizado.")

    def is_driver_active(self):
        try:
            # Un chequeo más robusto que solo self.driver.title
            # Intenta obtener la URL actual. Si falla, el driver no está activo.
            self.driver.current_url 
            return True
        except WebDriverException:
            return False
        except AttributeError: # Si self.driver es None
             return False

    def safe_close(self):
        print("Cerrando ventana del scraper...")
        # Restaurar stdout
        sys.stdout = self.original_stdout

        if self.worker_thread and self.worker_thread.is_alive():
            print("Esperando que el hilo de trabajo finalice...")
            # No se puede hacer join directamente desde el hilo principal de Tkinter si el hilo
            # está interactuando con la GUI. Se podría usar un evento o simplemente dejarlo.
            # Por ahora, solo cerramos el driver.
            # self.worker_thread.join(timeout=2) # Darle un tiempo para terminar
            pass

        if self.driver:
            try:
                print("Cerrando navegador (driver.quit())...")
                self.driver.quit()
                self.driver = None # Marcar como cerrado
                print("Navegador cerrado.")
            except Exception as e:
                print(f"Error al cerrar el driver: {e}")
        
        # Para CTkToplevel, se usa destroy()
        self.destroy() 
        print("Ventana del scraper destruida.")

# Esto es para prueba independiente, se quitará al integrar
if __name__ == "__main__": 
    import sys # Necesario para self.original_stdout
    app = SCBAScraperWindow(None)
    app.mainloop()
