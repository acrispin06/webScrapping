from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import traceback
from datetime import datetime
import unicodedata
import re

BASE_URL = 'https://www.cinemark-peru.com'
HEADLESS = False  # True = modo sin ventana
TIMEOUT = 20
MAX_CINES = None  # None = todos los cines, o número específico para pruebas
MAX_PELICULAS = None  # None = todas las películas

# Credenciales de login
EMAIL = "alvarocrispin0604@gmail.com"
PASSWORD = "Lizmoisesrodrigo0604"

def configurar_driver(headless=HEADLESS):
    """Configura y retorna un driver de Chrome con opciones anti-detección"""
    print("Configurando Chrome WebDriver...")
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Suprimir errores de consola
    options.add_argument('--log-level=3')
    options.add_argument('--disable-logging')
    options.add_argument('--disable-gpu')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Deshabilitar notificaciones
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("✓ WebDriver configurado\n")
    return driver

def normalizar_nombre_pelicula(nombre):
    """
    Normaliza nombre de película a slug para URL
    'El Resplandor [1980]' → 'el-resplandor-1980'
    """
    # Convertir a minúsculas
    slug = nombre.lower()
    
    # Remover acentos
    slug = ''.join(
        c for c in unicodedata.normalize('NFD', slug)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Remover caracteres especiales, reemplazar espacios por guiones
    slug = re.sub(r'[^\w\s-]', '', slug)  # Mantener solo letras, números, espacios y guiones
    slug = slug.replace(' ', '-')
    
    # Remover múltiples guiones consecutivos
    while '--' in slug:
        slug = slug.replace('--', '-')
    
    # Remover guiones al inicio/final
    slug = slug.strip('-')
    
    return slug

def cargar_peliculas_desde_lista(driver):
    """
    Carga la página de elegir-pelicula y extrae todas las películas con sus nombres normalizados
    Retorna: [{'nombre': 'Venom 3', 'slug': 'venom-3'}, ...]
    """
    try:
        print("Cargando lista de películas desde Cinemark...")
        url_peliculas = f"{BASE_URL}/elegir-pelicula"
        driver.get(url_peliculas)
        time.sleep(5)
        
        # Scroll para cargar todas las películas
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Buscar todas las tarjetas de películas
        peliculas = []
        
        # Selector para las tarjetas de películas (ajustar según el HTML real)
        selectores_peliculas = [
            "div[class*='movie-card']",
            "div[class*='MovieCard']",
            "a[href*='/pelicula/']",
        ]
        
        elementos_pelicula = []
        for selector in selectores_peliculas:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                if elementos:
                    elementos_pelicula = elementos
                    print(f"✓ Encontradas {len(elementos)} películas con selector: {selector}")
                    break
            except:
                continue
        
        if not elementos_pelicula:
            print("✗ No se encontraron películas")
            return []
        
        # Extraer nombre y slug de cada película
        for elem in elementos_pelicula:
            try:
                # Intentar extraer el nombre del título
                nombre = None
                slug = None
                
                # Intento 1: Desde el href del link
                try:
                    href = elem.get_attribute('href')
                    if href and '/pelicula/' in href:
                        slug = href.split('/pelicula/')[-1].strip('/')
                        # Reconstruir nombre desde slug
                        nombre = slug.replace('-', ' ').title()
                except:
                    pass
                
                # Intento 2: Desde un elemento de texto dentro
                if not nombre:
                    try:
                        nombre_elem = elem.find_element(By.CSS_SELECTOR, "h2, h3, h4, p[class*='title'], span[class*='title']")
                        nombre = nombre_elem.text.strip()
                        slug = normalizar_nombre_pelicula(nombre)
                    except:
                        pass
                
                if nombre and slug:
                    peliculas.append({
                        'nombre': nombre,
                        'slug': slug
                    })
            except:
                continue
        
        # Eliminar duplicados
        peliculas_unicas = []
        slugs_vistos = set()
        for p in peliculas:
            if p['slug'] not in slugs_vistos:
                peliculas_unicas.append(p)
                slugs_vistos.add(p['slug'])
        
        print(f"✓ Cargadas {len(peliculas_unicas)} películas únicas\n")
        
        # Mostrar las primeras 5 películas
        print("Primeras películas detectadas:")
        for i, p in enumerate(peliculas_unicas[:5], 1):
            print(f"   {i}. {p['nombre']:40s} → {p['slug']}")
        if len(peliculas_unicas) > 5:
            print(f"   ... y {len(peliculas_unicas) - 5} más\n")
        
        return peliculas_unicas
        
    except Exception as e:
        print(f"✗ Error cargando películas: {e}")
        traceback.print_exc()
        return []

def limpiar_cache_y_cookies(driver):
    """Limpia cache, cookies y datos de sesión"""
    try:
        # Limpiar localStorage
        driver.execute_script("window.localStorage.clear();")
        # Limpiar sessionStorage
        driver.execute_script("window.sessionStorage.clear();")
        # Eliminar todas las cookies
        driver.delete_all_cookies()
        time.sleep(1)
        return True
    except Exception as e:
        print(f"⚠️ Error limpiando cache: {str(e)[:50]}")
        return False

def hacer_login(driver):
    """
    Realiza el proceso de login en Cinemark
    Retorna: True si login exitoso, False si falla
    """
    try:
        print("→ Iniciando sesión en Cinemark...")
        
        # Buscar y hacer clic en el botón de login (icono de usuario)
        selectores_login = [
            "button[data-testid='header_user_profile']",
            "button[class*='user']",
            "a[href*='login']",
        ]
        
        boton_login = None
        for selector in selectores_login:
            try:
                boton_login = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except:
                continue
        
        if not boton_login:
            print("✗ No se encontró botón de login")
            return False
        
        driver.execute_script("arguments[0].click();", boton_login)
        time.sleep(3)
        
        # Ingresar email
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
            )
            email_input.clear()
            email_input.send_keys(EMAIL)
            time.sleep(1)
        except:
            print("✗ No se encontró campo de email")
            return False
        
        # Ingresar password
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
            password_input.clear()
            password_input.send_keys(PASSWORD)
            time.sleep(1)
        except:
            print("✗ No se encontró campo de password")
            return False
        
        # Hacer clic en el botón de "Iniciar sesión"
        try:
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            driver.execute_script("arguments[0].click();", submit_button)
            time.sleep(5)
        except:
            print("✗ No se encontró botón de submit")
            return False
        
        # Verificar si el login fue exitoso
        # (Verificar si el botón de usuario cambió o si hay un nombre de usuario visible)
        try:
            # Buscar indicador de sesión activa
            usuario_activo = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='header_user_profile']")
            if usuario_activo:
                print("✓ Login exitoso\n")
                return True
        except:
            pass
        
        print("✗ Login falló\n")
        return False
        
    except Exception as e:
        print(f"✗ Error en login: {e}\n")
        return False

def abrir_sidebar_cines(driver):
    """
    Abre el sidebar/modal de selección de cines si está cerrado
    Retorna: True si se abrió o ya estaba abierto
    """
    try:
        print(f"      → Verificando sidebar de cines...")
        
        # Verificar si el modal ya está abierto
        try:
            modal_abierto = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='teather-appply-button']")
            if modal_abierto and modal_abierto[0].is_displayed():
                print(f"      ✓ Modal de cines ya está abierto")
                return True
        except:
            pass
        
        # Buscar el botón para abrir el sidebar de cines
        # Puede ser un botón con el nombre del cine actual o un icono
        selectores_abrir = [
            "button[data-testid='teather-selector-button']",
            "button[class*='teather']",
            "//button[contains(text(), 'Cine')]",
            "//button[contains(@class, 'MuiButton') and contains(., 'Cinemark')]",
        ]
        
        boton_abrir = None
        for selector in selectores_abrir:
            try:
                if selector.startswith("//"):
                    elementos = driver.find_elements(By.XPATH, selector)
                else:
                    elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for elem in elementos:
                    if elem.is_displayed():
                        boton_abrir = elem
                        break
                
                if boton_abrir:
                    break
            except:
                continue
        
        if not boton_abrir:
            print(f"      ⚠️ No se encontró botón para abrir sidebar (puede que ya esté abierto)")
            return True  # Asumimos que está abierto
        
        # Hacer clic para abrir el sidebar
        driver.execute_script("arguments[0].click();", boton_abrir)
        time.sleep(2)
        print(f"      ✓ Sidebar de cines abierto")
        return True
        
    except Exception as e:
        print(f"      ✗ Error abriendo sidebar: {str(e)[:50]}")
        return False

def aceptar_cookies_si_aparece(driver):
    """
    Detecta y acepta el modal de cookies si aparece
    """
    try:
        # Buscar el botón de aceptar cookies
        boton_cookies = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='acceptance_cookies_modal_button']")
        if boton_cookies and boton_cookies[0].is_displayed():
            print(f"      → Modal de cookies detectado, aceptando...")
            driver.execute_script("arguments[0].click();", boton_cookies[0])
            time.sleep(1)
            print(f"      ✓ Cookies aceptadas")
            return True
        return False
    except Exception as e:
        return False

def detectar_modal_inicial_cines(driver):
    """
    Detecta si el modal de selección de cines aparece automáticamente
    al entrar a una película (cuando no hay cine seleccionado)
    Retorna: True si el modal está presente
    """
    try:
        # Primero aceptar cookies si aparecen
        aceptar_cookies_si_aparece(driver)
        
        time.sleep(2)
        
        # Buscar el modal con la lista de cines
        modal_elementos = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='teather-appply-button']")
        
        if modal_elementos and modal_elementos[0].is_displayed():
            # Verificar si el botón está deshabilitado (sin cine seleccionado)
            boton_texto = modal_elementos[0].text
            if "Selecciona un cine" in boton_texto or "disabled" in modal_elementos[0].get_attribute("class"):
                print(f"      ✓ Modal de selección de cines detectado (se requiere selección)")
                return True
        
        return False
        
    except Exception as e:
        print(f"      ⚠️ Error detectando modal: {str(e)[:50]}")
        return False

def desmarcar_cines_seleccionados(driver):
    """
    Desmarca cualquier cine que esté seleccionado actualmente en el modal
    Útil para limpiar selecciones previas
    """
    try:
        # Buscar checkboxes marcados (input checked)
        checkboxes_marcados = driver.find_elements(
            By.XPATH, 
            "//label[@data-testid='teather-item']//input[@type='checkbox' and @data-indeterminate='false']"
        )
        
        for checkbox in checkboxes_marcados:
            try:
                # Verificar si está checked
                if checkbox.is_selected():
                    # Hacer clic en el label padre para desmarcar
                    label = checkbox.find_element(By.XPATH, "./ancestor::label[@data-testid='teather-item']")
                    driver.execute_script("arguments[0].click();", label)
                    time.sleep(0.3)
            except:
                continue
        
        return True
    except Exception as e:
        print(f"      ⚠️ Error desmarcando cines: {str(e)[:50]}")
        return False

def seleccionar_cine_en_sidebar(driver, nombre_cine):
    """
    Selecciona un cine específico en el sidebar lateral o modal
    Retorna: True si selección exitosa
    """
    try:
        print(f"      → Seleccionando cine: {nombre_cine}")
        
        # CRÍTICO: Aceptar cookies si aparecen (bloquean todo)
        aceptar_cookies_si_aparece(driver)
        time.sleep(2)
        
        # Primero detectar si el modal está abierto automáticamente
        modal_auto = detectar_modal_inicial_cines(driver)
        
        # SIEMPRE intentar abrir el sidebar (por si no se detectó o tardó en cargar)
        if not modal_auto:
            print(f"      → Modal no detectado automáticamente, abriendo sidebar...")
            if not abrir_sidebar_cines(driver):
                print(f"      ✗ No se pudo abrir el sidebar de cines")
                return False
        else:
            # Incluso si se detectó, esperar un poco más para asegurar carga
            time.sleep(1)
        
        # Esperar EXPLÍCITAMENTE a que los elementos de cine se carguen
        print(f"      → Esperando a que se carguen los cines en el modal...")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "label[data-testid='teather-item']"))
            )
            time.sleep(2)  # Espera adicional para carga completa
            print(f"      ✓ Elementos de cine cargados")
        except TimeoutException:
            print(f"      ✗ Timeout esperando elementos de cine")
            return False
        
        # Desmarcar cualquier cine previamente seleccionado
        desmarcar_cines_seleccionados(driver)
        time.sleep(0.5)
        
        # Buscar el checkbox del cine usando el nombre
        # IMPORTANTE: El nombre está FUERA del label, en un <p> anterior
        # Estructura: <p>Nombre</p> ... <label data-testid="teather-item">
        selectores_cine = [
            # Buscar el <p> con el nombre, luego el label que está después en el DOM
            f"//p[@class='MuiTypography-root MuiTypography-body1 mui-mbobke' and text()='{nombre_cine}']/following::label[@data-testid='teather-item'][1]",
            f"//p[contains(@class, 'mui-mbobke') and text()='{nombre_cine}']/following::label[@data-testid='teather-item'][1]",
            f"//p[text()='{nombre_cine}']/following::label[@data-testid='teather-item'][1]",
        ]
        
        elemento_cine = None
        for selector in selectores_cine:
            try:
                elementos = driver.find_elements(By.XPATH, selector)
                if elementos:
                    # Buscar el primero visible
                    for elem in elementos:
                        if elem.is_displayed():
                            elemento_cine = elem
                            break
                
                if elemento_cine:
                    break
            except:
                continue
        
        if not elemento_cine:
            print(f"      ✗ No se encontró el cine '{nombre_cine}' en el sidebar")
            # Listar cines disponibles para debug
            print(f"      → Intentando listar cines disponibles...")
            try:
                # Intentar varios selectores para encontrar los nombres
                selectores_debug = [
                    # Los nombres NO están dentro del label, están en <p> separados antes
                    "//p[@class='MuiTypography-root MuiTypography-body1 mui-mbobke']",
                    "//div[@class='MuiBox-root mui-1lekzkb']/p[@class='MuiTypography-root MuiTypography-body1 mui-mbobke']",
                    "//p[contains(@class, 'mui-mbobke')]",
                ]
                
                cines_disponibles = []
                for selector in selectores_debug:
                    try:
                        if selector.startswith("//"):
                            elementos = driver.find_elements(By.XPATH, selector)
                        else:
                            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        if elementos:
                            cines_disponibles = elementos
                            print(f"      ✓ Encontrados {len(elementos)} elementos con selector: {selector[:50]}")
                            break
                    except:
                        continue
                
                if cines_disponibles:
                    print(f"      → Primeros 5 cines disponibles:")
                    for i, cine in enumerate(cines_disponibles[:5], 1):
                        texto = cine.text.strip()
                        if texto:
                            print(f"        {i}. '{texto}'")
                    if len(cines_disponibles) > 5:
                        print(f"        ... y {len(cines_disponibles) - 5} más")
                else:
                    print(f"      ✗ No se encontraron elementos de cine con ningún selector")
            except Exception as e:
                print(f"      ⚠️ Error listando cines: {str(e)}")
            return False
        
        # Scroll al elemento
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_cine)
        time.sleep(0.5)
        
        # Hacer clic en el checkbox/label
        driver.execute_script("arguments[0].click();", elemento_cine)
        time.sleep(1)
        
        # Esperar a que el botón "Aplicar" se habilite
        print(f"      → Esperando que botón 'Aplicar' se habilite...")
        time.sleep(1)
        
        # Hacer clic en el botón "Aplicar"
        try:
            # Esperar a que el botón NO esté disabled
            boton_aplicar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='teather-appply-button']"))
            )
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_aplicar)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", boton_aplicar)
            time.sleep(3)
            print(f"      ✓ Cine seleccionado y aplicado")
            return True
        except TimeoutException:
            print(f"      ✗ Timeout: botón Aplicar no se habilitó")
            return False
        except Exception as e:
            print(f"      ✗ Error al hacer clic en Aplicar: {str(e)[:50]}")
            return False
        
    except Exception as e:
        print(f"      ✗ Error seleccionando cine: {str(e)[:50]}")
        traceback.print_exc()
        return False

def extraer_precios_de_pagina(driver):
    """
    Extrae los precios de la página de compra de Cinemark
    Retorna: [{'categoria': 'GENERAL', 'tipo': 'PROMO ONLINE', 'precio': '8.50'}, ...]
    """
    precios = []
    try:
        time.sleep(2)
        
        print("      → Extrayendo precios...")
        
        # Buscar todas las secciones de precios (GENERAL y CONVENIOS)
        # Cada sección tiene un <h2> con el título y luego los ticket-card dentro
        secciones = driver.find_elements(By.CSS_SELECTOR, "div.MuiBox-root.mui-0")
        
        if not secciones:
            print("      ✗ No se encontraron secciones de precios")
            return []
        
        patron_precio = re.compile(r'S/\s*(\d+\.?\d*)')
        
        for seccion in secciones:
            try:
                # Buscar el h2 con la categoría (general/convenios)
                h2_elementos = seccion.find_elements(By.CSS_SELECTOR, "h2.MuiTypography-h2")
                if not h2_elementos:
                    continue
                
                categoria = h2_elementos[0].text.strip().upper()
                if not categoria or categoria not in ['GENERAL', 'CONVENIOS']:
                    continue
                
                # Buscar todos los ticket-card en esta sección
                tickets = seccion.find_elements(By.CSS_SELECTOR, "div[data-testid='ticket-card']")
                
                for ticket in tickets:
                    try:
                        # Extraer el tipo de entrada (p con clase mui-ntz2ds)
                        tipo_elem = ticket.find_element(By.CSS_SELECTOR, "p.MuiTypography-body2.mui-ntz2ds")
                        tipo_entrada = tipo_elem.text.strip()
                        
                        # Extraer el precio (p con clase mui-12idbfl)
                        precio_elem = ticket.find_element(By.CSS_SELECTOR, "p.MuiTypography-body2.mui-12idbfl")
                        precio_texto = precio_elem.text.strip()
                        
                        # Extraer solo el número del precio
                        match = patron_precio.search(precio_texto)
                        if match:
                            precio = match.group(1)
                            
                            precios.append({
                                'categoria': categoria,
                                'tipo': tipo_entrada,
                                'precio': precio
                            })
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        # Eliminar duplicados
        precios_unicos = []
        precios_vistos = set()
        for p in precios:
            key = f"{p['categoria']}_{p['tipo']}_{p['precio']}"
            if key not in precios_vistos:
                precios_unicos.append(p)
                precios_vistos.add(key)
        
        print(f"      ✓ Extraídos {len(precios_unicos)} precios")
        for p in precios_unicos:
            print(f"        • [{p['categoria']}] {p['tipo']}: S/{p['precio']}")
        
        return precios_unicos
        
    except Exception as e:
        print(f"      ✗ Error extrayendo precios: {str(e)[:100]}")
        traceback.print_exc()
        return []

def cancelar_compra_y_volver(driver, url_pelicula):
    """
    Cancela la compra actual y vuelve a la página de la película
    """
    try:
        print("      → Cancelando compra...")
        
        # Buscar botón de cancelar/cerrar
        selectores_cancelar = [
            "button[class*='close']",
            "button[class*='cancel']",
            "svg[class*='close']",
        ]
        
        for selector in selectores_cancelar:
            try:
                boton = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].click();", boton)
                time.sleep(2)
                break
            except:
                continue
        
        # Volver a la página de la película
        driver.get(url_pelicula)
        time.sleep(2)
        
        # Limpiar cache y cookies
        limpiar_cache_y_cookies(driver)
        
        print("      ✓ Compra cancelada")
        return True
        
    except Exception as e:
        print(f"      ✗ Error cancelando: {str(e)[:50]}")
        return False

def procesar_pelicula_cine(driver, pelicula, cine_nombre, tiene_sesion):
    """
    Procesa una película en un cine específico y extrae los precios.
    ASUME que ya estamos en la página de la película y el cine ya está seleccionado.
    """
    datos_extraidos = []
    
    try:
        print(f"    → Buscando horarios disponibles...")
        
        # Buscar y hacer clic en el primer horario disponible
        try:
            # Buscar tarjetas de horario (estructura: div.showtime-card-item)
            selectores_horario = [
                "div.showtime-card-item",  # Clase exacta de las tarjetas de horario
                "div[class*='showtime-card']",
                "div[class*='mui-v86l4p']",  # Clase específica vista en el HTML
            ]
            
            elemento_horario = None
            for selector in selectores_horario:
                try:
                    elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elementos:
                        # Filtrar solo elementos visibles
                        elementos_visibles = [e for e in elementos if e.is_displayed()]
                        if elementos_visibles:
                            elemento_horario = elementos_visibles[0]
                            print(f"    ✓ Encontrados {len(elementos_visibles)} horarios con selector: {selector}")
                            break
                except:
                    continue
            
            if not elemento_horario:
                print(f"    ✗ No hay horarios disponibles")
                return []
            
            print(f"    → Haciendo clic en horario...")
            # Hacer clic en el horario
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_horario)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", elemento_horario)
            time.sleep(3)
            
        except Exception as e:
            print(f"      ✗ Error haciendo clic en horario: {str(e)[:50]}")
            return []
        
        # Hacer clic en "COMPRAR ENTRADAS"
        try:
            selectores_comprar = [
                "button[data-testid='buy-tickets-button']",
                "//button[contains(text(), 'COMPRAR')]",
            ]
            
            boton_comprar = None
            for selector in selectores_comprar:
                try:
                    if selector.startswith("//"):
                        boton_comprar = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        boton_comprar = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    break
                except:
                    continue
            
            if not boton_comprar:
                print(f"    ✗ No se encontró botón COMPRAR ENTRADAS")
                return []
            
            print(f"    → Haciendo clic en COMPRAR ENTRADAS...")
            driver.execute_script("arguments[0].click();", boton_comprar)
            time.sleep(3)  # Esperar pantalla de pre-compra
            
        except Exception as e:
            print(f"    ✗ Error haciendo clic en COMPRAR: {str(e)[:50]}")
            return []
        
        # YA NO necesitamos hacer login aquí - se hizo al inicio del script
        # La sesión se mantiene durante toda la ejecución
        
        # Hacer clic en el botón "Continuar" para ir a la página de precios
        try:
            print(f"    → Haciendo clic en botón 'Continuar'...")
            # Usar contains() para mayor flexibilidad con espacios/formato
            boton_continuar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'MuiButton-fixedPrimary')]//div[contains(text(), 'Continuar')]"))
            )
            # Scroll al centro de la pantalla
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_continuar)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", boton_continuar)
            time.sleep(5)  # Esperar que cargue la página con los precios
            print(f"    ✓ Página de precios cargada")
        except Exception as e:
            print(f"    ✗ Error al hacer clic en 'Continuar': {str(e)[:100]}")
            return []
        
        # Extraer precios
        precios = extraer_precios_de_pagina(driver)
        
        # Determinar modalidad (si es posible desde la URL o página)
        modalidad = "2D"  # Valor por defecto
        try:
            url_actual = driver.current_url
            if "3d" in url_actual.lower():
                modalidad = "3D"
            elif "imax" in url_actual.lower():
                modalidad = "IMAX"
        except:
            pass
        
        # Construir datos extraídos con el nuevo formato
        for precio_data in precios:
            datos_extraidos.append({
                'cine': cine_nombre,
                'pelicula': pelicula['nombre'],
                'modalidad': modalidad,
                'tipo_entrada': precio_data['tipo'],
                'precio': precio_data['precio'],
                'beneficio': precio_data['categoria']  # Ahora es 'GENERAL' o 'CONVENIOS'
            })
        
        # Ya no necesitamos cancelar y volver - el main() se encarga de volver a la película
        print(f"    ✓ Extracción completada para este cine")
        
        return datos_extraidos
        
    except Exception as e:
        print(f"      ✗ Error procesando película: {str(e)[:100]}")
        traceback.print_exc()
        return []

def main():
    print("=" * 80)
    print("CINEMARK PERU - EXTRACTOR DE PRECIOS")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL Base: {BASE_URL}")
    print(f"Modo: {'Headless (sin ventana)' if HEADLESS else 'Navegador Visible'}")
    print(f"Limite de cines: {MAX_CINES if MAX_CINES else 'Todos'}")
    print(f"Limite de películas: {MAX_PELICULAS if MAX_PELICULAS else 'Todas'}")
    print(f"Login: {'Activado' if EMAIL else 'Desactivado'}")
    print("=" * 80)
    print()
    
    archivo_progreso = "precios_cinemark_EN_PROGRESO.csv"
    
    driver = None
    todos_los_datos = []
    
    try:
        # Configurar driver
        driver = configurar_driver()
        
        # IMPORTANTE: Hacer login AL INICIO para mantener sesión durante toda la extracción
        tiene_sesion = bool(EMAIL and PASSWORD)
        if tiene_sesion:
            print("→ Realizando login inicial...")
            print("  (Esto evitará el modal de login en cada compra)")
            # Ir a la página principal primero
            driver.get(BASE_URL)
            time.sleep(3)
            
            # Aceptar cookies si aparecen
            try:
                boton_cookies = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='acceptance_cookies_modal_button']")
                if boton_cookies and boton_cookies[0].is_displayed():
                    print("  → Aceptando cookies...")
                    driver.execute_script("arguments[0].click();", boton_cookies[0])
                    time.sleep(2)
            except:
                pass
            
            # Hacer login
            if hacer_login(driver):
                print("✓ Sesión iniciada correctamente\n")
            else:
                print("⚠️ No se pudo iniciar sesión, continuando sin login\n")
                tiene_sesion = False
        else:
            print("→ Modo sin login\n")
        
        # Cargar películas desde la página principal
        peliculas = cargar_peliculas_desde_lista(driver)
        
        if not peliculas:
            print("✗ No se pudieron cargar películas")
            return
        
        # Aplicar límite si existe
        if MAX_PELICULAS:
            peliculas = peliculas[:MAX_PELICULAS]
        
        # Cargar lista de cines desde archivo TXT
        try:
            with open('lista_cines_cinemark.txt', 'r', encoding='utf-8') as f:
                cines = [linea.strip() for linea in f.readlines() if linea.strip()]
            print(f"✓ Cargados {len(cines)} cines desde 'lista_cines_cinemark.txt'\n")
        except FileNotFoundError:
            print("⚠️ No se encontró 'lista_cines_cinemark.txt', usando lista por defecto")
            cines = [
                "Cinemark San Miguel",
                "Cinemark Plaza Lima Sur",
                "Cinemark Jockey Plaza",
                "Cinemark MallPlaza Angamos",
            ]
        
        # Aplicar límite si existe
        if MAX_CINES:
            cines = cines[:MAX_CINES]
            print(f"  (Limitado a {MAX_CINES} por configuración)\n")
        
        print(f"\n{'='*80}")
        print(f"PROCESANDO {len(peliculas)} PELÍCULAS × {len(cines)} CINES")
        print(f"{'='*80}\n")
        
        # Crear archivo CSV con encabezados
        with open(archivo_progreso, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'cine', 'pelicula', 'modalidad',
                'tipo_entrada', 'precio', 'beneficio'
            ])
            writer.writeheader()
        
        # tiene_sesion ya se definió al inicio (después del login)
        
        # NUEVA LÓGICA: Procesar cada PELÍCULA, probando todos los CINES
        for idx_pelicula, pelicula in enumerate(peliculas, 1):
            print(f"\n[PELÍCULA {idx_pelicula}/{len(peliculas)}] {pelicula['nombre']}")
            print("=" * 80)
            
            # Navegar a la película UNA VEZ
            url_pelicula = f"{BASE_URL}/pelicula/{pelicula['slug']}"
            print(f"URL: {url_pelicula}")
            driver.get(url_pelicula)
            time.sleep(3)
            
            # Probar cada cine para esta película
            for idx_cine, cine_nombre in enumerate(cines, 1):
                print(f"\n  [{idx_cine}/{len(cines)}] Cine: {cine_nombre}")
                print("  " + "-" * 76)
                
                # Seleccionar el cine en el modal
                print(f"    → Seleccionando cine en el modal...")
                if not seleccionar_cine_en_sidebar(driver, cine_nombre):
                    print(f"    ✗ No se pudo seleccionar el cine, pasando al siguiente")
                    continue
                
                # Esperar a que se actualice la página con el cine seleccionado
                time.sleep(3)
                
                # Intentar procesar esta combinación película-cine
                datos_pelicula = procesar_pelicula_cine(driver, pelicula, cine_nombre, tiene_sesion)
                
                if datos_pelicula:
                    # Guardar inmediatamente en CSV
                    with open(archivo_progreso, 'a', newline='', encoding='utf-8-sig') as f:
                        writer = csv.DictWriter(f, fieldnames=[
                            'cine', 'pelicula', 'modalidad',
                            'tipo_entrada', 'precio', 'beneficio'
                        ])
                        writer.writerows(datos_pelicula)
                    
                    todos_los_datos.extend(datos_pelicula)
                    print(f"    ✓ Guardados {len(datos_pelicula)} registros")
                else:
                    print(f"    → No hay datos para esta combinación")
                
                # Volver a la página de la película para probar el siguiente cine
                driver.get(url_pelicula)
                time.sleep(2)
        
        # Renombrar archivo final
        if todos_los_datos:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_final = f"precios_cinemark_COMPLETO_{timestamp}.csv"
            
            import os
            os.rename(archivo_progreso, archivo_final)
            
            print("\n" + "=" * 80)
            print("EXTRACCIÓN COMPLETADA")
            print("=" * 80)
            print(f"✓ Total registros:   {len(todos_los_datos)}")
            print(f"✓ Cines procesados:  {len(set(d['cine'] for d in todos_los_datos))}")
            print(f"✓ Películas:         {len(set(d['pelicula'] for d in todos_los_datos))}")
            print(f"✓ Archivo guardado:  {archivo_final}")
            print("=" * 80)
        else:
            print("\n✗ No se extrajeron datos")
    
    except KeyboardInterrupt:
        print("\n\n✗ Extracción interrumpida por el usuario")
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
