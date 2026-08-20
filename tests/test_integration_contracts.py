"""Tests for offline integration contract diagnostics."""

import unittest

from core.integration_contracts import (
    check_integration_contract,
    check_integration_contracts,
    contract_summary,
)


class TestIntegrationContracts(unittest.TestCase):
    def test_known_integration_has_callable_contract(self):
        result = check_integration_contract("github")

        self.assertTrue(result.ok)
        self.assertIn("callable run", result.detail)

    def test_missing_integration_is_reported_without_raising(self):
        result = check_integration_contract("does_not_exist")

        self.assertFalse(result.ok)
        self.assertIn("import failed", result.detail)

    def test_summary_counts_selected_contracts(self):
        results = check_integration_contracts(["github", "does_not_exist"])

        self.assertEqual(contract_summary(results), {"total": 2, "passed": 1, "failed": 1})


if __name__ == "__main__":
    unittest.main()
