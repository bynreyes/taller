#!/usr/bin/env python
"""
Stock Application
version: 0.5
name: stock.py
author: nreyes

description:
Simple inventory application, with the aim of exploring and deepening 
the concepts of protocol vs. abstract methods.
"""

import csv
import os
import logging
from typing import Protocol, List, Optional, TypeVar, Generic
from dataclasses import dataclass, asdict
from datetime import datetime
from tabulate import tabulate
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Domain Models ---

@dataclass
class Product:
    id: int
    name: str
    description: str
    price: float
    stock: int
    min_stock: int

    def __post_init__(self):
        self.id = int(self.id)
        self.price = float(self.price)
        self.stock = int(self.stock)
        self.min_stock = int(self.min_stock)

@dataclass
class Sale:
    id: int
    product_id: int
    quantity: int
    date: str
    total: float

    def __post_init__(self):
        self.id = int(self.id)
        self.product_id = int(self.product_id)
        self.quantity = int(self.quantity)
        self.total = float(self.total)

# --- Protocol ---

T = TypeVar('T')

class Repository(Protocol[T]):
    """Protocol defining the interface for data repositories."""
    def get_all(self) -> List[T]: ...
    def get_by_id(self, item_id: int) -> Optional[T]: ...
    def add(self, item: T) -> None: ...

# --- Base Repository with Context Manager with basic CRUD operations ---

class CsvRepository(Generic[T]):
    """Base class for CSV operations with context manager support."""
    
    def __init__(self, file_path: str, fieldnames: List[str], model_class):
        self.file_path = file_path
        self.fieldnames = fieldnames
        self.model_class = model_class
        self._init_file()

    def _init_file(self):
        """Initialize CSV file if it doesn't exist."""
        if not os.path.exists(self.file_path):
            with open(self.file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
            logger.info(f"Created: {self.file_path}")

    @contextmanager
    def _csv_writer(self):
        """Context manager for atomic CSV write operations."""
        temp_file = f"{self.file_path}.tmp"
        try:
            with open(temp_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()
                yield writer
            # Atomic replacement
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            os.rename(temp_file, self.file_path)
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e

    def get_all(self) -> List[T]:
        """Read all items from CSV."""
        items = []
        try:
            with open(self.file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    items.append(self.model_class(**row))
        except Exception as e:
            logger.error(f"Error reading {self.file_path}: {e}")
        return items

    def get_by_id(self, item_id: int) -> Optional[T]:
        """Get item by ID."""
        for item in self.get_all():
            if item.id == item_id:
                return item
        return None

    def add(self, item: T) -> None:
        """Append new item to CSV."""
        if self.get_by_id(item.id):
            logger.warning(f"ID {item.id} already exists.")
            return
        
        with open(self.file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(asdict(item))

    def save_all(self, items: List[T]) -> None:
        """Rewrite entire CSV with updated items."""
        with self._csv_writer() as writer:
            for item in items:
                writer.writerow(asdict(item))

# --- Concrete Repositories ---

class InventoryRepository(CsvRepository[Product]):
    def __init__(self, file_path: str = "inventory.csv"):
        super().__init__(
            file_path,
            ["id", "name", "description", "price", "stock", "min_stock"],
            Product
        )

class SalesRepository(CsvRepository[Sale]):
    def __init__(self, file_path: str = "sales.csv"):
        super().__init__(
            file_path,
            ["id", "product_id", "quantity", "date", "total"],
            Sale
        )

    def get_next_id(self) -> int:
        """Calculate next available ID."""
        sales = self.get_all()
        return max([s.id for s in sales], default=0) + 1

# --- Service Layer (Business Logic) ---

class StockService:
    """Service layer handling business logic."""
    
    def __init__(self, inventory_repo: Repository[Product], sales_repo: Repository[Sale]):
        self.inventory = inventory_repo
        self.sales = sales_repo

    def update_stock(self, product_id: int, quantity_change: int) -> bool:
        """Update stock level. Returns True if successful."""
        products = self.inventory.get_all()
        
        for product in products:
            if product.id == product_id:
                new_stock = product.stock + quantity_change
                
                if new_stock < 0:
                    logger.error(f"Insufficient stock for {product.name}. Available: {product.stock}")
                    return False
                
                product.stock = new_stock
                self.inventory.save_all(products)
                self._check_low_stock(product)
                return True
        
        logger.error(f"Product ID {product_id} not found.")
        return False

    def _check_low_stock(self, product: Product):
        """Check and notify if stock is low."""
        if product.stock <= product.min_stock:
            logger.warning(
                f"⚠️  LOW STOCK: {product.name} (ID: {product.id}) - "
                f"Stock: {product.stock}, Min: {product.min_stock}"
            )

    def register_sale(self, product_id: int, quantity: int) -> Optional[Sale]:
        """Register a sale and update inventory."""
        product = self.inventory.get_by_id(product_id)
        if not product:
            logger.error("Product not found.")
            return None
        
        if quantity <= 0:
            logger.error("Quantity must be positive.")
            return None

        # Update stock
        if not self.update_stock(product_id, -quantity):
            return None

        # Create sale record
        sale_id = self.sales.get_next_id()
        total = quantity * product.price
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        sale = Sale(sale_id, product_id, quantity, date_str, total)
        self.sales.add(sale)
        
        logger.info(f"Sale registered: ID {sale_id}, Total: ${total:.2f}")
        return sale

# --- Controller (UI/Menu) ---

class StockApp:
    """Controller handling user interface and menu."""
    
    def __init__(self):
        self.inventory_repo = InventoryRepository()
        self.sales_repo = SalesRepository()
        self.service = StockService(self.inventory_repo, self.sales_repo)

    def display_menu(self):
        print("\n" + "="*40)
        print(" STOCK MANAGEMENT SYSTEM")
        print("="*40)
        print("1. View Inventory")
        print("2. Add New Product")
        print("3. Register Sale")
        print("4. Restock Product")
        print("5. View Sales History")
        print("6. Exit")
        print("="*40)

    def run(self):
        while True:
            self.display_menu()
            choice = input("Select an option: ").strip()

            if choice == '1':
                self.view_inventory()
            elif choice == '2':
                self.add_product()
            elif choice == '3':
                self.register_sale()
            elif choice == '4':
                self.restock_product()
            elif choice == '5':
                self.view_sales()
            elif choice == '6':
                print("Goodbye!")
                break
            else:
                print("Invalid option.")

    def view_inventory(self):
        products = self.inventory_repo.get_all()
        if not products:
            print("Inventory is empty.")
            return
        print(tabulate([asdict(p) for p in products], headers="keys", tablefmt="grid"))

    def add_product(self):
        print("\n--- Add New Product ---")
        try:
            p_id = int(input("ID: "))
            if self.inventory_repo.get_by_id(p_id):
                print("Error: Product ID already exists.")
                return

            name = input("Name: ")
            desc = input("Description: ")
            price = float(input("Price: "))
            stock = int(input("Initial Stock: "))
            min_stock = int(input("Min Stock: "))

            product = Product(p_id, name, desc, price, stock, min_stock)
            self.inventory_repo.add(product)
            logger.info(f"Product added: {name}")
        except ValueError:
            print("Invalid input.")

    def register_sale(self):
        print("\n--- Register Sale ---")
        try:
            p_id = int(input("Product ID: "))
            product = self.inventory_repo.get_by_id(p_id)
            if not product:
                print("Product not found.")
                return

            print(f"Selected: {product.name} (Price: ${product.price:.2f}, Stock: {product.stock})")
            qty = int(input("Quantity: "))

            sale = self.service.register_sale(p_id, qty)
            if sale:
                print(f"✓ Sale successful! Total: ${sale.total:.2f}")
        except ValueError:
            print("Invalid input.")

    def restock_product(self):
        print("\n--- Restock Product ---")
        try:
            p_id = int(input("Product ID: "))
            product = self.inventory_repo.get_by_id(p_id)
            if not product:
                print("Product not found.")
                return

            print(f"Selected: {product.name} (Current Stock: {product.stock})")
            qty = int(input("Quantity to add: "))

            if qty <= 0:
                print("Quantity must be positive.")
                return

            if self.service.update_stock(p_id, qty):
                print("✓ Restock successful!")
        except ValueError:
            print("Invalid input.")

    def view_sales(self):
        sales = self.sales_repo.get_all()
        if not sales:
            print("No sales recorded.")
            return
        print(tabulate([asdict(s) for s in sales], headers="keys", tablefmt="simple"))

if __name__ == "__main__":
    try:
        app = StockApp()
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...")