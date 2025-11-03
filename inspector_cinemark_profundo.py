"""
ANÁLISIS PROFUNDO DE CINEMARK PERÚ
Detecta APIs y estructura de datos
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re

BASE_URL = 'https://www.cinemark-peru.com'

def configurar_driver_con_network():
    """Configura Chrome para capturar peticiones de red"""
    print("Configurando Chrome con captura de red...")
    options = Options()
    options.add_argument('--start-maximized')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def extraer_apis_de_logs(driver):
    """Extrae llamadas API de los logs de performance"""
    print("\nExtrayendo APIs de los logs...")
    logs = driver.get_log('performance')
    
    apis = []
    for entry in logs:
        try:
            log = json.loads(entry['message'])
            message = log.get('message', {})
            method = message.get('method', '')
            
            if method == 'Network.responseReceived':
                params = message.get('params', {})
                response = params.get('response', {})
                url = response.get('url', '')
                
                # Filtrar APIs relevantes
                if any(keyword in url.lower() for keyword in [
                    'api', 'cinema', 'movie', 'pelicula', 'cine', 
                    'theater', 'price', 'precio', 'show', 'function'
                ]):
                    apis.append({
                        'url': url,
                        'status': response.get('status'),
                        'mimeType': response.get('mimeType', '')
                    })
        except:
            pass
    
    # Eliminar duplicados
    apis_unicas = []
    urls_vistas = set()
    for api in apis:
        if api['url'] not in urls_vistas:
            urls_vistas.add(api['url'])
            apis_unicas.append(api)
    
    return apis_unicas

def analizar_con_interaccion(driver):
    """Analiza la página interactuando con elementos"""
    print("\n" + "="*80)
    print("ANÁLISIS CON INTERACCIÓN")
    print("="*80)
    
    # 1. Cargar página principal
    print("\n1. CARGANDO PÁGINA PRINCIPAL...")
    driver.get(BASE_URL)
    time.sleep(5)
    print(f"   ✓ Cargada: {driver.title}")
    
    apis_1 = extraer_apis_de_logs(driver)
    print(f"   ✓ APIs detectadas: {len(apis_1)}")
    
    # 2. Hacer clic en "ELEGIR CINE"
    print("\n2. HACIENDO CLIC EN 'ELEGIR CINE'...")
    try:
        boton_elegir_cine = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ELEGIR CINE')]"))
        )
        driver.execute_script("arguments[0].click();", boton_elegir_cine)
        time.sleep(3)
        print("   ✓ Clic realizado")
        
        # Ver si apareció un menú
        try:
            opciones_cine = driver.find_elements(By.CSS_SELECTOR, "[role='menuitem'], .MuiMenuItem-root, li")
            if opciones_cine:
                print(f"   ✓ Encontradas {len(opciones_cine)} opciones de cine")
                for i, opcion in enumerate(opciones_cine[:10]):
                    texto = opcion.text.strip()
                    if texto and len(texto) > 2:
                        print(f"      [{i+1}] {texto}")
                
                # Seleccionar el primer cine
                if opciones_cine:
                    print("\n   → Seleccionando primer cine...")
                    driver.execute_script("arguments[0].click();", opciones_cine[0])
                    time.sleep(3)
                    
                    apis_2 = extraer_apis_de_logs(driver)
                    print(f"   ✓ APIs después de seleccionar cine: {len(apis_2)}")
        except Exception as e:
            print(f"   ✗ No se encontró menú de cines: {e}")
    except Exception as e:
        print(f"   ✗ No se pudo hacer clic: {e}")
    
    # 3. Hacer clic en "CARTELERA"
    print("\n3. NAVEGANDO A CARTELERA...")
    try:
        boton_cartelera = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CARTELERA')]"))
        )
        driver.execute_script("arguments[0].click();", boton_cartelera)
        time.sleep(5)
        print(f"   ✓ URL actual: {driver.current_url}")
        
        apis_3 = extraer_apis_de_logs(driver)
        print(f"   ✓ APIs en cartelera: {len(apis_3)}")
        
        # Buscar películas
        peliculas = driver.find_elements(By.CSS_SELECTOR, "div[class*='card'], div[class*='movie'], div[class*='pelicula']")
        print(f"   ✓ Películas encontradas: {len(peliculas)}")
        
        if peliculas:
            # Hacer clic en primera película
            print("\n   → Haciendo clic en primera película...")
            try:
                # Buscar link dentro de la primera película
                primer_link = peliculas[0].find_element(By.CSS_SELECTOR, "a")
                url_pelicula = primer_link.get_attribute('href')
                print(f"      URL: {url_pelicula}")
                
                driver.get(url_pelicula)
                time.sleep(5)
                print(f"   ✓ Página de película cargada")
                
                apis_4 = extraer_apis_de_logs(driver)
                print(f"   ✓ APIs en página de película: {len(apis_4)}")
                
                # Guardar HTML de página de película
                with open('cinemark_pelicula.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("   ✓ HTML guardado en: cinemark_pelicula.html")
                
                # Buscar botones de horario
                botones_horario = driver.find_elements(By.CSS_SELECTOR, "button, a[class*='btn'], div[class*='time'], div[class*='hora']")
                print(f"\n   BOTONES/ELEMENTOS DE HORARIO:")
                for i, boton in enumerate(botones_horario[:10]):
                    texto = boton.text.strip()
                    if texto:
                        print(f"      [{i+1}] {texto[:60]}")
                
            except Exception as e:
                print(f"   ✗ Error navegando a película: {e}")
        
    except Exception as e:
        print(f"   ✗ Error en cartelera: {e}")
    
    # 4. Recopilar todas las APIs únicas
    print("\n" + "="*80)
    print("RESUMEN DE APIs DETECTADAS")
    print("="*80)
    
    todas_apis = extraer_apis_de_logs(driver)
    
    # Filtrar y categorizar
    apis_json = [api for api in todas_apis if 'json' in api.get('mimeType', '').lower()]
    apis_api = [api for api in todas_apis if '/api/' in api['url'].lower()]
    
    print(f"\n✓ Total APIs detectadas: {len(todas_apis)}")
    print(f"✓ APIs JSON: {len(apis_json)}")
    print(f"✓ APIs con /api/ en URL: {len(apis_api)}")
    
    print("\n--- APIs RELEVANTES ---")
    for i, api in enumerate(todas_apis[:20], 1):
        print(f"\n[{i}] Status: {api.get('status')}")
        print(f"    MIME: {api.get('mimeType')}")
        print(f"    URL: {api['url'][:120]}")
    
    return todas_apis

def buscar_datos_en_script_tags(driver):
    """Busca datos JSON embebidos en script tags"""
    print("\n" + "="*80)
    print("BUSCANDO DATOS EN <SCRIPT> TAGS")
    print("="*80)
    
    try:
        scripts = driver.find_elements(By.TAG_NAME, 'script')
        print(f"✓ Encontrados {len(scripts)} script tags")
        
        for i, script in enumerate(scripts):
            contenido = script.get_attribute('innerHTML')
            if contenido:
                # Buscar datos JSON embebidos
                if any(keyword in contenido.lower() for keyword in ['cinema', 'movie', 'theater', 'cine', 'pelicula']):
                    print(f"\n[Script #{i+1}] Contiene datos relevantes ({len(contenido)} chars)")
                    
                    # Intentar extraer JSON
                    try:
                        # Buscar patrones tipo: window.__DATA__ = {...}
                        matches = re.findall(r'window\.__\w+__\s*=\s*(\{.+?\});', contenido, re.DOTALL)
                        if matches:
                            print(f"   ✓ Encontrado JSON embebido")
                            for j, match in enumerate(matches[:2]):
                                try:
                                    data = json.loads(match)
                                    print(f"   ✓ JSON #{j+1} parseado exitosamente")
                                    print(f"      Keys: {list(data.keys())[:5]}")
                                except:
                                    pass
                    except:
                        pass
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    print("="*80)
    print("ANÁLISIS PROFUNDO DE CINEMARK PERÚ")
    print("="*80)
    print(f"URL: {BASE_URL}")
    print("="*80)
    print()
    
    driver = None
    try:
        driver = configurar_driver_con_network()
        
        # Análisis con interacción
        apis_detectadas = analizar_con_interaccion(driver)
        
        # Buscar datos embebidos
        buscar_datos_en_script_tags(driver)
        
        # Guardar resultado
        resultado = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'apis_detectadas': apis_detectadas,
            'total_apis': len(apis_detectadas)
        }
        
        with open('ANALISIS_CINEMARK_APIS.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*80)
        print("ANÁLISIS COMPLETADO")
        print("="*80)
        print("✓ Resultado guardado en: ANALISIS_CINEMARK_APIS.json")
        print("✓ HTMLs guardados para inspección manual")
        print("\nPresiona Enter para cerrar...")
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
