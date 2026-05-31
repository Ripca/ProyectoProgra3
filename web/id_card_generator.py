import os
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import qrcode
from PIL import Image
import tempfile

class IDCardGenerator:
    @staticmethod
    def generate(nombre, apellido, codigo_carnet, carrera, foto_path, firma_path, output_path, qr_data=None):
        """
        Generates a PDF ID Card with Premium Design
        """
        # ID1 Dimensions: 85.60 × 53.98 mm
        card_width = 85.60 * mm
        card_height = 53.98 * mm
        
        c = canvas.Canvas(output_path, pagesize=(card_width, card_height)) 
        
        # --- Design System ---
        UMG_BLUE = HexColor("#003366") # Official-ish Blue
        UMG_GOLD = HexColor("#D4AF37") # Accent
        TEXT_BLACK = HexColor("#222222")
        
        # 1. Background
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, card_width, card_height, fill=1, stroke=0)
        
        # Header Blue Bar
        header_height = 12 * mm
        c.setFillColor(UMG_BLUE)
        c.rect(0, card_height - header_height, card_width, header_height, fill=1, stroke=0)
        
        # Gold Line below header
        c.setStrokeColor(UMG_GOLD)
        c.setLineWidth(1)
        c.line(0, card_height - header_height, card_width, card_height - header_height)

        c.line(0, card_height - header_height, card_width, card_height - header_height)

        logo_path = os.path.join("assets", "LogoUniversidad.png")
        if os.path.exists(logo_path):
            logo_size = 10 * mm
            # Position: Inside header bar, left aligned
            c.drawImage(logo_path, 2 * mm, card_height - 11 * mm, width=logo_size, height=logo_size, mask='auto', preserveAspectRatio=True)

        # 2. Header Text (White) - Adjusted position to be next to logo
        c.setFillColorRGB(1, 1, 1) # White
        c.setFont("Helvetica-Bold", 11) # Slightly smaller
        # Center between logo end and card end Or just fixed offset.
        # Logo ends at 12mm. 
        c.drawString(14 * mm, card_height - 6 * mm, "UNIVERSIDAD MARIANO GÁLVEZ")
        c.setFont("Helvetica", 7)
        c.drawString(14 * mm, card_height - 9.5 * mm, "GUATEMALA")

        # 4. Photo (Left Side)
        c.setStrokeColor(UMG_BLUE)
        c.setLineWidth(0.5)
        # Define Photo Box
        photo_w = 22 * mm
        photo_h = 28 * mm
        photo_x = 5 * mm
        photo_y = 12 * mm 
        
        # No border rect as requested
        # c.rect(photo_x, photo_y, photo_w, photo_h, stroke=1, fill=0)
        
        if foto_path and os.path.exists(foto_path):
            # Center photo in box
            # We want to fill the width mostly
            c.drawImage(foto_path, photo_x + 0.5*mm, photo_y + 0.5*mm, width=photo_w - 1*mm, height=photo_h - 1*mm, preserveAspectRatio=True, anchor='c')

        # 5. Student Details (Center - Right)
        text_x = 32 * mm # Right of photo
        text_y = card_height - header_height - 6 * mm
        
        c.setFillColor(TEXT_BLACK)
        
        # Name
        c.setFont("Helvetica-Bold", 11)
        # Check text length to fit
        fullname = f"{nombre} {apellido}"
        if len(fullname) > 25:
             c.setFont("Helvetica-Bold", 9)
        c.drawString(text_x, text_y, nombre)
        c.drawString(text_x, text_y - 4.5*mm, apellido)
        
        # Info Block
        info_y = text_y - 10 * mm
        c.setFont("Helvetica-Bold", 6)
        c.setFillColor(UMG_BLUE)
        c.drawString(text_x, info_y, "CARRERA:")
        
        c.setFont("Helvetica", 7)
        c.setFillColor(TEXT_BLACK)
        # Multi-line career if too long
        if len(carrera) > 30:
            c.setFont("Helvetica", 6)
            c.drawString(text_x, info_y - 3*mm, carrera[:35])
            c.drawString(text_x, info_y - 5.5*mm, carrera[35:])
            info_y -= 2.5*mm
        else:
            c.drawString(text_x, info_y - 3*mm, carrera)
            
        info_y -= 8 * mm
        
        # ID / Carnet
        c.setFont("Helvetica-Bold", 6)
        c.setFillColor(UMG_BLUE)
        c.drawString(text_x, info_y, "CARNET:")
        
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_BLACK)
        c.drawString(text_x, info_y - 3.5*mm, codigo_carnet)

        # 6. QR Code (Moved to Top Right - Optimized)
        qr_size = 14 * mm
        qr_x = card_width - qr_size - 4 * mm
        qr_y = 20 * mm # Balanced position (was 25mm, too high)
        
        qr_content = qr_data if qr_data else codigo_carnet
        
        qr = qrcode.QRCode(box_size=10, border=0)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        temp_qr_path = tempfile.mktemp(suffix=".png")
        img_qr.save(temp_qr_path)
        
        c.drawImage(temp_qr_path, qr_x, qr_y, width=qr_size, height=qr_size)
        os.remove(temp_qr_path)

        # 7. Signature (Bottom Center-Left)
        # Position between Photo and QR
        # photo ends at 5mm + 22mm = 27mm. QR starts around 85-17=68mm.
        # Space avaiable: 30mm to 65mm. Center ~ 47mm.
        
        sig_x = 35 * mm
        sig_y = 4 * mm 
        sig_w = 25 * mm
        sig_h = 8 * mm
        
        if firma_path and os.path.exists(firma_path):
             c.drawImage(firma_path, sig_x, sig_y, width=sig_w, height=sig_h, mask='auto', preserveAspectRatio=True, anchor='s')
        
        c.setLineWidth(0.3)
        c.setStrokeColor(HexColor("#999999"))
        c.line(sig_x, sig_y, sig_x + sig_w, sig_y) # Line under signature
        c.setFont("Helvetica", 4)
        c.drawCentredString(sig_x + sig_w/2, sig_y - 2*mm, "FIRMA DEL ALUMNO")

        # 8. Footer Year (Vertical or small corner)
        c.setFillColor(UMG_BLUE)
        c.setFont("Helvetica-Bold", 6)
        c.drawRightString(card_width - 3*mm, card_height - header_height - 3*mm, "2025")

        c.save()
        return True
