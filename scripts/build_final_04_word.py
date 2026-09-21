# -*- coding: utf-8 -*-
"""
Script maestro para la construcción del informe definitivo y exhaustivo de 40+ páginas:
04_Informe_Sistemas_de_Recomendacion.docx
"""
import os
import sys

# Agregar ruta actual al path
sys.path.append(os.path.dirname(__file__))

from helpers_informe_4 import init_document
from report_sections_part1 import build_part1
from report_sections_part2 import build_part2
from report_sections_part3 import build_part3
from report_sections_part4 import build_part4

def build_final_04_docx():
    print("Iniciando construcción del informe definitivo y exhaustivo de 40+ páginas...")
    doc = init_document()
    
    print("-> Construyendo Parte 1: Portada, Objetivos, Metodología, Origen y Preparación...")
    build_part1(doc)
    
    print("-> Construyendo Parte 2: Eje 1 (df_transacciones) y Eje 2 (df_ordenes)...")
    build_part2(doc)
    
    print("-> Construyendo Parte 3: Eje 3 (df_prestamos) y Eje 4 (df_cliente_consolidado)...")
    build_part3(doc)
    
    print("-> Construyendo Parte 4: Descarte Empírico, Comparativa Global, MLOps, Conclusiones y Anexos A-E...")
    build_part4(doc)
    
    output_path = "04_Informe_Sistemas_de_Recomendacion.docx"
    doc.save(output_path)
    print(f"¡Éxito total! Documento guardado en: {os.path.abspath(output_path)}")

if __name__ == '__main__':
    build_final_04_docx()
