#!/usr/bin/env python3
"""
NoSQL Assistant - AI-powered tools for non-relational databases
Supports MongoDB, Cassandra, Redis, Elasticsearch, Neo4j, and InfluxDB
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

class NoSQLAssistant:
    """AI-powered assistant for NoSQL database operations"""
    
    def __init__(self, db_connector):
        self.db_connector = db_connector
        
        # NoSQL-specific patterns and templates
        self.nosql_patterns = {
            "mongodb": {
                "find": r"find\s+(?:all\s+)?(\w+)(?:\s+where\s+(.+))?",
                "aggregate": r"(?:count|sum|average|max|min)\s+(\w+)",
                "insert": r"insert\s+(?:into\s+)?(\w+)",
                "update": r"update\s+(\w+)\s+set\s+(.+)",
                "delete": r"delete\s+(?:from\s+)?(\w+)"
            },
            "redis": {
                "get": r"get\s+(\w+)",
                "set": r"set\s+(\w+)\s+(.+)",
                "keys": r"find\s+keys\s+(?:matching\s+)?(.+)",
                "info": r"(?:show|get)\s+(?:redis\s+)?info"
            },
            "elasticsearch": {
                "search": r"search\s+(?:in\s+)?(\w+)(?:\s+for\s+(.+))?",
                "index": r"index\s+(?:in\s+)?(\w+)",
                "analyze": r"analyze\s+(?:index\s+)?(\w+)"
            },
            "neo4j": {
                "nodes": r"find\s+(?:all\s+)?(\w+)\s+nodes",
                "relationships": r"find\s+relationships\s+(?:between\s+)?(.+)",
                "path": r"find\s+path\s+(?:from\s+)?(.+)\s+to\s+(.+)",
                "create": r"create\s+(?:node|relationship)\s+(.+)"
            },
            "cassandra": {
                "select": r"select\s+(?:from\s+)?(\w+)(?:\s+where\s+(.+))?",
                "insert": r"insert\s+(?:into\s+)?(\w+)",
                "update": r"update\s+(\w+)\s+set\s+(.+)",
                "keyspace": r"(?:show|list)\s+keyspaces?"
            },
            "influxdb": {
                "query": r"query\s+(?:from\s+)?(\w+)(?:\s+where\s+(.+))?",
                "measurement": r"(?:show|list)\s+measurements?",
                "bucket": r"(?:show|list)\s+buckets?"
            }
        }
        
        # Query templates for different NoSQL databases
        self.query_templates = {
            "mongodb": {
                "find_all": 'db.{collection}.find()',
                "find_filtered": 'db.{collection}.find({{{filter}}})',
                "aggregate": 'db.{collection}.aggregate([{{"$group": {{"_id": null, "result": {{"${function}": "${field}"}}}}}}])',
                "count": 'db.{collection}.countDocuments({{{filter}}})'
            },
            "redis": {
                "get": 'GET {key}',
                "set": 'SET {key} {value}',
                "keys": 'KEYS {pattern}',
                "info": 'INFO {section}'
            },
            "elasticsearch": {
                "search": '{{"query": {{"match": {{"{field}": "{value}"}}}}}}',
                "aggregate": '{{"aggs": {{"result": {{"{function}": {{"field": "{field}"}}}}}}}}',
                "index_stats": '{{"size": 0, "aggs": {{"doc_count": {{"value_count": {{"field": "_id"}}}}}}}}'
            },
            "neo4j": {
                "find_nodes": 'MATCH (n:{label}) RETURN n LIMIT {limit}',
                "find_relationships": 'MATCH (a)-[r:{type}]->(b) RETURN a, r, b LIMIT {limit}',
                "shortest_path": 'MATCH path = shortestPath((a:{label1})-[*]-(b:{label2})) RETURN path',
                "count_nodes": 'MATCH (n:{label}) RETURN count(n) as count'
            },
            "cassandra": {
                "select": 'SELECT * FROM {keyspace}.{table}',
                "select_filtered": 'SELECT * FROM {keyspace}.{table} WHERE {condition}',
                "count": 'SELECT COUNT(*) FROM {keyspace}.{table}',
                "keyspaces": 'SELECT keyspace_name FROM system_schema.keyspaces'
            },
            "influxdb": {
                "query": 'from(bucket: "{bucket}") |> range(start: -1h) |> filter(fn: (r) => r["_measurement"] == "{measurement}")',
                "aggregate": 'from(bucket: "{bucket}") |> range(start: -1h) |> filter(fn: (r) => r["_measurement"] == "{measurement}") |> {function}()',
                "measurements": 'import "influxdata/influxdb/schema" schema.measurements(bucket: "{bucket}")'
            }
        }
    
    async def analyze_nosql_query(self, natural_query: str, db_type: str, db_config: Dict) -> Dict[str, Any]:
        """Analyze natural language query for NoSQL databases"""
        try:
            # Analyze based on database type
            if db_type == "mongodb":
                return await self._analyze_mongodb_query(natural_query, db_config)
            elif db_type == "redis":
                return await self._analyze_redis_query(natural_query, db_config)
            elif db_type == "elasticsearch":
                return await self._analyze_elasticsearch_query(natural_query, db_config)
            elif db_type == "neo4j":
                return await self._analyze_neo4j_query(natural_query, db_config)
            elif db_type == "cassandra":
                return await self._analyze_cassandra_query(natural_query, db_config)
            elif db_type == "influxdb":
                return await self._analyze_influxdb_query(natural_query, db_config)
            else:
                return {"error": f"Unsupported NoSQL database type: {db_type}"}
                
        except Exception as e:
            return {"error": f"Failed to analyze NoSQL query: {str(e)}"}
    
    async def _analyze_mongodb_query(self, query: str, db_config: Dict) -> Dict[str, Any]:
        """Analyze MongoDB natural language query"""
        analysis = {
            "intent": "unknown",
            "collection": None,
            "filter": {},
            "aggregation": None,
            "limit": 10
        }
        
        query_lower = query.lower()
        
        # Extract collection name
        for pattern in self.nosql_patterns["mongodb"]["find"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["intent"] = "find"
                analysis["collection"] = match.group(1)
                if match.group(2):
                    analysis["filter"] = self._parse_mongodb_filter(match.group(2))
                break
        
        # Check for aggregations
        for pattern in self.nosql_patterns["mongodb"]["aggregate"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["intent"] = "aggregate"
                analysis["aggregation"] = match.group(1)
                break
        
        # Generate MongoDB query
        if analysis["intent"] == "find":
            if analysis["filter"]:
                query_template = self.query_templates["mongodb"]["find_filtered"]
                mongo_query = query_template.format(
                    collection=analysis["collection"],
                    filter=json.dumps(analysis["filter"])
                )
            else:
                query_template = self.query_templates["mongodb"]["find_all"]
                mongo_query = query_template.format(collection=analysis["collection"])
        elif analysis["intent"] == "aggregate":
            query_template = self.query_templates["mongodb"]["aggregate"]
            mongo_query = query_template.format(
                collection=analysis["collection"],
                function=analysis["aggregation"],
                field="_id"
            )
        else:
            mongo_query = f"db.{analysis.get('collection', 'collection')}.find()"
        
        return {
            "analysis": analysis,
            "query": mongo_query,
            "explanation": self._explain_mongodb_query(analysis),
            "suggestions": self._get_mongodb_suggestions(analysis)
        }
    
    async def _analyze_redis_query(self, query: str, db_config: Dict) -> Dict[str, Any]:
        """Analyze Redis natural language query"""
        analysis = {
            "intent": "unknown",
            "key": None,
            "value": None,
            "pattern": "*"
        }
        
        query_lower = query.lower()
        
        # Extract Redis operations
        for pattern in self.nosql_patterns["redis"]["get"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["intent"] = "get"
                analysis["key"] = match.group(1)
                break
        
        for pattern in self.nosql_patterns["redis"]["set"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["intent"] = "set"
                analysis["key"] = match.group(1)
                analysis["value"] = match.group(2)
                break
        
        for pattern in self.nosql_patterns["redis"]["keys"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["intent"] = "keys"
                analysis["pattern"] = match.group(1)
                break
        
        # Generate Redis command
        if analysis["intent"] == "get":
            redis_command = self.query_templates["redis"]["get"].format(key=analysis["key"])
        elif analysis["intent"] == "set":
            redis_command = self.query_templates["redis"]["set"].format(
                key=analysis["key"], 
                value=analysis["value"]
            )
        elif analysis["intent"] == "keys":
            redis_command = self.query_templates["redis"]["keys"].format(pattern=analysis["pattern"])
        else:
            redis_command = "INFO default"
        
        return {
            "analysis": analysis,
            "command": redis_command,
            "explanation": self._explain_redis_command(analysis),
            "suggestions": self._get_redis_suggestions(analysis)
        }
    
    async def _analyze_elasticsearch_query(self, query: str, db_config: Dict) -> Dict[str, Any]:
        """Analyze Elasticsearch natural language query"""
        analysis = {
            "intent": "search",
            "index": None,
            "field": None,
            "value": None,
            "aggregation": None
        }
        
        query_lower = query.lower()
        
        # Extract search parameters
        for pattern in self.nosql_patterns["elasticsearch"]["search"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["index"] = match.group(1)
                if match.group(2):
                    # Parse search terms
                    search_terms = match.group(2).split()
                    if len(search_terms) >= 2:
                        analysis["field"] = search_terms[0]
                        analysis["value"] = " ".join(search_terms[1:])
                break
        
        # Generate Elasticsearch query
        if analysis["field"] and analysis["value"]:
            es_query = self.query_templates["elasticsearch"]["search"].format(
                field=analysis["field"],
                value=analysis["value"]
            )
        else:
            es_query = '{"query": {"match_all": {}}}'
        
        return {
            "analysis": analysis,
            "query": es_query,
            "explanation": self._explain_elasticsearch_query(analysis),
            "suggestions": self._get_elasticsearch_suggestions(analysis)
        }
    
    async def _analyze_neo4j_query(self, query: str, db_config: Dict) -> Dict[str, Any]:
        """Analyze Neo4j natural language query"""
        analysis = {
            "intent": "find_nodes",
            "label": None,
            "relationship_type": None,
            "start_node": None,
            "end_node": None
        }
        
        query_lower = query.lower()
        
        # Extract node operations
        for pattern in self.nosql_patterns["neo4j"]["nodes"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["intent"] = "find_nodes"
                analysis["label"] = match.group(1)
                break
        
        # Extract path operations
        for pattern in self.nosql_patterns["neo4j"]["path"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["intent"] = "shortest_path"
                analysis["start_node"] = match.group(1)
                analysis["end_node"] = match.group(2)
                break
        
        # Generate Cypher query
        if analysis["intent"] == "find_nodes" and analysis["label"]:
            cypher_query = self.query_templates["neo4j"]["find_nodes"].format(
                label=analysis["label"],
                limit=10
            )
        elif analysis["intent"] == "shortest_path":
            cypher_query = self.query_templates["neo4j"]["shortest_path"].format(
                label1=analysis["start_node"],
                label2=analysis["end_node"]
            )
        else:
            cypher_query = "MATCH (n) RETURN n LIMIT 10"
        
        return {
            "analysis": analysis,
            "query": cypher_query,
            "explanation": self._explain_neo4j_query(analysis),
            "suggestions": self._get_neo4j_suggestions(analysis)
        }
    
    async def _analyze_cassandra_query(self, query: str, db_config: Dict) -> Dict[str, Any]:
        """Analyze Cassandra natural language query"""
        analysis = {
            "intent": "select",
            "keyspace": None,
            "table": None,
            "condition": None
        }
        
        query_lower = query.lower()
        
        # Extract table operations
        for pattern in self.nosql_patterns["cassandra"]["select"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["table"] = match.group(1)
                if match.group(2):
                    analysis["condition"] = match.group(2)
                break
        
        # Generate CQL query
        if analysis["condition"]:
            cql_query = self.query_templates["cassandra"]["select_filtered"].format(
                keyspace=analysis.get("keyspace", "keyspace"),
                table=analysis["table"],
                condition=analysis["condition"]
            )
        else:
            cql_query = self.query_templates["cassandra"]["select"].format(
                keyspace=analysis.get("keyspace", "keyspace"),
                table=analysis["table"]
            )
        
        return {
            "analysis": analysis,
            "query": cql_query,
            "explanation": self._explain_cassandra_query(analysis),
            "suggestions": self._get_cassandra_suggestions(analysis)
        }
    
    async def _analyze_influxdb_query(self, query: str, db_config: Dict) -> Dict[str, Any]:
        """Analyze InfluxDB natural language query"""
        analysis = {
            "intent": "query",
            "bucket": None,
            "measurement": None,
            "time_range": "-1h",
            "aggregation": None
        }
        
        query_lower = query.lower()
        
        # Extract query parameters
        for pattern in self.nosql_patterns["influxdb"]["query"]:
            match = re.search(pattern, query_lower)
            if match:
                analysis["measurement"] = match.group(1)
                if match.group(2):
                    analysis["condition"] = match.group(2)
                break
        
        # Generate Flux query
        if analysis["measurement"]:
            flux_query = self.query_templates["influxdb"]["query"].format(
                bucket=analysis.get("bucket", "bucket"),
                measurement=analysis["measurement"]
            )
        else:
            flux_query = 'from(bucket: "bucket") |> range(start: -1h)'
        
        return {
            "analysis": analysis,
            "query": flux_query,
            "explanation": self._explain_influxdb_query(analysis),
            "suggestions": self._get_influxdb_suggestions(analysis)
        }
    
    def _parse_mongodb_filter(self, filter_text: str) -> Dict[str, Any]:
        """Parse natural language filter into MongoDB filter object"""
        filter_obj = {}
        
        # Simple parsing for common patterns
        if "greater than" in filter_text or ">" in filter_text:
            # Extract field and value
            parts = filter_text.split()
            for i, part in enumerate(parts):
                if part in ["greater", "than", ">"]:
                    if i > 0 and i < len(parts) - 1:
                        field = parts[i-1]
                        value = parts[i+1]
                        filter_obj[field] = {"$gt": self._parse_value(value)}
                        break
        
        return filter_obj
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse string value to appropriate type"""
        try:
            if value_str.isdigit():
                return int(value_str)
            elif value_str.replace(".", "").isdigit():
                return float(value_str)
            elif value_str.lower() in ["true", "false"]:
                return value_str.lower() == "true"
            else:
                return value_str
        except:
            return value_str
    
    def _explain_mongodb_query(self, analysis: Dict) -> str:
        """Explain MongoDB query in natural language"""
        explanation = f"This MongoDB query "
        
        if analysis["intent"] == "find":
            explanation += f"finds documents in the '{analysis['collection']}' collection"
            if analysis["filter"]:
                explanation += f" that match the specified filters"
        elif analysis["intent"] == "aggregate":
            explanation += f"performs a {analysis['aggregation']} aggregation on the '{analysis['collection']}' collection"
        
        explanation += f" and returns up to {analysis['limit']} results."
        return explanation
    
    def _explain_redis_command(self, analysis: Dict) -> str:
        """Explain Redis command in natural language"""
        explanation = f"This Redis command "
        
        if analysis["intent"] == "get":
            explanation += f"retrieves the value stored at key '{analysis['key']}'"
        elif analysis["intent"] == "set":
            explanation += f"sets the key '{analysis['key']}' to value '{analysis['value']}'"
        elif analysis["intent"] == "keys":
            explanation += f"finds all keys matching pattern '{analysis['pattern']}'"
        
        return explanation
    
    def _explain_elasticsearch_query(self, analysis: Dict) -> str:
        """Explain Elasticsearch query in natural language"""
        explanation = f"This Elasticsearch query "
        
        if analysis["index"]:
            explanation += f"searches in the '{analysis['index']}' index"
            if analysis["field"] and analysis["value"]:
                explanation += f" for documents where '{analysis['field']}' matches '{analysis['value']}'"
        
        return explanation
    
    def _explain_neo4j_query(self, analysis: Dict) -> str:
        """Explain Neo4j query in natural language"""
        explanation = f"This Cypher query "
        
        if analysis["intent"] == "find_nodes":
            explanation += f"finds all nodes with label '{analysis['label']}'"
        elif analysis["intent"] == "shortest_path":
            explanation += f"finds the shortest path between '{analysis['start_node']}' and '{analysis['end_node']}' nodes"
        
        return explanation
    
    def _explain_cassandra_query(self, analysis: Dict) -> str:
        """Explain Cassandra query in natural language"""
        explanation = f"This CQL query "
        
        explanation += f"selects data from table '{analysis['table']}'"
        if analysis["condition"]:
            explanation += f" where {analysis['condition']}"
        
        return explanation
    
    def _explain_influxdb_query(self, analysis: Dict) -> str:
        """Explain InfluxDB query in natural language"""
        explanation = f"This Flux query "
        
        if analysis["measurement"]:
            explanation += f"queries data from measurement '{analysis['measurement']}'"
        explanation += f" for the last {analysis['time_range']}"
        
        return explanation
    
    def _get_mongodb_suggestions(self, analysis: Dict) -> List[str]:
        """Get suggestions for MongoDB queries"""
        suggestions = []
        
        if analysis["intent"] == "unknown":
            suggestions.append("💡 Try specifying a collection name (e.g., 'users', 'orders')")
        
        if analysis["intent"] == "find" and not analysis["filter"]:
            suggestions.append("💡 Consider adding filters to narrow down results")
        
        suggestions.append("💡 Use indexes on frequently queried fields for better performance")
        
        return suggestions
    
    def _get_redis_suggestions(self, analysis: Dict) -> List[str]:
        """Get suggestions for Redis commands"""
        suggestions = []
        
        if analysis["intent"] == "unknown":
            suggestions.append("💡 Try using specific Redis commands (GET, SET, KEYS, INFO)")
        
        suggestions.append("💡 Consider using Redis data structures (Lists, Sets, Hashes) for complex data")
        
        return suggestions
    
    def _get_elasticsearch_suggestions(self, analysis: Dict) -> List[str]:
        """Get suggestions for Elasticsearch queries"""
        suggestions = []
        
        if not analysis["index"]:
            suggestions.append("💡 Specify an index name for better search results")
        
        suggestions.append("💡 Use Elasticsearch aggregations for analytics")
        
        return suggestions
    
    def _get_neo4j_suggestions(self, analysis: Dict) -> List[str]:
        """Get suggestions for Neo4j queries"""
        suggestions = []
        
        if analysis["intent"] == "unknown":
            suggestions.append("💡 Try specifying node labels or relationship types")
        
        suggestions.append("💡 Use Cypher patterns for complex graph traversals")
        
        return suggestions
    
    def _get_cassandra_suggestions(self, analysis: Dict) -> List[str]:
        """Get suggestions for Cassandra queries"""
        suggestions = []
        
        if not analysis["table"]:
            suggestions.append("💡 Specify a table name for your query")
        
        suggestions.append("💡 Remember that Cassandra queries must include partition key in WHERE clause")
        
        return suggestions
    
    def _get_influxdb_suggestions(self, analysis: Dict) -> List[str]:
        """Get suggestions for InfluxDB queries"""
        suggestions = []
        
        if not analysis["measurement"]:
            suggestions.append("💡 Specify a measurement name for your query")
        
        suggestions.append("💡 Use Flux functions for data transformation and aggregation")
        
        return suggestions
