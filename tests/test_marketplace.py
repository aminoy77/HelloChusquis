"""Tests for the local marketplace storage and web routes."""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

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


if __name__ == "__main__":
    unittest.main()
