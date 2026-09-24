"""
==============================================================================
Script 25: Aplicación de Validadores $jsonSchema en MongoDB (Gobernanza de Datos)
==============================================================================
"""
import pymongo

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Financial"

def aplicar_validadores():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    print("=" * 80)
    print("APLICANDO VALIDACIÓN FORMAL $jsonSchema EN MONGODB (FINANCIAL)")
    print("=" * 80)
    
    # 1. Validador para distritos
    schema_distritos = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id_distrito", "nombre", "region", "poblacion", "tasa_desempleo", "tasa_criminalidad", "auditoria"],
            "properties": {
                "id_distrito": {"bsonType": "int", "description": "ID numérico del distrito"},
                "nombre": {"bsonType": "string"},
                "region": {"bsonType": "string"},
                "poblacion": {"bsonType": "int"},
                "tasa_desempleo": {"bsonType": ["double", "int", "decimal"]},
                "tasa_criminalidad": {"bsonType": ["double", "int", "decimal"]},
                "auditoria": {
                    "bsonType": "object",
                    "required": ["es_imputado"],
                    "properties": {
                        "es_imputado": {"bsonType": "bool"},
                        "metodo_imputacion": {"bsonType": ["string", "null"]}
                    }
                }
            }
        }
    }
    db.command("collMod", "distritos", validator=schema_distritos, validationLevel="moderate")
    print("  [OK] Validador $jsonSchema aplicado en colección 'distritos'.")
    
    # 2. Validador para prestamos
    schema_prestamos = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id_prestamo", "id_cuenta", "id_cliente", "condiciones", "evaluacion_riesgo"],
            "properties": {
                "id_prestamo": {"bsonType": "int"},
                "id_cuenta": {"bsonType": "int"},
                "id_cliente": {"bsonType": "int"},
                "condiciones": {
                    "bsonType": "object",
                    "required": ["monto", "plazo_meses", "cuota_mensual"],
                    "properties": {
                        "monto": {"bsonType": ["double", "int", "decimal"]},
                        "plazo_meses": {"bsonType": "int"},
                        "cuota_mensual": {"bsonType": ["double", "int", "decimal"]}
                    }
                },
                "evaluacion_riesgo": {
                    "bsonType": "object",
                    "required": ["codigo_estado", "condicion", "es_moroso"],
                    "properties": {
                        "codigo_estado": {"bsonType": "string", "enum": ["A", "B", "C", "D"]},
                        "condicion": {"bsonType": "string"},
                        "es_moroso": {"bsonType": "bool"}
                    }
                }
            }
        }
    }
    db.command("collMod", "prestamos", validator=schema_prestamos, validationLevel="moderate")
    print("  [OK] Validador $jsonSchema aplicado en colección 'prestamos'.")
    
    # 3. Validador para ordenes
    schema_ordenes = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id_orden", "id_cuenta", "id_cliente", "monto_mensual", "categoria_pago"],
            "properties": {
                "id_orden": {"bsonType": "int"},
                "id_cuenta": {"bsonType": "int"},
                "id_cliente": {"bsonType": "int"},
                "monto_mensual": {"bsonType": ["double", "int", "decimal"]},
                "categoria_pago": {
                    "bsonType": "object",
                    "required": ["codigo", "descripcion"],
                    "properties": {
                        "codigo": {"bsonType": "string"},
                        "descripcion": {"bsonType": "string"}
                    }
                }
            }
        }
    }
    db.command("collMod", "ordenes", validator=schema_ordenes, validationLevel="moderate")
    print("  [OK] Validador $jsonSchema aplicado en colección 'ordenes'.")
    
    # 4. Validador para FinancialMongo (Cliente 360)
    schema_cliente360 = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id_cliente", "datos_personales", "evaluacion_crediticia", "perfil_analitico", "distrito"],
            "properties": {
                "id_cliente": {"bsonType": "int"},
                "datos_personales": {
                    "bsonType": "object",
                    "required": ["sexo", "tipo_disposicion"]
                },
                "evaluacion_crediticia": {
                    "bsonType": "object",
                    "required": ["tiene_prestamo", "calificacion"]
                },
                "perfil_analitico": {
                    "bsonType": "object",
                    "required": ["macro_region", "segmento_edad", "arquetipo_demografico"]
                },
                "distrito": {
                    "bsonType": "object",
                    "required": ["id_distrito", "nombre", "region", "tasa_desempleo", "tasa_criminalidad"]
                }
            }
        }
    }
    db.command("collMod", "FinancialMongo", validator=schema_cliente360, validationLevel="moderate")
    print("  [OK] Validador $jsonSchema aplicado en colección 'FinancialMongo' (Cliente 360).")
    
    print("=" * 80)
    print("VALIDADORES $jsonSchema ACTIVADOS Y EN VIGOR.")
    print("=" * 80)
    client.close()

if __name__ == "__main__":
    aplicar_validadores()
