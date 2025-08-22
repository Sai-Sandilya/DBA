#!/usr/bin/env python3
"""
Smart Join Assistant - Helps users understand table joins and their outputs
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class SmartJoinAssistant:
    """Intelligent assistant for table joins"""
    
    def __init__(self, db_connector):
        self.db_connector = db_connector
        
    async def analyze_join_request(self, table1: str, table2: str, db_config: Dict) -> Dict[str, Any]:
        """
        Analyze two tables and provide join recommendations
        """
        try:
            # Get table schemas and sample data
            table1_info = await self._get_table_info(table1, db_config)
            table2_info = await self._get_table_info(table2, db_config)
            
            # Find potential join keys
            join_keys = self._find_join_keys(table1_info, table2_info)
            
            # Generate join examples
            join_examples = await self._generate_join_examples(table1, table2, join_keys, db_config)
            
            # Create recommendations
            recommendations = self._create_join_recommendations(table1_info, table2_info, join_keys)
            
            return {
                "table1_info": table1_info,
                "table2_info": table2_info,
                "join_keys": join_keys,
                "join_examples": join_examples,
                "recommendations": recommendations,
                "summary": self._create_summary(table1, table2, join_keys, recommendations)
            }
            
        except Exception as e:
            return {"error": f"Failed to analyze join: {str(e)}"}
    
    async def _get_table_info(self, table_name: str, db_config: Dict) -> Dict[str, Any]:
        """Get table schema and sample data"""
        try:
            connection = await self.db_connector.get_connection(db_config)
            
            # Get table schema
            schema_query = f"DESCRIBE {table_name}"
            schema_result = await connection.execute_query(schema_query)
            
            # Get sample data (first 5 rows)
            sample_query = f"SELECT * FROM {table_name} LIMIT 5"
            sample_result = await connection.execute_query(sample_query)
            
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = await connection.execute_query(count_query)
            row_count = count_result[0][0] if count_result else 0
            
            return {
                "name": table_name,
                "schema": schema_result,
                "sample_data": sample_result,
                "row_count": row_count,
                "columns": [col[0] for col in schema_result]
            }
            
        except Exception as e:
            return {"error": f"Failed to get table info for {table_name}: {str(e)}"}
    
    def _find_join_keys(self, table1_info: Dict, table2_info: Dict) -> List[Dict[str, str]]:
        """Find potential join keys between tables"""
        join_keys = []
        
        if "error" in table1_info or "error" in table2_info:
            return join_keys
            
        table1_cols = table1_info.get("columns", [])
        table2_cols = table2_info.get("columns", [])
        
        # Look for common column names
        common_cols = set(table1_cols) & set(table2_cols)
        for col in common_cols:
            join_keys.append({
                "table1_column": col,
                "table2_column": col,
                "type": "exact_match",
                "confidence": "high"
            })
        
        # Look for ID-like columns
        id_patterns = ["id", "_id", "code", "_code"]
        for pattern in id_patterns:
            table1_id_cols = [col for col in table1_cols if pattern in col.lower()]
            table2_id_cols = [col for col in table2_cols if pattern in col.lower()]
            
            for col1 in table1_id_cols:
                for col2 in table2_id_cols:
                    if col1 != col2:  # Avoid duplicates
                        join_keys.append({
                            "table1_column": col1,
                            "table2_column": col2,
                            "type": "id_pattern",
                            "confidence": "medium"
                        })
        
        return join_keys
    
    async def _generate_join_examples(self, table1: str, table2: str, join_keys: List[Dict], db_config: Dict) -> Dict[str, Any]:
        """Generate examples for different join types"""
        examples = {}
        
        if not join_keys:
            return {"error": "No join keys found"}
        
        # Use the first join key for examples
        join_key = join_keys[0]
        
        try:
            connection = await self.db_connector.get_connection(db_config)
            
            # Detect db type (supports dict or dataclass-like)
            db_type = None
            try:
                db_type = (db_config.get("db_type") if isinstance(db_config, dict) else getattr(db_config, "db_type", None))
            except Exception:
                db_type = None
            db_type_str = (str(db_type).lower() if db_type is not None else "")

            # Generate different join types
            join_types = {
                "INNER JOIN": f"""
                    SELECT t1.*, t2.* 
                    FROM {table1} t1 
                    INNER JOIN {table2} t2 
                    ON t1.{join_key['table1_column']} = t2.{join_key['table2_column']} 
                    LIMIT 10
                """,
                "LEFT JOIN": f"""
                    SELECT t1.*, t2.* 
                    FROM {table1} t1 
                    LEFT JOIN {table2} t2 
                    ON t1.{join_key['table1_column']} = t2.{join_key['table2_column']} 
                    LIMIT 10
                """,
                "RIGHT JOIN": f"""
                    SELECT t1.*, t2.* 
                    FROM {table1} t1 
                    RIGHT JOIN {table2} t2 
                    ON t1.{join_key['table1_column']} = t2.{join_key['table2_column']} 
                    LIMIT 10
                """,
                # MySQL does not support FULL OUTER JOIN; emulate with UNION of LEFT and RIGHT excluding overlaps
                "FULL OUTER JOIN": (
                    f"""
                    SELECT t1.*, t2.*
                    FROM {table1} t1
                    LEFT JOIN {table2} t2
                      ON t1.{join_key['table1_column']} = t2.{join_key['table2_column']}
                    UNION ALL
                    SELECT t1.*, t2.*
                    FROM {table1} t1
                    RIGHT JOIN {table2} t2
                      ON t1.{join_key['table1_column']} = t2.{join_key['table2_column']}
                    WHERE t1.{join_key['table1_column']} IS NULL
                    LIMIT 10
                    """ if db_type_str == "mysql" else f"""
                    SELECT t1.*, t2.* 
                    FROM {table1} t1 
                    FULL OUTER JOIN {table2} t2 
                      ON t1.{join_key['table1_column']} = t2.{join_key['table2_column']} 
                    LIMIT 10
                    """
                )
            }
            
            for join_type, query in join_types.items():
                try:
                    result = await connection.execute_query(query)
                    examples[join_type] = {
                        "query": query,
                        "result": result,
                        "row_count": len(result)
                    }
                except Exception as e:
                    examples[join_type] = {
                        "query": query,
                        "error": str(e),
                        "row_count": 0
                    }
            
            return examples
            
        except Exception as e:
            return {"error": f"Failed to generate join examples: {str(e)}"}
    
    def _create_join_recommendations(self, table1_info: Dict, table2_info: Dict, join_keys: List[Dict]) -> List[Dict[str, Any]]:
        """Create intelligent join recommendations"""
        recommendations = []
        
        if not join_keys:
            recommendations.append({
                "type": "warning",
                "message": "No obvious join keys found. You may need to specify custom join conditions.",
                "suggestion": "Consider joining on business logic or creating a mapping table."
            })
            return recommendations
        
        # Analyze table sizes
        table1_count = table1_info.get("row_count", 0)
        table2_count = table2_info.get("row_count", 0)
        
        # Recommend based on table sizes and relationships
        if table1_count > table2_count * 10:
            recommendations.append({
                "type": "info",
                "message": f"{table1_info['name']} is much larger than {table2_info['name']}",
                "suggestion": "Consider LEFT JOIN to preserve all records from the larger table.",
                "recommended_join": "LEFT JOIN"
            })
        elif table2_count > table1_count * 10:
            recommendations.append({
                "type": "info", 
                "message": f"{table2_info['name']} is much larger than {table1_info['name']}",
                "suggestion": "Consider RIGHT JOIN to preserve all records from the larger table.",
                "recommended_join": "RIGHT JOIN"
            })
        else:
            recommendations.append({
                "type": "info",
                "message": "Tables are similar in size",
                "suggestion": "INNER JOIN is usually best for similar-sized tables with matching data.",
                "recommended_join": "INNER JOIN"
            })
        
        # Add join key recommendations
        for i, key in enumerate(join_keys):
            confidence = "high" if key["type"] == "exact_match" else "medium"
            recommendations.append({
                "type": "join_key",
                "message": f"Join key {i+1}: {key['table1_column']} = {key['table2_column']}",
                "confidence": confidence,
                "suggestion": f"Use this key for joining: ON {key['table1_column']} = {key['table2_column']}"
            })
        
        return recommendations
    
    def _create_summary(self, table1: str, table2: str, join_keys: List[Dict], recommendations: List[Dict]) -> str:
        """Create a summary of the join analysis"""
        summary = f"## Join Analysis: {table1} + {table2}\n\n"
        
        if join_keys:
            summary += f"**Found {len(join_keys)} potential join key(s):**\n"
            for i, key in enumerate(join_keys):
                summary += f"- {key['table1_column']} = {key['table2_column']} ({key['confidence']} confidence)\n"
        else:
            summary += "**No automatic join keys found** - manual specification needed\n"
        
        summary += "\n**Recommendations:**\n"
        for rec in recommendations:
            if rec["type"] == "recommended_join":
                summary += f"- **Best join type**: {rec['recommended_join']}\n"
            elif rec["type"] == "join_key":
                summary += f"- **Join key**: {rec['suggestion']}\n"
        
        return summary
    
    async def generate_final_query(self, table1: str, table2: str, join_type: str, 
                                 join_condition: str, selected_columns: List[str] = None) -> str:
        """Generate the final SQL query based on user choices"""
        
        if not selected_columns:
            selected_columns = ["*"]
        
        columns_str = ", ".join(selected_columns)
        
        query = f"""
        SELECT {columns_str}
        FROM {table1} t1
        {join_type} {table2} t2
        ON {join_condition}
        """
        
        return query.strip()
    
    def explain_join_type(self, join_type: str) -> Dict[str, str]:
        """Explain what each join type does"""
        explanations = {
            "INNER JOIN": {
                "description": "Returns only the rows that have matching values in both tables",
                "when_to_use": "When you only want records that exist in both tables",
                "example": "Customers who have placed orders",
                "visual": "A ∩ B (intersection)"
            },
            "LEFT JOIN": {
                "description": "Returns all rows from the left table and matching rows from the right table",
                "when_to_use": "When you want all records from the first table, even if no match in second",
                "example": "All customers and their orders (including customers with no orders)",
                "visual": "All of A + matching B"
            },
            "RIGHT JOIN": {
                "description": "Returns all rows from the right table and matching rows from the left table", 
                "when_to_use": "When you want all records from the second table, even if no match in first",
                "example": "All orders and their customers (including orphaned orders)",
                "visual": "All of B + matching A"
            },
            "FULL OUTER JOIN": {
                "description": "Returns all rows from both tables, with NULLs where no match exists",
                "when_to_use": "When you want all records from both tables regardless of matches",
                "example": "Complete audit trail showing all customers and all orders",
                "visual": "A ∪ B (union)"
            }
        }
        
        return explanations.get(join_type, {
            "description": "Unknown join type",
            "when_to_use": "Not recommended",
            "example": "N/A",
            "visual": "N/A"
        })
