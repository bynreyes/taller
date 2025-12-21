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
- decorators for logging (save)
- basic json serialization and deserialization
- basic CRUD operations in a command-line app
- basic git operations for version control (init, add ., commit, push, etc)

future improvements:
- ORMs for data persistence (SQLAlchemy)

"""
from collections import namedtuple
from functools import wraps
import logging
import os
import json
from datetime import datetime
from tabulate import tabulate

# data, lists of tuples
table = [] # table of pending tasks
done = []  # list of completed tasks

next_id = 1000

# data structures
Task = namedtuple(
    "Task",
    "id owner title description priority created_at uri status comment finished_at",
    defaults=("IN PROGRESS", None, None)
)
Command = namedtuple("Command", "add update view drop entry exit")
Entry = namedtuple("Entry", "date entries")

# utility functions
def find_task(id, list_of_tasks=table):    
    result = next((task for task in list_of_tasks if task.id == id), None)
    return result

def save(func):
    """
    Decorator to save task or result data to a file in JSON format.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result:  
            uri, data = result
            try:
                # 1. create logger
                log = logging.getLogger(uri)
                log.setLevel(logging.INFO)
                
                # 2. handler
                handler = logging.FileHandler(uri, encoding="utf-8")
                handler.setFormatter(logging.Formatter("%(message)s"))  # solo el mensaje
                log.addHandler(handler)
                
                # 3. log function
                log.info(json.dumps(data._asdict(), default=str))

            except Exception as e:
                print(f"Error saving data to {uri}: {e}")

        return result
    return wrapper

   
def view_tasks():
    """
    view all tasks in the table
    """
    options = {
        "ALL": lambda: tprint_tasks(table + done),
        "IN PROGRESS": lambda: tprint_tasks(table),
        "DONE": lambda: tprint_tasks(done),
        "SUCCESS": lambda: tprint_tasks(filter_tasks("SUCCESS")),
        "FAILED": lambda: tprint_tasks(filter_tasks("FAILED"))
    }
    
    while True:
        status_filter = input("Enter status filter (ALL, IN PROGRESS, DONE, SUCCESS, FAILED) or press Enter for ALL: ").strip().upper() or "ALL"
        if status_filter.upper() in ["ALL", "IN PROGRESS", "DONE", "SUCCESS", "FAILED"]:
            break
        print("Invalid status filter. Please try again.")
    
    options[status_filter]()

def filter_tasks(status, list_of_tasks=done):
    """
    simple function to filter tasks by status.
    may use lambda.
    """
    return [task for task in list_of_tasks if task.status == status]

def tprint_tasks(data):
    """
    print tasks in a table
    """
    if not data:
        print("No tasks to display.")
        return
    
    print(tabulate([(t.id, t.owner, t.title, t.priority, t.created_at, t.status) for t in data], 
                   headers=["ID", "Owner", "Title", "Priority", "Created At", "Status"]))


# CRUD operations
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

    uri = f"{owner.replace(' ', '_')}_{next_id}.txt"
    task = Task(next_id, owner, title, description, priority, created_at=datetime.now(), uri=uri)
    table.append(task)
    next_id += 1
    print("Task added successfully!")
    # loggear
    return (uri, task)


@save
def entry_task(id):
    """
    an Activities performed during the task 
    """
    uri = find_task(id, table + done).uri
    if not uri:
        print("Task not found.")
        return None
    
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
    
    title = input("Enter the new title [{task.title}]: ").strip() or task.title
    description = input("Enter the new description [{task.description}]: ").strip() or task.description
    owner = input("Enter the new owner [{task.owner}]: ").strip() or task.owner
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
    command = Command(exit=False, 
                  add=add_task, 
                  update=lambda: update_task(int(input("Enter task ID to update: "))), 
                  view=view_tasks, 
                  drop=lambda: finish_task(int(input("Enter task ID to finish: "))), 
                  entry=lambda: entry_task(int(input("Enter task ID for entry: ")))
                  )
    
    while not command.exit:
        print("\n" + "="*20)
        print("TODO LIST - Options: add, update, view, drop, entry")
        print("="*20)
        print("Enter 'exit' to exit")
        action = input("Select action: ").strip().lower()
        if action == "exit":
            command = command._replace(exit=True)
        elif hasattr(command, action):
            getattr(command, action)()
        else:
            print("Invalid action. Please try again.")

if __name__ == "__main__":
    main()