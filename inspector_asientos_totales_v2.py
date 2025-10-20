"""
EXTRACTOR DE CAPACIDADES DE CINEPLANET - VERSIÓN OPTIMIZADA
============================================================

Estrategia de 2 fases:
1. FASE RECOLECCIÓN: Recopilar TODA la información en memoria (cines → películas → horarios)
2. FASE EXTRACCIÓN: Visitar cada horario para contar asientos

Esto garantiza:
- Procesar TODOS los 43 cines
- No perder datos por elementos stale
- Mayor eficiencia (menos navegaciones)
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from datetime import datetime
import json

BASE_URL = 'https://www.cineplanet.com.pe'
TIMEOUT = 20
HEADLESS = False  # True = modo sin ventana (esencial para ejecución paralela)
LISTA_CINES_FILE = 'lista_cines_faltantes.txt'  # Archivo TXT con lista de cines

# CONFIGURACIÓN
MAX_CINES = None      # None = TODOS (43)
MAX_PELICULAS = None  # None = TODAS
MAX_FUNCIONES = None  # None = TODAS

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
        print("✅ Chrome configurado\n")
        return driver
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️  Asegúrate de tener Chrome instalado")
        raise

def manejar_popups(driver):
    """Cierra popups y overlays"""
    try:
        driver.execute_script("""
            document.querySelectorAll('[class*="cookie"], [class*="consent"], [class*="popup"], [class*="overlay"]').forEach(el => el.remove());
        """)
        time.sleep(1)
    except:
        pass

# ============================================================================
# FASE 1: RECOLECCIÓN DE DATOS EN MEMORIA
# ============================================================================

def cargar_lista_cines_desde_txt():
    """
    Carga la lista de cines desde el archivo TXT
    Retorna: ['CP Alcazar', 'CP Brasil', ..., 'CP Villa María del Triunfo']
    """
    try:
        with open(LISTA_CINES_FILE, 'r', encoding='utf-8') as f:
            # Leer líneas, quitar espacios en blanco y filtrar líneas vacías
            cines = [linea.strip() for linea in f.readlines() if linea.strip()]
        return cines
    except FileNotFoundError:
        print(f"✗ ERROR: No se encontró el archivo '{LISTA_CINES_FILE}'")
        print(f"   Por favor, crea el archivo con la lista de cines (un cine por línea)")
        return []
    except Exception as e:
        print(f"✗ ERROR leyendo archivo: {e}")
        return []

def recolectar_lista_cines(driver):
    """
    PASO 1.1: Cargar lista de cines desde archivo TXT
    Ya no intenta cargar desde la página porque el sitio detecta Selenium
    Retorna: ['CP Alcazar', 'CP Brasil', ..., 'CP Villa María del Triunfo']
    """
    print("=" * 80)
    print("FASE 1.1: CARGANDO LISTA DE CINES DESDE ARCHIVO TXT")
    print("=" * 80)
    
    # Cargar lista desde archivo TXT
    cines = cargar_lista_cines_desde_txt()
    
    if not cines:
        print("✗ No se pudo cargar la lista de cines")
        return []
    
    print(f"\n✓ Total cines cargados desde '{LISTA_CINES_FILE}': {len(cines)}")
    
    # Mostrar nombres normalizados (slugs)
    print(f"\n📋 Lista de cines con slugs normalizados:")
    for i, nombre in enumerate(cines, 1):
        slug = normalizar_slug(nombre)
        url_completa = f"{BASE_URL}/cinemas/{slug}"
        print(f"   {i:2d}. {nombre:45s} → {slug:40s}")
        print(f"       {url_completa}")
    print("")
    
    # Aplicar límite si existe
    if MAX_CINES and len(cines) > MAX_CINES:
        cines = cines[:MAX_CINES]
        print(f"   (Limitado a {MAX_CINES} por configuración)")
    
    print(f"   Primeros: {', '.join(cines[:3])}")
    print(f"   Últimos: {', '.join(cines[-3:])}")
    
    return cines

def normalizar_slug(nombre):
    """
    Normaliza nombre de cine a slug para URL
    'CP Centro Jr. De La Unión' → 'cp-centro-jr-de-la-union'
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

def recolectar_peliculas_y_horarios_de_cine(driver, cine_nombre):
    """
    PASO 1.2: Recolectar películas y horarios de UN cine
    
    Retorna diccionario:
    {
        'cine': 'CP Alcazar',
        'cine_slug': 'cp-alcazar',
        'peliculas': [
            {
                'nombre': 'El Corazón del Lobo',
                'horarios': ['10:30', '14:00', '18:45', '22:30']
            },
            ...
        ]
    }
    """
    print(f"\n→ Recolectando: {cine_nombre}")
    
    cine_slug = normalizar_slug(cine_nombre)
    url_cine = f"{BASE_URL}/cinemas/{cine_slug}"
    
    resultado = {
        'cine': cine_nombre,
        'cine_slug': cine_slug,
        'url': url_cine,
        'peliculas': []
    }
    
    try:
        driver.get(url_cine)
        time.sleep(4)
        manejar_popups(driver)
        
        # Scroll para cargar películas
        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        
        # Buscar películas
        peliculas_elementos = driver.find_elements(By.CSS_SELECTOR, "div.movies-list-schedules--large-item")
        
        if not peliculas_elementos:
            print(f"   ⚠️ NO HAY PELÍCULAS")
            return resultado
        
        print(f"   Películas encontradas: {len(peliculas_elementos)}")
        
        # Aplicar límite si existe
        total_a_procesar = min(len(peliculas_elementos), MAX_PELICULAS) if MAX_PELICULAS else len(peliculas_elementos)
        
        # Recolectar cada película
        for idx in range(total_a_procesar):
            try:
                # Re-obtener elementos (evitar stale)
                peliculas_refresh = driver.find_elements(By.CSS_SELECTOR, "div.movies-list-schedules--large-item")
                if idx >= len(peliculas_refresh):
                    break
                
                pelicula_elem = peliculas_refresh[idx]
                
                # Extraer nombre
                try:
                    nombre_elem = pelicula_elem.find_element(By.CSS_SELECTOR, "h2.movies-list-schedules--large-movie-description-title")
                    nombre_pelicula = nombre_elem.text.strip()
                except:
                    nombre_pelicula = f"Película_{idx+1}"
                
                # Extraer horarios
                horarios_elementos = pelicula_elem.find_elements(By.CSS_SELECTOR, "button.showtime-selector--link")
                horarios = []
                
                total_horarios = min(len(horarios_elementos), MAX_FUNCIONES) if MAX_FUNCIONES else len(horarios_elementos)
                
                for horario_elem in horarios_elementos[:total_horarios]:
                    try:
                        horario_texto = horario_elem.text.strip()
                        if horario_texto:
                            horarios.append(horario_texto)
                    except:
                        pass
                
                if horarios:
                    resultado['peliculas'].append({
                        'nombre': nombre_pelicula,
                        'horarios': horarios
                    })
                    print(f"   ✓ {nombre_pelicula}: {len(horarios)} horarios")
                
            except Exception as e:
                print(f"   ⚠️ Error en película {idx+1}: {e}")
                continue
        
        print(f"   Total películas recolectadas: {len(resultado['peliculas'])}")
        
    except Exception as e:
        print(f"   ✗ Error en cine: {e}")
    
    return resultado

def recolectar_todo(driver):
    """
    PASO 1: Recolectar TODA la información en memoria
    
    Retorna estructura completa:
    [
        {
            'cine': 'CP Alcazar',
            'cine_slug': 'cp-alcazar',
            'url': 'https://...',
            'peliculas': [
                {'nombre': 'Movie 1', 'horarios': ['10:30', '14:00']},
                {'nombre': 'Movie 2', 'horarios': ['18:45']}
            ]
        },
        ...
    ]
    """
    print("\n" + "=" * 80)
    print("INICIANDO FASE 1: RECOLECCIÓN COMPLETA DE DATOS")
    print("=" * 80)
    
    # Paso 1.1: Obtener lista de cines
    lista_cines = recolectar_lista_cines(driver)
    
    if not lista_cines:
        print("\n✗ No se pudieron recolectar cines")
        return []
    
    # Paso 1.2: Para cada cine, recolectar películas y horarios
    print("\n" + "=" * 80)
    print("FASE 1.2: RECOLECTANDO PELÍCULAS Y HORARIOS POR CINE")
    print("=" * 80)
    
    datos_completos = []
    
    for i, cine_nombre in enumerate(lista_cines, 1):
        print(f"\n[{i}/{len(lista_cines)}]", end=" ")
        
        datos_cine = recolectar_peliculas_y_horarios_de_cine(driver, cine_nombre)
        datos_completos.append(datos_cine)
        
        time.sleep(1)  # Pausa entre cines

    
    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE RECOLECCIÓN")
    print("=" * 80)
    
    total_cines = len(datos_completos)
    cines_con_peliculas = len([c for c in datos_completos if c['peliculas']])
    cines_sin_peliculas = total_cines - cines_con_peliculas
    total_peliculas = sum(len(c['peliculas']) for c in datos_completos)
    total_horarios = sum(
        len(p['horarios']) 
        for c in datos_completos 
        for p in c['peliculas']
    )
    
    print(f"\n✓ Cines totales:        {total_cines}")
    print(f"✓ Cines con películas:  {cines_con_peliculas}")
    print(f"⚠️ Cines sin películas: {cines_sin_peliculas}")
    print(f"✓ Total películas:      {total_peliculas}")
    print(f"✓ Total horarios:       {total_horarios}")
    
    # Guardar en JSON para respaldo
    with open('datos_recolectados.json', 'w', encoding='utf-8') as f:
        json.dump(datos_completos, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Datos guardados en: datos_recolectados.json")
    
    return datos_completos

# ============================================================================
# FASE 2: EXTRACCIÓN DE CAPACIDADES
# ============================================================================

def extraer_capacidad_de_horario(driver, cine_nombre, pelicula_nombre, horario, cine_slug):
    """
    PASO 2: Visitar un horario específico y contar asientos
    """
    try:
        # Ir a la página del cine
        url_cine = f"{BASE_URL}/cinemas/{cine_slug}"
        driver.get(url_cine)
        time.sleep(3)
        manejar_popups(driver)
        
        # Scroll para cargar películas
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        
        # Buscar película
        peliculas = driver.find_elements(By.CSS_SELECTOR, "div.movies-list-schedules--large-item")
        
        for pelicula_elem in peliculas:
            try:
                # Verificar si es la película correcta
                nombre_elem = pelicula_elem.find_element(By.CSS_SELECTOR, "h2.movies-list-schedules--large-movie-description-title")
                if nombre_elem.text.strip() != pelicula_nombre:
                    continue
                
                # Buscar el horario específico
                horarios_botones = pelicula_elem.find_elements(By.CSS_SELECTOR, "button.showtime-selector--link")
                
                for boton in horarios_botones:
                    if boton.text.strip() == horario:
                        # ¡Encontrado! Hacer clic
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", boton)
                        time.sleep(3)

                        
                        # Verificar que estamos en página de asientos
                        if '/asientos' in driver.current_url:
                            asientos = driver.find_elements(By.CSS_SELECTOR, ".seat-map--seat")
                            return len(asientos)
                        else:
                            return None
                
            except Exception as e:
                continue
        
        return None
        
    except Exception as e:
        return None

def extraer_capacidades(driver, datos_recolectados):
    """
    FASE 2: Extraer capacidades visitando cada horario
    """
    print("\n" + "=" * 80)
    print("INICIANDO FASE 2: EXTRACCIÓN DE CAPACIDADES")
    print("=" * 80)
    
    resultados = []
    total_horarios = sum(
        len(p['horarios']) 
        for c in datos_recolectados 
        for p in c['peliculas']
    )
    
    contador = 0
    
    for cine_data in datos_recolectados:
        cine_nombre = cine_data['cine']
        cine_slug = cine_data['cine_slug']
        
        if not cine_data['peliculas']:
            continue
        
        print(f"\n→ Procesando: {cine_nombre}")
        
        for pelicula in cine_data['peliculas']:
            pelicula_nombre = pelicula['nombre']
            
            for horario in pelicula['horarios']:
                contador += 1
                print(f"   [{contador}/{total_horarios}] {pelicula_nombre} - {horario}", end=" ")
                
                asientos = extraer_capacidad_de_horario(
                    driver, 
                    cine_nombre, 
                    pelicula_nombre, 
                    horario,
                    cine_slug
                )
                
                if asientos is not None:
                    resultados.append({
                        'cine': cine_nombre,
                        'pelicula': pelicula_nombre,
                        'funcion': horario,
                        'asientos': asientos
                    })
                    print(f"→ {asientos} asientos")
                else:
                    print("→ ✗ No se pudo extraer")
                
                time.sleep(0.5)

        
        # Guardar progreso incremental
        df = pd.DataFrame(resultados)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df.to_csv(f'capacidades_cineplanet_EN_PROGRESO.csv', index=False, encoding='utf-8-sig')
        print(f"   💾 Progreso guardado: {len(resultados)} registros")
    
    return resultados

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("EXTRACTOR DE CAPACIDADES CINEPLANET - VERSIÓN OPTIMIZADA")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {'HEADLESS' if HEADLESS else 'CON VENTANA'}")
    print(f"Límites: Cines={MAX_CINES or 'TODOS'}, Películas={MAX_PELICULAS or 'TODAS'}, Funciones={MAX_FUNCIONES or 'TODAS'}")
    print("=" * 80)
    
    driver = configurar_driver()
    
    try:
        # FASE 1: Recolectar toda la información
        datos_recolectados = recolectar_todo(driver)
        
        if not datos_recolectados:
            print("\n✗ No hay datos para procesar")
            return
        
        # FASE 2: Extraer capacidades
        resultados = extraer_capacidades(driver, datos_recolectados)
        
        # Guardar resultado final
        if resultados:
            df = pd.DataFrame(resultados)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_final = f'capacidades_cineplanet_COMPLETO_{timestamp}.csv'
            df.to_csv(archivo_final, index=False, encoding='utf-8-sig')
            
            print("\n" + "=" * 80)
            print("EXTRACCIÓN COMPLETADA")
            print("=" * 80)
            print(f"✓ Total registros:     {len(resultados)}")
            print(f"✓ Cines procesados:    {df['cine'].nunique()}")
            print(f"✓ Películas únicas:    {df['pelicula'].nunique()}")
            print(f"✓ Capacidades únicas:  {df['asientos'].nunique()}")
            print(f"✓ Archivo guardado:    {archivo_final}")
            print("=" * 80)
        else:
            print("\n⚠️ No se extrajeron capacidades")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Extracción interrumpida por el usuario")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n→ Cerrando navegador...")
        driver.quit()
        print("✓ Proceso finalizado")

if __name__ == "__main__":
    main()
