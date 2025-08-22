#!/usr/bin/env python3
"""
Smart Query Builder - Converts natural language to SQL queries
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

class SmartQueryBuilder:
    """Intelligent query builder that converts natural language to SQL"""
    
    def __init__(self, db_connector):
        self.db_connector = db_connector
        
        # Common natural language patterns
        self.query_patterns = {
            "show_all": [
                r"show (?:me )?(?:all )?(\w+)",
                r"get (?:all )?(\w+)",
                r"list (?:all )?(\w+)",
                r"display (?:all )?(\w+)",
                r"find (?:all )?(\w+)",
                r"select (?:all )?(\w+)"
            ],
            "filter_by": [
                r"(\w+) (?:with|where|that have) (\w+) (?:greater than|more than|above|over) ([^,\s]+)",
                r"(\w+) (?:with|where|that have) (\w+) (?:less than|below|under) ([^,\s]+)",
                r"(\w+) (?:with|where|that have) (\w+) (?:equal to|is) ([^,\s]+)",
                r"(\w+) (?:with|where|that have) (\w+) (?:like|containing) ([^,\s]+)",
                r"(\w+) (?:which|that) (?:are|is) (null|empty|missing)",
                r"(\w+) (?:with|where|that have) (\w+) (?:which|that) (?:are|is) (null|empty|missing)",
                r"(\w+) (?:with|where|that have) (\w+) (?:not )?(?:equal to|is) ([^,\s]+)"
            ],
            "top_n": [
                r"top (\d+) (\w+)",
                r"(\d+) (?:best|highest|most) (\w+)",
                r"(\w+) (?:top|best|highest) (\d+)"
            ],
            "aggregate": [
                r"(?:what is|get|show) (?:the )?(count|sum|average|max|min) (?:of )?(\w+)",
                r"(?:how many|count) (\w+)",
                r"(?:total|sum) (?:of )?(\w+)"
            ],
            "date_range": [
                r"(\w+) (?:from|between) ([^,\s]+) (?:to|and) ([^,\s]+)",
                r"(\w+) (?:in|during) (?:the )?(\w+)",
                r"(\w+) (?:last|past) (\d+) (?:days|weeks|months|years)"
            ]
        }
        
        # SQL templates
        self.sql_templates = {
            "select_all": "SELECT * FROM {table}",
            "select_filtered": "SELECT * FROM {table} WHERE {condition}",
            "select_top": "SELECT * FROM {table} ORDER BY {order_by} DESC LIMIT {limit}",
            "select_aggregate": "SELECT {aggregate}({column}) FROM {table}",
            "select_grouped": "SELECT {columns} FROM {table} GROUP BY {group_by}",
            "select_joined": "SELECT {columns} FROM {table1} {join_type} {table2} ON {join_condition}"
        }
    
    async def build_query(self, natural_query: str, db_config: Dict, selected_table: str = None) -> Dict[str, Any]:
        """
        Convert natural language query to SQL
        """
        try:
            # Step 1: Analyze the natural language query
            analysis = self._analyze_natural_query(natural_query.lower())
            
            # Step 2: Get database schema for context
            schema_info = await self._get_database_schema(db_config)
            
            # Step 3: Match query intent with available tables/columns
            matched_entities = self._match_entities(analysis, schema_info, selected_table)
            
            # Step 4: Generate SQL query
            sql_query = await self._generate_sql_query(analysis, matched_entities, schema_info)
            
            # Step 5: Validate and optimize query
            validation = await self._validate_query(sql_query, db_config)
            
            return {
                "success": True,
                "natural_query": natural_query,
                "analysis": analysis,
                "matched_entities": matched_entities,
                "sql_query": sql_query,
                "validation": validation,
                "explanation": self._explain_query(sql_query, analysis),
                "suggestions": self._generate_suggestions(analysis, matched_entities)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to build query: {str(e)}",
                "natural_query": natural_query,
                "suggestions": self._get_fallback_suggestions(natural_query)
            }
    
    def _analyze_natural_query(self, query: str) -> Dict[str, Any]:
        """Analyze natural language query to extract intent"""
        analysis = {
            "intent": "unknown",
            "entities": [],
            "filters": [],
            "aggregations": [],
            "ordering": [],
            "limit": None,
            "date_range": None
        }
        
        # Detect query intent
        if any(re.search(pattern, query) for pattern in self.query_patterns["show_all"]):
            analysis["intent"] = "select"
            # Extract table name
            for pattern in self.query_patterns["show_all"]:
                match = re.search(pattern, query)
                if match:
                    analysis["entities"].append({"type": "table", "name": match.group(1)})
                    break
        
        # Detect filters - including null checks
        for pattern in self.query_patterns["filter_by"]:
            matches = re.finditer(pattern, query)
            for match in matches:
                if "null|empty|missing" in pattern:
                    # Handle null/empty checks
                    if len(match.groups()) >= 2:
                        table_name = match.group(1)
                        null_type = match.group(2)
                        analysis["filters"].append({
                            "table": table_name,
                            "column": "any",  # Will be matched to actual columns later
                            "operator": "IS NULL" if null_type == "null" else "=",
                            "value": "NULL" if null_type == "null" else "''"
                        })
                else:
                    # Handle regular filters
                    if len(match.groups()) >= 3:
                        analysis["filters"].append({
                            "table": match.group(1),
                            "column": match.group(2),
                            "operator": self._extract_operator(match.group(0)),
                            "value": match.group(3)
                        })
        
        # Detect top N queries
        for pattern in self.query_patterns["top_n"]:
            match = re.search(pattern, query)
            if match:
                analysis["limit"] = int(match.group(1))
                analysis["ordering"] = [{"column": match.group(2), "direction": "DESC"}]
                break
        
        # Detect aggregations
        for pattern in self.query_patterns["aggregate"]:
            match = re.search(pattern, query)
            if match:
                analysis["aggregations"].append({
                    "function": match.group(1),
                    "column": match.group(2) if len(match.groups()) > 1 else "id"
                })
                analysis["intent"] = "aggregate"
                break
        
        # Detect date ranges
        for pattern in self.query_patterns["date_range"]:
            match = re.search(pattern, query)
            if match:
                analysis["date_range"] = {
                    "table": match.group(1),
                    "start": match.group(2),
                    "end": match.group(3) if len(match.groups()) > 2 else None
                }
                break
        
        return analysis
    
    def _extract_operator(self, filter_text: str) -> str:
        """Extract SQL operator from natural language"""
        if any(word in filter_text for word in ["greater than", "more than", "above", "over"]):
            return ">"
        elif any(word in filter_text for word in ["less than", "below", "under"]):
            return "<"
        elif any(word in filter_text for word in ["equal to", "is"]):
            return "="
        elif any(word in filter_text for word in ["like", "containing"]):
            return "LIKE"
        else:
            return "="
    
    async def _get_database_schema(self, db_config: Dict) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            connection = await self.db_connector.get_connection(db_config)
            
            # Get all tables
            tables_query = "SHOW TABLES"
            tables_result = await connection.execute_query(tables_query)
            
            schema_info = {
                "tables": {},
                "relationships": [],
                "common_patterns": {}
            }
            
            for table_row in tables_result:
                table_name = table_row[0]
                
                # Get table structure
                describe_query = f"DESCRIBE {table_name}"
                structure_result = await connection.execute_query(describe_query)
                
                # Get sample data
                sample_query = f"SELECT * FROM {table_name} LIMIT 3"
                try:
                    sample_result = await connection.execute_query(sample_query)
                except:
                    sample_result = []
                
                schema_info["tables"][table_name] = {
                    "columns": [col[0] for col in structure_result],
                    "column_types": {col[0]: col[1] for col in structure_result},
                    "sample_data": sample_result,
                    "row_count": 0  # Will be filled later if needed
                }
            
            # Analyze common patterns
            schema_info["common_patterns"] = self._analyze_schema_patterns(schema_info["tables"])
            
            return schema_info
            
        except Exception as e:
            return {"error": f"Failed to get schema: {str(e)}"}
    
    def _analyze_schema_patterns(self, tables: Dict) -> Dict[str, Any]:
        """Analyze schema for common patterns and relationships"""
        patterns = {
            "id_columns": [],
            "date_columns": [],
            "money_columns": [],
            "name_columns": [],
            "status_columns": [],
            "foreign_keys": []
        }
        
        for table_name, table_info in tables.items():
            for column_name in table_info["columns"]:
                col_lower = column_name.lower()
                
                # ID patterns
                if col_lower in ["id", "user_id", "customer_id", "order_id", "product_id"]:
                    patterns["id_columns"].append(f"{table_name}.{column_name}")
                
                # Date patterns
                if any(word in col_lower for word in ["date", "time", "created", "updated"]):
                    patterns["date_columns"].append(f"{table_name}.{column_name}")
                
                # Money patterns
                if any(word in col_lower for word in ["price", "amount", "cost", "total", "sum"]):
                    patterns["money_columns"].append(f"{table_name}.{column_name}")
                
                # Name patterns
                if any(word in col_lower for word in ["name", "title", "description"]):
                    patterns["name_columns"].append(f"{table_name}.{column_name}")
                
                # Status patterns
                if any(word in col_lower for word in ["status", "state", "active", "enabled"]):
                    patterns["status_columns"].append(f"{table_name}.{column_name}")
        
        return patterns
    
    def _match_entities(self, analysis: Dict, schema_info: Dict, selected_table: str = None) -> Dict[str, Any]:
        """Match natural language entities with database schema"""
        matched = {
            "tables": [],
            "columns": [],
            "relationships": []
        }
        
        if "error" in schema_info:
            return matched
        
        # If a specific table is selected, use it
        if selected_table and selected_table != "All Tables" and selected_table in schema_info["tables"]:
            matched["tables"].append(selected_table)
            
            # Update filters to use the selected table
            for filter_item in analysis.get("filters", []):
                column_name = filter_item["column"]
                table_columns = schema_info["tables"][selected_table]["columns"]
                
                if column_name == "any": # Handle the "any" column for null checks
                    matched["columns"].append(f"{selected_table}.{column_name}")
                elif column_name in table_columns:
                    matched["columns"].append(f"{selected_table}.{column_name}")
                else:
                    # Try partial matches
                    for actual_col in table_columns:
                        if column_name in actual_col or actual_col in column_name:
                            matched["columns"].append(f"{selected_table}.{actual_col}")
                            break
        else:
            # Match table names from natural language
            for entity in analysis.get("entities", []):
                if entity["type"] == "table":
                    table_name = entity["name"]
                    # Try exact match first
                    if table_name in schema_info["tables"]:
                        matched["tables"].append(table_name)
                    else:
                        # Try partial matches
                        for actual_table in schema_info["tables"].keys():
                            if table_name in actual_table or actual_table in table_name:
                                matched["tables"].append(actual_table)
                                break
            
            # Match columns from filters
            for filter_item in analysis.get("filters", []):
                table_name = filter_item["table"]
                column_name = filter_item["column"]
                
                if table_name in schema_info["tables"]:
                    table_columns = schema_info["tables"][table_name]["columns"]
                    if column_name == "any": # Handle the "any" column for null checks
                        matched["columns"].append(f"{table_name}.{column_name}")
                    elif column_name in table_columns:
                        matched["columns"].append(f"{table_name}.{column_name}")
                    else:
                        # Try partial matches
                        for actual_col in table_columns:
                            if column_name in actual_col or actual_col in column_name:
                                matched["columns"].append(f"{table_name}.{actual_col}")
                                break
        
        return matched
    
    async def _generate_sql_query(self, analysis: Dict, matched_entities: Dict, schema_info: Dict) -> str:
        """Generate SQL query based on analysis and matched entities"""
        
        # Start with basic SELECT
        if analysis["intent"] == "aggregate":
            # Handle aggregate queries
            agg = analysis["aggregations"][0]
            table = matched_entities["tables"][0] if matched_entities["tables"] else "unknown_table"
            column = agg["column"]
            
            query = f"SELECT {agg['function'].upper()}({column}) FROM {table}"
        else:
            # Handle regular SELECT queries
            table = matched_entities["tables"][0] if matched_entities["tables"] else "unknown_table"
            query = f"SELECT * FROM {table}"
        
        # Add WHERE clauses
        where_conditions = []
        for filter_item in analysis.get("filters", []):
            table_name = filter_item["table"]
            column_name = filter_item["column"]
            operator = filter_item["operator"]
            value = filter_item["value"]
            
            # Handle null checks specially
            if column_name == "any" and operator == "IS NULL":
                # For null checks on "any" column, we need to check all nullable columns
                if table_name in schema_info["tables"]:
                    table_columns = schema_info["tables"][table_name]["columns"]
                    column_types = schema_info["tables"][table_name]["column_types"]
                    
                    # Find columns that can be null (not primary keys, not NOT NULL)
                    nullable_conditions = []
                    for col in table_columns:
                        col_type = column_types.get(col, "")
                        # Skip primary keys and NOT NULL columns for null checks
                        if "NOT NULL" not in col_type.upper() and col.lower() != "id":
                            nullable_conditions.append(f"{col} IS NULL")
                    
                    if nullable_conditions:
                        where_conditions.append(f"({' OR '.join(nullable_conditions)})")
                    else:
                        # If no nullable columns found, check common nullable columns
                        common_nullable = ["description", "notes", "comments", "details", "metadata"]
                        for col in common_nullable:
                            if col in table_columns:
                                nullable_conditions.append(f"{col} IS NULL")
                        if nullable_conditions:
                            where_conditions.append(f"({' OR '.join(nullable_conditions)})")
            else:
                # Handle regular filters
                if matched_entities["tables"] and len(matched_entities["tables"]) == 1:
                    # Use just the column name since we're already in the specific table
                    if operator == "LIKE":
                        condition = f"{column_name} LIKE '%{value}%'"
                    elif operator == "IS NULL":
                        condition = f"{column_name} IS NULL"
                    elif value.replace(".", "").isdigit():
                        condition = f"{column_name} {operator} {value}"
                    else:
                        condition = f"{column_name} {operator} '{value}'"
                else:
                    # Use table prefix for clarity when multiple tables might be involved
                    if operator == "LIKE":
                        condition = f"{table_name}.{column_name} LIKE '%{value}%'"
                    elif operator == "IS NULL":
                        condition = f"{table_name}.{column_name} IS NULL"
                    elif value.replace(".", "").isdigit():
                        condition = f"{table_name}.{column_name} {operator} {value}"
                    else:
                        condition = f"{table_name}.{column_name} {operator} '{value}'"
                
                where_conditions.append(condition)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Add ORDER BY
        if analysis.get("ordering"):
            order_clauses = []
            for order_item in analysis["ordering"]:
                order_clauses.append(f"{order_item['column']} {order_item['direction']}")
            query += " ORDER BY " + ", ".join(order_clauses)
        
        # Add LIMIT
        if analysis.get("limit"):
            query += f" LIMIT {analysis['limit']}"
        
        return query
    
    async def _validate_query(self, sql_query: str, db_config: Dict) -> Dict[str, Any]:
        """Validate the generated SQL query"""
        try:
            connection = await self.db_connector.get_connection(db_config)
            
            # Try to execute the query with LIMIT 1 to validate syntax
            test_query = sql_query
            if "LIMIT" not in sql_query.upper():
                test_query += " LIMIT 1"
            
            result = await connection.execute_query(test_query)
            
            return {
                "valid": True,
                "test_result": result,
                "estimated_rows": len(result) if result else 0
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "suggestions": self._get_query_fix_suggestions(str(e))
            }
    
    def _explain_query(self, sql_query: str, analysis: Dict) -> str:
        """Explain what the SQL query does in natural language"""
        explanation = "This query "
        
        if analysis["intent"] == "aggregate":
            agg = analysis["aggregations"][0]
            explanation += f"calculates the {agg['function']} of {agg['column']} "
        else:
            explanation += "retrieves all records "
        
        # Explain filters more specifically
        if analysis.get("filters"):
            filter_explanations = []
            for filter_item in analysis["filters"]:
                if filter_item["operator"] == "IS NULL":
                    if filter_item["column"] == "any":
                        filter_explanations.append("that have null values in any nullable column")
                    else:
                        filter_explanations.append(f"where {filter_item['column']} is null")
                elif filter_item["operator"] == "LIKE":
                    filter_explanations.append(f"where {filter_item['column']} contains '{filter_item['value']}'")
                else:
                    filter_explanations.append(f"where {filter_item['column']} {filter_item['operator']} {filter_item['value']}")
            
            if filter_explanations:
                explanation += "that match the following conditions: " + ", ".join(filter_explanations) + " "
        
        if analysis.get("ordering"):
            explanation += "and sorts them by the specified criteria "
        
        if analysis.get("limit"):
            explanation += f"and limits the results to {analysis['limit']} records "
        
        explanation += "from the database."
        
        return explanation
    
    def _generate_suggestions(self, analysis: Dict, matched_entities: Dict) -> List[str]:
        """Generate suggestions for improving the query"""
        suggestions = []
        
        if not matched_entities["tables"]:
            suggestions.append("💡 Try specifying a table name (e.g., 'customers', 'orders')")
        
        if analysis["intent"] == "unknown":
            suggestions.append("💡 Try being more specific about what you want to see")
        
        if analysis.get("filters"):
            suggestions.append("💡 Consider adding indexes on filtered columns for better performance")
        
        if analysis.get("limit") and analysis["limit"] > 100:
            suggestions.append("💡 Large result sets may be slow - consider adding more filters")
        
        return suggestions
    
    def _get_fallback_suggestions(self, query: str) -> List[str]:
        """Get fallback suggestions when query building fails"""
        return [
            "💡 Try rephrasing your query (e.g., 'Show me all customers')",
            "💡 Specify table names clearly (e.g., 'users', 'orders', 'products')",
            "💡 Use simple filters (e.g., 'customers with age > 25')",
            "💡 Try asking for specific data (e.g., 'top 10 products by sales')"
        ]
    
    def _get_query_fix_suggestions(self, error: str) -> List[str]:
        """Get suggestions for fixing SQL errors"""
        suggestions = []
        
        if "table" in error.lower() and "doesn't exist" in error.lower():
            suggestions.append("🔧 Check the table name spelling")
            suggestions.append("🔧 Use 'SHOW TABLES' to see available tables")
        
        if "column" in error.lower() and "doesn't exist" in error.lower():
            suggestions.append("🔧 Check the column name spelling")
            suggestions.append("🔧 Use 'DESCRIBE table_name' to see available columns")
        
        if "syntax" in error.lower():
            suggestions.append("🔧 The generated SQL has syntax errors")
            suggestions.append("🔧 Try rephrasing your natural language query")
        
        return suggestions
