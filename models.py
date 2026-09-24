"""Модели клиентов, товаров и заказов."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Client:
    """Клиент интернет-магазина."""
    id: int = None
    name: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""

    def __post_init__(self):
        self.name = self.name.strip()
        self.email = self.email.strip()
        self.phone = self.phone.strip()
        self.city = self.city.strip()

    def contact(self):
        """Возвращает контактные данные."""
        return "{}, {}".format(self.email, self.phone)


@dataclass
class Product:
    """Товар интернет-магазина."""
    id: int = None
    name: str = ""
    price: float = 0.0
    stock: int = 0

    def total_for(self, quantity):
        """Стоимость заданного количества товара."""
        return self.price * quantity


@dataclass
class Order:
    """Заказ клиента."""
    id: int = None
    client_id: int = 0
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    status: str = "Новый"
    total: float = 0.0
    items: list = field(default_factory=list)

    def add_item(self, product, quantity):
        """Добавляет товар в заказ."""
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным.")
        self.items.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": quantity,
            "price": product.price
        })
        self.total += product.total_for(quantity)


class BaseEntity:
    """Базовый класс для демонстрации наследования."""
    entity_type = "entity"

    def describe(self):
        """Возвращает описание типа объекта."""
        return "Тип объекта: {}".format(self.entity_type)


class CustomerEntity(BaseEntity):
    """Производный класс клиента."""
    entity_type = "customer"


class OrderEntity(BaseEntity):
    """Производный класс заказа."""
    entity_type = "order"


class ProductEntity(BaseEntity):
    """Производный класс товара."""
    entity_type = "product"
