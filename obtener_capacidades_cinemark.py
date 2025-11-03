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
    slug = re.sub(r'[^\w\s-]', '', slug)
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
                nombre = None
                slug = None
                
                # Desde el href del link
                try:
                    href = elem.get_attribute('href')
                    if href and '/pelicula/' in href:
                        slug = href.split('/pelicula/')[-1].strip('/')
                        nombre = slug.replace('-', ' ').title()
                except:
                    pass
                
                # Desde un elemento de texto dentro
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
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        driver.delete_all_cookies()
        time.sleep(1)
        return True
    except Exception as e:
        return False

def hacer_login(driver):
    """
    Realiza el proceso de login en Cinemark
    Retorna: True si login exitoso, False si falla
    """
    try:
        print("      → Iniciando sesión...")
        
        # Buscar y hacer clic en el botón de login
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
            return False
        
        driver.execute_script("arguments[0].click();", boton_login)
        time.sleep(3)
        
        # Ingresar email
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
        )
        email_input.clear()
        email_input.send_keys(EMAIL)
        time.sleep(1)
        
        # Ingresar password
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
        password_input.clear()
        password_input.send_keys(PASSWORD)
        time.sleep(1)
        
        # Hacer clic en submit
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", submit_button)
        time.sleep(5)
        
        print("      ✓ Login exitoso")
        return True
        
    except Exception as e:
        print(f"      ✗ Error en login: {str(e)[:50]}")
        return False

def seleccionar_cine_en_sidebar(driver, nombre_cine):
    """
    Selecciona un cine específico en el sidebar lateral
    Retorna: True si selección exitosa
    """
    try:
        print(f"      → Seleccionando cine: {nombre_cine}")
        time.sleep(2)
        
        # Buscar el checkbox del cine
        selectores_cine = [
            f"//p[contains(@class, 'MuiTypography') and text()='{nombre_cine}']/ancestor::label",
            f"//label[@data-testid='teather-item']//p[text()='{nombre_cine}']",
        ]
        
        elemento_cine = None
        for selector in selectores_cine:
            try:
                elemento_cine = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                break
            except:
                continue
        
        if not elemento_cine:
            print(f"      ✗ No se encontró el cine")
            return False
        
        # Scroll y click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_cine)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", elemento_cine)
        time.sleep(1)
        
        # Hacer clic en Aplicar
        boton_aplicar = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='teather-appply-button']"))
        )
        driver.execute_script("arguments[0].click();", boton_aplicar)
        time.sleep(3)
        
        print(f"      ✓ Cine seleccionado")
        return True
        
    except Exception as e:
        print(f"      ✗ Error seleccionando cine: {str(e)[:50]}")
        return False

def extraer_capacidad_total_sala(driver):
    """
    Extrae la capacidad total de la sala contando todos los asientos
    Retorna: {'total': int, 'disponibles': int, 'ocupados': int}
    """
    try:
        print("      → Extrayendo capacidad de la sala...")
        time.sleep(3)
        
        # Buscar todos los asientos en el mapa de asientos
        selectores_asientos = [
            "div[class*='seat']",
            "button[class*='seat']",
            "span[class*='seat']",
        ]
        
        todos_asientos = []
        for selector in selectores_asientos:
            try:
                asientos = driver.find_elements(By.CSS_SELECTOR, selector)
                if asientos:
                    todos_asientos = asientos
                    break
            except:
                continue
        
        if not todos_asientos:
            print("      ✗ No se encontró el mapa de asientos")
            return None
        
        # Contar asientos por estado
        disponibles = 0
        ocupados = 0
        
        for asiento in todos_asientos:
            try:
                clases = asiento.get_attribute('class') or ''
                
                # Identificar estado del asiento
                if 'available' in clases.lower() or 'libre' in clases.lower():
                    disponibles += 1
                elif 'occupied' in clases.lower() or 'ocupado' in clases.lower() or 'taken' in clases.lower():
                    ocupados += 1
            except:
                continue
        
        total = disponibles + ocupados
        
        resultado = {
            'total': total,
            'disponibles': disponibles,
            'ocupados': ocupados
        }
        
        print(f"      ✓ Capacidad: {total} asientos (Disponibles: {disponibles}, Ocupados: {ocupados})")
        return resultado
        
    except Exception as e:
        print(f"      ✗ Error extrayendo capacidad: {str(e)[:100]}")
        return None

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
    Procesa una película en un cine específico y extrae las capacidades
    """
    try:
        # Construir URL de la película
        url_pelicula = f"{BASE_URL}/pelicula/{pelicula['slug']}"
        print(f"    → Película: {pelicula['nombre']}")
        print(f"      URL: {url_pelicula}")
        
        # Navegar a la película
        driver.get(url_pelicula)
        time.sleep(4)
        
        # Limpiar cache y cookies
        limpiar_cache_y_cookies(driver)
        time.sleep(2)
        
        # Seleccionar cine en el sidebar
        if not seleccionar_cine_en_sidebar(driver, cine_nombre):
            return None
        
        # Buscar y hacer clic en el primer horario disponible
        try:
            selectores_horario = [
                "button[class*='showtime']",
                "button[class*='schedule']",
                "button[class*='session']",
            ]
            
            boton_horario = None
            for selector in selectores_horario:
                try:
                    botones = driver.find_elements(By.CSS_SELECTOR, selector)
                    if botones:
                        boton_horario = botones[0]
                        break
                except:
                    continue
            
            if not boton_horario:
                print(f"      ✗ No hay horarios disponibles")
                return None
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_horario)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", boton_horario)
            time.sleep(3)
            
        except Exception as e:
            print(f"      ✗ Error haciendo clic en horario: {str(e)[:50]}")
            return None
        
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
                print(f"      ✗ No se encontró botón COMPRAR")
                return None
            
            driver.execute_script("arguments[0].click();", boton_comprar)
            time.sleep(3)
            
        except Exception as e:
            print(f"      ✗ Error haciendo clic en COMPRAR: {str(e)[:50]}")
            return None
        
        # Si tiene sesión, hacer login
        if tiene_sesion:
            if not hacer_login(driver):
                return None
        
        # Hacer clic en "Continuar" después del login
        try:
            boton_continuar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CONTINUAR') or contains(text(), 'Continuar')]"))
            )
            driver.execute_script("arguments[0].click();", boton_continuar)
            time.sleep(3)
        except:
            pass
        
        # Hacer clic en una entrada para llegar a la selección de asientos
        try:
            # Buscar botón de +/agregar entrada
            selectores_entrada = [
                "button[class*='add']",
                "button[class*='plus']",
                "button:has(svg[class*='plus'])",
            ]
            
            boton_entrada = None
            for selector in selectores_entrada:
                try:
                    botones = driver.find_elements(By.CSS_SELECTOR, selector)
                    if botones:
                        boton_entrada = botones[0]
                        break
                except:
                    continue
            
            if boton_entrada:
                driver.execute_script("arguments[0].click();", boton_entrada)
                time.sleep(2)
        except:
            pass
        
        # Hacer clic en "Continuar" para ir a selección de asientos
        try:
            boton_continuar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CONTINUAR') or contains(text(), 'Continuar')]"))
            )
            driver.execute_script("arguments[0].click();", boton_continuar)
            time.sleep(4)
        except Exception as e:
            print(f"      ✗ No se pudo llegar a selección de asientos: {str(e)[:50]}")
            return None
        
        # Extraer capacidad de la sala
        capacidad = extraer_capacidad_total_sala(driver)
        
        if not capacidad:
            return None
        
        # Determinar modalidad
        modalidad = "2D"
        try:
            url_actual = driver.current_url
            if "3d" in url_actual.lower():
                modalidad = "3D"
            elif "imax" in url_actual.lower():
                modalidad = "IMAX"
        except:
            pass
        
        # Construir datos
        datos = {
            'cine': cine_nombre,
            'pelicula': pelicula['nombre'],
            'modalidad': modalidad,
            'capacidad_total': capacidad['total'],
            'asientos_disponibles': capacidad['disponibles'],
            'asientos_ocupados': capacidad['ocupados']
        }
        
        # Cancelar compra y volver
        cancelar_compra_y_volver(driver, url_pelicula)
        
        return datos
        
    except Exception as e:
        print(f"      ✗ Error procesando película: {str(e)[:100]}")
        traceback.print_exc()
        return None

def main():
    print("=" * 80)
    print("CINEMARK PERU - EXTRACTOR DE CAPACIDADES")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL Base: {BASE_URL}")
    print(f"Modo: {'Headless (sin ventana)' if HEADLESS else 'Navegador Visible'}")
    print(f"Limite de cines: {MAX_CINES if MAX_CINES else 'Todos'}")
    print(f"Limite de películas: {MAX_PELICULAS if MAX_PELICULAS else 'Todas'}")
    print(f"Login: {'Activado' if EMAIL else 'Desactivado'}")
    print("=" * 80)
    print()
    
    archivo_progreso = "capacidades_cinemark_EN_PROGRESO.csv"
    
    driver = None
    todos_los_datos = []
    
    try:
        # Configurar driver
        driver = configurar_driver()
        
        # Cargar películas
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
        print(f"PROCESANDO {len(cines)} CINES × {len(peliculas)} PELÍCULAS")
        print(f"{'='*80}\n")
        
        # Crear archivo CSV con encabezados
        with open(archivo_progreso, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'cine', 'pelicula', 'modalidad',
                'capacidad_total', 'asientos_disponibles', 'asientos_ocupados'
            ])
            writer.writeheader()
        
        # Determinar si tiene sesión
        tiene_sesion = bool(EMAIL and PASSWORD)
        
        # Procesar cada cine
        for idx_cine, cine_nombre in enumerate(cines, 1):
            print(f"\n[CINE {idx_cine}/{len(cines)}] {cine_nombre}")
            print("-" * 80)
            
            # Procesar cada película en este cine
            for idx_pelicula, pelicula in enumerate(peliculas, 1):
                print(f"  [{idx_pelicula}/{len(peliculas)}]")
                
                datos_pelicula = procesar_pelicula_cine(driver, pelicula, cine_nombre, tiene_sesion)
                
                if datos_pelicula:
                    # Guardar inmediatamente en CSV
                    with open(archivo_progreso, 'a', newline='', encoding='utf-8-sig') as f:
                        writer = csv.DictWriter(f, fieldnames=[
                            'cine', 'pelicula', 'modalidad',
                            'capacidad_total', 'asientos_disponibles', 'asientos_ocupados'
                        ])
                        writer.writerow(datos_pelicula)
                    
                    todos_los_datos.append(datos_pelicula)
                    print(f"    ✓ Capacidad guardada: {datos_pelicula['capacidad_total']} asientos")
                
                time.sleep(2)
        
        # Renombrar archivo final
        if todos_los_datos:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_final = f"capacidades_cinemark_COMPLETO_{timestamp}.csv"
            
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
