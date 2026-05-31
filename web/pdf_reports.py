"""
PDF Reports Module
Generates PDF attendance reports
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pathlib import Path
from datetime import datetime
import logging
from config import Config

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generates PDF reports for attendance"""
    
    @staticmethod
    def generate_attendance_report(attendance_data, output_path):
        """
        Generate PDF attendance report
        
        Args:
            attendance_data: Attendance data dictionary
            output_path: Path to save PDF
        
        Returns:
            bool: True if successful
        """
        try:
            c = canvas.Canvas(str(output_path), pagesize=letter)
            width, height = letter
            
            # --- Header ---
            # Logo
            logo_path = Config.ASSETS_DIR / 'LogoUniversidad.png'
            if logo_path.exists():
                try:
                    # Reduced size and adjusted position to avoid overlap
                    c.drawImage(str(logo_path), 40, height - 90, width=60, height=60, preserveAspectRatio=True, mask='auto')
                except:
                    pass
            elif (Config.ASSETS_DIR / 'umg-logo.jpg').exists():
                 try:
                    c.drawImage(str(Config.ASSETS_DIR / 'umg-logo.jpg'), 40, height - 90, width=60, height=60, preserveAspectRatio=True)
                 except:
                    pass

            # University Title
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width/2, height - 50, "UNIVERSIDAD MARIANO GÁLVEZ DE GUATEMALA")
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width/2, height - 70, "FACULTAD DE INGENIERÍA EN SISTEMAS")
            c.setFont("Helvetica", 12)
            c.drawCentredString(width/2, height - 90, "SEDE BOCA DEL MONTE")
            
            # Report Title
            c.setLineWidth(1)
            c.line(40, height - 110, width - 40, height - 110)
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height - 135, "ACTA DE ASISTENCIA OFICIAL")
            
            # --- Course Information Block ---
            curso = attendance_data['curso']
            assignment = attendance_data.get('assignment', {})
            rect_y = height - 230
            c.setStrokeColorRGB(0, 0, 0)
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(40, rect_y, width - 80, 80, fill=1)
            c.setFillColorRGB(0, 0, 0)
            
            # Left Column
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, rect_y + 65, "CURSO:")
            c.setFont("Helvetica", 9)
            c.drawString(100, rect_y + 65, f"{curso['nombre']} [{curso['codigo']}] - Sec {attendance_data.get('seccion', '')}")
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, rect_y + 45, "CATEDRÁTICO:")
            c.setFont("Helvetica", 9)
            c.drawString(130, rect_y + 45, f"{assignment.get('catedratico_nombre', '')} {assignment.get('catedratico_apellido', '')}")
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, rect_y + 25, "CARRERA:")
            c.setFont("Helvetica", 9)
            c.drawString(110, rect_y + 25, str(assignment.get('carrera_nombre', 'N/A')))
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, rect_y + 5, "SALÓN:")
            c.setFont("Helvetica", 9)
            c.drawString(100, rect_y + 5, str(attendance_data.get('salon', 'N/A')))
            
            # Right Column
            c.setFont("Helvetica-Bold", 9)
            c.drawString(350, rect_y + 65, "SEDE:")
            c.setFont("Helvetica", 9)
            c.drawString(390, rect_y + 65, str(assignment.get('sede_nombre', 'N/A')))
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(350, rect_y + 45, "JORNADA:")
            c.setFont("Helvetica", 9)
            c.drawString(410, rect_y + 45, str(assignment.get('jornada_nombre', 'N/A')))
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(350, rect_y + 25, "FECHA:")
            c.setFont("Helvetica", 9)
            c.drawString(400, rect_y + 25, attendance_data['fecha'].strftime('%d de %B de %Y'))
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(350, rect_y + 5, "HORA REPORTE:")
            c.setFont("Helvetica", 9)
            c.drawString(440, rect_y + 5, datetime.now().strftime('%H:%M:%S'))

            # --- Statistics Summary ---
            stats = attendance_data['estadisticas']
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, rect_y - 20, f"TOTAL ESTUDIANTES: {stats['total']}")
            
            c.setFillColorRGB(0, 0.5, 0)
            c.drawString(200, rect_y - 20, f"PRESENTES: {stats['presentes']}")
            
            c.setFillColorRGB(0.7, 0, 0)
            c.drawString(300, rect_y - 20, f"AUSENTES: {stats['ausentes']}")
            
            c.setFillColorRGB(0, 0, 0)
            c.drawString(400, rect_y - 20, f"PORCENTAJE: {stats['porcentaje_asistencia']:.1f}%")

            # --- Table Header ---
            table_y = rect_y - 50
            c.setFillColorRGB(0.1, 0.2, 0.4) # Dark Blue Header
            c.rect(40, table_y - 15, width - 80, 20, fill=1)
            c.setFillColorRGB(1, 1, 1) # White text
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(45, table_y - 10, "No.")
            c.drawString(70, table_y - 10, "CARNET")
            c.drawString(150, table_y - 10, "NOMBRE DEL ESTUDIANTE")
            c.drawString(350, table_y - 10, "HORA ENTRADA")
            c.drawString(480, table_y - 10, "ESTADO")
            
            c.setFillColorRGB(0, 0, 0) # Back to black text
            
            # --- Student Rows ---
            y_pos = table_y - 35
            row_height = 20
            
            for idx, estudiante in enumerate(attendance_data['estudiantes'], 1):
                if y_pos < 50:  # New page needed
                    c.showPage()
                    y_pos = height - 50
                    c.setFont("Helvetica", 9)
                    # Simple header on new page
                    c.drawString(40, y_pos + 10, "Continuación de lista...")
                    y_pos -= 20
                
                # Stripe background
                if idx % 2 == 0:
                    c.setFillColorRGB(0.95, 0.95, 0.95)
                    c.rect(40, y_pos - 5, width - 80, row_height, fill=1, stroke=0)
                    c.setFillColorRGB(0, 0, 0)
                
                c.setFont("Helvetica", 9)
                c.drawString(45, y_pos + 5, str(idx))
                c.drawString(70, y_pos + 5, estudiante['codigo_carnet'])
                
                nombre = f"{estudiante['apellido']}, {estudiante['nombre']}"
                c.drawString(150, y_pos + 5, nombre[:35])
                
                if estudiante['presente'] and estudiante['hora_acceso']:
                    hora = estudiante['hora_acceso'].strftime('%H:%M:%S')
                    c.drawString(350, y_pos + 5, hora)
                else:
                    c.drawString(350, y_pos + 5, "--:--:--")
                    
                if estudiante['presente']:
                    c.setFillColorRGB(0, 0.6, 0)
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(480, y_pos + 5, "PRESENTE")
                else:
                    c.setFillColorRGB(0.8, 0, 0)
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(480, y_pos + 5, "AUSENTE")
                
                c.setFillColorRGB(0, 0, 0) # Reset
                y_pos -= row_height

            # --- Footer / Signature ---
            # Ensure space for signature
            if y_pos < 120:
                c.showPage()
                y_pos = height - 100

            sig_y = y_pos - 60
            c.line(width/2 - 100, sig_y, width/2 + 100, sig_y)
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, sig_y - 15, f"Firma del Catedrático: {curso.get('catedratico_nombre', '')} {curso.get('catedratico_apellido', '')}")
            
            # Bottom footer
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawCentredString(width/2, 30, "Este documento fue generado automáticamente por el Sistema Biométrico UMG")
            c.drawCentredString(width/2, 20, f"ID de Reporte: {datetime.now().strftime('%Y%m%d%H%M%S')}-{course_name_clean(curso['nombre'])}")

            c.save()
            logger.info(f"Attendance report generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating attendance report: {e}")
            return False

def course_name_clean(name):
    return "".join(c for c in name if c.isalnum())

