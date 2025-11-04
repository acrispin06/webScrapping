"""
Script de prueba para verificar selectores de Cinemark Peru
Ejecuta pasos individuales y muestra resultados en consola
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

BASE_URL = 'https://www.cinemark-peru.com'

def configurar_driver():
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument('--log-level=3')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def test_cargar_peliculas(driver):
    """Test 1: Cargar página de películas y detectarlas"""
    print("\n" + "="*80)
    print("TEST 1: Cargar lista de películas")
    print("="*80)
    
    url = f"{BASE_URL}/elegir-pelicula"
    driver.get(url)
    time.sleep(5)
    
    # Scroll para cargar todo
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    # Intentar varios selectores
    selectores = [
        ("a[href*='/pelicula/']", "Links con /pelicula/"),
        ("div[class*='movie']", "Divs con 'movie'"),
        ("div[class*='card']", "Divs con 'card'"),
    ]
    
    for selector, descripcion in selectores:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"✓ {descripcion}: {len(elementos)} elementos")
            
            if elementos and selector == "a[href*='/pelicula/']":
                print("\n  Primeras 5 películas detectadas:")
                for i, elem in enumerate(elementos[:5], 1):
                    href = elem.get_attribute('href')
                    slug = href.split('/pelicula/')[-1] if '/pelicula/' in href else '?'
                    print(f"    {i}. {slug}")
        except Exception as e:
            print(f"✗ {descripcion}: Error - {str(e)[:50]}")
    
    input("\nPresiona ENTER para continuar al siguiente test...")

def test_pagina_pelicula(driver):
    """Test 2: Navegar a página de película y detectar sidebar"""
    print("\n" + "="*80)
    print("TEST 2: Página de película y sidebar de cines")
    print("="*80)
    
    # Usar una película conocida
    url = f"{BASE_URL}/pelicula/venom-el-ultimo-baile"
    print(f"Navegando a: {url}")
    driver.get(url)
    time.sleep(5)
    
    # Verificar si el sidebar está visible
    try:
        sidebar = driver.find_element(By.CSS_SELECTOR, "div[class*='MuiBox']")
        print("✓ Sidebar detectado")
    except:
        print("✗ Sidebar no detectado")
    
    # Buscar cines en el sidebar
    selectores_cines = [
        ("label[data-testid='teather-item']", "Labels con data-testid"),
        ("p[class*='MuiTypography'][class*='mui-mbobke']", "Textos de cines"),
    ]
    
    for selector, descripcion in selectores_cines:
        try:
            cines = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"✓ {descripcion}: {len(cines)} cines detectados")
            
            if cines:
                print("\n  Primeros 5 cines:")
                for i, cine in enumerate(cines[:5], 1):
                    texto = cine.text.strip().split('\n')[0]  # Primera línea
                    print(f"    {i}. {texto}")
        except Exception as e:
            print(f"✗ {descripcion}: Error - {str(e)[:50]}")
    
    input("\nPresiona ENTER para continuar al siguiente test...")

def test_seleccionar_cine(driver):
    """Test 3: Seleccionar un cine y ver horarios"""
    print("\n" + "="*80)
    print("TEST 3: Seleccionar cine y detectar horarios")
    print("="*80)
    
    # Buscar el primer cine disponible
    try:
        cine = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "label[data-testid='teather-item']"))
        )
        nombre_cine = cine.text.split('\n')[0]
        print(f"Cine seleccionado: {nombre_cine}")
        
        # Click en el checkbox
        driver.execute_script("arguments[0].click();", cine)
        time.sleep(2)
        
        # Click en Aplicar
        boton_aplicar = driver.find_element(By.CSS_SELECTOR, "button[data-testid='teather-appply-button']")
        driver.execute_script("arguments[0].click();", boton_aplicar)
        time.sleep(3)
        
        print("✓ Cine seleccionado exitosamente")
        
    except Exception as e:
        print(f"✗ Error seleccionando cine: {str(e)[:100]}")
        input("\nPresiona ENTER para continuar...")
        return
    
    # Buscar botones de horario
    selectores_horarios = [
        ("button[class*='showtime']", "Botones con 'showtime'"),
        ("button[class*='schedule']", "Botones con 'schedule'"),
        ("button[class*='time']", "Botones con 'time'"),
    ]
    
    for selector, descripcion in selectores_horarios:
        try:
            horarios = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"✓ {descripcion}: {len(horarios)} horarios detectados")
            
            if horarios:
                print("\n  Primeros 5 horarios:")
                for i, h in enumerate(horarios[:5], 1):
                    texto = h.text.strip()
                    print(f"    {i}. {texto}")
        except Exception as e:
            print(f"✗ {descripcion}: Error - {str(e)[:50]}")
    
    input("\nPresiona ENTER para continuar al siguiente test...")

def test_click_horario_y_comprar(driver):
    """Test 4: Click en horario y botón de comprar"""
    print("\n" + "="*80)
    print("TEST 4: Click en horario y botón COMPRAR ENTRADAS")
    print("="*80)
    
    # Buscar y hacer clic en primer horario
    try:
        horarios = driver.find_elements(By.CSS_SELECTOR, "button[class*='showtime'], button[class*='schedule']")
        
        if not horarios:
            print("✗ No se encontraron horarios")
            input("\nPresiona ENTER para finalizar...")
            return
        
        primer_horario = horarios[0]
        print(f"Haciendo clic en horario: {primer_horario.text}")
        driver.execute_script("arguments[0].click();", primer_horario)
        time.sleep(3)
        
        print("✓ Click en horario exitoso")
        
    except Exception as e:
        print(f"✗ Error haciendo clic en horario: {str(e)[:100]}")
        input("\nPresiona ENTER para finalizar...")
        return
    
    # Buscar botón COMPRAR ENTRADAS
    selectores_comprar = [
        ("button[data-testid='buy-tickets-button']", "Botón con data-testid"),
        ("//button[contains(text(), 'COMPRAR')]", "Botón con texto COMPRAR"),
    ]
    
    boton_encontrado = False
    for selector, descripcion in selectores_comprar:
        try:
            if selector.startswith("//"):
                boton = driver.find_element(By.XPATH, selector)
            else:
                boton = driver.find_element(By.CSS_SELECTOR, selector)
            
            print(f"✓ {descripcion}: Encontrado")
            print(f"  Texto del botón: {boton.text}")
            boton_encontrado = True
            break
        except:
            print(f"✗ {descripcion}: No encontrado")
    
    if boton_encontrado:
        print("\n✓ Todos los selectores básicos funcionan correctamente")
    else:
        print("\n⚠️ Algunos selectores necesitan ajustes")
    
    input("\nPresiona ENTER para finalizar...")

def main():
    print("="*80)
    print("CINEMARK PERU - TEST DE SELECTORES")
    print("="*80)
    print("\nEste script verifica que los selectores CSS/XPath estén funcionando")
    print("Se ejecutarán 4 tests secuenciales:")
    print("  1. Cargar lista de películas")
    print("  2. Navegar a página de película")
    print("  3. Seleccionar cine y ver horarios")
    print("  4. Click en horario y botón comprar")
    print("\nEl navegador quedará abierto para que puedas inspeccionar")
    print("="*80)
    
    input("\nPresiona ENTER para comenzar...")
    
    driver = None
    try:
        driver = configurar_driver()
        
        test_cargar_peliculas(driver)
        test_pagina_pelicula(driver)
        test_seleccionar_cine(driver)
        test_click_horario_y_comprar(driver)
        
        print("\n" + "="*80)
        print("TESTS COMPLETADOS")
        print("="*80)
        print("\nEl navegador permanecerá abierto para que puedas inspeccionar")
        print("Cierra esta ventana cuando termines")
        
        input("\nPresiona ENTER para cerrar el navegador...")
        
    except KeyboardInterrupt:
        print("\n\nTest interrumpido por el usuario")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona ENTER para cerrar...")
    finally:
        if driver:
            driver.quit()
            print("✓ Navegador cerrado")

if __name__ == "__main__":
    main()
