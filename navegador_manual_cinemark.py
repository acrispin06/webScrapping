"""
NAVEGADOR MANUAL DE CINEMARK
Script interactivo para navegar y capturar el flujo completo
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

BASE_URL = 'https://www.cinemark-peru.com'

def configurar_driver():
    print("Configurando Chrome...")
    options = Options()
    options.add_argument('--start-maximized')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def extraer_apis_relevantes(driver):
    """Extrae APIs con datos útiles"""
    logs = driver.get_log('performance')
    apis = []
    
    for entry in logs:
        try:
            log = json.loads(entry['message'])
            message = log.get('message', {})
            
            if message.get('method') == 'Network.responseReceived':
                params = message.get('params', {})
                response = params.get('response', {})
                url = response.get('url', '')
                mime = response.get('mimeType', '')
                
                # Filtrar URLs útiles
                if any(k in url.lower() for k in ['api', 'bff', 'data']) or 'json' in mime.lower():
                    apis.append({
                        'url': url,
                        'status': response.get('status'),
                        'mime': mime
                    })
        except:
            pass
    
    return apis

def main():
    print("="*80)
    print("NAVEGADOR MANUAL DE CINEMARK")
    print("="*80)
    print("\nEste script te guiará paso a paso por el flujo de Cinemark")
    print("y capturará las APIs utilizadas en cada paso.\n")
    print("="*80)
    
    driver = None
    try:
        driver = configurar_driver()
        
        # PASO 1: Cargar página principal
        print("\n[PASO 1] Cargando página principal...")
        driver.get(BASE_URL)
        time.sleep(5)
        print(f"✓ Cargada: {driver.title}")
        
        input("\n▶ Presiona Enter para capturar APIs de página principal...")
        apis_inicio = extraer_apis_relevantes(driver)
        print(f"✓ Capturadas {len(apis_inicio)} APIs")
        
        # PASO 2: Navegar a cartelera
        print("\n[PASO 2] Intentando navegar a cartelera...")
        print("Opciones:")
        print("  1. Hacer clic en botón CARTELERA")
        print("  2. Ir directamente a /cartelera")
        print("  3. Buscar link de cine específico")
        
        opcion = input("\n¿Qué prefieres? (1/2/3): ").strip()
        
        if opcion == "2":
            driver.get(f"{BASE_URL}/cartelera")
            time.sleep(5)
            print(f"✓ URL actual: {driver.current_url}")
        elif opcion == "3":
            print("\nBuscando links de cines...")
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='cinema'], a[href*='cine']")
            print(f"✓ Encontrados {len(links)} links")
            if links:
                for i, link in enumerate(links[:10]):
                    href = link.get_attribute('href')
                    texto = link.text.strip()[:50]
                    print(f"  [{i+1}] {texto:50s} → {href}")
                
                idx = input("\n¿Cuál quieres visitar? (número): ").strip()
                try:
                    driver.get(links[int(idx)-1].get_attribute('href'))
                    time.sleep(5)
                    print(f"✓ Navegado a: {driver.current_url}")
                except:
                    print("✗ Opción inválida")
        
        input("\n▶ Presiona Enter para capturar APIs...")
        apis_cartelera = extraer_apis_relevantes(driver)
        print(f"✓ Capturadas {len(apis_cartelera)} APIs")
        
        # PASO 3: Buscar películas
        print("\n[PASO 3] Buscando películas en la página...")
        
        selectores = [
            ("div[class*='card']", "Tarjetas"),
            ("div[class*='movie']", "Contenedores de película"),
            ("a[href*='pelicula']", "Links a películas"),
            ("h2, h3", "Títulos")
        ]
        
        for selector, desc in selectores:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            if elementos:
                print(f"\n✓ {desc}: {len(elementos)} elementos encontrados")
                for i, elem in enumerate(elementos[:5]):
                    try:
                        texto = elem.text.strip()[:60]
                        if texto:
                            print(f"   [{i+1}] {texto}")
                    except:
                        pass
        
        # PASO 4: Seleccionar película
        print("\n[PASO 4] Seleccionar una película")
        print("Opciones:")
        print("  1. Buscar automáticamente primer link de película")
        print("  2. Introducir URL manualmente")
        
        opcion = input("\n¿Qué prefieres? (1/2): ").strip()
        
        url_pelicula = None
        if opcion == "1":
            links_pelicula = driver.find_elements(By.CSS_SELECTOR, "a[href*='/pelicula/']")
            if links_pelicula:
                url_pelicula = links_pelicula[0].get_attribute('href')
                print(f"✓ Encontrada: {url_pelicula}")
        else:
            url_pelicula = input("Introduce URL de película: ").strip()
        
        if url_pelicula:
            driver.get(url_pelicula)
            time.sleep(5)
            print(f"✓ URL actual: {driver.current_url}")
            
            # Guardar HTML de película
            with open('cinemark_pelicula_NAVEGACION.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("✓ HTML guardado en: cinemark_pelicula_NAVEGACION.html")
            
            input("\n▶ Presiona Enter para capturar APIs...")
            apis_pelicula = extraer_apis_relevantes(driver)
            print(f"✓ Capturadas {len(apis_pelicula)} APIs")
        
        # PASO 5: Buscar horarios
        print("\n[PASO 5] Buscando horarios/botones...")
        
        botones = driver.find_elements(By.CSS_SELECTOR, "button, a[class*='btn']")
        print(f"✓ Encontrados {len(botones)} botones")
        
        for i, boton in enumerate(botones[:15]):
            try:
                texto = boton.text.strip()
                if texto and len(texto) < 50:
                    clase = boton.get_attribute('class')[:50]
                    print(f"   [{i+1}] {texto:30s} | {clase}")
            except:
                pass
        
        # PASO 6: Recopilar todas las APIs
        print("\n" + "="*80)
        print("RESUMEN DE APIs CAPTURADAS")
        print("="*80)
        
        todas_apis = extraer_apis_relevantes(driver)
        
        # Eliminar duplicados
        urls_unicas = {}
        for api in todas_apis:
            url_base = api['url'].split('?')[0]  # Sin parámetros
            if url_base not in urls_unicas:
                urls_unicas[url_base] = api
        
        print(f"\n✓ Total APIs únicas: {len(urls_unicas)}")
        
        print("\n--- APIs RELEVANTES ---")
        for i, (url, api) in enumerate(list(urls_unicas.items())[:30], 1):
            print(f"\n[{i}] {url}")
            print(f"    Status: {api['status']} | MIME: {api.get('mime', 'N/A')[:30]}")
        
        # Guardar resultado
        resultado = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'url_actual': driver.current_url,
            'apis_capturadas': list(urls_unicas.values())
        }
        
        with open('NAVEGACION_MANUAL_RESULTADO.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*80)
        print("ANÁLISIS COMPLETADO")
        print("="*80)
        print("✓ Resultado guardado en: NAVEGACION_MANUAL_RESULTADO.json")
        print("✓ HTML guardado para análisis offline")
        
        print("\n▶ El navegador permanecerá abierto para inspección manual")
        print("  Puedes usar DevTools para explorar más")
        print("\nPresiona Enter cuando termines...")
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
