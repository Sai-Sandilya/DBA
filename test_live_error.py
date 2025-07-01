#!/usr/bin/env python3
"""
Live Database Error Testing Script
Creates real errors in your database to test auto-error resolution
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai.dba_assistant import DBAAssistant
from core.config import Config
from core.utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_live_database_errors():
    """Test auto-error resolution with real database errors"""
    
    print("🚀 LIVE DATABASE ERROR TESTING")
    print("=" * 50)
    print("This will create controlled errors in your DBT database")
    print("to test the auto-error resolution system.")
    print()
    
    # Initialize DBA Assistant
    config = Config()
    assistant = DBAAssistant(config)
    
    print(f"✅ DBA Assistant initialized")
    print(f"📊 Auto-Error System: {'🟢 ACTIVE' if assistant.db_connector.error_callback else '🔴 INACTIVE'}")
    print()
    
    # Get database configuration
    if not assistant.config.databases:
        print("❌ No database configuration found!")
        return
    
    db_name = list(assistant.config.databases.keys())[0]
    db_config = assistant.config.databases[db_name]
    
    print(f"🗄️ Using Database: {db_config.database}")
    print(f"🌐 Host: {db_config.host}:{db_config.port}")
    print()
    
    # Test different error scenarios
    test_scenarios = [
        {
            "name": "TABLE NOT FOUND ERROR",
            "description": "Query a non-existent table",
            "query": "SELECT * FROM non_existent_table_xyz123",
            "expected_error": "TABLE_NOT_FOUND"
        },
        {
            "name": "SYNTAX ERROR", 
            "description": "Execute SQL with syntax error",
            "query": "SELCT * FROM users WHRE id = 1",  # Multiple typos
            "expected_error": "SYNTAX_ERROR"
        },
        {
            "name": "COLUMN NOT FOUND ERROR",
            "description": "Query non-existent column",
            "query": "SELECT non_existent_column_xyz FROM users",
            "expected_error": "COLUMN_NOT_FOUND"
        },
        {
            "name": "INVALID FUNCTION ERROR",
            "description": "Use non-existent MySQL function",
            "query": "SELECT INVALID_FUNCTION(id) FROM users",
            "expected_error": "FUNCTION_ERROR"
        }
    ]
    
    # Track errors for summary
    captured_errors = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"🧪 TEST {i}: {scenario['name']}")
        print(f"📝 Description: {scenario['description']}")
        print(f"🔍 Query: {scenario['query']}")
        print("-" * 50)
        
        try:
            # Get database connection
            connection = await assistant.db_connector.get_connection(db_config)
            
            # Execute the query that should cause an error
            print("⚡ Executing query (this should trigger an error)...")
            
            try:
                result = await connection.execute_query(scenario['query'])
                print(f"⚠️ Unexpected: Query succeeded with result: {result}")
                
            except Exception as e:
                print(f"✅ Error captured: {type(e).__name__}")
                print(f"📄 Error message: {str(e)}")
                
                # The auto-error resolution should have triggered
                print("🤖 Auto-error resolution should have been triggered!")
                
                # Check if error was stored
                if assistant.recent_errors:
                    latest_error = assistant.recent_errors[-1]
                    captured_errors.append({
                        "scenario": scenario['name'],
                        "error_type": latest_error.error_type,
                        "error_code": latest_error.error_code,
                        "message": latest_error.message,
                        "query": latest_error.query
                    })
                    
                    print(f"📊 Error stored as: {latest_error.error_type}")
                    print(f"🔢 Error code: {latest_error.error_code}")
                    
                    # Generate resolution
                    print("\n🔧 Generating AI resolution...")
                    try:
                        resolution = await assistant.get_auto_error_resolution(
                            latest_error.to_ai_prompt(), 
                            latest_error
                        )
                        
                        print("✅ AUTO-GENERATED RESOLUTION:")
                        print("=" * 30)
                        # Show first 300 characters of resolution
                        print(resolution[:300] + "..." if len(resolution) > 300 else resolution)
                        print("=" * 30)
                        
                    except Exception as res_error:
                        print(f"❌ Failed to generate resolution: {res_error}")
                
            # Clean up connection
            if hasattr(connection, 'close'):
                await connection.close()
                
        except Exception as conn_error:
            print(f"❌ Connection error: {conn_error}")
            
        print("\n" + "🔹" * 60 + "\n")
    
    # Summary Report
    print("📋 SUMMARY REPORT")
    print("=" * 50)
    print(f"🧪 Total tests: {len(test_scenarios)}")
    print(f"🚨 Errors captured: {len(captured_errors)}")
    print(f"📊 Total errors in system: {len(assistant.recent_errors)}")
    
    if captured_errors:
        print("\n📋 Captured Errors:")
        for i, error in enumerate(captured_errors, 1):
            print(f"  {i}. {error['scenario']} → {error['error_type']} (Code: {error['error_code']})")
    
    print(f"\n🎯 Auto-Error Resolution System Status:")
    print(f"   - Error Callback: {'✅ Active' if assistant.db_connector.error_callback else '❌ Inactive'}")
    print(f"   - Error Storage: {'✅ Working' if assistant.recent_errors else '❌ Not storing'}")
    print(f"   - AI Resolution: {'✅ Functional' if captured_errors else '❌ Needs check'}")
    
    # Test the web interface integration
    print(f"\n🌐 Web Interface Integration:")
    print(f"   - Visit: http://localhost:8502")
    print(f"   - Go to: Monitoring → Auto-Error Resolution System")
    print(f"   - You should see {len(assistant.recent_errors)} recent errors")

async def main():
    """Main function"""
    try:
        await test_live_database_errors()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test error: {e}", exc_info=True)

if __name__ == "__main__":
    print("🧪 LIVE DATABASE AUTO-ERROR RESOLUTION TEST")
    print("This script will create controlled database errors")
    print("to verify your auto-resolution system is working.\n")
    
    # Run the test
    asyncio.run(main()) 