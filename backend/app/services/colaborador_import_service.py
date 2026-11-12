import os
import time
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from sqlalchemy.orm import Session
import xlrd

from app.models.trabajador import Trabajador
from app.models.marcacion import Marcacion
from app.models.ejecucion import EjecucionSincronizacion
from app.core.config import settings


class ColaboradorImportService:
    @staticmethod
    def _nombre_valido(nombre_raw: str, ac_no: str) -> Optional[str]:
        """
        Devuelve el nombre solo si el archivo aporta un valor real.
        El export de ZLM60_TFT repite el código en la columna Name en algunos
        registros (p. ej. AC No. 104 con Name "104"); esos casos se consideran
        nombre no disponible en lugar de mostrarse como nombre de la persona.
        """
        nombre = (nombre_raw or "").strip()
        if not nombre:
            return None
        if nombre == ac_no:
            return None
        if nombre.isdigit() and ac_no.isdigit() and int(nombre) == int(ac_no):
            return None
        return nombre

    @staticmethod
    def import_from_xls(
        db: Session,
        xls_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Importa trabajadores desde el archivo Excel .xls (ZLM60_TFT) hacia MySQL.
        - Detecta y lee formato BIFF8 con xlrd y codificación cp1252.
        - Relaciona los colaboradores con las marcaciones existentes usando AC No. <-> user_id.
        - Conserva identificadores como texto con ceros a la izquierda.
        - Actualiza trabajadores existentes sin eliminar marcaciones originales.
        - Registra diferencias si un nombre confirmado cambia.
        - Crea trabajadores nuevos que no tienen marcaciones previas.
        - Es completamente idempotente: ejecuciones repetidas omiten registros sin cambios.
        - Cumple con no exponer datos personales en logs ni auditorías.
        """
        start_time = time.time()

        # 1. Resolver ruta del archivo .xls
        target_path = xls_file_path
        if not target_path:
            # Buscar en carpeta datos/
            posibles_rutas = [
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "datos", "Colaboradores Export.xls")),
                os.path.abspath("C:/Proyectos/asistencia-k20/datos/Colaboradores Export.xls"),
                os.path.abspath("datos/Colaboradores Export.xls"),
            ]
            for p in posibles_rutas:
                if os.path.exists(p):
                    target_path = p
                    break

        if not target_path or not os.path.exists(target_path):
            raise FileNotFoundError(f"No se encontró el archivo de colaboradores en: {target_path}")

        # 2. Registrar inicio de ejecución en auditoría
        ejecucion = EjecucionSincronizacion(
            origen="xls_colaboradores",
            archivo_nombre=os.path.basename(target_path),
            estado="en_progreso",
            iniciado_el=datetime.utcnow(),
        )
        db.add(ejecucion)
        db.commit()
        db.refresh(ejecucion)

        total_procesados = 0
        trabajadores_creados = 0
        trabajadores_actualizados = 0
        trabajadores_omitidos = 0
        nombres_no_disponibles = 0
        errores_count = 0
        diferencias_detectadas: List[Dict[str, Any]] = []

        try:
            # 3. Abrir archivo con xlrd usando encoding_override para caracteres en español (cp1252)
            workbook = xlrd.open_workbook(target_path, encoding_override="cp1252")
            sheet = workbook.sheet_by_index(0)

            if sheet.nrows < 1:
                raise ValueError("El archivo Excel está vacío.")

            # Identificar encabezados dinámicamente
            headers = [str(sheet.cell_value(0, c)).strip() for c in range(sheet.ncols)]
            
            try:
                ac_col = headers.index("AC No.")
            except ValueError:
                raise ValueError("Columna requerida 'AC No.' no encontrada en los encabezados del archivo Excel.")

            try:
                name_col = headers.index("Name")
            except ValueError:
                raise ValueError("Columna requerida 'Name' no encontrada en los encabezados del archivo Excel.")

            dept_col = headers.index("department") if "department" in headers else -1

            # 4. Obtener universo de user_id en marcaciones para calcular códigos sin coincidencia
            marcaciones_user_ids: Set[str] = set(
                u[0] for u in db.query(Marcacion.user_id).distinct().all()
            )

            # Cargar trabajadores existentes en memoria para actualización rápida O(1)
            trabajadores_db = {t.user_id: t for t in db.query(Trabajador).all()}
            ac_nos_en_archivo: Set[str] = set()

            # 5. Iterar filas de trabajadores
            for row_idx in range(1, sheet.nrows):
                total_procesados += 1
                try:
                    cell_ac = sheet.cell(row_idx, ac_col)
                    # Tratamiento estricto de AC No. como texto conservando ceros iniciales
                    if cell_ac.ctype == xlrd.XL_CELL_NUMBER:
                        ac_no = str(int(cell_ac.value)).strip()
                    else:
                        ac_no = str(cell_ac.value).strip()

                    if not ac_no:
                        # Fila vacía, omitir
                        continue

                    ac_nos_en_archivo.add(ac_no)

                    nombre_raw = str(sheet.cell_value(row_idx, name_col)).strip()
                    departamento_raw = (
                        str(sheet.cell_value(row_idx, dept_col)).strip()
                        if dept_col >= 0
                        else None
                    )
                    departamento_val = departamento_raw if departamento_raw else None

                    # El export puede repetir el código en "Name": se guarda como nombre no disponible
                    nombre_val = ColaboradorImportService._nombre_valido(nombre_raw, ac_no)
                    if nombre_val is None:
                        nombres_no_disponibles += 1

                    # Comprobar si el trabajador ya existe en la base de datos
                    if ac_no in trabajadores_db:
                        trabajador = trabajadores_db[ac_no]

                        nombre_actual_raw = (trabajador.nombre or "").strip()
                        # Un nombre igual al código es un dato inválido heredado de importaciones previas
                        nombre_actual = ColaboradorImportService._nombre_valido(nombre_actual_raw, ac_no)
                        dept_actual = (trabajador.departamento or "").strip() or None
                        hubo_cambios = False

                        if nombre_val is not None and nombre_val != nombre_actual:
                            # Registrar diferencia detectada para trazabilidad (sin exponer nombres)
                            diferencias_detectadas.append({
                                "user_id": ac_no,
                                "cambio_nombre": True,
                                "cambio_departamento": dept_actual != departamento_val,
                            })
                            trabajador.nombre = nombre_val
                            hubo_cambios = True
                        elif nombre_val is None and nombre_actual_raw and nombre_actual is None:
                            # Limpieza: el nombre almacenado era en realidad el código del trabajador
                            trabajador.nombre = None
                            hubo_cambios = True

                        if dept_actual != departamento_val:
                            trabajador.departamento = departamento_val
                            hubo_cambios = True

                        if hubo_cambios:
                            trabajadores_actualizados += 1
                        else:
                            # Idéntico: omitir para garantizar idempotencia
                            trabajadores_omitidos += 1
                    else:
                        # Trabajador nuevo (por ejemplo, colaborador sin marcaciones previas en este corte)
                        nuevo_trabajador = Trabajador(
                            user_id=ac_no,
                            nombre=nombre_val,
                            departamento=departamento_val,
                            activo=True,
                            total_marcaciones=0,
                        )
                        db.add(nuevo_trabajador)
                        trabajadores_db[ac_no] = nuevo_trabajador
                        trabajadores_creados += 1

                except Exception as row_error:
                    errores_count += 1
                    continue

            # 6. Confirmar cambios en la base de datos
            db.commit()

            # 7. Calcular marcaciones cuyos user_id no figuran en este archivo XLS
            codigos_sin_coincidencia = len(marcaciones_user_ids - ac_nos_en_archivo)

            duration = round(time.time() - start_time, 2)

            # 8. Actualizar auditoría de ejecución (sin exponer datos personales en logs)
            detalle_resumen = (
                f"Importación de colaboradores finalizada en {duration}s. "
                f"Procesados: {total_procesados}, Creados: {trabajadores_creados}, "
                f"Actualizados: {trabajadores_actualizados}, Omitidos (sin cambios): {trabajadores_omitidos}, "
                f"Nombres no disponibles en el archivo (código repetido): {nombres_no_disponibles}, "
                f"Marcaciones sin coincidencia en archivo: {codigos_sin_coincidencia}, "
                f"Diferencias registradas: {len(diferencias_detectadas)}, Errores: {errores_count}."
            )

            ejecucion.estado = "completado"
            ejecucion.total_leidos = total_procesados
            ejecucion.nuevos_registros = trabajadores_creados
            ejecucion.duplicados_omitidos = trabajadores_omitidos
            ejecucion.fechas_sospechosas_detectadas = codigos_sin_coincidencia
            ejecucion.errores = errores_count
            ejecucion.mensaje_detalle = detalle_resumen
            ejecucion.finalizado_el = datetime.utcnow()
            db.commit()

            return {
                "ejecucion_id": ejecucion.id,
                "estado": "completado",
                "archivo": os.path.basename(target_path),
                "total_procesados": total_procesados,
                "trabajadores_creados": trabajadores_creados,
                "trabajadores_actualizados": trabajadores_actualizados,
                "trabajadores_omitidos": trabajadores_omitidos,
                "nombres_no_disponibles": nombres_no_disponibles,
                "codigos_sin_coincidencia": codigos_sin_coincidencia,
                "errores": errores_count,
                "diferencias_detectadas_count": len(diferencias_detectadas),
                "mensaje_detalle": detalle_resumen,
                "tiempo_segundos": duration,
            }

        except Exception as e:
            db.rollback()
            duration = round(time.time() - start_time, 2)
            ejecucion.estado = "fallido"
            ejecucion.mensaje_detalle = f"Fallo al procesar archivo de colaboradores: {str(e)}"
            ejecucion.finalizado_el = datetime.utcnow()
            db.commit()
            raise e

