from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
import os

load_dotenv() 

class EmailSender:
    
    SMTP_SERVER = "smtp.gmail.com" 
    SMTP_PORT = 587
    # Allow hardcoding by defaults if env vars are missing
    SENDER_EMAIL = os.getenv("EMAIL_USER", "tu_correo@gmail.com") 
    SENDER_PASSWORD = os.getenv("EMAIL_PASS", "tu_app_password")

    @staticmethod
    def send_id_card(to_email, name, pdf_path):
        
        # Debug print to see what's being used
        print(f"📧 Intentando enviar correo desde: {EmailSender.SENDER_EMAIL}")
        
        if "tu_correo" in EmailSender.SENDER_EMAIL:
             print("⚠️ Correos no configurados adecuadamente.")
             return False

        msg = EmailMessage()
        msg['Subject'] = 'Bienvenido a UMG - Tu Carnet Digital'
        msg['From'] = EmailSender.SENDER_EMAIL
        msg['To'] = to_email
        msg.set_content(f"Hola {name},\n\nBienvenido a la Universidad Mariano Gálvez.\nAdjunto encontrarás tu Carnet Digital 2025.\n\nAtentamente,\nRegistro Académico")

        with open(pdf_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(pdf_path)
        
        msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

        try:
            with smtplib.SMTP(EmailSender.SMTP_SERVER, EmailSender.SMTP_PORT) as server:
                server.starttls()
                server.login(EmailSender.SENDER_EMAIL, EmailSender.SENDER_PASSWORD)
                server.send_message(msg)
            print(f"✅ Email enviado a {to_email}")
            return True
        except Exception as e:
            print(f"❌ Error enviando email: {e}")
            return False

    @staticmethod
    def send_attendance_report(to_email, course_name, pdf_path, date_str):
        print(f"📧 Enviando reporte de asistencia a: {to_email}")
        
        if "tu_correo" in EmailSender.SENDER_EMAIL:
             print("⚠️ Correos no configurados. Saltando envío real.")
             return False

        msg = EmailMessage()
        msg['Subject'] = f'Reporte de Asistencia: {course_name} - {date_str}'
        msg['From'] = EmailSender.SENDER_EMAIL
        msg['To'] = to_email
        msg.set_content(f"""Estimado Catedrático,

Adjunto encontrará el reporte oficial de asistencia para el curso:
{course_name}
Fecha: {date_str}

Este documento ha sido generado automáticamente por el Sistema Biométrico UMG.

Atentamente,
Registro Académico
Universidad Mariano Gálvez""")

        try:
            with open(pdf_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(pdf_path)
            
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

            with smtplib.SMTP(EmailSender.SMTP_SERVER, EmailSender.SMTP_PORT) as server:
                server.starttls()
                server.login(EmailSender.SENDER_EMAIL, EmailSender.SENDER_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Reporte enviado exitosamente a {to_email}")
            return True
        except Exception as e:
            print(f"❌ Error enviando reporte: {e}")
            return False
