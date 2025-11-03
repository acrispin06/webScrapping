"""
Script de navegación manual MEJORADO para Cinemark - Captura con horarios
Objetivo: Navegar hasta una página que SÍ tenga horarios visibles
Autor: Sistema de análisis Cinemark
Fecha: 2025-10-29
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import time

def configurar_driver():
    """Configura el driver de Chrome con opciones optimizadas"""
    print("🔧 Configurando Chrome WebDriver...")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Habilitar logs de performance para capturar APIs
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print("✅ Chrome configurado exitosamente\n")
    return driver

def esperar_y_verificar(driver, data_testid, descripcion, timeout=10):
    """Espera a que un elemento esté presente y visible"""
    try:
        print(f"⏳ Esperando elemento: {descripcion}...")
        elemento = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='{data_testid}']"))
        )
        print(f"✅ Elemento encontrado: {descripcion}")
        return elemento
    except TimeoutException:
        print(f"⚠️ TIMEOUT: No se encontró {descripcion} en {timeout} segundos")
        return None

def verificar_horarios_presentes(driver):
    """Verifica si hay horarios visibles en la página actual"""
    try:
        # Buscar el contenedor de sesiones
        sessions_container = driver.find_element(By.CSS_SELECTOR, "[data-testid='sessions']")
        
        # Buscar mensaje de "sin sesiones"
        try:
            mensaje_sin_sesiones = driver.find_element(By.CSS_SELECTOR, "p.mui-17h4bc")
            if "no tenemos funciones" in mensaje_sin_sesiones.text.lower():
                print("❌ NO hay horarios disponibles (mensaje detectado)")
                return False
        except:
            pass
        
        # Buscar botones de horario (buscar varios posibles selectores)
        posibles_selectores_horario = [
            "button[class*='showtime']",
            "button[class*='session']",
            "button[class*='schedule']",
            ".mui-* button[type='button']",  # Botones genéricos de Material-UI
        ]
        
        for selector in posibles_selectores_horario:
            try:
                horarios = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(horarios) > 0:
                    print(f"✅ HORARIOS ENCONTRADOS: {len(horarios)} botones con selector '{selector}'")
                    return True
            except:
                continue
        
        print("⚠️ No se detectaron botones de horario claros, pero el contenedor existe")
        return None  # Incierto
    except:
        print("❌ No se encontró el contenedor de sesiones")
        return False

def capturar_apis_desde_logs(driver):
    """Captura las llamadas API desde los logs de performance"""
    print("\n🔍 Analizando logs de red...")
    apis_encontradas = []
    
    try:
        logs = driver.get_log('performance')
        
        palabras_clave = [
            'api', 'cinema', 'movie', 'session', 'showtime', 'schedule',
            'theater', 'film', 'ticket', 'price', 'horario', 'pelicula',
            'cine', 'funcion', 'bff', 'graphql'
        ]
        
        for log in logs:
            try:
                mensaje = json.loads(log['message'])
                metodo = mensaje.get('message', {}).get('method', '')
                
                if 'Network.response' in metodo or 'Network.request' in metodo:
                    params = mensaje.get('message', {}).get('params', {})
                    url = params.get('request', {}).get('url', '') or params.get('response', {}).get('url', '')
                    
                    if url and any(palabra in url.lower() for palabra in palabras_clave):
                        if url not in apis_encontradas:
                            apis_encontradas.append(url)
                            print(f"  📡 API detectada: {url[:80]}...")
            except:
                continue
        
        if not apis_encontradas:
            print("  ⚠️ No se detectaron APIs con palabras clave conocidas")
        else:
            print(f"  ✅ Total APIs capturadas: {len(apis_encontradas)}")
            
    except Exception as e:
        print(f"  ⚠️ Error al leer logs: {e}")
    
    return apis_encontradas

def guardar_resultados(driver, nombre_pelicula, nombre_cine, tiene_horarios):
    """Guarda HTML y resultados del análisis"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Capturar APIs
    apis = capturar_apis_desde_logs(driver)
    
    # Guardar HTML
    html_filename = f"cinemark_CON_HORARIOS_{timestamp}.html"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"\n💾 HTML guardado: {html_filename}")
    
    # Guardar JSON con metadatos
    resultado = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "url_actual": driver.current_url,
        "pelicula": nombre_pelicula,
        "cine": nombre_cine,
        "tiene_horarios": tiene_horarios,
        "apis_capturadas": apis,
        "archivos_generados": [html_filename]
    }
    
    json_filename = f"RESULTADO_HORARIOS_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON guardado: {json_filename}")
    
    return html_filename, json_filename

def main():
    """Función principal con navegación guiada paso a paso"""
    print("="*70)
    print("🎬 NAVEGADOR MANUAL CINEMARK v2.0 - BÚSQUEDA DE HORARIOS")
    print("="*70)
    print("\n📋 OBJETIVO: Capturar HTML de página con horarios VISIBLES")
    print("\n" + "="*70 + "\n")
    
    driver = configurar_driver()
    
    try:
        # PASO 1: Ir a Cinemark
        print("🌐 PASO 1: Accediendo a Cinemark Peru...")
        driver.get("https://www.cinemark-peru.com")
        time.sleep(3)
        
        input("\n⏸️  Presiona ENTER cuando la página haya cargado completamente...")
        
        # PASO 2: Instrucciones para seleccionar película
        print("\n" + "="*70)
        print("📝 PASO 2: SELECCIONAR PELÍCULA CON HORARIOS")
        print("="*70)
        print("\n🎯 PELÍCULAS RECOMENDADAS (prueba en este orden):")
        print("   1. Venom: El Último Baile (Venom 3)")
        print("   2. Terrifier 3")
        print("   3. Robot Salvaje")
        print("   4. Smile 2")
        print("   5. Cualquier película visible en la portada")
        print("\n📌 INSTRUCCIONES:")
        print("   • Click en la película que elijas")
        print("   • O usa el botón 'CARTELERA' del menú")
        print("   • Luego selecciona una película de la lista")
        
        nombre_pelicula = input("\n👉 Escribe el nombre de la película seleccionada: ").strip()
        
        input("\n⏸️  Presiona ENTER después de hacer click en la película...")
        time.sleep(2)
        
        # PASO 3: Verificar si estamos en página de película
        print("\n" + "="*70)
        print("🔍 PASO 3: VERIFICANDO PÁGINA DE PELÍCULA")
        print("="*70)
        
        url_actual = driver.current_url
        print(f"📍 URL actual: {url_actual}")
        
        if "/pelicula/" not in url_actual:
            print("⚠️ ADVERTENCIA: No parece ser una página de película")
            continuar = input("¿Deseas continuar de todas formas? (s/n): ")
            if continuar.lower() != 's':
                print("❌ Proceso cancelado")
                return
        
        # PASO 4: Seleccionar cine
        print("\n" + "="*70)
        print("🏢 PASO 4: SELECCIONAR CINE")
        print("="*70)
        print("\n📌 INSTRUCCIONES:")
        print("   • Busca el botón con el nombre del cine (ej: 'Cinemark Asia')")
        print("   • Haz click en el dropdown y selecciona OTRO CINE")
        print("   • RECOMENDACIÓN: Prueba con 'Cinemark San Miguel' o 'Cinemark Plaza Lima Sur'")
        print("   • Si no aparecen horarios, intenta con otro cine")
        
        nombre_cine = input("\n👉 Escribe el nombre del cine seleccionado: ").strip()
        
        input("\n⏸️  Presiona ENTER después de seleccionar el cine...")
        time.sleep(3)  # Esperar a que carguen los horarios
        
        # PASO 5: Verificar presencia de horarios
        print("\n" + "="*70)
        print("🎯 PASO 5: VERIFICANDO PRESENCIA DE HORARIOS")
        print("="*70)
        
        tiene_horarios = verificar_horarios_presentes(driver)
        
        if tiene_horarios == False:
            print("\n❌ NO SE DETECTARON HORARIOS")
            print("\n💡 OPCIONES:")
            print("   1. Cambia de cine usando el dropdown")
            print("   2. Cambia los filtros de fecha/formato")
            print("   3. Prueba con otra película")
            
            reintentar = input("\n¿Deseas cambiar de cine/filtros y reintentar? (s/n): ")
            if reintentar.lower() == 's':
                print("\n🔄 Realiza los cambios necesarios...")
                input("⏸️  Presiona ENTER cuando veas horarios en pantalla...")
                tiene_horarios = verificar_horarios_presentes(driver)
        
        # PASO 6: Captura final
        print("\n" + "="*70)
        print("📸 PASO 6: CAPTURA FINAL")
        print("="*70)
        
        if tiene_horarios != False:
            print("\n✅ ¡Excelente! Vamos a capturar esta página")
        else:
            print("\n⚠️ Capturaremos de todas formas para análisis posterior")
        
        # Scroll para asegurar que todo esté cargado
        print("\n🔄 Haciendo scroll para cargar todo el contenido...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Guardar todo
        html_file, json_file = guardar_resultados(driver, nombre_pelicula, nombre_cine, tiene_horarios)
        
        # RESUMEN FINAL
        print("\n" + "="*70)
        print("✅ CAPTURA COMPLETADA")
        print("="*70)
        print(f"\n📊 RESUMEN:")
        print(f"   • Película: {nombre_pelicula}")
        print(f"   • Cine: {nombre_cine}")
        print(f"   • ¿Tiene horarios?: {'✅ SÍ' if tiene_horarios else '❌ NO' if tiene_horarios == False else '⚠️ INCIERTO'}")
        print(f"   • URL: {driver.current_url}")
        print(f"\n📁 Archivos generados:")
        print(f"   • {html_file}")
        print(f"   • {json_file}")
        
        if tiene_horarios:
            print("\n🎉 ¡PERFECTO! Este HTML contiene horarios para analizar")
        else:
            print("\n💡 SIGUIENTE PASO: Ejecuta el script de nuevo con otra película/cine")
        
        input("\n\n⏸️  Presiona ENTER para cerrar el navegador...")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona ENTER para cerrar...")
    
    finally:
        print("\n🔒 Cerrando navegador...")
        driver.quit()
        print("✅ Navegador cerrado")

if __name__ == "__main__":
    main()
