import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import Database
from models import Client, Product, Order, CustomerEntity
from analysis import top_clients_by_orders, orders_dynamics
from gui import validate_email, validate_phone, sort_orders


class TestProject(unittest.TestCase):

    def test_models_and_oop(self):
        client = Client(name=" Иван ", email="a@test.ru", phone="+7999", city="Москва")
        self.assertEqual(client.name, "Иван")
        product = Product(id=1, name="Товар", price=100)
        order = Order()
        order.add_item(product, 3)
        self.assertEqual(order.total, 300)
        self.assertEqual(CustomerEntity().describe(), "Тип объекта: customer")

    def test_json_storage(self):
        temp = tempfile.TemporaryDirectory()
        path = Path(temp.name) / "data.json"
        db = Database(path)
        before = len(db.get_clients())
        db.add_client("Тест", "unique@test.ru", "+7 900 000-00-00", "Москва")
        db2 = Database(path)
        self.assertEqual(len(db2.get_clients()), before + 1)
        db.close()
        db2.close()
        temp.cleanup()

    def test_order(self):
        temp = tempfile.TemporaryDirectory()
        path = Path(temp.name) / "data.json"
        db = Database(path)
        client = db.get_clients()[0]
        product = db.get_products()[0]
        old_stock = product["stock"]
        db.add_order(client["id"], "2026-09-24", "Новый", [(product["id"], 1)])
        self.assertEqual(product["stock"], old_stock - 1)
        self.assertEqual(len(db.get_orders()), 11)
        db.close()
        temp.cleanup()

    def test_analysis(self):
        temp = tempfile.TemporaryDirectory()
        path = Path(temp.name) / "data.json"
        db = Database(path)
        self.assertEqual(top_clients_by_orders(db)[0][1], 2)
        self.assertEqual(orders_dynamics(db)[0][0], "2026-09-01")
        db.close()
        temp.cleanup()

    def test_regex_and_sorting(self):
        self.assertTrue(validate_email("student@example.com"))
        self.assertFalse(validate_email("wrong-email"))
        self.assertTrue(validate_phone("+7 900 123-45-67"))
        self.assertFalse(validate_phone("abc"))
        rows = [
            {"date": "2026-09-03", "total": 500, "client_name": "B"},
            {"date": "2026-09-01", "total": 100, "client_name": "A"}
        ]
        self.assertEqual(sort_orders(rows, "total")[0]["total"], 100)


if __name__ == "__main__":
    unittest.main()
