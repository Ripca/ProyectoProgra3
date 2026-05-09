"""
Registration GUI Module
Tkinter-based interface for person registration
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import logging
from datetime import datetime

from config import Config
from database.models import PersonaDAO, TipoPersonaDAO
from modules.registro.camera_capture import CameraCapture
from modules.registro.face_encoder import FaceEncoder
from modules.registro.id_generator import IDGenerator
from modules.registro.email_sender import EmailSender
from utils.helpers import validate_email, generate_codigo_carnet, safe_filename, hash_password

logger = logging.getLogger(__name__)


class RegistroGUI:
    """Registration GUI application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Registro Biométrico UMG")
        self.root.geometry("700x800")
        
        self.captured_photo_path = None
        self.camera = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text="Registro de Personas", 
                         font=('Helvetica', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=10)
        
        subtitle = ttk.Label(main_frame, text="Universidad Mariano Gálvez - Sede Boca del Monte",
                            font=('Helvetica', 10))
        subtitle.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Form fields
        row = 2
        
        # Nombre
        ttk.Label(main_frame, text="Nombre:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.nombre_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.nombre_var, width=40).grid(row=row, column=1, pady=5)
        row += 1
        
        # Apellido
        ttk.Label(main_frame, text="Apellido:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.apellido_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.apellido_var, width=40).grid(row=row, column=1, pady=5)
        row += 1
        
        # Teléfono
        ttk.Label(main_frame, text="Teléfono:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.telefono_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.telefono_var, width=40).grid(row=row, column=1, pady=5)
        row += 1
        
        # Email
        ttk.Label(main_frame, text="Email UMG:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(main_frame, textvariable=self.email_var, width=40)
        email_entry.grid(row=row, column=1, pady=5)
        ttk.Label(main_frame, text="(debe terminar en @umg.edu.gt)", 
                 font=('Helvetica', 8, 'italic')).grid(row=row+1, column=1, sticky=tk.W)
        row += 2
        
        # Tipo de persona
        self.tipos_persona_list = TipoPersonaDAO.get_all()
        tipos_nombres = [t['nombre'] for t in self.tipos_persona_list] if self.tipos_persona_list else ['estudiante', 'catedrático', 'administrativo', 'operativo']
        
        ttk.Label(main_frame, text="Tipo de Persona:*").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.tipo_var = tk.StringVar()
        tipo_combo = ttk.Combobox(main_frame, textvariable=self.tipo_var, width=37,
                                  values=tipos_nombres)
        tipo_combo.grid(row=row, column=1, pady=5)
        if tipos_nombres:
            tipo_combo.current(0)
        row += 1
        
        # Password (for catedráticos and admin)
        ttk.Label(main_frame, text="Contraseña:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.password_var, width=40, show="*").grid(row=row, column=1, pady=5)
        ttk.Label(main_frame, text="(solo para catedráticos y administrativos)", 
                 font=('Helvetica', 8, 'italic')).grid(row=row+1, column=1, sticky=tk.W)
        row += 2
        
        # Photo section
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(main_frame, text="Fotografía:*", font=('Helvetica', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        # Photo buttons
        photo_frame = ttk.Frame(main_frame)
        photo_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        ttk.Button(photo_frame, text="📷 Capturar con Cámara", 
                  command=self.capture_photo).pack(side=tk.LEFT, padx=5)
        ttk.Button(photo_frame, text="📁 Seleccionar Archivo", 
                  command=self.select_photo_file).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Photo status
        self.photo_status_var = tk.StringVar(value="No se ha capturado ninguna foto")
        self.photo_status_label = ttk.Label(main_frame, textvariable=self.photo_status_var,
                                           foreground="red")
        self.photo_status_label.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        # Buttons
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="✅ Registrar Persona", 
                  command=self.register_person, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="🔄 Limpiar Formulario", 
                  command=self.clear_form).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Cerrar", 
                  command=self.root.quit).pack(side=tk.LEFT, padx=10)
        
        # Status bar
        self.status_var = tk.StringVar(value="Listo para registrar")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def capture_photo(self):
        """Capture photo using webcam"""
        try:
            self.status_var.set("Iniciando cámara...")
            self.root.update()
            
            # Check if camera is available
            if not CameraCapture.is_camera_available():
                messagebox.showerror("Error", "No se detectó ninguna cámara en el sistema")
                self.status_var.set("Error: No hay cámara disponible")
                return
            
            # Create temp photo path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_path = Config.TEMP_DIR / f"capture_{timestamp}.jpg"
            
            # Capture with preview
            camera = CameraCapture()
            success, message, frame = camera.capture_with_preview(photo_path)
            camera.release()
            
            if success:
                # Validate face detection
                face_success, face_message, face_location = FaceEncoder.detect_face_in_image(photo_path)
                
                if not face_success:
                    messagebox.showwarning("Advertencia", face_message)
                    self.status_var.set("Foto capturada pero sin rostro válido")
                    return
                
                self.captured_photo_path = photo_path
                self.photo_status_var.set(f"✓ Foto capturada: {photo_path.name}")
                self.photo_status_label.config(foreground="green")
                self.status_var.set("Foto capturada exitosamente")
                messagebox.showinfo("Éxito", "Foto capturada y validada correctamente")
            else:
                self.status_var.set(f"Error: {message}")
                messagebox.showerror("Error", message)
                
        except Exception as e:
            logger.error(f"Error capturing photo: {e}")
            messagebox.showerror("Error", f"Error al capturar foto: {str(e)}")
            self.status_var.set("Error al capturar foto")
    
    def select_photo_file(self):
        """Select photo from file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Seleccionar Fotografía",
                filetypes=[("Imágenes", "*.jpg *.jpeg *.png"), ("Todos los archivos", "*.*")]
            )
            
            if file_path:
                # Validate face detection
                face_success, face_message, face_location = FaceEncoder.detect_face_in_image(file_path)
                
                if not face_success:
                    messagebox.showwarning("Advertencia", face_message)
                    return
                
                self.captured_photo_path = Path(file_path)
                self.photo_status_var.set(f"✓ Foto seleccionada: {self.captured_photo_path.name}")
                self.photo_status_label.config(foreground="green")
                self.status_var.set("Foto seleccionada y validada")
                
        except Exception as e:
            logger.error(f"Error selecting photo: {e}")
            messagebox.showerror("Error", f"Error al seleccionar foto: {str(e)}")
    
    def validate_form(self):
        """Validate form data"""
        errors = []
        
        if not self.nombre_var.get().strip():
            errors.append("El nombre es obligatorio")
        
        if not self.apellido_var.get().strip():
            errors.append("El apellido es obligatorio")
        
        email = self.email_var.get().strip()
        if not email:
            errors.append("El email es obligatorio")
        elif not validate_email(email, require_umg=True):
            errors.append("El email debe ser válido y terminar en @umg.edu.gt")
        
        if not self.tipo_var.get():
            errors.append("Debe seleccionar un tipo de persona")
        
        if not self.captured_photo_path:
            errors.append("Debe capturar o seleccionar una fotografía")
        
        # Check if email already exists
        if email:
            existing = PersonaDAO.get_by_email(email)
            if existing:
                errors.append(f"El email {email} ya está registrado")
        
        return errors
    
    def register_person(self):
        """Register person in database"""
        try:
            # Validate form
            errors = self.validate_form()
            if errors:
                messagebox.showerror("Errores de Validación", "\n".join(errors))
                return
            
            self.status_var.set("Procesando registro...")
            self.root.update()
            
            # Generate carnet code
            codigo_carnet = generate_codigo_carnet(self.tipo_var.get())
            
            # Save photo permanently
            photo_filename = f"{safe_filename(self.apellido_var.get())}_{safe_filename(self.nombre_var.get())}_{codigo_carnet}.jpg"
            permanent_photo_path = Config.PHOTOS_DIR / photo_filename
            
            import shutil
            shutil.copy(self.captured_photo_path, permanent_photo_path)
            
            # Generate facial encoding
            self.status_var.set("Generando encoding facial...")
            self.root.update()
            
            encoding = FaceEncoder.generate_encoding(str(permanent_photo_path))
            if encoding is None:
                messagebox.showerror("Error", "No se pudo generar el encoding facial")
                return
            
            # Hash password if provided
            password_hash = None
            if self.password_var.get().strip():
                password_hash = hash_password(self.password_var.get())
            
            # Get Tipo de Persona ID
            tipo_nombre = self.tipo_var.get()
            tipo_persona_id = 1 # default
            if self.tipos_persona_list:
                for t in self.tipos_persona_list:
                    if t['nombre'] == tipo_nombre:
                        tipo_persona_id = t['id']
                        break
            
            # Insert into database
            self.status_var.set("Guardando en base de datos...")
            self.root.update()
            
            persona_id = PersonaDAO.create(
                nombre=self.nombre_var.get().strip(),
                apellido=self.apellido_var.get().strip(),
                telefono=self.telefono_var.get().strip() or None,
                email=self.email_var.get().strip(),
                tipo_persona_id=tipo_persona_id,
                foto_path=str(permanent_photo_path),
                firma_path=None,
                encoding_facial=encoding,
                codigo_carnet=codigo_carnet,
                seccion_id=None,
                carrera_id=None,
                password_hash=password_hash
            )
            
            logger.info(f"Person registered with ID: {persona_id}")
            
            # Generate ID card
            self.status_var.set("Generando carnet PDF...")
            self.root.update()
            
            persona_data = {
                'nombre': self.nombre_var.get().strip(),
                'apellido': self.apellido_var.get().strip(),
                'email': self.email_var.get().strip(),
                'tipo_persona': tipo_nombre,
                'carrera': tipo_nombre,
                'seccion': 'N/A',
                'codigo_carnet': codigo_carnet,
                'foto_path': str(permanent_photo_path),
                'fecha_registro': datetime.now().strftime('%d/%m/%Y')
            }
            
            success, pdf_path = IDGenerator.generate_complete_id(persona_data)
            
            if not success:
                messagebox.showwarning("Advertencia", "Persona registrada pero hubo un error al generar el PDF")
                self.status_var.set("Registro completado (sin PDF)")
                return
            
            # Send email
            self.status_var.set("Enviando email...")
            self.root.update()
            
            email_success, email_message = EmailSender.send_id_card(persona_data, pdf_path)
            
            # Show success message
            success_msg = f"""
Registro completado exitosamente!

Código de Carnet: {codigo_carnet}
PDF generado: {pdf_path.name}

Email: {email_message}
"""
            
            messagebox.showinfo("Registro Exitoso", success_msg)
            self.status_var.set("Registro completado exitosamente")
            
            # Clear form
            self.clear_form()
            
        except Exception as e:
            logger.error(f"Error registering person: {e}")
            messagebox.showerror("Error", f"Error al registrar persona: {str(e)}")
            self.status_var.set("Error en el registro")
    
    def clear_form(self):
        """Clear all form fields"""
        self.nombre_var.set("")
        self.apellido_var.set("")
        self.telefono_var.set("")
        self.email_var.set("")
        if hasattr(self, 'tipos_persona_list') and self.tipos_persona_list:
            self.tipo_var.set(self.tipos_persona_list[0]['nombre'])
        else:
            self.tipo_var.set("estudiante")
        self.password_var.set("")
        self.captured_photo_path = None
        self.photo_status_var.set("No se ha capturado ninguna foto")
        self.photo_status_label.config(foreground="red")
        self.status_var.set("Formulario limpiado")


def launch_registration_gui():
    """Launch the registration GUI"""
    root = tk.Tk()
    app = RegistroGUI(root)
    root.mainloop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    launch_registration_gui()
