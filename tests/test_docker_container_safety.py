"""Regression tests for safe Docker container identifiers."""

import unittest

from tools import docker


class TestDockerContainerSafety(unittest.TestCase):
    def test_container_identifier_is_a_single_safe_path_segment(self):
        self.assertEqual(docker._container_id("7f3a9c12ab45"), "7f3a9c12ab45")
        for unsafe_id in ("../images", "container/start", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    docker._container_id(unsafe_id)


if __name__ == "__main__":
    unittest.main()
