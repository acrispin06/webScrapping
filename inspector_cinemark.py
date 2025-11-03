"""
INSPECTOR DE CINEMARK PERÚ
Analiza la estructura de la página y las llamadas a API
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json
import requests

BASE_URL = 'https://www.cinemark-peru.com'

def configurar_driver():
    """Configura Chrome con capacidades de logging de red"""
    print("Configurando Chrome WebDriver con logging de red...")
    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Habilitar logging de performance para capturar network requests
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
    
    print("✓ WebDriver configurado\n")
    return driver

def capturar_peticiones_red(driver, duracion_segundos=10):
    """Captura todas las peticiones de red durante un periodo"""
    print(f"Capturando peticiones de red por {duracion_segundos} segundos...")
    
    time.sleep(duracion_segundos)
    
    # Obtener logs de performance
    logs = driver.get_log('performance')
    
    peticiones = []
    for entry in logs:
        try:
            log_data = json.loads(entry['message'])
            message = log_data.get('message', {})
            method = message.get('method', '')
            
            # Filtrar solo peticiones de red
            if 'Network.request' in method or 'Network.response' in method:
                params = message.get('params', {})
                
                if 'request' in params:
                    request_data = params['request']
                    url = request_data.get('url', '')
                    method_http = request_data.get('method', '')
                    
                    # Filtrar URLs relevantes (APIs, JSON, etc)
                    if any(keyword in url.lower() for keyword in ['api', 'json', 'data', 'movie', 'cinema', 'theater', 'price', 'ticket']):
                        peticiones.append({
                            'url': url,
                            'method': method_http,
                            'type': 'REQUEST'
                        })
                
                if 'response' in params:
                    response_data = params['response']
                    url = response_data.get('url', '')
                    
                    if any(keyword in url.lower() for keyword in ['api', 'json', 'data', 'movie', 'cinema', 'theater', 'price', 'ticket']):
                        peticiones.append({
                            'url': url,
                            'status': response_data.get('status', ''),
                            'type': 'RESPONSE'
                        })
        except:
            continue
    
    return peticiones

def analizar_estructura_html(driver):
    """Analiza la estructura HTML de la página"""
    print("\n" + "="*80)
    print("ANÁLISIS DE ESTRUCTURA HTML")
    print("="*80)
    
    try:
        # Buscar secciones principales
        print("\n1. BUSCAR SELECTORES DE CINES:")
        selectores_cines = [
            "a[href*='cinema']",
            "a[href*='cine']",
            "div[class*='cinema']",
            "div[class*='theater']",
            "select option",
            ".cinema-selector",
            ".theater-selector"
        ]
        
        for selector in selectores_cines:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                if elementos:
                    print(f"   ✓ Selector '{selector}': {len(elementos)} elementos")
                    # Mostrar primeros 3 elementos
                    for i, elem in enumerate(elementos[:3]):
                        try:
                            texto = elem.text.strip() if elem.text else elem.get_attribute('href')
                            if texto:
                                print(f"      [{i+1}] {texto[:80]}")
                        except:
                            pass
            except:
                pass
        
        print("\n2. BUSCAR SELECTORES DE PELÍCULAS:")
        selectores_peliculas = [
            "div[class*='movie']",
            "div[class*='film']",
            "div[class*='pelicula']",
            "a[href*='movie']",
            "a[href*='pelicula']",
            ".movie-card",
            ".movie-item",
            ".film-card"
        ]
        
        for selector in selectores_peliculas:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                if elementos:
                    print(f"   ✓ Selector '{selector}': {len(elementos)} elementos")
                    for i, elem in enumerate(elementos[:3]):
                        try:
                            texto = elem.text.strip() if elem.text else elem.get_attribute('href')
                            if texto:
                                print(f"      [{i+1}] {texto[:80]}")
                        except:
                            pass
            except:
                pass
        
        print("\n3. BUSCAR SELECTORES DE HORARIOS:")
        selectores_horarios = [
            "button[class*='time']",
            "button[class*='horario']",
            "button[class*='showtime']",
            "a[class*='time']",
            "div[class*='schedule']",
            ".showtime",
            ".time-selector"
        ]
        
        for selector in selectores_horarios:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                if elementos:
                    print(f"   ✓ Selector '{selector}': {len(elementos)} elementos")
                    for i, elem in enumerate(elementos[:3]):
                        try:
                            texto = elem.text.strip() if elem.text else elem.get_attribute('class')
                            if texto:
                                print(f"      [{i+1}] {texto[:80]}")
                        except:
                            pass
            except:
                pass
        
        print("\n4. BUSCAR SELECTORES DE PRECIOS:")
        selectores_precios = [
            "span[class*='price']",
            "span[class*='precio']",
            "div[class*='price']",
            ".price",
            ".precio",
            "[class*='ticket-type']",
            "[class*='entrada']"
        ]
        
        for selector in selectores_precios:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                if elementos:
                    print(f"   ✓ Selector '{selector}': {len(elementos)} elementos")
                    for i, elem in enumerate(elementos[:3]):
                        try:
                            texto = elem.text.strip()
                            if texto:
                                print(f"      [{i+1}] {texto[:80]}")
                        except:
                            pass
            except:
                pass
        
    except Exception as e:
        print(f"✗ Error en análisis HTML: {e}")

def buscar_apis(driver):
    """Intenta identificar llamadas a APIs"""
    print("\n" + "="*80)
    print("BÚSQUEDA DE APIs")
    print("="*80)
    
    # Scroll para activar carga lazy
    print("\nHaciendo scroll para activar carga de datos...")
    for i in range(3):
        driver.execute_script(f"window.scrollTo(0, {(i+1)*500});")
        time.sleep(1)
    
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    # Capturar peticiones
    peticiones = capturar_peticiones_red(driver, duracion_segundos=5)
    
    # Filtrar y mostrar APIs únicas
    urls_unicas = set()
    apis_relevantes = []
    
    for pet in peticiones:
        url = pet.get('url', '')
        if url and url not in urls_unicas:
            urls_unicas.add(url)
            
            # Identificar APIs relevantes
            if any(keyword in url.lower() for keyword in ['api', 'json', 'data', 'graphql']):
                apis_relevantes.append(pet)
    
    print(f"\n✓ Encontradas {len(apis_relevantes)} llamadas a API potenciales:")
    for i, api in enumerate(apis_relevantes[:10], 1):
        print(f"\n   [{i}] {api.get('method', 'GET')} {api.get('type', '')}")
        print(f"       URL: {api['url'][:120]}")
        if 'status' in api:
            print(f"       Status: {api['status']}")
    
    return apis_relevantes

def inspeccionar_pagina_cine(driver):
    """Intenta navegar a una página de cine específico"""
    print("\n" + "="*80)
    print("INSPECCIÓN DE PÁGINA DE CINE")
    print("="*80)
    
    try:
        # Buscar link a un cine
        print("\nBuscando link a un cine...")
        
        # Intentar varios selectores
        cine_link = None
        selectores = [
            "a[href*='/cines/']",
            "a[href*='/cinemas/']",
            "a[href*='/cartelera']",
        ]
        
        for selector in selectores:
            try:
                links = driver.find_elements(By.CSS_SELECTOR, selector)
                if links:
                    cine_link = links[0]
                    print(f"   ✓ Link encontrado con selector: {selector}")
                    print(f"     URL: {cine_link.get_attribute('href')}")
                    break
            except:
                pass
        
        if cine_link:
            # Hacer clic
            driver.execute_script("arguments[0].click();", cine_link)
            time.sleep(5)
            
            print(f"\n   URL actual: {driver.current_url}")
            
            # Analizar estructura
            analizar_estructura_html(driver)
            
            # Capturar APIs de esta página
            print("\n   Capturando APIs de página de cine...")
            peticiones = capturar_peticiones_red(driver, duracion_segundos=5)
            
            print(f"   ✓ Capturadas {len(peticiones)} peticiones")
            
    except Exception as e:
        print(f"✗ Error navegando a página de cine: {e}")

def inspeccionar_flujo_compra(driver):
    """Intenta navegar por el flujo de compra para identificar estructura"""
    print("\n" + "="*80)
    print("INSPECCIÓN DE FLUJO DE COMPRA")
    print("="*80)
    
    try:
        # Buscar botón de horario
        print("\nBuscando botones de horario...")
        
        selectores_horario = [
            "button[class*='showtime']",
            "button[class*='time']",
            "a[class*='showtime']",
            "a[class*='time']",
        ]
        
        boton_horario = None
        for selector in selectores_horario:
            try:
                botones = driver.find_elements(By.CSS_SELECTOR, selector)
                if botones:
                    boton_horario = botones[0]
                    print(f"   ✓ Botón encontrado: {selector}")
                    break
            except:
                pass
        
        if boton_horario:
            driver.execute_script("arguments[0].click();", boton_horario)
            time.sleep(5)
            
            print(f"\n   URL actual: {driver.current_url}")
            
            # Analizar página de asientos
            print("\n   Analizando página de selección...")
            analizar_estructura_html(driver)
            
    except Exception as e:
        print(f"✗ Error en flujo de compra: {e}")

def main():
    print("="*80)
    print("INSPECTOR DE CINEMARK PERÚ")
    print("="*80)
    print(f"URL: {BASE_URL}")
    print("="*80)
    print()
    
    driver = None
    try:
        driver = configurar_driver()
        
        # 1. Cargar página principal
        print("Cargando página principal...")
        driver.get(BASE_URL)
        time.sleep(5)
        
        print(f"✓ Página cargada: {driver.title}\n")
        
        # 2. Buscar APIs en página principal
        apis_principales = buscar_apis(driver)
        
        # 3. Analizar estructura HTML
        analizar_estructura_html(driver)
        
        # 4. Intentar navegar a página de cine
        # inspeccionar_pagina_cine(driver)
        
        # 5. Guardar resultado
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        archivo_resultado = f"INSPECCION_CINEMARK_{timestamp}.json"
        
        resultado = {
            'url_base': BASE_URL,
            'timestamp': timestamp,
            'apis_encontradas': apis_principales,
            'titulo_pagina': driver.title,
            'url_actual': driver.current_url
        }
        
        with open(archivo_resultado, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*80)
        print("INSPECCIÓN COMPLETADA")
        print("="*80)
        print(f"✓ Resultado guardado en: {archivo_resultado}")
        print("\nPresiona Enter para cerrar el navegador...")
        input()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\nPresiona Enter para cerrar...")
        input()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
