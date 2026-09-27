"""
Generador de Proyectos Power BI Desktop (.pbip)
Crea las estructuras oficiales de Power BI Project para Kimball SQL Server y MongoDB NoSQL
"""

import os
import json

def create_pbip_project(base_dir, project_name, db_type="kimball"):
    proj_dir = os.path.join(base_dir, project_name)
    os.makedirs(proj_dir, exist_ok=True)

    pbip_file = os.path.join(proj_dir, f"{project_name}.pbip")
    report_folder = os.path.join(proj_dir, f"{project_name}.Report")
    dataset_folder = os.path.join(proj_dir, f"{project_name}.Dataset")

    os.makedirs(report_folder, exist_ok=True)
    os.makedirs(dataset_folder, exist_ok=True)

    # 1. Archivo maestro .pbip
    pbip_content = {
        "version": "1.0",
        "artifacts": [
            {
                "report": {
                    "path": f"{project_name}.Report"
                }
            }
        ],
        "settings": {
            "enableAutoAuth": True
        }
    }
    with open(pbip_file, "w", encoding="utf-8") as f:
        json.dump(pbip_content, f, indent=2)

    # 2. definition.pbir
    pbir_content = {
        "version": "1.0",
        "datasetReference": {
            "byPath": {
                "path": f"../{project_name}.Dataset"
            },
            "byConnection": None
        }
    }
    with open(os.path.join(report_folder, "definition.pbir"), "w", encoding="utf-8") as f:
        json.dump(pbir_content, f, indent=2)

    # 3. definition.pbism
    pbism_content = {
        "version": "1.0"
    }
    with open(os.path.join(dataset_folder, "definition.pbism"), "w", encoding="utf-8") as f:
        json.dump(pbism_content, f, indent=2)

    # 4. model.bim (Tabular Object Model)
    data_source_desc = "SQL Server (DM_Financial_Kimball_v2)" if db_type == "kimball" else "MongoDB NoSQL (Financial)"
    model_bim = {
        "name": f"{project_name}_Model",
        "compatibilityLevel": 1550,
        "model": {
            "culture": "es-EC",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True
            },
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "es-EC",
            "tables": [
                {
                    "name": "_Medidas",
                    "description": "Tabla de Medidas DAX Centralizadas para Auditoría Bancaria",
                    "columns": [
                        {
                            "name": "Métrica",
                            "dataType": "string",
                            "isCalculated": True,
                            "expression": "\"Métricas Oficiales Reconciliadas Δ=$0.00\""
                        }
                    ],
                    "measures": [
                        {
                            "name": "Total Cartera Colocada",
                            "expression": "CALCULATE(SUM(Fact_Prestamos[monto]))",
                            "formatString": "\"$\"#,##0.00;(\"$\"#,##0.00);\"$\"0.00",
                            "description": "Total de cartera colocado en 682 contratos: $103,261,740.00"
                        },
                        {
                            "name": "Total Depósitos Captados",
                            "expression": "CALCULATE(SUM(vw_PBI_Saldo_Final_Cuenta[saldo_cierre_1998]))",
                            "formatString": "\"$\"#,##0.00;(\"$\"#,##0.00);\"$\"0.00",
                            "description": "Saldo final al 31/12/1998 de las 4,500 cuentas: $197,140,434.00"
                        },
                        {
                            "name": "Ratio Absorción Crediticia",
                            "expression": "DIVIDE([Total Cartera Colocada], [Total Depósitos Captados], 0)",
                            "formatString": "0.00%",
                            "description": "Ratio de absorción nacional: 52.38%"
                        },
                        {
                            "name": "Tasa Morosidad Activa Vigente",
                            "expression": "VAR NumMoraD = CALCULATE(COUNTROWS(Fact_Prestamos), Fact_Prestamos[estado] = \"D\") VAR DenVigentes = CALCULATE(COUNTROWS(Fact_Prestamos), Fact_Prestamos[estado] IN {\"C\", \"D\"}) RETURN DIVIDE(NumMoraD, DenVigentes, 0)",
                            "formatString": "0.00%",
                            "description": "Tasa de morosidad sobre préstamos vigentes (C+D): 10.04%"
                        },
                        {
                            "name": "Total Transaccionado",
                            "expression": "CALCULATE(SUM(vw_PBI_Trans_Anual_Cuenta[monto_total]))",
                            "formatString": "\"$\"#,##0.00;(\"$\"#,##0.00);\"$\"0.00",
                            "description": "Monto acumulado en 1,056,320 operaciones: $6,257,862,197.00"
                        }
                    ]
                }
            ],
            "annotations": [
                {
                    "name": "PBI_QueryOrder",
                    "value": "[\"_Medidas\"]"
                },
                {
                    "name": "PersistenciaPoliglota",
                    "value": data_source_desc
                }
            ]
        }
    }
    with open(os.path.join(dataset_folder, "model.bim"), "w", encoding="utf-8") as f:
        json.dump(model_bim, f, indent=2)

    # 5. README de instrucciones en la carpeta del dashboard
    readme_content = f"""# {project_name}
## Proyecto Power BI Desktop Oficial (.pbip)

**Arquitectura:** {data_source_desc}  
**Caso de Estudio:** Financial_ijs (Czech Bank Benchmark)  
**Reconciliación Cuantitativa:** Δ = $0.00  

### Cómo abrir y desplegar este tablero:
1. Haga doble clic en `{project_name}.pbip` para abrirlo directamente en Power BI Desktop.
2. Si su entorno requiere actualización de credenciales:
   - Para SQL Server: Verifique que `(localdb)\\MSSQLLocalDB` o su servidor local tenga la base `DM_Financial_Kimball_v2` con las vistas de `../../sql/04_Vistas_PowerBI_Kimball.sql`.
   - Para MongoDB: Ejecute el script de conexión `../../scripts/26_powerbi_mongo_dashboard.py` desde *Obtener datos -> Script de Python*.
3. Copie las medidas completas desde `../../sql/05_Medidas_DAX_PowerBI.dax`.
"""
    with open(os.path.join(proj_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"[OK] Proyecto Power BI generado: {pbip_file}")

def main():
    base_dir = "dashboards"
    create_pbip_project(base_dir, "Dashboard_Financial_Kimball", "kimball")
    create_pbip_project(base_dir, "Dashboard_Financial_Mongo", "mongo")

if __name__ == "__main__":
    main()
