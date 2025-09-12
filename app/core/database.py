import aiomysql
from typing import Dict, Any, List
from app.core.config import settings
import json
import os

class DatabaseManager:
    def __init__(self):
        # Removed connection caching to prevent stale data
        self.subdomains = self._load_subdomains()
    
    def _load_subdomains(self) -> Dict[str, str]:
        """Load subdomains configuration from JSON file"""
        try:
            with open(settings.SUBDOMAINS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    async def get_connection(self, subdomain: str = None) -> aiomysql.Connection:
        """Get fresh database connection for specific subdomain or master database (no caching)"""
        if subdomain and subdomain in self.subdomains:
            db_name = self.subdomains[subdomain]
        else:
            # Connect to MySQL server without specific database
            db_name = None
        
        # Always create a fresh connection to prevent stale data
        connection = await aiomysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=db_name,
            charset='utf8mb4',
            autocommit=True
        )
        
        if connection is None:
            raise Exception(f"Failed to connect to database: {db_name or 'default'}")
        
        return connection
    
    async def close_all_connections(self):
        """Close all database connections (no longer needed since we don't cache connections)"""
        # No longer needed since we create fresh connections each time
        pass
    
    def get_available_subdomains(self) -> List[str]:
        """Get list of available subdomains"""
        return list(self.subdomains.keys())
    
    async def test_all_subdomains(self) -> Dict[str, Any]:
        """Test connection to all configured subdomains (each subdomain is a database within the main MySQL server)"""
        # Test only the first 5 subdomains
        subdomains_to_test = dict(list(self.subdomains.items())[:5])
        
        results = {
            "total_subdomains_configured": len(self.subdomains),
            "total_subdomains_tested": len(subdomains_to_test),
            "successful_connections": 0,
            "failed_connections": 0,
            "subdomain_results": {},
            "summary": {}
        }
        
        if not self.subdomains:
            return {
                "status": "warning",
                "message": "No subdomains configured",
                "subdomains_file": settings.SUBDOMAINS_FILE,
                "results": results
            }
        
        # Test only the first 5 subdomains
        subdomains_to_test = dict(list(self.subdomains.items())[:5])
        
        for subdomain_name, db_name in subdomains_to_test.items():
            try:
                # Test connection to this subdomain
                connection = await aiomysql.connect(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    db=db_name,
                    charset='utf8mb4',
                    autocommit=True
                )
                
                if connection:
                    cursor = await connection.cursor()
                    
                    # Test basic query
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    
                    # Get current time
                    await cursor.execute("SELECT NOW()")
                    time_result = await cursor.fetchone()
                    
                    # Get database info
                    await cursor.execute("SELECT DATABASE()")
                    db_name_result = await cursor.fetchone()
                    
                    await cursor.execute("SELECT VERSION()")
                    version_result = await cursor.fetchone()
                    
                    # Get table count
                    await cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()")
                    table_count = await cursor.fetchone()
                    
                    await cursor.close()
                    await connection.ensure_closed()
                    
                    results["subdomain_results"][subdomain_name] = {
                        "status": "connected",
                        "database_name": db_name,
                        "test_query_result": result[0] if result else None,
                        "current_time": str(time_result[0]) if time_result else None,
                        "database_name_actual": db_name_result[0] if db_name_result else None,
                        "mysql_version": version_result[0] if version_result else None,
                        "table_count": table_count[0] if table_count else 0
                    }
                    results["successful_connections"] += 1
                else:
                    results["subdomain_results"][subdomain_name] = {
                        "status": "error",
                        "database_name": db_name,
                        "error": "Connection returned None"
                    }
                    results["failed_connections"] += 1
                    
            except Exception as e:
                results["subdomain_results"][subdomain_name] = {
                    "status": "error",
                    "database_name": db_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                results["failed_connections"] += 1
        
        # Generate summary
        results["summary"] = {
            "connection_success_rate": f"{(results['successful_connections'] / results['total_subdomains_tested'] * 100):.1f}%" if results['total_subdomains_tested'] > 0 else "0%",
            "all_connected": results["failed_connections"] == 0,
            "connection_params": {
                "host": settings.DB_HOST,
                "port": settings.DB_PORT,
                "user": settings.DB_USER,
                "password": "***" if settings.DB_PASSWORD else "None"
            }
        }
        
        return {
            "status": "completed",
            "message": f"Tested {results['total_subdomains_tested']} of {results['total_subdomains_configured']} subdomains (first 5 only)",
            "results": results
        }



# Global database manager instance
db_manager = DatabaseManager()
