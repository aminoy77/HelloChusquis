"""Tests for the local marketplace storage and web routes."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import core.marketplace as marketplace
from core.marketplace import (
    create_order,
    create_product,
    init_marketplace,
    list_products,
)
from web import server


class TestMarketplace(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = Path(self.tempdir.name) / "marketplace.db"
        init_marketplace(self.db)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_seed_catalog_is_searchable(self):
        products = list_products(self.db, search="tomates")
        self.assertEqual(len(products), 1)
        self.assertIn("tomates", products[0]["title"].lower())

    def test_create_product_is_persisted(self):
        product = create_product(
            self.db,
            seller_name="Vecino Uno",
            neighborhood="Norte",
            title="Jarrón",
            description="Pieza de cerámica",
            category="Hogar",
            price_cents=2500,
            stock=3,
        )
        self.assertEqual(product["seller"], "Vecino Uno")
        self.assertEqual(product["stock"], 3)

    def test_order_checks_stock_and_reduces_inventory(self):
        product = list_products(self.db)[0]
        order = create_order(
            self.db,
            principal_id="test-principal",
            customer_name="Ana",
            items=[{"product_id": product["id"], "quantity": 1}],
        )
        self.assertEqual(order["status"], "confirmed")
        updated = next(p for p in list_products(self.db) if p["id"] == product["id"])
        self.assertEqual(updated["stock"], product["stock"] - 1)

    def test_web_routes_are_available(self):
        headers = {
            "Authorization": f"Bearer {server.REQUIRED_API_KEY}",
            "X-HelloChusquis-Session": "marketplace-test",
        }
        client = TestClient(server.app)
        response = client.get("/marketplace/categories", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Todos", response.json()["categories"])


class MarketplaceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / ".hellochusquis"
        patches = [
            patch.object(marketplace, "DEFAULT_HOME", self.home),
            patch.object(marketplace, "SKILLS_DIR", self.home / "skills"),
            patch.object(marketplace, "PLUGINS_DIR", self.home / "plugins"),
            patch.object(marketplace, "MCP_CONFIG", self.home / "mcp.json"),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def test_catalog_has_supported_items(self):
        items = marketplace.load_catalog()
        self.assertEqual({"skill", "plugin", "mcp"}, {item["kind"] for item in items})

    def test_install_and_uninstall_skill(self):
        marketplace.install_item("caveman")
        item = marketplace.get_item("caveman")
        self.assertTrue(marketplace.is_installed(item))
        marketplace.uninstall_item("caveman")
        self.assertFalse(marketplace.is_installed(item))

    def test_install_and_uninstall_plugin(self):
        marketplace.install_item("slack")
        item = marketplace.get_item("slack")
        self.assertTrue(marketplace.is_installed(item))
        marketplace.uninstall_item("slack")
        self.assertFalse(marketplace.is_installed(item))

    def test_reject_unknown_item(self):
        with self.assertRaises(marketplace.MarketplaceError):
            marketplace.install_item("../bad")


if __name__ == "__main__":
    unittest.main()
