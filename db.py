"""Хранение данных в JSON. SQLite не используется."""
import csv
import json
from pathlib import Path


DATA_PATH = Path(__file__).with_name("shop_data.json")


class Database:
    """Хранилище данных на основе обычного JSON-файла."""

    def __init__(self, path=DATA_PATH):
        self.path = Path(path)
        self.data = {"clients": [], "products": [], "orders": []}
        self.load()
        if not self.data["clients"] and not self.data["products"]:
            self.seed_data()

    def load(self):
        """Загружает данные из JSON."""
        if not self.path.exists():
            self.save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                loaded = json.load(file)
            self.data = {
                "clients": loaded.get("clients", []),
                "products": loaded.get("products", []),
                "orders": loaded.get("orders", [])
            }
        except (OSError, json.JSONDecodeError):
            self.data = {"clients": [], "products": [], "orders": []}
            self.save()

    def save(self):
        """Сохраняет данные в JSON."""
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=2)

    def _next_id(self, collection):
        """Возвращает следующий ID."""
        return max([item["id"] for item in collection] or [0]) + 1

    def seed_data(self):
        """Создаёт демонстрационные данные."""
        clients = [
            ("Иван Петров", "ivan@example.com", "+7 900 111-11-11", "Москва"),
            ("Анна Смирнова", "anna@example.com", "+7 900 222-22-22", "Санкт-Петербург"),
            ("Максим Орлов", "max@example.com", "+7 900 333-33-33", "Казань"),
            ("Елена Волкова", "elena@example.com", "+7 900 444-44-44", "Москва"),
            ("Дмитрий Соколов", "dmitry@example.com", "+7 900 555-55-55", "Новосибирск"),
            ("Ольга Морозова", "olga@example.com", "+7 900 666-66-66", "Екатеринбург")
        ]
        for row in clients:
            self.add_client(*row, save=False)

        products = [
            ("Ноутбук", 79990, 15), ("Смартфон", 49990, 30),
            ("Наушники", 7990, 50), ("Клавиатура", 5990, 40),
            ("Монитор", 29990, 20)
        ]
        for name, price, stock in products:
            self.data["products"].append({
                "id": self._next_id(self.data["products"]),
                "name": name, "price": float(price), "stock": int(stock)
            })

        client_ids = [x["id"] for x in self.data["clients"]]
        product_ids = [x["id"] for x in self.data["products"]]
        orders = [
            (client_ids[0], "2026-09-01", "Завершён"),
            (client_ids[0], "2026-09-05", "Завершён"),
            (client_ids[1], "2026-09-06", "В обработке"),
            (client_ids[1], "2026-09-08", "Завершён"),
            (client_ids[2], "2026-09-10", "Новый"),
            (client_ids[3], "2026-09-12", "Завершён"),
            (client_ids[3], "2026-09-14", "В обработке"),
            (client_ids[4], "2026-09-15", "Завершён"),
            (client_ids[5], "2026-09-16", "Новый"),
            (client_ids[5], "2026-09-18", "Завершён")
        ]
        for number, (client_id, date, status) in enumerate(orders, 1):
            product = self.get_product(product_ids[(number - 1) % len(product_ids)])
            quantity = number % 3 + 1
            self.data["orders"].append({
                "id": self._next_id(self.data["orders"]),
                "client_id": client_id, "date": date, "status": status,
                "total": product["price"] * quantity,
                "items": [{
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "quantity": quantity,
                    "price": product["price"]
                }]
            })
        self.save()

    def add_client(self, name, email, phone, city, save=True):
        """Добавляет клиента."""
        if any(x["email"].lower() == email.lower() for x in self.data["clients"]):
            raise ValueError("Клиент с таким email уже существует.")
        client_id = self._next_id(self.data["clients"])
        self.data["clients"].append({
            "id": client_id, "name": name, "email": email,
            "phone": phone, "city": city
        })
        if save:
            self.save()
        return client_id

    def get_clients(self, search=""):
        """Возвращает клиентов с поиском."""
        result = self.data["clients"][:]
        if search:
            text = search.lower()
            result = [
                x for x in result
                if any(text in str(x[key]).lower()
                       for key in ("name", "email", "phone", "city"))
            ]
        return sorted(result, key=lambda x: x["name"].lower())

    def get_products(self):
        """Возвращает товары."""
        return sorted(self.data["products"], key=lambda x: x["name"].lower())

    def get_product(self, product_id):
        """Ищет товар по ID."""
        return next((x for x in self.data["products"] if x["id"] == product_id), None)

    def add_order(self, client_id, date, status, items):
        """Создаёт заказ и изменяет остатки товаров."""
        if not items:
            raise ValueError("Заказ должен содержать товар.")
        if not any(x["id"] == client_id for x in self.data["clients"]):
            raise ValueError("Клиент не найден.")

        prepared = []
        total = 0.0
        for product_id, quantity in items:
            if quantity <= 0:
                raise ValueError("Количество должно быть положительным.")
            product = self.get_product(product_id)
            if product is None:
                raise ValueError("Товар не найден.")
            if product["stock"] < quantity:
                raise ValueError("Недостаточно товара на складе.")
            prepared.append({
                "product_id": product_id,
                "product_name": product["name"],
                "quantity": quantity,
                "price": product["price"]
            })
            total += product["price"] * quantity

        for item in prepared:
            self.get_product(item["product_id"])["stock"] -= item["quantity"]

        order_id = self._next_id(self.data["orders"])
        self.data["orders"].append({
            "id": order_id, "client_id": client_id, "date": date,
            "status": status, "total": total, "items": prepared
        })
        self.save()
        return order_id

    def get_orders(self, search="", sort_by="date"):
        """Возвращает заказы с поиском и сортировкой."""
        result = []
        for order in self.data["orders"]:
            client = next(
                (x for x in self.data["clients"] if x["id"] == order["client_id"]),
                {"name": "Неизвестный клиент", "email": ""}
            )
            row = dict(order)
            row["client_name"] = client["name"]
            row["email"] = client["email"]
            result.append(row)

        if search:
            text = search.lower()
            result = [
                x for x in result
                if text in x["client_name"].lower()
                or text in x["status"].lower()
            ]

        key = {
            "total": lambda x: x["total"],
            "client": lambda x: x["client_name"].lower(),
            "date": lambda x: x["date"]
        }.get(sort_by, lambda x: x["date"])
        return sorted(result, key=key)

    def get_order_items(self, order_id):
        """Возвращает товары заказа."""
        order = next((x for x in self.data["orders"] if x["id"] == order_id), None)
        return order.get("items", []) if order else []

    def export_clients_csv(self, path):
        """Экспортирует клиентов в CSV."""
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "name", "email", "phone", "city"])
            for row in self.get_clients():
                writer.writerow([row["id"], row["name"], row["email"], row["phone"], row["city"]])

    def export_orders_csv(self, path):
        """Экспортирует заказы в CSV."""
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "date", "status", "total", "client_name", "email"])
            for row in self.get_orders():
                writer.writerow([row["id"], row["date"], row["status"], row["total"], row["client_name"], row["email"]])

    def export_all_json(self, path):
        """Экспортирует все данные в JSON."""
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=2)

    def import_clients_csv(self, path):
        """Импортирует клиентов из CSV."""
        added = 0
        with open(path, newline="", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                try:
                    self.add_client(row["name"], row["email"], row["phone"], row["city"])
                    added += 1
                except (ValueError, KeyError):
                    pass
        return added

    def close(self):
        """Сохраняет данные перед завершением."""
        self.save()
