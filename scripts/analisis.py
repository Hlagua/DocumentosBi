import numpy as np
import pandas as pd

# Cargar dataset
df = pd.read_csv('df_cliente_consolidado.csv')

# Filtrar columnas de distritos únicos
columnas = [
    'id_distrito',
    'nombre_distrito',
    'region',
    'poblacion',
    'salario_promedio',
    'tasa_desempleo',
    'tasa_criminalidad',
]
dist = df[columnas].drop_duplicates(subset='id_distrito').reset_index(drop=True)

# Excluir el distrito 69
completos = dist[dist['id_distrito'] != 69].copy()

# Forzar columnas a formato numérico 
for col in [
    'poblacion',
    'salario_promedio',
    'tasa_desempleo',
    'tasa_criminalidad',
]:
  completos[col] = pd.to_numeric(completos[col], errors='coerce')

print('=== CORRELACIONES (distrito 69 excluido) ===\n')
print(
    'Poblacion vs Tasa Desempleo:',
    round(completos['poblacion'].corr(completos['tasa_desempleo']), 3),
)
print(
    'Poblacion vs Tasa Criminalidad:',
    round(completos['poblacion'].corr(completos['tasa_criminalidad']), 3),
)
print(
    'Salario vs Tasa Desempleo:',
    round(completos['salario_promedio'].corr(completos['tasa_desempleo']), 3),
)
print(
    'Salario vs Tasa Criminalidad:',
    round(
        completos['salario_promedio'].corr(completos['tasa_criminalidad']), 3
    ),
)

print('\n=== PROMEDIO DE TASA DE DESEMPLEO POR REGION ===')
print(completos.groupby('region')['tasa_desempleo'].mean().round(2))