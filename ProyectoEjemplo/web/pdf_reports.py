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
            
            # Header
            logo_path = Config.ASSETS_DIR / 'logo_umg.png'
            if logo_path.exists():
                try:
                    c.drawImage(str(logo_path), 50, height - 100, width=80, height=80, preserveAspectRatio=True)
                except:
                    pass
            
            # University info
            c.setFont("Helvetica-Bold", 16)
            c.drawString(150, height - 60, "Universidad Mariano Gálvez")
            c.setFont("Helvetica", 12)
            c.drawString(150, height - 80, "Sede Boca del Monte")
            
            # Report title
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width/2, height - 130, "REPORTE DE ASISTENCIA")
            
            # Course information
            curso = attendance_data['curso']
            y_pos = height - 170
            
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y_pos, "Curso:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y_pos, f"{curso['nombre']} ({curso['codigo']})")
            
            y_pos -= 20
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y_pos, "Catedrático:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y_pos, f"{curso.get('catedratico_nombre', '')} {curso.get('catedratico_apellido', '')}")
            
            y_pos -= 20
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y_pos, "Salón:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y_pos, curso.get('salon', 'N/A'))
            
            y_pos -= 20
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y_pos, "Fecha:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y_pos, attendance_data['fecha'].strftime('%d/%m/%Y'))
            
            y_pos -= 20
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y_pos, "Hora de Generación:")
            c.setFont("Helvetica", 11)
            c.drawString(150, y_pos, datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            
            # Statistics
            stats = attendance_data['estadisticas']
            y_pos -= 30
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y_pos, f"Total de Estudiantes: {stats['total']}")
            c.setFillColorRGB(0, 0.5, 0)
            c.drawString(250, y_pos, f"Presentes: {stats['presentes']}")
            c.setFillColorRGB(0.7, 0, 0)
            c.drawString(380, y_pos, f"Ausentes: {stats['ausentes']}")
            c.setFillColorRGB(0, 0, 0)
            c.drawString(480, y_pos, f"({stats['porcentaje_asistencia']:.1f}%)")
            
            # Table header
            y_pos -= 40
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y_pos, "No.")
            c.drawString(80, y_pos, "Carnet")
            c.drawString(180, y_pos, "Nombre Completo")
            c.drawString(380, y_pos, "Email")
            c.drawString(520, y_pos, "Estado")
            
            # Line under header
            y_pos -= 5
            c.line(50, y_pos, width - 50, y_pos)
            
            # Student list
            y_pos -= 20
            c.setFont("Helvetica", 9)
            
            for idx, estudiante in enumerate(attendance_data['estudiantes'], 1):
                if y_pos < 100:  # New page if needed
                    c.showPage()
                    y_pos = height - 50
                    c.setFont("Helvetica", 9)
                
                # Row number
                c.drawString(50, y_pos, str(idx))
                
                # Carnet
                c.drawString(80, y_pos, estudiante['codigo_carnet'])
                
                # Name
                nombre_completo = f"{estudiante['apellido']}, {estudiante['nombre']}"
                if len(nombre_completo) > 25:
                    nombre_completo = nombre_completo[:22] + "..."
                c.drawString(180, y_pos, nombre_completo)
                
                # Email
                email = estudiante['email']
                if len(email) > 20:
                    email = email[:17] + "..."
                c.drawString(380, y_pos, email)
                
                # Status
                if estudiante['presente']:
                    c.setFillColorRGB(0, 0.5, 0)
                    c.drawString(520, y_pos, "PRESENTE")
                else:
                    c.setFillColorRGB(0.7, 0, 0)
                    c.drawString(520, y_pos, "AUSENTE")
                
                c.setFillColorRGB(0, 0, 0)
                y_pos -= 18
            
            # Footer
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(50, 50, f"Generado por Sistema de Control de Asistencia UMG")
            c.drawString(50, 35, f"Documento oficial de asistencia")
            
            # Signature line
            c.line(width - 250, 80, width - 50, 80)
            c.setFont("Helvetica", 9)
            c.drawCentredString(width - 150, 65, "Firma del Catedrático")
            
            c.save()
            logger.info(f"Attendance report generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating attendance report: {e}")
            return False
