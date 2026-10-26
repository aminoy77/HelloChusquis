"""Generated tool code: coherent action names, path params, output field."""
import json
from unittest.mock import Mock, patch

from core.tool_builder import _generate_openapi_tool as _generate_tool_code_from_ops


OPS = [
    {"method": "GET", "path": "/pet/findByStatus", "operation_id": "findPetsByStatus",
     "summary": "Finds Pets by status", "parameters": [{"name": "status", "in": "query"}]},
    {"method": "GET", "path": "/pet/{petId}", "operation_id": "getPetById",
     "summary": "Find pet by ID", "parameters": [{"name": "petId", "in": "path"}]},
    {"method": "POST", "path": "/pet", "operation_id": "addPet",
     "summary": "Add a pet", "parameters": []},
]


def _build_tool():
    code = _generate_tool_code_from_ops(
        service_name="petstore", file_name="petstore",
        base_url="https://api.test.com/v2",
        description="Petstore test", auth_type="api_key",
        auth_config={}, operations=OPS)
    ns = {}
    exec(compile(code, "generated_petstore.py", "exec"), ns)
    tool = ns["PetstoreTool"]()
    tool.config = {"api_key": "k", "base_url": "https://api.test.com/v2"}
    return tool, ns


def _mock_response(status=200, payload=None):
    m = Mock()
    m.status_code = status
    m.json.return_value = payload or {"ok": True}
    m.text = ""
    m.raise_for_status = Mock()
    return m


def test_action_names_are_operation_ids():
    tool, _ = _build_tool()
    with patch("httpx.get", return_value=_mock_response()) as g:
        r = tool.run("findPetsByStatus", status="available")
    assert r.success, r.error
    assert g.call_args.args[0] == "https://api.test.com/v2/pet/findByStatus"


def test_path_params_substituted():
    tool, _ = _build_tool()
    with patch("httpx.get", return_value=_mock_response()) as g:
        r = tool.run("getPetById", petId="42")
    assert r.success, r.error
    assert g.call_args.args[0] == "https://api.test.com/v2/pet/42"


def test_output_filled_with_json():
    tool, _ = _build_tool()
    with patch("httpx.post", return_value=_mock_response(payload={"id": 7})):
        r = tool.run("addPet", data={"name": "Rex"})
    assert r.success, r.error
    assert json.loads(r.output) == {"id": 7}


def test_unknown_action_lists_available():
    tool, _ = _build_tool()
    r = tool.run("nope")
    assert not r.success
    assert "findPetsByStatus" in r.error
