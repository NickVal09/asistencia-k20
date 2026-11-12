import io
import csv
from datetime import datetime
from typing import Generator
from sqlalchemy.orm import Session
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.schemas.marcacion import MarcacionFilterParams
from app.services.marcacion_service import MarcacionService


class ExportService:
    @staticmethod
    def export_to_csv_stream(db: Session, filters: MarcacionFilterParams) -> io.BytesIO:
        """
        Genera un archivo CSV en memoria con codificación UTF-8 BOM,
        respetando exactamente los filtros aplicados e incorporando el nombre
        del colaborador desde la relación con Trabajador.
        """
        output = io.StringIO()
        # Escribir BOM para compatibilidad directa con Microsoft Excel en español
        output.write("\ufeff")
        
        writer = csv.writer(output, delimiter=",", lineterminator="\r\n")
        
        # Encabezados enriquecidos con nombres y departamentos
        writer.writerow([
            "ID Registro",
            "UID Original",
            "ID Trabajador",
            "Nombre del Trabajador",
            "Departamento",
            "Fecha y Hora",
            "Status Original",
            "Punch Original",
            "Tipo Marcación",
            "Fecha Sospechosa",
            "Motivo Sospecha"
        ])

        query = MarcacionService.aplicar_orden(
            MarcacionService.get_filtered_query(db, filters), filters
        )

        punch_etiquetas = {
            0: "Punch 0 (Tipo 0)",
            1: "Punch 1 (Tipo 1)",
            4: "Punch 4 (Tipo 4)",
            5: "Punch 5 (Tipo 5)",
        }

        # Iterar en lotes para eficiencia de memoria
        for record in query.yield_per(2000):
            writer.writerow([
                record.id,
                record.uid if record.uid is not None else "",
                record.user_id,
                record.nombre_trabajador,
                record.departamento_trabajador,
                record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                record.status,
                record.punch,
                punch_etiquetas.get(record.punch, f"Punch {record.punch}"),
                "SI" if record.fecha_sospechosa else "NO",
                record.motivo_sospecha or "",
            ])

        mem = io.BytesIO()
        mem.write(output.getvalue().encode("utf-8-sig"))
        mem.seek(0)
        return mem

    @staticmethod
    def export_to_excel(db: Session, filters: MarcacionFilterParams) -> io.BytesIO:
        """
        Genera un libro Excel (.xlsx) profesional estilizado con openpyxl,
        incorporando la relación con el Trabajador (nombre y departamento).
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Marcaciones K20"

        # Estilos corporativos
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Azul marino institucional
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
        meta_font = Font(name="Calibri", size=9, italic=True, color="4B5563")
        normal_font = Font(name="Calibri", size=10)
        warning_font = Font(name="Calibri", size=10, bold=True, color="B91C1C")
        unregistered_font = Font(name="Calibri", size=10, italic=True, color="6B7280")
        
        thin_border = Border(
            left=Side(style='thin', color='E5E7EB'),
            right=Side(style='thin', color='E5E7EB'),
            top=Side(style='thin', color='E5E7EB'),
            bottom=Side(style='thin', color='E5E7EB')
        )
        alt_fill = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")

        # Título y Metadata del reporte
        ws["A1"] = "SISTEMA DE CONTROL DE ASISTENCIA K20 - REPORTE DE MARCACIONES"
        ws["A1"].font = title_font
        ws["A2"] = f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Dispositivo: ZKTeco K20 (192.168.10.69)"
        ws["A2"].font = meta_font

        headers = [
            "ID Registro",
            "UID Original",
            "ID Trabajador",
            "Nombre del Trabajador",
            "Departamento",
            "Fecha y Hora",
            "Status Original",
            "Punch Original",
            "Tipo Marcación",
            "Fecha Sospechosa",
            "Motivo Sospecha"
        ]

        row_idx = 4
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        ws.row_dimensions[row_idx].height = 24

        query = MarcacionService.aplicar_orden(
            MarcacionService.get_filtered_query(db, filters), filters
        )

        punch_etiquetas = {
            0: "Punch 0 (Tipo 0)",
            1: "Punch 1 (Tipo 1)",
            4: "Punch 4 (Tipo 4)",
            5: "Punch 5 (Tipo 5)",
        }

        # Poblar filas de datos
        row_idx = 5
        for record in query.yield_per(2000):
            is_alt = (row_idx % 2 == 0)
            nom = record.nombre_trabajador
            dept = record.departamento_trabajador
            
            row_values = [
                record.id,
                record.uid if record.uid is not None else "",
                record.user_id,
                nom,
                dept,
                record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                record.status,
                record.punch,
                punch_etiquetas.get(record.punch, f"Punch {record.punch}"),
                "SI" if record.fecha_sospechosa else "NO",
                record.motivo_sospecha or "",
            ]

            for col_idx, val in enumerate(row_values, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = normal_font
                cell.border = thin_border
                
                # Resaltar fechas sospechosas
                if record.fecha_sospechosa and col_idx in (6, 10, 11):
                    cell.font = warning_font
                    cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                elif col_idx == 4 and nom == "Sin nombre registrado":
                    cell.font = unregistered_font
                elif is_alt:
                    cell.fill = alt_fill

                # Alineación
                if col_idx in (1, 2, 7, 8):
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in (3, 10):
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.alignment = Alignment(horizontal="left")

            row_idx += 1

        # Auto-ajuste de ancho de columnas
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row < 4:
                    continue
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        mem = io.BytesIO()
        wb.save(mem)
        mem.seek(0)
        return mem
