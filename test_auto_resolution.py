#!/usr/bin/env python3
"""
Test script for Auto-Error Resolution System
Demonstrates how DBA-GPT automatically captures and resolves database errors
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai.dba_assistant import DBAAssistant
from core.config import Config
from core.database.connector import DatabaseError
from core.utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_auto_error_resolution():
    """Test the auto-error resolution system"""
    
    print("🚀 Testing DBA-GPT Auto-Error Resolution System")
    print("=" * 60)
    
    # Initialize DBA Assistant
    config = Config()
    assistant = DBAAssistant(config)
    
    print(f"✅ DBA Assistant initialized")
    print(f"📊 Error callback status: {'Active' if assistant.db_connector.error_callback else 'Inactive'}")
    print()
    
    # Test different error types
    test_errors = [
        {
            "type": "TABLE_NOT_FOUND",
            "error": DatabaseError(
                error_type="TABLE_NOT_FOUND",
                error_code="1146",
                message="Table 'DBT.non_existent_table' doesn't exist",
                query="SELECT * FROM non_existent_table",
                table="non_existent_table"
            )
        },
        {
            "type": "ACCESS_DENIED",
            "error": DatabaseError(
                error_type="ACCESS_DENIED",
                error_code="1045",
                message="Access denied for user 'test'@'localhost' (using password: YES)",
                query="SELECT * FROM users"
            )
        },
        {
            "type": "SYNTAX_ERROR",
            "error": DatabaseError(
                error_type="SYNTAX_ERROR",
                error_code="1064",
                message="You have an error in your SQL syntax",
                query="SELCT * FROM users",  # Intentional typo
                table="users"
            )
        },
        {
            "type": "CONNECTION_ERROR",
            "error": DatabaseError(
                error_type="CONNECTION_ERROR",
                error_code="2003",
                message="Can't connect to MySQL server on 'localhost'",
                query="SHOW TABLES"
            )
        }
    ]
    
    # Test each error type
    for i, test_case in enumerate(test_errors, 1):
        print(f"🧪 Test {i}: {test_case['type']}")
        print("-" * 40)
        
        error = test_case['error']
        print(f"Error: {error.message}")
        if error.query:
            print(f"Query: {error.query}")
        
        print("\n🤖 Generating AI resolution...")
        try:
            # Test the auto-resolution system
            resolution = await assistant.get_auto_error_resolution(
                error.to_ai_prompt(), 
                error
            )
            
            print("✅ Auto-Resolution Generated:")
            print(resolution[:500] + "..." if len(resolution) > 500 else resolution)
            
        except Exception as e:
            print(f"❌ Error generating resolution: {e}")
            
        print("\n" + "=" * 60 + "\n")
    
    # Test simulated database error
    print("🧪 Testing Simulated Database Error")
    print("-" * 40)
    
    try:
        # Get a database connection
        db_config = list(assistant.config.databases.values())[0] if assistant.config.databases else None
        
        if db_config:
            print(f"Connecting to {db_config.database}...")
            connection = await assistant.db_connector.get_connection(db_config)
            
            # This should trigger an auto-error resolution
            print("Executing invalid query to trigger error...")
            try:
                await connection.execute_query("SELECT * FROM non_existent_table_12345")
            except Exception as e:
                print(f"✅ Error captured and handled: {type(e).__name__}")
                
        else:
            print("⚠️ No database configuration found")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
    
    print(f"\n📊 Total errors stored: {len(assistant.recent_errors)}")
    
    if assistant.recent_errors:
        print("\n📋 Recent Errors Summary:")
        for i, error in enumerate(assistant.recent_errors, 1):
            print(f"  {i}. {error.error_type} - {error.message[:50]}...")

async def main():
    """Main function"""
    try:
        await test_auto_error_resolution()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test error: {e}", exc_info=True)

if __name__ == "__main__":
    print("🧪 DBA-GPT Auto-Error Resolution Test")
    print("This script demonstrates automatic error capture and resolution")
    print()
    
    # Run the test
    asyncio.run(main()) 