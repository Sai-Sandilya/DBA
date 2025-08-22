#!/usr/bin/env python3
"""
AWS Athena Database Connector for DBA-GPT
Provides seamless integration with AWS Athena for data analytics
"""

import asyncio
import boto3
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AthenaConnection:
    """AWS Athena database connection wrapper"""
    
    def __init__(self, config: Dict[str, Any]):
        self.region = config.get('region', 'us-east-1')
        self.s3_staging_dir = config.get('s3_staging_dir')
        self.work_group = config.get('work_group', 'primary')
        self.catalog = config.get('catalog', 'awsdatacatalog')
        self.database = config.get('database', 'default')
        
        # AWS credentials (IAM role, access keys, or profile)
        self.session = boto3.Session(
            aws_access_key_id=config.get('aws_access_key_id'),
            aws_secret_access_key=config.get('aws_secret_access_key'),
            profile_name=config.get('profile_name'),
            region_name=self.region
        )
        
        # Initialize Athena client
        self.athena_client = self.session.client('athena')
        
    async def execute_query(self, query: str, **kwargs) -> List[Dict]:
        """Execute Athena query and return results"""
        try:
            logger.info(f"Executing Athena query: {query[:100]}...")
            
            # Connect to Athena
            conn = connect(
                s3_staging_dir=self.s3_staging_dir,
                region_name=self.region,
                work_group=self.work_group,
                boto3_session=self.session
            )
            
            # Execute query
            cursor = conn.cursor(PandasCursor)
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            if hasattr(results, 'to_dict'):
                return results.to_dict('records')
            else:
                return results
                
        except Exception as e:
            logger.error(f"Athena query failed: {str(e)}")
            raise Exception(f"Athena query failed: {str(e)}")
    
    async def get_tables(self) -> List[str]:
        """Get list of tables in the database"""
        try:
            query = f"""
            SELECT table_name 
            FROM {self.catalog}.{self.database}.information_schema.tables 
            WHERE table_schema = '{self.database}'
            ORDER BY table_name
            """
            results = await self.execute_query(query)
            return [row['table_name'] for row in results]
        except Exception as e:
            logger.error(f"Failed to get tables: {str(e)}")
            return []
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        try:
            query = f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM {self.catalog}.{self.database}.information_schema.columns 
            WHERE table_schema = '{self.database}' AND table_name = '{table_name}'
            ORDER BY ordinal_position
            """
            results = await self.execute_query(query)
            
            schema = {
                'table_name': table_name,
                'columns': results,
                'total_columns': len(results)
            }
            return schema
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {str(e)}")
            return {'table_name': table_name, 'columns': [], 'total_columns': 0}
    
    async def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get table statistics"""
        try:
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {self.database}.{table_name}"
            count_result = await self.execute_query(count_query)
            row_count = count_result[0]['row_count'] if count_result else 0
            
            # Get table size (approximate)
            size_query = f"""
            SELECT 
                SUM(CAST(data_length AS BIGINT)) as table_size_bytes,
                COUNT(*) as partition_count
            FROM {self.catalog}.{self.database}.information_schema.partitions 
            WHERE table_schema = '{self.database}' AND table_name = '{table_name}'
            """
            size_result = await self.execute_query(size_query)
            
            stats = {
                'table_name': table_name,
                'row_count': row_count,
                'table_size_bytes': size_result[0].get('table_size_bytes', 0) if size_result else 0,
                'partition_count': size_result[0].get('partition_count', 0) if size_result else 0
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats for {table_name}: {str(e)}")
            return {'table_name': table_name, 'row_count': 0, 'table_size_bytes': 0, 'partition_count': 0}
    
    async def get_workgroups(self) -> List[Dict[str, Any]]:
        """Get available Athena workgroups"""
        try:
            response = self.athena_client.list_work_groups()
            return response.get('WorkGroups', [])
        except Exception as e:
            logger.error(f"Failed to get workgroups: {str(e)}")
            return []
    
    async def get_query_history(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Get query execution history"""
        try:
            response = self.athena_client.list_query_executions(
                MaxResults=max_results
            )
            query_ids = response.get('QueryExecutionIds', [])
            
            # Get details for each query
            query_details = []
            for query_id in query_ids[:10]:  # Limit to 10 for performance
                try:
                    detail_response = self.athena_client.get_query_execution(
                        QueryExecutionId=query_id
                    )
                    query_details.append(detail_response.get('QueryExecution', {}))
                except Exception:
                    continue
            
            return query_details
        except Exception as e:
            logger.error(f"Failed to get query history: {str(e)}")
            return []
    
    async def optimize_query(self, query: str) -> str:
        """Optimize SQL for Athena performance"""
        optimized = query
        
        # Add Athena-specific optimizations
        if "CREATE TABLE" in query.upper() and "STORED AS" not in query.upper():
            optimized += " STORED AS PARQUET"
        
        # Add partition hints
        if "WHERE" in query.upper() and "partition" not in query.lower():
            optimized += " -- Consider partitioning by date columns for better performance"
        
        # S3 path optimization
        if "s3://" in query:
            optimized += " -- Use S3 Select for large files to reduce data scanned"
            
        return optimized
    
    async def estimate_cost(self, query: str, data_scanned_gb: float = 1.0) -> Dict[str, Any]:
        """Estimate Athena query cost"""
        try:
            # Athena charges $5 per TB scanned
            cost_per_tb = 5.0
            cost = (data_scanned_gb / 1024) * cost_per_tb
            
            return {
                'estimated_cost_usd': round(cost, 4),
                'data_scanned_gb': data_scanned_gb,
                'cost_per_tb': cost_per_tb,
                'optimization_tips': [
                    'Use columnar formats (Parquet/ORC)',
                    'Partition data by frequently queried columns',
                    'Use S3 Select for large files',
                    'Avoid SELECT * when possible'
                ]
            }
        except Exception as e:
            logger.error(f"Failed to estimate cost: {str(e)}")
            return {'estimated_cost_usd': 0, 'error': str(e)}
    
    async def close(self):
        """Close the connection"""
        # Athena connections are stateless, no cleanup needed
        pass
