#!/usr/bin/env python3
"""
Cloud Database AI Assistant for DBA-GPT
Provides specialized AI assistance for AWS Athena and Azure SQL Database
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CloudDBAAssistant:
    """AI Assistant specialized for cloud databases"""
    
    def __init__(self):
        self.athena_tips = [
            "Use Parquet/ORC formats for better compression and query performance",
            "Partition data by frequently queried columns (e.g., date, region)",
            "Use S3 Select for large files to reduce data scanned",
            "Avoid SELECT * - only query needed columns",
            "Use workgroups to control costs and resource allocation",
            "Monitor query costs - Athena charges $5 per TB scanned"
        ]
        
        self.azure_sql_tips = [
            "Use Azure AD authentication for better security",
            "Enable Query Store for performance monitoring",
            "Use elastic pools for cost optimization",
            "Implement connection pooling for better performance",
            "Use Azure Advisor for optimization recommendations",
            "Monitor DTU/CPU usage for scaling decisions"
        ]
    
    async def get_athena_insights(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get AWS Athena specific insights and recommendations"""
        try:
            insights = {
                "database_type": "AWS Athena",
                "description": "Serverless interactive query service for analyzing data in S3",
                "key_features": [
                    "Pay-per-query pricing model",
                    "No infrastructure management",
                    "Direct S3 integration",
                    "Standard SQL support",
                    "Built-in security and compliance"
                ],
                "cost_optimization": {
                    "data_scanned_pricing": "$5 per TB scanned",
                    "optimization_strategies": [
                        "Use columnar formats (Parquet/ORC)",
                        "Implement data partitioning",
                        "Use S3 Select for large files",
                        "Avoid scanning unnecessary data"
                    ]
                },
                "performance_tips": self.athena_tips,
                "best_practices": [
                    "Organize data in S3 with logical folder structure",
                    "Use appropriate file formats and compression",
                    "Implement data lifecycle policies",
                    "Monitor query performance and costs",
                    "Use workgroups for resource management"
                ]
            }
            return insights
            
        except Exception as e:
            logger.error(f"Error getting Athena insights: {e}")
            return {"error": str(e)}
    
    async def get_azure_sql_insights(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get Azure SQL Database specific insights and recommendations"""
        try:
            insights = {
                "database_type": "Azure SQL Database",
                "description": "Fully managed SQL database service in the cloud",
                "key_features": [
                    "Built-in intelligence and security",
                    "Automatic tuning and optimization",
                    "High availability and disaster recovery",
                    "Scalable performance tiers",
                    "Azure AD integration"
                ],
                "performance_tiers": {
                    "DTU_based": "Database Transaction Units for predictable performance",
                    "vCore_based": "Virtual cores for more granular control",
                    "serverless": "Auto-scaling based on workload"
                },
                "optimization_tips": self.azure_sql_tips,
                "monitoring_recommendations": [
                    "Use Azure Monitor for performance metrics",
                    "Enable Query Performance Insight",
                    "Monitor connection pool usage",
                    "Track DTU/CPU consumption",
                    "Use Azure Advisor for recommendations"
                ],
                "security_features": [
                    "Always Encrypted for sensitive data",
                    "Row-level security",
                    "Dynamic data masking",
                    "Advanced threat protection",
                    "Azure AD authentication"
                ]
            }
            return insights
            
        except Exception as e:
            logger.error(f"Error getting Azure SQL insights: {e}")
            return {"error": str(e)}
    
    async def optimize_cloud_query(self, query: str, db_type: str) -> Dict[str, Any]:
        """Optimize queries for cloud databases"""
        try:
            if db_type == "athena":
                return await self._optimize_athena_query(query)
            elif db_type == "azure_sql":
                return await self._optimize_azure_sql_query(query)
            else:
                return {"error": f"Unsupported database type: {db_type}"}
                
        except Exception as e:
            logger.error(f"Error optimizing cloud query: {e}")
            return {"error": str(e)}
    
    async def _optimize_athena_query(self, query: str) -> Dict[str, Any]:
        """Optimize SQL for AWS Athena performance"""
        try:
            original_query = query
            optimized_query = query
            recommendations = []
            
            # Check for SELECT *
            if "SELECT *" in query.upper():
                recommendations.append("Replace SELECT * with specific columns to reduce data scanned")
                optimized_query = query.replace("SELECT *", "SELECT column1, column2, column3")
            
            # Check for missing WHERE clauses
            if "FROM" in query.upper() and "WHERE" not in query.upper():
                recommendations.append("Add WHERE clause with partition columns to limit data scanned")
                optimized_query += " WHERE partition_date >= '2024-01-01'"
            
            # Check for ORDER BY without LIMIT
            if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
                recommendations.append("Add LIMIT clause to ORDER BY queries to reduce processing")
                optimized_query += " LIMIT 1000"
            
            # Check for appropriate file formats
            if "CREATE TABLE" in query.upper() and "STORED AS" not in query.upper():
                recommendations.append("Specify STORED AS PARQUET for better compression and performance")
                optimized_query += " STORED AS PARQUET"
            
            # Cost estimation
            estimated_cost = await self._estimate_athena_cost(query)
            
            return {
                "original_query": original_query,
                "optimized_query": optimized_query,
                "recommendations": recommendations,
                "estimated_cost": estimated_cost,
                "performance_impact": "High" if recommendations else "Low"
            }
            
        except Exception as e:
            logger.error(f"Error optimizing Athena query: {e}")
            return {"error": str(e)}
    
    async def _optimize_azure_sql_query(self, query: str) -> Dict[str, Any]:
        """Optimize SQL for Azure SQL Database performance"""
        try:
            original_query = query
            optimized_query = query
            recommendations = []
            
            # Check for SELECT *
            if "SELECT *" in query.upper():
                recommendations.append("Replace SELECT * with specific columns for better performance")
                optimized_query = query.replace("SELECT *", "SELECT column1, column2, column3")
            
            # Check for missing indexes
            if "WHERE" in query.upper():
                recommendations.append("Ensure WHERE clause columns are properly indexed")
            
            # Check for ORDER BY optimization
            if "ORDER BY" in query.upper():
                recommendations.append("Consider adding covering indexes for ORDER BY columns")
            
            # Check for JOIN optimization
            if "JOIN" in query.upper():
                recommendations.append("Ensure JOIN columns are indexed and use appropriate JOIN types")
            
            # Check for parameter sniffing
            if "DECLARE" in query.upper() or "@" in query:
                recommendations.append("Use OPTION (RECOMPILE) for queries with local variables")
            
            return {
                "original_query": original_query,
                "optimized_query": optimized_query,
                "recommendations": recommendations,
                "performance_impact": "High" if recommendations else "Low"
            }
            
        except Exception as e:
            logger.error(f"Error optimizing Azure SQL query: {e}")
            return {"error": str(e)}
    
    async def _estimate_athena_cost(self, query: str) -> Dict[str, Any]:
        """Estimate AWS Athena query cost"""
        try:
            # Simple cost estimation based on query complexity
            base_cost = 0.0001  # Base cost per query
            
            # Estimate data scanned (very rough approximation)
            data_scanned_gb = 1.0  # Default assumption
            
            # Adjust based on query characteristics
            if "SELECT *" in query.upper():
                data_scanned_gb *= 2  # SELECT * scans more data
            
            if "JOIN" in query.upper():
                data_scanned_gb *= 1.5  # JOINs typically scan more data
            
            if "GROUP BY" in query.upper():
                data_scanned_gb *= 1.3  # Aggregations may scan more data
            
            # Calculate cost (Athena charges $5 per TB)
            cost_per_tb = 5.0
            estimated_cost = (data_scanned_gb / 1024) * cost_per_tb + base_cost
            
            return {
                "estimated_cost_usd": round(estimated_cost, 6),
                "data_scanned_gb": data_scanned_gb,
                "cost_per_tb": cost_per_tb,
                "base_cost_per_query": base_cost,
                "note": "This is a rough estimate. Actual costs depend on data size and query complexity."
            }
            
        except Exception as e:
            logger.error(f"Error estimating Athena cost: {e}")
            return {"error": str(e)}
    
    async def get_cloud_database_comparison(self) -> Dict[str, Any]:
        """Compare different cloud database options"""
        try:
            comparison = {
                "aws_athena": {
                    "type": "Serverless Query Service",
                    "best_for": ["Ad-hoc analytics", "Data exploration", "ETL workflows"],
                    "pricing_model": "Pay-per-query ($5/TB scanned)",
                    "pros": [
                        "No infrastructure management",
                        "Direct S3 integration",
                        "Standard SQL support",
                        "Built-in security"
                    ],
                    "cons": [
                        "Query latency (seconds to minutes)",
                        "Cost can be unpredictable",
                        "Limited to read operations"
                    ]
                },
                "azure_sql": {
                    "type": "Managed Relational Database",
                    "best_for": ["OLTP applications", "Business applications", "Real-time analytics"],
                    "pricing_model": "DTU/vCore based + storage",
                    "pros": [
                        "High performance",
                        "Built-in intelligence",
                        "Automatic tuning",
                        "High availability"
                    ],
                    "cons": [
                        "Higher cost for large workloads",
                        "More complex management",
                        "Vendor lock-in"
                    ]
                },
                "recommendations": {
                    "use_athena_when": [
                        "Analyzing large datasets in S3",
                        "Need serverless architecture",
                        "Cost is primary concern",
                        "Query performance is not critical"
                    ],
                    "use_azure_sql_when": [
                        "Building production applications",
                        "Need real-time performance",
                        "Require ACID compliance",
                        "Have predictable workloads"
                    ]
                }
            }
            return comparison
            
        except Exception as e:
            logger.error(f"Error getting cloud database comparison: {e}")
            return {"error": str(e)}
    
    async def get_migration_guidance(self, source_db: str, target_cloud: str) -> Dict[str, Any]:
        """Provide guidance for migrating to cloud databases"""
        try:
            if target_cloud == "athena":
                return await self._get_athena_migration_guide(source_db)
            elif target_cloud == "azure_sql":
                return await self._get_azure_sql_migration_guide(source_db)
            else:
                return {"error": f"Unsupported target cloud: {target_cloud}"}
                
        except Exception as e:
            logger.error(f"Error getting migration guidance: {e}")
            return {"error": str(e)}
    
    async def _get_athena_migration_guide(self, source_db: str) -> Dict[str, Any]:
        """Get migration guide for AWS Athena"""
        try:
            guide = {
                "target": "AWS Athena",
                "migration_steps": [
                    "1. Export data from source database to CSV/Parquet format",
                    "2. Upload data to S3 bucket with organized folder structure",
                    "3. Create external tables in Athena pointing to S3 data",
                    "4. Test queries and optimize data format",
                    "5. Update application connection strings",
                    "6. Monitor query performance and costs"
                ],
                "data_format_recommendations": [
                    "Use Parquet format for best compression and performance",
                    "Partition data by date, region, or other logical columns",
                    "Use appropriate compression (Snappy, Gzip)",
                    "Organize S3 folders logically (e.g., /year/month/day/)"
                ],
                "considerations": [
                    "Query latency will increase (seconds vs milliseconds)",
                    "Cost model changes from fixed to pay-per-query",
                    "Data updates require re-uploading to S3",
                    "Consider using AWS Glue for data catalog management"
                ]
            }
            return guide
            
        except Exception as e:
            logger.error(f"Error getting Athena migration guide: {e}")
            return {"error": str(e)}
    
    async def _get_azure_sql_migration_guide(self, source_db: str) -> Dict[str, Any]:
        """Get migration guide for Azure SQL Database"""
        try:
            guide = {
                "target": "Azure SQL Database",
                "migration_steps": [
                    "1. Assess source database compatibility using Data Migration Assistant",
                    "2. Choose appropriate service tier (DTU or vCore)",
                    "3. Use Azure Database Migration Service for online migration",
                    "4. Test application compatibility and performance",
                    "5. Update connection strings and authentication",
                    "6. Monitor performance and optimize as needed"
                ],
                "service_tier_selection": [
                    "DTU-based: Simple, predictable pricing for small to medium workloads",
                    "vCore-based: More control, better for large or variable workloads",
                    "Serverless: Auto-scaling for development and testing"
                ],
                "considerations": [
                    "Ensure network connectivity and firewall rules",
                    "Plan for authentication method (SQL vs Azure AD)",
                    "Consider using Azure SQL Managed Instance for easier migration",
                    "Plan for backup and disaster recovery strategies"
                ]
            }
            return guide
            
        except Exception as e:
            logger.error(f"Error getting Azure SQL migration guide: {e}")
            return {"error": str(e)}
