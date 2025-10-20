from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re
from datetime import datetime

BASE_URL = 'https://www.cineplanet.com.pe'
HEADLESS = False  # False para PROBAR primero (ver navegador), True para producción
TIMEOUT = 20
MAX_CINES = None  # 1 para PROBAR primero, None = TODOS los cines

EMAIL = "72669293"
PASSWORD = "Lizmoi2003"

def configurar_driver(headless=HEADLESS):
    print("⚙️  Configurando Chrome...")
    options = ChromeOptions()
    
    if headless:
        options.add_argument('--headless')
    
    options.add_argument('--disable-notifications')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-popup-blocking')
    
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        print("✅ Chrome configurado")
        return driver
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️  Asegúrate de tener Chrome instalado")
        raise

def manejar_popups_iniciales(driver):
    """
    Maneja los popups de cookies y notificaciones al entrar a Cineplanet
    """
    try:
        time.sleep(2)
        
        # 1. Cerrar popup de notificaciones del navegador (ya bloqueado en opciones)
        
        # 2. Aceptar cookies
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
                if selector.startswith('//'):
                    # XPath
                    boton = driver.find_element(By.XPATH, selector)
                else:
                    # CSS Selector
                    boton = driver.find_element(By.CSS_SELECTOR, selector)
                
                if boton and boton.is_displayed():
                    boton.click()
                    cookies_aceptadas = True
                    time.sleep(1)
                    break
            except:
                continue
        
        if not cookies_aceptadas:
            # Buscar por texto visible
            try:
                botones = driver.find_elements(By.TAG_NAME, "button")
                for boton in botones:
                    texto = boton.text.strip().upper()
                    if 'ACEPTAR' in texto and 'COOKIE' in texto:
                        boton.click()
                        time.sleep(1)
                        break
            except:
                pass
        
        # 3. Cerrar cualquier modal o overlay adicional
        try:
            close_buttons = driver.find_elements(By.CSS_SELECTOR, "button[class*='close'], button[aria-label='close'], .close, [data-dismiss='modal']")
            for btn in close_buttons[:2]:  # Solo primeros 2
                try:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(0.5)
                except:
                    continue
        except:
            pass
        
    except Exception as e:
        pass  # Silencioso, popups no críticos

def normalizar_slug(nombre):
    """
    Normaliza el nombre del cine para URL (slug)
    Ejemplo: 'CP Centro Cívico' → 'cp-centro-civico'
    """
    import unicodedata
    
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

def cargar_lista_cines_desde_txt():
    """
    Carga la lista de cines desde el archivo TXT
    Retorna: ['CP Alcazar', 'CP Angamos', ..., 'CP Villa María del Triunfo']
    """
    LISTA_CINES_FILE = 'lista_cines.txt'
    try:
        with open(LISTA_CINES_FILE, 'r', encoding='utf-8') as f:
            # Leer líneas, quitar espacios en blanco y filtrar líneas vacías
            cines = [linea.strip() for linea in f.readlines() if linea.strip()]
        print(f"✅ Cargados {len(cines)} cines desde '{LISTA_CINES_FILE}'\n")
        return cines
    except FileNotFoundError:
        print(f"❌ ERROR: No se encontró el archivo '{LISTA_CINES_FILE}'")
        print(f"   Por favor, crea el archivo con la lista de cines (un cine por línea)\n")
        return []
    except Exception as e:
        print(f"❌ ERROR leyendo archivo: {e}\n")
        return []

def hacer_login(driver, es_relogin=False):
    if not EMAIL or not PASSWORD:
        print("⚠️  Sin credenciales - Solo precios generales\n")
        return False
    try:
        print("🔐 Iniciando sesión..." if not es_relogin else "🔐 Re-autenticando...")
        
        driver.get(f"{BASE_URL}/autenticacion/login")
        
        # Login DIRECTO sin delays
        email_input = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='cineplanet-code']"))
        )
        email_input.clear()
        email_input.send_keys(EMAIL)
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        password_input.clear()
        password_input.send_keys(PASSWORD)
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        time.sleep(3)
        
        # Verificar éxito
        if "login" not in driver.current_url.lower() and "autenticacion" not in driver.current_url.lower():
            print("✅ Sesión iniciada\n")
            return True
        else:
            print("❌ Login falló\n")
            return False

        
        # Verificar éxito
        if "login" not in driver.current_url.lower() and "autenticacion" not in driver.current_url.lower():
            print("✅ Sesión iniciada\n")
            return True
        else:
            print("❌ Login falló\n")
            return False
            
    except Exception as e:
        print(f"❌ Error en login: {str(e)[:50]}\n")
        return False
def ir_a_cine_directo(driver, nombre_cine):
    """
    Navega directamente a la página del cine usando su URL
    Parámetros:
        driver: Instancia de WebDriver
        nombre_cine: Nombre del cine desde lista_cines.txt (ej: 'CP Alcazar')
    Retorna: True si navegó exitosamente, False en caso contrario
    """
    try:
        # Normalizar nombre para URL
        slug = normalizar_slug(nombre_cine)
        url_cine = f"{BASE_URL}/cinemas/{slug}"
        
        print(f"🎬 Navegando a: {nombre_cine}")
        print(f"   URL: {url_cine}")
        
        # Navegar a la URL con delay aleatorio
        driver.get(url_cine)
        time.sleep(3)  # Delay aleatorio más largo para carga de página

        
        # Verificar si la página cargó correctamente (no es 404)
        page_title = driver.title.lower()
        if "404" in page_title or "not found" in page_title:
            print(f"   ❌ Página no encontrada (404)")
            return False
        
        # Verificar si estamos en la URL correcta
        if "cinemas/" not in driver.current_url:
            print(f"   ❌ Redirigido a otra página (posible error)")
            return False
        
        # Intentar encontrar películas (timeout más largo para cines remotos)
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.movies-list-schedules--large-item'))
            )
            # Contar películas encontradas
            peliculas = driver.find_elements(By.CSS_SELECTOR, 'div.movies-list-schedules--large-item')
            print(f"   ✅ Cine cargado → {len(peliculas)} películas disponibles")
            return True
            
        except TimeoutException:
            # No se encontraron películas, pero verificar si la página del cine existe
            # Buscar otros elementos que indiquen que es una página de cine válida
            try:
                # Intentar encontrar el contenedor de películas (aunque esté vacío)
                contenedor = driver.find_elements(By.CSS_SELECTOR, 'div.movies-list-schedules, div.billboard, section.cinema-detail')
                if contenedor:
                    print(f"   ⚠️  Cine válido pero SIN películas en cartelera")
                    return True
                else:
                    print(f"   ❌ Página del cine no tiene estructura esperada")
                    return False
            except:
                print(f"   ❌ No se pudo verificar estructura de la página")
                return False
        
    except Exception as e:
        print(f"   ❌ Error navegando: {str(e)[:100]}")
        return False

def cancelar_compra(driver):
    """
    Cancela la compra actual haciendo clic en el botón de cerrar y luego 'Cancelar Compra'.
    Esto es mejor que solo limpiar cookies porque cierra la transacción correctamente.
    """
    try:
        print("              → Cancelando compra...")
        
        # Buscar botón de cerrar (X) en el header
        try:
            boton_cerrar = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.purchase-header-icon-container--button"))
            )
            driver.execute_script("arguments[0].click();", boton_cerrar)
            time.sleep(2)
            print("              ✓ Click en botón cerrar (X)")
        except:
            print("              No se encontró botón cerrar")
            return False
        
        # Buscar y hacer clic en "Cancelar Compra"
        try:
            boton_cancelar = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'call-to-action--text') and contains(text(), 'Cancelar Compra')]"))
            )
            driver.execute_script("arguments[0].click();", boton_cancelar)
            time.sleep(2)
            print("              ✓ Compra cancelada correctamente")
            return True
        except:
            print("              No se encontró botón 'Cancelar Compra'")
            return False
            
    except Exception as e:
        print(f"              Error cancelando compra: {str(e)[:50]}")
        return False

def limpiar_cache_y_datos_navegador(driver):
    """
    Limpieza PROFUNDA de todo lo que el servidor podría usar para rastrear compras:
    - Cookies
    - localStorage
    - sessionStorage
    - Cache del navegador
    
    Esto es CRÍTICO para poder hacer múltiples compras sin el error "Error en el servicio"
    """
    try:
        print("              → Limpiando caché y datos del navegador...")
        
        # 1. Limpiar localStorage (puede guardar info del carrito)
        try:
            driver.execute_script("window.localStorage.clear();")
            print("              ✓ localStorage limpiado")
        except Exception as e:
            print(f"              Error limpiando localStorage: {str(e)[:30]}")
        
        # 2. Limpiar sessionStorage (puede guardar estado de sesión)
        try:
            driver.execute_script("window.sessionStorage.clear();")
            print("              ✓ sessionStorage limpiado")
        except Exception as e:
            print(f"              Error limpiando sessionStorage: {str(e)[:30]}")
        
        # 3. Limpiar todas las cookies
        try:
            driver.delete_all_cookies()
            print("              ✓ Cookies eliminadas")
        except Exception as e:
            print(f"              Error eliminando cookies: {str(e)[:30]}")
        
        # 4. Pequeña pausa para que los cambios se propaguen
        time.sleep(1)
        
        print("              ✓ Limpieza profunda completada")
        return True
        
    except Exception as e:
        print(f"              Error en limpieza profunda: {str(e)[:50]}")
        return False

def seleccionar_asiento_y_continuar(driver):
    """
    Selecciona un asiento disponible y hace clic en Continuar.
    Retorna: bool (éxito o fallo)
    """
    try:
        # Buscar asiento disponible DIRECTO
        asiento_selector = ".seat-map--seat.seat-map--seat_available"
        
        try:
            asiento = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, asiento_selector))
            )
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", asiento)
            driver.execute_script("arguments[0].click();", asiento)
            print("              ✓ Asiento seleccionado")
            time.sleep(1)
            
        except TimeoutException:
            print("              ✗ No se encontraron asientos disponibles")
            return False
        
        # Verificar si hay algún mensaje de error o alerta
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"              Alerta detectada: {alert_text}")
            alert.accept()
            return False
        except:
            pass  # No hay alerta
        
        # Buscar botón Continuar DIRECTO
        try:
            print("              → Buscando 'Continuar'...")
            
            boton_continuar = None
            for _ in range(2):
                botones = driver.find_elements(By.XPATH, "//button[contains(@class, 'call-to-action')]//span[contains(text(),'Continuar')]/..")
                for btn in botones:
                    if 'disabled' not in btn.get_attribute('class'):
                        boton_continuar = btn
                        break
                if boton_continuar:
                    break
                time.sleep(1)
            
            if not boton_continuar:
                print("              ✗ Botón 'Continuar' no disponible")
                return False
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_continuar)
            driver.execute_script("arguments[0].click();", boton_continuar)
            time.sleep(2)
            print("              ✓ Click en 'Continuar'")
            return True
            
        except TimeoutException:
            print("              ✗ Botón 'Continuar' no se habilitó")
            return False
        except Exception as e:
            print(f"              ✗ Error al hacer clic en 'Continuar': {str(e)[:100]}")
            # Intentar con JavaScript como fallback
            try:
                botones = driver.find_elements(By.XPATH, "//button//span[text()='Continuar']/..")
                for boton in botones:
                    if 'disabled' not in boton.get_attribute('class'):
                        driver.execute_script("arguments[0].click();", boton)
                        time.sleep(4)
                        print("              ✓ Click en 'Continuar' (JavaScript)")
                        return True
            except:
                pass
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
        time.sleep(3)  # Esperar a que cargue la página completamente
        
        # 1. EXTRAER PRECIOS GENERALES (sin beneficio)
        # Buscar dentro de la sección de entradas generales
        try:
            seccion_general = driver.find_element(By.CSS_SELECTOR, ".purchase-tickets--common-tickets")
            categorias_generales = seccion_general.find_elements(By.CSS_SELECTOR, ".purchase-tickets--common-tickets-categories")
            
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
                        
                except Exception as e:
                    # Categoria sin precio o elemento faltante
                    continue
                    
        except Exception as e:
            print(f"              → No se encontró sección de entradas generales: {e}")
        
        # 2. EXTRAER PRECIOS CON BENEFICIO (si tiene sesión)
        if tiene_sesion:
            try:
                # Verificar si existe la sección de beneficios
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
                                # Extraer el título (tipo de entrada)
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
                                    
                            except Exception as e:
                                continue
                else:
                    print(f"              → No se encontró sección de beneficios")
                    
            except Exception as e:
                print(f"              → Error extrayendo beneficios: {e}")
        
        print(f"              → Total precios extraídos: {len(precios)} ({len([p for p in precios if p['beneficio'] == 'No'])} generales, {len([p for p in precios if p['beneficio'] == 'Si'])} con beneficio)")
        
        return precios
        
    except Exception as e:
        print(f"              ✗ Error en extracción de precios: {e}")
        return []

def extraer_modalidades_y_horarios_de_pelicula(elemento_pelicula):
    """
    Extrae las modalidades (2D REGULAR, 2D PRIME, 3D, etc) y sus horarios
    Usa el HTML real: button.showtime-selector--link para horarios
    Retorna: [{'modalidad': '2D REGULAR SUBTITULADA', 'horario_boton': <WebElement>}, ...]
    """
    modalidades_horarios = []
    try:
        # Buscar botones de horario: button.showtime-selector--link
        botones_horario = elemento_pelicula.find_elements(By.CSS_SELECTOR, "button.showtime-selector--link")
        
        if not botones_horario:
            return []  # No hay horarios disponibles
        
        # Tomar solo el PRIMER horario (cualquier horario sirve, solo queremos precios)
        primer_boton = botones_horario[0]
        texto_horario = primer_boton.text.strip()
        
        # Extraer modalidad del contexto
        try:
            # Buscar formato en sessions-details--formats
            formato_div = elemento_pelicula.find_element(By.CSS_SELECTOR, "div.sessions-details--formats")
            formato_text = formato_div.text.upper()
            
            # Determinar modalidad
            modalidad = 'STANDARD'
            if '3D' in formato_text:
                modalidad = '3D'
            elif '2D' in formato_text and 'PRIME' in formato_text:
                modalidad = '2D PRIME'
            elif '2D' in formato_text:
                modalidad = '2D REGULAR'
            elif 'IMAX' in formato_text:
                modalidad = 'IMAX'
            
        except:
            modalidad = 'STANDARD'
        
        modalidades_horarios.append({
            'modalidad': modalidad,
            'horario_boton': primer_boton,
            'horario_texto': texto_horario
        })
        
        return modalidades_horarios
    except:
        return []

def extraer_peliculas_y_precios_de_cine(driver, cine_nombre, tiene_sesion):
    """
    FLUJO CORRECTO:
    1. Ya estamos en la página del cine (llegamos por click)
    2. Por cada película, detectar modalidades (2D REGULAR, 2D PRIME, 3D, etc)
    3. Click en PRIMER horario de cada modalidad
    4. Extraer precios de página /asientos
    5. Volver y repetir
    """
    print(f"  Procesando cine: {cine_nombre}")
    datos_extraidos = []
    
    try:
        url_cine = driver.current_url  # Usar la URL actual en lugar de construirla
        print(f"     URL: {url_cine}")
        time.sleep(3)  # Delay aleatorio
        
        # Scroll para cargar películas con delays
        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, 0);")

        
        # Buscar películas usando el selector CORRECTO del HTML
        # Cada película está en: div.movies-list-schedules--large-item
        selector_correcto = "div.movies-list-schedules--large-item"
        
        peliculas_encontradas = driver.find_elements(By.CSS_SELECTOR, selector_correcto)
        print(f"     ✓ Selector: {selector_correcto}")
        print(f"     ✓ Encontradas {len(peliculas_encontradas)} películas")
        
        if len(peliculas_encontradas) == 0:
            print(f"     ⚠️  No hay películas disponibles en este cine")
            return datos_extraidos
        
        total_peliculas = len(peliculas_encontradas)
        peliculas_procesadas = set()
        peliculas_validas_procesadas = 0
        MAX_PELICULAS = None  # None = TODAS las películas del cine
        
        # USAR ÍNDICES en lugar de iterar elementos directamente
        # Esto permite re-encontrar elementos después de volver al cine
        idx_pelicula = 0
        while idx_pelicula < total_peliculas and (MAX_PELICULAS is None or peliculas_validas_procesadas < MAX_PELICULAS):
            try:
                # Re-encontrar películas cada vez (evita StaleElementReferenceException)
                peliculas_actuales = driver.find_elements(By.CSS_SELECTOR, selector_correcto)
                if idx_pelicula >= len(peliculas_actuales):
                    break
                
                elemento = peliculas_actuales[idx_pelicula]
                idx_pelicula += 1  # Avanzar índice
                
                # Extraer nombre de película usando el selector CORRECTO
                # Título está en: h2.movies-list-schedules--small-movie-description-title
                nombre_pelicula = None
                try:
                    # El título está en un h2 simple dentro del large-item
                    titulo_elem = elemento.find_element(By.CSS_SELECTOR, "h2")
                    nombre_pelicula = titulo_elem.text.strip()
                except:
                    # Fallback: intentar obtener de atributos de imagen
                    try:
                        img = elemento.find_element(By.CSS_SELECTOR, "img")
                        nombre_pelicula = img.get_attribute('alt')
                    except:
                        pass
                
                if not nombre_pelicula or len(nombre_pelicula) < 3:
                    continue
                
                # Evitar duplicados
                if nombre_pelicula in peliculas_procesadas:
                    continue
                peliculas_procesadas.add(nombre_pelicula)
                
                print(f"     [{idx_pelicula}] - {nombre_pelicula}")
                
                # Extraer modalidades y horarios
                modalidades = extraer_modalidades_y_horarios_de_pelicula(elemento)
                
                if not modalidades:
                    print(f"         No se encontraron horarios disponibles")
                    datos_extraidos.append({
                        'cine': cine_nombre,
                        'pelicula': nombre_pelicula,
                        'precio': 'Sin funciones',
                        'tipo': 'N/A',
                        'beneficio': 'No',
                        'modalidad': 'N/A'
                    })
                    # No contar películas sin horarios
                    continue
                
                # Contar esta película como válida (tiene horarios)
                peliculas_validas_procesadas += 1
                
                print(f"         {len(modalidades)} modalidad(es) encontrada(s)")
                
                # Procesar SOLO la primera modalidad (evita múltiples compras que causan errores)
                if modalidades:
                    mod = modalidades[0]
                    try:
                        print(f"            {mod['modalidad']} - Horario: {mod['horario_texto']}")
                        
                        # Scroll y click DIRECTO
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", mod['horario_boton'])
                        driver.execute_script("arguments[0].click();", mod['horario_boton'])
                        print(f"              → Click en horario {mod['horario_texto']}")
                        time.sleep(1.5)

                        
                        # Verificar que estamos en la página de asientos (debe contener /asientos al final)
                        if '/asientos' in driver.current_url:
                            print(f"              ✓ En página de asientos")
                            
                            # Seleccionar asiento y hacer clic en Continuar
                            exito = seleccionar_asiento_y_continuar(driver)
                            if exito:
                                # Verificar página de precios
                                if '/asientos' not in driver.current_url and '/compra/' in driver.current_url:
                                    print("              ✓ En página de precios")

                                    
                                    # Extraer precios
                                    precios = extraer_precios_de_pagina(driver, tiene_sesion)
                                else:
                                    print(f"              No llegó a página de compra (URL: {driver.current_url})")
                                    precios = []
                                
                                if precios:
                                    for precio_info in precios:
                                        datos_extraidos.append({
                                            'cine': cine_nombre,
                                            'pelicula': nombre_pelicula,
                                            'precio': precio_info['precio'],
                                            'tipo': precio_info['tipo'],
                                            'beneficio': precio_info['beneficio'],
                                            'modalidad': mod['modalidad']
                                        })
                                    print(f"              ✓ {len(precios)} precio(s) extraído(s)")
                                else:
                                    print(f"              No se encontraron precios")
                                    datos_extraidos.append({
                                        'cine': cine_nombre,
                                        'pelicula': nombre_pelicula,
                                        'precio': 'N/A',
                                        'tipo': 'N/A',
                                        'beneficio': 'No',
                                        'modalidad': mod['modalidad']
                                    })
                            else:
                                print("              ✗ No se pudo seleccionar asiento")
                            
                                            # LIMPIEZA RÁPIDA
                            cancelar_compra(driver)
                            limpiar_cache_y_datos_navegador(driver)
                            driver.get(url_cine)
                            time.sleep(3)  # Delay aleatorio
                            
                            # 4. RE-LOGIN porque borramos las cookies
                            if tiene_sesion:
                                print("              → Re-login después de limpiar caché...")
                                if hacer_login(driver):
                                    print("              ✓ Re-login exitoso")
                                    # Volver al cine después del login
                                    driver.get(url_cine)
                                    time.sleep(3)  # Delay aleatorio
                                else:
                                    print("              Re-login falló, continuando sin sesión")
                            
                            # 5. Re-localizar películas (el DOM cambió)
                            try:
                                manejar_popups_iniciales(driver)
                                driver.execute_script("window.scrollTo(0, 0);")
                            except:
                                pass

                        else:
                            print(f"              No se llegó a página de asientos (URL: {driver.current_url})")
                        
                    except Exception as e:
                        print(f"              Error procesando modalidad: {e}")
                        # No hacer continue - ya procesamos esta película, seguir con la siguiente
                
            except StaleElementReferenceException:
                print(f"         Elemento obsoleto, continuando...")
                continue
            except Exception as e:
                print(f"         Error: {e}")
                continue
        
        # Mostrar mensaje si se alcanzó el límite
        if MAX_PELICULAS and peliculas_validas_procesadas >= MAX_PELICULAS:
            print(f"     ✓ Límite de {MAX_PELICULAS} películas alcanzado")
        elif peliculas_validas_procesadas > 0:
            print(f"     ✓ Procesadas {peliculas_validas_procesadas} películas")
        
        print(f"  ✅ Total extraído: {len(datos_extraidos)} registros\n")
        return datos_extraidos
        
    except Exception as e:
        print(f"  Error en cine {cine_nombre}: {e}\n")
        import traceback
        traceback.print_exc()
        return datos_extraidos

def main():
    print("=" * 80)
    print("CINEPLANET PERU - EXTRACTOR DE PRECIOS V3.1 (GUARDADO INCREMENTAL)")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL Base: {BASE_URL}")
    print(f"Modo: {'Headless (sin ventana)' if HEADLESS else 'Navegador Visible'}")
    print(f"Limite de cines: {MAX_CINES if MAX_CINES else 'Todos'}")
    print(f"Login: {'Activado' if EMAIL else 'Desactivado'}")
    print()
    print("CARACTERÍSTICAS:")
    print("  Guardado incremental: UN SOLO ARCHIVO que se actualiza cada cine")
    print("  Archivo: precios_cineplanet_EN_PROGRESO.csv")
    print("  Si se interrumpe: Los datos están en ese archivo")
    print("  Al terminar: Se renombra con timestamp final")
    print("=" * 80)
    print()
    
    # Definir nombre del archivo de progreso (ÚNICO, no cambia)
    archivo_progreso = "precios_cineplanet_EN_PROGRESO.csv"
    
    driver = None
    todos_los_datos = []
    try:
        driver = configurar_driver()
        
        # Ir a página principal primero para manejar popups
        driver.get(BASE_URL)
        time.sleep(3)  # Delay aleatorio inicial
        manejar_popups_iniciales(driver)

        
        tiene_sesion = hacer_login(driver)
        
        # 🚀 NUEVA MEJORA: Cargar lista desde archivo TXT (igual que inspector_asientos_totales_v2.py)
        nombres_cines = cargar_lista_cines_desde_txt()
        if not nombres_cines:
            print("❌ No se cargó la lista de cines. Abortando.\n")
            return
        
        # Aplicar límite si está configurado
        if MAX_CINES and len(nombres_cines) > MAX_CINES:
            nombres_cines = nombres_cines[:MAX_CINES]
            print(f"⚙️  Limitado a primeros {MAX_CINES} cines (MAX_CINES configurado)\n")
        
        print("=" * 80)
        print(f"INICIANDO EXTRACCION - {len(nombres_cines)} CINES")
        print("=" * 80)
        print()
        
        # Iterar directamente por nombres, navegando a URL específica de cada cine
        for idx, cine_nombre in enumerate(nombres_cines):
            print(f"\n[{idx+1}/{len(nombres_cines)}] CINE: {cine_nombre}")
            print("-" * 80)
            
            try:
                # 🚀 NAVEGACION DIRECTA: Ir directo a la URL del cine
                if not ir_a_cine_directo(driver, cine_nombre):
                    print(f"  ⚠️  No se pudo navegar a {cine_nombre}, saltando...")
                    continue
                
                # Manejar popups si aparecen
                manejar_popups_iniciales(driver)
                time.sleep(3)  # Delay aleatorio
                
                # Extraer datos del cine (usará driver.current_url)
                datos_cine = extraer_peliculas_y_precios_de_cine(driver, cine_nombre, tiene_sesion)
                todos_los_datos.extend(datos_cine)
                
                # 💾 GUARDADO INCREMENTAL: Actualizar el MISMO archivo después de cada cine
                # Esto evita perder datos si la PC se suspende o el script se interrumpe
                if todos_los_datos:
                    try:
                        df_progreso = pd.DataFrame(todos_los_datos)
                        df_progreso.columns = ['Cine', 'Pelicula', 'Precio', 'Tipo', 'Beneficio', 'Modalidad']
                        
                        # SOBREESCRIBIR el mismo archivo (no crear uno nuevo cada vez)
                        df_progreso.to_csv(archivo_progreso, index=False, encoding='utf-8-sig')
                        
                        print(f"  💾 Progreso actualizado: {archivo_progreso}")
                        print(f"     → Registros totales: {len(df_progreso)}")
                        print(f"     → Cines procesados: {df_progreso['Cine'].nunique()}/{len(nombres_cines)}")
                        print(f"     → Películas únicas: {df_progreso['Pelicula'].nunique()}")
                        
                        # 🎯 DELAY MUY IMPORTANTE: Entre cines (comportamiento humano)
                        if idx < len(nombres_cines) - 1:  # No delay después del último cine
                            print(f"\n  💤 Pausa entre cines (anti-detección)...")
                            time.sleep(3)  # Delay aleatorio LARGO entre cines (30-60 segundos)
                        print()

                    except Exception as e_save:
                        print(f"  ⚠️ Error guardando progreso: {e_save}")
                
            except Exception as e:
                print(f"  ✗ Error al procesar {cine_nombre}: {e}")
                import traceback
                traceback.print_exc()
        print("=" * 80)
        print("EXTRACCIÓN COMPLETADA - GUARDANDO ARCHIVO FINAL")
        print("=" * 80)
        if todos_los_datos:
            df = pd.DataFrame(todos_los_datos)
            df.columns = ['Cine', 'Pelicula', 'Precio', 'Tipo', 'Beneficio', 'Modalidad']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_final = f"precios_cineplanet_COMPLETO_{timestamp}.csv"
            df.to_csv(filename_final, index=False, encoding='utf-8-sig')
            
            print(f"✅ Archivo final: {filename_final}")
            print(f"Registros: {len(df)}")
            print()
            print("ESTADISTICAS:")
            print(f"   Cines: {df['Cine'].nunique()}")
            print(f"   Peliculas: {df['Pelicula'].nunique()}")
            print(f"   Con precio: {len(df[df['Precio'] != 'N/A'])}")
            print()
            print("MUESTRA (primeros 10):")
            print(df.head(10).to_string(index=False))
            print()
            
            # Eliminar el archivo de progreso ya que tenemos el final
            try:
                import os
                if os.path.exists(archivo_progreso):
                    os.remove(archivo_progreso)
                    print(f"🗑️  Archivo temporal eliminado: {archivo_progreso}")
            except:
                pass
        else:
            print("No se obtuvieron datos\n")
    except KeyboardInterrupt:
        print("\n\n⚠️ INTERRUMPIDO POR USUARIO")
        print("=" * 80)
        if todos_los_datos:
            print(f"✅ Los datos ya están guardados en: {archivo_progreso}")
            print(f"   Total de registros: {len(todos_los_datos)}")
            print()
            print("💡 Puedes usar ese archivo directamente, o renombrarlo:")
            print(f"   Ejemplo: precios_cineplanet_INTERRUMPIDO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        else:
            print("No se obtuvieron datos antes de la interrupción\n")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("\nCerrando navegador...")
            driver.quit()
            print("Cerrado")
    print("\n" + "=" * 80)
    print("FINALIZADO")
    print("=" * 80)

if __name__ == "__main__":
    main()
