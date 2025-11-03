from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import csv
import traceback
from datetime import datetime
import unicodedata

BASE_URL = 'https://www.cineplanet.com.pe'
HEADLESS = False  # True = modo sin ventana (menos recursos, evita suspensión de PC)
TIMEOUT = 20
MAX_CINES = None  # PRUEBA: 1 cine

EMAIL = "72669293"
PASSWORD = "Lizmoi2003"

def configurar_driver(headless=HEADLESS):
    print("Configurando Chrome WebDriver...")
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Suprimir errores de consola de Chrome
    options.add_argument('--log-level=3')  # Solo errores FATALES
    options.add_argument('--disable-logging')
    options.add_argument('--disable-gpu')  # Evitar errores de GPU
    options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suprimir DevTools listening
    
    # Deshabilitar notificaciones del navegador
    prefs = {
        "profile.default_content_setting_values.notifications": 2,  # 2 = bloquear notificaciones
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.media_stream_mic": 2,
        "profile.default_content_setting_values.media_stream_camera": 2
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("WebDriver configurado\n")
    return driver

def manejar_popups_iniciales(driver):
    """
    Maneja los popups de cookies y notificaciones al entrar a Cineplanet
    """
    try:
        print("Manejando popups iniciales...")
        time.sleep(2)
        
        # Aceptar cookies
        selectores_cookies = [
            "button:contains('Aceptar Cookies')",
            "button[class*='accept']",
            "button[id*='accept']",
            "//button[contains(text(), 'Aceptar')]",
            "//button[contains(text(), 'ACEPTAR')]",
            ".cookie-accept",
            "#cookie-accept",
            "button[aria-label*='accept']"
        ]
        
        cookies_aceptadas = False
        for selector in selectores_cookies:
            try:
                if selector.startswith("//"):
                    boton = driver.find_element(By.XPATH, selector)
                else:
                    boton = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].click();", boton)
                cookies_aceptadas = True
                print("  ✓ Cookies aceptadas")
                time.sleep(1)
                break
            except:
                continue
        
        if not cookies_aceptadas:
            try:
                driver.execute_script("""
                    document.querySelectorAll('[class*="cookie"], [class*="consent"]').forEach(el => el.remove());
                """)
            except:
                pass
        
        # Cerrar cualquier modal o overlay adicional
        try:
            driver.execute_script("""
                document.querySelectorAll('[class*="modal"], [class*="overlay"], [class*="popup"]').forEach(el => el.remove());
            """)
        except:
            pass
        
        print("  ✓ Popups manejados\n")
        
    except Exception as e:
        print(f"Advertencia manejando popups: {e}\n")

def normalizar_slug(nombre):
    """
    Normaliza nombre de cine a slug para URL
    'CP Centro Jr. De La Unión' → 'cp-centro-jr-de-la-union'
    """
    # Convertir a minúsculas
    slug = nombre.lower()
    
    # Remover acentos
    slug = ''.join(
        c for c in unicodedata.normalize('NFD', slug)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Reemplazar espacios y puntos por guiones
    slug = slug.replace(' ', '-').replace('.', '')
    
    # Remover múltiples guiones consecutivos
    while '--' in slug:
        slug = slug.replace('--', '-')
    
    # Remover guiones al inicio/final
    slug = slug.strip('-')
    
    return slug

def hacer_login(driver, es_relogin=False):
    if not EMAIL or not PASSWORD:
        print("Sin credenciales - Solo precios sin beneficio\n")
        return False
    try:
        if es_relogin:
            print("   → Re-login...")
        else:
            print("Intentando hacer login...")
        
        # Ir a página de login
        driver.get(f"{BASE_URL}/autenticacion/login")
        time.sleep(5)
        
        # Manejar popups
        try:
            manejar_popups_iniciales(driver)
        except:
            pass
        
        time.sleep(2)
        
        # Usar los selectores correctos del HTML de Cineplanet
        print("  → Buscando campo de DNI/Código...")
        timeout_login = 20 if es_relogin else TIMEOUT
        email_input = WebDriverWait(driver, timeout_login).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='cineplanet-code']"))
        )
        print("  → Campo encontrado, ingresando DNI...")
        email_input.clear()
        time.sleep(0.5)
        email_input.send_keys(EMAIL)
        time.sleep(1)
        
        # Campo PASSWORD
        print("  → Buscando campo de contraseña...")
        password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        print("  → Campo encontrado, ingresando contraseña...")
        password_input.clear()
        password_input.send_keys(PASSWORD)
        time.sleep(1)
        
        # Botón de login
        print("  → Buscando botón de login...")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        print("  → Haciendo clic en login...")
        login_button.click()
        
        time.sleep(7)
        
        # Verificar si el login fue exitoso
        print(f"  → URL actual: {driver.current_url}")
        if "login" not in driver.current_url.lower() and "autenticacion" not in driver.current_url.lower():
            print("✓ Login exitoso\n")
            return True
        else:
            print("✗ Login falló - aún en página de login\n")
            try:
                errores = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error']")
                if errores:
                    print(f"  Mensajes de error: {[e.text for e in errores if e.text.strip()]}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"✗ Error en login: {e}\n")
        traceback.print_exc()
        return False

def cargar_lista_cines_desde_txt():
    """
    Carga la lista de cines desde el archivo TXT
    Retorna: ['CP Alcazar', 'CP Brasil', ..., 'CP Villa María del Triunfo']
    """
    try:
        with open('lista_cines.txt', 'r', encoding='utf-8') as f:
            # Leer líneas, quitar espacios en blanco y filtrar líneas vacías
            cines = [linea.strip() for linea in f.readlines() if linea.strip()]
        
        print(f"✓ Cargados {len(cines)} cines desde 'lista_cines.txt'")
        
        # Aplicar límite si existe
        if MAX_CINES and len(cines) > MAX_CINES:
            cines = cines[:MAX_CINES]
            print(f"  (Limitado a {MAX_CINES} por configuración)")
        
        print(f"\nLista de cines:")
        for i, nombre in enumerate(cines, 1):
            slug = normalizar_slug(nombre)
            print(f"   {i:2d}. {nombre:45s} → {slug}")
        print()
        
        return cines
        
    except FileNotFoundError:
        print(f"✗ ERROR: No se encontró el archivo 'lista_cines.txt'")
        print(f"   Por favor, crea el archivo con la lista de cines (un cine por línea)")
        return []
    except Exception as e:
        print(f"✗ ERROR leyendo archivo: {e}")
        return []

def cancelar_compra(driver):
    """
    Cancela la compra actual haciendo clic en el botón de cerrar y luego 'Cancelar Compra'.
    """
    try:
        print("              → Cancelando compra...")
        time.sleep(2)
        
        # 1. Buscar y hacer clic en el botón de cerrar (X)
        try:
            # Selector correcto: botón con icono de cerrar
            selectores_cerrar = [
                "button.purchase-header-icon-container--button",
                "button:has(span.cineplanet-icon_close)",
                "span.cineplanet-icon_close",
            ]
            
            boton_cerrar = None
            for selector in selectores_cerrar:
                try:
                    elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elementos:
                        if elem.is_displayed():
                            boton_cerrar = elem
                            break
                    if boton_cerrar:
                        break
                except:
                    continue
            
            if boton_cerrar:
                driver.execute_script("arguments[0].click();", boton_cerrar)
                time.sleep(2)
                print("              ✓ Botón cerrar clickeado")
            else:
                print("              No se encontró botón de cerrar")
                return False
                
        except Exception as e:
            print(f"              ✗ Error cerrando: {str(e)[:50]}")
            return False
        
        # 2. Buscar y hacer clic en "Cancelar Compra"
        try:
            # Selector correcto: span con clase call-to-action--text
            selectores_cancelar = [
                "//span[@class='call-to-action--text' and contains(text(), 'Cancelar Compra')]/parent::button",
                "//span[contains(@class, 'call-to-action--text') and contains(text(), 'Cancelar')]/parent::*",
                "button:has(span:contains('Cancelar Compra'))",
            ]
            
            boton_cancelar = None
            for selector in selectores_cancelar:
                try:
                    if selector.startswith("//"):
                        boton_cancelar = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        boton_cancelar = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    break
                except:
                    continue
            
            if boton_cancelar:
                driver.execute_script("arguments[0].click();", boton_cancelar)
                time.sleep(2)
                print("              ✓ Compra cancelada")
                return True
            else:
                print("              No se encontró botón 'Cancelar Compra'")
                return False
                
        except Exception as e:
            print(f"              ✗ Error cancelando compra: {str(e)[:50]}")
            return False
            
    except Exception as e:
        print(f"              ✗ Error en cancelar_compra: {str(e)[:50]}")
        return False
            
    except Exception as e:
        print(f"              Error cancelando compra: {str(e)[:50]}")
        return False

def limpiar_cache_y_datos_navegador(driver):
    """
    Limpieza selectiva que NO elimina cookies de sesión/login
    Solo limpia localStorage y sessionStorage
    """
    try:
        print("              → Limpiando datos temporales...")
        
        # 1. Limpiar localStorage
        try:
            driver.execute_script("window.localStorage.clear();")
        except Exception as e:
            pass
        
        # 2. Limpiar sessionStorage
        try:
            driver.execute_script("window.sessionStorage.clear();")
        except Exception as e:
            pass
        
        # 3. NO eliminamos cookies - mantener sesión activa
        # Las cookies contienen información de login que necesitamos preservar
        
        # 4. Pequeña pausa para que los cambios se propaguen
        time.sleep(1)
        
        print("              ✓ Limpieza completada (sesión preservada)")
        return True
        
    except Exception as e:
        print(f"              ⚠️ Error en limpieza: {str(e)[:50]}")
        return False

def limpiar_cache_y_datos_navegador(driver):
    """
    Limpieza selectiva que NO elimina cookies de sesión/login
    Solo limpia localStorage y sessionStorage
    """
    try:
        # 1. Limpiar localStorage
        try:
            driver.execute_script("window.localStorage.clear();")
        except:
            pass
        
        # 2. Limpiar sessionStorage
        try:
            driver.execute_script("window.sessionStorage.clear();")
        except:
            pass
        
        # 3. NO eliminamos cookies - mantener sesión activa
        # Las cookies contienen información de login que necesitamos preservar
        
        # 4. Pequeña pausa
        time.sleep(0.5)
        
        return True
        
    except Exception as e:
        return False

def seleccionar_asiento_y_continuar(driver):
    """
    Selecciona un asiento disponible y hace clic en Continuar.
    Retorna: éxito (bool)
    """
    try:
        print("              → Seleccionando asiento...")
        time.sleep(3)
        
        # Cerrar cualquier popup que pueda estar bloqueando
        try:
            manejar_popups_iniciales(driver)
        except:
            pass
        
        # Buscar un asiento disponible
        asiento_selector = ".seat-map--seat.seat-map--seat_available"
        
        try:
            asiento = WebDriverWait(driver, TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, asiento_selector))
            )
            
            # Scroll al asiento y hacer clic
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", asiento)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", asiento)
            time.sleep(2)
            print("              ✓ Asiento seleccionado")
            
        except TimeoutException:
            print("              ✗ No hay asientos disponibles")
            return False
        
        # Verificar si hay algún mensaje de error o alerta
        try:
            error_msg = driver.find_element(By.CSS_SELECTOR, ".alert, .error, [class*='error']")
            if error_msg.is_displayed():
                print(f"             Alerta: {error_msg.text[:50]}")
        except:
            pass
        
        # Buscar y hacer clic en el botón "Continuar"
        try:
            # Selector correcto: el texto está dentro de un span con clase call-to-action--text
            selectores_continuar = [
                "//span[@class='call-to-action--text' and contains(text(), 'Continuar')]/parent::button",
                "//span[contains(@class, 'call-to-action--text') and contains(text(), 'Continuar')]/parent::*",
                "button:has(span.call-to-action--text)",
                ".call-to-action--text",
            ]
            
            continuar_btn = None
            for selector in selectores_continuar:
                try:
                    if selector.startswith("//"):
                        continuar_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        continuar_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    print(f"              ✓ Botón encontrado con: {selector}")
                    break
                except:
                    continue
            
            if not continuar_btn:
                print("              ✗ No se encontró botón 'Continuar'")
                return False
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continuar_btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", continuar_btn)
            time.sleep(3)
            print("              ✓ Botón 'Continuar' clickeado")
            return True
            
        except TimeoutException:
            print("              ✗ No se encontró botón 'Continuar'")
            return False
        except Exception as e:
            print(f"              ✗ Error en botón Continuar: {str(e)[:100]}")
            return False
            
    except Exception as e:
        print(f"              ✗ Error seleccionando asiento: {str(e)[:100]}")
        return False

def extraer_precios_de_pagina(driver, tiene_sesion):
    """
    Extrae precios generales y precios con beneficio de la página de compra.
    Retorna: [{'precio': '41.00', 'tipo': 'General 3D OL', 'beneficio': 'No'}, ...]
    """
    precios = []
    try:
        time.sleep(3)
        
        # 1. EXTRAER PRECIOS GENERALES (sin beneficio)
        print("              → Extrayendo precios generales...")
        try:
            # Buscar directamente las categorías de entradas (sin buscar contenedor padre)
            categorias_generales = driver.find_elements(By.CSS_SELECTOR, ".purchase-tickets--common-tickets--categories .purchase-tickets--common-tickets-categories")
            
            print(f"              → Encontradas {len(categorias_generales)} categorías generales")
            
            for categoria in categorias_generales:
                try:
                    # Extraer el título (tipo de entrada)
                    titulo_elem = categoria.find_element(By.CSS_SELECTOR, ".purchase-tickets--common-tickets-categories--title")
                    tipo = titulo_elem.text.strip()
                    
                    # Extraer el precio
                    precio_elem = categoria.find_element(By.CSS_SELECTOR, ".purchase-tickets--common-tickets-categories--price span")
                    precio_texto = precio_elem.text.strip()
                    
                    # Limpiar el precio (remover S/ y espacios)
                    precio = precio_texto.replace('S/', '').strip()
                    
                    if precio and tipo:
                        precios.append({
                            'precio': precio,
                            'tipo': tipo,
                            'beneficio': 'No'
                        })
                        print(f"                ✓ {tipo}: S/{precio} (General)")
                        
                except Exception as e:
                    # Categoría sin precio o elemento faltante
                    continue
                    
        except Exception as e:
            print(f"              ✗ No se encontró sección de entradas generales: {str(e)[:80]}")
        
        # 2. EXTRAER PRECIOS CON BENEFICIO (si tiene sesión)
        if tiene_sesion:
            print("              → Extrayendo precios con beneficio...")
            try:
                # Buscar el contenedor de beneficios
                beneficios_wrapper = driver.find_elements(By.CSS_SELECTOR, ".purchase-tickets-benefits--wrapper")
                
                if beneficios_wrapper:
                    print(f"              → Sección de beneficios encontrada")
                    
                    # Verificar si dice "No tienes vouchers disponibles"
                    texto_wrapper = beneficios_wrapper[0].text
                    if "No tienes vouchers disponibles" in texto_wrapper or "No tienes beneficios" in texto_wrapper:
                        print(f"              → No hay beneficios disponibles para esta función")
                    else:
                        # Extraer categorías con beneficio
                        categorias_beneficio = beneficios_wrapper[0].find_elements(By.CSS_SELECTOR, ".purchase-tickets--common-tickets-categories")
                        
                        print(f"              → Encontradas {len(categorias_beneficio)} categorías con beneficio")
                        
                        for categoria in categorias_beneficio:
                            try:
                                # Extraer el título (tipo de entrada/beneficio)
                                titulo_elem = categoria.find_element(By.CSS_SELECTOR, ".purchase-tickets--common-tickets-categories--title")
                                tipo = titulo_elem.text.strip()
                                
                                # Extraer el precio
                                precio_elem = categoria.find_element(By.CSS_SELECTOR, ".purchase-tickets--common-tickets-categories--price span")
                                precio_texto = precio_elem.text.strip()
                                
                                # Limpiar el precio
                                precio = precio_texto.replace('S/', '').strip()
                                
                                if precio and tipo:
                                    precios.append({
                                        'precio': precio,
                                        'tipo': tipo,
                                        'beneficio': 'Si'
                                    })
                                    print(f"                ✓ {tipo}: S/{precio} (Beneficio)")
                                    
                            except Exception as e:
                                continue
                else:
                    print(f"              → No se encontró sección de beneficios")
                    
            except Exception as e:
                print(f"              ✗ Error extrayendo beneficios: {str(e)[:80]}")
        
        print(f"              → Total precios extraídos: {len(precios)} ({len([p for p in precios if p['beneficio'] == 'No'])} generales, {len([p for p in precios if p['beneficio'] == 'Si'])} con beneficio)")
        
        return precios
        
    except Exception as e:
        print(f"              ✗ Error en extracción de precios: {str(e)[:100]}")
        return []

def extraer_modalidades_y_horarios_de_pelicula(elemento_pelicula):
    """
    Extrae las modalidades (2D REGULAR, 2D PRIME, 3D, etc) y sus horarios
    Retorna: [{'modalidad': '2D REGULAR DOBLADA', 'horario_boton': <WebElement>}, ...]
    """
    modalidades_horarios = []
    try:
        # Buscar botones de horario directamente en la película
        botones_horario = elemento_pelicula.find_elements(By.CSS_SELECTOR, "button.showtime-selector--link")
        
        if not botones_horario:
            return []
        
        # Tomar el primer botón de horario
        primer_boton = botones_horario[0]
        
        # Intentar extraer la modalidad del elemento padre o contenedor
        try:
            # Buscar el contenedor de formato que contiene este botón
            formato_container = primer_boton.find_element(By.XPATH, "./ancestor::*[contains(@class, 'showtime-format')]")
            modalidad = formato_container.text.split('\n')[0].strip()  # Primer línea es la modalidad
        except:
            try:
                # Alternativa: buscar texto de formato cerca del botón
                formato_elem = elemento_pelicula.find_element(By.CSS_SELECTOR, ".showtime-format")
                modalidad = formato_elem.text.split('\n')[0].strip()
            except:
                # Si no encuentra modalidad, usar el texto completo del elemento
                texto_completo = elemento_pelicula.text
                # Buscar líneas que parezcan modalidades (contienen "2D", "3D", "REGULAR", etc)
                lineas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
                for linea in lineas:
                    if any(keyword in linea.upper() for keyword in ['2D', '3D', 'IMAX', 'REGULAR', 'PRIME', 'DOBLADA', 'SUBTITULADA']):
                        modalidad = linea
                        break
                else:
                    modalidad = "2D REGULAR"
        
        modalidades_horarios.append({
            'modalidad': modalidad,
            'horario_boton': primer_boton
        })
        
        return modalidades_horarios
        
    except Exception as e:
        print(f"        ✗ Error extrayendo modalidades: {str(e)[:50]}")
        return []

def extraer_peliculas_y_precios_de_cine(driver, cine_nombre, tiene_sesion):
    """
    Procesa un cine: detecta películas, modalidades y extrae precios
    """
    print(f"  Procesando cine: {cine_nombre}")
    datos_extraidos = []
    
    try:
        # Construir URL del cine directamente
        cine_slug = normalizar_slug(cine_nombre)
        url_cine = f"{BASE_URL}/cinemas/{cine_slug}"
        
        print(f"     URL: {url_cine}")
        driver.get(url_cine)
        time.sleep(3)
        
        # Manejar popups
        manejar_popups_iniciales(driver)
        
        # Scroll para cargar películas
        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Buscar películas
        selector_correcto = "div.movies-list-schedules--large-item"
        peliculas_encontradas = driver.find_elements(By.CSS_SELECTOR, selector_correcto)
        
        print(f"     ✓ Encontradas {len(peliculas_encontradas)} películas")
        
        total_peliculas = len(peliculas_encontradas)
        MAX_PELICULAS = None  # PRUEBA: 1 película
        
        # USAR ÍNDICES para evitar elementos stale
        idx_pelicula = 0
        while idx_pelicula < total_peliculas and (MAX_PELICULAS is None or idx_pelicula < MAX_PELICULAS):
            try:
                # Re-obtener elementos
                peliculas_refresh = driver.find_elements(By.CSS_SELECTOR, selector_correcto)
                if idx_pelicula >= len(peliculas_refresh):
                    break
                
                pelicula_elem = peliculas_refresh[idx_pelicula]
                
                # Extraer nombre
                try:
                    nombre_elem = pelicula_elem.find_element(By.CSS_SELECTOR, "h2.movies-list-schedules--large-movie-description-title")
                    nombre_pelicula = nombre_elem.text.strip()
                except:
                    nombre_pelicula = f"Película_{idx_pelicula+1}"
                
                print(f"\n     [{idx_pelicula+1}/{total_peliculas}] {nombre_pelicula}")
                
                # Extraer modalidades y horarios
                modalidades = extraer_modalidades_y_horarios_de_pelicula(pelicula_elem)
                
                if not modalidades:
                    print(f"        Sin horarios disponibles")
                    idx_pelicula += 1
                    continue
                
                # Procesar cada modalidad
                for modalidad_data in modalidades:
                    modalidad = modalidad_data['modalidad']
                    horario_boton = modalidad_data['horario_boton']
                    
                    print(f"        → Modalidad: {modalidad}")
                    
                    try:
                        # Scroll y click en horario
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", horario_boton)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", horario_boton)
                        time.sleep(3)
                        
                        # Verificar que estamos en /asientos
                        if '/asientos' not in driver.current_url:
                            print(f"              ✗ No se llegó a página de asientos")
                            driver.get(url_cine)
                            time.sleep(2)
                            continue
                        
                        # Seleccionar asiento y continuar
                        if not seleccionar_asiento_y_continuar(driver):
                            print(f"              ✗ No se pudo seleccionar asiento")
                            driver.get(url_cine)
                            time.sleep(2)
                            continue
                        
                        # Extraer precios
                        precios = extraer_precios_de_pagina(driver, tiene_sesion)
                        
                        for precio_data in precios:
                            datos_extraidos.append({
                                'cine': cine_nombre,
                                'pelicula': nombre_pelicula,
                                'modalidad': modalidad,
                                'tipo_entrada': precio_data['tipo'],
                                'precio': precio_data['precio'],
                                'beneficio': precio_data['beneficio']
                            })
                        
                        print(f"              ✓ Extraídos {len(precios)} precios")
                        
                        # Cancelar compra
                        cancelar_compra(driver)
                        
                        # Limpiar datos temporales (localStorage y sessionStorage)
                        limpiar_cache_y_datos_navegador(driver)
                        
                        # ESTRATEGIA SIMPLE: Siempre hacer re-login después de cada película
                        # Cineplanet cierra la sesión automáticamente, así que re-autenticamos
                        print("              → Haciendo re-login para siguiente película...")
                        if EMAIL and PASSWORD:
                            tiene_sesion = hacer_login(driver, es_relogin=True)
                        
                        # Volver al cine
                        driver.get(url_cine)
                        time.sleep(3)
                        
                    except Exception as e:
                        print(f"              ✗ Error en modalidad: {str(e)[:50]}")
                        driver.get(url_cine)
                        time.sleep(2)
                        continue
                
                idx_pelicula += 1
                
            except Exception as e:
                print(f"        ✗ Error en película: {str(e)[:50]}")
                idx_pelicula += 1
                continue
        
        print(f"\n  ✓ Extraídos {len(datos_extraidos)} registros de precios para {cine_nombre}\n")
        return datos_extraidos
        
    except Exception as e:
        print(f"  ✗ Error en cine {cine_nombre}: {e}\n")
        traceback.print_exc()
        return []

def main():
    print("=" * 80)
    print("CINEPLANET PERU - EXTRACTOR DE PRECIOS V4 (SIMPLIFICADO)")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL Base: {BASE_URL}")
    print(f"Modo: {'Headless (sin ventana)' if HEADLESS else 'Navegador Visible'}")
    print(f"Limite de cines: {MAX_CINES if MAX_CINES else 'Todos'}")
    print(f"Login: {'Activado' if EMAIL else 'Desactivado'}")
    print()
    print("CARACTERÍSTICAS:")
    print("  ✓ Carga cines desde lista_cines.txt")
    print("  ✓ Construcción directa de URLs (sin clicks)")
    print("  ✓ Guardado incremental en CSV")
    print("=" * 80)
    print()
    
    # Definir nombre del archivo de progreso
    archivo_progreso = "precios_cineplanet_EN_PROGRESO.csv"
    
    driver = None
    todos_los_datos = []
    try:
        # Configurar driver
        driver = configurar_driver()
        
        # Login (opcional)
        tiene_sesion = False
        if EMAIL and PASSWORD:
            tiene_sesion = hacer_login(driver)
        
        # Cargar lista de cines desde TXT
        nombres_cines = cargar_lista_cines_desde_txt()
        
        if not nombres_cines:
            print("✗ No se pudieron cargar cines")
            return
        
        print(f"{'='*80}")
        print(f"PROCESANDO {len(nombres_cines)} CINES")
        print(f"{'='*80}\n")
        
        # Crear archivo CSV con encabezados (sobrescribir si existe)
        with open(archivo_progreso, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'cine', 'pelicula', 'modalidad', 
                'tipo_entrada', 'precio', 'beneficio'
            ])
            writer.writeheader()
        
        # Procesar cada cine
        for idx, cine_nombre in enumerate(nombres_cines, 1):
            print(f"\n[{idx}/{len(nombres_cines)}] {cine_nombre}")
            print("-" * 80)
            
            # Extraer datos del cine
            datos_cine = extraer_peliculas_y_precios_de_cine(driver, cine_nombre, tiene_sesion)
            
            if datos_cine:
                # Guardar INMEDIATAMENTE en CSV
                with open(archivo_progreso, 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'cine', 'pelicula', 'modalidad',
                        'tipo_entrada', 'precio', 'beneficio'
                    ])
                    writer.writerows(datos_cine)
                
                todos_los_datos.extend(datos_cine)
                print(f"✓ Guardados {len(datos_cine)} registros → Total acumulado: {len(todos_los_datos)}")
            
            time.sleep(2)  # Pausa entre cines
        
        # Renombrar archivo final
        if todos_los_datos:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_final = f"precios_cineplanet_COMPLETO_{timestamp}.csv"
            
            import os
            os.rename(archivo_progreso, archivo_final)
            
            print("\n" + "=" * 80)
            print("EXTRACCIÓN COMPLETADA")
            print("=" * 80)
            print(f"✓ Total registros:   {len(todos_los_datos)}")
            print(f"✓ Cines procesados:  {len(set(d['cine'] for d in todos_los_datos))}")
            print(f"✓ Archivo guardado:  {archivo_final}")
            print("=" * 80)
        else:
            print("\nNo se extrajeron datos")
            
    except KeyboardInterrupt:
        print("\n\nExtracción interrumpida por el usuario")
        if todos_los_datos:
            print(f"Datos guardados hasta el momento en: {archivo_progreso}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        traceback.print_exc()
    finally:
        if driver:
            print("\n→ Cerrando navegador...")
            driver.quit()
            print("✓ Proceso finalizado")
    
    print("\n" + "=" * 80)
    print("FINALIZADO")
    print("=" * 80)

if __name__ == "__main__":
    main()
