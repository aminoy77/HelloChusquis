from tools.base import BaseTool, ToolResult
import os
import json


PLUGIN_NAME = "postgresql"
PLUGIN_DESCRIPTION = "Execute queries on PostgreSQL databases"

POSTGRESQL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "postgresql",
        "description": "Execute SQL queries on PostgreSQL",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["query", "execute", "list_tables", "describe_table", "list_databases"],
                    "description": "The PostgreSQL action to perform"
                },
                "sql": {"type": "string", "description": "SQL query to execute"},
                "database": {"type": "string", "description": "Database name"},
                "schema": {"type": "string", "description": "Schema name (default: public)"},
                "table": {"type": "string", "description": "Table name"},
                "limit": {"type": "number", "description": "Limit results (default 10)"},
            },
            "required": ["action"]
        }
    }
}


def get_postgres_credentials() -> dict:
    """Get PostgreSQL credentials from environment."""
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "database": os.getenv("POSTGRES_DB") or os.getenv("POSTGRES_DATABASE"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }


def run(action: str, sql: str = "", database: str = "", schema: str = "public", 
       table: str = "", limit: int = 10) -> str:
    """Execute PostgreSQL operations."""
    creds = get_postgres_credentials()
    
    if not creds["database"] or not creds["user"]:
        return "Error: PostgreSQL credentials not found. Set POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD."
    
    try:
        import psycopg2
    except ImportError:
        return "Error: psycopg2 not installed. Run: pip install psycopg2-binary"
    
    try:
        conn = psycopg2.connect(
            host=creds["host"],
            port=creds["port"],
            database=database or creds["database"],
            user=creds["user"],
            password=creds["password"]
        )
        cursor = conn.cursor()
        
        if action == "list_databases":
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            rows = cursor.fetchall()
            result = [f"• {r[0]}" for r in rows]
            conn.close()
            return "\n".join(result) if result else "No databases found."
        
        elif action == "list_tables":
            q = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY table_name
            """
            cursor.execute(q, (schema,))
            rows = cursor.fetchall()[:20]
            result = [f"• {schema}.{r[0]}" for r in rows]
            conn.close()
            return "\n".join(result) if result else "No tables found."
        
        elif action == "describe_table":
            if not table:
                return "Error: table name required for describe_table"
            
            # Get columns
            q = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """
            cursor.execute(q, (schema, table))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                nullable = "NULL" if r[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {r[3]}" if r[3] else ""
                result.append(f"• {r[0]}: {r[1]} {nullable}{default}")
            
            # Get primary key
            pk_q = """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = %s AND tc.table_name = %s
                    AND tc.constraint_type = 'PRIMARY KEY'
            """
            cursor.execute(pk_q, (schema, table))
            pks = cursor.fetchall()
            if pks:
                result.append(f"PK: {', '.join([p[0] for p in pks])}")
            
            conn.close()
            return "\n".join(result) if result else "Table not found."
        
        elif action == "query":
            if not sql:
                return "Error: sql query required for query action"
            
            cursor.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Format result
                result = []
                for row in rows[:limit]:
                    result.append(" | ".join([str(r)[:30] for r in row)))
                
                header = " | ".join(col_names) if col_names else "Results"
                conn.close()
                return f"{header}\n" + "-" * len(header) + "\n" + "\n".join(result)
            else:
                conn.commit()
                conn.close()
                return f"Query executed! :white_check_mark:\nRows affected: {cursor.rowcount}"
        
        elif action == "execute":
            if not sql:
                return "Error: sql query required for execute action"
            
            cursor.execute(sql)
            conn.commit()
            conn.close()
            return f"SQL executed! :white_check_mark:\nRows affected: {cursor.rowcount}"
        
        else:
            conn.close()
            return f"Error: Unknown action '{action}'. Available: query, execute, list_tables, describe_table, list_databases"
    
    except ImportError:
        return "Error: psycopg2 not installed. Run: pip install psycopg2-binary"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("PostgreSQL plugin loaded. Use 'postgresql' tool in HelloChusquis.")