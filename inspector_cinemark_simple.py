"""
INSPECTOR SIMPLE DE CINEMARK PERÚ
Analiza la estructura básica de la página
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import json

BASE_URL = 'https://www.cinemark-peru.com'

def configurar_driver():
    """Configura Chrome simple"""
    print("Configurando Chrome...")
    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
    
    print("✓ WebDriver configurado\n")
    return driver

def analizar_pagina_principal(driver):
    """Analiza elementos de la página principal"""
    print("="*80)
    print("ANÁLISIS DE PÁGINA PRINCIPAL")
    print("="*80)
    
    print("\nCARGANDO PÁGINA...")
    driver.get(BASE_URL)
    time.sleep(8)
    
    print(f"✓ Título: {driver.title}")
    print(f"✓ URL: {driver.current_url}\n")
    
    # Guardar HTML para inspección
    with open('cinemark_homepage.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("✓ HTML guardado en: cinemark_homepage.html\n")
    
    # Buscar menú de cines
    print("BUSCANDO MENÚ DE CINES...")
    selectores_cines = [
        "a[href*='cines']",
        "a[href*='cinema']",
        ".nav-link",
        "nav a",
        "header a"
    ]
    
    for selector in selectores_cines:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            if elementos:
                print(f"\n✓ Selector '{selector}': {len(elementos)} elementos")
                for i, elem in enumerate(elementos[:5]):
                    try:
                        texto = elem.text.strip()
                        href = elem.get_attribute('href')
                        if texto or href:
                            print(f"   [{i+1}] {texto:30s} → {href}")
                    except:
                        pass
        except Exception as e:
            pass
    
    # Buscar sección de películas
    print("\n" + "="*80)
    print("BUSCANDO SECCIÓN DE PELÍCULAS...")
    print("="*80)
    
    selectores_peliculas = [
        "div[class*='movie']",
        "div[class*='pelicula']",
        "div[class*='film']",
        "div[class*='card']",
        "article",
        ".movie",
        ".pelicula"
    ]
    
    for selector in selectores_peliculas:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            if elementos:
                print(f"\n✓ Selector '{selector}': {len(elementos)} elementos")
                # Mostrar primeros 3
                for i, elem in enumerate(elementos[:3]):
                    try:
                        texto = elem.text.strip()[:100]
                        if texto:
                            print(f"   [{i+1}] {texto}")
                    except:
                        pass
        except:
            pass
    
    # Buscar botones de horario
    print("\n" + "="*80)
    print("BUSCANDO BOTONES DE HORARIO...")
    print("="*80)
    
    selectores_horarios = [
        "button",
        "a[class*='btn']",
        "a[class*='button']",
        ".btn",
        ".button"
    ]
    
    for selector in selectores_horarios:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            if elementos:
                print(f"\n✓ Selector '{selector}': {len(elementos)} elementos")
                # Mostrar primeros 5
                for i, elem in enumerate(elementos[:5]):
                    try:
                        texto = elem.text.strip()
                        clase = elem.get_attribute('class')
                        if texto:
                            print(f"   [{i+1}] Texto: {texto[:50]:50s} | Clase: {clase[:50]}")
                    except:
                        pass
        except:
            pass
    
    print("\n" + "="*80)
    print("¿Qué acción quieres realizar?")
    print("="*80)
    print("1. Inspeccionar manualmente (mantener navegador abierto)")
    print("2. Intentar navegar a un cine")
    print("3. Buscar página de cartelera")
    print("4. Salir")
    print()
    
    opcion = input("Opción (1-4): ").strip()
    
    if opcion == "1":
        print("\n✓ Navegador abierto para inspección manual")
        print("  → Abre DevTools (F12) y revisa la pestaña Network")
        print("  → Presiona Enter cuando termines...")
        input()
    
    elif opcion == "2":
        intentar_navegar_cine(driver)
    
    elif opcion == "3":
        buscar_cartelera(driver)

def intentar_navegar_cine(driver):
    """Intenta navegar a una página de cine"""
    print("\n" + "="*80)
    print("NAVEGANDO A PÁGINA DE CINE")
    print("="*80)
    
    # Buscar link de cines
    try:
        links_cines = driver.find_elements(By.CSS_SELECTOR, "a[href*='cine']")
        if links_cines:
            primer_link = links_cines[0]
            url = primer_link.get_attribute('href')
            print(f"\n✓ Navegando a: {url}")
            
            driver.get(url)
            time.sleep(5)
            
            print(f"✓ URL actual: {driver.current_url}")
            print(f"✓ Título: {driver.title}\n")
            
            # Guardar HTML
            with open('cinemark_cine.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("✓ HTML guardado en: cinemark_cine.html\n")
            
            # Analizar estructura
            analizar_estructura_peliculas(driver)
            
            print("\nPresiona Enter para continuar...")
            input()
    except Exception as e:
        print(f"✗ Error: {e}")

def buscar_cartelera(driver):
    """Busca la página de cartelera"""
    print("\n" + "="*80)
    print("BUSCANDO CARTELERA")
    print("="*80)
    
    urls_probar = [
        f"{BASE_URL}/cartelera",
        f"{BASE_URL}/peliculas",
        f"{BASE_URL}/movies",
        f"{BASE_URL}/estrenos"
    ]
    
    for url in urls_probar:
        print(f"\nProbando: {url}")
        try:
            driver.get(url)
            time.sleep(3)
            
            if driver.current_url == url:
                print(f"✓ Página encontrada: {driver.title}")
                
                # Guardar HTML
                with open('cinemark_cartelera.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("✓ HTML guardado en: cinemark_cartelera.html")
                
                analizar_estructura_peliculas(driver)
                break
        except Exception as e:
            print(f"✗ No encontrada")

def analizar_estructura_peliculas(driver):
    """Analiza estructura de películas y horarios"""
    print("\n" + "="*80)
    print("ANALIZANDO ESTRUCTURA DE PELÍCULAS")
    print("="*80)
    
    # Buscar títulos de películas
    selectores_titulos = [
        "h1", "h2", "h3",
        ".title",
        ".movie-title",
        "[class*='title']"
    ]
    
    print("\nTÍTULOS ENCONTRADOS:")
    for selector in selectores_titulos:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            if elementos:
                for i, elem in enumerate(elementos[:5]):
                    try:
                        texto = elem.text.strip()
                        if texto and len(texto) > 3:
                            print(f"   {selector:30s} → {texto[:60]}")
                    except:
                        pass
        except:
            pass
    
    # Buscar horarios
    print("\nHORARIOS/BOTONES ENCONTRADOS:")
    selectores_horarios = [
        "button[class*='time']",
        "button[class*='hora']",
        "a[class*='time']",
        "span[class*='time']",
        ".showtime"
    ]
    
    for selector in selectores_horarios:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            if elementos:
                print(f"\n✓ {selector}: {len(elementos)} elementos")
                for i, elem in enumerate(elementos[:5]):
                    try:
                        texto = elem.text.strip()
                        if texto:
                            print(f"     [{i+1}] {texto}")
                    except:
                        pass
        except:
            pass

def main():
    print("="*80)
    print("INSPECTOR SIMPLE DE CINEMARK PERÚ")
    print("="*80)
    print(f"URL: {BASE_URL}")
    print("="*80)
    print()
    
    driver = None
    try:
        driver = configurar_driver()
        analizar_pagina_principal(driver)
        
        print("\n" + "="*80)
        print("INSPECCIÓN COMPLETADA")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("\nCerrando navegador...")
            driver.quit()

if __name__ == "__main__":
    main()
