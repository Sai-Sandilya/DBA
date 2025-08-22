#!/usr/bin/env python3
"""
Pattern Detection - AI-powered data quality and anomaly detection
"""

import asyncio
import re
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

class PatternDetector:
    """AI-powered pattern detection for data quality and anomalies"""
    
    def __init__(self, db_connector):
        self.db_connector = db_connector
        
        # Data quality patterns
        self.quality_patterns = {
            "null_values": {
                "severity": "medium",
                "description": "High percentage of NULL values in columns",
                "threshold": 0.3  # 30% null values
            },
            "duplicates": {
                "severity": "high",
                "description": "Duplicate records found",
                "threshold": 0.1  # 10% duplicates
            },
            "outliers": {
                "severity": "medium",
                "description": "Statistical outliers detected",
                "threshold": 3.0  # 3 standard deviations
            },
            "data_type_mismatch": {
                "severity": "high",
                "description": "Data type inconsistencies",
                "threshold": 0.05  # 5% mismatches
            },
            "missing_indexes": {
                "severity": "medium",
                "description": "Missing indexes on frequently queried columns",
                "threshold": 0.8  # 80% of queries could benefit
            },
            "constraint_violations": {
                "severity": "critical",
                "description": "Constraint violations detected",
                "threshold": 0.0  # Any violation is critical
            }
        }
        
        # Anomaly detection patterns
        self.anomaly_patterns = {
            "sudden_spikes": {
                "description": "Sudden increase in data volume or values",
                "window": 7  # 7 days
            },
            "data_drift": {
                "description": "Statistical distribution changes over time",
                "window": 30  # 30 days
            },
            "unusual_patterns": {
                "description": "Unusual patterns in data",
                "window": 1  # 1 day
            }
        }
    
    async def detect_all_patterns(self, db_config: Dict) -> Dict[str, Any]:
        """
        Comprehensive pattern detection across the entire database
        """
        try:
            # Get database schema
            schema_info = await self._get_database_schema(db_config)
            
            if "error" in schema_info:
                return {"error": f"Failed to get schema: {schema_info['error']}"}
            
            # Run all detection methods
            results = {
                "timestamp": datetime.now(),
                "database": getattr(db_config, "database", "unknown"),
                "data_quality_issues": [],
                "schema_problems": [],
                "performance_issues": [],
                "anomalies": [],
                "recommendations": [],
                "summary": {}
            }
            
            # 1. Data Quality Detection
            quality_issues = await self._detect_data_quality_issues(schema_info, db_config)
            results["data_quality_issues"] = quality_issues
            
            # 2. Schema Analysis
            schema_problems = await self._detect_schema_problems(schema_info, db_config)
            results["schema_problems"] = schema_problems
            
            # 3. Performance Analysis
            performance_issues = await self._detect_performance_issues(schema_info, db_config)
            results["performance_issues"] = performance_issues
            
            # 4. Anomaly Detection
            anomalies = await self._detect_anomalies(schema_info, db_config)
            results["anomalies"] = anomalies
            
            # 5. Generate Recommendations
            recommendations = self._generate_recommendations(results)
            results["recommendations"] = recommendations
            
            # 6. Create Summary
            results["summary"] = self._create_summary(results)
            
            return results
            
        except Exception as e:
            return {"error": f"Pattern detection failed: {str(e)}"}
    
    async def _detect_data_quality_issues(self, schema_info: Dict, db_config: Dict) -> List[Dict]:
        """Detect data quality issues"""
        issues = []
        connection = await self.db_connector.get_connection(db_config)
        
        for table_name, table_info in schema_info["tables"].items():
            # Check for null values
            null_issues = await self._check_null_values(connection, table_name, table_info)
            issues.extend(null_issues)
            
            # Check for duplicates
            duplicate_issues = await self._check_duplicates(connection, table_name, table_info)
            issues.extend(duplicate_issues)
            
            # Check for outliers
            outlier_issues = await self._check_outliers(connection, table_name, table_info)
            issues.extend(outlier_issues)
            
            # Check for data type mismatches
            type_issues = await self._check_data_type_mismatches(connection, table_name, table_info)
            issues.extend(type_issues)
        
        return issues
    
    async def _check_null_values(self, connection, table_name: str, table_info: Dict) -> List[Dict]:
        """Check for high percentage of NULL values"""
        issues = []
        
        for column_name in table_info["columns"]:
            try:
                # Count total rows and null rows
                total_query = f"SELECT COUNT(*) FROM {table_name}"
                null_query = f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL"
                
                total_result = await connection.execute_query(total_query)
                null_result = await connection.execute_query(null_query)
                
                if total_result and null_result:
                    total_count = total_result[0][0]
                    null_count = null_result[0][0]
                    
                    if total_count > 0:
                        null_percentage = null_count / total_count
                        
                        if null_percentage > self.quality_patterns["null_values"]["threshold"]:
                            issues.append({
                                "type": "null_values",
                                "table": table_name,
                                "column": column_name,
                                "severity": self.quality_patterns["null_values"]["severity"],
                                "description": f"High percentage of NULL values ({null_percentage:.1%}) in {column_name}",
                                "details": {
                                    "total_rows": total_count,
                                    "null_rows": null_count,
                                    "null_percentage": null_percentage
                                },
                                "recommendation": "Consider adding NOT NULL constraint or data validation"
                            })
            except Exception as e:
                # Skip columns that can't be analyzed
                continue
        
        return issues
    
    async def _check_duplicates(self, connection, table_name: str, table_info: Dict) -> List[Dict]:
        """Check for duplicate records"""
        issues = []
        
        try:
            # Find potential duplicate columns (non-primary keys)
            potential_dup_columns = []
            for column_name in table_info["columns"]:
                if not column_name.lower().endswith('id') and column_name.lower() != 'id':
                    potential_dup_columns.append(column_name)
            
            if potential_dup_columns:
                # Check for duplicates in each potential column
                for column_name in potential_dup_columns[:3]:  # Limit to first 3 columns
                    try:
                        total_query = f"SELECT COUNT(*) FROM {table_name}"
                        distinct_query = f"SELECT COUNT(DISTINCT {column_name}) FROM {table_name}"
                        
                        total_result = await connection.execute_query(total_query)
                        distinct_result = await connection.execute_query(distinct_query)
                        
                        if total_result and distinct_result:
                            total_count = total_result[0][0]
                            distinct_count = distinct_result[0][0]
                            
                            if total_count > 0:
                                duplicate_percentage = (total_count - distinct_count) / total_count
                                
                                if duplicate_percentage > self.quality_patterns["duplicates"]["threshold"]:
                                    issues.append({
                                        "type": "duplicates",
                                        "table": table_name,
                                        "column": column_name,
                                        "severity": self.quality_patterns["duplicates"]["severity"],
                                        "description": f"High percentage of duplicates ({duplicate_percentage:.1%}) in {column_name}",
                                        "details": {
                                            "total_rows": total_count,
                                            "distinct_values": distinct_count,
                                            "duplicate_percentage": duplicate_percentage
                                        },
                                        "recommendation": "Consider adding UNIQUE constraint or data deduplication"
                                    })
                    except Exception as e:
                        continue
        except Exception as e:
            pass
        
        return issues
    
    async def _check_outliers(self, connection, table_name: str, table_info: Dict) -> List[Dict]:
        """Check for statistical outliers in numeric columns"""
        issues = []
        
        # Find numeric columns
        numeric_columns = []
        for column_name, column_type in table_info.get("column_types", {}).items():
            if any(num_type in column_type.lower() for num_type in ["int", "decimal", "float", "double"]):
                numeric_columns.append(column_name)
        
        for column_name in numeric_columns:
            try:
                # Get sample of values for outlier detection
                sample_query = f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 1000"
                sample_result = await connection.execute_query(sample_query)
                
                if sample_result and len(sample_result) > 10:
                    values = [row[0] for row in sample_result if row[0] is not None]
                    
                    if len(values) > 10:
                        mean_val = statistics.mean(values)
                        std_val = statistics.stdev(values)
                        
                        if std_val > 0:
                            # Find outliers (beyond 3 standard deviations)
                            outliers = [v for v in values if abs(v - mean_val) > self.quality_patterns["outliers"]["threshold"] * std_val]
                            
                            if outliers:
                                outlier_percentage = len(outliers) / len(values)
                                
                                issues.append({
                                    "type": "outliers",
                                    "table": table_name,
                                    "column": column_name,
                                    "severity": self.quality_patterns["outliers"]["severity"],
                                    "description": f"Statistical outliers detected in {column_name}",
                                    "details": {
                                        "sample_size": len(values),
                                        "outlier_count": len(outliers),
                                        "outlier_percentage": outlier_percentage,
                                        "mean": mean_val,
                                        "std_dev": std_val,
                                        "outlier_values": outliers[:5]  # Show first 5 outliers
                                    },
                                    "recommendation": "Review outlier values for data quality issues"
                                })
            except Exception as e:
                continue
        
        return issues
    
    async def _check_data_type_mismatches(self, connection, table_name: str, table_info: Dict) -> List[Dict]:
        """Check for data type inconsistencies"""
        issues = []
        
        # This is a simplified check - in a real implementation, you'd do more sophisticated analysis
        for column_name, column_type in table_info.get("column_types", {}).items():
            try:
                # Check if string columns contain numeric data
                if "varchar" in column_type.lower() or "text" in column_type.lower():
                    # Sample some values to check for numeric patterns
                    sample_query = f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 100"
                    sample_result = await connection.execute_query(sample_query)
                    
                    if sample_result:
                        numeric_count = 0
                        total_count = len(sample_result)
                        
                        for row in sample_result:
                            value = row[0]
                            if value and str(value).replace('.', '').replace('-', '').isdigit():
                                numeric_count += 1
                        
                        if total_count > 0:
                            numeric_percentage = numeric_count / total_count
                            
                            if numeric_percentage > self.quality_patterns["data_type_mismatch"]["threshold"]:
                                issues.append({
                                    "type": "data_type_mismatch",
                                    "table": table_name,
                                    "column": column_name,
                                    "severity": self.quality_patterns["data_type_mismatch"]["severity"],
                                    "description": f"String column {column_name} contains mostly numeric data",
                                    "details": {
                                        "column_type": column_type,
                                        "numeric_percentage": numeric_percentage,
                                        "sample_size": total_count
                                    },
                                    "recommendation": "Consider changing column type to numeric"
                                })
            except Exception as e:
                continue
        
        return issues
    
    async def _detect_schema_problems(self, schema_info: Dict, db_config: Dict) -> List[Dict]:
        """Detect schema-related problems"""
        issues = []
        connection = await self.db_connector.get_connection(db_config)
        
        for table_name, table_info in schema_info["tables"].items():
            # Check for missing primary keys
            pk_issues = await self._check_missing_primary_keys(connection, table_name, table_info)
            issues.extend(pk_issues)
            
            # Check for missing indexes
            index_issues = await self._check_missing_indexes(connection, table_name, table_info)
            issues.extend(index_issues)
            
            # Check for missing foreign keys
            fk_issues = await self._check_missing_foreign_keys(connection, table_name, table_info)
            issues.extend(fk_issues)
        
        return issues
    
    async def _check_missing_primary_keys(self, connection, table_name: str, table_info: Dict) -> List[Dict]:
        """Check for missing primary keys"""
        issues = []
        
        try:
            # Check if table has primary key
            pk_query = f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_NAME = '{table_name}' 
                AND CONSTRAINT_NAME = 'PRIMARY'
            """
            pk_result = await connection.execute_query(pk_query)
            
            if pk_result and pk_result[0][0] == 0:
                issues.append({
                    "type": "missing_primary_key",
                    "table": table_name,
                    "severity": "high",
                    "description": f"Table {table_name} has no primary key",
                    "details": {
                        "table_name": table_name,
                        "columns": table_info["columns"]
                    },
                    "recommendation": "Add a primary key constraint to ensure data integrity"
                })
        except Exception as e:
            pass
        
        return issues
    
    async def _check_missing_indexes(self, connection, table_name: str, table_info: Dict) -> List[Dict]:
        """Check for missing indexes on frequently queried columns"""
        issues = []
        
        try:
            # Get existing indexes
            index_query = f"SHOW INDEX FROM {table_name}"
            index_result = await connection.execute_query(index_query)
            
            existing_indexes = set()
            if index_result:
                for row in index_result:
                    existing_indexes.add(row[4])  # Column name
            
            # Check for missing indexes on common query columns
            common_query_columns = ["id", "user_id", "customer_id", "order_id", "created_at", "updated_at"]
            
            for column_name in common_query_columns:
                if column_name in table_info["columns"] and column_name not in existing_indexes:
                    issues.append({
                        "type": "missing_index",
                        "table": table_name,
                        "column": column_name,
                        "severity": "medium",
                        "description": f"Missing index on frequently queried column {column_name}",
                        "details": {
                            "table_name": table_name,
                            "column_name": column_name,
                            "existing_indexes": list(existing_indexes)
                        },
                        "recommendation": f"Add index on {column_name} for better query performance"
                    })
        except Exception as e:
            pass
        
        return issues
    
    async def _check_missing_foreign_keys(self, connection, table_name: str, table_info: Dict) -> List[Dict]:
        """Check for missing foreign key constraints"""
        issues = []
        
        # Look for columns that might be foreign keys
        potential_fk_columns = []
        for column_name in table_info["columns"]:
            if column_name.lower().endswith('_id') and column_name.lower() != 'id':
                potential_fk_columns.append(column_name)
        
        for column_name in potential_fk_columns:
            try:
                # Check if foreign key constraint exists
                fk_query = f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_NAME = '{table_name}' 
                    AND COLUMN_NAME = '{column_name}'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """
                fk_result = await connection.execute_query(fk_query)
                
                if fk_result and fk_result[0][0] == 0:
                    issues.append({
                        "type": "missing_foreign_key",
                        "table": table_name,
                        "column": column_name,
                        "severity": "medium",
                        "description": f"Missing foreign key constraint on {column_name}",
                        "details": {
                            "table_name": table_name,
                            "column_name": column_name
                        },
                        "recommendation": f"Add foreign key constraint on {column_name} for referential integrity"
                    })
            except Exception as e:
                continue
        
        return issues
    
    async def _detect_performance_issues(self, schema_info: Dict, db_config: Dict) -> List[Dict]:
        """Detect performance-related issues"""
        issues = []
        connection = await self.db_connector.get_connection(db_config)
        
        # Check for large tables without partitioning
        size_issues = await self._check_table_sizes(connection, schema_info)
        issues.extend(size_issues)
        
        # Check for missing constraints
        constraint_issues = await self._check_missing_constraints(connection, schema_info)
        issues.extend(constraint_issues)
        
        return issues
    
    async def _check_table_sizes(self, connection, schema_info: Dict) -> List[Dict]:
        """Check for large tables that might need partitioning"""
        issues = []
        
        for table_name in schema_info["tables"].keys():
            try:
                # Get table size
                size_query = f"""
                    SELECT 
                        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size_MB'
                    FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                """
                size_result = await connection.execute_query(size_query)
                
                if size_result and size_result[0][0]:
                    size_mb = size_result[0][0]
                    
                    if size_mb > 100:  # Tables larger than 100MB
                        issues.append({
                            "type": "large_table",
                            "table": table_name,
                            "severity": "medium",
                            "description": f"Large table {table_name} ({size_mb} MB)",
                            "details": {
                                "table_name": table_name,
                                "size_mb": size_mb
                            },
                            "recommendation": "Consider partitioning for better performance"
                        })
            except Exception as e:
                continue
        
        return issues
    
    async def _check_missing_constraints(self, connection, schema_info: Dict) -> List[Dict]:
        """Check for missing important constraints"""
        issues = []
        
        for table_name, table_info in schema_info["tables"].items():
            # Check for missing NOT NULL constraints on important columns
            important_columns = ["id", "created_at", "updated_at", "status"]
            
            for column_name in important_columns:
                if column_name in table_info["columns"]:
                    try:
                        # Check if column allows NULL
                        null_query = f"""
                            SELECT IS_NULLABLE 
                            FROM INFORMATION_SCHEMA.COLUMNS 
                            WHERE TABLE_NAME = '{table_name}' 
                            AND COLUMN_NAME = '{column_name}'
                        """
                        null_result = await connection.execute_query(null_query)
                        
                        if null_result and null_result[0][0] == 'YES':
                            issues.append({
                                "type": "missing_not_null",
                                "table": table_name,
                                "column": column_name,
                                "severity": "medium",
                                "description": f"Missing NOT NULL constraint on {column_name}",
                                "details": {
                                    "table_name": table_name,
                                    "column_name": column_name
                                },
                                "recommendation": f"Add NOT NULL constraint to {column_name}"
                            })
                    except Exception as e:
                        continue
        
        return issues
    
    async def _detect_anomalies(self, schema_info: Dict, db_config: Dict) -> List[Dict]:
        """Detect anomalies in data patterns"""
        issues = []
        connection = await self.db_connector.get_connection(db_config)
        
        # Check for unusual data patterns
        pattern_issues = await self._check_unusual_patterns(connection, schema_info)
        issues.extend(pattern_issues)
        
        return issues
    
    async def _check_unusual_patterns(self, connection, schema_info: Dict) -> List[Dict]:
        """Check for unusual patterns in data"""
        issues = []
        
        for table_name, table_info in schema_info["tables"].items():
            # Check for unusual value distributions
            for column_name in table_info["columns"][:5]:  # Check first 5 columns
                try:
                    # Get value distribution
                    dist_query = f"""
                        SELECT {column_name}, COUNT(*) as count 
                        FROM {table_name} 
                        WHERE {column_name} IS NOT NULL 
                        GROUP BY {column_name} 
                        ORDER BY count DESC 
                        LIMIT 10
                    """
                    dist_result = await connection.execute_query(dist_query)
                    
                    if dist_result and len(dist_result) > 1:
                        counts = [row[1] for row in dist_result]
                        total = sum(counts)
                        
                        # Check for highly skewed distributions
                        if len(counts) > 1:
                            max_count = max(counts)
                            skew_ratio = max_count / total
                            
                            if skew_ratio > 0.8:  # 80% of values are the same
                                issues.append({
                                    "type": "skewed_distribution",
                                    "table": table_name,
                                    "column": column_name,
                                    "severity": "low",
                                    "description": f"Highly skewed distribution in {column_name}",
                                    "details": {
                                        "table_name": table_name,
                                        "column_name": column_name,
                                        "skew_ratio": skew_ratio,
                                        "top_value": dist_result[0][0],
                                        "top_count": dist_result[0][1]
                                    },
                                    "recommendation": "Review data distribution for potential issues"
                                })
                except Exception as e:
                    continue
        
        return issues
    
    def _generate_recommendations(self, results: Dict) -> List[Dict]:
        """Generate actionable recommendations based on findings"""
        recommendations = []
        
        # Group issues by severity
        critical_issues = []
        high_issues = []
        medium_issues = []
        low_issues = []
        
        for issue_type in ["data_quality_issues", "schema_problems", "performance_issues", "anomalies"]:
            for issue in results.get(issue_type, []):
                severity = issue.get("severity", "medium")
                if severity == "critical":
                    critical_issues.append(issue)
                elif severity == "high":
                    high_issues.append(issue)
                elif severity == "medium":
                    medium_issues.append(issue)
                else:
                    low_issues.append(issue)
        
        # Generate prioritized recommendations
        if critical_issues:
            recommendations.append({
                "priority": "critical",
                "title": "🚨 Critical Issues Require Immediate Attention",
                "description": f"Found {len(critical_issues)} critical issues that need immediate resolution",
                "actions": [issue.get("recommendation", "") for issue in critical_issues[:3]]
            })
        
        if high_issues:
            recommendations.append({
                "priority": "high",
                "title": "⚠️ High Priority Issues",
                "description": f"Found {len(high_issues)} high priority issues",
                "actions": [issue.get("recommendation", "") for issue in high_issues[:3]]
            })
        
        if medium_issues:
            recommendations.append({
                "priority": "medium",
                "title": "📊 Medium Priority Improvements",
                "description": f"Found {len(medium_issues)} medium priority issues",
                "actions": [issue.get("recommendation", "") for issue in medium_issues[:3]]
            })
        
        # Add general recommendations
        recommendations.append({
            "priority": "general",
            "title": "💡 General Database Health Tips",
            "description": "Best practices for maintaining database health",
            "actions": [
                "Regularly monitor query performance",
                "Set up automated backups",
                "Review and update indexes periodically",
                "Monitor disk space usage",
                "Set up alerts for critical issues"
            ]
        })
        
        return recommendations
    
    def _create_summary(self, results: Dict) -> Dict:
        """Create a summary of all findings"""
        total_issues = 0
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for issue_type in ["data_quality_issues", "schema_problems", "performance_issues", "anomalies"]:
            for issue in results.get(issue_type, []):
                total_issues += 1
                severity = issue.get("severity", "medium")
                severity_counts[severity] += 1
        
        return {
            "total_issues": total_issues,
            "severity_breakdown": severity_counts,
            "health_score": self._calculate_health_score(severity_counts),
            "scan_timestamp": results["timestamp"],
            "database_name": results["database"]
        }
    
    def _calculate_health_score(self, severity_counts: Dict) -> int:
        """Calculate overall database health score (0-100)"""
        total_issues = sum(severity_counts.values())
        
        if total_issues == 0:
            return 100
        
        # Weight issues by severity
        weighted_score = (
            severity_counts["critical"] * 10 +
            severity_counts["high"] * 5 +
            severity_counts["medium"] * 2 +
            severity_counts["low"] * 1
        )
        
        # Convert to 0-100 scale
        max_possible_score = total_issues * 10
        health_score = max(0, 100 - (weighted_score / max_possible_score) * 100)
        
        return int(health_score)
    
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
                
                schema_info["tables"][table_name] = {
                    "columns": [col[0] for col in structure_result],
                    "column_types": {col[0]: col[1] for col in structure_result},
                    "row_count": 0
                }
            
            return schema_info
            
        except Exception as e:
            return {"error": f"Failed to get schema: {str(e)}"}
