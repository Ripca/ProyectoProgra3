"""
Email Sender Module
Sends emails with attachments (ID cards, reports)
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import logging
from config import Config

logger = logging.getLogger(__name__)


class EmailSender:
    """Handles email sending functionality"""
    
    @staticmethod
    def send_email(to_email, subject, body, attachment_path=None, html=False):
        """
        Send email with optional attachment
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            attachment_path: Optional path to file to attach
            html: If True, body is HTML content
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # Check if email is configured
        if not Config.SMTP_CONFIG['user'] or not Config.SMTP_CONFIG['password']:
            logger.warning("Email not configured, skipping email send")
            return False, "Email no configurado en el sistema"
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = Config.SMTP_CONFIG['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachment if provided
            if attachment_path and Path(attachment_path).exists():
                filename = Path(attachment_path).name
                
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                msg.attach(part)
                
                logger.info(f"Attached file: {filename}")
            
            # Connect to server and send
            server = smtplib.SMTP(Config.SMTP_CONFIG['server'], Config.SMTP_CONFIG['port'])
            server.starttls()
            server.login(Config.SMTP_CONFIG['user'], Config.SMTP_CONFIG['password'])
            
            text = msg.as_string()
            server.sendmail(Config.SMTP_CONFIG['from_email'], to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False, f"Error al enviar email: {str(e)}"
    
    @staticmethod
    def send_id_card(persona_data, pdf_path):
        """
        Send ID card to person's email
        
        Args:
            persona_data: Dictionary with person information
            pdf_path: Path to PDF ID card
        
        Returns:
            tuple: (success: bool, message: str)
        """
        subject = f"Tu Carnet UMG - {persona_data['codigo_carnet']}"
        
        body = f"""
Estimado/a {persona_data['nombre']} {persona_data['apellido']},

¡Bienvenido/a a la Universidad Mariano Gálvez, Sede Boca del Monte!

Tu registro biométrico ha sido completado exitosamente. Adjunto encontrarás tu carnet de identificación oficial.

Información de tu carnet:
- Código de Carnet: {persona_data['codigo_carnet']}
- Tipo: {persona_data['tipo_persona'].title()}
- Email: {persona_data['email']}

Por favor, imprime este carnet y preséntalo en la entrada de las instalaciones.

El código QR en tu carnet contiene tu información de identificación y puede ser escaneado para verificación rápida.

Atentamente,
Sistema de Registro Biométrico
Universidad Mariano Gálvez
Sede Boca del Monte
"""
        
        return EmailSender.send_email(
            to_email=persona_data['email'],
            subject=subject,
            body=body,
            attachment_path=pdf_path
        )
    
    @staticmethod
    def send_attendance_report(catedratico_email, curso_nombre, pdf_path, fecha):
        """
        Send attendance report to professor
        
        Args:
            catedratico_email: Professor's email
            curso_nombre: Course name
            pdf_path: Path to attendance PDF report
            fecha: Date of attendance
        
        Returns:
            tuple: (success: bool, message: str)
        """
        subject = f"Reporte de Asistencia - {curso_nombre} - {fecha}"
        
        body = f"""
Estimado/a Catedrático/a,

Se ha generado el reporte de asistencia para el curso {curso_nombre} correspondiente a la fecha {fecha}.

El reporte adjunto contiene el listado completo de estudiantes presentes y ausentes.

Este documento constituye el registro oficial de asistencia para esta sesión de clase.

Atentamente,
Sistema de Control de Asistencia
Universidad Mariano Gálvez
Sede Boca del Monte
"""
        
        return EmailSender.send_email(
            to_email=catedratico_email,
            subject=subject,
            body=body,
            attachment_path=pdf_path
        )
    
    @staticmethod
    def test_email_config():
        """
        Test email configuration
        
        Returns:
            bool: True if email is configured
        """
        if not Config.SMTP_CONFIG['user'] or not Config.SMTP_CONFIG['password']:
            logger.warning("Email credentials not configured")
            return False
        
        logger.info("Email configuration appears valid")
        return True
