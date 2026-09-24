"""Анализ и визуализация данных."""
from collections import defaultdict


def top_clients_by_orders(data, limit=5):
    """TOP клиентов по числу заказов."""
    names = {x["id"]: x["name"] for x in data.data["clients"]}
    counts = defaultdict(int)
    for order in data.data["orders"]:
        counts[names.get(order["client_id"], "Неизвестный")] += 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:limit]


def orders_dynamics(data):
    """Количество заказов по датам."""
    counts = defaultdict(int)
    for order in data.data["orders"]:
        counts[order["date"]] += 1
    return sorted(counts.items())


def client_edges(data):
    """Связи клиентов по общим товарам."""
    names = {x["id"]: x["name"] for x in data.data["clients"]}
    products = defaultdict(set)
    for order in data.data["orders"]:
        for item in order.get("items", []):
            products[order["client_id"]].add(item["product_id"])

    ids = sorted(products)
    edges = []
    for i, first in enumerate(ids):
        for second in ids[i + 1:]:
            common = products[first] & products[second]
            if common:
                edges.append((names.get(first, "Неизвестный"),
                              names.get(second, "Неизвестный"),
                              len(common)))
    return edges


def show_top_clients(data):
    """Показывает TOP-5 клиентов."""
    import matplotlib.pyplot as plt
    values = top_clients_by_orders(data)
    plt.figure(figsize=(8, 5))
    plt.bar([x[0] for x in values], [x[1] for x in values])
    plt.title("TOP-5 клиентов по количеству заказов")
    plt.xlabel("Клиент")
    plt.ylabel("Количество заказов")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.show()


def show_orders_dynamics(data):
    """Показывает динамику заказов."""
    import matplotlib.pyplot as plt
    values = orders_dynamics(data)
    plt.figure(figsize=(9, 5))
    plt.plot([x[0] for x in values], [x[1] for x in values], marker="o")
    plt.title("Динамика количества заказов")
    plt.xlabel("Дата")
    plt.ylabel("Количество заказов")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.show()


def show_client_graph(data):
    """Показывает граф связей клиентов."""
    import matplotlib.pyplot as plt
    import networkx as nx
    graph = nx.Graph()
    for first, second, weight in client_edges(data):
        graph.add_edge(first, second, weight=weight)
    if not graph.nodes:
        return
    positions = nx.spring_layout(graph, seed=42)
    widths = [graph[a][b]["weight"] for a, b in graph.edges]
    plt.figure(figsize=(9, 6))
    nx.draw_networkx(graph, positions, with_labels=True, node_size=1800,
                     font_size=8, width=widths)
    plt.title("Связи клиентов по общим товарам")
    plt.axis("off")
    plt.tight_layout()
    plt.show()
