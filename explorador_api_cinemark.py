"""
EXPLORADOR DE API DE CINEMARK
Intenta acceder a los endpoints de la API detectada
"""
import requests
import json
import time

# URLs base detectadas del HTML
API_URLS = {
    'local': 'https://www.cinemark-peru.com/api',
    'bff': 'https://bff.cinemark-peru.com/api'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Referer': 'https://www.cinemark-peru.com/',
    'Origin': 'https://www.cinemark-peru.com'
}

def explorar_endpoints():
    """Explora endpoints comunes de la API"""
    print("="*80)
    print("EXPLORACIÓN DE API DE CINEMARK")
    print("="*80)
    
    # Endpoints comunes a probar
    endpoints = [
        '/cinemas',
        '/cines',
        '/theaters',
        '/movies',
        '/peliculas',
        '/films',
        '/showtimes',
        '/horarios',
        '/functions',
        '/funciones',
        '/prices',
        '/precios',
        '/tickets',
        '/entradas',
        '/cities',
        '/ciudades',
        '/formats',
        '/formatos',
        '/sessions',
        '/sesiones'
    ]
    
    resultados = []
    
    for api_name, base_url in API_URLS.items():
        print(f"\n{'='*80}")
        print(f"PROBANDO API: {api_name.upper()} ({base_url})")
        print(f"{'='*80}")
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            print(f"\n[{api_name}] Probando: {endpoint}")
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✓ ÉXITO!")
                    print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                    
                    # Intentar parsear JSON
                    try:
                        data = response.json()
                        print(f"   ✓ JSON válido")
                        print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Es una lista'}")
                        
                        # Guardar respuesta
                        filename = f"api_response_{api_name}_{endpoint.replace('/', '_')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"   ✓ Guardado en: {filename}")
                        
                        resultados.append({
                            'api': api_name,
                            'endpoint': endpoint,
                            'url': url,
                            'status': response.status_code,
                            'data': data
                        })
                        
                    except json.JSONDecodeError:
                        print(f"   ⚠️ Respuesta no es JSON")
                        print(f"   Contenido: {response.text[:200]}")
                
                elif response.status_code == 404:
                    print(f"   ✗ No encontrado")
                elif response.status_code == 401 or response.status_code == 403:
                    print(f"   ⚠️ Requiere autenticación")
                else:
                    print(f"   ⚠️ Otro status")
                    
                time.sleep(0.5)  # No saturar el servidor
                
            except requests.exceptions.Timeout:
                print(f"   ✗ Timeout")
            except requests.exceptions.ConnectionError:
                print(f"   ✗ Error de conexión")
            except Exception as e:
                print(f"   ✗ Error: {str(e)[:50]}")
    
    return resultados

def probar_endpoints_con_parametros():
    """Prueba endpoints con parámetros comunes"""
    print("\n" + "="*80)
    print("PROBANDO ENDPOINTS CON PARÁMETROS")
    print("="*80)
    
    # Endpoints con parámetros comunes
    tests = [
        # Cinemas/Cines
        {
            'url': 'https://www.cinemark-peru.com/api/cinemas',
            'params': {}
        },
        {
            'url': 'https://bff.cinemark-peru.com/api/cinemas',
            'params': {}
        },
        # Movies/Películas
        {
            'url': 'https://www.cinemark-peru.com/api/movies',
            'params': {'city': 'lima'}
        },
        {
            'url': 'https://bff.cinemark-peru.com/api/movies',
            'params': {}
        },
        # Showtimes/Horarios
        {
            'url': 'https://www.cinemark-peru.com/api/showtimes',
            'params': {}
        },
        {
            'url': 'https://bff.cinemark-peru.com/api/showtimes',
            'params': {}
        },
    ]
    
    for test in tests:
        url = test['url']
        params = test['params']
        
        print(f"\n→ {url}")
        if params:
            print(f"   Params: {params}")
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✓ JSON válido")
                    
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())[:10]}")
                    elif isinstance(data, list):
                        print(f"   ✓ Lista con {len(data)} elementos")
                        if data:
                            print(f"   Primer elemento keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                    
                except:
                    print(f"   Contenido: {response.text[:200]}")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ✗ Error: {str(e)[:50]}")

def analizar_estructura_next_data():
    """Intenta obtener datos del __NEXT_DATA__ de una página"""
    print("\n" + "="*80)
    print("ANALIZANDO __NEXT_DATA__ DE PÁGINAS")
    print("="*80)
    
    urls_probar = [
        'https://www.cinemark-peru.com/',
        'https://www.cinemark-peru.com/cartelera',
    ]
    
    for url in urls_probar:
        print(f"\n→ {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Buscar __NEXT_DATA__
                import re
                matches = re.findall(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
                
                if matches:
                    print(f"   ✓ Encontrado __NEXT_DATA__")
                    
                    try:
                        data = json.loads(matches[0])
                        print(f"   ✓ JSON parseado")
                        print(f"   Keys: {list(data.keys())}")
                        
                        # Guardar
                        filename = f"next_data_{url.split('/')[-1] or 'home'}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"   ✓ Guardado en: {filename}")
                        
                    except Exception as e:
                        print(f"   ✗ Error parseando: {e}")
                else:
                    print(f"   ✗ No se encontró __NEXT_DATA__")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"   ✗ Error: {str(e)[:50]}")

def main():
    print("="*80)
    print("EXPLORADOR DE API DE CINEMARK PERÚ")
    print("="*80)
    print()
    
    try:
        # 1. Explorar endpoints básicos
        resultados = explorar_endpoints()
        
        # 2. Probar con parámetros
        probar_endpoints_con_parametros()
        
        # 3. Analizar __NEXT_DATA__
        analizar_estructura_next_data()
        
        # Resumen
        print("\n" + "="*80)
        print("RESUMEN")
        print("="*80)
        print(f"✓ Endpoints exitosos encontrados: {len(resultados)}")
        
        if resultados:
            print("\nEndpoints exitosos:")
            for r in resultados:
                print(f"   • {r['api']}: {r['endpoint']} ({r['status']})")
        
        print("\n✓ Exploración completada")
        print("✓ Revisa los archivos JSON generados para más detalles")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
