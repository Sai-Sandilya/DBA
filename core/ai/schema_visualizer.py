#!/usr/bin/env python3
"""
Schema Visualizer - Interactive table relationship diagrams
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

class SchemaVisualizer:
    """Interactive schema visualization and ERD generator"""
    
    def __init__(self, db_connector):
        self.db_connector = db_connector
        
        # Visual configuration
        self.visual_config = {
            "colors": {
                "primary": "#FF6B6B",
                "secondary": "#4ECDC4", 
                "tertiary": "#45B7D1",
                "quaternary": "#96CEB4",
                "quinary": "#FFEAA7"
            },
            "shapes": {
                "table": "rectangle",
                "view": "diamond",
                "index": "circle"
            },
            "layout": {
                "direction": "TB",  # Top to Bottom
                "spacing": 100,
                "padding": 20
            }
        }
    
    async def generate_schema_diagram(self, db_config: Dict) -> Dict[str, Any]:
        """
        Generate comprehensive schema visualization
        """
        try:
            # Get database schema
            schema_info = await self._get_database_schema(db_config)
            
            if "error" in schema_info:
                return {"error": f"Failed to get schema: {schema_info['error']}"}
            
            # Analyze relationships (simplified)
            relationships = await self._analyze_relationships(schema_info, db_config)
            
            # Generate visual elements
            visual_elements = self._generate_visual_elements(schema_info, relationships)
            
            # Create different diagram types
            diagrams = {
                "erd": self._create_erd_diagram(schema_info, relationships),
                "network": self._create_network_diagram(schema_info, relationships),
                "hierarchy": self._create_hierarchy_diagram(schema_info, relationships),
                "summary": self._create_summary_diagram(schema_info, relationships)
            }
            
            return {
                "success": True,
                "timestamp": datetime.now(),
                "database": getattr(db_config, "database", "unknown"),
                "schema_info": schema_info,
                "relationships": relationships,
                "visual_elements": visual_elements,
                "diagrams": diagrams,
                "statistics": self._calculate_schema_statistics(schema_info, relationships)
            }
            
        except Exception as e:
            return {"error": f"Schema visualization failed: {str(e)}"}
    
    async def _get_database_schema(self, db_config: Dict) -> Dict[str, Any]:
        """Get comprehensive database schema information"""
        try:
            connection = await self.db_connector.get_connection(db_config)
            
            # Get all tables
            tables_query = "SHOW TABLES"
            tables_result = await connection.execute_query(tables_query)
            
            schema_info = {
                "tables": {},
                "views": {},
                "indexes": {},
                "triggers": {},
                "procedures": {},
                "functions": {}
            }
            
            for table_row in tables_result:
                table_name = table_row[0]
                
                # Get table structure
                describe_query = f"DESCRIBE {table_name}"
                structure_result = await connection.execute_query(describe_query)
                
                # Get table indexes
                indexes_query = f"SHOW INDEX FROM {table_name}"
                try:
                    indexes_result = await connection.execute_query(indexes_query)
                except:
                    indexes_result = []
                
                # Get table size and row count
                stats_query = f"""
                    SELECT 
                        TABLE_ROWS,
                        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size_MB'
                    FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                """
                try:
                    stats_result = await connection.execute_query(stats_query)
                    table_rows = stats_result[0][0] if stats_result else 0
                    table_size = stats_result[0][1] if stats_result else 0
                except:
                    table_rows = 0
                    table_size = 0
                
                # Process structure to find primary keys (simplified)
                primary_keys = []
                for col in structure_result:
                    if len(col) > 3 and col[3] == 'PRI':  # Primary key indicator
                        primary_keys.append(col[0])
                
                # Process indexes
                table_indexes = []
                for index in indexes_result:
                    if len(index) >= 6:
                        table_indexes.append({
                            "name": index[2],
                            "column": index[4],
                            "type": index[10] if len(index) > 10 else "BTREE"
                        })
                
                schema_info["tables"][table_name] = {
                    "columns": [col[0] for col in structure_result],
                    "column_types": {col[0]: col[1] for col in structure_result},
                    "column_nullable": {col[0]: col[2] for col in structure_result},
                    "column_defaults": {col[0]: col[4] for col in structure_result},
                    "primary_keys": primary_keys,
                    "foreign_keys": [],  # Simplified - no foreign key detection
                    "unique_constraints": [],
                    "indexes": table_indexes,
                    "row_count": table_rows,
                    "size_mb": table_size
                }
            
            return schema_info
            
        except Exception as e:
            return {"error": f"Failed to get schema: {str(e)}"}
    
    async def _analyze_relationships(self, schema_info: Dict, db_config: Dict) -> Dict[str, Any]:
        """Analyze table relationships and dependencies (simplified)"""
        relationships = {
            "foreign_keys": [],
            "potential_relationships": [],
            "circular_dependencies": [],
            "orphaned_tables": [],
            "dependency_chains": []
        }
        
        # Find potential relationships (naming conventions only)
        for table_name, table_info in schema_info["tables"].items():
            for column_name in table_info["columns"]:
                # Look for columns that might be foreign keys but aren't defined as such
                if column_name.lower().endswith('_id') and column_name.lower() != 'id':
                    potential_ref_table = column_name[:-3]  # Remove '_id'
                    if potential_ref_table in schema_info["tables"]:
                        relationships["potential_relationships"].append({
                            "from_table": table_name,
                            "from_column": column_name,
                            "to_table": potential_ref_table,
                            "to_column": "id",
                            "type": "potential",
                            "confidence": 0.8
                        })
        
        # Find orphaned tables (no relationships)
        all_related_tables = set()
        for rel in relationships["foreign_keys"] + relationships["potential_relationships"]:
            all_related_tables.add(rel["from_table"])
            all_related_tables.add(rel["to_table"])
        
        for table_name in schema_info["tables"].keys():
            if table_name not in all_related_tables:
                relationships["orphaned_tables"].append(table_name)
        
        return relationships
    
    def _generate_visual_elements(self, schema_info: Dict, relationships: Dict) -> Dict[str, Any]:
        """Generate visual elements for the diagram"""
        elements = {
            "nodes": [],
            "edges": [],
            "groups": [],
            "annotations": []
        }
        
        # Generate nodes for tables
        for table_name, table_info in schema_info["tables"].items():
            node = {
                "id": table_name,
                "type": "table",
                "label": table_name,
                "data": {
                    "columns": table_info["columns"],
                    "primary_keys": table_info["primary_keys"],
                    "foreign_keys": table_info["foreign_keys"],
                    "row_count": table_info["row_count"],
                    "size_mb": table_info["size_mb"]
                },
                "position": {"x": 0, "y": 0},  # Will be set by layout algorithm
                "style": {
                    "backgroundColor": self.visual_config["colors"]["primary"],
                    "borderColor": "#333",
                    "borderWidth": 2
                }
            }
            elements["nodes"].append(node)
        
        # Generate edges for potential relationships only
        for rel in relationships["potential_relationships"]:
            edge = {
                "id": f"{rel['from_table']}_{rel['from_column']}_to_{rel['to_table']}_potential",
                "source": rel["from_table"],
                "target": rel["to_table"],
                "label": f"{rel['from_column']} → {rel['to_column']} (potential)",
                "type": "potential",
                "style": {
                    "stroke": self.visual_config["colors"]["tertiary"],
                    "strokeWidth": 1,
                    "strokeDasharray": "5,5",
                    "arrowHead": "arrow"
                }
            }
            elements["edges"].append(edge)
        
        return elements
    
    def _create_erd_diagram(self, schema_info: Dict, relationships: Dict) -> Dict[str, Any]:
        """Create Entity Relationship Diagram"""
        erd = {
            "type": "erd",
            "title": "Entity Relationship Diagram",
            "description": "Shows tables and their relationships",
            "elements": {
                "entities": [],
                "relationships": [],
                "attributes": []
            }
        }
        
        # Create entities (tables)
        for table_name, table_info in schema_info["tables"].items():
            entity = {
                "name": table_name,
                "type": "entity",
                "attributes": []
            }
            
            # Add attributes (columns)
            for column_name in table_info["columns"]:
                column_type = table_info["column_types"][column_name]
                is_nullable = table_info["column_nullable"][column_name]
                is_primary = column_name in table_info["primary_keys"]
                is_foreign = any(fk["column"] == column_name for fk in table_info["foreign_keys"])
                
                attribute = {
                    "name": column_name,
                    "type": column_type,
                    "nullable": is_nullable == "YES",
                    "primary_key": is_primary,
                    "foreign_key": is_foreign
                }
                entity["attributes"].append(attribute)
            
            erd["elements"]["entities"].append(entity)
        
        # Create relationships (potential only)
        for rel in relationships["potential_relationships"]:
            relationship = {
                "name": f"{rel['from_table']}_to_{rel['to_table']}",
                "from_entity": rel["from_table"],
                "to_entity": rel["to_table"],
                "from_attribute": rel["from_column"],
                "to_attribute": rel["to_column"],
                "type": "potential"
            }
            erd["elements"]["relationships"].append(relationship)
        
        return erd
    
    def _create_network_diagram(self, schema_info: Dict, relationships: Dict) -> Dict[str, Any]:
        """Create network diagram showing table connections"""
        network = {
            "type": "network",
            "title": "Table Relationship Network",
            "description": "Shows how tables are connected",
            "nodes": [],
            "edges": []
        }
        
        # Create nodes
        for table_name, table_info in schema_info["tables"].items():
            node = {
                "id": table_name,
                "label": table_name,
                "size": min(max(table_info["row_count"] / 1000, 10), 50),  # Size based on row count
                "color": self.visual_config["colors"]["primary"],
                "data": {
                    "row_count": table_info["row_count"],
                    "size_mb": table_info["size_mb"],
                    "column_count": len(table_info["columns"])
                }
            }
            network["nodes"].append(node)
        
        # Create edges (potential relationships only)
        for rel in relationships["potential_relationships"]:
            edge = {
                "source": rel["from_table"],
                "target": rel["to_table"],
                "label": f"{rel['from_column']} → {rel['to_column']}",
                "color": self.visual_config["colors"]["tertiary"],
                "width": 1
            }
            network["edges"].append(edge)
        
        return network
    
    def _create_hierarchy_diagram(self, schema_info: Dict, relationships: Dict) -> Dict[str, Any]:
        """Create hierarchy diagram showing table dependencies"""
        hierarchy = {
            "type": "hierarchy",
            "title": "Table Dependency Hierarchy",
            "description": "Shows table dependencies in hierarchical structure",
            "levels": [],
            "dependencies": []
        }
        
        # Simplified hierarchy - all tables at same level since no foreign keys
        hierarchy["levels"].append({
            "level": 0,
            "tables": list(schema_info["tables"].keys())
        })
        
        return hierarchy
    
    def _create_summary_diagram(self, schema_info: Dict, relationships: Dict) -> Dict[str, Any]:
        """Create summary diagram with key statistics"""
        summary = {
            "type": "summary",
            "title": "Database Schema Summary",
            "description": "Overview of database structure and statistics",
            "statistics": {
                "total_tables": len(schema_info["tables"]),
                "total_columns": sum(len(table["columns"]) for table in schema_info["tables"].values()),
                "total_rows": sum(table["row_count"] for table in schema_info["tables"].values()),
                "total_size_mb": sum(table["size_mb"] for table in schema_info["tables"].values()),
                "tables_with_primary_keys": sum(1 for table in schema_info["tables"].values() if table["primary_keys"]),
                "tables_with_foreign_keys": sum(1 for table in schema_info["tables"].values() if table["foreign_keys"])
            },
            "largest_tables": [],
            "most_connected_tables": []
        }
        
        # Find largest tables
        table_sizes = [(name, info["size_mb"]) for name, info in schema_info["tables"].items()]
        table_sizes.sort(key=lambda x: x[1], reverse=True)
        summary["largest_tables"] = table_sizes[:5]
        
        # Find most connected tables (simplified)
        connection_counts = {}
        for table_name in schema_info["tables"].keys():
            count = 0
            for rel in relationships["potential_relationships"]:
                if rel["from_table"] == table_name or rel["to_table"] == table_name:
                    count += 1
            connection_counts[table_name] = count
        
        most_connected = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)
        summary["most_connected_tables"] = most_connected[:5]
        
        return summary
    
    def _calculate_schema_statistics(self, schema_info: Dict, relationships: Dict) -> Dict[str, Any]:
        """Calculate comprehensive schema statistics"""
        stats = {
            "overview": {
                "total_tables": len(schema_info["tables"]),
                "total_columns": sum(len(table["columns"]) for table in schema_info["tables"].values()),
                "total_rows": sum(table["row_count"] for table in schema_info["tables"].values()),
                "total_size_mb": sum(table["size_mb"] for table in schema_info["tables"].values())
            },
            "relationships": {
                "total_foreign_keys": len(relationships["foreign_keys"]),
                "potential_relationships": len(relationships["potential_relationships"]),
                "orphaned_tables": len(relationships["orphaned_tables"]),
                "circular_dependencies": len(relationships["circular_dependencies"])
            },
            "data_quality": {
                "tables_with_primary_keys": sum(1 for table in schema_info["tables"].values() if table["primary_keys"]),
                "tables_without_primary_keys": sum(1 for table in schema_info["tables"].values() if not table["primary_keys"]),
                "tables_with_foreign_keys": sum(1 for table in schema_info["tables"].values() if table["foreign_keys"]),
                "tables_without_foreign_keys": sum(1 for table in schema_info["tables"].values() if not table["foreign_keys"])
            },
            "performance": {
                "largest_table": max(schema_info["tables"].items(), key=lambda x: x[1]["size_mb"])[0] if schema_info["tables"] else None,
                "smallest_table": min(schema_info["tables"].items(), key=lambda x: x[1]["size_mb"])[0] if schema_info["tables"] else None,
                "most_rows": max(schema_info["tables"].items(), key=lambda x: x[1]["row_count"])[0] if schema_info["tables"] else None,
                "least_rows": min(schema_info["tables"].items(), key=lambda x: x[1]["row_count"])[0] if schema_info["tables"] else None
            }
        }
        
        return stats
