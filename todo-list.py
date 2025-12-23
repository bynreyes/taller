"""
version: 1.0
name: todo-list.py
author: nreyes

description:
TODO List Application
A simple command-line TODO list application to manage tasks.
by nreyes

what was learned:
- usage of namedtuple for structured data
- decorators for save functionality
- basic yml serialization and deserialization
- basic CRUD operations in a command-line app
- basic git operations for version control (init, add ., commit, push, etc)

yaml vs json:
- YAML is more human-readable and supports comments
- JSON is more widely used in web applications and APIs

future improvements:
- ORMs for data persistence (SQLAlchemy)
- type hints for better code clarity
- maybe a GUI using Tkinter
"""
from collections import namedtuple
from functools import wraps
import os
import yaml
from datetime import datetime
import sys
from tabulate import tabulate

# data
table = [] # table of pending tasks
done = []  # list of completed tasks
next_id = 1000

# data structures
Task = namedtuple(
    "Task",
    "id owner title description priority created_at uri status comment finished_at",
    defaults=("IN PROGRESS", None, None)
)
# Just for fun, since the most pythonic solution is a dictionary.
Command = namedtuple("Command", "add update view history drop entry exit")
Entry = namedtuple("Entry", "date entries")

class Repository:
    """
    Abstract class to handle YAML persistence
    """
    def __init__(self, folder="tasks"):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def _get_path(self, uri):
        return os.path.join(self.folder, f"{uri}.yaml")
    
    def load(self, uri):
        """
        load history from YAML file
        """
        path = self._get_path(uri)
        if not os.path.exists(path):
            return []
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or []
    
    def push(self, uri, data):
        """
        push new data to YAML file
        
        :param uri: URI of the task
        :param data: data to be saved
        """
        path = self._get_path(uri)
        history = self.load(uri)
        history.append({
            'timestamp': datetime.now().isoformat(),
            'type': type(data).__name__,
            'data': data._asdict() if hasattr(data, '_asdict') else vars(data)
        })

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(history, f, allow_unicode=True, sort_keys=False)

repo = Repository()

# decorators
def tabulate_print(func):
    """
    Decorator to print data on tabulate format
    Handles both lists of Task namedtuples and lists of dictionaries
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = func(*args, **kwargs)
        if not data:
            print("No tasks to display.")
            return data

        # Check if it's a list of dictionaries (from history)
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            print(tabulate(data, headers='keys'))
        # Check if it's a list of Task namedtuples
        elif isinstance(data, list) and len(data) > 0 and hasattr(data[0], 'id'):
            print(tabulate([(t.id, t.owner, t.title, t.priority, t.created_at, t.status) for t in data], 
                           headers=["ID", "Owner", "Title", "Priority", "Created At", "Status"]))
        
        return data
    return wrapper

def save(func):
    """
    Decorator to save task changes to YAML repository
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, tuple) and len(result) == 2:
            uri, data = result
            repo.push(uri, data)        
        return result
    return wrapper

# utility functions
def find_task(id, list_of_tasks=table):    
    result = next((task for task in list_of_tasks if task.id == id), None)
    return result

@tabulate_print
def view_tasks():
    """
    view all tasks in the table
    """
    options = {
        "ALL": lambda: [*table, *done],
        "IN PROGRESS": lambda: table,
        "DONE": lambda: done,
        "SUCCESS": lambda: filter_tasks("SUCCESS"),
        "FAILED": lambda: filter_tasks("FAILED")
    }
    
    while True:
        status_filter = input("Enter status filter (ALL, IN PROGRESS, DONE, SUCCESS, FAILED) or press Enter for ALL: ").strip().upper() or "ALL"
        if status_filter.upper() in ["ALL", "IN PROGRESS", "DONE", "SUCCESS", "FAILED"]:
            break
        print("Invalid status filter. Please try again.")
    
    return options[status_filter]()

def filter_tasks(status, list_of_tasks=done):
    """
    simple function to filter tasks by status.
    """
    return [task for task in list_of_tasks if task.status == status]

@tabulate_print
def view_history(id):
    """
    view the history of a specific task (changes, etc.)
    Returns a list of dictionaries with history entries for tabulate
    """
    task = find_task(id, table) or find_task(id, done)
    if not task:
        print("Task not found.")
        return
    
    uri = task.uri
    title = task.title
    status = task.status
    
    history = repo.load(uri)
    if not history:
        print("📭 No history found")
        return
    
    print(f"\n{'='*60}")
    print(f"TASK #{id}: {title} | {status}")
    print('='*60)
    
    # Convert history to a list of dictionaries for tabulation
    history_data = []
    for record in history:
        ts = record['timestamp']
        rtype = record['type']
        data = record['data']
        
        if rtype == 'Task':
            history_data.append({
                'Timestamp': ts,
                'Type': 'CREATED',
                'Title': data['title'],
                'Description': data['description'],
                'Priority': data['priority']
            })
        
        elif rtype == 'Entry':
            history_data.append({
                'Timestamp': ts,
                'Type': 'ENTRY',
                'Title': '-',
                'Description': data['entries'],
                'Priority': '-'
            })
    
    print('='*60)
    return history_data

# CRUD  basic operations
@save
def add_task():
    """
    add a new task to the table
    """
    global next_id
    owner = input("Enter the owner of the task: ").strip()
    title = input("Enter the title of the task: ").strip()
    description = input("Enter the description of the task: ").strip()

    while True:
        priority = input("Enter the priority of the task (Low, Medium, High): ").strip().upper()
        if priority in ['LOW', 'MEDIUM', 'HIGH']:
            break
        print("Invalid priority. Please enter Low, Medium, or High.")

    uri = f"{owner.replace(' ', '_')}_{next_id}"
    task = Task(next_id, owner, title, description, priority, created_at=datetime.now(), uri=uri)
    table.append(task)
    next_id += 1
    print("Task added successfully!")
    return (uri, task)

@save
def entry_task(id):
    """
    an Activities performed during the task 
    """
    
    task = find_task(id, table)
    if not task:
        print("Task not found.")
        return None
    
    uri = task.uri
    activity = input("Enter the new details for the task:\n")
    update_at = datetime.now()    
    entry = Entry(update_at, activity)
    print("Task updated successfully!")
    return (uri, entry)

@save
def update_task(id):
    """
    update an existing task in the table
    """
    task = find_task(id)
    if not task:
        print("Task not found.")
        return None
    
    title = input(f"Enter the new title [{task.title}]: ").strip() or task.title
    description = input("Enter the new description [{task.description}]: ").strip() or task.description
    owner = input(f"Enter the new owner [{task.owner}]: ").strip() or task.owner
    uri = f"{owner.replace(' ', '_')}_{id}.txt"
    if uri != task.uri and os.path.exists(task.uri):
        os.rename(task.uri, uri)
   
    updated_task = task._replace(title=title, description=description, owner=owner, uri=uri)
    table.remove(task)
    table.append(updated_task)
    print("Task updated successfully!")
    return (uri, updated_task)

@save
def finish_task(id):
    """
    finish a task and move it to done list
    """
    task = find_task(id, table)
    if not task:
        print("Task not found.")
        return None
       
    while True:
        status = input("task completion, enter: success or failed: ").strip().upper()
        if status in ['SUCCESS', 'FAILED']:
            break
        
        print("Invalid input. Please enter 'SUCCESS' or 'FAILED'.")
    
    comment = input("Enter any comments about the task completion: ").strip()
    finish_at = datetime.now()
    
    table.remove(task)
    # update task status, comment, finished_at
    task = task._replace(status=status, comment=comment, finished_at=finish_at)
    done.append(task)
    
    print("Task finished successfully!")
    return (task.uri, task)

def main():
    """
    Main function to run the TODO list application.
    """
    # 
    command = Command(exit=lambda: sys.exit(0), 
                  add=add_task, 
                  update=lambda: update_task(int(input("Enter task ID to update: "))), 
                  view=view_tasks, 
                  drop=lambda: finish_task(int(input("Enter task ID to finish: "))),
                  history=lambda: view_history(int(input("Enter task ID to view history: "))), 
                  entry=lambda: entry_task(int(input("Enter task ID for entry: ")))
                  )
    
    while True:
        print("\n" + "="*60)
        print("TODO LIST - Options: add, update, view, drop, entry, history, exit")
        print("="*60)
        action = input("Select action: ").strip().lower()
        if hasattr(command, action):
            try:
                getattr(command, action)()
            except ValueError:
                print("Invalid ID format.")
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("Invalid action. Please try again.")

if __name__ == "__main__":
    main()