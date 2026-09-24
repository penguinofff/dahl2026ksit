"""Графический интерфейс Tkinter."""
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

from db import Database
import analysis


EMAIL_RE = re.compile(
    r"^[A-Za-zА-Яа-яЁё0-9._%+-]+@[A-Za-zА-Яа-яЁё0-9.-]+\.[A-Za-zА-Яа-яЁё]{2,}$"
)
PHONE_RE = re.compile(r"^\+?[0-9 ()-]{7,20}$")


def validate_email(email):
    """Проверяет email."""
    return bool(EMAIL_RE.fullmatch(email.strip()))


def validate_phone(phone):
    """Проверяет телефон."""
    return bool(PHONE_RE.fullmatch(phone.strip()))


def sort_orders(items, key="date"):
    """Собственная сортировка заказов."""
    if key == "total":
        return sorted(items, key=lambda x: float(x["total"]))
    if key == "client":
        return sorted(items, key=lambda x: x["client_name"].lower())
    return sorted(items, key=lambda x: x["date"])


class OrderManagerApp:
    """Главное окно приложения."""

    def __init__(self):
        self.db = Database()
        self.root = tk.Tk()
        self.root.title("Управление интернет-магазином")
        self.root.geometry("1100x700")
        self.build_ui()
        self.refresh_all()

    def build_ui(self):
        """Создаёт интерфейс."""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.clients_tab = ttk.Frame(notebook)
        self.products_tab = ttk.Frame(notebook)
        self.orders_tab = ttk.Frame(notebook)
        self.analysis_tab = ttk.Frame(notebook)

        notebook.add(self.clients_tab, text="Клиенты")
        notebook.add(self.products_tab, text="Товары")
        notebook.add(self.orders_tab, text="Заказы")
        notebook.add(self.analysis_tab, text="Аналитика")

        self.build_clients()
        self.build_products()
        self.build_orders()
        self.build_analysis()

        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(bottom, text="Экспорт CSV", command=self.export_csv).pack(side="left", padx=4)
        ttk.Button(bottom, text="Импорт клиентов CSV", command=self.import_clients).pack(side="left", padx=4)
        ttk.Button(bottom, text="Экспорт JSON", command=self.export_json).pack(side="left", padx=4)
        ttk.Button(bottom, text="Обновить", command=self.refresh_all).pack(side="right", padx=4)

    def build_clients(self):
        """Создаёт вкладку клиентов."""
        form = ttk.LabelFrame(self.clients_tab, text="Регистрация клиента")
        form.pack(fill="x", padx=10, pady=10)

        self.client_name = tk.StringVar()
        self.client_email = tk.StringVar()
        self.client_phone = tk.StringVar()
        self.client_city = tk.StringVar()

        fields = [
            ("Имя", self.client_name),
            ("Email", self.client_email),
            ("Телефон", self.client_phone),
            ("Город", self.client_city)
        ]
        for col, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=col, padx=5, pady=5)
            ttk.Entry(form, textvariable=variable, width=25).grid(row=1, column=col, padx=5, pady=5)

        ttk.Button(form, text="Добавить клиента", command=self.add_client).grid(row=1, column=4, padx=10)

        search = ttk.Frame(self.clients_tab)
        search.pack(fill="x", padx=10)
        self.client_search = tk.StringVar()
        ttk.Label(search, text="Поиск:").pack(side="left")
        ttk.Entry(search, textvariable=self.client_search).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(search, text="Найти", command=self.refresh_clients).pack(side="left")

        columns = ("id", "name", "email", "phone", "city")
        self.client_tree = ttk.Treeview(self.clients_tab, columns=columns, show="headings")
        titles = {"id": "ID", "name": "Имя", "email": "Email", "phone": "Телефон", "city": "Город"}
        for column in columns:
            self.client_tree.heading(column, text=titles[column])
            self.client_tree.column(column, width=150)
        self.client_tree.column("id", width=50)
        self.client_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def build_products(self):
        """Создаёт вкладку товаров."""
        frame = ttk.Frame(self.products_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("id", "name", "price", "stock")
        self.product_tree = ttk.Treeview(frame, columns=columns, show="headings")
        titles = {"id": "ID", "name": "Товар", "price": "Цена", "stock": "Остаток"}
        for column in columns:
            self.product_tree.heading(column, text=titles[column])
            self.product_tree.column(column, width=200)
        self.product_tree.column("id", width=50)
        self.product_tree.pack(fill="both", expand=True)

    def build_orders(self):
        """Создаёт вкладку заказов."""
        top = ttk.Frame(self.orders_tab)
        top.pack(fill="x", padx=10, pady=10)
        self.order_search = tk.StringVar()
        ttk.Label(top, text="Поиск клиента/статуса:").pack(side="left")
        ttk.Entry(top, textvariable=self.order_search, width=25).pack(side="left", padx=5)
        ttk.Button(top, text="Найти", command=self.refresh_orders).pack(side="left")
        ttk.Label(top, text="Сортировка:").pack(side="left", padx=(20, 5))
        self.order_sort = tk.StringVar(value="date")
        ttk.Combobox(top, textvariable=self.order_sort,
                     values=("date", "total", "client"),
                     state="readonly", width=12).pack(side="left")
        ttk.Button(top, text="Применить", command=self.refresh_orders).pack(side="left", padx=5)
        ttk.Button(top, text="Создать заказ", command=self.open_order_dialog).pack(side="right")

        columns = ("id", "date", "client", "status", "total")
        self.order_tree = ttk.Treeview(self.orders_tab, columns=columns, show="headings")
        titles = {"id": "ID", "date": "Дата", "client": "Клиент", "status": "Статус", "total": "Сумма"}
        for column in columns:
            self.order_tree.heading(column, text=titles[column])
            self.order_tree.column(column, width=180)
        self.order_tree.column("id", width=50)
        self.order_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.order_tree.bind("<Double-1>", self.show_order)

    def build_analysis(self):
        """Создаёт вкладку аналитики."""
        frame = ttk.Frame(self.analysis_tab)
        frame.pack(fill="both", expand=True, padx=30, pady=30)
        ttk.Label(frame, text="Инструменты анализа данных",
                  font=("Arial", 16, "bold")).pack(pady=20)
        ttk.Button(frame, text="TOP-5 клиентов по числу заказов",
                   command=self.show_top_clients).pack(fill="x", pady=8)
        ttk.Button(frame, text="Динамика количества заказов по датам",
                   command=self.show_dynamics).pack(fill="x", pady=8)
        ttk.Button(frame, text="Граф связей клиентов по общим товарам",
                   command=self.show_graph).pack(fill="x", pady=8)

    def add_client(self):
        """Проверяет поля и добавляет клиента."""
        try:
            name, email = self.client_name.get().strip(), self.client_email.get().strip()
            phone, city = self.client_phone.get().strip(), self.client_city.get().strip()
            if not all((name, email, phone, city)):
                raise ValueError("Заполните все поля.")
            if not validate_email(email):
                raise ValueError("Некорректный email.")
            if not validate_phone(phone):
                raise ValueError("Некорректный номер телефона.")
            self.db.add_client(name, email, phone, city)
            for variable in (self.client_name, self.client_email, self.client_phone, self.client_city):
                variable.set("")
            self.refresh_clients()
            messagebox.showinfo("Готово", "Клиент добавлен.")
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))

    def open_order_dialog(self):
        """Открывает форму создания заказа."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание заказа")
        dialog.geometry("500x420")
        dialog.grab_set()

        clients = self.db.get_clients()
        products = self.db.get_products()
        client_map = {"{}: {}".format(x["id"], x["name"]): x["id"] for x in clients}
        product_map = {"{}: {} — {:.2f}".format(x["id"], x["name"], x["price"]): x["id"] for x in products}

        ttk.Label(dialog, text="Клиент").pack(pady=(15, 3))
        client_var = tk.StringVar()
        ttk.Combobox(dialog, textvariable=client_var, values=list(client_map),
                     state="readonly", width=40).pack()

        ttk.Label(dialog, text="Товар").pack(pady=(15, 3))
        product_var = tk.StringVar()
        ttk.Combobox(dialog, textvariable=product_var, values=list(product_map),
                     state="readonly", width=40).pack()

        ttk.Label(dialog, text="Количество").pack(pady=(15, 3))
        quantity_var = tk.StringVar(value="1")
        ttk.Entry(dialog, textvariable=quantity_var, width=10).pack()

        ttk.Label(dialog, text="Статус").pack(pady=(15, 3))
        status_var = tk.StringVar(value="Новый")
        ttk.Combobox(dialog, textvariable=status_var,
                     values=("Новый", "В обработке", "Завершён", "Отменён"),
                     state="readonly").pack()

        def save_order():
            try:
                client_id = client_map[client_var.get()]
                product_id = product_map[product_var.get()]
                quantity = int(quantity_var.get())
                self.db.add_order(client_id, datetime.now().strftime("%Y-%m-%d"),
                                  status_var.get(), [(product_id, quantity)])
                dialog.destroy()
                self.refresh_all()
                messagebox.showinfo("Готово", "Заказ создан.")
            except Exception as exc:
                messagebox.showerror("Ошибка", str(exc))

        ttk.Button(dialog, text="Создать", command=save_order).pack(pady=25)

    def show_order(self, _event=None):
        """Показывает товары выбранного заказа."""
        selected = self.order_tree.selection()
        if not selected:
            return
        order_id = int(self.order_tree.item(selected[0])["values"][0])
        items = self.db.get_order_items(order_id)
        text = "\n".join("{} — {} шт. × {:.2f}".format(
            x["product_name"], x["quantity"], x["price"]) for x in items)
        messagebox.showinfo("Заказ №{}".format(order_id), text or "Товары отсутствуют.")

    def refresh_clients(self):
        """Обновляет клиентов."""
        for item in self.client_tree.get_children():
            self.client_tree.delete(item)
        for row in self.db.get_clients(self.client_search.get()):
            self.client_tree.insert("", "end",
                                    values=(row["id"], row["name"], row["email"], row["phone"], row["city"]))

    def refresh_products(self):
        """Обновляет товары."""
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        for row in self.db.get_products():
            self.product_tree.insert("", "end",
                                    values=(row["id"], row["name"], "{:.2f}".format(row["price"]), row["stock"]))

    def refresh_orders(self):
        """Обновляет заказы."""
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        for row in self.db.get_orders(self.order_search.get(), self.order_sort.get()):
            self.order_tree.insert("", "end",
                                   values=(row["id"], row["date"], row["client_name"],
                                           row["status"], "{:.2f}".format(row["total"])))

    def refresh_all(self):
        """Обновляет все таблицы."""
        self.refresh_clients()
        self.refresh_products()
        self.refresh_orders()

    def show_top_clients(self):
        """Показывает TOP-5."""
        try:
            analysis.show_top_clients(self.db)
        except Exception as exc:
            messagebox.showerror("Ошибка анализа", str(exc))

    def show_dynamics(self):
        """Показывает динамику."""
        try:
            analysis.show_orders_dynamics(self.db)
        except Exception as exc:
            messagebox.showerror("Ошибка анализа", str(exc))

    def show_graph(self):
        """Показывает граф."""
        try:
            analysis.show_client_graph(self.db)
        except ImportError:
            messagebox.showerror("Ошибка", "Установите networkx: pip install networkx")
        except Exception as exc:
            messagebox.showerror("Ошибка анализа", str(exc))

    def export_csv(self):
        """Экспортирует заказы в CSV."""
        try:
            path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV", "*.csv")])
            if path:
                self.db.export_orders_csv(path)
                messagebox.showinfo("Экспорт", "Заказы экспортированы.")
        except Exception as exc:
            messagebox.showerror("Ошибка экспорта", str(exc))

    def import_clients(self):
        """Импортирует клиентов из CSV."""
        try:
            path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
            if path:
                count = self.db.import_clients_csv(path)
                self.refresh_clients()
                messagebox.showinfo("Импорт", "Добавлено клиентов: {}".format(count))
        except Exception as exc:
            messagebox.showerror("Ошибка импорта", str(exc))

    def export_json(self):
        """Экспортирует данные в JSON."""
        try:
            path = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON", "*.json")])
            if path:
                self.db.export_all_json(path)
                messagebox.showinfo("Экспорт", "Данные экспортированы.")
        except Exception as exc:
            messagebox.showerror("Ошибка экспорта", str(exc))

    def run(self):
        """Запускает программу."""
        try:
            self.root.mainloop()
        finally:
            self.db.close()
