import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.colaborador_import_service import ColaboradorImportService
from app.services.marcacion_service import MarcacionService
from app.services.export_service import ExportService
from app.schemas.marcacion import MarcacionFilterParams
from app.models.marcacion import Marcacion
from app.models.trabajador import Trabajador


def test_colaboradores_pipeline():
    print("=== INICIANDO PRUEBAS DE IMPORTACIÓN DE COLABORADORES ===")
    db = SessionLocal()
    try:
        # 1. Comprobar estado previo
        marcaciones_pre = db.query(Marcacion).count()
        trabajadores_pre = db.query(Trabajador).count()
        print(f"Estado inicial de la base de datos:")
        print(f"  - Marcaciones en MySQL: {marcaciones_pre}")
        print(f"  - Trabajadores en MySQL: {trabajadores_pre}")
        assert marcaciones_pre == 48601, f"Se esperaban 48601 marcaciones, hay {marcaciones_pre}"
        assert trabajadores_pre in (232, 289), (
            f"Estado inesperado: se esperaban 232 trabajadores (pre-importación) "
            f"o 289 (post-importación), hay {trabajadores_pre}"
        )

        # 2. Primera Importación de Colaboradores Export.xls
        print("\n--- 1. Ejecutando importación de Colaboradores Export.xls ---")
        xls_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datos", "Colaboradores Export.xls"))
        res1 = ColaboradorImportService.import_from_xls(db=db, xls_file_path=xls_path)
        
        print("Resultado de la 1ra importación:")
        print(f"  - Total procesados: {res1['total_procesados']}")
        print(f"  - Trabajadores actualizados (con marcaciones existentes): {res1['trabajadores_actualizados']}")
        print(f"  - Trabajadores nuevos creados (sin marcaciones previas): {res1['trabajadores_creados']}")
        print(f"  - Trabajadores omitidos: {res1['trabajadores_omitidos']}")
        print(f"  - Nombres no disponibles en el archivo: {res1.get('nombres_no_disponibles', 0)}")
        print(f"  - Códigos sin coincidencia: {res1['codigos_sin_coincidencia']}")
        print(f"  - Errores: {res1['errores']}")
        print(f"  - Tiempo de ejecución: {res1['tiempo_segundos']}s")

        assert res1['total_procesados'] == 289, f"Esperado 289, obtenido {res1['total_procesados']}"
        assert res1['codigos_sin_coincidencia'] == 0, f"Esperado 0 sin coincidencia, obtenido {res1['codigos_sin_coincidencia']}"
        assert res1['errores'] == 0, f"Esperado 0 errores, obtenido {res1['errores']}"
        assert res1['nombres_no_disponibles'] == 80, (
            f"Esperado 80 registros sin nombre real (código repetido), obtenido {res1['nombres_no_disponibles']}"
        )

        if trabajadores_pre == 232:
            # Primera ejecución sobre una base con solo los 232 códigos históricos
            assert res1['trabajadores_actualizados'] == 232, f"Esperado 232 actualizados, obtenido {res1['trabajadores_actualizados']}"
            assert res1['trabajadores_creados'] == 57, f"Esperado 57 creados, obtenido {res1['trabajadores_creados']}"
        else:
            # Base ya importada: no debe crear nada; solo puede limpiar nombres inválidos heredados
            assert res1['trabajadores_creados'] == 0, f"Esperado 0 creados, obtenido {res1['trabajadores_creados']}"
            assert res1['trabajadores_actualizados'] + res1['trabajadores_omitidos'] == 289

        # 3. Verificar que las marcaciones siguen exactamente intactas
        marcaciones_post = db.query(Marcacion).count()
        trabajadores_post = db.query(Trabajador).count()
        print(f"\nVerificación de integridad post-importación:")
        print(f"  - Marcaciones en MySQL: {marcaciones_post} (Intactas: {marcaciones_post == marcaciones_pre})")
        print(f"  - Trabajadores totales: {trabajadores_post} (Esperado: 289)")
        assert marcaciones_post == 48601, "ALERTA: Se alteró el total de marcaciones"
        assert trabajadores_post == 289, "ALERTA: El total de trabajadores no coincide con 289"

        # 3b. Ningún trabajador debe conservar el código como nombre
        con_codigo_como_nombre = db.query(Trabajador).filter(Trabajador.nombre == Trabajador.user_id).count()
        assert con_codigo_como_nombre == 0, (
            f"Quedaron {con_codigo_como_nombre} trabajadores con el código repetido como nombre"
        )

        # 4. Prueba de Idempotencia (segunda importación del mismo archivo)
        print("\n--- 2. Probando idempotencia (segunda importación inmediata) ---")
        res2 = ColaboradorImportService.import_from_xls(db=db, xls_file_path=xls_path)
        print("Resultado de la 2da importación (Idempotencia):")
        print(f"  - Total procesados: {res2['total_procesados']}")
        print(f"  - Trabajadores actualizados: {res2['trabajadores_actualizados']}")
        print(f"  - Trabajadores creados: {res2['trabajadores_creados']}")
        print(f"  - Trabajadores omitidos (sin cambios): {res2['trabajadores_omitidos']}")
        print(f"  - Tiempo de ejecución: {res2['tiempo_segundos']}s")

        assert res2['trabajadores_creados'] == 0, f"Error de idempotencia: se crearon {res2['trabajadores_creados']}"
        assert res2['trabajadores_actualizados'] == 0, f"Error de idempotencia: se actualizaron {res2['trabajadores_actualizados']}"
        assert res2['trabajadores_omitidos'] == 289, f"Error: no se omitieron los 289 trabajadores idénticos"

        # 5. Comprobar que las marcaciones ahora tienen el nombre asociado mediante la relación
        print("\n--- 3. Verificando relación Marcacion -> Trabajador ---")
        sample_trabajador = db.query(Trabajador).filter(
            Trabajador.nombre.isnot(None),
            Trabajador.nombre != "",
            Trabajador.total_marcaciones > 0,
        ).first()
        assert sample_trabajador is not None, "No hay trabajadores con nombre y marcaciones asociadas"
        sample_item = db.query(Marcacion).filter(Marcacion.user_id == sample_trabajador.user_id).first()
        assert sample_item is not None
        assert sample_item.trabajador is not None, "La relación trabajador es None"
        assert bool(sample_item.nombre_trabajador), "El nombre del trabajador está vacío"
        assert sample_item.nombre_trabajador != "Sin nombre registrado", "No se asoció el nombre registrado"
        print("  - Relación verificada: Marcacion ID", sample_item.id, "asociada con éxito a su Trabajador.")
        print(f"  - Ejemplo: user_id {sample_item.user_id} -> {sample_item.nombre_trabajador}")

        # 5b. Los 80 registros con el código repetido en "Name" deben mostrar el texto de respaldo
        sin_nombre_count = db.query(Trabajador).filter(
            (Trabajador.nombre.is_(None)) | (Trabajador.nombre == "")
        ).count()
        assert sin_nombre_count == 80, f"Esperado 80 trabajadores sin nombre real, obtenido {sin_nombre_count}"
        codigo_sin_nombre = db.query(Marcacion).filter(Marcacion.user_id == "104").first()
        if codigo_sin_nombre is not None:
            assert codigo_sin_nombre.nombre_trabajador == "Sin nombre registrado"

        # 6. Probar fallback 'Sin nombre registrado' cuando no hay trabajador asociado
        dummy_marcacion = Marcacion(
            user_id="CODIGO_INEXISTENTE_9999",
            timestamp=sample_item.timestamp,
            status=1,
            punch=0,
            fecha_sospechosa=False,
            hash_deduplicacion="dummy_hash_test_verification_fallback",
        )
        assert dummy_marcacion.nombre_trabajador == "Sin nombre registrado", "El fallback debe ser 'Sin nombre registrado'"
        print("  - Fallback verificado: marcación sin trabajador devuelve 'Sin nombre registrado'.")

        # 7. Probar Exportación a Excel y CSV con las nuevas columnas
        print("\n--- 4. Probando exportación a Excel y CSV enriquecida ---")
        f_test = MarcacionFilterParams(user_id="104")
        excel_stream = ExportService.export_to_excel(db, f_test)
        csv_stream = ExportService.export_to_csv_stream(db, f_test)

        assert len(excel_stream.getvalue()) > 0
        assert len(csv_stream.getvalue()) > 0
        csv_content = csv_stream.getvalue().decode("utf-8-sig")
        assert "Nombre del Trabajador" in csv_content, "La cabecera de CSV debe incluir 'Nombre del Trabajador'"
        assert "Departamento" in csv_content, "La cabecera de CSV debe incluir 'Departamento'"
        print(f"  - Exportación Excel generada: {len(excel_stream.getvalue())} bytes")
        print(f"  - Exportación CSV generada: {len(csv_stream.getvalue())} bytes con cabeceras verificadas.")

        print("\n>>> TODAS LAS PRUEBAS DE IMPORTACIÓN DE COLABORADORES Y ASOCIACIÓN PASARON EXITOSAMENTE! <<<")

    finally:
        db.close()


if __name__ == "__main__":
    test_colaboradores_pipeline()

