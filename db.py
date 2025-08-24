import sqlite3
import json
import csv
from typing import List, Dict, Type, Any, Optional
from pathlib import Path
from datetime import datetime
from models import Client, Product, Order, OrderItem, PremiumClient

class Database:
    def __init__(self, db_path: str = "shop.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    registration_date TEXT NOT NULL,
                    is_premium INTEGER DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    stock INTEGER DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    order_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    PRIMARY KEY (order_id, product_id),
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            conn.commit()
    
    def _dict_to_client(self, data: Dict) -> Client:
        if data.get('is_premium'):
            return PremiumClient(**{k: v for k, v in data.items() if k != 'is_premium'})
        return Client(**{k: v for k, v in data.items() if k != 'is_premium'})
    
    def add_client(self, client: Client) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            is_premium = 1 if isinstance(client, PremiumClient) else 0
            cursor.execute("""
                INSERT INTO clients (name, email, phone, address, registration_date, is_premium)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                client.name, client.email, client.phone, 
                client.address, client.registration_date, is_premium
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_client(self, client_id: int) -> Optional[Client]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                client_data = dict(zip(columns, row))
                return self._dict_to_client(client_data)
            return None
    
    def get_all_clients(self) -> List[Client]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients")
            columns = [desc[0] for desc in cursor.description]
            return [self._dict_to_client(dict(zip(columns, row))) for row in cursor.fetchall()]
    
    def add_product(self, product: Product) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (name, price, category, stock)
                VALUES (?, ?, ?, ?)
            """, (product.name, product.price, product.category, product.stock))
            conn.commit()
            return cursor.lastrowid
    
    def get_product(self, product_id: int) -> Optional[Product]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return Product(**dict(zip(columns, row)))
            return None
    
    def get_all_products(self) -> List[Product]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products")
            columns = [desc[0] for desc in cursor.description]
            return [Product(**dict(zip(columns, row))) for row in cursor.fetchall()]
    
    def add_order(self, order: Order) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (client_id, order_date, status)
                VALUES (?, ?, ?)
            """, (order.client_id, order.order_date, order.status))
            order_id = cursor.lastrowid
            
            for item in order.items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """, (order_id, item.product_id, item.quantity, item.unit_price))
                
                # Update product stock
                cursor.execute("""
                    UPDATE products 
                    SET stock = stock - ?
                    WHERE id = ?
                """, (item.quantity, item.product_id))
            
            conn.commit()
            return order_id
    
    def get_order(self, order_id: int) -> Optional[Order]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get order details
            cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order_row = cursor.fetchone()
            if not order_row:
                return None
                
            order_columns = [desc[0] for desc in cursor.description]
            order_data = dict(zip(order_columns, order_row))
            
            # Get order items
            cursor.execute("""
                SELECT product_id, quantity, unit_price 
                FROM order_items 
                WHERE order_id = ?
            """, (order_id,))
            
            items = [
                OrderItem(product_id=row[0], quantity=row[1], unit_price=row[2])
                for row in cursor.fetchall()
            ]
            
            return Order(
                id=order_data['id'],
                client_id=order_data['client_id'],
                items=items,
                order_date=order_data['order_date'],
                status=order_data['status']
            )
    
    def get_all_orders(self) -> List[Order]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM orders")
            order_ids = [row[0] for row in cursor.fetchall()]
            return [self.get_order(order_id) for order_id in order_ids]
    
    def update_order_status(self, order_id: int, status: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE orders 
                SET status = ?
                WHERE id = ?
            """, (status, order_id))
            conn.commit()
    
    def search_clients(self, search_term: str) -> List[Client]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM clients 
                WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            
            columns = [desc[0] for desc in cursor.description]
            return [self._dict_to_client(dict(zip(columns, row))) for row in cursor.fetchall()]
    
    def search_products(self, search_term: str) -> List[Product]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE name LIKE ? OR category LIKE ?
            """, (f"%{search_term}%", f"%{search_term}%"))
            
            columns = [desc[0] for desc in cursor.description]
            return [Product(**dict(zip(columns, row))) for row in cursor.fetchall()]
    
    def export_to_csv(self, entity_type: str, file_path: str):
        data = []
        if entity_type == "clients":
            data = self.get_all_clients()
        elif entity_type == "products":
            data = self.get_all_products()
        elif entity_type == "orders":
            data = self.get_all_orders()
        else:
            raise ValueError("Invalid entity type")
        
        if not data:
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if entity_type == "orders":
                # Special handling for orders with nested items
                writer = csv.writer(f)
                writer.writerow(['id', 'client_id', 'order_date', 'status', 'items'])
                for order in data:
                    items_str = ";".join(
                        f"{item.product_id}:{item.quantity}:{item.unit_price}"
                        for item in order.items
                    )
                    writer.writerow([
                        order.id, order.client_id, order.order_date, 
                        order.status, items_str
                    ])
            else:
                writer = csv.DictWriter(f, fieldnames=vars(data[0]).keys())
                writer.writeheader()
                for item in data:
                    writer.writerow(vars(item))
    
    def import_from_csv(self, entity_type: str, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if entity_type == "clients":
                for row in reader:
                    try:
                        client_data = {
                            'name': row['name'],
                            'email': row['email'],
                            'phone': row['phone'],
                            'address': row['address'],
                            'registration_date': row.get('registration_date', datetime.now().strftime("%Y-%m-%d"))
                        }
                        if row.get('is_premium') == '1':
                            client = PremiumClient(**client_data)
                        else:
                            client = Client(**client_data)
                        self.add_client(client)
                    except Exception as e:
                        print(f"Error importing client: {e}")
            
            elif entity_type == "products":
                for row in reader:
                    try:
                        product = Product(
                            id=int(row['id']),
                            name=row['name'],
                            price=float(row['price']),
                            category=row['category'],
                            stock=int(row.get('stock', 0))
                        )
                        self.add_product(product)
                    except Exception as e:
                        print(f"Error importing product: {e}")
            
            elif entity_type == "orders":
                for row in reader:
                    try:
                        order = Order(
                            id=int(row['id']),
                            client_id=int(row['client_id']),
                            order_date=row['order_date'],
                            status=row['status'])
                        
                        # Parse items
                        items_str = row.get('items', '')
                        if items_str:
                            for item_str in items_str.split(';'):
                                if ':' in item_str:
                                    product_id, quantity, unit_price = item_str.split(':')
                                    order.items.append(OrderItem(
                                        product_id=int(product_id),
                                        quantity=int(quantity),
                                        unit_price=float(unit_price)
                                    ))
                        
                        self.add_order(order)
                    except Exception as e:
                        print(f"Error importing order: {e}")
    
    def export_to_json(self, entity_type: str, file_path: str):
        data = []
        if entity_type == "clients":
            data = [vars(client) for client in self.get_all_clients()]
        elif entity_type == "products":
            data = [vars(product) for product in self.get_all_products()]
        elif entity_type == "orders":
            data = []
            for order in self.get_all_orders():
                order_dict = {
                    'id': order.id,
                    'client_id': order.client_id,
                    'order_date': order.order_date,
                    'status': order.status,
                    'items': [
                        {
                            'product_id': item.product_id,
                            'quantity': item.quantity,
                            'unit_price': item.unit_price
                        }
                        for item in order.items
                    ]
                }
                data.append(order_dict)
        else:
            raise ValueError("Invalid entity type")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def import_from_json(self, entity_type: str, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            if entity_type == "clients":
                for item in data:
                    try:
                        # ИСПРАВЛЕННЫЙ КОД: проверяем is_premium вместо discount_rate
                        if item.get('is_premium', False):
                            client = PremiumClient(
                                id=item['id'],
                                name=item['name'],
                                email=item['email'],
                                phone=item['phone'],
                                address=item['address'],
                                registration_date=item.get('registration_date', datetime.now().strftime("%Y-%m-%d"))
                            )
                        else:
                            client = Client(
                                id=item['id'],
                                name=item['name'],
                                email=item['email'],
                                phone=item['phone'],
                                address=item['address'],
                                registration_date=item.get('registration_date', datetime.now().strftime("%Y-%m-%d"))
                            )
                        self.add_client(client)
                    except Exception as e:
                        print(f"Error importing client: {e}")
            
            elif entity_type == "products":
                for item in data:
                    try:
                        product = Product(
                            id=item['id'],
                            name=item['name'],
                            price=item['price'],
                            category=item['category'],
                            stock=item['stock']
                        )
                        self.add_product(product)
                    except Exception as e:
                        print(f"Error importing product: {e}")
            
            elif entity_type == "orders":
                for item in data:
                    try:
                        order = Order(
                            id=item['id'],
                            client_id=item['client_id'],
                            order_date=item['order_date'],
                            status=item['status'],
                            items=[]
                        )
                        
                        for order_item in item.get('items', []):
                            order.items.append(OrderItem(
                                product_id=order_item['product_id'],
                                quantity=order_item['quantity'],
                                unit_price=order_item['unit_price']
                            ))
                        
                        self.add_order(order)
                    except Exception as e:
                        print(f"Error importing order: {e}")
    
    def get_orders_by_date_range(self, start_date: str, end_date: str) -> List[Order]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM orders 
                WHERE order_date BETWEEN ? AND ?
                ORDER BY order_date
            """, (start_date, end_date))
            
            order_ids = [row[0] for row in cursor.fetchall()]
            return [self.get_order(order_id) for order_id in order_ids]
    
    def get_top_clients(self, limit: int = 5) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name, COUNT(o.id) as order_count, SUM(oi.quantity * oi.unit_price) as total_spent
                FROM clients c
                LEFT JOIN orders o ON c.id = o.client_id
                LEFT JOIN order_items oi ON o.id = oi.order_id
                GROUP BY c.id, c.name
                ORDER BY order_count DESC, total_spent DESC
                LIMIT ?
            """, (limit,))
            
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'order_count': row[2],
                    'total_spent': row[3] if row[3] else 0
                }
                for row in cursor.fetchall()
            ]
    
    def get_sales_by_date(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    order_date,
                    COUNT(DISTINCT o.id) as order_count,
                    SUM(oi.quantity * oi.unit_price) as total_amount
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                GROUP BY order_date
                ORDER BY order_date
            """)
            
            return [
                {
                    'date': row[0],
                    'order_count': row[1],
                    'total_amount': row[2] if row[2] else 0
                }
                for row in cursor.fetchall()
            ]
    
    def get_product_sales(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.id,
                    p.name,
                    p.category,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.quantity * oi.unit_price) as total_revenue
                FROM products p
                LEFT JOIN order_items oi ON p.id = oi.product_id
                GROUP BY p.id, p.name, p.category
                ORDER BY total_revenue DESC
            """)
            
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'total_quantity': row[3] if row[3] else 0,
                    'total_revenue': row[4] if row[4] else 0
                }
                for row in cursor.fetchall()
            ]