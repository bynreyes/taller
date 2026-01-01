"""
Algoritmos de ordenacion 
heapq vs sorted vs algoritmo de ordenacion clasico

creo que podria hacer el test dentro del mismo wrapper
"""
from collections import namedtuple
from faker import Faker
import heapq
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

User = namedtuple("User", "CC name last_name phone_number email")

def generated_data(region, q=10000):
    logging.info(f"Generating {q} data records.")
    data = []
    fake = Faker(region)
    for _ in range(q):
        name = fake.first_name()
        last_name = fake.last_name()
        data.append(
            User(
                CC=random.randint(1000000000, 1111999999),
                name=name,
                last_name=last_name,
                phone_number=fake.phone_number(),
                email=f"{name[0]}.{last_name}@UTS.edu.co"
            ))
    logging.info("Data generation complete.")
    return data
    
def timing(func):
    def wrapper(*arg, **kw):
        t1 = time.time()
        result = func(*arg, **kw)
        t2 = time.time()
        return (t2 - t1), result, func.__name__
    return wrapper

@timing
def heapsort(iterable):
    logging.info(f"Starting heapsort with {len(iterable)} items.")
    h = []
    for value in iterable:
        heapq.heappush(h, value)
        
    return [heapq.heappop(h) for i in range(len(h))]

@timing 
def bubblesort(data):
    logging.info(f"Starting bubblesort with {len(data)} items.")
    iterable = data.copy()
    for i in range(len(iterable)):
        for j in range(len(iterable) - 1):
            if iterable[j].CC > iterable[j + 1].CC:
                iterable[j], iterable[j + 1] = iterable[j + 1], iterable[j]

    return iterable

@timing
def python_sort(data):
    logging.info(f"Starting python_sort with {len(data)} items.")
    iterable = data.copy()
    return sorted(iterable, key=lambda x: x.CC)

@timing
def quicksort(data):
    logging.info(f"Starting quicksort with {len(data)} items.")
    iterable = data.copy()
    _quicksort(iterable, 0, len(iterable) - 1)
    return iterable

def _quicksort(iterable, low, high):
    if low < high:
        pi = _partition(iterable, low, high)
        _quicksort(iterable, low, pi - 1)
        _quicksort(iterable, pi + 1, high)

def _partition(iterable, low, high):
    pivot = iterable[high].CC
    i = low - 1
    for j in range(low, high):
        if iterable[j].CC <= pivot:
            i += 1
            iterable[i], iterable[j] = iterable[j], iterable[i]
    iterable[i + 1], iterable[high] = iterable[high], iterable[i + 1]
    return i + 1

def test_sort(func_name, sorted_data, real_sorted_data):
    logging.info(f"Testing {func_name} result.")
    if real_sorted_data == sorted_data:
        logging.info(f"{func_name} sorted the data correctly.")
    else:
        logging.error(f"{func_name} did not sort the data correctly.")

if __name__ == '__main__':
    logging.info("Starting process.")
    REGION = "es_CO"
    times = []
    test = []
    data = generated_data(REGION)
    canon = sorted(data, key=lambda x: x.CC)

    logging.info("Initial data (first 10 items):")
    for i, _ in enumerate(range(10)):
        print(f"pos {i +1}: {data[i].name} {data[i].last_name} {data[i].CC}")

    func_list = [heapsort, bubblesort, python_sort, quicksort]
    logging.info("Starting sorting algorithms.")
    for f in func_list:
        times.append(f(data))
        
    logging.info("Sorting complete.")
    times.sort(key=lambda x: x[0])
    logging.info("Printing results.")

    for (timed, result, func_name) in times:
        test_sort(func_name=func_name, sorted_data=result, real_sorted_data=canon)

    for (timed, result, func_name) in times:
        print(f"{func_name} algorithm took --> {timed * 1000:.3f}ms.")
    logging.info("Process finished.")