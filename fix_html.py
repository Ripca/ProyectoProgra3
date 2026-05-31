import re

file_path = 'c:/Users/VELA/Desktop/Reck2/web/templates/registro_facial.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the tags
content = content.replace("</div                </form>", "</div>\n                </form>")
content = content.replace("</div>/div>", "</div>")
content = re.sub(r'(\s*<div class="mb-3">\s*<label for="tipo_persona".*?Restricción de Ingreso.*?</div>\s*</form>)+', 
                 '\n                    <div class="mb-3">\n                        <label for="tipo_persona" class="form-label">Tipo de Usuario</label>\n                        <select class="form-select" id="tipo_persona" required>\n                            {% for tp in tipos_persona %}\n                            <option value="{{ tp.id }}">{{ tp.nombre }}</option>\n                            {% endfor %}\n                        </select>\n                    </div>\n                    \n                    <div class="mt-3 form-check form-switch border p-2 rounded shadow-sm">\n                        <input class="form-check-input ms-0 me-2" type="checkbox" id="restriccion_ingreso" value="1">\n                        <label class="form-check-label text-danger fw-bold" for="restriccion_ingreso">\n                            <i class="bi bi-exclamation-triangle-fill"></i> Restricción de Ingreso\n                        </label>\n                    </div>\n                </form>', 
                 content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML fixed.")
