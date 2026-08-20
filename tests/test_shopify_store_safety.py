"""Regression tests for safe Shopify store URL construction."""

import unittest

from tools import shopify


class TestShopifyStoreSafety(unittest.TestCase):
    def test_store_domain_is_canonical_and_cannot_override_the_api_origin(self):
        self.assertEqual(
            shopify._shopify_base_url("sample-store.myshopify.com"),
            "https://sample-store.myshopify.com/admin/api/2024-01",
        )
        for unsafe_store in (
            "https://sample-store.myshopify.com",
            "sample-store.myshopify.com/admin",
            "sample-store.myshopify.com@127.0.0.1",
            "127.0.0.1",
        ):
            with self.subTest(unsafe_store=unsafe_store):
                with self.assertRaises(ValueError):
                    shopify._shopify_base_url(unsafe_store)

    def test_query_and_inventory_inputs_are_bounded_and_typed(self):
        self.assertEqual(shopify._bounded_limit(999), 250)
        self.assertEqual(shopify._bounded_limit("invalid"), 10)
        self.assertEqual(shopify._shopify_status("OPEN"), "open")
        self.assertEqual(shopify._inventory_quantity("-4"), -4)
        for invalid_status in ("any&financial_status=paid", "unknown"):
            with self.subTest(invalid_status=invalid_status):
                with self.assertRaises(ValueError):
                    shopify._shopify_status(invalid_status)
        for invalid_id in ("../1", 0, True):
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(ValueError):
                    shopify._positive_integer(invalid_id, "inventory_item_id")


if __name__ == "__main__":
    unittest.main()
