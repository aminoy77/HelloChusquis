"""Regression tests for safe generic GraphQL endpoints."""

import unittest

from tools import graphql
from tools.web_fetch import SsrFBlockedError


class TestGraphQLEndpointSafety(unittest.TestCase):
    def test_graphql_endpoint_reuses_shared_ssrf_validation(self):
        self.assertEqual(graphql._safe_endpoint("https://8.8.8.8/graphql"), "https://8.8.8.8/graphql")
        with self.assertRaises(SsrFBlockedError):
            graphql._safe_endpoint("http://127.0.0.1:8080/graphql")


if __name__ == "__main__":
    unittest.main()
