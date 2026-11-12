import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.import_service import ImportService
from app.services.marcacion_service import MarcacionService
from app.services.dashboard_service import DashboardService
from app.services.export_service import ExportService
from app.schemas.marcacion import MarcacionFilterParams
from app.models.marcacion import Marcacion
from app.models.trabajador import Trabajador


def test_full_pipeline():
    print("=== INICIANDO PRUEBAS DEL SISTEMA ASISTENCIA K20 ===")
    db = SessionLocal()
    try:
        # 1. Prueba de primera importación
        print("\n--- 1. Ejecutando primera importación de registros_k20.csv ---")
        csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datos", "registros_k20.csv"))
        res1 = ImportService.import_csv(db=db, csv_file_path=csv_path)
        print(f"Resultado Importación 1:")
        print(f"  - Total leídos: {res1['total_leidos']}")
        print(f"  - Nuevos registros: {res1['nuevos_registros']}")
        print(f"  - Duplicados omitidos: {res1['duplicados_omitidos']}")
        print(f"  - Fechas sospechosas detectadas: {res1['fechas_sospechosas_detectadas']}")
        print(f"  - Trabajadores actualizados: {res1['trabajadores_actualizados']}")
        print(f"  - Tiempo: {res1['tiempo_segundos']} segundos")
        
        assert res1['total_leidos'] == 48601, f"Esperado 48601 leídos, obtenido {res1['total_leidos']}"
        # Válido tanto en una base limpia (48601 nuevos) como en una re-ejecución (48601 duplicados)
        assert res1['nuevos_registros'] + res1['duplicados_omitidos'] == 48601, (
            f"Esperado 48601 registros entre nuevos y duplicados, obtenido "
            f"{res1['nuevos_registros']} + {res1['duplicados_omitidos']}"
        )
        assert res1['fechas_sospechosas_detectadas'] == 37, f"Esperado 37 sospechosas, obtenido {res1['fechas_sospechosas_detectadas']}"
        assert res1['trabajadores_actualizados'] == 232, f"Esperado 232 trabajadores, obtenido {res1['trabajadores_actualizados']}"

        # 2. Prueba de Idempotencia (segunda importación del mismo archivo)
        print("\n--- 2. Probando idempotencia (re-ejecución inmediata de importación) ---")
        res2 = ImportService.import_csv(db=db, csv_file_path=csv_path)
        print(f"Resultado Importación 2 (Idempotencia):")
        print(f"  - Total leídos: {res2['total_leidos']}")
        print(f"  - Nuevos registros: {res2['nuevos_registros']}")
        print(f"  - Duplicados omitidos: {res2['duplicados_omitidos']}")
        print(f"  - Tiempo: {res2['tiempo_segundos']} segundos")

        assert res2['nuevos_registros'] == 0, f"Error de duplicación: se insertaron {res2['nuevos_registros']} registros"
        assert res2['duplicados_omitidos'] == 48601, f"Error: no se omitieron los 48601 duplicados"

        # 3. Prueba de Dashboard Overview
        print("\n--- 3. Probando estadísticas del Dashboard ---")
        overview = DashboardService.get_overview(db)
        print(f"Dashboard Stats:")
        print(f"  - Total marcaciones: {overview.stats.total_marcaciones}")
        print(f"  - Trabajadores identificados: {overview.stats.trabajadores_identificados}")
        print(f"  - Fechas sospechosas: {overview.stats.fechas_sospechosas}")
        print(f"  - Marcaciones del día de referencia ({overview.stats.fecha_referencia_hoy}): {overview.stats.marcaciones_hoy}")
        print(f"  - Distribución de punches:")
        for p in overview.distribucion_punches:
            print(f"     * {p.nombre}: {p.cantidad} ({p.porcentaje}%)")
        print(f"  - Años de fechas sospechosas detectadas: {[y.anio for y in overview.desglose_sospechosas]}")

        total_trabajadores = db.query(Trabajador).count()
        print(f"  - Trabajadores en padrón: {total_trabajadores}")

        # Tras la sincronizacion con el K20 pueden existir registros nuevos
        # (22 al 12/11/2026); el historico CSV (48 601) se conserva intacto.
        assert overview.stats.total_marcaciones >= 48601
        # El padrón incluye los 232 códigos históricos y los colaboradores sin marcaciones (289 en total)
        assert overview.stats.trabajadores_identificados == total_trabajadores
        assert total_trabajadores >= 232
        assert overview.stats.fechas_sospechosas == 37

        # 4. Prueba de Filtros y Paginación
        print("\n--- 4. Probando filtros y paginación en marcaciones ---")
        # Filtro por usuario '104'
        f_user = MarcacionFilterParams(user_id="104")
        items_u, total_u = MarcacionService.get_paginated(db, f_user, page=1, per_page=10)
        print(f"  - Filtro user_id='104': {total_u} marcaciones encontradas")
        assert total_u > 0, "No se encontraron marcaciones para el trabajador 104"

        # Filtro por punch 0
        f_p0 = MarcacionFilterParams(punch=0)
        items_p0, total_p0 = MarcacionService.get_paginated(db, f_p0, page=1, per_page=10)
        print(f"  - Filtro punch=0: {total_p0} marcaciones encontradas")
        assert total_p0 >= 16139, f"Esperado al menos 16139 para punch 0, obtenido {total_p0}"

        # Filtro por fechas sospechosas
        f_sosp = MarcacionFilterParams(fecha_sospechosa=True)
        items_sosp, total_sosp = MarcacionService.get_paginated(db, f_sosp, page=1, per_page=10)
        print(f"  - Filtro solo sospechosas: {total_sosp} marcaciones encontradas")
        assert total_sosp == 37, f"Esperado 37 sospechosas, obtenido {total_sosp}"

        # 5. Prueba de Exportación a CSV y Excel
        print("\n--- 5. Probando exportación respetando filtros ---")
        # Exportar las sospechosas a CSV
        csv_bytes = ExportService.export_to_csv_stream(db, f_sosp)
        csv_len = len(csv_bytes.getvalue())
        print(f"  - CSV generado para sospechosas: {csv_len} bytes")
        assert csv_len > 0

        # Exportar las sospechosas a Excel .xlsx
        excel_bytes = ExportService.export_to_excel(db, f_sosp)
        excel_len = len(excel_bytes.getvalue())
        print(f"  - Excel .xlsx generado para sospechosas: {excel_len} bytes")
        assert excel_len > 0

        print("\n>>> TODAS LAS PRUEBAS DEL BACKEND Y BASE DE DATOS PASARON EXITOSAMENTE! <<<")

    finally:
        db.close()


if __name__ == "__main__":
    test_full_pipeline()

