# Python unittest module

- In Python, `unittest.TestCase` methods named `test_*` run as isolated test cases.
- In Python, `setUp`/`tearDown` prepare and clean fixtures around every single test.
- In Python, `assertEqual`, `assertIn`, `assertRaises`, and `assertTrue` cover most assertions.
- In Python, `assertRaisesRegex` checks both the exception type and its message pattern.
- In Python, `subTest` continues a looped test past individual case failures.
- In Python, `unittest.mock.patch` swaps dependencies; `Mock(return_value=...)` fakes callables.
- In Python, `mock.patch.object` targets one attribute without touching module imports.
- In Python, `python -m unittest discover tests -q` runs whole suites quietly.
- In Python, `setUpClass`/`tearDownClass` share expensive fixtures across a test class once.
- In Python, `skipTest` and `@unittest.skip` mark known gaps explicitly instead of deleting tests.
