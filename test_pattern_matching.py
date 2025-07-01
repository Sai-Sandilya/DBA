#!/usr/bin/env python3
"""
Test Pattern Matching for Auto-Error Resolution
"""

def test_pattern_matching():
    """Test if the pattern matching logic works"""
    
    # Entity patterns from the actual code
    entity_patterns = [
        'entity not found', 'entity missing', 'entity doesn\'t exist',
        'table not found', 'table missing', 'table doesn\'t exist', 'unknown table',
        'fix entity not found', 'resolve entity not found', 'entity error',
        'table error', 'missing entity', 'missing table', 'cannot find entity',
        'cannot find table', 'entity does not exist', 'table does not exist'
    ]
    
    # Test messages from the logs
    test_messages = [
        'how to fix entity not found ?',
        'how to fix entity not found ? give me query and solution for that aslo ',
        'Available Tables in Database \'DBT\'',
        'how to fix db connection issue',
        'give me questions ?'
    ]
    
    print("🧪 Testing Pattern Matching Logic")
    print("=" * 50)
    
    for message in test_messages:
        message_lower = message.lower()
        print(f"\n📝 Testing: '{message}'")
        print(f"   Lowercase: '{message_lower}'")
        
        # Test entity patterns
        matched_patterns = []
        for pattern in entity_patterns:
            if pattern in message_lower:
                matched_patterns.append(pattern)
        
        if matched_patterns:
            print(f"   ✅ MATCHED: {matched_patterns}")
        else:
            print(f"   ❌ NO MATCH")
            
        # Test the actual logic from the code
        pattern_match = any(pattern in message_lower for pattern in entity_patterns)
        print(f"   🔍 any() result: {pattern_match}")

if __name__ == "__main__":
    test_pattern_matching() 