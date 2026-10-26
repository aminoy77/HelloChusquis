"""Auto-generated tests for petstore tool."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from tools.petstore import PetstoreTool, run


class TestPetstoreTool:
    """Test cases for petstore API tool."""
    
    @pytest.fixture
    def tool(self):
        """Create tool instance with mock config."""
        tool = PetstoreTool()
        tool.config = {
            "api_key": "test_key",
            "base_url": "https://api.test.com/v1"
        }
        return tool
    
    def test_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == "petstore"
        assert tool.description is not None
    
    def test_list_action(self, tool):
        """Test list action calls correct endpoint."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"items": []}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = tool.run("list")
            
            assert result.success is True
            mock_get.assert_called_once()
    
    def test_get_action(self, tool):
        """Test get action retrieves specific item."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "123", "name": "test"}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = tool.run("get", id="123")
            
            assert result.success is True
            assert result.data.get("id") == "123"
    
    def test_create_action(self, tool):
        """Test create action posts data."""
        with patch('httpx.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "456", "name": "new"}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            result = tool.run("create", data={"name": "new"})
            
            assert result.success is True
            mock_post.assert_called_once()
    
    
    def test_http_error_handling(self, tool):
        """Test tool handles HTTP errors correctly."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=mock_response
            )
            mock_get.return_value = mock_response
            
            result = tool.run("list")
            
            assert result.success is False
            assert "404" in result.error
    
    def test_timeout_handling(self, tool):
        """Test tool handles timeouts."""
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timed out")
            
            result = tool.run("list")
            
            assert result.success is False
            assert "timed out" in result.error
    
    def test_unknown_action(self, tool):
        """Test tool handles unknown actions."""
        result = tool.run("unknown_action")
        
        assert result.success is False
        assert "Unknown action" in result.error


class TestPetstoreToolRun:
    """Test the run() entry point function."""

    @pytest.fixture
    def tool(self):
        """Create tool instance with mock config."""
        tool = PetstoreTool()
        tool.config = {
            "api_key": "test_key",
            "base_url": "https://api.test.com/v1"
        }
        return tool

    def test_run_function_exists(self):
        """Test run function is callable."""
        assert callable(run)
    
    def test_run_with_list_action(self):
        """Test run function with list action."""
        with patch('tools.petstore.PetstoreTool.run') as mock_run:
            mock_run.return_value = Mock(success=True, data={})
            
            result = run("list")
            
            mock_run.assert_called_once_with("list")


# Additional operation-specific tests

    def test_addPet(self, tool):
        """Test Add a new pet to the store.."""
        with patch('httpx.post') as mock_call:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status = Mock()
            mock_call.return_value = mock_response
            
            result = tool.run("addPet")

            assert result.success is True

    def test_updatePet(self, tool):
        """Test Update an existing pet.."""
        with patch('httpx.put') as mock_call:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status = Mock()
            mock_call.return_value = mock_response
            
            result = tool.run("updatePet")

            assert result.success is True

    def test_findPetsByStatus(self, tool):
        """Test Finds Pets by status.."""
        with patch('httpx.get') as mock_call:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status = Mock()
            mock_call.return_value = mock_response
            
            result = tool.run("findPetsByStatus")

            assert result.success is True

    def test_findPetsByTags(self, tool):
        """Test Finds Pets by tags.."""
        with patch('httpx.get') as mock_call:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status = Mock()
            mock_call.return_value = mock_response
            
            result = tool.run("findPetsByTags")

            assert result.success is True

    def test_getPetById(self, tool):
        """Test Find pet by ID.."""
        with patch('httpx.get') as mock_call:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status = Mock()
            mock_call.return_value = mock_response
            
            result = tool.run("getPetById")

            assert result.success is True

# Make tests runnable with: pytest tests/test_<tool>.py -v
