from web.pdf_reports import PDFReportGenerator
from datetime import datetime, date
from pathlib import Path
import os
import sys

# Mock data
class MockCurso:
    def __getitem__(self, key):
        data = {
            'nombre': 'Introducción a la Programación',
            'codigo': '0900-101',
            'catedratico_nombre': 'Alan',
            'catedratico_apellido': 'Turing',
            'salon': 'Salón 204'
        }
        return data.get(key)
    
    def get(self, key, default=None):
        return self[key] or default

attendance_data = {
    'curso': MockCurso(),
    'fecha': date.today(),
    'estadisticas': {
        'total': 5,
        'presentes': 3,
        'ausentes': 2,
        'porcentaje_asistencia': 60.0
    },
    'estudiantes': [
        {'codigo_carnet': '12345', 'nombre': 'John', 'apellido': 'Doe', 'email': 'jdoe@umg.edu.gt', 'presente': True, 'hora_acceso': datetime.now()},
        {'codigo_carnet': '67890', 'nombre': 'Jane', 'apellido': 'Smith', 'email': 'jsmith@umg.edu.gt', 'presente': False, 'hora_acceso': None},
        {'codigo_carnet': '11223', 'nombre': 'Alice', 'apellido': 'Wonderland', 'email': 'alice@umg.edu.gt', 'presente': True, 'hora_acceso': datetime.now()},
        {'codigo_carnet': '44556', 'nombre': 'Bob', 'apellido': 'Builder', 'email': 'bob@umg.edu.gt', 'presente': True, 'hora_acceso': datetime.now()},
        {'codigo_carnet': '99887', 'nombre': 'Charlie', 'apellido': 'Brown', 'email': 'charlie@umg.edu.gt', 'presente': False, 'hora_acceso': None}
    ]
}

output_path = Path('test_report.pdf')

print("Generating PDF...")
if PDFReportGenerator.generate_attendance_report(attendance_data, output_path):
    print(f"✅ PDF generated successfully at {output_path.absolute()}")
else:
    print("❌ PDF generation failed")
