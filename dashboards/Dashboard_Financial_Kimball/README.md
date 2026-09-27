# Dashboard_Financial_Kimball
## Proyecto Power BI Desktop Oficial (.pbip)

**Arquitectura:** SQL Server (DM_Financial_Kimball_v2)  
**Caso de Estudio:** Financial_ijs (Czech Bank Benchmark)  
**Reconciliación Cuantitativa:** Δ = $0.00  

### Cómo abrir y desplegar este tablero:
1. Haga doble clic en `Dashboard_Financial_Kimball.pbip` para abrirlo directamente en Power BI Desktop.
2. Si su entorno requiere actualización de credenciales:
   - Para SQL Server: Verifique que `(localdb)\MSSQLLocalDB` o su servidor local tenga la base `DM_Financial_Kimball_v2` con las vistas de `../../sql/04_Vistas_PowerBI_Kimball.sql`.
   - Para MongoDB: Ejecute el script de conexión `../../scripts/26_powerbi_mongo_dashboard.py` desde *Obtener datos -> Script de Python*.
3. Copie las medidas completas desde `../../sql/05_Medidas_DAX_PowerBI.dax`.
