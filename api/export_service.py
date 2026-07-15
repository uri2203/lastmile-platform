"""
LAST MILE DELIVERY - Export Service
CSV and PDF export with branded templates.
"""

import os
import csv
import io
import logging
from datetime import datetime

logger = logging.getLogger('lastmile.export')


class ExportService:
    def __init__(self):
        self.company_name = os.environ.get('COMPANY_NAME', 'Last Mile Delivery')
        self.company_logo = os.environ.get('COMPANY_LOGO', '')

    def to_csv(self, data, columns, filename=None):
        """Export data to CSV format."""
        if not data:
            return {'success': False, 'error': 'No data to export'}

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()

        for row in data:
            filtered_row = {col: row.get(col, '') for col in columns}
            writer.writerow(filtered_row)

        if not filename:
            filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return {
            'success': True,
            'content': output.getvalue(),
            'filename': filename,
            'content_type': 'text/csv'
        }

    def to_pdf(self, data, columns, title='Reporte', filename=None, totals=None):
        """Export data to PDF format with branded header."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, mm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        except ImportError:
            return {'success': False, 'error': 'reportlab not installed'}

        if not data:
            return {'success': False, 'error': 'No data to export'}

        if not filename:
            filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                topMargin=30*mm, bottomMargin=20*mm,
                                leftMargin=15*mm, rightMargin=15*mm)

        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                     fontSize=16, spaceAfter=6)
        elements.append(Paragraph(title, title_style))

        # Subtitle
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                        fontSize=10, textColor=colors.grey,
                                        spaceAfter=20)
        elements.append(Paragraph(
            f'{self.company_name} | {datetime.now().strftime("%d/%m/%Y %H:%M")}',
            subtitle_style
        ))

        # Table data
        header = columns.values()
        table_data = [list(header)]

        for row in data:
            table_row = [str(row.get(col_key, '')) for col_key in columns.keys()]
            table_data.append(table_row)

        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e5ed')),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ]))

        elements.append(table)

        # Totals
        if totals:
            elements.append(Spacer(1, 20))
            total_style = ParagraphStyle('Total', parent=styles['Normal'],
                                         fontSize=11, alignment=TA_RIGHT, spaceAfter=4)
            for label, value in totals.items():
                elements.append(Paragraph(f'<b>{label}:</b> {value}', total_style))

        # Footer
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                      fontSize=8, textColor=colors.grey,
                                      alignment=TA_CENTER)
        elements.append(Paragraph(
            f'Generado por {self.company_name} - {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}',
            footer_style
        ))

        doc.build(elements)

        return {
            'success': True,
            'content': buffer.getvalue(),
            'filename': filename,
            'content_type': 'application/pdf'
        }


# Export configurations for each entity
EXPORT_CONFIGS = {
    'pedidos': {
        'title': 'Reporte de Pedidos',
        'columns': {
            'PED_ID': 'ID',
            'PED_NUMERO': 'Folio',
            'PED_CLIENTE_NOMBRE': 'Cliente',
            'PED_DESTINO_DIR': 'Destino',
            'PED_DESTINO_COL': 'Colonia',
            'PED_DESTINO_CIUDAD': 'Ciudad',
            'PED_ESTADO': 'Estado',
            'PED_BULTOS': 'Bultos',
            'PED_PESO_KG': 'Peso (kg)',
            'PED_COSTO_TOTAL': 'Costo Total',
            'PED_FORMA_PAGO': 'Forma Pago',
            'PED_FECHA_PEDIDO': 'Fecha Pedido',
            'PED_PRIORIDAD': 'Prioridad',
        }
    },
    'clientes': {
        'title': 'Reporte de Clientes',
        'columns': {
            'CLI_ID': 'ID',
            'CLI_RAZON_SOCIAL': 'Razon Social',
            'CLI_RFC': 'RFC',
            'CLI_CONTACTO': 'Contacto',
            'CLI_EMAIL': 'Email',
            'CLI_TELEFONO': 'Telefono',
            'CLI_TIPO_CLIENTE': 'Tipo',
            'CLI_ESTATUS': 'Estatus',
            'CLI_CIUDAD': 'Ciudad',
            'CLI_ESTADO': 'Estado',
        }
    },
    'choferes': {
        'title': 'Reporte de Choferes',
        'columns': {
            'CHO_ID': 'ID',
            'CHO_NOMBRE': 'Nombre',
            'CHO_APELLIDO': 'Apellido',
            'CHO_TELEFONO': 'Telefono',
            'CHO_EMAIL': 'Email',
            'CHO_LICENCIA': 'Licencia',
            'CHO_TIPO': 'Tipo',
            'CHO_ESTATUS': 'Estatus',
            'CHO_RFC': 'RFC',
        }
    },
    'vehiculos': {
        'title': 'Reporte de Vehiculos',
        'columns': {
            'VEH_ID': 'ID',
            'VEH_UNIDAD': 'Unidad',
            'VEH_PLACAS': 'Placas',
            'VEH_TIPO': 'Tipo',
            'VEH_MARCA': 'Marca',
            'VEH_MODELO': 'Modelo',
            'VEH_ANIO': 'Anio',
            'VEH_KM': 'KM',
            'VEH_ESTATUS': 'Estatus',
        }
    },
    'usuarios': {
        'title': 'Reporte de Usuarios',
        'columns': {
            'USU_ID': 'ID',
            'USU_NOMBRE': 'Nombre',
            'USU_USUARIO': 'Usuario',
            'USU_EMAIL': 'Email',
            'USU_ROL': 'Rol',
            'USU_ACTIVO': 'Activo',
        }
    },
    'pagos': {
        'title': 'Reporte de Pagos',
        'columns': {
            'TRP_ID': 'ID',
            'PED_ID': 'Pedido',
            'TRP_MONTO': 'Monto',
            'TRP_METODO': 'Metodo',
            'TRP_REFERENCIA': 'Referencia',
            'TRP_ESTATUS': 'Estatus',
            'TRP_FECHA_REGISTRO': 'Fecha',
        }
    },
    'facturas': {
        'title': 'Reporte de Facturas',
        'columns': {
            'CFDI_ID': 'ID',
            'CFDI_FOLIO': 'Folio',
            'CFDI_UUID': 'UUID',
            'CFDI_CLIENTE': 'Cliente',
            'CFDI_RFC': 'RFC',
            'CFDI_IMPORTE': 'Importe',
            'CFDI_ESTADO': 'Estado',
            'CFDI_FECHA_EMISION': 'Fecha Emision',
        }
    }
}


# Singleton
export_service = ExportService()
