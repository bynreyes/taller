"""
Reporte por lotes de tareas
task.csv

"""

import yaml
from docxtpl import DocxTemplate, RichText
from datetime import datetime
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configurar logging al inicio
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Constantes
FIELDS = ("uri", "owner", "title", "description", "status")
FOLDER = "tasks"
DATE_NOW = datetime.today().strftime("%d/%m/%Y")

def load_yaml(yaml_path: str) -> List[Dict[str, Any]]:
    """Carga actividades desde archivo YAML"""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            logging.info(f"Cargadas {len(data)} actividades desde YAML")
            return data
    except Exception as e:
        logging.error(f"Error cargando YAML: {e}")
        return []

def load_csv(folder_path: str = FOLDER) -> List[Dict[str, Any]]:
    """Carga tareas desde CSV (igual que antes)"""
    file_path = Path(folder_path) / "tasks.csv"
    tasks_list: List[Dict[str, Any]] = []
    
    if not file_path.exists():
        logging.info("No se encontró CSV existente. Iniciando desde cero.")
        return tasks_list
    
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                if not all(field in row for field in FIELDS):
                    missing = [f for f in FIELDS if f not in row]
                    logging.warning(f"Fila {row_num}: Campos faltantes {missing}")
                    continue
                
                task = {field: row[field] for field in FIELDS}
                tasks_list.append(task)
        
        logging.info(f"Cargadas {len(tasks_list)} tareas desde CSV")
        
    except Exception as e:
        logging.error(f"Error cargando CSV: {e}")
    
    return tasks_list

def generate_reports(task: Dict[str, Any], 
                     actividades: List[Dict[str, Any]],
                     template_path: str = f"{FOLDER}/template.docx",
                     output_folder: str = "reports"
                     ):
    """Genera reportes de Word para cada tarea"""
    if not tasks:
        logging.info("No hay tareas para generar reportes")
        return 
    
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
   
    lista_rt = RichText()  # Crear RichText con la lista de actividades
    for idx, act in enumerate(actividades, 1):
        # Formato: "1. [2025-12-29] instalar git (linux/windows/mac)"
        fecha = datetime.fromisoformat(act['date']).strftime("%d/%m/%Y")
        lista_rt.add(f"{idx}. [{fecha}] {act['activity']}\n", style='List Bullet')
    
    template = DocxTemplate(template_path)
    
    try:
        # Contexto combina task + lista de actividades
        context = task.copy()
        context['lista_actividades'] = lista_rt  # Para Opción 1 {{r lista_actividades}}
        context['actividades'] = actividades     # Para Opción 2 
        context['date_now'] = DATE_NOW
        
        template.render(context)
        
        # Generar nombre de archivo seguro
        safe_owner = "".join(c for c in task['owner'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = "".join(c for c in task['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_owner}_{safe_title}.docx"

        output_file = output_path / filename
        template.save(output_file) 
        logging.info(f"{len(tasks)} Reporte generado: {output_file}") 
            
    except Exception as e:
        logging.error(f"Error generando reporte: {e}")

if __name__ == "__main__":
    tasks = load_csv()
    for task in tasks:
        uri, data = task['uri'], task
        actividades = load_yaml(f"tasks/{uri}.yaml")
        generate_reports(data, actividades)