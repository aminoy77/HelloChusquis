"""Every bundled module must import on an installation without optional extras."""

import importlib
import pkgutil
import unittest

from tools.optional_deps import EXTRA_FOR_MODULE, MissingDependencyError, require

PACKAGES = ("core", "tools", "ui")


class TestBareInstallImports(unittest.TestCase):
    def test_bundled_modules_import_without_optional_extras(self):
        failures = {}
        for package in PACKAGES:
            for module in pkgutil.iter_modules([package]):
                name = f"{package}.{module.name}"
                with self.subTest(module=name):
                    try:
                        importlib.import_module(name)
                    except Exception as exc:  # noqa: BLE001 - reported per module below
                        failures[name] = f"{type(exc).__name__}: {exc}"
        self.assertEqual(failures, {})

    def test_optional_dependency_error_names_the_install_extra(self):
        with self.assertRaises(MissingDependencyError) as ctx:
            require("hellochusquis_missing_dependency_probe")
        self.assertIn("pip install", str(ctx.exception))
        self.assertIn("boto3", EXTRA_FOR_MODULE)


if __name__ == "__main__":
    unittest.main()
