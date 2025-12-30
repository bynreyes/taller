"""
version: 0.2
name: todo-list.py
author: nreyes

description:
TODO List Application 
A simple command-line TODO list application to manage tasks.

what was learned:
- usage of namedtuple for structured data
- basic logging for error handling
- decorators for save functionality
- basic yml serialization and deserialization
- basic .csv handling for data persistence
- basic CRUD operations in a command-line app
"""

from collections import namedtuple, defaultdict
from functools import wraps
from datetime import datetime
from tabulate import tabulate
import logging
import os
import csv
import yaml
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Estructuras de datos
Task = namedtuple(
    "Task",
    "id owner title description priority uri status created_at finished_at",
    defaults=("IN PROGRESS", None, None)
)
Entry = namedtuple("Entry", "date action activity")

# Variables globales
FOLDER = "tasks"
dict_tasks = {}
history = defaultdict(list)
next_id = 1000

# Utilidades
def get_date():
    return datetime.now().isoformat()

def find_task(task_id):
    """Busca una tarea por ID"""
    task = dict_tasks.get(int(task_id))
    if not task:
        logging.warning(f"Task with ID:{task_id} not found.")
    return task

# Decorador para tabular salida
def tabulate_print(func):
    """Decorator to print data in tabulate format"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            data = func(*args, **kwargs)
            if not data:
                print("No data to display.")
                return data
            
            # Lista de diccionarios
            if isinstance(data, list) and isinstance(data[0], dict):
                print(tabulate(data, headers='keys'))
            # Lista de namedtuples (Task o Entry)
            elif isinstance(data, list) and hasattr(data[0], '_asdict'):
                dicts = [item._asdict() for item in data]
                print(tabulate(dicts, headers='keys'))
            else:
                print(data)
                
            return data
        except Exception as e:
            logging.error(f"Error displaying data: {e}")
            return None
    return wrapper

# Persistencia CSV
def load_csv():
    """Carga tareas desde CSV"""
    global next_id
    file_path = os.path.join(FOLDER, "tasks.csv")
    tasks = {}
    
    if not os.path.exists(file_path):
        logging.info("No existing CSV found. Starting fresh.")
        return tasks
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('id') and row.get('title'):
                    task = Task(
                        id=int(row['id']),
                        owner=row['owner'].strip(),
                        title=row['title'].strip(),
                        description=row.get('description', '').strip(),
                        priority=row['priority'].strip().upper(),
                        uri=row['uri'].strip(),
                        status=row.get('status', 'IN PROGRESS'),
                        created_at=row.get('created_at', ''),
                        finished_at=row.get('finished_at', ''),
                    )
                    tasks[task.id] = task
        
        # Actualizar next_id
        if tasks:
            next_id = max(tasks.keys()) + 1
            
        logging.info(f"Loaded {len(tasks)} tasks from CSV")
    except Exception as e:
        logging.error(f"Error loading CSV: {e}")
    
    return tasks

def save_csv():
    """Guarda tareas en CSV"""
    os.makedirs(FOLDER, exist_ok=True)
    file_path = os.path.join(FOLDER, "tasks.csv")
    
    try:
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            if dict_tasks:
                fieldnames = Task._fields
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for task in dict_tasks.values():
                    writer.writerow(task._asdict())
        logging.info(f"Saved {len(dict_tasks)} tasks to CSV")
    except Exception as e:
        logging.error(f"Error saving CSV: {e}")

# Persistencia YAML (historial)
def load_history(task_id):
    """Carga historial de una tarea desde YAML"""
    uri = dict_tasks[task_id].uri
    file_path = os.path.join(FOLDER, f"{uri}.yaml")
    
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or []
            return [Entry(**item) for item in data]
    except Exception as e:
        logging.error(f"Error loading history: {e}")
        return []

def save_history(task_id):
    """Guarda historial de una tarea en YAML"""
    if task_id not in dict_tasks:
        return
    
    os.makedirs(FOLDER, exist_ok=True)
    uri = dict_tasks[task_id].uri
    file_path = os.path.join(FOLDER, f"{uri}.yaml")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            data = [entry._asdict() for entry in history[task_id]]
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    except Exception as e:
        logging.error(f"Error saving history: {e}")

# Operaciones CRUD
def add_task():
    """Agregar nueva tarea"""
    global next_id
    
    owner = input("Enter the owner of the task: ").strip()
    title = input("Enter the title of the task: ").strip()
    description = input("Enter the description of the task: ").strip()
    
    priority_map = {"1": "LOW", "2": "MEDIUM", "3": "HIGH"}
    print("\nPriority options:")
    for key, value in priority_map.items():
        print(f"  {key} --> {value}")
    
    priority_choice = input("Select priority (1-3): ").strip()
    priority = priority_map.get(priority_choice, "LOW")
    
    uri = f"{owner.replace(' ', '_')}_{next_id}"
    task = Task(
        id=next_id,
        owner=owner,
        title=title,
        description=description,
        priority=priority,
        uri=uri,
        status="IN PROGRESS",
        created_at=get_date(),
        finished_at=None
    )
    
    dict_tasks[next_id] = task
    history[next_id].append(Entry(
        date=get_date(),
        action='CREATED',
        activity=f"Task '{title}' created"
    ))
    
    print(f"\n✓ Task {next_id} added successfully!")
    next_id += 1

def update_task():
    """Actualizar tarea existente"""
    task_id = int(input("Enter task ID to update: "))
    task = find_task(task_id)
    if not task:
        return
    
    print(f"\nCurrent values (press Enter to keep):")
    title = input(f"Title [{task.title}]: ").strip() or task.title
    description = input(f"Description [{task.description}]: ").strip() or task.description
    owner = input(f"Owner [{task.owner}]: ").strip() or task.owner
    
    uri = f"{owner.replace(' ', '_')}_{task_id}"
    updated_task = task._replace(
        title=title,
        description=description,
        owner=owner,
        uri=uri
    )
    
    dict_tasks[task_id] = updated_task
    history[task_id].append(Entry(
        date=get_date(),
        action='UPDATED',
        activity=f"Task updated: {title}"
    ))
    
    print(f"\n✓ Task {task_id} updated successfully!")

def add_entry():
    """Agregar entrada al historial de una tarea"""
    task_id = int(input("Enter task ID for entry: "))
    task = find_task(task_id)
    
    if not task:
        return
    
    activity = input("Enter activity details:\n").strip()
    
    history[task_id].append(Entry(
        date=get_date(),
        action='ENTRY',
        activity=activity
    ))
    
    print(f"\n✓ Entry added to task {task_id}")

def finalize_task():
    """Finalizar tarea"""
    task_id = int(input("Enter task ID to finish: "))
    task = find_task(task_id)
    
    if not task:
        return
    
    if task.status in ['SUCCESS', 'FAILED']:
        print("Task already completed.")
        return
    
    while True:
        status = input("Task completion (SUCCESS/FAILED): ").strip().upper()
        if status in ['SUCCESS', 'FAILED']:
            break
        print("Invalid input. Please enter 'SUCCESS' or 'FAILED'.")
    
    comment = input("Enter comments: ").strip()
    
    updated_task = task._replace(
        status=status,
        finished_at=get_date()
    )
    dict_tasks[task_id] = updated_task
    
    history[task_id].append(Entry(
        date=get_date(),
        action='COMPLETED',
        activity=f"Task marked as {status}. Comment: {comment}"
    ))
    
    print(f"\n✓ Task {task_id} finished as {status}!")

@tabulate_print
def view_tasks():
    """Ver todas las tareas con filtro opcional"""
    print("\nFilter options: ALL, IN PROGRESS, DONE, SUCCESS, FAILED")
    status_filter = input("Enter filter (or press Enter for ALL): ").strip().upper() or "ALL"
    
    if status_filter == "ALL":
        return list(dict_tasks.values())
    elif status_filter == "IN PROGRESS":
        return [t for t in dict_tasks.values() if t.status == "IN PROGRESS"]
    elif status_filter == "DONE":
        return [t for t in dict_tasks.values() if t.status in ("SUCCESS", "FAILED")]
    elif status_filter == "SUCCESS":
        return [t for t in dict_tasks.values() if t.status == "SUCCESS"]
    elif status_filter == "FAILED":
        return [t for t in dict_tasks.values() if t.status == "FAILED"]
    else:
        print("Invalid filter. Showing all tasks.")
        return list(dict_tasks.values())

@tabulate_print
def view_history():
    """Ver historial de una tarea"""
    task_id = int(input("Enter task ID to view history: "))
    if not find_task(task_id):
        return None
    
    return history[task_id] if history[task_id] else []

def exit_app():
    """Guardar y salir"""
    print("\nSaving data...")
    save_csv()
    
    for task_id in history.keys():
        if history[task_id]:
            save_history(task_id)
    
    print("✓ Data saved successfully. Goodbye!")
    sys.exit(0)

# Menú principal
def main():
    """Función principal"""
    global dict_tasks
    
    # Cargar datos existentes
    os.makedirs(FOLDER, exist_ok=True)
    dict_tasks = load_csv()
    
    # Cargar historiales
    for task_id in dict_tasks.keys():
        loaded_history = load_history(task_id)
        if loaded_history:
            history[task_id] = loaded_history
    
    # Menú de opciones
    options = {
        '1': ('Add task', add_task),
        '2': ('Update task', update_task),
        '3': ('View tasks', view_tasks),
        '4': ('Finalize task', finalize_task),
        '5': ('Add entry', add_entry),
        '6': ('View history', view_history),
        '7': ('Save and exit', exit_app)
    }
    
    while True:
        print("\n" + "="*70)
        print("TODO LIST APPLICATION")
        print("="*70)
        for key, (description, _) in options.items():
            print(f"  {key} --> {description}")
        print("="*70)
        
        action = input("Select action (1-7): ").strip()
        
        if action in options:
            try:
                _, func = options[action]
                func()
            except ValueError:
                logging.warning("Invalid input format.")
            except KeyboardInterrupt:
                print("\n\nInterrupted by user.")
                exit_app()
            except Exception as e:
                logging.error(f"An error occurred: {e}")
        else:
            print("Invalid option. Please select 1-7.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        exit_app()