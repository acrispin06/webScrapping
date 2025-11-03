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

def seleccionar_cine_en_sidebar(driver, nombre_cine):
    """
    Selecciona un cine específico en el sidebar lateral
    Retorna: True si selección exitosa
    """
    try:
        print(f"      → Seleccionando cine: {nombre_cine}")
        time.sleep(2)
        
        # Buscar el checkbox del cine usando el nombre
        # El selector usa data-testid="teather-item"
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
            print(f"      ✗ No se encontró el cine '{nombre_cine}' en el sidebar")
            return False
        
        # Scroll al elemento
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_cine)
        time.sleep(0.5)
        
        # Hacer clic en el checkbox
        driver.execute_script("arguments[0].click();", elemento_cine)
        time.sleep(1)
        
        # Hacer clic en el botón "Aplicar"
        try:
            boton_aplicar = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='teather-appply-button']"))
            )
            driver.execute_script("arguments[0].click();", boton_aplicar)
            time.sleep(3)
            print(f"      ✓ Cine seleccionado")
            return True
        except:
            print(f"      ✗ No se encontró botón Aplicar")
            return False
        
    except Exception as e:
        print(f"      ✗ Error seleccionando cine: {str(e)[:50]}")
        return False

def extraer_precios_de_pagina(driver):
    """
    Extrae los precios de la página de compra de Cinemark
    Retorna: [{'tipo': 'General', 'precio': '25.00'}, ...]
    """
    precios = []
    try:
        time.sleep(3)
        
        print("      → Extrayendo precios...")
        
        # Buscar elementos de precio en la página
        # Los precios suelen estar en elementos con clases como "price", "amount", etc.
        selectores_precio = [
            "div[class*='price']",
            "span[class*='price']",
            "p[class*='price']",
            "div[class*='amount']",
        ]
        
        elementos_precio = []
        for selector in selectores_precio:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                if elementos:
                    elementos_precio = elementos
                    break
            except:
                continue
        
        if not elementos_precio:
            print("      ✗ No se encontraron elementos de precio")
            return []
        
        # Extraer texto de cada elemento y buscar patrones de precio
        patron_precio = re.compile(r'S/?\s*(\d+\.?\d*)')
        
        for elem in elementos_precio:
            try:
                texto = elem.text.strip()
                match = patron_precio.search(texto)
                if match:
                    precio = match.group(1)
                    
                    # Intentar determinar el tipo de entrada
                    tipo = "General"
                    if "socio" in texto.lower() or "miembro" in texto.lower():
                        tipo = "Socio"
                    elif "niño" in texto.lower() or "kids" in texto.lower():
                        tipo = "Niño"
                    
                    precios.append({
                        'tipo': tipo,
                        'precio': precio
                    })
            except:
                continue
        
        # Eliminar duplicados
        precios_unicos = []
        precios_vistos = set()
        for p in precios:
            key = f"{p['tipo']}_{p['precio']}"
            if key not in precios_vistos:
                precios_unicos.append(p)
                precios_vistos.add(key)
        
        print(f"      ✓ Extraídos {len(precios_unicos)} precios")
        for p in precios_unicos:
            print(f"        • {p['tipo']}: S/{p['precio']}")
        
        return precios_unicos
        
    except Exception as e:
        print(f"      ✗ Error extrayendo precios: {str(e)[:100]}")
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
    Procesa una película en un cine específico y extrae los precios
    """
    datos_extraidos = []
    
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
            print(f"      ✗ No se pudo seleccionar el cine")
            return []
        
        # Buscar y hacer clic en el primer horario disponible
        try:
            # Buscar botones de horario
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
                return []
            
            # Hacer clic en el horario
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_horario)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", boton_horario)
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
                print(f"      ✗ No se encontró botón COMPRAR ENTRADAS")
                return []
            
            driver.execute_script("arguments[0].click();", boton_comprar)
            time.sleep(3)
            
        except Exception as e:
            print(f"      ✗ Error haciendo clic en COMPRAR: {str(e)[:50]}")
            return []
        
        # Si tiene sesión, hacer login
        if tiene_sesion:
            if not hacer_login(driver):
                print(f"      ✗ Login falló")
                return []
        
        # Hacer clic en "Continuar" después del login
        try:
            boton_continuar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CONTINUAR') or contains(text(), 'Continuar')]"))
            )
            driver.execute_script("arguments[0].click();", boton_continuar)
            time.sleep(3)
        except:
            print(f"      ⚠️ No se encontró botón Continuar (puede ser opcional)")
        
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
        
        # Construir datos extraídos
        for precio_data in precios:
            datos_extraidos.append({
                'cine': cine_nombre,
                'pelicula': pelicula['nombre'],
                'modalidad': modalidad,
                'tipo_entrada': precio_data['tipo'],
                'precio': precio_data['precio'],
                'beneficio': 'Si' if tiene_sesion else 'No'
            })
        
        # Cancelar compra y volver
        cancelar_compra_y_volver(driver, url_pelicula)
        
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
        print(f"PROCESANDO {len(cines)} CINES × {len(peliculas)} PELÍCULAS")
        print(f"{'='*80}\n")
        
        # Crear archivo CSV con encabezados
        with open(archivo_progreso, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'cine', 'pelicula', 'modalidad',
                'tipo_entrada', 'precio', 'beneficio'
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
                            'tipo_entrada', 'precio', 'beneficio'
                        ])
                        writer.writerows(datos_pelicula)
                    
                    todos_los_datos.extend(datos_pelicula)
                    print(f"    ✓ Guardados {len(datos_pelicula)} registros")
                
                time.sleep(2)  # Pausa entre películas
        
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
