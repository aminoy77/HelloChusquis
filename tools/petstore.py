"""
This is a sample Pet Store Server based on the OpenAPI 3.0 specification.  You can find out more about
Swagger at [https://swagger.io](https://swagger.io). In the third iteration of the pet store, we've switched to the design first approach!
You can now help us improve the API whether it's by making changes to the definition itself or to the code.
That way, with time, we can improve the API in general, and expose some of the new features in OAS3.

Some useful links:
- [The Pet Store repository](https://github.com/swagger-api/swagger-petstore)
- [The source API definition for the Pet Store](https://github.com/swagger-api/swagger-petstore/blob/master/src/main/resources/openapi.yaml)
Generated from OpenAPI spec. 19 operations.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from tools.base import Tool, ToolResult


class PetstoreTool(Tool):
    name = 'petstore'
    description = "This is a sample Pet Store Server based on the OpenAPI 3.0 specification.  You can find out more about\nSwagger at [https://swagger.io](https://swagger.io). In the third iteration of the pet store, we've switched to the design first approach!\nYou can now help us improve the API whether it's by making changes to the definition itself or to the code.\nThat way, with time, we can improve the API in general, and expose some of the new features in OAS3.\n\nSome useful links:\n- [The Pet Store repository](https://github.com/swagger-api/swagger-petstore)\n- [The source API definition for the Pet Store](https://github.com/swagger-api/swagger-petstore/blob/master/src/main/resources/openapi.yaml)"

    def run(self, action: str, **kwargs) -> ToolResult:
        """Execute an action against the petstore API."""
        headers = {"Content-Type": "application/json"}

        base_url = self.config.get("base_url", "/api/v3")

        # CRUD aliases → real operation ids
        action = {
        "create": "addPet",
        "update": "updatePet",
        "list": "findPetsByStatus",
        "get": "getPetById",
        "delete": "deletePet",
        }.get(action, action)

        try:
            if action == "findPetsByStatus":
                # Finds Pets by status.
                url = f"{base_url}/pet/findByStatus"
                params = {}
                for p in ['status']:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.get(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "findPetsByTags":
                # Finds Pets by tags.
                url = f"{base_url}/pet/findByTags"
                params = {}
                for p in ['tags']:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.get(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "getInventory":
                # Returns pet inventories by status.
                url = f"{base_url}/store/inventory"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.get(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "loginUser":
                # Logs user into the system.
                url = f"{base_url}/user/login"
                params = {}
                for p in ['username', 'password']:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.get(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "logoutUser":
                # Logs out current logged in user session.
                url = f"{base_url}/user/logout"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.get(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            if action == "getPetById":
                # Find pet by ID.
                url = f"{base_url}/pet/{{petId}}"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in ['petId']:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.get(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "getOrderById":
                # Find purchase order by ID.
                url = f"{base_url}/store/order/{{orderId}}"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in ['orderId']:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.get(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "getUserByName":
                # Get user by user name.
                url = f"{base_url}/user/{{username}}"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in ['username']:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.get(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            if action == "addPet":
                # Add a new pet to the store.
                url = f"{base_url}/pet"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.post(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "updatePetWithForm":
                # Updates a pet in the store with form data.
                url = f"{base_url}/pet/{{petId}}"
                params = {}
                for p in ['name', 'status']:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in ['petId']:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.post(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "uploadFile":
                # Uploads an image.
                url = f"{base_url}/pet/{{petId}}/uploadImage"
                params = {}
                for p in ['additionalMetadata']:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in ['petId']:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.post(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "placeOrder":
                # Place an order for a pet.
                url = f"{base_url}/store/order"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.post(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "createUser":
                # Create user.
                url = f"{base_url}/user"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.post(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "createUsersWithListInput":
                # Creates list of users with given input array.
                url = f"{base_url}/user/createWithList"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.post(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            if action == "updatePet":
                # Update an existing pet.
                url = f"{base_url}/pet"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in []:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.put(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "updateUser":
                # Update user resource.
                url = f"{base_url}/user/{{username}}"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in ['username']:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.put(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            if action == "deletePet":
                # Deletes a pet.
                url = f"{base_url}/pet/{{petId}}"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in ['petId']:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.delete(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "deleteOrder":
                # Delete purchase order by identifier.
                url = f"{base_url}/store/order/{{orderId}}"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in ['orderId']:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.delete(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())
            elif action == "deleteUser":
                # Delete user resource.
                url = f"{base_url}/user/{{username}}"
                params = {}
                for p in []:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in ['username']:
                    if kwargs.get(p):
                        url = url.replace('{' + p + '}', str(kwargs.get(p)))
                r = httpx.delete(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}. Available actions: addPet, updatePet, findPetsByStatus, findPetsByTags, getPetById, updatePetWithForm, deletePet, uploadFile, getInventory, placeOrder, getOrderById, deleteOrder, createUser, createUsersWithListInput, loginUser, logoutUser, getUserByName, updateUser, deleteUser")

        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, error=f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except httpx.TimeoutException:
            return ToolResult(success=False, error="Request timed out")
        except Exception as e:
            return ToolResult(success=False, error=f"Request failed: {str(e)}")

    def list(self, **kwargs) -> ToolResult:
        """List all resources."""
        return self.run("list", **kwargs)
    
    def get(self, id: str, **kwargs) -> ToolResult:
        """Get a specific resource by ID."""
        return self.run("get", id=id, **kwargs)
    
    def create(self, data: Dict, **kwargs) -> ToolResult:
        """Create a new resource."""
        return self.run("create", data=data, **kwargs)
    
    def update(self, id: str, data: Dict, **kwargs) -> ToolResult:
        """Update an existing resource."""
        return self.run("update", id=id, data=data, **kwargs)
    
    def delete(self, id: str, **kwargs) -> ToolResult:
        """Delete a resource."""
        return self.run("delete", id=id, **kwargs)


def run(action: str = "list", **kwargs):
    """Entry point for the tool."""
    tool = PetstoreTool()
    return tool.run(action, **kwargs)
