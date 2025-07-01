#!/usr/bin/env python3
"""
Basic usage examples for DBA-GPT
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.ai.dba_assistant import DBAAssistant


async def basic_chat_example():
    """Basic chat example"""
    print("🤖 DBA-GPT Basic Chat Example")
    print("=" * 40)
    
    # Initialize configuration and assistant
    config = Config()
    assistant = DBAAssistant(config)
    
    # Example questions
    questions = [
        "My PostgreSQL database is running slow. What should I check first?",
        "How do I optimize MySQL performance?",
        "What security measures should I implement for my database?",
        "How do I create a backup strategy for PostgreSQL?",
        "What are the best practices for database indexing?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print("-" * 50)
        
        try:
            recommendation = await assistant.get_recommendation(question)
            
            print(f"🎯 Issue: {recommendation.issue}")
            print(f"⚠️  Severity: {recommendation.severity}")
            print(f"📊 Category: {recommendation.category}")
            print(f"📝 Description: {recommendation.description}")
            print(f"🔧 Solution: {recommendation.solution}")
            print(f"📈 Impact: {recommendation.estimated_impact}")
            print(f"⚠️  Risk: {recommendation.risk_level}")
            
            if recommendation.sql_commands:
                print(f"💻 SQL Commands:")
                for j, cmd in enumerate(recommendation.sql_commands, 1):
                    print(f"   {j}. {cmd}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            
        print()


async def database_analysis_example():
    """Database analysis example"""
    print("🔍 DBA-GPT Database Analysis Example")
    print("=" * 40)
    
    config = Config()
    assistant = DBAAssistant(config)
    
    # Check if databases are configured
    if not config.databases:
        print("⚠️  No databases configured. Please add database connections to config.yaml")
        return
    
    for db_name, db_config in config.databases.items():
        print(f"\n📊 Analyzing database: {db_name}")
        print("-" * 30)
        
        try:
            # Get current metrics
            metrics = await assistant.analyzer.get_current_metrics(db_config)
            print(f"📈 CPU Usage: {metrics.get('cpu_usage', 'N/A')}%")
            print(f"💾 Memory Usage: {metrics.get('memory_usage', 'N/A')}%")
            print(f"💿 Disk Usage: {metrics.get('disk_usage', 'N/A')}%")
            print(f"🔗 Active Connections: {metrics.get('active_connections', 'N/A')}")
            print(f"🐌 Slow Queries: {metrics.get('slow_queries', 'N/A')}")
            
            # Get system health
            health = await assistant.analyzer.get_system_health(db_config)
            print(f"🏥 Overall Health: {health.get('overall_status', 'N/A')}")
            
            if health.get('recommendations'):
                print("💡 Recommendations:")
                for rec in health['recommendations']:
                    print(f"   • {rec}")
                    
        except Exception as e:
            print(f"❌ Error analyzing {db_name}: {e}")


async def monitoring_example():
    """Monitoring example"""
    print("📊 DBA-GPT Monitoring Example")
    print("=" * 40)
    
    config = Config()
    assistant = DBAAssistant(config)
    
    if not config.databases:
        print("⚠️  No databases configured for monitoring")
        return
    
    print("Starting monitoring simulation...")
    
    for db_name, db_config in config.databases.items():
        print(f"\n🔍 Monitoring {db_name}...")
        
        try:
            # Simulate monitoring cycle
            metrics = await assistant.analyzer.get_current_metrics(db_config)
            health = await assistant.analyzer.get_system_health(db_config)
            
            # Check for issues
            if health.get('overall_status') == 'critical':
                print(f"🚨 CRITICAL: {db_name} has critical issues!")
            elif health.get('overall_status') == 'warning':
                print(f"⚠️  WARNING: {db_name} has warnings")
            else:
                print(f"✅ HEALTHY: {db_name} is running well")
                
            # Show key metrics
            cpu = metrics.get('cpu_usage', 0)
            memory = metrics.get('memory_usage', 0)
            
            if cpu > 80:
                print(f"🔥 High CPU usage: {cpu}%")
            if memory > 85:
                print(f"💾 High memory usage: {memory}%")
                
        except Exception as e:
            print(f"❌ Error monitoring {db_name}: {e}")


async def tips_example():
    """Get DBA tips example"""
    print("💡 DBA-GPT Tips Example")
    print("=" * 40)
    
    config = Config()
    assistant = DBAAssistant(config)
    
    # Get general tips
    print("📚 General DBA Tips:")
    general_tips = await assistant.get_quick_tips()
    for i, tip in enumerate(general_tips[:5], 1):  # Show first 5 tips
        print(f"   {i}. {tip}")
    
    # Get database-specific tips
    for db_type in ['postgresql', 'mysql']:
        print(f"\n📚 {db_type.upper()} Specific Tips:")
        db_tips = await assistant.get_quick_tips(db_type)
        for i, tip in enumerate(db_tips, 1):
            print(f"   {i}. {tip}")


async def main():
    """Main example function"""
    print("🚀 DBA-GPT Examples")
    print("=" * 50)
    
    try:
        # Run examples
        await basic_chat_example()
        await database_analysis_example()
        await monitoring_example()
        await tips_example()
        
        print("\n🎉 All examples completed!")
        print("\nTo use DBA-GPT interactively:")
        print("1. CLI: python main.py --mode cli")
        print("2. Web: python main.py --mode web")
        print("3. API: python main.py --mode api")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("\nMake sure:")
        print("1. Dependencies are installed: pip install -r requirements.txt")
        print("2. Ollama is running: ollama serve")
        print("3. AI models are downloaded: ollama pull llama2:13b")
        print("4. Database connections are configured in config.yaml")


if __name__ == "__main__":
    asyncio.run(main()) 