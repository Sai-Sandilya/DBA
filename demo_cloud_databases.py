#!/usr/bin/env python3
"""
Cloud Database Demo Script for DBA-GPT
Demonstrates AWS Athena and Azure SQL Database integration
"""

import asyncio
import json
from pathlib import Path
from core.database.athena_connector import AthenaConnection
from core.database.azure_sql_connector import AzureSQLConnection
from core.ai.cloud_dba_assistant import CloudDBAAssistant

async def demo_aws_athena():
    """Demo AWS Athena capabilities"""
    print("🚀 **AWS Athena Demo**")
    print("=" * 50)
    
    # Mock configuration (replace with real values for testing)
    config = {
        'region': 'us-east-1',
        's3_staging_dir': 's3://demo-bucket/athena-staging/',
        'work_group': 'primary',
        'catalog': 'awsdatacatalog',
        'database': 'analytics_db'
    }
    
    try:
        # Initialize Athena connection
        athena_conn = AthenaConnection(config)
        
        # Demo query optimization
        sample_query = "SELECT * FROM sales_data WHERE date >= '2024-01-01'"
        print(f"\n📝 **Sample Query:** {sample_query}")
        
        optimized = await athena_conn.optimize_query(sample_query)
        print(f"🔧 **Optimized:** {optimized}")
        
        # Demo cost estimation
        cost_estimate = await athena_conn.estimate_cost(sample_query, 5.0)
        print(f"💰 **Cost Estimate:** ${cost_estimate['estimated_cost_usd']}")
        
        # Demo workgroups
        workgroups = await athena_conn.get_workgroups()
        print(f"🏢 **Available Workgroups:** {len(workgroups)} found")
        
        print("\n✅ AWS Athena demo completed successfully!")
        
    except Exception as e:
        print(f"❌ AWS Athena demo failed: {e}")
        print("💡 This is expected without real AWS credentials")

async def demo_azure_sql():
    """Demo Azure SQL Database capabilities"""
    print("\n🔵 **Azure SQL Database Demo**")
    print("=" * 50)
    
    # Mock configuration (replace with real values for testing)
    config = {
        'server': 'demo-server.database.windows.net',
        'database': 'demo_db',
        'authentication': 'sql',
        'port': 1433,
        'username': 'demo_user',
        'password': 'demo_password'
    }
    
    try:
        # Initialize Azure SQL connection
        azure_conn = AzureSQLConnection(config)
        
        # Demo query optimization
        sample_query = "SELECT * FROM users WHERE age > 18 ORDER BY name"
        print(f"\n📝 **Sample Query:** {sample_query}")
        
        optimized = await azure_conn.optimize_query(sample_query)
        print(f"🔧 **Optimized:** {optimized}")
        
        # Demo performance metrics (mock)
        print("📊 **Performance Metrics:** Mock data available")
        
        print("\n✅ Azure SQL demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Azure SQL demo failed: {e}")
        print("💡 This is expected without real Azure credentials")

async def demo_cloud_ai_assistant():
    """Demo Cloud Database AI Assistant"""
    print("\n🤖 **Cloud Database AI Assistant Demo**")
    print("=" * 50)
    
    try:
        # Initialize AI assistant
        ai_assistant = CloudDBAAssistant()
        
        # Demo Athena insights
        print("\n📊 **AWS Athena Insights:**")
        athena_insights = await ai_assistant.get_athena_insights({})
        print(f"   • Type: {athena_insights['database_type']}")
        print(f"   • Description: {athena_insights['description']}")
        print(f"   • Key Features: {len(athena_insights['key_features'])} features")
        
        # Demo Azure SQL insights
        print("\n📊 **Azure SQL Insights:**")
        azure_insights = await ai_assistant.get_azure_sql_insights({})
        print(f"   • Type: {azure_insights['database_type']}")
        print(f"   • Description: {azure_insights['description']}")
        print(f"   • Key Features: {len(azure_insights['key_features'])} features")
        
        # Demo query optimization
        print("\n🔧 **Query Optimization Demo:**")
        sample_query = "SELECT * FROM large_table JOIN another_table ON id = id WHERE date > '2024-01-01'"
        print(f"   • Original: {sample_query[:60]}...")
        
        athena_optimized = await ai_assistant.optimize_cloud_query(sample_query, "athena")
        print(f"   • Athena Optimized: {len(athena_optimized.get('recommendations', []))} recommendations")
        
        azure_optimized = await ai_assistant.optimize_cloud_query(sample_query, "azure_sql")
        print(f"   • Azure SQL Optimized: {len(azure_optimized.get('recommendations', []))} recommendations")
        
        # Demo cloud database comparison
        print("\n📈 **Cloud Database Comparison:**")
        comparison = await ai_assistant.get_cloud_database_comparison()
        print(f"   • AWS Athena: {comparison['aws_athena']['type']}")
        print(f"   • Azure SQL: {comparison['azure_sql']['type']}")
        
        print("\n✅ Cloud AI Assistant demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Cloud AI Assistant demo failed: {e}")

async def demo_migration_guidance():
    """Demo migration guidance"""
    print("\n🔄 **Migration Guidance Demo**")
    print("=" * 50)
    
    try:
        ai_assistant = CloudDBAAssistant()
        
        # Demo Athena migration guide
        print("\n📋 **AWS Athena Migration Guide:**")
        athena_migration = await ai_assistant.get_migration_guidance("mysql", "athena")
        print(f"   • Target: {athena_migration['target']}")
        print(f"   • Steps: {len(athena_migration['migration_steps'])} migration steps")
        print(f"   • Considerations: {len(athena_migration['considerations'])} key points")
        
        # Demo Azure SQL migration guide
        print("\n📋 **Azure SQL Migration Guide:**")
        azure_migration = await ai_assistant.get_migration_guidance("postgresql", "azure_sql")
        print(f"   • Target: {azure_migration['target']}")
        print(f"   • Steps: {len(azure_migration['migration_steps'])} migration steps")
        print(f"   • Service Tiers: {len(azure_migration['service_tier_selection'])} options")
        
        print("\n✅ Migration guidance demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration guidance demo failed: {e}")

async def main():
    """Main demo function"""
    print("☁️ **DBA-GPT Cloud Database Integration Demo**")
    print("=" * 60)
    print("This demo showcases the new cloud database capabilities:")
    print("• AWS Athena integration for serverless analytics")
    print("• Azure SQL Database integration for managed SQL")
    print("• AI-powered query optimization and cost estimation")
    print("• Migration guidance and best practices")
    print("=" * 60)
    
    # Run all demos
    await demo_aws_athena()
    await demo_azure_sql()
    await demo_cloud_ai_assistant()
    await demo_migration_guidance()
    
    print("\n🎉 **All Cloud Database Demos Completed!**")
    print("\n💡 **Next Steps:**")
    print("1. Configure real AWS credentials for Athena testing")
    print("2. Set up Azure SQL Database connection")
    print("3. Test with real data and queries")
    print("4. Explore cost optimization features")
    print("5. Use migration guidance for real projects")

if __name__ == "__main__":
    asyncio.run(main())
