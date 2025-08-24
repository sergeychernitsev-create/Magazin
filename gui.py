import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional, List, Dict
from db import Database
from analysis import DataAnalyzer
from models import Client, Product, Order, ValidationError, PremiumClient
import sqlite3
class ShopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shop Management System")
        self.root.geometry("1200x800")
        
        # Initialize database
        self.db = Database()
        self.analyzer = DataAnalyzer(self.db)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_clients_tab()
        self.create_products_tab()
        self.create_orders_tab()
        self.create_reports_tab()
        self.create_import_export_tab()
        
        # Load initial data
        self.refresh_clients_list()
        self.refresh_products_list()
        self.refresh_orders_list()
    
    def create_clients_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Клиенты")
        
        # Client list frame
        list_frame = ttk.LabelFrame(tab, text="Список клиентов", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Search and filter
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.client_search_entry = ttk.Entry(search_frame)
        self.client_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.client_search_entry.bind("<KeyRelease>", self.on_client_search)
        
        ttk.Button(search_frame, text="Очистить", command=self.clear_client_search).pack(side=tk.LEFT)
        
        # Client list treeview
        self.clients_tree = ttk.Treeview(
            list_frame,
            columns=("id", "name", "email", "phone", "address", "reg_date", "premium"),
            show="headings"
        )
        
        self.clients_tree.heading("id", text="ID", command=lambda: self.sort_clients("id"))
        self.clients_tree.heading("name", text="Имя", command=lambda: self.sort_clients("name"))
        self.clients_tree.heading("email", text="Email", command=lambda: self.sort_clients("email"))
        self.clients_tree.heading("phone", text="Телефон", command=lambda: self.sort_clients("phone"))
        self.clients_tree.heading("address", text="Адрес", command=lambda: self.sort_clients("address"))
        self.clients_tree.heading("reg_date", text="Дата регистрации", command=lambda: self.sort_clients("reg_date"))
        self.clients_tree.heading("premium", text="Премиум", command=lambda: self.sort_clients("premium"))
        
        self.clients_tree.column("id", width=50)
        self.clients_tree.column("name", width=150)
        self.clients_tree.column("email", width=200)
        self.clients_tree.column("phone", width=120)
        self.clients_tree.column("address", width=200)
        self.clients_tree.column("reg_date", width=120)
        self.clients_tree.column("premium", width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.clients_tree.pack(fill=tk.BOTH, expand=True)
        
        # Client details frame
        detail_frame = ttk.LabelFrame(tab, text="Данные клиента", padding=10)
        detail_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Form fields
        form_frame = ttk.Frame(detail_frame)
        form_frame.pack(fill=tk.X)
        
        ttk.Label(form_frame, text="Имя:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.client_name_entry = ttk.Entry(form_frame)
        self.client_name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.client_email_entry = ttk.Entry(form_frame)
        self.client_email_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Телефон:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.client_phone_entry = ttk.Entry(form_frame)
        self.client_phone_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Адрес:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.client_address_entry = ttk.Entry(form_frame)
        self.client_address_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.client_premium_var = tk.BooleanVar()
        ttk.Checkbutton(
            form_frame, 
            text="Премиум клиент", 
            variable=self.client_premium_var
        ).grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(detail_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame, 
            text="Добавить", 
            command=self.add_client
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Обновить", 
            command=self.update_client
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Удалить", 
            command=self.delete_client
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Очистить", 
            command=self.clear_client_form
        ).pack(side=tk.LEFT, padx=5)
        
        # Bind treeview selection
        self.clients_tree.bind("<<TreeviewSelect>>", self.on_client_select)
    
    def create_products_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Товары")
        
        # Product list frame
        list_frame = ttk.LabelFrame(tab, text="Список товаров", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Search and filter
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.product_search_entry = ttk.Entry(search_frame)
        self.product_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.product_search_entry.bind("<KeyRelease>", self.on_product_search)
        
        ttk.Button(search_frame, text="Очистить", command=self.clear_product_search).pack(side=tk.LEFT)
        
        # Product list treeview
        self.products_tree = ttk.Treeview(
            list_frame,
            columns=("id", "name", "price", "category", "stock"),
            show="headings"
        )
        
        self.products_tree.heading("id", text="ID", command=lambda: self.sort_products("id"))
        self.products_tree.heading("name", text="Название", command=lambda: self.sort_products("name"))
        self.products_tree.heading("price", text="Цена", command=lambda: self.sort_products("price"))
        self.products_tree.heading("category", text="Категория", command=lambda: self.sort_products("category"))
        self.products_tree.heading("stock", text="Остаток", command=lambda: self.sort_products("stock"))
        
        self.products_tree.column("id", width=50)
        self.products_tree.column("name", width=200)
        self.products_tree.column("price", width=100)
        self.products_tree.column("category", width=150)
        self.products_tree.column("stock", width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.products_tree.pack(fill=tk.BOTH, expand=True)
        
        # Product details frame
        detail_frame = ttk.LabelFrame(tab, text="Данные товара", padding=10)
        detail_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Form fields
        form_frame = ttk.Frame(detail_frame)
        form_frame.pack(fill=tk.X)
        
        ttk.Label(form_frame, text="Название:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.product_name_entry = ttk.Entry(form_frame)
        self.product_name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Цена:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.product_price_entry = ttk.Entry(form_frame)
        self.product_price_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Категория:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.product_category_entry = ttk.Entry(form_frame)
        self.product_category_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Остаток:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.product_stock_entry = ttk.Entry(form_frame)
        self.product_stock_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(detail_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame, 
            text="Добавить", 
            command=self.add_product
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Обновить", 
            command=self.update_product
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Удалить", 
            command=self.delete_product
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Очистить", 
            command=self.clear_product_form
        ).pack(side=tk.LEFT, padx=5)
        
        # Bind treeview selection
        self.products_tree.bind("<<TreeviewSelect>>", self.on_product_select)
    
    def create_orders_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Заказы")
        
        # Order list frame
        list_frame = ttk.LabelFrame(tab, text="Список заказов", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Search and filter
        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Клиент:").pack(side=tk.LEFT)
        self.order_client_filter = ttk.Combobox(filter_frame, state="readonly")
        self.order_client_filter.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.order_client_filter.bind("<<ComboboxSelected>>", self.on_order_filter)
        
        ttk.Label(filter_frame, text="Статус:").pack(side=tk.LEFT, padx=(10, 0))
        self.order_status_filter = ttk.Combobox(
            filter_frame, 
            values=["Все", "ожидание", "обработка", "завершен", "отменен"],
            state="readonly"
        )
        self.order_status_filter.current(0)
        self.order_status_filter.pack(side=tk.LEFT, padx=5)
        self.order_status_filter.bind("<<ComboboxSelected>>", self.on_order_filter)
        
        ttk.Button(filter_frame, text="Очистить", command=self.clear_order_filter).pack(side=tk.LEFT)
        
        # Order list treeview
        self.orders_tree = ttk.Treeview(
            list_frame,
            columns=("id", "client", "date", "status", "amount", "items"),
            show="headings"
        )
        
        self.orders_tree.heading("id", text="ID", command=lambda: self.sort_orders("id"))
        self.orders_tree.heading("client", text="Клиент", command=lambda: self.sort_orders("client"))
        self.orders_tree.heading("date", text="Дата", command=lambda: self.sort_orders("date"))
        self.orders_tree.heading("status", text="Статус", command=lambda: self.sort_orders("status"))
        self.orders_tree.heading("amount", text="Сумма", command=lambda: self.sort_orders("amount"))
        self.orders_tree.heading("items", text="Товары", command=lambda: self.sort_orders("items"))
        
        self.orders_tree.column("id", width=50)
        self.orders_tree.column("client", width=150)
        self.orders_tree.column("date", width=100)
        self.orders_tree.column("status", width=100)
        self.orders_tree.column("amount", width=100)
        self.orders_tree.column("items", width=200)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.orders_tree.pack(fill=tk.BOTH, expand=True)
        
        # Order details frame
        detail_frame = ttk.LabelFrame(tab, text="Детали заказа", padding=10)
        detail_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Form fields
        form_frame = ttk.Frame(detail_frame)
        form_frame.pack(fill=tk.X)
        
        ttk.Label(form_frame, text="Клиент:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.order_client_combobox = ttk.Combobox(form_frame, state="readonly")
        self.order_client_combobox.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(form_frame, text="Дата:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.order_date_entry = ttk.Entry(form_frame)
        self.order_date_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        self.order_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(form_frame, text="Статус:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.order_status_combobox = ttk.Combobox(
            form_frame, 
            values=["ожидание", "обработка", "завершен", "отменен"],
            state="readonly"
        )
        self.order_status_combobox.current(0)
        self.order_status_combobox.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Order items frame
        items_frame = ttk.LabelFrame(detail_frame, text="Товары в заказе", padding=10)
        items_frame.pack(fill=tk.X, pady=5)
        
        # Product selection
        item_select_frame = ttk.Frame(items_frame)
        item_select_frame.pack(fill=tk.X)
        
        ttk.Label(item_select_frame, text="Товар:").pack(side=tk.LEFT)
        self.order_product_combobox = ttk.Combobox(item_select_frame, state="readonly")
        self.order_product_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Label(item_select_frame, text="Кол-во:").pack(side=tk.LEFT, padx=(10, 0))
        self.order_quantity_entry = ttk.Entry(item_select_frame, width=5)
        self.order_quantity_entry.pack(side=tk.LEFT)
        self.order_quantity_entry.insert(0, "1")
        
        ttk.Button(
            item_select_frame, 
            text="Добавить", 
            command=self.add_order_item
        ).pack(side=tk.LEFT, padx=5)
        
        # Order items list
        self.order_items_tree = ttk.Treeview(
            items_frame,
            columns=("product", "price", "quantity", "total"),
            show="headings"
        )
        
        self.order_items_tree.heading("product", text="Товар")
        self.order_items_tree.heading("price", text="Цена")
        self.order_items_tree.heading("quantity", text="Количество")
        self.order_items_tree.heading("total", text="Сумма")
        
        self.order_items_tree.column("product", width=200)
        self.order_items_tree.column("price", width=100)
        self.order_items_tree.column("quantity", width=80)
        self.order_items_tree.column("total", width=100)
        
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.order_items_tree.yview)
        self.order_items_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.order_items_tree.pack(fill=tk.BOTH, expand=True)
        
        # Total amount
        total_frame = ttk.Frame(items_frame)
        total_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(total_frame, text="Общая сумма:").pack(side=tk.LEFT)
        self.order_total_label = ttk.Label(total_frame, text="0₽", font=('Arial', 10, 'bold'))
        self.order_total_label.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(detail_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame, 
            text="Создать", 
            command=self.create_order
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Обновить", 
            command=self.update_order
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Удалить", 
            command=self.delete_order
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Очистить", 
            command=self.clear_order_form
        ).pack(side=tk.LEFT, padx=5)
        
        # Bind treeview selection
        self.orders_tree.bind("<<TreeviewSelect>>", self.on_order_select)
        
        # Initialize comboboxes
        self.update_client_comboboxes()
        self.update_product_comboboxes()
    
    def create_reports_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Отчеты")
        
        # Date range selection
        date_frame = ttk.LabelFrame(tab, text="Период", padding=10)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(date_frame, text="С:").pack(side=tk.LEFT)
        self.report_start_date = ttk.Entry(date_frame)
        self.report_start_date.pack(side=tk.LEFT, padx=5)
        self.report_start_date.insert(0, "2023-01-01")
        
        ttk.Label(date_frame, text="По:").pack(side=tk.LEFT, padx=(10, 0))
        self.report_end_date = ttk.Entry(date_frame)
        self.report_end_date.pack(side=tk.LEFT, padx=5)
        self.report_end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Report buttons
        report_frame = ttk.LabelFrame(tab, text="Отчеты", padding=10)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Button(
            report_frame, 
            text="Топ клиентов", 
            command=self.show_top_clients
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            report_frame, 
            text="Динамика продаж", 
            command=self.show_sales_trend
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            report_frame, 
            text="Топ товаров", 
            command=self.show_top_products
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            report_frame, 
            text="Распределение по категориям", 
            command=self.show_category_distribution
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            report_frame, 
            text="Сеть клиентов", 
            command=self.show_client_network
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            report_frame, 
            text="Сгенерировать отчет", 
            command=self.generate_sales_report
        ).pack(fill=tk.X, pady=2)
    
    def create_import_export_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Импорт/Экспорт")
        
        # Export frame
        export_frame = ttk.LabelFrame(tab, text="Экспорт данных", padding=10)
        export_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(export_frame, text="Тип данных:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.export_type = ttk.Combobox(
            export_frame, 
            values=["clients", "products", "orders"],
            state="readonly"
        )
        self.export_type.current(0)
        self.export_type.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(export_frame, text="Формат:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.export_format = ttk.Combobox(
            export_frame, 
            values=["CSV", "JSON"],
            state="readonly"
        )
        self.export_format.current(0)
        self.export_format.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Button(
            export_frame, 
            text="Экспорт", 
            command=self.export_data
        ).grid(row=2, column=0, columnspan=2, pady=5)
        
        export_frame.columnconfigure(1, weight=1)
        
        # Import frame
        import_frame = ttk.LabelFrame(tab, text="Импорт данных", padding=10)
        import_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(import_frame, text="Тип данных:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.import_type = ttk.Combobox(
            import_frame, 
            values=["clients", "products", "orders"],
            state="readonly"
        )
        self.import_type.current(0)
        self.import_type.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(import_frame, text="Формат:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.import_format = ttk.Combobox(
            import_frame, 
            values=["CSV", "JSON"],
            state="readonly"
        )
        self.import_format.current(0)
        self.import_format.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Button(
            import_frame, 
            text="Импорт", 
            command=self.import_data
        ).grid(row=2, column=0, columnspan=2, pady=5)
        
        import_frame.columnconfigure(1, weight=1)
    
    # Client methods
    def refresh_clients_list(self):
        self.clients_tree.delete(*self.clients_tree.get_children())
        clients = self.db.get_all_clients()
        for client in clients:
            self.clients_tree.insert("", tk.END, values=(
                client.id,
                client.name,
                client.email,
                client.phone,
                client.address,
                client.registration_date,
                "Да" if isinstance(client, PremiumClient) else "Нет"
            ))
    
    def on_client_search(self, event):
        search_term = self.client_search_entry.get()
        if not search_term:
            self.refresh_clients_list()
            return
        
        self.clients_tree.delete(*self.clients_tree.get_children())
        clients = self.db.search_clients(search_term)
        for client in clients:
            self.clients_tree.insert("", tk.END, values=(
                client.id,
                client.name,
                client.email,
                client.phone,
                client.address,
                client.registration_date,
                "Да" if isinstance(client, PremiumClient) else "Нет"
            ))
    
    def clear_client_search(self):
        self.client_search_entry.delete(0, tk.END)
        self.refresh_clients_list()
    
    def sort_clients(self, column):
        # This is a simplified sorting - in a real app you'd implement proper sorting
        self.refresh_clients_list()
    
    def on_client_select(self, event):
        selected = self.clients_tree.focus()
        if not selected:
            return
        
        values = self.clients_tree.item(selected, 'values')
        if not values:
            return
        
        self.clear_client_form()
        
        self.client_name_entry.insert(0, values[1])
        self.client_email_entry.insert(0, values[2])
        self.client_phone_entry.insert(0, values[3])
        self.client_address_entry.insert(0, values[4])
        self.client_premium_var.set(values[6] == "Да")
    
    def clear_client_form(self):
        self.client_name_entry.delete(0, tk.END)
        self.client_email_entry.delete(0, tk.END)
        self.client_phone_entry.delete(0, tk.END)
        self.client_address_entry.delete(0, tk.END)
        self.client_premium_var.set(False)
    
    def add_client(self):
        try:
            name = self.client_name_entry.get()
            email = self.client_email_entry.get()
            phone = self.client_phone_entry.get()
            address = self.client_address_entry.get()
            is_premium = self.client_premium_var.get()
            
            if not all([name, email, phone, address]):
                messagebox.showerror("Ошибка", "Все поля обязательны для заполнения")
                return
            
            if is_premium:
                client = PremiumClient(
                    id=0,  # Will be auto-generated
                    name=name,
                    email=email,
                    phone=phone,
                    address=address
                )
            else:
                client = Client(
                    id=0,  # Will be auto-generated
                    name=name,
                    email=email,
                    phone=phone,
                    address=address
                )
            
            self.db.add_client(client)
            self.refresh_clients_list()
            self.clear_client_form()
            self.update_client_comboboxes()
            messagebox.showinfo("Успех", "Клиент добавлен успешно")
        except ValidationError as e:
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить клиента: {str(e)}")
    
    def update_client(self):
        selected = self.clients_tree.focus()
        if not selected:
            messagebox.showerror("Ошибка", "Клиент не выбран")
            return
        
        client_id = self.clients_tree.item(selected, 'values')[0]
        try:
            name = self.client_name_entry.get()
            email = self.client_email_entry.get()
            phone = self.client_phone_entry.get()
            address = self.client_address_entry.get()
            is_premium = self.client_premium_var.get()
            
            if not all([name, email, phone, address]):
                messagebox.showerror("Ошибка", "Все поля обязательны для заполнения")
                return
            
            # In a real app, we would update the client in the database
            # For this example, we'll just show a message
            messagebox.showinfo("Информация", f"Клиент {client_id} будет обновлен в реальной реализации")
            
            self.refresh_clients_list()
            self.clear_client_form()
            self.update_client_comboboxes()
        except ValidationError as e:
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить клиента: {str(e)}")

    def delete_client(self):
        selected = self.clients_tree.focus()
        if not selected:
            messagebox.showerror("Error", "No client selected")
            return

        client_id = self.clients_tree.item(selected, 'values')[0]
        if messagebox.askyesno("Confirm", f"Delete client {client_id}?"):
            try:
                # РЕАЛЬНОЕ УДАЛЕНИЕ ИЗ БАЗЫ ДАННЫХ
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    # Сначала удаляем связанные заказы и элементы заказов
                    cursor.execute("SELECT id FROM orders WHERE client_id = ?", (client_id,))
                    order_ids = [row[0] for row in cursor.fetchall()]

                    for order_id in order_ids:
                        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))

                    cursor.execute("DELETE FROM orders WHERE client_id = ?", (client_id,))
                    # Затем удаляем самого клиента
                    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
                    conn.commit()

                # ОБНОВЛЯЕМ ИНТЕРФЕЙС
                self.refresh_clients_list()
                self.clear_client_form()
                self.update_client_comboboxes()
                messagebox.showinfo("Success", f"Client {client_id} deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete client: {str(e)}")
    
    # Product methods
    def refresh_products_list(self):
        self.products_tree.delete(*self.products_tree.get_children())
        products = self.db.get_all_products()
        for product in products:
            self.products_tree.insert("", tk.END, values=(
                product.id,
                product.name,
                f"{product.price}₽",
                product.category,
                product.stock
            ))
    
    def on_product_search(self, event):
        search_term = self.product_search_entry.get()
        if not search_term:
            self.refresh_products_list()
            return
        
        self.products_tree.delete(*self.products_tree.get_children())
        products = self.db.search_products(search_term)
        for product in products:
            self.products_tree.insert("", tk.END, values=(
                product.id,
                product.name,
                f"{product.price}₽",
                product.category,
                product.stock
            ))
    
    def clear_product_search(self):
        self.product_search_entry.delete(0, tk.END)
        self.refresh_products_list()
    
    def sort_products(self, column):
        # This is a simplified sorting - in a real app you'd implement proper sorting
        self.refresh_products_list()
    
    def on_product_select(self, event):
        selected = self.products_tree.focus()
        if not selected:
            return
        
        values = self.products_tree.item(selected, 'values')
        if not values:
            return
        
        self.clear_product_form()
        
        self.product_name_entry.insert(0, values[1])
        self.product_price_entry.insert(0, values[2].replace("₽", ""))
        self.product_category_entry.insert(0, values[3])
        self.product_stock_entry.insert(0, values[4])
    
    def clear_product_form(self):
        self.product_name_entry.delete(0, tk.END)
        self.product_price_entry.delete(0, tk.END)
        self.product_category_entry.delete(0, tk.END)
        self.product_stock_entry.delete(0, tk.END)
    
    def add_product(self):
        try:
            name = self.product_name_entry.get()
            price = float(self.product_price_entry.get())
            category = self.product_category_entry.get()
            stock = int(self.product_stock_entry.get())
            
            if not all([name, category]):
                messagebox.showerror("Ошибка", "Название и категория обязательны")
                return
            
            product = Product(
                id=0,  # Will be auto-generated
                name=name,
                price=price,
                category=category,
                stock=stock
            )
            
            self.db.add_product(product)
            self.refresh_products_list()
            self.clear_product_form()
            self.update_product_comboboxes()
            messagebox.showinfo("Успех", "Товар добавлен успешно")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверное числовое значение")
        except ValidationError as e:
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить товар: {str(e)}")
    
    def update_product(self):
        selected = self.products_tree.focus()
        if not selected:
            messagebox.showerror("Ошибка", "Товар не выбран")
            return
        
        product_id = self.products_tree.item(selected, 'values')[0]
        try:
            name = self.product_name_entry.get()
            price = float(self.product_price_entry.get())
            category = self.product_category_entry.get()
            stock = int(self.product_stock_entry.get())
            
            if not all([name, category]):
                messagebox.showerror("Ошибка", "Название и категория обязательны")
                return
            
            # In a real app, we would update the product in the database
            # For this example, we'll just show a message
            messagebox.showinfo("Информация", f"Товар {product_id} будет обновлен в реальной реализации")
            
            self.refresh_products_list()
            self.clear_product_form()
            self.update_product_comboboxes()
        except ValueError:
            messagebox.showerror("Ошибка", "Неверное числовое значение")
        except ValidationError as e:
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить товар: {str(e)}")

    def delete_product(self):
        selected = self.products_tree.focus()
        if not selected:
            messagebox.showerror("Error", "No product selected")
            return

        product_id = self.products_tree.item(selected, 'values')[0]
        if messagebox.askyesno("Confirm", f"Delete product {product_id}?"):
            try:
                # РЕАЛЬНОЕ УДАЛЕНИЕ ИЗ БАЗЫ ДАННЫХ
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    # Удаляем связанные элементы заказов
                    cursor.execute("DELETE FROM order_items WHERE product_id = ?", (product_id,))
                    # Затем удаляем сам товар
                    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                    conn.commit()

                # ОБНОВЛЯЕМ ИНТЕРФЕЙС
                self.refresh_products_list()
                self.clear_product_form()
                self.update_product_comboboxes()
                messagebox.showinfo("Success", f"Product {product_id} deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product: {str(e)}")
    
    # Order methods
    def refresh_orders_list(self):
        self.orders_tree.delete(*self.orders_tree.get_children())
        orders = self.db.get_all_orders()
        for order in orders:
            client = self.db.get_client(order.client_id)
            client_name = client.name if client else f"Клиент {order.client_id}"
            
            item_count = len(order.items)
            total_amount = order.total_amount
            
            self.orders_tree.insert("", tk.END, values=(
                order.id,
                client_name,
                order.order_date,
                order.status.capitalize(),
                f"{total_amount}₽",
                f"{item_count} товаров"
            ))
    
    def on_order_filter(self, event):
        client_filter = self.order_client_filter.get()
        status_filter = self.order_status_filter.get()
        
        # In a real app, we would filter orders based on these criteria
        # For this example, we'll just refresh the list
        self.refresh_orders_list()
    
    def clear_order_filter(self):
        self.order_client_filter.set('')
        self.order_status_filter.current(0)
        self.refresh_orders_list()
    
    def sort_orders(self, column):
        # This is a simplified sorting - in a real app you'd implement proper sorting
        self.refresh_orders_list()
    
    def on_order_select(self, event):
        selected = self.orders_tree.focus()
        if not selected:
            return
        
        order_id = self.orders_tree.item(selected, 'values')[0]
        order = self.db.get_order(order_id)
        if not order:
            return
        
        self.clear_order_form()
        
        # Set order details
        self.order_client_combobox.set(order.client_id)
        self.order_date_entry.delete(0, tk.END)
        self.order_date_entry.insert(0, order.order_date)
        self.order_status_combobox.set(order.status)
        
        # Add items to the items tree
        self.order_items_tree.delete(*self.order_items_tree.get_children())
        for item in order.items:
            product = self.db.get_product(item.product_id)
            product_name = product.name if product else f"Товар {item.product_id}"
            
            self.order_items_tree.insert("", tk.END, values=(
                product_name,
                f"{item.unit_price}₽",
                item.quantity,
                f"{item.total_price}₽"
            ))
        
        # Update total
        self.order_total_label.config(text=f"{order.total_amount}₽")
    
    def clear_order_form(self):
        self.order_client_combobox.set('')
        self.order_date_entry.delete(0, tk.END)
        self.order_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.order_status_combobox.current(0)
        self.order_items_tree.delete(*self.order_items_tree.get_children())
        self.order_total_label.config(text="0₽")
        self.order_product_combobox.set('')
        self.order_quantity_entry.delete(0, tk.END)
        self.order_quantity_entry.insert(0, "1")

    def add_order_item(self):
        product_selection = self.order_product_combobox.get()
        if not product_selection:
            messagebox.showerror("Error", "Please select a product")
            return

        try:
            # Парсим ID товара из комбобокса (формат: "id: name")
            product_id = int(product_selection.split(':')[0].strip())
            quantity = int(self.order_quantity_entry.get())

            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            product = self.db.get_product(product_id)
            if not product:
                messagebox.showerror("Error", "Selected product not found")
                return

            if product.stock < quantity:
                messagebox.showerror("Error", f"Insufficient stock. Available: {product.stock}")
                return

            # Добавляем в дерево items
            self.order_items_tree.insert("", tk.END, values=(
                product.name,
                f"{product.price:.2f} Р",
                quantity,
                f"{product.price * quantity:.2f} Р"
            ))

            # Обновляем общую сумму - ПРОСТОЙ И НАДЕЖНЫЙ СПОСОБ
            # Пересчитываем всю сумму заново из всех items
            total = 0.0
            for child in self.order_items_tree.get_children():
                values = self.order_items_tree.item(child, 'values')
                item_total = float(values[3].replace(' Р', ''))
                total += item_total

            self.order_total_label.config(text=f"{total:.2f} Р")

            # Очищаем поля
            self.order_product_combobox.set('')
            self.order_quantity_entry.delete(0, tk.END)
            self.order_quantity_entry.insert(0, "1")

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add item: {str(e)}")

    def create_order(self):
        client_selection = self.order_client_combobox.get()
        if not client_selection:
            messagebox.showerror("Error", "Please select a client")
            return

        try:
            # Парсим ID клиента из комбобокса (формат: "id: name")
            client_id = int(client_selection.split(':')[0].strip())

            items = []
            for child in self.order_items_tree.get_children():
                values = self.order_items_tree.item(child, 'values')
                product_name = values[0]
                quantity = int(values[2])

                # Ищем товар по имени
                product = None
                for p in self.db.get_all_products():
                    if p.name == product_name:
                        product = p
                        break

                if not product:
                    messagebox.showerror("Error", f"Product '{product_name}' not found")
                    return

                items.append((product, quantity))

            if not items:
                messagebox.showerror("Error", "Order must have at least one item")
                return

            order = Order(
                id=0,  # Will be auto-generated
                client_id=client_id,
                order_date=self.order_date_entry.get(),
                status=self.order_status_combobox.get()
            )

            for product, quantity in items:
                order.add_item(product, quantity)

            self.db.add_order(order)
            self.refresh_orders_list()
            self.clear_order_form()
            messagebox.showinfo("Success", "Order created successfully")

        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create order: {str(e)}")
    
    def update_order(self):
        selected = self.orders_tree.focus()
        if not selected:
            messagebox.showerror("Ошибка", "Заказ не выбран")
            return
        
        order_id = self.orders_tree.item(selected, 'values')[0]
        try:
            # In a real app, we would update the order in the database
            # For this example, we'll just show a message
            messagebox.showinfo("Информация", f"Заказ {order_id} будет обновлен в реальной реализации")
            
            self.refresh_orders_list()
            self.clear_order_form()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить заказ: {str(e)}")
    
    def delete_order(self):
        selected = self.orders_tree.focus()
        if not selected:
            messagebox.showerror("Ошибка", "Заказ не выбран")
            return
        
        order_id = self.orders_tree.item(selected, 'values')[0]
        if messagebox.askyesno("Подтверждение", f"Удалить заказ {order_id}?"):
            try:
                # In a real app, we would delete the order from the database
                # For this example, we'll just show a message
                messagebox.showinfo("Информация", f"Заказ {order_id} будет удален в реальной реализации")
                
                self.refresh_orders_list()
                self.clear_order_form()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить заказ: {str(e)}")
    
    # Report methods
    def show_top_clients(self):
        self.analyzer.plot_top_clients()
    
    def show_sales_trend(self):
        self.analyzer.plot_sales_trend()
    
    def show_top_products(self):
        self.analyzer.plot_top_products()
    
    def show_category_distribution(self):
        self.analyzer.plot_product_category_distribution()
    
    def show_client_network(self):
        self.analyzer.plot_client_network()
    
    def generate_sales_report(self):
        start_date = self.report_start_date.get()
        end_date = self.report_end_date.get()
        
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return
        
        self.analyzer.generate_sales_report(start_date, end_date)
    
    # Import/Export methods
    def export_data(self):
        entity_type = self.export_type.get()
        file_format = self.export_format.get().lower()
        
        if not entity_type:
            messagebox.showerror("Ошибка", "Выберите тип данных для экспорта")
            return
        
        file_ext = file_format
        file_types = [(f"{file_format.upper()} files", f"*.{file_ext}")]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{file_ext}",
            filetypes=file_types,
            title=f"Экспорт {entity_type} в {file_format.upper()}"
        )
        
        if not file_path:
            return
        
        try:
            if file_format == "csv":
                self.db.export_to_csv(entity_type, file_path)
            elif file_format == "json":
                self.db.export_to_json(entity_type, file_path)
            
            messagebox.showinfo("Успех", f"Данные успешно экспортированы в {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать данные: {str(e)}")
    
    def import_data(self):
        entity_type = self.import_type.get()
        file_format = self.import_format.get().lower()
        
        if not entity_type:
            messagebox.showerror("Ошибка", "Выберите тип данных для импорта")
            return
        
        file_ext = file_format
        file_types = [(f"{file_format.upper()} files", f"*.{file_ext}")]
        
        file_path = filedialog.askopenfilename(
            filetypes=file_types,
            title=f"Импорт {entity_type} из {file_format.upper()}"
        )
        
        if not file_path:
            return
        
        try:
            if file_format == "csv":
                self.db.import_from_csv(entity_type, file_path)
            elif file_format == "json":
                self.db.import_from_json(entity_type, file_path)
            
            # Refresh all views
            self.refresh_clients_list()
            self.refresh_products_list()
            self.refresh_orders_list()
            self.update_client_comboboxes()
            self.update_product_comboboxes()
            
            messagebox.showinfo("Успех", f"Данные успешно импортированы из {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось импортировать данные: {str(e)}")
    
    # Utility methods
    def update_client_comboboxes(self):
        clients = self.db.get_all_clients()
        client_options = [(client.id, client.name) for client in clients]
        
        # Update order client combobox
        self.order_client_combobox['values'] = [f"{id}: {name}" for id, name in client_options]
        
        # Update order filter combobox
        self.order_client_filter['values'] = ["Все"] + [f"{id}: {name}" for id, name in client_options]

    def update_product_comboboxes(self):
        products = self.db.get_all_products()
        # Формат: "id: name"
        product_options = [f"{product.id}: {product.name}" for product in products]

        # Обновляем комбобокс товаров в заказе
        self.order_product_combobox['values'] = product_options