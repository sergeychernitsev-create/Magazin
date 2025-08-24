import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional

class ValidationError(Exception):
    pass

@dataclass
class Product:
    id: int
    name: str
    price: float
    category: str
    stock: int = 0
    
    def __post_init__(self):
        if self.price <= 0:
            raise ValidationError("Price must be positive")
        if not self.name.strip():
            raise ValidationError("Product name cannot be empty")

@dataclass
class Client:
    id: int
    name: str
    email: str
    phone: str
    address: str
    registration_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    def __post_init__(self):
        if not self._validate_email():
            raise ValidationError("Invalid email format")
        if not self._validate_phone():
            raise ValidationError("Invalid phone format")
    
    def _validate_email(self) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, self.email) is not None
    
    def _validate_phone(self) -> bool:
        pattern = r'^\+?[1-9]\d{1,14}$'  # E.164 format
        return re.match(pattern, self.phone) is not None

@dataclass
class OrderItem:
    product_id: int
    quantity: int
    unit_price: float
    
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price

@dataclass
class Order:
    id: int
    client_id: int
    items: List[OrderItem] = field(default_factory=list)
    order_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    status: str = "pending"
    
    @property
    def total_amount(self) -> float:
        return sum(item.total_price for item in self.items)
    
    def add_item(self, product: Product, quantity: int):
        if quantity <= 0:
            raise ValidationError("Quantity must be positive")
        if product.stock < quantity:
            raise ValidationError("Insufficient stock")
        
        self.items.append(OrderItem(
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price
        ))
        product.stock -= quantity

class BaseEntity:
    def to_dict(self) -> Dict:
        return self.__dict__
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)

class PremiumClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discount_rate = 0.1  # 10% discount for premium clients
    
    def apply_discount(self, amount: float) -> float:
        return amount * (1 - self.discount_rate)