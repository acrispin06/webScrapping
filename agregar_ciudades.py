"""
Script para agregar columna 'Ciudad' a CSV de Cineplanet (precios y capacidades)
Lee lista_cines_ciudades.txt y agrega la ciudad correspondiente a cada cine

Uso:
    # Procesar TODOS los archivos COMPLETO (precios y capacidades)
    python agregar_ciudades.py
    
    # Procesar un archivo específico
    python agregar_ciudades.py archivo.csv
    
Archivos procesados automáticamente:
    - precios_cineplanet_COMPLETO_*.csv
    - capacidades_cineplanet_COMPLETO_*.csv
    
Nota: Solo procesa archivos COMPLETO (ignora EN_PROGRESO)
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime


def cargar_diccionario_ciudades(archivo_ciudades='lista_cines_ciudades.txt'):
    """
    Carga el archivo de ciudades y crea un diccionario {cine: ciudad}
    
    Formato esperado en archivo:
        CP Alcazar - Lima
        CP Arequipa Mall Plaza - Arequipa
        ...
    
    Returns:
        dict: {nombre_cine: ciudad}
    """
    print(f"📖 Leyendo archivo: {archivo_ciudades}")
    diccionario = {}
    
    try:
        with open(archivo_ciudades, 'r', encoding='utf-8') as f:
            for num_linea, linea in enumerate(f, 1):
                linea = linea.strip()
                
                # Saltar líneas vacías
                if not linea:
                    continue
                
                # Buscar el separador ' - ' (con espacios)
                if ' - ' not in linea:
                    # Intentar con solo '-' (sin espacios)
                    if '-' in linea:
                        separador = '-'
                    else:
                        print(f"   ⚠️  Línea {num_linea} sin separador válido: {linea[:50]}")
                        continue
                else:
                    separador = ' - '
                
                # Separar por el separador encontrado
                partes = linea.split(separador, 1)  # Limitar a 1 split (por si ciudad tiene '-')
                
                if len(partes) >= 2:
                    cine = partes[0].strip()
                    ciudad = partes[1].strip()
                    
                    if cine and ciudad:
                        diccionario[cine] = ciudad
                    else:
                        print(f"   ⚠️  Línea {num_linea} con datos vacíos: {linea[:50]}")
                else:
                    print(f"   ⚠️  Línea {num_linea} sin formato válido: {linea[:50]}")
        
        print(f"✅ Cargados {len(diccionario)} cines con sus ciudades\n")
        return diccionario
        
    except FileNotFoundError:
        print(f"❌ ERROR: No se encontró el archivo '{archivo_ciudades}'")
        print("   Asegúrate de que el archivo existe en el directorio actual.\n")
        return {}
    except Exception as e:
        print(f"❌ ERROR leyendo archivo: {e}\n")
        return {}


def normalizar_nombre_cine(nombre):
    """
    Normaliza el nombre del cine para matching
    - Convierte a mayúsculas
    - Elimina espacios extra
    """
    return nombre.strip().upper()


def encontrar_ciudad(nombre_cine, diccionario_ciudades):
    """
    Busca la ciudad de un cine en el diccionario
    Intenta matching exacto y luego matching parcial
    
    Args:
        nombre_cine (str): Nombre del cine desde el CSV
        diccionario_ciudades (dict): Diccionario {cine: ciudad}
    
    Returns:
        str: Ciudad encontrada o 'Desconocida'
    """
    nombre_normalizado = normalizar_nombre_cine(nombre_cine)
    
    # 1. Intentar matching exacto
    for cine_dict, ciudad in diccionario_ciudades.items():
        if normalizar_nombre_cine(cine_dict) == nombre_normalizado:
            return ciudad
    
    # 2. Intentar matching parcial (el nombre del CSV contiene el nombre del diccionario)
    for cine_dict, ciudad in diccionario_ciudades.items():
        cine_dict_norm = normalizar_nombre_cine(cine_dict)
        if cine_dict_norm in nombre_normalizado or nombre_normalizado in cine_dict_norm:
            return ciudad
    
    # 3. No encontrado
    return 'Desconocida'


def agregar_ciudades_a_csv(archivo_csv, diccionario_ciudades, columna_cine='Cine'):
    """
    Lee un CSV, agrega columna 'Ciudad' y guarda el resultado
    
    Args:
        archivo_csv (str): Ruta al archivo CSV
        diccionario_ciudades (dict): Diccionario {cine: ciudad}
        columna_cine (str): Nombre de la columna que contiene el nombre del cine
    
    Returns:
        bool: True si se procesó correctamente, False en caso contrario
    """
    print(f"📄 Procesando CSV: {archivo_csv}")
    
    try:
        # Leer CSV
        df = pd.read_csv(archivo_csv, encoding='utf-8-sig')
        print(f"   Registros: {len(df)}")
        print(f"   Columnas: {list(df.columns)}")
        
        # Verificar que existe la columna de cine
        if columna_cine not in df.columns:
            print(f"\n❌ ERROR: No se encontró la columna '{columna_cine}' en el CSV")
            print(f"   Columnas disponibles: {list(df.columns)}\n")
            return False
        
        # Agregar columna 'Ciudad' si no existe
        if 'Ciudad' in df.columns:
            print(f"\n⚠️  La columna 'Ciudad' ya existe. Se sobrescribirá.")
        
        print(f"\n🔍 Buscando ciudades para cada cine...")
        
        # Crear lista de ciudades para cada registro
        ciudades = []
        cines_sin_ciudad = set()
        
        for idx, row in df.iterrows():
            nombre_cine = str(row[columna_cine])
            ciudad = encontrar_ciudad(nombre_cine, diccionario_ciudades)
            ciudades.append(ciudad)
            
            if ciudad == 'Desconocida':
                cines_sin_ciudad.add(nombre_cine)
        
        # Agregar columna Ciudad (después de Cine)
        # Encontrar posición de columna Cine
        pos_cine = df.columns.get_loc(columna_cine)
        
        # Insertar Ciudad después de Cine
        df.insert(pos_cine + 1, 'Ciudad', ciudades)
        
        print(f"✅ Columna 'Ciudad' agregada exitosamente")
        print(f"   Posición: Después de '{columna_cine}'")
        
        # Estadísticas
        ciudades_unicas = df['Ciudad'].nunique()
        registros_con_ciudad = len(df[df['Ciudad'] != 'Desconocida'])
        registros_sin_ciudad = len(df[df['Ciudad'] == 'Desconocida'])
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Total registros: {len(df)}")
        print(f"   Ciudades únicas: {ciudades_unicas}")
        print(f"   Con ciudad asignada: {registros_con_ciudad} ({registros_con_ciudad/len(df)*100:.1f}%)")
        print(f"   Sin ciudad (Desconocida): {registros_sin_ciudad} ({registros_sin_ciudad/len(df)*100:.1f}%)")
        
        if cines_sin_ciudad:
            print(f"\n⚠️  CINES SIN CIUDAD ASIGNADA ({len(cines_sin_ciudad)}):")
            for cine in sorted(cines_sin_ciudad):
                print(f"   - {cine}")
            print()
        
        # Generar nombre de archivo de salida
        archivo_path = Path(archivo_csv)
        nombre_base = archivo_path.stem
        extension = archivo_path.suffix
        
        # Si el archivo ya tiene "_con_ciudades", no agregarlo de nuevo
        if "_con_ciudades" in nombre_base:
            archivo_salida = archivo_csv
        else:
            archivo_salida = archivo_path.parent / f"{nombre_base}_con_ciudades{extension}"
        
        # Guardar CSV actualizado
        df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
        print(f"💾 Archivo guardado: {archivo_salida}")
        print(f"   Tamaño: {archivo_salida.stat().st_size:,} bytes")
        
        # Mostrar muestra
        print(f"\n📋 MUESTRA DE DATOS (primeras 5 filas):")
        print(df.head().to_string(index=False))
        print()
        
        return True
        
    except FileNotFoundError:
        print(f"\n❌ ERROR: No se encontró el archivo '{archivo_csv}'\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR procesando CSV: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def buscar_archivos_csv(tipo='precios'):
    """
    Busca archivos CSV de precios o capacidades en el directorio actual
    Prioriza archivos COMPLETO sobre EN_PROGRESO
    
    Args:
        tipo (str): 'precios' o 'capacidades'
    
    Returns:
        list: Lista de archivos CSV encontrados (ordenados por prioridad)
    """
    directorio_actual = Path('.')
    
    # Buscar archivos según el tipo
    if tipo == 'capacidades':
        patron = 'capacidades_cineplanet*.csv'
    else:
        patron = 'precios_cineplanet*.csv'
    
    archivos = list(directorio_actual.glob(patron))
    
    if not archivos:
        return []
    
    # Filtrar solo archivos COMPLETO (excluir EN_PROGRESO)
    archivos_completo = [f for f in archivos if 'COMPLETO' in f.name]
    
    if not archivos_completo:
        # Si no hay archivos COMPLETO, usar todos
        archivos_completo = archivos
    
    # Ordenar por fecha (más reciente primero)
    archivos_ordenados = sorted(archivos_completo, key=lambda f: f.stat().st_mtime, reverse=True)
    return archivos_ordenados


def main():
    print("=" * 80)
    print("🎬 AGREGAR CIUDADES A CSV DE CINEPLANET")
    print("=" * 80)
    print()
    
    # 1. Cargar diccionario de ciudades
    diccionario_ciudades = cargar_diccionario_ciudades()
    
    if not diccionario_ciudades:
        print("❌ No se pudo cargar el diccionario de ciudades. Abortando.\n")
        return
    
    # 2. Determinar archivo CSV a procesar
    if len(sys.argv) > 1:
        # Usuario especificó archivo CSV
        archivo_csv = sys.argv[1]
        print(f"📂 Archivo especificado: {archivo_csv}\n")
        archivos_a_procesar = [archivo_csv]
    else:
        # Buscar archivos CSV automáticamente (PRECIOS y CAPACIDADES)
        print("🔍 Buscando archivos CSV COMPLETO...")
        
        archivos_precios = buscar_archivos_csv('precios')
        archivos_capacidades = buscar_archivos_csv('capacidades')
        
        todos_archivos = archivos_precios + archivos_capacidades
        
        if not todos_archivos:
            print("\n❌ No se encontraron archivos CSV COMPLETO en el directorio actual.")
            print("   Uso: python agregar_ciudades.py archivo.csv\n")
            return
        
        print(f"✅ Encontrados {len(todos_archivos)} archivo(s) COMPLETO:")
        print(f"   - Precios: {len(archivos_precios)}")
        print(f"   - Capacidades: {len(archivos_capacidades)}\n")
        
        for i, archivo in enumerate(todos_archivos, 1):
            tamano = archivo.stat().st_size
            fecha = datetime.fromtimestamp(archivo.stat().st_mtime)
            tipo = "📊 PRECIOS" if "precios" in archivo.name.lower() else "🪑 CAPACIDADES"
            print(f"   {i}. {tipo} - {archivo.name}")
            print(f"      ({tamano:,} bytes, {fecha.strftime('%Y-%m-%d %H:%M:%S')})")
        
        archivos_a_procesar = [str(f) for f in todos_archivos]
        print()
    
    # 3. Procesar CSV(s)
    total_procesados = 0
    total_exitosos = 0
    
    for archivo_csv in archivos_a_procesar:
        print("-" * 80)
        print(f"📌 Procesando: {Path(archivo_csv).name}")
        print("-" * 80)
        
        # Determinar columna de cine según el tipo de archivo
        if 'capacidades' in archivo_csv.lower():
            # Archivos de capacidades usan columna 'cine' (minúscula)
            columna_cine = 'cine'
        else:
            # Archivos de precios usan columna 'Cine' (mayúscula)
            columna_cine = 'Cine'
        
        exito = agregar_ciudades_a_csv(archivo_csv, diccionario_ciudades, columna_cine)
        
        total_procesados += 1
        if exito:
            total_exitosos += 1
        
        print()
    
    # 4. Resultado final
    print("=" * 80)
    if total_exitosos == total_procesados:
        print(f"✅ PROCESO COMPLETADO EXITOSAMENTE ({total_exitosos}/{total_procesados})")
    else:
        print(f"⚠️  PROCESO COMPLETADO CON ALGUNOS ERRORES ({total_exitosos}/{total_procesados} exitosos)")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
