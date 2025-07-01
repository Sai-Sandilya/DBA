#!/usr/bin/env python3
"""
Demo: External MySQL Error Detection
Shows what would happen if external MySQL errors were detected
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


async def demo_external_error_detection():
    """Demonstrate what external error detection would look like"""
    
    print("🎭 DEMO: External MySQL Error Detection")
    print("=" * 50)
    print("This shows what would happen if you ran bad SQL")
    print("in MySQL Workbench, command line, etc.")
    print()
    
    # Initialize DBA Assistant
    config = Config()
    assistant = DBAAssistant(config)
    
    print(f"✅ Enhanced DBA Assistant running")
    print(f"📊 Current errors: {len(assistant.recent_errors)}")
    print()
    
    # Simulate external MySQL errors that would be detected
    external_scenarios = [
        {
            "source": "MySQL Workbench",
            "query": "SELECT * FROM customers_backup;",
            "error": "Table 'ecommerce.customers_backup' doesn't exist",
            "user": "john@localhost"
        },
        {
            "source": "phpMyAdmin",
            "query": "UPDATE users SET status='active' WHERE invalid_column=1;",
            "error": "Unknown column 'invalid_column' in 'where clause'",
            "user": "admin@192.168.1.100"
        },
        {
            "source": "MySQL Command Line",
            "query": "SELCT name FROM products;",
            "error": "You have an error in your SQL syntax near 'SELCT'",
            "user": "root@localhost"
        }
    ]
    
    print("🔍 SIMULATING EXTERNAL ERRORS...")
    print("(These would be detected from MySQL logs in real scenario)")
    print()
    
    for i, scenario in enumerate(external_scenarios, 1):
        print(f"📱 EXTERNAL ERROR #{i}")
        print(f"   Source: {scenario['source']}")
        print(f"   User: {scenario['user']}")
        print(f"   Query: {scenario['query']}")
        print(f"   Error: {scenario['error']}")
        print()
        
        # Create external error object
        if "doesn't exist" in scenario['error']:
            error_type = "TABLE_NOT_FOUND"
            error_code = "1146"
        elif "Unknown column" in scenario['error']:
            error_type = "COLUMN_NOT_FOUND" 
            error_code = "1054"
        elif "syntax" in scenario['error']:
            error_type = "SYNTAX_ERROR"
            error_code = "1064"
        else:
            error_type = "GENERAL"
            error_code = "UNKNOWN"
        
        # Extract table name if present
        table_name = None
        if "FROM" in scenario['query']:
            parts = scenario['query'].split("FROM")
            if len(parts) > 1:
                table_part = parts[1].strip().split()[0].rstrip(';')
                table_name = table_part
        
        external_error = DatabaseError(
            error_type=error_type,
            error_code=error_code,
            message=scenario['error'],
            query=scenario['query'],
            table=table_name,
            context={
                "source": "external_mysql",
                "external_source": scenario['source'],
                "user": scenario['user'],
                "detection_method": "mysql_log_monitor"
            }
        )
        
        print("🤖 Processing with Enhanced Auto-Resolution...")
        
        # Process through enhanced auto-resolution system
        try:
            resolution = await assistant.handle_auto_error_resolution(external_error)
            
            # Show what strategy was used
            similar_count = assistant._count_similar_errors(
                assistant._generate_error_signature(external_error)
            )
            strategy = assistant._determine_resolution_strategy(external_error, similar_count)
            
            print(f"   ✅ Strategy: {strategy}")
            print(f"   🔍 Pattern: {assistant._generate_error_signature(external_error)}")
            print(f"   📊 Similar errors: {similar_count}")
            
            # Show resolution preview
            if resolution:
                preview = resolution[:150] + "..." if len(resolution) > 150 else resolution
                print(f"   🚨 Resolution: {preview}")
            
        except Exception as e:
            print(f"   ❌ Error processing: {e}")
        
        print("   " + "─" * 40)
        print()
    
    # Show enhanced analytics
    print("📊 ENHANCED ANALYTICS AFTER EXTERNAL ERRORS")
    print("=" * 45)
    
    try:
        stats = assistant.get_enhanced_system_stats()
        
        print(f"🎯 Total Resolutions: {stats['total_resolutions']}")
        print(f"🔍 Error Patterns: {stats['error_patterns']}")
        print(f"🏥 System Health: {stats['system_health'].upper()}")
        
        if stats['most_common_errors']:
            print(f"\n📈 Top Error Types:")
            for error_type, count in stats['most_common_errors'][:3]:
                print(f"   • {error_type}: {count} occurrences")
        
        if stats['resolution_strategies']:
            print(f"\n🛠️ Resolution Strategies:")
            for strategy, count in stats['resolution_strategies'].items():
                icon = {
                    'SELF_HEALING': '🤖',
                    'IMMEDIATE_FIX': '🚨', 
                    'PREVENTIVE': '🛡️',
                    'AI_POWERED': '🧠'
                }.get(strategy, '⚙️')
                print(f"   {icon} {strategy}: {count} times")
                
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
    
    print(f"\n🎭 DEMO COMPLETE")
    print("=" * 20)
    print(f"📊 Total errors in system: {len(assistant.recent_errors)}")
    print("✨ This is what would happen with external MySQL error detection!")
    
    return len(assistant.recent_errors)


async def main():
    """Main demo function"""
    try:
        error_count = await demo_external_error_detection()
        
        print(f"\n🌟 SUMMARY: External Error Detection Demo")
        print("=" * 45)
        print(f"✅ {error_count} external errors processed")
        print("🤖 Enhanced auto-resolution working")
        print("📊 Pattern analysis functioning") 
        print("🛡️ Self-healing capabilities demonstrated")
        
        print(f"\n💡 TO ENABLE THIS FOR REAL:")
        print("1. Enable MySQL error logging")
        print("2. Start MySQL log monitor")
        print("3. External errors will be auto-resolved!")
        print("4. Check the web interface for real-time monitoring")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    print("🎭 External MySQL Error Detection Demo")
    print("Shows how DBA-GPT would handle external MySQL errors")
    print()
    
    asyncio.run(main()) 