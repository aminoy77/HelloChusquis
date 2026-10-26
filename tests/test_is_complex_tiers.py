"""is_complex: casual mentions of plan keywords must NOT trigger plan mode."""
import pytest
from main import is_complex


class TestCasualNotComplex:
    """Common phrases containing plan keywords — should stay simple."""

    @pytest.mark.parametrize("text", [
        "analiza el error",           # 3 words, casual
        "compara estos dos archivos", # casual
        "cada cuánto se ejecuta el cron",  # 'cada' casual
        "busca y reemplaza foo por bar en config.py",  # mechanical edit
        "explícame qué hace la tool shell",
    ])
    def test_casual_stays_simple(self, text):
        assert not is_complex(text), f"'{text}' wrongly triggers plan"


class TestExplicitDeliverables:
    """Explicit multi-step deliverables — always plan."""

    @pytest.mark.parametrize("text", [
        "crea un pdf con el resumen",
        "crea un word",
        "haz un informe sobre ventas",
        "crea un documento oficial",
    ])
    def test_deliverable_is_complex(self, text):
        assert is_complex(text), f"'{text}' should trigger plan"


class TestLongTasks:
    """Long detailed requests — plan."""

    @pytest.mark.parametrize("text", [
        "investiga las mejores librerías de python para procesar pdfs y compara rendimiento y escribe un resumen detallado",
        "analiza el código del proyecto, busca bugs de seguridad, lista los problemas encontrados y propón soluciones para cada uno",
    ])
    def test_long_is_complex(self, text):
        assert is_complex(text), f"'{text}' should trigger plan"


class TestSimple:
    @pytest.mark.parametrize("text", [
        "hola", "hello", "gracias", "ok",
        "crea el archivo test.txt",   # short mechanical
        "borra /tmp/foo",
    ])
    def test_simple(self, text):
        assert not is_complex(text)
