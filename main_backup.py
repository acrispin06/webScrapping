from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import pandas as pd
import time
import re
from datetime import datetime

BASE_URL = 'https://www.cineplanet.com.pe'
HEADLESS = False  # True = modo sin ventana (menos recursos, evita suspensión de PC)
TIMEOUT = 20
MAX_CINES = 1  # PRUEBA: 1 cine para probar conteo de asientos

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
                    print("  ✓ Cookies aceptadas")
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
                        print("  ✓ Cookies aceptadas")
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
        
        print("  ✓ Popups manejados\n")
        
    except Exception as e:
        print(f"Advertencia manejando popups: {e}\n")

def normalizar_nombre_cine_para_url(nombre_cine):
    return nombre_cine.lower().replace(' ', '-')

def hacer_login(driver, es_relogin=False):
    if not EMAIL or not PASSWORD:
        print("Sin credenciales - Solo precios sin beneficio\n")
        return False
    try:
        print("Intentando hacer login...")
        
        # Si es re-login, dar más tiempo y limpiar el estado
        if es_relogin:
            # Para re-login, primero ir a home page para resetear estado
            print("  → Limpiando estado del navegador...")
            driver.get(BASE_URL)
            time.sleep(3)
        
        driver.get(f"{BASE_URL}/autenticacion/login")
        time.sleep(7 if es_relogin else 5)  # Más tiempo para re-login
        
        # Manejar popups que puedan aparecer
        try:
            manejar_popups_iniciales(driver)
        except:
            pass
        
        time.sleep(2)
        
        # Usar los selectores correctos del HTML de Cineplanet
        # Campo EMAIL: name="cineplanet-code"
        print("  → Buscando campo de DNI/Código...")
        timeout_login = 20 if es_relogin else TIMEOUT  # Más tiempo para re-login
        email_input = WebDriverWait(driver, timeout_login).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='cineplanet-code']"))
        )
        print("  → Campo encontrado, ingresando DNI...")
        email_input.clear()
        time.sleep(0.5)
        email_input.send_keys(EMAIL)
        time.sleep(1)
        
        # Campo PASSWORD: name="password"
        print("  → Buscando campo de contraseña...")
        password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        print("  → Campo encontrado, ingresando contraseña...")
        password_input.clear()
        password_input.send_keys(PASSWORD)
        time.sleep(1)
        
        # Botón de login (submit)
        print("  → Buscando botón de login...")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        print("  → Haciendo clic en login...")
        login_button.click()
        
        time.sleep(7)  # Aumentar tiempo de espera después del click
        
        # Verificar si el login fue exitoso
        print(f"  → URL actual: {driver.current_url}")
        if "login" not in driver.current_url.lower() and "autenticacion" not in driver.current_url.lower():
            print("✓ Login exitoso\n")
            return True
        else:
            print("✗ Login falló - aún en página de login\n")
            # Intentar capturar mensaje de error
            try:
                errores = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error']")
                if errores:
                    print(f"  Mensajes de error: {[e.text for e in errores if e.text.strip()]}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"✗ Error en login: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def cargar_cines_hasta_indice(driver, indice_objetivo):
    """
    Carga cines hasta alcanzar el índice objetivo (los cines cargan de 6 en 6)
    Args:
        indice_objetivo: índice del cine que queremos cargar (0-indexed)
    Returns:
        clicks_realizados: número de clicks realizados en 'Ver más cines'
    """
    CINES_POR_GRUPO = 6
    # Calcular cuántos clicks necesitamos (cada click carga 6 cines más)
    # Índice 0-5: 0 clicks, Índice 6-11: 1 click, Índice 12-17: 2 clicks, etc.
    clicks_necesarios = indice_objetivo // CINES_POR_GRUPO
    
    if clicks_necesarios == 0:
        # No necesitamos hacer clicks, los primeros 6 ya están cargados
        return 0
    
    print(f"  → Cargando cines hasta índice {indice_objetivo} (necesita {clicks_necesarios} clicks)...")
    clicks_realizados = 0
    
    while clicks_realizados < clicks_necesarios:
        try:
            # Buscar el botón "Ver más cines"
            boton_ver_mas = driver.find_element(By.XPATH, "//span[contains(text(), 'Ver más cines')]/parent::button")
            
            if boton_ver_mas.is_displayed():
                # Scroll al botón
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_ver_mas)
                time.sleep(1)
                
                # Hacer clic
                boton_ver_mas.click()
                clicks_realizados += 1
                print(f"     ✓ Click #{clicks_realizados} en 'Ver más cines'")
                time.sleep(2)  # Esperar a que carguen más cines
            else:
                print(f"     Botón 'Ver más cines' no visible")
                break
        except NoSuchElementException:
            print(f"     ✓ No hay más botón 'Ver más cines'")
            break
        except Exception as e:
            print(f"     Error cargando más cines: {e}")
            break
    
    # Scroll final para asegurar que todo está visible
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    return clicks_realizados

def obtener_lista_nombres_cines(driver):
    """
    Obtiene solo los NOMBRES de los cines desde /cinemas
    No guarda elementos WebElement (que se vuelven stale)
    Retorna lista de nombres de cines
    """
    print("Obteniendo lista de cines desde /cinemas...")
    try:
        driver.get(f"{BASE_URL}/cinemas")
        time.sleep(5)
        
        # Manejar popups de cookies y notificaciones
        manejar_popups_iniciales(driver)
        time.sleep(2)
        
        # Cargar TODOS los cines para saber cuántos hay en total
        print("  → Cargando todos los cines para obtener lista completa...")
        max_clicks = 10
        clicks = 0
        while clicks < max_clicks:
            try:
                boton = driver.find_element(By.XPATH, "//span[contains(text(), 'Ver más cines')]/parent::button")
                if boton.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton)
                    time.sleep(1)
                    boton.click()
                    clicks += 1
                    print(f"     ✓ Click #{clicks} en 'Ver más cines'")
                    time.sleep(2)
                else:
                    break
            except NoSuchElementException:
                break
            except:
                break
        
        # Buscar SOLO los nombres de cines
        print("  → Extrayendo nombres de cines...")
        nombres_cines = []
        
        try:
            elementos_cine = driver.find_elements(By.CSS_SELECTOR, "li.cinemas--list--item div.cinema")
            print(f"  → Encontrados {len(elementos_cine)} elementos de cine")
            
            for elemento in elementos_cine:
                try:
                    titulo = elemento.find_element(By.CSS_SELECTOR, "h2.cinema--title")
                    nombre_cine = titulo.text.strip().upper()
                    
                    if nombre_cine and len(nombre_cine) >= 3:
                        nombres_cines.append(nombre_cine)
                except:
                    continue
                    
        except Exception as e:
            print(f"  ✗ Error extrayendo nombres: {e}")
            return []
        
        # Limitar cantidad si es necesario
        if MAX_CINES and len(nombres_cines) > MAX_CINES:
            nombres_cines = nombres_cines[:MAX_CINES]
        
        print(f"\n✓ Encontrados {len(nombres_cines)} cines:")
        for i, nombre in enumerate(nombres_cines, 1):
            print(f"   {i}. {nombre}")
        print()
        
        return nombres_cines
        
    except Exception as e:
        print(f"✗ Error obteniendo lista de cines: {e}\n")
        import traceback
        traceback.print_exc()
        return []

def obtener_elemento_cine_por_indice(driver, indice):
    """
    Obtiene el elemento clickeable de un cine específico por su índice (0-indexed)
    Esta función se llama cada vez que necesitamos hacer clic en un cine
    Args:
        indice: posición del cine en la lista (0-indexed)
    Returns:
        WebElement clickeable o None si no se encuentra
    """
    try:
        # Obtener todos los elementos de cine visibles actualmente
        elementos_cine = driver.find_elements(By.CSS_SELECTOR, "li.cinemas--list--item div.cinema")
        
        if indice >= len(elementos_cine):
            print(f"  ✗ Índice {indice} fuera de rango (hay {len(elementos_cine)} cines cargados)")
            return None
        
        # Obtener el elemento en la posición indicada
        elemento = elementos_cine[indice]
        
        # Obtener el elemento clickeable
        try:
            clickeable = elemento.find_element(By.CSS_SELECTOR, "div.cinema--image-wrapper")
        except:
            clickeable = elemento
        
        return clickeable
        
    except Exception as e:
        print(f"  ✗ Error obteniendo elemento de cine #{indice}: {e}")
        return None

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
    Retorna: (éxito: bool, asientos_totales: int)
    """
    try:
        print("              → Seleccionando asiento...")
        time.sleep(3)
        
        # CONTAR ASIENTOS TOTALES EN LA SALA (cualquier estado)
        asientos_totales = 0
        try:
            todos_asientos = driver.find_elements(By.CSS_SELECTOR, ".seat-map--seat")
            asientos_totales = len(todos_asientos)
            print(f"              ℹ️ Asientos totales en sala: {asientos_totales}")
        except Exception as e:
            print(f"              ⚠️ No se pudo contar asientos: {e}")
            asientos_totales = 0
        
        # Cerrar cualquier popup que pueda estar bloqueando
        try:
            manejar_popups_iniciales(driver)
        except:
            pass
        
        # Buscar un asiento disponible
        asiento_selector = ".seat-map--seat.seat-map--seat_available"
        
        try:
            asiento = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, asiento_selector))
            )
            
            # Scroll al asiento
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", asiento)
            time.sleep(2)
            
            # Intentar clic normal primero
            try:
                asiento.click()
                print("              ✓ Asiento seleccionado (click normal)")
            except:
                # Si falla, usar JavaScript
                driver.execute_script("arguments[0].click();", asiento)
                print("              ✓ Asiento seleccionado (JavaScript)")
            
            time.sleep(3)  # Esperar más tiempo para que se actualice el botón
            
        except TimeoutException:
            print("              ✗ No se encontraron asientos disponibles")
            return (False, asientos_totales)
        
        # Verificar si hay algún mensaje de error o alerta
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"              Alerta detectada: {alert_text}")
            alert.accept()
            return (False, asientos_totales)
        except:
            pass  # No hay alerta
        
        # Buscar y hacer clic en el botón "Continuar"
        try:
            # Esperar a que el botón esté habilitado (no tenga clase disabled)
            print("              → Esperando botón 'Continuar'...")
            
            # Intentar múltiples selectores
            boton_continuar = None
            for intento in range(3):
                try:
                    # Buscar botón que no esté disabled
                    botones = driver.find_elements(By.XPATH, "//button[contains(@class, 'call-to-action')]//span[contains(text(),'Continuar')]/..")
                    for btn in botones:
                        if 'disabled' not in btn.get_attribute('class'):
                            boton_continuar = btn
                            break
                    
                    if boton_continuar:
                        break
                    
                    time.sleep(2)
                except:
                    time.sleep(2)
            
            if not boton_continuar:
                print("              ✗ Botón 'Continuar' no encontrado o deshabilitado")
                return (False, asientos_totales)
            
            # Scroll al botón
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_continuar)
            time.sleep(1)
            
            # Hacer clic con JavaScript directamente (más confiable)
            print("              → Haciendo clic en 'Continuar'...")
            driver.execute_script("arguments[0].click();", boton_continuar)
            time.sleep(5)
            print("              ✓ Click en 'Continuar'")
            
            # Verificar si hubo algún error después del click
            try:
                # Buscar mensajes de error en la página
                error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error'], [class*='alert']")
                for elem in error_elements:
                    if elem.is_displayed() and elem.text.strip():
                        print(f"              Error en página: {elem.text.strip()[:100]}")
                        return (False, asientos_totales)
            except:
                pass
            
            return (True, asientos_totales)
            
        except TimeoutException:
            print("              ✗ Botón 'Continuar' no se habilitó")
            return (False, asientos_totales)
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
                        return (True, asientos_totales)
            except:
                pass
            return (False, asientos_totales)
            
    except Exception as e:
        print(f"              ✗ Error seleccionando asiento: {str(e)[:100]}")
        return (False, 0)

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
        time.sleep(3)
        
        # Scroll para cargar películas
        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Buscar películas usando el selector CORRECTO del HTML
        # Cada película está en: div.movies-list-schedules--large-item
        selector_correcto = "div.movies-list-schedules--large-item"
        
        peliculas_encontradas = driver.find_elements(By.CSS_SELECTOR, selector_correcto)
        print(f"     ✓ Selector: {selector_correcto}")
        print(f"     ✓ Encontradas {len(peliculas_encontradas)} películas")
        
        total_peliculas = len(peliculas_encontradas)
        peliculas_procesadas = set()
        peliculas_validas_procesadas = 0
        MAX_PELICULAS = 1  # PRUEBA: 1 película para probar conteo de asientos
        
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
                        
                        # Scroll al botón y hacer click
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", mod['horario_boton'])
                        time.sleep(0.5)
                        
                        # Click en el horario con JavaScript (más confiable)
                        try:
                            driver.execute_script("arguments[0].click();", mod['horario_boton'])
                            print(f"              → Click en horario {mod['horario_texto']}")
                        except Exception as e:
                            print(f"              ✗ Error en click: {str(e)[:50]}")
                            continue
                        
                        time.sleep(6)  # Esperar que cargue página de asientos (puede tardar)
                        
                        # Verificar que estamos en la página de asientos (debe contener /asientos al final)
                        if '/asientos' in driver.current_url:
                            print(f"              ✓ En página de asientos")
                            
                            # Seleccionar asiento y hacer clic en Continuar (retorna tupla)
                            exito, asientos_totales = seleccionar_asiento_y_continuar(driver)
                            if exito:
                                time.sleep(3)
                                
                                # Verificar que llegamos a página de precios (ya NO debe tener /asientos)
                                if '/asientos' not in driver.current_url and '/compra/' in driver.current_url:
                                    print("              ✓ En página de precios")
                                    time.sleep(2)
                                    
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
                                            'modalidad': mod['modalidad'],
                                            'asientos_totales': asientos_totales
                                        })
                                    print(f"              {len(precios)} precio(s) extraído(s) | 🪑 {asientos_totales} asientos")
                                else:
                                    print(f"              No se encontraron precios")
                                    datos_extraidos.append({
                                        'cine': cine_nombre,
                                        'pelicula': nombre_pelicula,
                                        'precio': 'N/A',
                                        'tipo': 'N/A',
                                        'beneficio': 'No',
                                        'modalidad': mod['modalidad'],
                                        'asientos_totales': asientos_totales
                                    })
                            else:
                                print("              ✗ No se pudo seleccionar asiento")
                            
                            # LIMPIEZA PROFUNDA para permitir múltiples compras
                            # 1. Cancelar la compra actual
                            cancelar_compra(driver)
                            time.sleep(2)
                            
                            # 2. LIMPIAR TODO: caché, cookies, localStorage, sessionStorage
                            #    Esto es CRÍTICO para evitar "Error en el servicio"
                            limpiar_cache_y_datos_navegador(driver)
                            
                            # 3. Volver al cine (perdimos las cookies, así que navegamos normal)
                            driver.get(url_cine)
                            time.sleep(4)
                            
                            # 4. RE-LOGIN porque borramos las cookies
                            if tiene_sesion:
                                print("              → Re-login después de limpiar caché...")
                                if hacer_login(driver):
                                    print("              ✓ Re-login exitoso")
                                    # Volver al cine después del login
                                    driver.get(url_cine)
                                    time.sleep(3)
                                else:
                                    print("              Re-login falló, continuando sin sesión")
                            
                            # 5. Re-localizar películas (el DOM cambió)
                            try:
                                manejar_popups_iniciales(driver)
                                driver.execute_script("window.scrollTo(0, 0);")
                                time.sleep(1)
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
        
        print(f"  Total extraído: {len(datos_extraidos)} registros\n")
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
        time.sleep(2)
        manejar_popups_iniciales(driver)
        
        tiene_sesion = hacer_login(driver)
        
        # Obtener lista de NOMBRES de cines (no elementos WebElement)
        nombres_cines = obtener_lista_nombres_cines(driver)
        if not nombres_cines:
            print("No se encontraron cines. Abortando.\n")
            return
        
        print("INICIANDO EXTRACCION")
        print("=" * 80)
        print()
        
        # Iterar usando índices para evitar stale element references
        for idx, cine_nombre in enumerate(nombres_cines):
            print(f"[{idx+1}/{len(nombres_cines)}] CINE: {cine_nombre}")
            print("-" * 80)
            
            try:               
                # Navegar a /cinemas para tener página fresca
                print(f"  → Navegando a /cinemas...")
                driver.get(f"{BASE_URL}/cinemas")
                time.sleep(3)
                
                # Manejar popups si aparecen
                manejar_popups_iniciales(driver)
                time.sleep(1)
                
                # Cargar cines solo hasta el índice actual (optimizado)
                print(f"  → Cargando cines hasta índice {idx}...")
                clicks = cargar_cines_hasta_indice(driver, idx)
                print(f"     ✓ {clicks} clicks en 'Ver más cines'")
                time.sleep(2)
                
                # Obtener elemento FRESCO del cine
                elemento_cine = obtener_elemento_cine_por_indice(driver, idx)
                if not elemento_cine:
                    print(f"  ✗ No se pudo obtener elemento del cine #{idx}")
                    continue
                
                # Hacer clic en el elemento del cine
                print(f"  → Haciendo clic en {cine_nombre}...")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_cine)
                time.sleep(1)
                elemento_cine.click()
                time.sleep(5)  # Esperar a que cargue la página del cine
                
                # Extraer datos del cine (usará driver.current_url)
                datos_cine = extraer_peliculas_y_precios_de_cine(driver, cine_nombre, tiene_sesion)
                todos_los_datos.extend(datos_cine)
                
                # � GUARDADO INCREMENTAL: Actualizar el MISMO archivo después de cada cine
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
            df.columns = ['Cine', 'Pelicula', 'Precio', 'Tipo', 'Beneficio', 'Modalidad', 'AsientosTotales']
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
