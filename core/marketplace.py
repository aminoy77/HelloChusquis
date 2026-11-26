"""Local marketplace storage backed by SQLite."""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable


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


ITEM_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
DEFAULT_HOME = Path.home() / ".hellochusquis"
SKILLS_DIR = DEFAULT_HOME / "skills"
PLUGINS_DIR = DEFAULT_HOME / "plugins"
MCP_CONFIG = DEFAULT_HOME / "mcp.json"
CATALOG_FILE = Path(__file__).with_name("marketplace_catalog.json")


class MarketplaceError(ValueError):
    pass


def _safe_id(value: Any) -> str:
    item_id = str(value or "").strip()
    if not ITEM_ID_RE.fullmatch(item_id):
        raise MarketplaceError("Invalid marketplace item id")
    return item_id


def load_catalog() -> list[dict[str, Any]]:
    try:
        data = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MarketplaceError(f"Unable to read marketplace catalog: {exc}") from exc
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise MarketplaceError("Marketplace catalog has invalid format")
    catalog = [item for item in items if isinstance(item, dict)]
    known_ids = {str(item.get("id")) for item in catalog}

    tools_dir = CATALOG_FILE.resolve().parents[1] / "tools"
    for source in sorted(tox_path for tox_path in tools_dir.glob("*.py") if tox_path.name not in {"__init__.py"}):
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        plugin_name = ""
        description = ""
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            value = node.value
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id == "PLUGIN_NAME":
                    plugin_name = value.value
                elif target.id == "PLUGIN_DESCRIPTION":
                    description = value.value
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", plugin_name) or plugin_name in known_ids:
            continue
        catalog.append({
            "id": plugin_name,
            "kind": "plugin",
            "name": plugin_name.replace("_", " ").replace("-", " ").title(),
            "description": description or f"Local {plugin_name} integration plugin.",
            "source": source.stem,
        })
        known_ids.add(plugin_name)

    skills_dir = CATALOG_FILE.resolve().parents[1] / "examples" / "skills"
    if skills_dir.is_dir():
        for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
            skill_id = skill_file.parent.name
            if skill_id in known_ids:
                continue
            body = skill_file.read_text(encoding="utf-8")
            match = re.search(r"^description:\s*(.+)$", body, re.MULTILINE)
            catalog.append({
                "id": skill_id,
                "kind": "skill",
                "name": skill_id.replace("-", " ").replace("_", " ").title(),
                "description": match.group(1).strip() if match else "Local HelloChusquis skill.",
                "skill_md": body,
            })
            known_ids.add(skill_id)

    return catalog


def get_item(item_id: str) -> dict[str, Any]:
    safe_id = _safe_id(item_id)
    for item in load_catalog():
        if item.get("id") == safe_id:
            return item
    raise MarketplaceError(f"Unknown marketplace item: {safe_id}")


def list_items(kind: str = "") -> list[dict[str, Any]]:
    kind = kind.strip().lower()
    return [
        item
        for item in load_catalog()
        if not kind or item.get("kind") == kind
    ]


def is_installed(item: dict[str, Any]) -> bool:
    item_id = _safe_id(item["id"])
    kind = item.get("kind")
    if kind == "skill":
        return (SKILLS_DIR / item_id / "SKILL.md").is_file()
    if kind == "plugin":
        return (PLUGINS_DIR / f"{item_id}.py").is_file()
    if kind == "mcp":
        try:
            data = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return item_id in data.get("mcpServers", {}) if isinstance(data, dict) else False
    return False


def _atomic_write(path: Path, content: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def install_item(item_id: str) -> dict[str, Any]:
    item = get_item(item_id)
    kind = item.get("kind")
    item_id = _safe_id(item["id"])

    if kind == "skill":
        body = item.get("skill_md")
        if not isinstance(body, str) or not body.strip():
            raise MarketplaceError("Skill package is missing SKILL.md content")
        destination = SKILLS_DIR / item_id / "SKILL.md"
        _atomic_write(destination, body)
    elif kind == "plugin":
        source_name = item.get("source")
        if not isinstance(source_name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", source_name):
            raise MarketplaceError("Plugin package has an invalid source")
        source = Path(__file__).resolve().parents[1] / "tools" / f"{source_name}.py"
        if not source.is_file():
            raise MarketplaceError(f"Bundled plugin source is missing: {source_name}")
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(PLUGINS_DIR, 0o700)
        destination = PLUGINS_DIR / f"{item_id}.py"
        shutil.copyfile(source, destination)
        os.chmod(destination, 0o600)
    elif kind == "mcp":
        config = item.get("config")
        if not isinstance(config, dict):
            raise MarketplaceError("MCP package has invalid configuration")
        try:
            existing = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
        except FileNotFoundError:
            existing = {}
        except json.JSONDecodeError as exc:
            raise MarketplaceError(f"MCP configuration is invalid: {exc}") from exc
        if not isinstance(existing, dict):
            raise MarketplaceError("MCP configuration root must be a JSON object")
        servers = existing.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            raise MarketplaceError("MCP mcpServers entry must be a JSON object")
        servers[item_id] = config
        _atomic_write(MCP_CONFIG, json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
    else:
        raise MarketplaceError(f"Unsupported marketplace item kind: {kind}")
    return {"status": "installed", "item": item_id, "kind": kind}


def uninstall_item(item_id: str) -> dict[str, Any]:
    item = get_item(item_id)
    kind = item.get("kind")
    item_id = _safe_id(item["id"])

    if kind == "skill":
        destination = SKILLS_DIR / item_id
        if destination.is_dir():
            shutil.rmtree(destination)
    elif kind == "plugin":
        destination = PLUGINS_DIR / f"{item_id}.py"
        destination.unlink(missing_ok=True)
    elif kind == "mcp":
        try:
            existing = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            existing = {}
        if isinstance(existing, dict):
            servers = existing.get("mcpServers")
            if isinstance(servers, dict):
                servers.pop(item_id, None)
                _atomic_write(MCP_CONFIG, json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
    else:
        raise MarketplaceError(f"Unsupported marketplace item kind: {kind}")
    return {"status": "uninstalled", "item": item_id, "kind": kind}
