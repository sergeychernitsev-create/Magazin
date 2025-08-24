import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import networkx as nx
from typing import List, Dict
from datetime import datetime
from db import Database

class DataAnalyzer:
    def __init__(self, db: Database):
        self.db = db
    
    def plot_top_clients(self, limit: int = 5):
        """Визуализация топ клиентов по количеству заказов"""
        top_clients = self.db.get_top_clients(limit)
        if not top_clients:
            print("Нет данных о клиентах")
            return
        
        df = pd.DataFrame(top_clients)
        df['name'] = df['name'].str[:15] + '...'  # Обрезаем длинные имена
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x='order_count', y='name', data=df, palette='viridis')
        plt.title(f'Топ {limit} клиентов по количеству заказов')
        plt.xlabel('Количество заказов')
        plt.ylabel('Имя клиента')
        plt.tight_layout()
        plt.show()
    
    def plot_sales_trend(self):
        """График динамики продаж по датам"""
        sales_data = self.db.get_sales_by_date()
        if not sales_data:
            print("Нет данных о продажах")
            return
        
        df = pd.DataFrame(sales_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        plt.figure(figsize=(12, 6))
        
        # График количества заказов
        plt.subplot(1, 2, 1)
        plt.plot(df['date'], df['order_count'], marker='o', color='b')
        plt.title('Количество заказов по дням')
        plt.xlabel('Дата')
        plt.ylabel('Количество заказов')
        plt.grid(True)
        
        # График суммы продаж
        plt.subplot(1, 2, 2)
        plt.plot(df['date'], df['total_amount'], marker='o', color='r')
        plt.title('Выручка по дням')
        plt.xlabel('Дата')
        plt.ylabel('Сумма (₽)')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def plot_top_products(self, limit: int = 10):
        """Топ товаров по количеству продаж и выручке"""
        product_sales = self.db.get_product_sales()
        if not product_sales:
            print("Нет данных о продажах товаров")
            return
        
        df = pd.DataFrame(product_sales)
        df = df[df['total_quantity'] > 0].sort_values('total_quantity', ascending=False).head(limit)
        df['name'] = df['name'].str[:15] + '...'  # Обрезаем длинные названия
        
        plt.figure(figsize=(12, 6))
        
        # График по количеству
        plt.subplot(1, 2, 1)
        sns.barplot(x='total_quantity', y='name', data=df, palette='coolwarm')
        plt.title(f'Топ {limit} товаров по количеству продаж')
        plt.xlabel('Количество продаж')
        plt.ylabel('Название товара')
        
        # График по выручке
        plt.subplot(1, 2, 2)
        sns.barplot(x='total_revenue', y='name', data=df, palette='coolwarm')
        plt.title(f'Топ {limit} товаров по выручке')
        plt.xlabel('Общая выручка (₽)')
        plt.ylabel('')
        
        plt.tight_layout()
        plt.show()
    
    def plot_product_category_distribution(self):
        """Распределение продаж по категориям"""
        product_sales = self.db.get_product_sales()
        if not product_sales:
            print("Нет данных о продажах товаров")
            return
        
        df = pd.DataFrame(product_sales)
        category_stats = df.groupby('category').agg({
            'total_quantity': 'sum',
            'total_revenue': 'sum'
        }).reset_index()
        
        plt.figure(figsize=(12, 6))
        
        # Круговая диаграмма по количеству
        plt.subplot(1, 2, 1)
        plt.pie(
            category_stats['total_quantity'],
            labels=category_stats['category'],
            autopct='%1.1f%%',
            startangle=90
        )
        plt.title('Распределение продаж по категориям (количество)')
        
        # Круговая диаграмма по выручке
        plt.subplot(1, 2, 2)
        plt.pie(
            category_stats['total_revenue'],
            labels=category_stats['category'],
            autopct='%1.1f%%',
            startangle=90
        )
        plt.title('Распределение продаж по категориям (выручка)')
        
        plt.tight_layout()
        plt.show()
    
    def plot_client_network(self):
        """Граф связей клиентов и товаров"""
        orders = self.db.get_all_orders()
        if not orders:
            print("Нет данных о заказах")
            return
        
        # Создаем граф
        G = nx.Graph()
        
        # Добавляем клиентов как узлы
        clients = self.db.get_all_clients()
        for client in clients:
            G.add_node(client.id, label=client.name, type='client')
        
        # Добавляем товары как узлы и связи между клиентами и товарами
        for order in orders:
            for item in order.items:
                product = self.db.get_product(item.product_id)
                if product:
                    if product.id not in G:
                        G.add_node(product.id, label=product.name, type='product')
                    G.add_edge(order.client_id, product.id, weight=item.quantity)
        
        # Рисуем граф
        plt.figure(figsize=(12, 12))
        
        # Разделяем узлы клиентов и товаров
        client_nodes = [n for n in G.nodes if G.nodes[n]['type'] == 'client']
        product_nodes = [n for n in G.nodes if G.nodes[n]['type'] == 'product']
        
        # Позиционируем узлы
        pos = nx.spring_layout(G, k=0.3, iterations=50)
        
        # Рисуем узлы
        nx.draw_networkx_nodes(
            G, pos, 
            nodelist=client_nodes, 
            node_color='lightblue', 
            node_size=500,
            label='Клиенты'
        )
        nx.draw_networkx_nodes(
            G, pos, 
            nodelist=product_nodes, 
            node_color='lightgreen', 
            node_size=300,
            label='Товары'
        )
        
        # Рисуем связи
        edges = G.edges(data=True)
        nx.draw_networkx_edges(
            G, pos, 
            edgelist=edges,
            width=[d['weight']*0.1 for (u, v, d) in edges],
            alpha=0.5
        )
        
        # Подписи узлов
        node_labels = {n: G.nodes[n]['label'] for n in G.nodes}
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)
        
        plt.title("Сеть покупок: Клиенты-Товары")
        plt.legend()
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def generate_sales_report(self, start_date: str, end_date: str):
        """Генерация отчета о продажах за период"""
        orders = self.db.get_orders_by_date_range(start_date, end_date)
        if not orders:
            print(f"Заказы не найдены в период с {start_date} по {end_date}")
            return
        
        # Расчет метрик
        total_orders = len(orders)
        total_revenue = sum(order.total_amount for order in orders)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Анализ товаров
        product_sales = {}
        for order in orders:
            for item in order.items:
                if item.product_id not in product_sales:
                    product_sales[item.product_id] = {
                        'quantity': 0,
                        'revenue': 0.0,
                        'product': self.db.get_product(item.product_id)
                    }
                product_sales[item.product_id]['quantity'] += item.quantity
                product_sales[item.product_id]['revenue'] += item.total_price
        
        top_products = sorted(
            product_sales.values(),
            key=lambda x: x['revenue'],
            reverse=True
        )[:5]
        
        # Вывод отчета
        print(f"\n=== Отчет о продажах ({start_date} по {end_date}) ===")
        print(f"Всего заказов: {total_orders}")
        print(f"Общая выручка: {total_revenue}₽")
        print(f"Средний чек: {avg_order_value}₽")
        
        print("\nТоп товаров по выручке:")
        for i, product in enumerate(top_products, 1):
            p = product['product']
            if p:
                print(f"{i}. {p.name} - {product['quantity']} шт. проданно ({product['revenue']}₽)")
        
        # График продаж
        self.plot_sales_trend()