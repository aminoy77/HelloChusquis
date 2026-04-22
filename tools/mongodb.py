from tools.base import BaseTool, ToolResult
import os


PLUGIN_NAME = "mongodb"
PLUGIN_DESCRIPTION = "Interact with MongoDB databases"

MONGODB_SCHEMA = {
    "type": "function",
    "function": {
        "name": "mongodb",
        "description": "Query and manipulate MongoDB collections",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["find", "insert", "update", "delete", "list_databases", "list_collections", "aggregate"],
                    "description": "The MongoDB action to perform"
                },
                "database": {"type": "string", "description": "Database name"},
                "collection": {"type": "string", "description": "Collection name"},
                "filter": {"type": "string", "description": "Query filter (JSON)"},
                "document": {"type": "string", "description": "Document to insert/update (JSON)"},
                "update": {"type": "string", "description": "Update operation (JSON)"},
                "limit": {"type": "number", "description": "Limit results (default 10)"},
            },
            "required": ["action"]
        }
    }
}


def get_mongo_credentials() -> dict:
    """Get MongoDB credentials from environment."""
    return {
        "host": os.getenv("MONGODB_HOST", "localhost"),
        "port": os.getenv("MONGODB_PORT", "27017"),
        "database": os.getenv("MONGODB_DB"),
        "user": os.getenv("MONGODB_USER"),
        "password": os.getenv("MONGODB_PASSWORD"),
    }


def run(action: str, database: str = "", collection: str = "", filter: str = "", 
       document: str = "", update: str = "", limit: int = 10) -> str:
    """Execute MongoDB operations."""
    creds = get_mongo_credentials()
    
    if not creds["database"] or not creds["user"]:
        return "Error: MongoDB credentials not found. Set MONGODB_DB, MONGODB_USER, MONGODB_PASSWORD."
    
    try:
        from pymongo import MongoClient
    except ImportError:
        return "Error: pymongo not installed. Run: pip install pymongo"
    
    try:
        # Build connection URI
        uri = f"mongodb://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
        client = MongoClient(uri)
        
        db = client[database or creds["database"]]
        
        if action == "list_databases":
            dbs = client.list_database_names()
            result = [f"• {d}" for d in dbs]
            client.close()
            return "\n".join(result) if result else "No databases found."
        
        elif action == "list_collections":
            colls = db.list_collection_names()
            result = [f"• {c}" for c in colls]
            client.close()
            return "\n".join(result) if result else "No collections found."
        
        elif action == "find":
            if not collection:
                return "Error: collection name required for find"
            
            coll = db[collection]
            
            # Parse filter
            query = {}
            if filter:
                import json
                query = json.loads(filter)
            
            cursor = coll.find(query).limit(limit)
            result = []
            for doc in cursor:
                # Remove MongoDB internal fields
                doc.pop("_id", None)
                result.append(str(doc)[:200])
            
            client.close()
            return "\n".join(result) if result else "No documents found."
        
        elif action == "insert":
            if not collection or not document:
                return "Error: collection and document required for insert"
            
            coll = db[collection]
            
            import json
            doc = json.loads(document)
            if isinstance(doc, list):
                result = coll.insert_many(doc)
                client.close()
                return f"Inserted {len(result.inserted_ids)} documents! :white_check_mark:"
            else:
                result = coll.insert_one(doc)
                client.close()
                return f"Inserted document! :white_check_mark:\nID: {result.inserted_id}"
        
        elif action == "update":
            if not collection or not filter or not update:
                return "Error: collection, filter, and update required for update"
            
            coll = db[collection]
            
            import json
            query = json.loads(filter)
            new_values = {"$set": json.loads(update)}
            
            result = coll.update_many(query, new_values)
            client.close()
            return f"Updated {result.modified_count} documents! :white_check_mark:"
        
        elif action == "delete":
            if not collection or not filter:
                return "Error: collection and filter required for delete"
            
            coll = db[collection]
            
            import json
            query = json.loads(filter)
            
            result = coll.delete_many(query)
            client.close()
            return f"Deleted {result.deleted_count} documents! :white_check_mark:"
        
        elif action == "aggregate":
            if not collection or not filter:
                return "Error: collection and filter (pipeline) required for aggregate"
            
            coll = db[collection]
            
            import json
            pipeline = json.loads(filter)
            
            cursor = coll.aggregate(pipeline).limit(limit)
            result = []
            for doc in cursor:
                doc.pop("_id", None)
                result.append(str(doc)[:200])
            
            client.close()
            return "\n".join(result) if result else "No results."
        
        else:
            client.close()
            return f"Error: Unknown action '{action}'. Available: find, insert, update, delete, list_databases, list_collections, aggregate"
    
    except ImportError:
        return "Error: pymongo not installed. Run: pip install pymongo"
    except ImportError:
        return "Error: pymongo not installed. Run: pip install pymongo"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("MongoDB plugin loaded. Use 'mongodb' tool in HelloChusquis.")