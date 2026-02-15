"""
ID Generator Module
Generates QR codes and PDF ID cards for registered persons
"""
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from pathlib import Path
import logging
from config import Config

logger = logging.getLogger(__name__)


class IDGenerator:
    """Generates QR codes and PDF ID cards"""
    
    @staticmethod
    def generate_qr_code(data, output_path):
        """
        Generate QR code from data
        
        Args:
            data: Data to encode in QR code
            output_path: Path to save QR code image
        
        Returns:
            bool: True if successful
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(output_path)
            
            logger.info(f"QR code generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return False
    
    @staticmethod
    def generate_id_card(persona_data, output_path):
        """
        Generate PDF ID card for a person
        
        Args:
            persona_data: Dictionary with person information
            output_path: Path to save PDF file
        
        Returns:
            bool: True if successful
        """
        try:
            # Create canvas
            c = canvas.Canvas(str(output_path), pagesize=letter)
            width, height = letter
            
            # Card dimensions (3.5" x 2.5" - standard ID card size)
            card_width = 3.5 * inch
            card_height = 2.5 * inch
            
            # Center the card on the page
            x_offset = (width - card_width) / 2
            y_offset = height - 2 * inch  # Top of page with margin
            
            # Draw card border
            c.setStrokeColorRGB(0, 0.2, 0.4)  # UMG Blue
            c.setLineWidth(2)
            c.rect(x_offset, y_offset - card_height, card_width, card_height)
            
            # Header background
            c.setFillColorRGB(0, 0.2, 0.4)  # UMG Blue
            c.rect(x_offset, y_offset - 0.6*inch, card_width, 0.6*inch, fill=1, stroke=0)
            
            # UMG Logo
            logo_path = Config.ASSETS_DIR / 'logo_umg.png'
            if logo_path.exists():
                try:
                    c.drawImage(str(logo_path), x_offset + 0.1*inch, y_offset - 0.55*inch, 
                               width=0.5*inch, height=0.5*inch, preserveAspectRatio=True)
                except:
                    logger.warning("Could not load logo image")
            
            # University name
            c.setFillColorRGB(1, 1, 1)  # White
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_offset + 0.7*inch, y_offset - 0.25*inch, "Universidad Mariano Gálvez")
            c.setFont("Helvetica", 8)
            c.drawString(x_offset + 0.7*inch, y_offset - 0.45*inch, "Sede Boca del Monte")
            
            # Photo
            foto_path = persona_data.get('foto_path')
            if foto_path and Path(foto_path).exists():
                try:
                    c.drawImage(str(foto_path), x_offset + 0.1*inch, y_offset - 1.8*inch,
                               width=0.8*inch, height=1.0*inch, preserveAspectRatio=True)
                except Exception as e:
                    logger.warning(f"Could not load photo: {e}")
            
            # Person information
            c.setFillColorRGB(0, 0, 0)  # Black
            y_pos = y_offset - 0.9*inch
            x_text = x_offset + 1.0*inch
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x_text, y_pos, f"{persona_data['nombre']} {persona_data['apellido']}")
            
            y_pos -= 0.2*inch
            c.setFont("Helvetica", 7)
            c.drawString(x_text, y_pos, f"Carnet: {persona_data['codigo_carnet']}")
            
            y_pos -= 0.15*inch
            c.drawString(x_text, y_pos, f"Tipo: {persona_data['tipo_persona'].title()}")
            
            if persona_data.get('carrera'):
                y_pos -= 0.15*inch
                c.drawString(x_text, y_pos, f"Carrera: {persona_data['carrera'][:25]}")
            
            if persona_data.get('seccion'):
                y_pos -= 0.15*inch
                c.drawString(x_text, y_pos, f"Sección: {persona_data['seccion']}")
            
            y_pos -= 0.15*inch
            c.setFont("Helvetica", 6)
            c.drawString(x_text, y_pos, f"Email: {persona_data['email'][:30]}")
            
            # QR Code
            qr_temp_path = Config.TEMP_DIR / f"qr_{persona_data['codigo_carnet']}.png"
            qr_data = f"UMG-{persona_data['codigo_carnet']}-{persona_data['email']}"
            
            if IDGenerator.generate_qr_code(qr_data, qr_temp_path):
                try:
                    c.drawImage(str(qr_temp_path), x_offset + 2.7*inch, y_offset - 2.3*inch,
                               width=0.7*inch, height=0.7*inch)
                except Exception as e:
                    logger.warning(f"Could not add QR code: {e}")
            
            # Footer
            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(x_offset + 0.1*inch, y_offset - 2.4*inch, 
                        f"Emitido: {persona_data.get('fecha_registro', 'N/A')}")
            
            # Digital signature placeholder
            c.setFont("Helvetica-Oblique", 6)
            c.drawString(x_offset + card_width - 1.2*inch, y_offset - 2.4*inch, "Firma Digital UMG")
            
            # Save PDF
            c.save()
            logger.info(f"ID card generated: {output_path}")
            
            # Clean up temp QR code
            if qr_temp_path.exists():
                qr_temp_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating ID card: {e}")
            return False
    
    @staticmethod
    def generate_complete_id(persona_data):
        """
        Generate complete ID package (QR code + PDF card)
        
        Args:
            persona_data: Dictionary with person information
        
        Returns:
            tuple: (success: bool, pdf_path: Path or None)
        """
        try:
            codigo_carnet = persona_data['codigo_carnet']
            
            # Generate PDF ID card
            pdf_path = Config.IDS_DIR / f"ID_{codigo_carnet}.pdf"
            
            success = IDGenerator.generate_id_card(persona_data, pdf_path)
            
            if success:
                return True, pdf_path
            else:
                return False, None
                
        except Exception as e:
            logger.error(f"Error generating complete ID: {e}")
            return False, None
