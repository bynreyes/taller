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
done = []  # list of finished tasks

next_id = 1000

# data structures
Task = namedtuple(
    "Task",
    "id owner title description priority created_at uri status comment finished_at",
    defaults=("IN PROGRESS", None, None)
)
Command = namedtuple("Command", "exit add update view drop entry view_done")
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
    activity = input("Enter the new details for the task:\n")
    update_at = datetime.now()
    uri = find_task(id).uri
    if not uri:
        print("Task not found.")
        return None
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

   
def view_tasks():
    """
    view all tasks (pending) in the table
    """
    if not table:
        print("No tasks available.")
        return

    for task in table:
        print(tabulate([t._asdict() for t in table], headers="keys"))

@save
def finish_task(id):
    """
    finish a task and move it to done list
    """
    task = find_task(id)
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

def view_done():
    """
    view all finished tasks
    """
    if not done:
        print("No finished tasks available.")
        return
    
    for task in done:
        print(tabulate([t._asdict() for t in done], headers="keys"))

def main():
    """
    Main function to run the TODO list application.
    """
    command = Command(exit=False, 
                  add=add_task, 
                  update=lambda: update_task(int(input("Enter task ID to update: "))), 
                  view=view_tasks, 
                  drop=lambda: finish_task(int(input("Enter task ID to finish: "))), 
                  entry=lambda: entry_task(int(input("Enter task ID for entry: "))), 
                  view_done=view_done
                  )
    
    while not command.exit:
        print("\n" + "="*20)
        print("TODO LIST - Options: add, update, view, drop, view_done, exit")
        action = input("Select action: ").strip().lower()
        if action == "exit":
            command = command._replace(exit=True)
        elif hasattr(command, action):
            getattr(command, action)()
        else:
            print("Invalid action. Please try again.")

if __name__ == "__main__":
    main()