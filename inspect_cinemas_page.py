from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

BASE_URL = 'https://www.cineplanet.com.pe'

def configurar_driver():
    options = Options()
    options.add_argument('--start-maximized')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

driver = configurar_driver()

try:
    print("Navegando a /cinemas...")
    driver.get(f"{BASE_URL}/cinemas")
    time.sleep(5)
    
    # Intentar cerrar popups
    try:
        driver.execute_script("""
            var consents = document.querySelectorAll('.consent--background, .consent-overlay, [class*="consent"]');
            consents.forEach(function(el) { el.remove(); });
        """)
    except:
        pass
    
    time.sleep(2)
    
    # Buscar elementos que contengan "cine" o "cinema"
    print("\n=== Buscando elementos con 'cinema' en el texto ===")
    all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Cineplanet') or contains(text(), 'CP ') or contains(text(), 'ALCAZAR')]")
    
    for i, elem in enumerate(all_elements[:10]):
        print(f"\n{i+1}. Tag: {elem.tag_name}")
        print(f"   Class: {elem.get_attribute('class')}")
        print(f"   Text: {elem.text[:50]}")
        print(f"   Parent: {elem.find_element(By.XPATH, '..').get_attribute('class')}")
    
    print("\n\n=== Buscando todos los <a> en la página ===")
    all_links = driver.find_elements(By.TAG_NAME, "a")
    
    cinema_links = [link for link in all_links if 'cinema' in link.get_attribute('href')]
    
    print(f"Total links con 'cinema': {len(cinema_links)}")
    
    for i, link in enumerate(cinema_links[:10]):
        print(f"\n{i+1}. Href: {link.get_attribute('href')}")
        print(f"   Class: {link.get_attribute('class')}")
        print(f"   Text: {link.text[:50]}")
    
    print("\n\nPresiona ENTER para cerrar...")
    input()
    
finally:
    driver.quit()
