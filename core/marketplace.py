"""Local marketplace storage backed by SQLite."""

from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path
from typing import Iterable


MARKETPLACE_DB_PATH = Path.home() / ".hellochusquis" / "marketplace.db"

_lock = threading.RLock()


def _connect(db_path: Path | str = MARKETPLACE_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    managed_directory = Path.home() / ".hellochusquis"
    if path.parent == managed_directory:
        os.chmod(managed_directory, 0o700)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    if str(path) != ":memory:":
        os.chmod(path, 0o600)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_marketplace(db_path: Path | str = MARKETPLACE_DB_PATH) -> None:
    with _lock, _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                neighborhood TEXT NOT NULL,
                rating REAL NOT NULL DEFAULT 5.0
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
                stock INTEGER NOT NULL CHECK(stock >= 0),
                color TEXT NOT NULL DEFAULT '#f5a623',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(seller_id) REFERENCES sellers(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                principal_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed',
                total_cents INTEGER NOT NULL CHECK(total_cents >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0),
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );
            """
        )
        if conn.execute("SELECT COUNT(*) FROM sellers").fetchone()[0] == 0:
            sellers = [
                ("Taller Esquina", "Centro", 4.9),
                ("Huerta del Sur", "Sur", 4.8),
                ("Estudio Norte", "Norte", 4.7),
                ("Migas Barrio", "Este", 4.9),
            ]
            conn.executemany(
                "INSERT INTO sellers(name, neighborhood, rating) VALUES (?, ?, ?)",
                sellers,
            )
            seed = [
                (1, "Lámpara de barro", "Pieza hecha a mano con acabado mate.", "Hogar", 4800, 8, "#d98945"),
                (1, "Bolsa de lona", "Bolsa resistente para compras de barrio.", "Accesorios", 2200, 15, "#c6a66b"),
                (2, "Caja de tomates", "Tomates de temporada cosechados esta semana.", "Alimentos", 950, 24, "#d95d4f"),
                (2, "Mermelada cítrica", "Receta pequeña con cáscara y azúcar morena.", "Alimentos", 680, 12, "#edb84a"),
                (3, "Cuaderno retrato", "Cuaderno cosido con papel de 120 g.", "Arte", 1900, 10, "#6e91a8"),
                (3, "Póster oficio", "Edición local impresa en papel reciclado.", "Arte", 3500, 6, "#9a7bb3"),
                (4, "Pan de masa madre", "Horneado cada mañana en la panadería local.", "Alimentos", 850, 18, "#c89a64"),
            ]
            conn.executemany(
                """
                INSERT INTO products(seller_id, title, description, category, price_cents, stock, color)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                seed,
            )


def list_products(
    db_path: Path | str = MARKETPLACE_DB_PATH,
    search: str = "",
    category: str = "",
) -> list[dict]:
    init_marketplace(db_path)
    clauses: list[str] = []
    params: list[str] = []
    if search.strip():
        clauses.append("(p.title LIKE ? OR p.description LIKE ? OR s.name LIKE ?)")
        term = f"%{search.strip()}%"
        params.extend([term, term, term])
    if category.strip() and category.lower() != "todos":
        clauses.append("p.category = ?")
        params.append(category.strip())
    where = " AND ".join(clauses)
    sql = """
        SELECT p.id, p.title, p.description, p.category, p.price_cents, p.stock,
               p.color, s.name AS seller, s.neighborhood, s.rating
        FROM products p
        JOIN sellers s ON s.id = p.seller_id
    """
    if where:
        sql += " WHERE " + where
    sql += " ORDER BY p.created_at DESC, p.id DESC"
    with _lock, _connect(db_path) as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def categories(db_path: Path | str = MARKETPLACE_DB_PATH) -> list[str]:
    init_marketplace(db_path)
    with _lock, _connect(db_path) as conn:
        return [row[0] for row in conn.execute(
            "SELECT DISTINCT category FROM products ORDER BY category"
        ).fetchall()]


def create_product(
    db_path: Path | str,
    seller_name: str,
    neighborhood: str,
    title: str,
    description: str,
    category: str,
    price_cents: int,
    stock: int,
) -> dict:
    init_marketplace(db_path)
    with _lock, _connect(db_path) as conn:
        seller = conn.execute(
            "SELECT id FROM sellers WHERE name = ?", (seller_name,)
        ).fetchone()
        if seller:
            seller_id = seller["id"]
        else:
            cur = conn.execute(
                "INSERT INTO sellers(name, neighborhood) VALUES (?, ?)",
                (seller_name, neighborhood),
            )
            seller_id = cur.lastrowid
        cur = conn.execute(
            """
            INSERT INTO products(seller_id, title, description, category, price_cents, stock)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (seller_id, title, description, category, price_cents, stock),
        )
        product_id = cur.lastrowid
        row = conn.execute(
            """
            SELECT p.id, p.title, p.description, p.category, p.price_cents, p.stock,
                   p.color, s.name AS seller, s.neighborhood, s.rating
            FROM products p JOIN sellers s ON s.id = p.seller_id
            WHERE p.id = ?
            """,
            (product_id,),
        ).fetchone()
        return dict(row)


def create_order(
    db_path: Path | str,
    principal_id: str,
    customer_name: str,
    items: Iterable[dict],
) -> dict:
    init_marketplace(db_path)
    normalized = [(int(item["product_id"]), int(item["quantity"])) for item in items]
    if not normalized:
        raise ValueError("El carrito está vacío")
    if any(quantity < 1 or quantity > 99 for _, quantity in normalized):
        raise ValueError("La cantidad debe estar entre 1 y 99")

    with _lock, _connect(db_path) as conn:
        total = 0
        order_items = []
        for product_id, quantity in normalized:
            product = conn.execute(
                "SELECT id, title, price_cents, stock FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()
            if not product:
                raise ValueError(f"Producto {product_id} no existe")
            if quantity > product["stock"]:
                raise ValueError(f"Stock insuficiente para {product['title']}")
            total += product["price_cents"] * quantity
            order_items.append((product_id, quantity, product["price_cents"], product["title"]))

        cur = conn.execute(
            """
            INSERT INTO orders(principal_id, customer_name, total_cents)
            VALUES (?, ?, ?)
            """,
            (principal_id, customer_name, total),
        )
        order_id = cur.lastrowid
        for product_id, quantity, price_cents, _title in order_items:
            conn.execute(
                """
                INSERT INTO order_items(order_id, product_id, quantity, unit_price_cents)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, product_id, quantity, price_cents),
            )
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (quantity, product_id),
            )
        return {
            "id": order_id,
            "customer_name": customer_name,
            "status": "confirmed",
            "total_cents": total,
            "items": [
                {"product_id": pid, "title": title, "quantity": quantity, "unit_price_cents": price}
                for pid, quantity, price, title in order_items
            ],
        }
