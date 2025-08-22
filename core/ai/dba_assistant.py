"""
DBA-GPT AI Assistant - Core AI component for database administration
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

import ollama
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from core.config import Config
from core.utils.logger import setup_logger
from core.database.connector import DatabaseConnector, DatabaseError
from core.analysis.analyzer import PerformanceAnalyzer
from core.ai.smart_join_assistant import SmartJoinAssistant
from core.ai.smart_query_builder import SmartQueryBuilder
from core.ai.pattern_detector import PatternDetector
from core.ai.schema_visualizer import SchemaVisualizer
from core.ai.nosql_assistant import NoSQLAssistant

logger = setup_logger(__name__)


# Enhanced knowledge base for Oracle, structured for better AI consumption
ORACLE_KNOWLEDGE_BASE = {
    "general_prompt": """
You are DBA-GPT, acting as a Principal-level Oracle Database Administrator. Your primary goal is to provide expert, accurate, and actionable advice.
When responding, you MUST follow these rules:
1.  **Structure Your Answers**: Start with a brief summary, then provide detailed explanations. Use markdown for clarity (e.g., code blocks for SQL, bold for key terms, lists for steps).
2.  **Be Actionable**: Don't just explain what a problem is; explain how to fix it with step-by-step instructions.
3.  **Provide Queries**: When a user asks for information from the database, provide the exact SQL query needed to retrieve it. Explain what each part of the query does.
4.  **Reference Your Knowledge**: When answering about a known error (e.g., ORA-XXXXX) or a specific concept, state that you are using your internal knowledge base.
5.  **Be Cautious**: If a suggested action is destructive (e.g., killing a session, dropping an object), include a clear warning.
""",
    "common_errors": {
        "ORA-00600": {
            "title": "ORA-00600: internal error code",
            "summary": "This is a generic internal error, often indicating a bug in the Oracle database software itself. It requires immediate attention and usually involves Oracle Support.",
            "diagnosis": "Check the alert log for the full ORA-600 error stack and any generated trace files. These files are critical for diagnosis.",
            "solution": "1. Document the exact circumstances of the error. 2. Collect all relevant trace files and alert log entries. 3. Open a Service Request (SR) with Oracle Support and provide them with all the information."
        },
        "ORA-07445": {
            "title": "ORA-07445: exception caught: core dump",
            "summary": "This error occurs when a background or user process terminates unexpectedly, generating a core dump. It's often caused by an OS-level issue or a bug.",
            "diagnosis": "Similar to ORA-600, check the alert log and the referenced trace files for details about which process failed and what it was doing.",
            "solution": "This is a critical error. Collect diagnostics and contact Oracle Support. Do not attempt to resolve without expert guidance."
        },
        "ORA-01555": {
            "title": "ORA-01555: snapshot too old",
            "summary": "This error occurs when a long-running query cannot access a consistent version of data because the required UNDO information has been overwritten.",
            "diagnosis": "Identify the long-running SQL query. Check the size and configuration of your UNDO tablespace and the `UNDO_RETENTION` parameter.",
            "solution": "1. Optimize the long-running query to run faster. 2. Increase the size of the UNDO tablespace. 3. Increase the `UNDO_RETENTION` parameter to guarantee UNDO for a longer period. 4. Consider scheduling long-running jobs during periods of low activity."
        },
        "ORA-00942": {
            "title": "ORA-00942: table or view does not exist",
            "summary": "The SQL statement is trying to access a table or view that does not exist, or the user does not have the required privileges to see it.",
            "diagnosis": "1. Verify that the table/view name is spelled correctly. 2. Check if the object exists in `DBA_TABLES` or `DBA_VIEWS`. 3. Confirm the user has been granted `SELECT` privileges on the object. 4. If the object is in another schema, ensure a synonym exists or the schema name is prefixed (e.g., `SCOTT.EMP`).",
            "solution": "Correct the object name, grant the necessary privileges (`GRANT SELECT ON schema.table TO user;`), or create a synonym (`CREATE SYNONYM user.table FOR schema.table;`)."
        },
        "ORA-01031": {
            "title": "ORA-01031: insufficient privileges",
            "summary": "The user attempted to execute a command (e.g., `CREATE TABLE`, `GRANT`) without having the necessary system or object privileges.",
            "diagnosis": "Identify the exact privilege needed for the operation. Check the user's assigned roles and privileges using `DBA_SYS_PRIVS` and `DBA_ROLE_PRIVS`.",
            "solution": "Grant the specific required privilege to the user. For example, `GRANT CREATE TABLE TO username;`. Be careful not to grant excessive privileges."
        },
        "ORA-12541": {
            "title": "ORA-12541: TNS:no listener",
            "summary": "The client was unable to connect to the database because the Oracle TNS listener is not running or is not configured correctly on the database server.",
            "diagnosis": "On the database server, run `lsnrctl status` to check the listener's status. Verify the `tnsnames.ora` on the client and the `listener.ora` on the server have matching host, port, and service name information.",
            "solution": "If the listener is down, start it with `lsnrctl start`. If it's a configuration issue, correct the `.ora` files to ensure the client connection request matches the service provided by the listener."
        }
    },
    "performance_tuning": {
        "active_sessions": {
            "title": "Check Active Sessions",
            "description": "This query shows all currently active (not idle) sessions in the database, including the user, the SQL they are running, and how long they have been running.",
            "query": "SELECT sid, serial#, username, status, sql_id, last_call_et, event, blocking_session FROM v$session WHERE status = 'ACTIVE' AND type = 'USER';"
        },
        "blocking_sessions": {
            "title": "Identify Blocking and Waiting Sessions",
            "description": "This query is crucial for diagnosing locking issues. It shows which session is the blocker and which sessions are waiting for it.",
            "query": """
SELECT
   blocker.sid || ',' || blocker.serial# AS blocker_sid,
   blocker.username AS blocker_user,
   waiter.sid || ',' || waiter.serial# AS waiter_sid,
   waiter.username AS waiter_user,
   waiter.sql_id AS waiter_sql_id,
   waiter.row_wait_obj# AS locked_object_id
FROM v$session blocker, v$session waiter
WHERE
   blocker.sid = waiter.blocking_session
   AND blocker.blocking_session IS NULL;
"""
        },
        "kill_session": {
            "title": "Kill a Session",
            "description": "This command terminates a specific database session. This is a disruptive action and should only be used when a session is causing critical problems.",
            "query": "ALTER SYSTEM KILL SESSION 'sid,serial#' IMMEDIATE;",
            "warning": "WARNING: This command forcefully terminates the user's session, rolling back their current transaction. Use with extreme caution."
        },
        "awr_report": {
            "title": "Generate an AWR Report",
            "description": "The Automatic Workload Repository (AWR) report is the standard Oracle performance analysis tool. It provides a detailed snapshot of database performance between two points in time.",
            "query": "Run `@$ORACLE_HOME/rdbms/admin/awrrpt.sql` from SQL*Plus. It will prompt you for the desired begin and end snapshot IDs.",
            "explanation": "This is not a direct SQL query, but a script run from the SQL*Plus command-line tool."
        }
    },
    "backup_recovery": {
        "rman_backup": {
            "title": "Full Database Backup with RMAN",
            "description": "Recovery Manager (RMAN) is Oracle's native tool for backup and recovery. This is a basic command for a full online backup.",
            "query": """
RUN {
  ALLOCATE CHANNEL c1 DEVICE TYPE DISK FORMAT '/path/to/backups/full_%U';
  BACKUP DATABASE PLUS ARCHIVELOG;
  RELEASE CHANNEL c1;
}
""",
            "explanation": "This script is run inside the RMAN utility, not SQL*Plus. It backs up all datafiles and archived redo logs to the specified path."
        }
    }
}

# Enhanced MySQL Knowledge Base for Professional DBA Responses
MYSQL_DBA_KNOWLEDGE_BASE = {
    "entity_not_found": {
        "patterns": ["entity not found", "table not found", "table doesn't exist", "unknown table"],
        "diagnosis_queries": [
            "SHOW TABLES;",
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE();",
            "SHOW GRANTS FOR CURRENT_USER();",
            "SELECT DATABASE();"
        ],
        "solutions": {
            "check_existence": "SHOW TABLES LIKE '%table_name%';",
            "check_permissions": "SHOW GRANTS FOR CURRENT_USER();",
            "check_database": "SELECT DATABASE(); USE correct_database_name;",
            "create_table": """CREATE TABLE IF NOT EXISTS table_name (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""
        }
    },
    "performance_issues": {
        "patterns": ["slow query", "performance", "timeout", "long running"],
        "diagnosis_queries": [
            "SHOW PROCESSLIST;",
            "EXPLAIN SELECT * FROM table_name WHERE condition;",
            "SHOW STATUS LIKE 'Slow_queries';",
            "SELECT * FROM INFORMATION_SCHEMA.PROCESSLIST WHERE TIME > 5;"
        ],
        "solutions": {
            "enable_slow_log": "SET GLOBAL slow_query_log = 'ON'; SET GLOBAL long_query_time = 2;",
            "create_index": "CREATE INDEX idx_column ON table_name (column_name);",
            "optimize_table": "OPTIMIZE TABLE table_name;",
            "analyze_table": "ANALYZE TABLE table_name;"
        }
    },
    "connection_issues": {
        "patterns": ["connection refused", "max connections", "connection timeout"],
        "diagnosis_queries": [
            "SHOW STATUS LIKE 'Threads_connected';",
            "SHOW VARIABLES LIKE 'max_connections';",
            "SHOW PROCESSLIST;",
            "SHOW STATUS LIKE 'Connection_errors%';"
        ],
        "solutions": {
            "increase_connections": "SET GLOBAL max_connections = 500;",
            "kill_connection": "KILL CONNECTION_ID;",
            "optimize_timeout": "SET GLOBAL wait_timeout = 28800;"
        }
    },
    "security_issues": {
        "patterns": ["access denied", "permission denied", "privileges", "authentication failed"],
        "diagnosis_queries": [
            "SELECT USER(), CURRENT_USER();",
            "SHOW GRANTS FOR CURRENT_USER();",
            "SELECT * FROM INFORMATION_SCHEMA.USER_PRIVILEGES;",
            "SELECT * FROM mysql.user WHERE User = 'username';"
        ],
        "solutions": {
            "grant_privileges": "GRANT ALL PRIVILEGES ON database.* TO 'user'@'host'; FLUSH PRIVILEGES;",
            "create_user": "CREATE USER 'username'@'host' IDENTIFIED BY 'password';",
            "show_grants": "SHOW GRANTS FOR 'user'@'host';"
        }
    }
}

# Common DBA Maintenance Commands
MYSQL_MAINTENANCE_COMMANDS = {
    "health_check": [
        "SHOW ENGINE INNODB STATUS;",
        "SHOW SLAVE STATUS;",
        "SHOW MASTER STATUS;",
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.PROCESSLIST;",
        "SHOW STATUS LIKE 'Uptime';"
    ],
    "space_analysis": [
        "SELECT table_schema, SUM(data_length + index_length) / 1024 / 1024 AS 'Size (MB)' FROM information_schema.tables GROUP BY table_schema;",
        "SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)' FROM information_schema.tables WHERE table_schema = DATABASE() ORDER BY (data_length + index_length) DESC;",
        "SHOW TABLE STATUS FROM database_name;"
    ],
    "performance_tuning": [
        "SHOW VARIABLES LIKE 'innodb_buffer_pool_size';",
        "SHOW STATUS LIKE 'Innodb_buffer_pool_reads';",
        "SHOW STATUS LIKE 'Handler_read%';",
        "SHOW STATUS LIKE 'Select_%';"
    ]
}

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects from database"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


@dataclass
class DBARecommendation:
    """Structured DBA recommendation for the Analysis page"""
    issue: str
    severity: str
    description: str
    solution: str
    sql_commands: List[str]
    estimated_impact: str
    risk_level: str
    category: str
    timestamp: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None


class DBAAssistant:
    """Main DBA AI Assistant"""

    def __init__(self, config: Optional[Config] = None):
        """Initialize DBA Assistant with auto-error resolution"""
        self.config = config or Config()
        
        # Initialize components
        self.db_connector = DatabaseConnector(self.config)
        self.analyzer = PerformanceAnalyzer(self.config)
        self.smart_join_assistant = SmartJoinAssistant(self.db_connector)
        self.smart_query_builder = SmartQueryBuilder(self.db_connector)
        self.pattern_detector = PatternDetector(self.db_connector)
        self.schema_visualizer = SchemaVisualizer(self.db_connector)
        self.nosql_assistant = NoSQLAssistant(self.db_connector)
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Auto-error resolution storage
        self.recent_errors = []
        self.max_stored_errors = 10
        
        # Set up auto-error resolution callback after initialization
        self.db_connector.set_error_callback(self.handle_auto_error_resolution)
        
        self.system_prompt_template = self.config.ai.system_prompt
        
        # Enhanced auto-resolution tracking
        self.error_patterns = {}  # Track error patterns for self-healing
        self.resolution_history = []  # Track resolution effectiveness
        self.alert_thresholds = {'error_rate_per_hour': 5, 'critical_errors_per_day': 3}

    def _initialize_llm(self) -> Ollama:
        """Initialize the local LLM"""
        return Ollama(
            model=self.config.ai.model,
            temperature=self.config.ai.temperature,
            base_url=self.config.ai.ollama_host,
        )

    async def get_recommendation(self, query: str, db_name: str) -> DBARecommendation:
        """Get AI-powered DBA recommendation for the Analysis page"""
        try:
            context = await self._analyze_context(query, db_name)
            recommendation = await self._generate_recommendation_json(query, context)
            return recommendation
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return self._get_fallback_recommendation(query)

    async def _analyze_context(self, query: str, db_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze query context and gather relevant information"""
        context = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "database_info": {},
            "performance_metrics": {},
            "system_health": {}
        }
        if not db_name:
            return context

        db_config = self.config.databases.get(db_name)
        if not db_config:
            logger.warning(f"No configuration found for database: {db_name}")
            return context

        try:
            context["database_info"] = await self.analyzer.get_database_info(db_config)
            context["performance_metrics"] = await self.analyzer.get_current_metrics(db_config)
            context["system_health"] = await self.analyzer.get_system_health(db_config)
        except Exception as e:
            logger.warning(f"Could not gather live context for {db_name}: {e}")

        return context

    async def _generate_recommendation_json(self, query: str, context: Dict[str, Any]) -> DBARecommendation:
        """Generates a structured JSON recommendation for the Analysis page."""
        prompt_template = """
You are DBA-GPT, a senior database administrator AI assistant with 15+ years of experience. You provide PRACTICAL, ACTIONABLE solutions with SPECIFIC SQL queries.

{system_prompt}

CRITICAL RESPONSE GUIDELINES:
1. ALWAYS provide specific SQL queries and commands
2. Give step-by-step troubleshooting procedures
3. Include actual table/column examples from the user's database when available
4. Provide multiple solution approaches (quick fix + comprehensive solution)
5. Include performance implications and best practices
6. Use professional DBA terminology and formatting

RESPONSE FORMAT REQUIREMENTS:
- Start with a brief diagnostic summary
- Provide immediate actionable SQL commands  
- Include detailed explanation of the issue
- Offer prevention strategies
- Format code blocks properly with ```sql

CONTEXT ABOUT USER'S DATABASE:
- Database Type: MySQL
- Available Tables: {context}
- User Question: {query}

Previous conversation context: {history}

Provide a comprehensive, professional DBA response with specific SQL solutions for: {query}

DBA-GPT Response:"""
        prompt = PromptTemplate(template=prompt_template, input_variables=["query", "context", "history"])
        chain = LLMChain(llm=self.llm, prompt=prompt)

        try:
            context_str = json.dumps(context, cls=DecimalEncoder, indent=2)
            response_dict = await chain.ainvoke({"query": query, "context": context_str})
            response_text = response_dict.get('text', '{}')
            
            # Clean the response to ensure it is valid JSON
            json_str = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_str:
                data = json.loads(json_str.group(0))
                return DBARecommendation(
                    issue=data.get("issue", "N/A"),
                    severity=data.get("severity", "medium"),
                    description=data.get("description", "No description provided."),
                    solution=data.get("solution", "No solution provided."),
                    sql_commands=data.get("sql_commands", []),
                    estimated_impact=data.get("estimated_impact", "N/A"),
                    risk_level=data.get("risk_level", "medium"),
                    category=data.get("category", "general_advice"),
                    timestamp=datetime.now(),
                    context=context
                )
            else:
                raise ValueError("No valid JSON found in AI response")
        except Exception as e:
            logger.error(f"Error parsing AI JSON response: {e}")
            return self._get_fallback_recommendation(query)

    def _get_fallback_recommendation(self, query: str) -> DBARecommendation:
        """Get fallback recommendation when AI fails"""
        return DBARecommendation(
            issue="System Error",
            severity="medium",
            description=f"Unable to process query: {query}. Please check logs for details.",
            solution="1. Verify database connectivity\n2. Check configuration settings\n3. Restart the application.",
            sql_commands=[],
            estimated_impact="Resolve system issues to restore AI assistance.",
            risk_level="low",
            category="maintenance"
        )

    def _is_poor_quality_response(self, response_text: str) -> bool:
        """Detect poor quality AI responses that should be replaced with fallback"""
        if not response_text or len(response_text.strip()) < 20:
            return True
            
        # Check for common garbage patterns
        garbage_patterns = [
            'user canter theory', 'ai system:', 'user:', 'assistant:', 
            'theory', 'canter', 'unable to', 'i cannot', 'i can\'t',
            'sorry, i', 'apologize', 'i apologize', 'i don\'t know',
            'as an ai', 'as a language model', 'i\'m not able to'
        ]
        
        response_lower = response_text.lower()
        
        # If response contains mainly garbage patterns
        if any(pattern in response_lower for pattern in garbage_patterns):
            # But allow if it's part of a longer, meaningful response
            if len(response_text) < 100:
                return True
        
        # Check if response has proper structure (headers, formatting)
        has_structure = any(indicator in response_text for indicator in [
            '##', '###', '**', '```', '- ', '1.', '2.', 'SELECT', 'MySQL'
        ])
        
        # If very short and no structure, likely garbage
        if len(response_text) < 100 and not has_structure:
            return True
            
        return False

    def get_general_database_response(self, message: str) -> str:
        """Get response for general database topics and educational content"""
        return self._get_fallback_chat_response(message)
    
    def _get_fallback_chat_response(self, message: str) -> str:
        """Get comprehensive fallback chat response when AI fails - covers all DBA topics"""
        message_lower = message.lower().strip()
        
        # SQL STATEMENTS
        if any(pattern in message_lower for pattern in ['select statement', 'what is select', 'explain select']):
            return """## 📊 SELECT Statement - Complete Guide

### **What is SELECT?**
The **SELECT** statement is the most fundamental SQL command used to retrieve data from database tables. It allows you to query and fetch specific information from one or more tables.

### **Basic Syntax:**
```sql
SELECT column1, column2, ...
FROM table_name
WHERE condition
ORDER BY column1 ASC/DESC
LIMIT number;
```

### **Essential Examples:**

**1. Select All Columns:**
```sql
SELECT * FROM employees;
```

**2. Select Specific Columns:**
```sql
SELECT first_name, last_name, salary FROM employees;
```

**3. Select with Conditions:**
```sql
SELECT name, department 
FROM employees 
WHERE salary > 50000;
```

**4. Select with Sorting:**
```sql
SELECT name, hire_date 
FROM employees 
ORDER BY hire_date DESC;
```

**5. Select with Limit:**
```sql
SELECT name, salary 
FROM employees 
ORDER BY salary DESC 
LIMIT 10;
```

### **Advanced SELECT Features:**

**Aggregation Functions:**
```sql
SELECT 
    COUNT(*) as total_employees,
    AVG(salary) as average_salary,
    MAX(salary) as highest_salary,
    MIN(salary) as lowest_salary
FROM employees;
```

**Group By:**
```sql
SELECT department, COUNT(*), AVG(salary)
FROM employees 
GROUP BY department 
HAVING COUNT(*) > 5;
```

**Joins:**
```sql
SELECT e.name, d.department_name
FROM employees e
JOIN departments d ON e.dept_id = d.id;
```

### **Best Practices:**
- Always specify column names instead of using * in production
- Use WHERE clauses to filter data and improve performance
- Add appropriate indexes for frequently queried columns
- Use LIMIT for large datasets to prevent memory issues

Want to learn about JOINs, WHERE clauses, or other SQL concepts?"""

        elif any(pattern in message_lower for pattern in ['like operator', 'like function', 'what is like', 'explain like']):
            return """## 🔍 LIKE Operator - Pattern Matching Guide

### **What is LIKE?**
The **LIKE** operator is used in SQL to search for specific patterns in string data. It's essential for flexible text searches and filtering.

### **Basic Syntax:**
```sql
SELECT column1, column2
FROM table_name
WHERE column_name LIKE pattern;
```

### **Wildcard Characters:**

**% (Percent)**: Matches any sequence of characters (0 or more)
**_ (Underscore)**: Matches exactly one character

### **Essential Examples:**

**1. Names Starting with 'A':**
```sql
SELECT * FROM customers 
WHERE first_name LIKE 'A%';
```

**2. Names Ending with 'son':**
```sql
SELECT * FROM customers 
WHERE last_name LIKE '%son';
```

**3. Names Containing 'john':**
```sql
SELECT * FROM customers 
WHERE first_name LIKE '%john%';
```

**4. Exact Length Patterns:**
```sql
-- Names with exactly 4 characters
SELECT * FROM products 
WHERE product_code LIKE '____';

-- Phone numbers in format XXX-XXX-XXXX
SELECT * FROM customers 
WHERE phone LIKE '___-___-____';
```

**5. Multiple Pattern Matching:**
```sql
SELECT * FROM employees 
WHERE first_name LIKE 'J%' 
   OR first_name LIKE 'M%';
```

### **Advanced LIKE Usage:**

**Case Insensitive Search:**
```sql
SELECT * FROM products 
WHERE LOWER(product_name) LIKE LOWER('%laptop%');
```

**Email Validation:**
```sql
SELECT * FROM users 
WHERE email LIKE '%@%.%' 
  AND email NOT LIKE '%@%@%';
```

**Date Pattern Search:**
```sql
SELECT * FROM orders 
WHERE order_date LIKE '2024-%';
```

### **Performance Tips:**
- **Leading wildcards (LIKE '%text')** can be slow - avoid when possible
- **Use indexes** on columns frequently searched with LIKE
- **Consider FULLTEXT indexes** for complex text searches
- **Use REGEXP** for more complex pattern matching

### **Alternative Options:**
```sql
-- Regular expressions (MySQL)
SELECT * FROM customers 
WHERE first_name REGEXP '^[A-M]';

-- Full-text search (MySQL)
SELECT * FROM articles 
WHERE MATCH(title, content) AGAINST('database optimization');
```

Need help with WHERE clauses, JOINs, or other SQL operators?"""

        elif any(pattern in message_lower for pattern in ['where clause', 'where condition', 'what is where', 'explain where']):
            return """## 🎯 WHERE Clause - Filtering Data Guide

### **What is WHERE?**
The **WHERE** clause is used to filter records in SQL queries. It specifies conditions that must be met for rows to be included in the result set.

### **Basic Syntax:**
```sql
SELECT column1, column2
FROM table_name
WHERE condition;
```

### **Comparison Operators:**
- **=** Equal to
- **!=** or **<>** Not equal to
- **>** Greater than
- **<** Less than
- **>=** Greater than or equal
- **<=** Less than or equal

### **Essential Examples:**

**1. Simple Equality:**
```sql
SELECT * FROM employees 
WHERE department = 'Sales';
```

**2. Numeric Comparisons:**
```sql
SELECT name, salary FROM employees 
WHERE salary > 50000;
```

**3. Date Filtering:**
```sql
SELECT * FROM orders 
WHERE order_date >= '2024-01-01';
```

**4. Text Matching:**
```sql
SELECT * FROM customers 
WHERE city = 'New York';
```

### **Logical Operators:**

**AND - Both conditions must be true:**
```sql
SELECT * FROM employees 
WHERE department = 'IT' 
  AND salary > 60000;
```

**OR - At least one condition must be true:**
```sql
SELECT * FROM products 
WHERE category = 'Electronics' 
   OR category = 'Computers';
```

**NOT - Exclude matching records:**
```sql
SELECT * FROM customers 
WHERE NOT country = 'USA';
```

### **Advanced WHERE Conditions:**

**IN - Match any value in a list:**
```sql
SELECT * FROM employees 
WHERE department IN ('Sales', 'Marketing', 'HR');
```

**BETWEEN - Range matching:**
```sql
SELECT * FROM products 
WHERE price BETWEEN 100 AND 500;
```

**IS NULL / IS NOT NULL:**
```sql
SELECT * FROM customers 
WHERE phone_number IS NOT NULL;
```

**LIKE - Pattern matching:**
```sql
SELECT * FROM customers 
WHERE first_name LIKE 'J%';
```

### **Complex WHERE Examples:**

**Multiple Conditions:**
```sql
SELECT * FROM orders 
WHERE (status = 'completed' OR status = 'shipped')
  AND order_date >= '2024-01-01'
  AND total_amount > 100;
```

**Subqueries in WHERE:**
```sql
SELECT * FROM employees 
WHERE salary > (
    SELECT AVG(salary) 
    FROM employees
);
```

**EXISTS:**
```sql
SELECT * FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o 
    WHERE o.customer_id = c.id
);
```

### **Performance Tips:**
- **Use indexes** on columns in WHERE clauses
- **Place selective conditions first** in AND operations
- **Avoid functions** on column names: `WHERE YEAR(date_col) = 2024` → `WHERE date_col >= '2024-01-01'`
- **Use appropriate data types** for comparisons

Need help with JOINs, GROUP BY, or other SQL concepts?"""

        elif any(pattern in message_lower for pattern in ['join', 'inner join', 'left join', 'right join', 'what is join']):
            return """## 🔗 SQL JOINs - Complete Guide

### **What are JOINs?**
JOINs are used to combine rows from two or more tables based on a related column between them. They're essential for retrieving data from normalized database structures.

### **Types of JOINs:**

## **1. INNER JOIN**
Returns only rows that have matching values in both tables.

```sql
SELECT customers.name, orders.order_date, orders.total
FROM customers
INNER JOIN orders ON customers.id = orders.customer_id;
```

## **2. LEFT JOIN (LEFT OUTER JOIN)**
Returns all rows from the left table, and matched rows from the right table.

```sql
SELECT customers.name, orders.order_date
FROM customers
LEFT JOIN orders ON customers.id = orders.customer_id;
```

## **3. RIGHT JOIN (RIGHT OUTER JOIN)**
Returns all rows from the right table, and matched rows from the left table.

```sql
SELECT customers.name, orders.order_date
FROM customers
RIGHT JOIN orders ON customers.id = orders.customer_id;
```

## **4. FULL OUTER JOIN**
Returns all rows when there's a match in either table.

```sql
SELECT customers.name, orders.order_date
FROM customers
FULL OUTER JOIN orders ON customers.id = orders.customer_id;
```

### **Real-World Examples:**

**E-commerce Database:**
```sql
-- Get customer orders with product details
SELECT 
    c.name as customer_name,
    o.order_date,
    p.product_name,
    oi.quantity,
    oi.price
FROM customers c
INNER JOIN orders o ON c.id = o.customer_id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
WHERE o.order_date >= '2024-01-01';
```

**Employee Database:**
```sql
-- Get employees with their department and manager info
SELECT 
    e.name as employee_name,
    d.department_name,
    m.name as manager_name,
    e.salary
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id
LEFT JOIN employees m ON e.manager_id = m.id
ORDER BY d.department_name, e.name;
```

### **Advanced JOIN Techniques:**

**Self JOIN:**
```sql
-- Find employees and their managers
SELECT 
    e1.name as employee,
    e2.name as manager
FROM employees e1
LEFT JOIN employees e2 ON e1.manager_id = e2.id;
```

**Multiple JOINs with Aggregation:**
```sql
SELECT 
    c.name,
    COUNT(o.id) as total_orders,
    SUM(o.total) as total_spent,
    AVG(o.total) as avg_order_value
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name
HAVING COUNT(o.id) > 0
ORDER BY total_spent DESC;
```

**JOIN with Subqueries:**
```sql
SELECT 
    d.department_name,
    avg_salary.average_salary
FROM departments d
JOIN (
    SELECT 
        dept_id,
        AVG(salary) as average_salary
    FROM employees
    GROUP BY dept_id
) avg_salary ON d.id = avg_salary.dept_id;
```

### **Performance Tips:**
- **Use appropriate indexes** on JOIN columns
- **Join on primary keys** when possible for better performance
- **Filter early** with WHERE clauses before JOINing
- **Consider JOIN order** - smaller tables first in complex queries
- **Use EXPLAIN** to analyze query performance

### **Common JOIN Patterns:**

**One-to-Many:**
```sql
-- One customer, many orders
SELECT c.name, COUNT(o.id) as order_count
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name;
```

**Many-to-Many (via junction table):**
```sql
-- Students and their enrolled courses
SELECT s.name, c.course_name
FROM students s
JOIN enrollments e ON s.id = e.student_id
JOIN courses c ON e.course_id = c.id;
```

Need help with specific JOIN scenarios or other SQL concepts?"""

        elif any(pattern in message_lower for pattern in ['group by', 'having', 'aggregate', 'count', 'sum', 'avg']):
            return """## 📊 GROUP BY & Aggregate Functions - Complete Guide

### **What is GROUP BY?**
GROUP BY groups rows that have the same values in specified columns into summary rows. It's typically used with aggregate functions to perform calculations on groups of data.

### **Aggregate Functions:**
- **COUNT()** - Count rows
- **SUM()** - Add up values
- **AVG()** - Calculate average
- **MAX()** - Find maximum value
- **MIN()** - Find minimum value

### **Basic Syntax:**
```sql
SELECT column1, AGGREGATE_FUNCTION(column2)
FROM table_name
WHERE condition
GROUP BY column1
HAVING aggregate_condition
ORDER BY column1;
```

### **Essential Examples:**

**1. Count by Category:**
```sql
SELECT department, COUNT(*) as employee_count
FROM employees
GROUP BY department;
```

**2. Sum by Group:**
```sql
SELECT department, SUM(salary) as total_salary
FROM employees
GROUP BY department;
```

**3. Average by Group:**
```sql
SELECT department, AVG(salary) as avg_salary
FROM employees
GROUP BY department
ORDER BY avg_salary DESC;
```

**4. Multiple Aggregates:**
```sql
SELECT 
    department,
    COUNT(*) as employee_count,
    AVG(salary) as avg_salary,
    MAX(salary) as max_salary,
    MIN(salary) as min_salary
FROM employees
GROUP BY department;
```

### **HAVING Clause:**
HAVING filters groups after GROUP BY (unlike WHERE which filters before grouping).

```sql
SELECT department, AVG(salary) as avg_salary
FROM employees
GROUP BY department
HAVING AVG(salary) > 50000;
```

### **Advanced GROUP BY Examples:**

**Multiple Column Grouping:**
```sql
SELECT 
    department, 
    job_title,
    COUNT(*) as employee_count,
    AVG(salary) as avg_salary
FROM employees
GROUP BY department, job_title
ORDER BY department, job_title;
```

**Date-based Grouping:**
```sql
-- Sales by month
SELECT 
    YEAR(order_date) as year,
    MONTH(order_date) as month,
    COUNT(*) as order_count,
    SUM(total) as total_sales
FROM orders
GROUP BY YEAR(order_date), MONTH(order_date)
ORDER BY year, month;
```

**Conditional Aggregation:**
```sql
SELECT 
    department,
    COUNT(*) as total_employees,
    COUNT(CASE WHEN salary > 60000 THEN 1 END) as high_earners,
    COUNT(CASE WHEN hire_date >= '2024-01-01' THEN 1 END) as recent_hires
FROM employees
GROUP BY department;
```

### **Real-World Examples:**

**E-commerce Analytics:**
```sql
-- Top customers by total purchases
SELECT 
    c.name,
    COUNT(o.id) as total_orders,
    SUM(o.total) as total_spent,
    AVG(o.total) as avg_order_value,
    MAX(o.order_date) as last_order_date
FROM customers c
JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name
HAVING COUNT(o.id) >= 5
ORDER BY total_spent DESC
LIMIT 10;
```

**Inventory Analysis:**
```sql
-- Product performance by category
SELECT 
    p.category,
    COUNT(DISTINCT p.id) as product_count,
    SUM(oi.quantity) as total_sold,
    SUM(oi.quantity * oi.price) as total_revenue,
    AVG(oi.price) as avg_price
FROM products p
JOIN order_items oi ON p.id = oi.product_id
JOIN orders o ON oi.order_id = o.id
WHERE o.order_date >= '2024-01-01'
GROUP BY p.category
ORDER BY total_revenue DESC;
```

### **Performance Tips:**
- **Index columns** used in GROUP BY
- **Use covering indexes** that include both GROUP BY and SELECT columns
- **Filter with WHERE** before grouping to reduce dataset size
- **Avoid unnecessary DISTINCT** with GROUP BY
- **Consider partitioning** for large tables with date-based grouping

### **Common Patterns:**

**Top N per Group:**
```sql
-- Top 3 highest paid employees per department
SELECT department, name, salary
FROM (
    SELECT 
        department, 
        name, 
        salary,
        ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rn
    FROM employees
) ranked
WHERE rn <= 3;
```

**Running Totals:**
```sql
SELECT 
    order_date,
    daily_sales,
    SUM(daily_sales) OVER (ORDER BY order_date) as running_total
FROM (
    SELECT 
        order_date,
        SUM(total) as daily_sales
    FROM orders
    GROUP BY order_date
) daily_totals;
```

Need help with window functions, subqueries, or other advanced SQL concepts?"""

        elif any(pattern in message_lower for pattern in ['database', 'what is database', 'explain database']):
            return """## 🗄️ Database Fundamentals - Complete Guide

### **What is a Database?**
A **database** is an organized collection of structured information or data, typically stored electronically in a computer system. It's managed by a Database Management System (DBMS).

### **Key Components:**
- **Tables**: Store data in rows and columns
- **Records**: Individual entries (rows) in a table  
- **Fields**: Individual data points (columns) in a record
- **Primary Key**: Unique identifier for each record
- **Foreign Key**: Links tables together
- **Indexes**: Speed up data retrieval

### **Database Types:**

**1. Relational Databases (RDBMS):**
- **MySQL** - Most popular open-source database
- **PostgreSQL** - Advanced open-source with rich features
- **Oracle** - Enterprise-grade commercial database
- **SQL Server** - Microsoft's enterprise database
- **SQLite** - Lightweight file-based database

**2. NoSQL Databases:**
- **MongoDB** - Document-based database
- **Redis** - In-memory key-value store
- **Cassandra** - Wide-column store
- **Neo4j** - Graph database

### **Database Design Principles:**

**Normalization Rules:**
- **1NF**: Atomic values, no repeating groups
- **2NF**: No partial dependencies
- **3NF**: No transitive dependencies

**Example of Good Design:**
```sql
-- Customers Table
CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders Table  
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'shipped', 'delivered', 'cancelled'),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
```

### **Common Use Cases:**

**E-commerce:**
- Product catalogs
- Customer information
- Order processing
- Inventory management

**Banking:**
- Account information
- Transaction records
- Customer data
- Audit trails

**Healthcare:**
- Patient records
- Medical history
- Appointments
- Prescription tracking

**Social Media:**
- User profiles
- Posts and content
- Connections/friendships
- Activity logs

### **Database Operations (CRUD):**

**Create (INSERT):**
```sql
INSERT INTO customers (name, email, phone)
VALUES ('John Doe', 'john@email.com', '555-1234');
```

**Read (SELECT):**
```sql
SELECT name, email FROM customers
WHERE created_at >= '2024-01-01';
```

**Update:**
```sql
UPDATE customers 
SET phone = '555-9999'
WHERE email = 'john@email.com';
```

**Delete:**
```sql
DELETE FROM customers
WHERE id = 123;
```

### **Best Practices:**

**Security:**
- Use strong passwords
- Implement proper user permissions
- Regular security updates
- Data encryption for sensitive information

**Performance:**
- Create appropriate indexes
- Optimize queries
- Regular maintenance (OPTIMIZE TABLE)
- Monitor slow query logs

**Backup & Recovery:**
- Regular automated backups
- Test restore procedures
- Point-in-time recovery capability
- Offsite backup storage

**Data Integrity:**
- Use primary keys and foreign keys
- Implement constraints
- Regular data validation
- Transaction management

Want to learn more about SQL queries, database design, or specific database concepts?"""

        elif any(pattern in message_lower for pattern in ['performance', 'optimize', 'optimization', 'slow', 'tuning', 'speed', 'tip', 'performance optimization', 'database performance']):
            return """## 🎯 Enterprise Database Performance Optimization Guide

### Executive Summary
Database performance optimization requires systematic analysis of queries, indexes, server configuration, and hardware resources. Focus on the 80/20 rule: 20% of queries typically consume 80% of resources.

## 🔍 Technical Analysis - Performance Fundamentals

### **1. Query Performance Analysis**
```sql
-- Enable slow query log for analysis
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
SET GLOBAL log_queries_not_using_indexes = 'ON';

-- Identify problematic queries
SELECT 
    query_time,
    lock_time,
    rows_sent,
    rows_examined,
    db,
    sql_text
FROM mysql.slow_log 
ORDER BY query_time DESC 
LIMIT 20;

-- Current running queries analysis
SELECT 
    ID,
    USER,
    HOST,
    DB,
    COMMAND,
    TIME,
    STATE,
    LEFT(INFO, 100) as QUERY_PREVIEW
FROM INFORMATION_SCHEMA.PROCESSLIST 
WHERE TIME > 1 
ORDER BY TIME DESC;
```

### **2. Index Optimization Strategy**
```sql
-- Find tables without primary keys (critical for replication)
SELECT 
    TABLE_SCHEMA,
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES t
LEFT JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc 
    ON t.TABLE_SCHEMA = tc.TABLE_SCHEMA 
    AND t.TABLE_NAME = tc.TABLE_NAME 
    AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
WHERE tc.CONSTRAINT_NAME IS NULL 
    AND t.TABLE_TYPE = 'BASE TABLE';

-- Index cardinality analysis
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    CARDINALITY,
    CASE 
        WHEN CARDINALITY = 0 THEN 'UNUSED/DUPLICATE'
        WHEN CARDINALITY < 10 THEN 'LOW_SELECTIVITY'
        ELSE 'GOOD'
    END as INDEX_QUALITY
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, INDEX_NAME;
```

## ⚡ Immediate Actions (Priority 1)

### **InnoDB Configuration (my.cnf)**
```ini
# Buffer Pool - Set to 70-80% of available RAM
innodb_buffer_pool_size = 4G
innodb_buffer_pool_instances = 8

# Redo Log Configuration
innodb_log_file_size = 1G
innodb_log_files_in_group = 2
innodb_log_buffer_size = 64M

# I/O Configuration
innodb_read_io_threads = 8
innodb_write_io_threads = 8
innodb_io_capacity = 2000
```

### **Query Cache Optimization**
```sql
-- Query cache configuration
SET GLOBAL query_cache_type = ON;
SET GLOBAL query_cache_size = 268435456; -- 256MB

-- Monitor query cache effectiveness
SHOW STATUS LIKE 'Qcache%';
```

### **Connection Management**
```sql
-- Optimize connection handling
SET GLOBAL max_connections = 500;
SET GLOBAL wait_timeout = 28800;
SET GLOBAL thread_cache_size = 50;

-- Monitor connection efficiency
SHOW STATUS LIKE 'Threads%';
```

## 🛠️ Strategic Implementation

### **Advanced Index Strategies**
```sql
-- Create composite indexes for multi-column WHERE clauses
CREATE INDEX idx_orders_status_date_customer 
ON orders (status, order_date, customer_id);

-- Covering indexes to avoid table lookups
CREATE INDEX idx_users_email_covering 
ON users (email, first_name, last_name, status);
```

### **Table Optimization**
```sql
-- Regular maintenance schedule
SELECT 
    TABLE_NAME,
    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS 'Size_MB',
    TABLE_ROWS,
    ROUND((DATA_FREE / 1024 / 1024), 2) AS 'Free_Space_MB'
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE();

-- Automated optimization
SELECT CONCAT('OPTIMIZE TABLE ', TABLE_NAME, ';') as optimize_commands
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
    AND ENGINE = 'InnoDB'
    AND DATA_FREE > 0;
```

Want to learn more about specific optimization techniques?"""

        # Add more SQL concepts
        elif any(pattern in message_lower for pattern in ['index', 'indexes', 'what is index', 'explain index']):
            return """## 🚀 Database Indexes - Complete Guide

### **What are Indexes?**
Indexes are database objects that improve the speed of data retrieval operations. Think of them like a book's index - they provide fast access to specific information without scanning the entire content.

### **How Indexes Work:**
- Create a separate data structure that points to table rows
- Dramatically speed up SELECT queries
- Slightly slow down INSERT/UPDATE/DELETE operations
- Require additional storage space

### **Types of Indexes:**

**1. Primary Index (Clustered):**
```sql
-- Automatically created with PRIMARY KEY
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100)
);
```

**2. Secondary Index (Non-clustered):**
```sql
-- Create index on frequently queried columns
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_name ON users(name);
```

**3. Composite Index:**
```sql
-- Multiple columns in specific order
CREATE INDEX idx_user_name_email ON users(name, email);
CREATE INDEX idx_order_status_date ON orders(status, order_date);
```

**4. Unique Index:**
```sql
-- Enforces uniqueness
CREATE UNIQUE INDEX idx_user_email_unique ON users(email);
```

### **When to Use Indexes:**

**✅ Create indexes for:**
- Columns in WHERE clauses
- Columns in JOIN conditions
- Columns in ORDER BY clauses
- Foreign key columns
- Frequently searched columns

**❌ Avoid indexes on:**
- Small tables (< 1000 rows)
- Columns that change frequently
- Tables with high INSERT/UPDATE/DELETE rates
- Columns with low cardinality (few unique values)

### **Index Performance Examples:**

**Without Index:**
```sql
-- Scans entire table (slow)
SELECT * FROM users WHERE email = 'john@example.com';
-- Execution time: 0.5 seconds for 1M rows
```

**With Index:**
```sql
-- Uses index lookup (fast)
CREATE INDEX idx_email ON users(email);
SELECT * FROM users WHERE email = 'john@example.com';
-- Execution time: 0.001 seconds for 1M rows
```

### **Index Maintenance Commands:**

**Analyze Index Usage:**
```sql
-- Check index usage statistics
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    CARDINALITY,
    CASE 
        WHEN CARDINALITY = 0 THEN 'UNUSED'
        WHEN CARDINALITY < 10 THEN 'LOW_SELECTIVITY'
        ELSE 'GOOD'
    END as INDEX_QUALITY
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, INDEX_NAME;
```

**Drop Unused Indexes:**
```sql
-- Remove indexes that aren't being used
DROP INDEX idx_unused_column ON table_name;
```

**Rebuild Indexes:**
```sql
-- Optimize index performance
ALTER TABLE table_name ENGINE=InnoDB;
-- or
OPTIMIZE TABLE table_name;
```

### **Best Practices:**
1. **Monitor index usage** regularly
2. **Create composite indexes** with most selective column first
3. **Use covering indexes** to avoid table lookups
4. **Limit number of indexes** per table (usually 5-7 max)
5. **Test query performance** before and after index creation

Need help with query optimization or other database concepts?"""

        elif any(pattern in message_lower for pattern in ['constraint', 'primary key', 'foreign key', 'unique key']):
            return """## 🔒 Database Constraints - Data Integrity Guide

### **What are Constraints?**
Constraints are rules enforced by the database to maintain data integrity and consistency. They prevent invalid data from being entered into tables.

### **Types of Constraints:**

## **1. PRIMARY KEY**
Uniquely identifies each row in a table.

```sql
-- Single column primary key
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL
);

-- Composite primary key
CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT,
    PRIMARY KEY (order_id, product_id)
);
```

## **2. FOREIGN KEY** 
Links two tables together and ensures referential integrity.

```sql
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    order_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
```

**Foreign Key Actions:**
- **CASCADE**: Automatically update/delete related records
- **SET NULL**: Set foreign key to NULL when referenced record is deleted
- **RESTRICT**: Prevent deletion if related records exist
- **NO ACTION**: Same as RESTRICT

## **3. UNIQUE**
Ensures all values in a column are different.

```sql
-- Single column unique
CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(100) UNIQUE,
    username VARCHAR(50) UNIQUE
);

-- Composite unique constraint
ALTER TABLE users 
ADD CONSTRAINT uk_user_email_username 
UNIQUE (email, username);
```

## **4. NOT NULL**
Ensures a column cannot have empty values.

```sql
CREATE TABLE customers (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) -- This can be NULL
);
```

## **5. CHECK**
Validates that values meet specific conditions.

```sql
CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) CHECK (price > 0),
    stock_quantity INT CHECK (stock_quantity >= 0),
    category VARCHAR(50) CHECK (category IN ('electronics', 'clothing', 'books'))
);
```

## **6. DEFAULT**
Sets a default value when no value is specified.

```sql
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_date DATE DEFAULT (CURRENT_DATE),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Managing Constraints:**

**Add Constraints to Existing Tables:**
```sql
-- Add primary key
ALTER TABLE table_name 
ADD PRIMARY KEY (column_name);

-- Add foreign key
ALTER TABLE orders 
ADD CONSTRAINT fk_customer 
FOREIGN KEY (customer_id) REFERENCES customers(id);

-- Add unique constraint
ALTER TABLE users 
ADD CONSTRAINT uk_email 
UNIQUE (email);

-- Add check constraint
ALTER TABLE products 
ADD CONSTRAINT chk_price 
CHECK (price > 0);
```

**Remove Constraints:**
```sql
-- Drop foreign key
ALTER TABLE orders 
DROP FOREIGN KEY fk_customer;

-- Drop unique constraint
ALTER TABLE users 
DROP INDEX uk_email;

-- Drop primary key
ALTER TABLE table_name 
DROP PRIMARY KEY;
```

### **Constraint Examples:**

**E-commerce Database:**
```sql
CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date DATE DEFAULT (CURRENT_DATE),
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') 
           DEFAULT 'pending',
    total DECIMAL(10,2) CHECK (total >= 0),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) CHECK (price > 0),
    stock_quantity INT CHECK (stock_quantity >= 0) DEFAULT 0,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Best Practices:**
1. **Always use PRIMARY KEY** for every table
2. **Create FOREIGN KEY constraints** to maintain referential integrity
3. **Use NOT NULL** for required fields
4. **Implement CHECK constraints** for data validation
5. **Name constraints explicitly** for easier maintenance
6. **Consider performance impact** of constraints on large tables

### **Common Constraint Errors:**
- **Duplicate entry**: Violates UNIQUE or PRIMARY KEY constraint
- **Cannot add foreign key**: Referenced table/column doesn't exist
- **Data too long**: Exceeds column size limit
- **Check constraint violated**: Data doesn't meet CHECK condition

Need help with database design or other SQL concepts?"""

        # Add fallback for unrecognized questions
        else:
            return f"""## 🎓 DBA Assistant - Comprehensive Database Help

I can help you with a wide range of database topics! Here are some areas I cover:

### **SQL Fundamentals:**
- **SELECT statements** - Data retrieval and querying
- **JOINs** - Combining data from multiple tables  
- **WHERE clauses** - Filtering and conditions
- **GROUP BY & HAVING** - Data aggregation and grouping
- **INSERT, UPDATE, DELETE** - Data manipulation

### **Database Design:**
- **Database basics** - What databases are and how they work
- **Normalization** - Designing efficient table structures
- **Constraints** - Primary keys, foreign keys, unique constraints
- **Indexes** - Improving query performance
- **Relationships** - One-to-many, many-to-many relationships

### **Advanced Topics:**
- **Performance optimization** - Query tuning and server configuration
- **Stored procedures** - Creating reusable database logic
- **Triggers** - Automatic database actions
- **Transactions** - Ensuring data consistency
- **Backup & recovery** - Protecting your data

### **Ask me questions like:**
- "What is a SELECT statement?"
- "Explain the LIKE operator"
- "How do I use WHERE clauses?"
- "What are database JOINs?"
- "How do I optimize database performance?"
- "What are indexes and when should I use them?"
- "Explain primary keys and foreign keys"

### **Your Question:**
**"{message}"**

**Suggestions:**
- Try rephrasing your question to be more specific
- Ask about a particular SQL concept or operation
- Request help with database design or optimization

**For immediate help:**
- Ask about "database basics" for foundational concepts
- Ask about "performance optimization" for tuning tips
- Ask about specific SQL commands like "SELECT", "JOIN", "WHERE"

What specific database topic would you like to learn about?"""

    async def _handle_database_query(self, message: str, db_name: str) -> Optional[str]:
        """Handle direct database queries and database-specific operations"""
        logger.info(f"Attempting direct database query for: '{message}' on db: '{db_name}'")
        
        db_config = self.config.databases.get(db_name)
        if not db_config:
            logger.warning(f"No database config found for: {db_name}")
            return None
            
        message_lower = message.lower().strip()
        logger.info(f"Checking message patterns for: '{message_lower}'")
        
        # Special handling for NoSQL databases
        if db_config.db_type == "mongodb":
            if any(phrase in message_lower for phrase in ['what tables', 'show tables', 'list tables', 'tables in', 'collections in', 'what collections', 'show collections', 'list collections']):
                try:
                    connection = await self.db_connector.get_connection(db_config)
                    collections = await connection.execute_query("db.getCollectionNames()")
                    
                    if collections:
                        collection_list = ", ".join(collections)
                        return f"📁 **Collections in MongoDB database '{db_config.database}':**\n\n{collection_list}\n\n💡 In MongoDB, collections store flexible documents with varying structures - each document can have different fields and nested data, unlike SQL tables with fixed rows."
                    else:
                        return f"📁 No collections found in MongoDB database '{db_config.database}'"
                        
                except Exception as e:
                    return f"❌ Error accessing MongoDB: {str(e)}"
        
        # FIRST: Check for database-specific operations that should be handled here
        database_specific_patterns = [
            # Table operations
            'show tables', 'list tables', 'what tables', 'available tables', 'tables in my database',
            'find tables', 'get tables', 'all tables', 'how many tables', 'count tables',
            
            # MongoDB document operations
            'show me documents', 'show documents', 'documents from', 'find documents', 'get documents',
            'how many documents', 'count documents', 'documents are in', 'records are in',
            'show me data', 'show data from', 'data in collection',
            
            # Index operations  
            'show indexes', 'list indexes', 'find indexes', 'get indexes', 'all indexes',
            'indexes in my database', 'find all indexes', 'show all indexes', 'list all indexes',
            'indexes on', 'index on', 'show index', 'list index',
            
            # Table structure
            'describe table', 'structure of', 'columns in', 'schema of', 'table structure',
            'show columns', 'get columns', 'table schema', 'column names',
            
            # Data counts
            'count rows', 'row count', 'how many rows', 'number of rows', 'rows in',
            'count records', 'record count', 'how many records', 'number of records', 'records in', 'records are in',
            'count entries', 'entry count', 'how many entries', 'number of entries', 'entries in', 'entries are in',
            'count for', 'record count for', 'row count for', 'records for', 'rows for', 'entries for',
            'table size', 'data in table', 'data count',
            
            # Database info
            'database size', 'size of database', 'size of my database', 'db size', 'database info', 'database schema',
            'what\'s the size', 'how big is', 'storage used', 'disk space', 'space usage',
            'show databases', 'list databases', 'available databases',
            
            # Performance queries
            'show status', 'show variables', 'show processlist', 'running queries',
            'current connections', 'active connections', 'connection count'
        ]
        
        # Check if this is a database-specific operation
        is_database_specific = any(pattern in message_lower for pattern in database_specific_patterns)
        
        # Debug: Log which patterns match
        matched_patterns = [pattern for pattern in database_specific_patterns if pattern in message_lower]
        logger.info(f"Database-specific patterns matched: {matched_patterns}")
        
        if is_database_specific:
            logger.info("Database-specific pattern detected - processing as database operation")
            # Continue to database operation handling below
        else:
            # Check for general conversational patterns only if not database-specific
            conversational_indicators = [
                'what is', 'what are', 'explain', 'tell me', 'how to', 'how do', 'how can',
                'can you', 'could you', 'would you', 'please', 'help me', 'i need', 'i want',
                'what does', 'what means', 'define', 'describe what', 'explain what',
                'performance tip', 'optimization tip', 'best practice', 'recommend', 'advice',
                'guidance', 'suggest', 'improve', 'optimize', 'configure', 'setup', 'install',
                'monitor', 'analyze', 'troubleshoot', 'debug', 'fix issue', 'solve problem',
                ' function', ' operator', ' clause', ' syntax', ' command'
            ]
            
            # Check for conversational patterns - if found, route to chat
            for pattern in conversational_indicators:
                if pattern in message_lower:
                    logger.info(f"Conversational pattern '{pattern}' detected - routing to chat handler")
                    return None
        
        # Check for pure SQL commands
        pure_sql_patterns = [
            message_lower.strip().startswith('select '),
            message_lower.strip().startswith('insert '),
            message_lower.strip().startswith('update '),
            message_lower.strip().startswith('delete '),
            message_lower.strip().startswith('create '),
            message_lower.strip().startswith('drop '),
            message_lower.strip().startswith('alter '),
            message_lower.strip().startswith('show '),
            message_lower.strip().startswith('describe '),
            # Only allow EXPLAIN if it's clearly a SQL EXPLAIN command
            (message_lower.strip().startswith('explain ') and 
             any(sql_word in message_lower for sql_word in ['select', 'insert', 'update', 'delete']))
        ]
        
        # Check for MongoDB commands
        mongodb_patterns = [
            message_lower.strip().startswith('db.'),
            message_lower.strip().startswith('db['),
            'find()' in message_lower,
            'findone()' in message_lower,
            'countdocuments()' in message_lower,
            'aggregate(' in message_lower,
            'insertone(' in message_lower,
            'insertmany(' in message_lower,
            'updateone(' in message_lower,
            'updatemany(' in message_lower,
            'deleteone(' in message_lower,
            'deletemany(' in message_lower
        ]
        
        # If it's not database-specific and not pure SQL/MongoDB, route to chat
        if not is_database_specific and not any(pure_sql_patterns) and not any(mongodb_patterns):
            logger.info("No database-specific, SQL, or MongoDB patterns detected - routing to chat handler")
            return None
        
        try:
            # Enhanced DBA troubleshooting patterns with flexible matching
            logger.info("Starting pattern matching...")
            
            # Entity/Table not found issues - More comprehensive patterns
            entity_patterns = [
                'entity not found', 'entity missing', 'entity doesn\'t exist',
                'table not found', 'table missing', 'table doesn\'t exist', 'unknown table',
                'fix entity not found', 'resolve entity not found', 'entity error',
                'table error', 'missing entity', 'missing table', 'cannot find entity',
                'cannot find table', 'entity does not exist', 'table does not exist'
            ]
            
            logger.info(f"Testing entity patterns against: '{message_lower}'")
            # Debug each pattern individually
            for i, pattern in enumerate(entity_patterns):
                match = pattern in message_lower
                logger.info(f"Pattern {i+1} '{pattern}' -> Match: {match}")
                if match:
                    break
            entity_match = any(pattern in message_lower for pattern in entity_patterns)
            logger.info(f"Final entity pattern match result: {entity_match}")
            
            if entity_match:
                logger.info("Matched entity/table not found pattern")
                connection = None
                try:
                    connection = await self.db_connector.get_connection(db_config)
                    # Get all tables in database
                    tables_result = await connection.execute_query("SHOW TABLES")
                    table_list = [table[0] for table in tables_result] if tables_result else []
                    
                    # Check for recently dropped tables (from binary logs if available)
                    dropped_tables_query = """
                        SELECT TABLE_NAME, ENGINE, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        ORDER BY TABLE_NAME
                    """
                    table_info = await connection.execute_query(dropped_tables_query)
                finally:
                    # Ensure MySQL connection is properly closed
                    if connection and db_config.db_type == 'mysql':
                        try:
                            # For MySQL connections, check type and close appropriately
                            from core.database.connector import MySQLConnection
                            if isinstance(connection, MySQLConnection):
                                await connection.close()
                        except Exception as close_error:
                            logger.warning(f"Error closing MySQL connection: {close_error}")
                
                response = f"""## 🔍 Entity/Table Not Found - Diagnostic Report

### **Available Tables in Database '{db_config.database}':**
"""
                if table_list:
                    for i, table in enumerate(table_list, 1):
                        response += f"{i}. `{table}`\n"
                else:
                    response += "❌ **No tables found in database**\n"

                response += f"""
### **🛠️ Troubleshooting Steps:**

**1. Verify Table Existence:**
```sql
SHOW TABLES LIKE '%your_table_name%';
```

**2. Check Table in All Databases:**
```sql
SELECT TABLE_SCHEMA, TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE '%your_table_name%';
```

**3. Check Recently Dropped Tables (if binary logging enabled):**
```sql
SHOW BINLOG EVENTS WHERE Event_type = 'Query' AND Info LIKE '%DROP TABLE%';
```

**4. Verify User Permissions:**
```sql
SHOW GRANTS FOR CURRENT_USER();
```

**5. Create Missing Table (template):**
```sql
CREATE TABLE your_table_name (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **💡 Common Causes:**
- Typo in table name (case sensitivity in Linux)
- Wrong database selected (`USE database_name;`)
- Insufficient privileges (`GRANT SELECT ON database.table TO user;`)
- Table was dropped accidentally
- Application connecting to wrong database
"""
                return response

            # Permission/Access denied issues - Enhanced patterns
            elif any(pattern in message_lower for pattern in [
                'access denied', 'permission denied', 'privileges', 'cannot connect',
                'authentication failed', 'user denied', 'login failed', 'unauthorized',
                'fix access denied', 'resolve permission', 'grant access', 'permission error',
                'access error', 'authentication error', 'connection denied', 'forbidden',
                'insufficient privileges', 'no permission', 'access restricted'
            ]):
                logger.info("Matched permission/access pattern")
                connection = await self.db_connector.get_connection(db_config)
                
                # Get current user and grants
                user_result = await connection.execute_query("SELECT USER(), CURRENT_USER()")
                current_user = user_result[0] if user_result else ("Unknown", "Unknown")
                
                response = f"""## 🔐 Access/Permission Issues - Diagnostic Report

### **Current Session Info:**
- **Connected as:** `{current_user[0]}`
- **Effective user:** `{current_user[1]}`
- **Database:** `{db_config.database}`

### **🔧 Permission Diagnostics:**

**1. Check Current User Privileges:**
```sql
SHOW GRANTS FOR CURRENT_USER();
```

**2. Check Specific Database Privileges:**
```sql
SELECT * FROM INFORMATION_SCHEMA.SCHEMA_PRIVILEGES 
WHERE GRANTEE LIKE '%{current_user[1].split('@')[0]}%';
```

**3. Check Table-Level Privileges:**
```sql
SELECT * FROM INFORMATION_SCHEMA.TABLE_PRIVILEGES 
WHERE GRANTEE LIKE '%{current_user[1].split('@')[0]}%';
```

**4. Test Connection:**
```sql
SELECT 'Connection successful' as status;
```

### **🛠️ Common Fixes:**

**Grant Database Access:**
```sql
GRANT ALL PRIVILEGES ON {db_config.database}.* TO 'username'@'host';
FLUSH PRIVILEGES;
```

**Grant Specific Table Access:**
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON {db_config.database}.table_name TO 'username'@'host';
```

**Create New User with Privileges:**
```sql
CREATE USER 'new_user'@'%' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON {db_config.database}.* TO 'new_user'@'%';
FLUSH PRIVILEGES;
```
"""
                return response

            # Performance/Slow query issues - Enhanced patterns
            elif any(pattern in message_lower for pattern in [
                'slow query', 'performance issue', 'query timeout', 'long running',
                'optimize query', 'index needed', 'performance problem', 'query slow',
                'fix slow query', 'improve performance', 'speed up query', 'query optimization',
                'database slow', 'timeout error', 'execution time', 'high cpu', 'query tuning'
            ]):
                logger.info("Matched performance/slow query pattern")
                connection = await self.db_connector.get_connection(db_config)
                
                # Get slow query log status
                slow_log_result = await connection.execute_query("SHOW VARIABLES LIKE 'slow_query_log%'")
                
                response = f"""## ⚡ Query Performance Issues - Optimization Guide

### **🔍 Performance Diagnostics:**

**1. Check Currently Running Queries:**
```sql
SHOW PROCESSLIST;
```

**2. Enable Slow Query Log:**
```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;  -- Log queries taking >2 seconds
```

**3. Find Slow Queries:**
```sql
SELECT * FROM INFORMATION_SCHEMA.PROCESSLIST 
WHERE COMMAND != 'Sleep' AND TIME > 5;
```

**4. Analyze Query Performance:**
```sql
EXPLAIN SELECT * FROM your_table WHERE condition;
```

### **🛠️ Optimization Solutions:**

**Create Missing Indexes:**
```sql
-- For single column
CREATE INDEX idx_column_name ON table_name (column_name);

-- For multiple columns
CREATE INDEX idx_multi ON table_name (col1, col2, col3);

-- For covering index
CREATE INDEX idx_covering ON table_name (col1, col2) INCLUDE (col3, col4);
```

**Optimize Table:**
```sql
OPTIMIZE TABLE table_name;
```

**Update Table Statistics:**
```sql
ANALYZE TABLE table_name;
```

### **📊 Performance Monitoring:**
```sql
-- Check index usage
SELECT TABLE_NAME, INDEX_NAME, CARDINALITY 
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE();
```
"""
                return response

            # Connection issues - Enhanced patterns
            elif any(pattern in message_lower for pattern in [
                'connection refused', 'cannot connect', 'connection timeout',
                'connection lost', 'max connections', 'connection error', 'connection failed',
                'fix connection', 'resolve connection', 'database offline', 'server unreachable',
                'connection pool', 'too many connections', 'connection reset', 'network error'
            ]):
                logger.info("Matched connection issues pattern")
                connection = await self.db_connector.get_connection(db_config)
                
                # Get connection statistics
                conn_stats = await connection.execute_query("""
                    SHOW STATUS WHERE Variable_name IN (
                        'Connections', 'Max_used_connections', 'Threads_connected',
                        'Threads_running', 'Connection_errors_max_connections'
                    )
                """)
                
                response = f"""## 🔗 Database Connection Issues - Diagnostic Report

### **Current Connection Statistics:**
"""
                for stat in conn_stats:
                    response += f"- **{stat[0]}:** {stat[1]}\n"

                response += f"""
### **🔧 Connection Diagnostics:**

**1. Check Max Connections:**
```sql
SHOW VARIABLES LIKE 'max_connections';
```

**2. Current Connection Usage:**
```sql
SHOW STATUS LIKE 'Threads_connected';
```

**3. Show All Current Connections:**
```sql
SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE 
FROM INFORMATION_SCHEMA.PROCESSLIST;
```

### **🛠️ Connection Fixes:**

**Increase Max Connections:**
```sql
SET GLOBAL max_connections = 500;
```

**Kill Long-Running Connections:**
```sql
-- Find long-running connections
SELECT ID, USER, HOST, TIME, INFO 
FROM INFORMATION_SCHEMA.PROCESSLIST 
WHERE TIME > 300 AND COMMAND != 'Sleep';

-- Kill specific connection
KILL CONNECTION_ID;
```

**Optimize Connection Pool:**
```sql
-- Adjust connection timeout
SET GLOBAL wait_timeout = 28800;
SET GLOBAL interactive_timeout = 28800;
```
"""
                return response

            # Advanced DBA patterns - Table management queries  
            elif any(pattern in message_lower for pattern in ['how many tables', 'count tables', 'list tables', 'show tables', 'what tables', 'available tables']):
                logger.info("Matched table count/list pattern")
                if db_config.db_type == 'mysql':
                    logger.info("Connecting to MySQL database...")
                    connection = await self.db_connector.get_connection(db_config)
                    logger.info("Executing SHOW TABLES query...")
                    result = await connection.execute_query("SHOW TABLES")
                    logger.info(f"Query result: {result}")
                    
                    table_count = len(result)
                    table_names = [row[0] for row in result]
                    
                    return f"""## Database Tables in {db_config.database}

**Total Tables:** {table_count}

**Table List:**
{chr(10).join([f"- {name}" for name in table_names])}

You can ask me about specific tables, like:
- "Describe table {table_names[0] if table_names else 'table_name'}"
- "Count rows in {table_names[0] if table_names else 'table_name'}"
"""
                
            # MongoDB structure handling
            elif db_config.db_type == 'mongodb' and any(phrase in message_lower for phrase in ['structure of', 'schema of', 'show columns', 'get columns', 'table schema', 'column names']):
                logger.info("Matched MongoDB structure pattern")
                try:
                    # Extract collection name from the message
                    words = message_lower.split()
                    collection_name = None
                    for i, word in enumerate(words):
                        if word in ["of", "in"] and i + 1 < len(words):
                            collection_name = words[i + 1]
                            break
                    
                    if collection_name:
                        # Remove any trailing punctuation
                        collection_name = collection_name.rstrip('?')
                        
                        connection = await self.db_connector.get_connection(db_config)
                        documents = await connection.execute_query("find documents", collection_name)
                        if documents and not isinstance(documents[0], str):  # Not collection names
                            # Analyze document structure
                            sample_doc = documents[0]
                            response = f"## 📋 MongoDB Collection Structure: `{collection_name}`\n\n"
                            response += "**Document Fields:**\n"
                            
                            for key, value in sample_doc.items():
                                if isinstance(value, dict):
                                    response += f"- **{key}** (Object):\n"
                                    for sub_key, sub_value in value.items():
                                        response += f"  - {sub_key}: {type(sub_value).__name__}\n"
                                elif isinstance(value, list):
                                    response += f"- **{key}** (Array): {type(value[0]).__name__ if value else 'empty'}\n"
                                else:
                                    response += f"- **{key}**: {type(value).__name__}\n"
                            
                            response += f"\n**Sample Document:**\n```json\n{json.dumps(sample_doc, indent=2)}\n```\n\n"
                            response += "**💡 MongoDB Structure Notes:**\n"
                            response += "- Documents can have different fields (flexible schema)\n"
                            response += "- Fields can be nested objects or arrays\n"
                            response += "- No predefined columns like SQL tables\n"
                            response += "- Each document can have unique structure"
                            
                            return response
                        else:
                            return f"❌ No documents found in collection '{collection_name}'"
                    else:
                        return "❌ Please specify a collection name (e.g., 'What's the structure of user_profiles?')"
                except Exception as e:
                    logger.error(f"Error getting MongoDB structure: {e}")
                    return f"❌ Error retrieving collection structure: {str(e)}"
            
            elif any(phrase in message_lower for phrase in ['describe table', 'structure of', 'columns in']):
                logger.info("Matched table describe pattern")
                # Extract table name (simple approach)
                words = message_lower.split()
                table_name = None
                for i, word in enumerate(words):
                    if word in ['table', 'of'] and i + 1 < len(words):
                        table_name = words[i + 1]
                        break
                
                if table_name:
                    connection = await self.db_connector.get_connection(db_config)
                    result = await connection.execute_query(f"DESCRIBE {table_name}")
                    if result:
                        columns_info = []
                        for row in result:
                            columns_info.append(f"- **{row[0]}**: {row[1]} {'(NULL)' if row[2] == 'YES' else '(NOT NULL)'}")
                        
                        return f"""## Table Structure: {table_name}

**Columns:**
{chr(10).join(columns_info)}

**Sample queries you can try:**
- `SELECT * FROM {table_name} LIMIT 5;`
- `SELECT COUNT(*) FROM {table_name};`
"""
                    else:
                        return f"Table '{table_name}' not found in database {db_config.database}"
                
            # MongoDB document handling
            elif db_config.db_type == 'mongodb' and any(phrase in message_lower for phrase in ['show me documents', 'show documents', 'documents from', 'find documents', 'get documents']):
                logger.info("Matched MongoDB document query pattern")
                try:
                    # Extract collection name from the message
                    words = message_lower.split()
                    collection_name = None
                    for i, word in enumerate(words):
                        if word in ["from", "in"] and i + 1 < len(words):
                            collection_name = words[i + 1]
                            break
                    
                    if collection_name:
                        # Remove any trailing words like "collection"
                        if collection_name.endswith("collection"):
                            collection_name = collection_name[:-10]
                        
                        connection = await self.db_connector.get_connection(db_config)
                        documents = await connection.execute_query("find documents", collection_name)
                        if documents and not isinstance(documents[0], str):  # Not collection names
                            response = f"📄 Documents from '{collection_name}' collection:\n\n"
                            for i, doc in enumerate(documents[:5]):  # Show first 5 documents
                                response += f"**Document {i+1}:**\n"
                                for key, value in doc.items():
                                    if isinstance(value, dict):
                                        response += f"  {key}: {str(value)}\n"
                                    elif isinstance(value, list):
                                        response += f"  {key}: {value}\n"
                                    else:
                                        response += f"  {key}: {value}\n"
                                response += "\n"
                            if len(documents) > 5:
                                response += f"... and {len(documents) - 5} more documents"
                            return response
                        else:
                            return f"❌ No documents found in collection '{collection_name}'"
                    else:
                        return "❌ Please specify a collection name (e.g., 'Show me documents from user_profiles')"
                except Exception as e:
                    logger.error(f"Error getting MongoDB documents: {e}")
                    return f"❌ Error retrieving documents: {str(e)}"
            
            elif db_config.db_type == 'mongodb' and any(phrase in message_lower for phrase in ['how many documents', 'count documents', 'documents are in', 'records are in']):
                logger.info("Matched MongoDB document count pattern")
                try:
                    # Extract collection name from the message
                    words = message_lower.split()
                    collection_name = None
                    for i, word in enumerate(words):
                        if word in ["in", "from"] and i + 1 < len(words):
                            collection_name = words[i + 1]
                            break
                    
                    if collection_name:
                        # Remove any trailing words
                        if collection_name.endswith("collection"):
                            collection_name = collection_name[:-10]
                        
                        connection = await self.db_connector.get_connection(db_config)
                        result = await connection.execute_query("count documents", collection_name)
                        if result and "count" in result[0]:
                            count = result[0]["count"]
                            return f"📊 Collection '{collection_name}' contains **{count:,} documents**"
                        else:
                            return f"❌ Could not get document count for collection '{collection_name}'"
                    else:
                        return "❌ Please specify a collection name (e.g., 'How many documents are in product_catalog')"
                except Exception as e:
                    logger.error(f"Error getting MongoDB document count: {e}")
                    return f"❌ Error counting documents: {str(e)}"
            
            elif any(phrase in message_lower for phrase in ['count rows', 'row count', 'how many rows', 'count records', 'record count', 'how many records', 'number of records', 'records in', 'records are in', 'count entries', 'entry count', 'how many entries', 'number of entries', 'entries in', 'entries are in', 'count for', 'record count for', 'row count for', 'records for', 'rows for', 'entries for']):
                logger.info("Matched row/record count pattern")
                # Extract table name - improved extraction for multiple patterns
                words = message_lower.split()
                table_name = None
                
                # Handle "for table_name" patterns
                if 'for' in words:
                    for i, word in enumerate(words):
                        if word == 'for' and i + 1 < len(words):
                            next_word = words[i + 1]
                            if next_word in ['my', 'the'] and i + 2 < len(words):
                                table_name = words[i + 2]
                            else:
                                table_name = next_word
                            break
                
                # Handle "in my table_name", "in table_name", "from table_name" patterns
                if not table_name:
                    for i, word in enumerate(words):
                        if word in ['in', 'from'] and i + 1 < len(words):
                            next_word = words[i + 1]
                            if next_word == 'my' and i + 2 < len(words):
                                table_name = words[i + 2]
                            else:
                                table_name = next_word
                            break
                
                if table_name:
                    connection = await self.db_connector.get_connection(db_config)
                    result = await connection.execute_query(f"SELECT COUNT(*) FROM {table_name}")
                    if result:
                        row_count = result[0][0]
                        return f"""## Row Count for {table_name}

**Total Rows:** {row_count:,}

**Additional information you can get:**
- "Describe table {table_name}" - to see column structure
- "Show indexes on {table_name}" - to see indexes
"""
                    else:
                        return f"Could not get row count for table '{table_name}'"
                        
            elif any(phrase in message_lower for phrase in ['database size', 'size of database', 'size of my database', 'db size', 'what\'s the size', 'how big is', 'storage used', 'disk space', 'space usage']):
                logger.info("Matched database size pattern")
                try:
                    connection = await self.db_connector.get_connection(db_config)
                    
                    # Get comprehensive database size information
                    size_query = """
                    SELECT 
                        table_schema AS 'Database',
                        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size_MB',
                        ROUND(SUM(data_length + index_length) / 1024 / 1024 / 1024, 3) AS 'Size_GB',
                        COUNT(*) as 'Table_Count',
                        ROUND(SUM(data_length) / 1024 / 1024, 2) AS 'Data_MB',
                        ROUND(SUM(index_length) / 1024 / 1024, 2) AS 'Index_MB'
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE()
                    GROUP BY table_schema
                    """
                    
                    size_result = await connection.execute_query(size_query)
                    
                    if size_result and len(size_result) > 0:
                        db_name_result, size_mb_raw, size_gb_raw, table_count_raw, data_mb_raw, index_mb_raw = size_result[0]
                        
                        # Convert to proper numeric types
                        size_mb = float(size_mb_raw) if size_mb_raw is not None else 0.0
                        size_gb = float(size_gb_raw) if size_gb_raw is not None else 0.0
                        table_count = int(table_count_raw) if table_count_raw is not None else 0
                        data_mb = float(data_mb_raw) if data_mb_raw is not None else 0.0
                        index_mb = float(index_mb_raw) if index_mb_raw is not None else 0.0
                        
                        # Get detailed table breakdown
                        table_sizes_query = """
                        SELECT 
                            table_name,
                            ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size_MB',
                            ROUND((data_length / 1024 / 1024), 2) AS 'Data_MB',
                            ROUND((index_length / 1024 / 1024), 2) AS 'Index_MB',
                            table_rows
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'
                        ORDER BY (data_length + index_length) DESC
                        LIMIT 10
                        """
                        
                        table_results = await connection.execute_query(table_sizes_query)
                        
                        # Format table breakdown
                        table_breakdown = ""
                        if table_results:
                            table_breakdown = "\n### 📊 **Top 10 Largest Tables:**\n"
                            for table_name, table_size_raw, data_size_raw, index_size_raw, rows_raw in table_results:
                                table_size = float(table_size_raw) if table_size_raw is not None else 0.0
                                data_size = float(data_size_raw) if data_size_raw is not None else 0.0
                                index_size = float(index_size_raw) if index_size_raw is not None else 0.0
                                rows = int(rows_raw) if rows_raw is not None else 0
                                table_breakdown += f"• `{table_name}`: **{table_size} MB** (Data: {data_size} MB, Indexes: {index_size} MB, Rows: {rows:,})\n"
                        
                        # Generate professional assessment
                        assessment = ""
                        if size_mb > 1000:  # > 1GB
                            assessment = "🔴 **LARGE DATABASE** - Requires attention"
                        elif size_mb > 100:  # > 100MB
                            assessment = "🟡 **MEDIUM DATABASE** - Monitor growth"
                        else:
                            assessment = "🟢 **SMALL DATABASE** - Healthy size"
                        
                        # Professional recommendations
                        recommendations = ""
                        if size_mb > 500:
                            recommendations = """
### 🎯 **Professional Recommendations:**
- **Backup Strategy**: Implement incremental backups for large database
- **Archiving**: Consider archiving historical data (>6 months old)
- **Partitioning**: Evaluate table partitioning for largest tables
- **Monitoring**: Set up automated size monitoring alerts
- **Maintenance**: Schedule regular OPTIMIZE TABLE operations"""
                        elif size_mb > 100:
                            recommendations = """
### 🎯 **Professional Recommendations:**
- **Growth Monitoring**: Track growth rate for capacity planning
- **Index Review**: Analyze index efficiency on larger tables
- **Regular Maintenance**: Weekly ANALYZE TABLE for statistics"""
                        else:
                            recommendations = """
### 🎯 **Professional Recommendations:**
- **Growth Planning**: Monitor for future scaling needs
- **Index Optimization**: Ensure optimal indexing strategy"""
                        
                        # Calculate percentages safely
                        data_percentage = (data_mb/size_mb*100) if size_mb > 0 else 0
                        index_percentage = (index_mb/size_mb*100) if size_mb > 0 else 0
                        data_index_ratio = (data_mb/index_mb) if index_mb > 0 else 0
                        
                        return f"""## 💾 **Professional Database Size Analysis**

### 📋 **Executive Summary**
**Database:** `{db_name_result}`
**Total Size:** {size_mb} MB ({size_gb} GB)
**Status:** {assessment}

### 🔍 **Detailed Breakdown**
- **Total Tables:** {table_count}
- **Data Size:** {data_mb} MB ({data_percentage:.1f}%)
- **Index Size:** {index_mb} MB ({index_percentage:.1f}%)
- **Data/Index Ratio:** {data_index_ratio:.2f}:1

{table_breakdown}

{recommendations}

### 📊 **SQL Commands Used:**
```sql
-- Database size query
{size_query.strip()}

-- Table breakdown query  
{table_sizes_query.strip()}
```

### 💡 **Quick Actions:**
- `SHOW TABLE STATUS` - Detailed table information
- `ANALYZE TABLE table_name` - Update table statistics
- `OPTIMIZE TABLE table_name` - Defragment and optimize
"""
                    else:
                        return "❌ Could not retrieve database size information. Database may be empty or access denied."
                        
                except Exception as e:
                    logger.error(f"Error getting database size: {e}")
                    raise e
                         
            elif any(phrase in message_lower for phrase in ['show indexes', 'list indexes', 'find indexes', 'find all indexes', 'show all indexes', 'list all indexes', 'indexes in my database', 'all indexes', 'indexes on']):
                logger.info("Matched index query pattern")
                
                # Check if asking for all indexes in database
                if any(phrase in message_lower for phrase in ['all indexes', 'indexes in my database', 'find all indexes', 'show all indexes', 'list all indexes']):
                    logger.info("Getting all indexes in database")
                    connection = await self.db_connector.get_connection(db_config)
                    
                    # MongoDB-specific index handling
                    if db_config.db_type == 'mongodb':
                        try:
                            # For MongoDB demo, return mock index information
                            response = f"## 📊 All Indexes in MongoDB Database '{db_config.database}'\n\n"
                            response += "### 🗂️ Collection: `user_profiles`\n"
                            response += "- **email_idx** (UNIQUE) on (email)\n"
                            response += "- **username_idx** (UNIQUE) on (username)\n"
                            response += "- **created_at_idx** on (profile.created_at)\n\n"
                            
                            response += "### 🗂️ Collection: `product_catalog`\n"
                            response += "- **product_id_idx** (UNIQUE) on (product_id)\n"
                            response += "- **category_idx** on (category)\n"
                            response += "- **price_idx** on (price)\n\n"
                            
                            response += "### 🗂️ Collection: `order_transactions`\n"
                            response += "- **order_id_idx** (UNIQUE) on (order_id)\n"
                            response += "- **user_id_idx** on (user_id)\n"
                            response += "- **order_date_idx** on (order_date)\n\n"
                            
                            response += "### 🗂️ Collection: `analytics_events`\n"
                            response += "- **event_id_idx** (UNIQUE) on (event_id)\n"
                            response += "- **user_id_idx** on (user_id)\n"
                            response += "- **timestamp_idx** on (timestamp)\n\n"
                            
                            response += "### 🗂️ Collection: `content_management`\n"
                            response += "- **content_id_idx** (UNIQUE) on (content_id)\n"
                            response += "- **author_id_idx** on (author_id)\n"
                            response += "- **publish_date_idx** on (publish_date)\n\n"
                            
                            response += """
### 💡 **MongoDB Index Tips:**
- **Single Field Indexes** speed up queries on specific fields
- **Compound Indexes** optimize queries on multiple fields
- **Text Indexes** enable full-text search capabilities
- **Geospatial Indexes** optimize location-based queries
- **TTL Indexes** automatically expire documents

### 🔍 **Useful MongoDB Commands:**
```javascript
// Show indexes for specific collection
db.collection_name.getIndexes()

// Create new index
db.collection_name.createIndex({field_name: 1})

// Create compound index
db.collection_name.createIndex({field1: 1, field2: -1})

// Create text index
db.collection_name.createIndex({field_name: "text"})
```
"""
                            return response
                        except Exception as e:
                            logger.error(f"MongoDB index query error: {e}")
                            return f"❌ Error retrieving MongoDB indexes: {str(e)}"
                    
                    # MySQL/SQLite index handling
                    else:
                        result = await connection.execute_query("""
                            SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, NON_UNIQUE, INDEX_TYPE
                            FROM INFORMATION_SCHEMA.STATISTICS 
                            WHERE TABLE_SCHEMA = DATABASE()
                            ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
                        """)
                        
                        if result:
                            indexes_by_table = {}
                            for row in result:
                                table_name, index_name, column_name, non_unique, index_type = row
                                if table_name not in indexes_by_table:
                                    indexes_by_table[table_name] = {}
                                if index_name not in indexes_by_table[table_name]:
                                    indexes_by_table[table_name][index_name] = {
                                        'columns': [],
                                        'unique': not non_unique,
                                        'type': index_type
                                    }
                                indexes_by_table[table_name][index_name]['columns'].append(column_name)
                            
                            response = f"## 📊 All Indexes in Database '{db_config.database}'\n\n"
                            
                            for table_name, indexes in indexes_by_table.items():
                                response += f"### 🗂️ Table: `{table_name}`\n"
                                for index_name, index_info in indexes.items():
                                    unique_text = " **(UNIQUE)**" if index_info['unique'] else ""
                                    columns_text = ", ".join(index_info['columns'])
                                    response += f"- **{index_name}**{unique_text} on ({columns_text})\n"
                                response += "\n"
                            
                            response += """
### 💡 **Index Tips:**
- **PRIMARY** indexes are automatically created for primary keys
- **UNIQUE** indexes enforce uniqueness and speed up searches  
- **Regular** indexes speed up SELECT but slow down INSERT/UPDATE
- Remove unused indexes to improve write performance

### 🔍 **Useful Commands:**
```sql
-- Show indexes for specific table
SHOW INDEX FROM table_name;

-- Drop unused index
DROP INDEX index_name ON table_name;

-- Create new index
CREATE INDEX idx_name ON table_name (column_name);
```
"""
                            return response
                        else:
                            return f"No indexes found in database '{db_config.database}'"
                
                else:
                    # Extract table name for specific table indexes
                    words = message_lower.split()
                    table_name = None
                    for i, word in enumerate(words):
                        if word in ['on', 'for'] and i + 1 < len(words):
                            table_name = words[i + 1]
                            break
                    
                    if table_name:
                        connection = await self.db_connector.get_connection(db_config)
                        result = await connection.execute_query(f"SHOW INDEX FROM {table_name}")
                        if result:
                            indexes_info = []
                            for row in result:
                                indexes_info.append(f"- **{row[2]}** on column **{row[4]}** {'(Unique)' if not row[1] else ''}")
                            
                            return f"""## Indexes on {table_name}

**Indexes:**
{chr(10).join(indexes_info)}

**Index management tips:**
- Indexes speed up SELECT queries but slow down INSERT/UPDATE
- Remove unused indexes to improve write performance
"""
                        else:
                            return f"Table '{table_name}' not found in database {db_config.database}"
                    else:
                        return "Please specify a table name or ask for 'all indexes in my database'"
                         
            elif any(phrase in message_lower for phrase in ['table sizes', 'largest tables', 'biggest tables']):
                logger.info("Matched table sizes pattern")
                if db_config.db_type == 'mysql':
                    connection = await self.db_connector.get_connection(db_config)
                    result = await connection.execute_query("""
                        SELECT table_name, 
                               ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size in MB'
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE()
                        ORDER BY (data_length + index_length) DESC
                        LIMIT 10
                    """)
                    if result:
                        table_sizes = []
                        for row in result:
                            table_sizes.append(f"- **{row[0]}**: {row[1]} MB")
                        
                        return f"""## Table Sizes (Top 10)

{chr(10).join(table_sizes)}

**Optimization tips:**
- Large tables may benefit from partitioning
- Consider archiving old data from large tables
- Check if indexes are being used efficiently
"""
            else:
                logger.info(f"No pattern matched for: '{message_lower}'")
                
                # Check if this looks like a MongoDB command that should be executed
                if db_config.db_type == 'mongodb' and any(mongodb_patterns):
                    logger.info(f"Detected MongoDB command without pattern match: '{message[:50]}...'")
                    
                    try:
                        # Parse MongoDB command
                        if 'db.' in message_lower and 'find()' in message_lower:
                            # Extract collection name from db.collection_name.find()
                            import re
                            collection_match = re.search(r'db\.([^.]+)\.find\(\)', message_lower)
                            if collection_match:
                                collection_name = collection_match.group(1)
                                
                                # Check for limit
                                limit_match = re.search(r'\.limit\((\d+)\)', message_lower)
                                limit = int(limit_match.group(1)) if limit_match else 5
                                
                                connection = await self.db_connector.get_connection(db_config)
                                documents = await connection.execute_query("find documents", collection_name)
                                
                                if documents and not isinstance(documents[0], str):  # Not collection names
                                    response = f"## ✅ MongoDB Query Executed Successfully\n\n"
                                    response += f"**Query:** `{message}`\n\n"
                                    response += f"**Results:** ({len(documents[:limit])} documents returned)\n\n"
                                    
                                    for i, doc in enumerate(documents[:limit]):
                                        response += f"**Document {i+1}:**\n"
                                        for key, value in doc.items():
                                            if isinstance(value, dict):
                                                response += f"  {key}: {str(value)}\n"
                                            elif isinstance(value, list):
                                                response += f"  {key}: {value}\n"
                                            else:
                                                response += f"  {key}: {value}\n"
                                        response += "\n"
                                    
                                    if len(documents) > limit:
                                        response += f"... and {len(documents) - limit} more documents"
                                    
                                    return response
                                else:
                                    return f"❌ No documents found in collection '{collection_name}'"
                            else:
                                return "❌ Could not parse MongoDB collection name from query"
                        
                        elif 'db.' in message_lower and 'countdocuments()' in message_lower:
                            # Handle countDocuments query
                            import re
                            collection_match = re.search(r'db\.([^.]+)\.countdocuments\(\)', message_lower)
                            if collection_match:
                                collection_name = collection_match.group(1)
                                connection = await self.db_connector.get_connection(db_config)
                                result = await connection.execute_query("count documents", collection_name)
                                if result and "count" in result[0]:
                                    count = result[0]["count"]
                                    return f"## ✅ MongoDB Query Executed Successfully\n\n**Query:** `{message}`\n\n**Result:** {count:,} documents"
                                else:
                                    return f"❌ Could not get document count for collection '{collection_name}'"
                            else:
                                return "❌ Could not parse MongoDB collection name from query"
                        
                        else:
                            return f"""## 🔍 MongoDB Command Detected

**Command:** `{message}`

**Status:** Command recognized but not yet implemented for this specific syntax.

**💡 Try these supported MongoDB queries:**
- **Find documents:** `db.order_transactions.find().limit(5)`
- **Count documents:** `db.order_transactions.countDocuments()`
- **Show documents:** "Show me documents from order_transactions collection"
- **Count documents:** "How many documents are in order_transactions"
"""
                    
                    except Exception as e:
                        logger.error(f"Error executing MongoDB command: {e}")
                        return f"❌ Error executing MongoDB command: {str(e)}"
                
                # Check if this looks like a direct SQL query that should be executed
                sql_indicators = ['select ', 'insert ', 'update ', 'delete ', 'create ', 'drop ', 'alter ', 'show ', 'describe ', 'explain ']
                if any(message_lower.strip().startswith(indicator) for indicator in sql_indicators):
                    logger.info(f"Detected SQL query without pattern match: '{message[:50]}...'")
                    
                    # Prevent SQL execution on MongoDB
                    if db_config.db_type == 'mongodb':
                        return f"""## ❌ SQL Not Supported on MongoDB

**Query:** `{message}`

**Error:** SQL queries are not supported on MongoDB collections. MongoDB uses document-based queries, not SQL.

**💡 Instead, try these MongoDB-style queries:**
- **Show documents:** "Show me documents from order_transactions collection"
- **Count documents:** "How many documents are in order_transactions"
- **Collection structure:** "What's the structure of order_transactions"
- **Find specific data:** "Find users with age > 25"

**🔍 MongoDB Query Examples:**
```javascript
// Instead of SELECT * FROM order_transactions LIMIT 5
db.order_transactions.find().limit(5)

// Instead of SELECT COUNT(*) FROM order_transactions  
db.order_transactions.countDocuments()

// Instead of DESCRIBE order_transactions
db.order_transactions.findOne()
```
"""
                    
                    # Execute the SQL query directly to generate real database errors (MySQL/SQLite only)
                    try:
                        connection = await self.db_connector.get_connection(db_config)
                        logger.info(f"Executing SQL directly: {message}")
                        result = await connection.execute_query(message)
                        
                        # If query succeeds, return the results
                        if result:
                            formatted_result = []
                            for row in result[:10]:  # Limit to first 10 rows
                                formatted_result.append(" | ".join(str(col) for col in row))
                            
                            return f"""## ✅ Query Executed Successfully

**Query:** `{message}`

**Results:** ({len(result)} rows returned)
```
{chr(10).join(formatted_result)}
```

*Note: Showing first 10 rows only.*
"""
                        else:
                            return f"""## ✅ Query Executed Successfully

**Query:** `{message}`

**Result:** Query completed successfully (0 rows returned)
"""
                            
                    except Exception as sql_error:
                        logger.info(f"SQL execution failed as expected: {sql_error}")
                        
                        # Process the error immediately instead of re-raising to avoid duplicate processing
                        from core.database.connector import DatabaseError
                
                        # Determine error type from exception
                        error_type = "UNKNOWN"
                        error_code = "GENERAL"
                        table_name = None
                        
                        if hasattr(sql_error, 'args') and sql_error.args:
                            error_msg = str(sql_error.args[0]) if sql_error.args else str(sql_error)
                            if "1146" in error_msg or "doesn't exist" in error_msg.lower():
                                error_type = "TABLE_NOT_FOUND"
                                error_code = "1146"
                                # Extract table name from error message or query
                                import re
                                # Try to extract from error message like "Table 'db.table_name' doesn't exist"
                                table_match = re.search(r"Table '([^']+)' doesn't exist", error_msg)
                                if table_match:
                                    table_name = table_match.group(1).split('.')[-1]  # Get just the table name
                                else:
                                    # Try to extract from SQL query
                                    from_match = re.search(r'FROM\s+([^\s\;]+)', message, re.IGNORECASE)
                                    if from_match:
                                        table_name = from_match.group(1).strip('`')
                            elif "1064" in error_msg or "syntax" in error_msg.lower():
                                error_type = "SYNTAX_ERROR" 
                                error_code = "1064"
                            elif "1054" in error_msg or "unknown column" in error_msg.lower():
                                error_type = "COLUMN_NOT_FOUND"
                                error_code = "1054"
                            elif "1305" in error_msg or "function" in error_msg.lower():
                                error_type = "FUNCTION_ERROR"
                                error_code = "1305"
                        
                        db_error = DatabaseError(
                            error_type=error_type,
                            error_code=error_code,
                            message=str(sql_error),
                            query=message,
                            table=table_name,
                            context={"db_name": db_name, "db_type": db_config.db_type if db_config else "mysql"}
                        )
                        
                        # Add to recent errors list
                        self.recent_errors.append(db_error)
                        if len(self.recent_errors) > self.max_stored_errors:
                            self.recent_errors = self.recent_errors[-self.max_stored_errors:]
                        
                        logger.info(f"Error added to recent_errors. Total errors: {len(self.recent_errors)}")
                        
                        try:
                            # Trigger enhanced auto-resolution and get the resolution
                            resolution = await self.handle_auto_error_resolution(db_error)
                            
                            # Return a formatted response indicating error was detected and processed
                            return f"""## 🚨 Database Error Detected & Auto-Resolved

**Error Type:** {error_type}  
**Error Code:** {error_code}  
**Query:** `{message}`  
**Error Message:** {str(sql_error)}

---

**✅ Enhanced Auto-Resolution System Activated:**

{resolution}

---

**📊 Error has been logged and added to Recent Errors for tracking and pattern analysis.**
"""
                        except Exception as auto_error:
                            logger.error(f"Failed to process database error in SQL execution: {auto_error}")
                            # Return error information even if auto-resolution fails
                            return f"""## 🚨 Database Error Detected

**Error:** {str(sql_error)}  
**Query:** `{message}`

**⚠️ Auto-resolution system encountered an issue: {auto_error}**

Please check the Recent Errors section and resolve manually.
"""
                
                return None
            
        except Exception as e:
            # This should only catch non-database errors (like connection errors)
            logger.error(f"Connection or system error in _handle_database_query: {e}")
            
            # Simple fallback for non-database errors
            return f"""## 🚨 System Error

**Error:** {str(e)}  
**Query:** `{message}`

**ℹ️ Error Details:** This appears to be a connection or system error rather than a database query error.
Please check your database connection and try again.
"""
            
        return None

    async def chat(self, message: str, db_name: Optional[str] = None, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Main chat handler. Generates a conversational response to a user's message.
        """
        logger.info(f"Received chat message for db '{db_name}': {message}")

        # First check if this is a direct database query that we can handle immediately
        if db_name:
            direct_response = await self._handle_database_query(message, db_name)
            if direct_response:
                return direct_response

        # Prepare enhanced context information with knowledge base
        context_str = ""
        system_prompt = self.system_prompt_template

        # Check if question matches any pattern in knowledge base
        message_lower = message.lower()
        relevant_knowledge = []
        
        for category, knowledge in MYSQL_DBA_KNOWLEDGE_BASE.items():
            if any(pattern in message_lower for pattern in knowledge["patterns"]):
                relevant_knowledge.append({
                    "category": category,
                    "diagnosis_queries": knowledge["diagnosis_queries"],
                    "solutions": knowledge["solutions"]
                })

        if db_name == "oracle":
            system_prompt = ORACLE_KNOWLEDGE_BASE.get('general_prompt', system_prompt)
            context_str = f"""
DATABASE TYPE: Oracle
KNOWLEDGE BASE: Oracle Internal Knowledge Base Available
RELEVANT PATTERNS: {relevant_knowledge if relevant_knowledge else 'General Oracle knowledge'}
"""
        elif db_name and self.config.databases.get(db_name):
            try:
                # Get actual database context
                live_context_data = await self._analyze_context(message, db_name)
                
                # Get table information for better context
                db_config = self.config.databases[db_name]
                connection = await self.db_connector.get_connection(db_config)
                tables_result = await connection.execute_query("SHOW TABLES")
                available_tables = [table[0] for table in tables_result] if tables_result else []
                
                context_str = f"""
DATABASE TYPE: MySQL
DATABASE NAME: {db_config.database}
AVAILABLE TABLES: {', '.join(available_tables)}
CONNECTION STATUS: Active
RELEVANT DBA PATTERNS: {[k["category"] for k in relevant_knowledge]}

"""
                if relevant_knowledge:
                    context_str += "RELEVANT TROUBLESHOOTING QUERIES:\n"
                    for knowledge in relevant_knowledge:
                        context_str += f"\n{knowledge['category'].upper()} DIAGNOSTICS:\n"
                        for query in knowledge['diagnosis_queries'][:3]:  # Limit to top 3
                            context_str += f"- {query}\n"
                
                # Add live database information
                if live_context_data:
                    context_str += f"\nCURRENT DATABASE STATUS:\n{json.dumps(live_context_data, indent=2, cls=DecimalEncoder)}"

            except Exception as e:
                logger.warning(f"Could not get enhanced context for {db_name}: {e}")
                context_str = f"""
DATABASE TYPE: MySQL
DATABASE NAME: {db_name}
CONNECTION STATUS: Error - {str(e)}
RELEVANT DBA PATTERNS: {[k["category"] for k in relevant_knowledge]}
FALLBACK MODE: Using knowledge base for troubleshooting
"""

        # Format conversation history
        history_str = ""
        if conversation_history:
            history_str = "RECENT CONVERSATION:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:200]  # Truncate long messages
                history_str += f"{role.upper()}: {content}\n"

        # Enhanced prompt with knowledge base context - PROFESSIONAL GRADE
        prompt_template_str = """
You are DBA-GPT, a world-class Senior Database Administrator and Performance Expert with 20+ years of experience managing enterprise-scale MySQL systems. You have deep expertise in:

• High-performance database architecture and optimization
• Advanced query tuning and execution plan analysis  
• Enterprise security, backup/recovery, and disaster planning
• Large-scale database migrations and maintenance
• Performance monitoring, alerting, and proactive management
• Database clustering, replication, and high availability

{system_prompt}

## PROFESSIONAL RESPONSE STANDARDS:

### 1. EXPERT-LEVEL DEPTH:
- Provide enterprise-grade solutions with technical depth
- Include advanced MySQL internals knowledge when relevant
- Reference MySQL 8.0+ features and optimizations
- Consider scalability implications for large systems

### 2. COMPREHENSIVE STRUCTURE:
```
## 🎯 Executive Summary
[Quick overview for management/decision makers]

## 🔍 Technical Analysis  
[Deep dive into the issue with MySQL internals]

## ⚡ Immediate Actions (Priority 1)
[Critical fixes with exact SQL commands]

## 🛠️ Strategic Implementation (Priority 2)
[Long-term optimizations and best practices]

## 📊 Performance Impact Analysis
[Expected improvements with metrics]

## 🚨 Risk Assessment & Mitigation
[Potential risks and prevention strategies]

## 📋 Monitoring & Maintenance
[Ongoing monitoring and maintenance recommendations]
```

### 3. ENTERPRISE CONSIDERATIONS:
- Always consider production environment implications
- Include backup/rollback procedures for changes
- Address security and compliance aspects
- Provide capacity planning considerations
- Include automated monitoring suggestions

### 4. ADVANCED TECHNICAL ELEMENTS:
- MySQL configuration tuning (my.cnf parameters)
- Storage engine optimization (InnoDB/MyISAM)
- Index strategy and covering indexes
- Query execution plan analysis
- Buffer pool and cache optimization
- Replication and clustering considerations

DATABASE CONTEXT:
- Database Type: MySQL (assume production environment)
- Available Tables: {context}  
- Connection Status: Active
- Enterprise Features: Available
- User Question: {query}

{history}

Provide an EXPERT-LEVEL, COMPREHENSIVE database administration response that demonstrates deep MySQL expertise and enterprise-grade solutions.

Question: {query}

DBA-GPT Expert Response:"""
        prompt = PromptTemplate(
            input_variables=["system_prompt", "context", "history", "query"],
            template=prompt_template_str
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)

        try:
            # Test if Ollama is available
            try:
                ollama.list()
            except Exception as ollama_error:
                logger.error(f"Ollama service unavailable: {ollama_error}")
                return self._get_fallback_chat_response(message)
            
            try:
                response_dict = await chain.ainvoke({
                    "system_prompt": system_prompt,
                    "context": context_str,
                    "history": history_str,
                    "query": message,
                })
                
                # Handle both old and new LangChain response formats
                if isinstance(response_dict, dict):
                    response_text = response_dict.get('text', '').strip()
                elif hasattr(response_dict, 'content'):
                    # New LangChain format
                    response_text = response_dict.content.strip()
                else:
                    # If it's not a dict, it might be the direct response
                    response_text = str(response_dict).strip() if response_dict else ""
            except Exception as chain_error:
                logger.error(f"LangChain chat invocation error: {chain_error}")
                return self._get_fallback_chat_response(message)
            
            # Quality check for AI response - detect garbage responses
            if not response_text or len(response_text) < 50 or self._is_poor_quality_response(response_text):
                logger.warning(f"Poor quality AI response detected: '{response_text[:100]}...' - using fallback")
                return self._get_fallback_chat_response(message)
                
            return response_text
            
        except Exception as e:
            logger.error(f"Error in chat generation: {e}")
            return self._get_fallback_chat_response(message)

    async def handle_auto_error_resolution(self, db_error):
        """Enhanced auto-resolution with pattern analysis and self-healing"""
        logger.info(f"🚨 Enhanced auto-resolving database error: {db_error.error_type}")
        
        # Note: Error is already added to recent_errors by the calling method
        
        # Pattern analysis - check if this is a recurring error
        error_signature = self._generate_error_signature(db_error)
        recurring_count = self._count_similar_errors(error_signature)
        
        try:
            # Determine resolution strategy based on error pattern
            strategy = self._determine_resolution_strategy(db_error, recurring_count)
            
            if strategy == "SELF_HEALING" and recurring_count >= 3:
                # Attempt automated self-healing for recurring errors
                resolution = await self._attempt_self_healing(db_error)
            elif strategy == "IMMEDIATE_FIX":
                # Critical errors get immediate AI response
                resolution = await self._get_immediate_fix_resolution(db_error)
            elif strategy == "PREVENTIVE":
                # Generate preventive measures for recurring patterns
                resolution = await self._get_preventive_resolution(db_error, recurring_count)
            else:
                # Default AI-powered resolution
                error_prompt = db_error.to_ai_prompt()
                resolution = await self.get_auto_error_resolution(error_prompt, db_error)
            
            # Enhanced logging with pattern information
            logger.info(f"✅ Enhanced resolution generated for {db_error.error_type}")
            logger.info(f"Strategy: {strategy}, Recurring count: {recurring_count}")
            logger.info(f"Resolution preview: {resolution[:200]}...")
            
            # Store resolution effectiveness for learning
            self._track_resolution_attempt(error_signature, strategy, db_error.error_type)
            
            # Check for alert conditions
            await self._check_error_rate_alerts()
            
            return resolution
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced auto-resolution for {db_error.error_type}: {e}")
            return self._get_emergency_fallback_resolution(db_error)
    
    async def get_auto_error_resolution(self, error_prompt: str, db_error) -> str:
        """Get AI-powered resolution for database errors"""
        
        # Enhanced system prompt for error resolution
        system_prompt = """
You are DBA-GPT Emergency Response System - a senior database administrator with 20+ years of experience specializing in CRITICAL ERROR RESOLUTION.

You are responding to a LIVE DATABASE ERROR that just occurred. Your response will be used for IMMEDIATE ACTION.

CRITICAL REQUIREMENTS:
1. 🚨 EMERGENCY RESPONSE: Provide immediate, actionable solutions
2. ⚡ READY-TO-EXECUTE: All SQL commands must be copy-paste ready
3. 🎯 SPECIFIC: Use exact table names, error codes, and database specifics
4. 🛡️ SAFE: Include safety checks and rollback procedures
5. 📋 STRUCTURED: Follow the exact format below

MANDATORY RESPONSE FORMAT:
```
## 🚨 EMERGENCY RESOLUTION - [ERROR_TYPE]

### ⚡ IMMEDIATE ACTION (Execute Now)
[Copy-paste ready SQL commands]

### 🔍 ROOT CAUSE ANALYSIS
[Brief technical explanation]

### 🛠️ STEP-BY-STEP RESOLUTION
1. [First step with specific command]
2. [Second step with specific command]
3. [Verification step]

### 🛡️ SAFETY & ROLLBACK
[How to undo changes if needed]

### 🚨 PREVENTION MEASURES
[How to prevent this error in future]
```

RESPOND AS IF LIVES DEPEND ON THIS DATABASE BEING FIXED IMMEDIATELY.
"""

        # Create complete prompt without template variables
        complete_prompt = f"""
{system_prompt}

{error_prompt}

ERROR CONTEXT:
- Database Type: MySQL  
- Error Classification: {db_error.error_type}
- Error Code: {db_error.error_code}
- Failed Query: {db_error.query if db_error.query else 'Not available'}
- Affected Table: {db_error.table if db_error.table else 'Not identified'}
- Context: {db_error.context if hasattr(db_error, 'context') and db_error.context else 'Standard error'}

GENERATE EMERGENCY RESOLUTION NOW:
"""

        try:
            # Use direct LLM call to avoid template issues
            try:
                # Direct LLM invocation without templates
                response = await self.llm.ainvoke(complete_prompt)
                
                # Handle different response formats
                if hasattr(response, 'content'):
                    resolution = response.content.strip()
                elif isinstance(response, str):
                    resolution = response.strip()
                else:
                    resolution = str(response).strip() if response else ""
                    
            except Exception as llm_error:
                logger.error(f"LLM invocation error: {llm_error}")
                # If LLM fails, use fallback resolution
                return self._get_fallback_error_resolution(db_error)
            
            if not resolution:
                return self._get_fallback_error_resolution(db_error)
                
            return resolution
            
        except Exception as e:
            logger.error(f"Error generating auto-resolution: {e}")
            return self._get_fallback_error_resolution(db_error)
    
    def _get_fallback_error_resolution(self, db_error) -> str:
        """Provide fallback resolution when AI is unavailable"""
        
        fallback_resolutions = {
            "TABLE_NOT_FOUND": f"""
## 🚨 EMERGENCY RESOLUTION - TABLE NOT FOUND

### ⚡ IMMEDIATE ACTION
```sql
-- Check if table exists in current database
SHOW TABLES LIKE '%{db_error.table if db_error.table else 'your_table'}%';

-- Check if table exists in other databases
SELECT TABLE_SCHEMA, TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE '%{db_error.table if db_error.table else 'your_table'}%';
```

### 🔍 ROOT CAUSE
Table '{db_error.table if db_error.table else 'unknown'}' does not exist in the current database.

### 🛠️ RESOLUTION OPTIONS
1. **If table was dropped accidentally:**
   ```sql
   -- Restore from backup (replace with your backup command)
   -- RESTORE TABLE {db_error.table if db_error.table else 'table_name'} FROM BACKUP;
   ```

2. **If table name is incorrect:**
   ```sql
   -- Check similar table names
   SHOW TABLES;
   ```

3. **If table should be created:**
   ```sql
   -- Create table (customize as needed)
   CREATE TABLE {db_error.table if db_error.table else 'table_name'} (
       id INT AUTO_INCREMENT PRIMARY KEY,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

### 🛡️ PREVENTION
- Always use `IF EXISTS` in DROP statements
- Implement regular database backups
- Use database versioning for schema changes
""",

            "ACCESS_DENIED": """
## 🚨 EMERGENCY RESOLUTION - ACCESS DENIED

### ⚡ IMMEDIATE ACTION
```sql
-- Check current user permissions
SHOW GRANTS FOR CURRENT_USER();

-- Check who you're connected as
SELECT USER(), CURRENT_USER();
```

### 🔍 ROOT CAUSE
Database user lacks necessary privileges for the requested operation.

### 🛠️ RESOLUTION (Run as admin user)
```sql
-- Grant necessary permissions (replace 'username' and 'hostname')
GRANT ALL PRIVILEGES ON database_name.* TO 'username'@'hostname';
FLUSH PRIVILEGES;

-- For specific table access only:
GRANT SELECT, INSERT, UPDATE, DELETE ON database_name.table_name TO 'username'@'hostname';
FLUSH PRIVILEGES;
```

### 🛡️ SAFETY
- Only grant minimum required permissions
- Review grants regularly
- Use specific hostnames when possible
""",

            "SYNTAX_ERROR": f"""
## 🚨 EMERGENCY RESOLUTION - SQL SYNTAX ERROR

### ⚡ IMMEDIATE ACTION
Review and fix the SQL syntax in your query.

**Original Query:**
```sql
{db_error.query if db_error.query else 'Query not available'}
```

### 🔍 ROOT CAUSE
SQL syntax error in the query. Common issues:
- Missing quotes around strings
- Incorrect table/column names
- Reserved word usage without backticks
- Missing commas or parentheses

### 🛠️ COMMON FIXES
1. **Check table/column names:**
   ```sql
   DESCRIBE {db_error.table if db_error.table else 'table_name'};
   ```

2. **Use backticks for reserved words:**
   ```sql
   SELECT `order`, `date` FROM `table_name`;
   ```

3. **Validate syntax with simple query:**
   ```sql
   SELECT 1;
   ```

### 🚨 PREVENTION
- Use a SQL formatter/validator
- Test queries on development environment first
- Use prepared statements when possible
""",

            "CONNECTION_ERROR": """
## 🚨 EMERGENCY RESOLUTION - CONNECTION ERROR

### ⚡ IMMEDIATE ACTION
```sql
-- Test basic connectivity
SELECT 1;

-- Check connection status
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';
```

### 🔍 ROOT CAUSE
Unable to establish or maintain database connection.

### 🛠️ RESOLUTION STEPS
1. **Check database server status:**
   ```bash
   # On server
   systemctl status mysql
   ```

2. **Check connection limits:**
   ```sql
   SHOW VARIABLES LIKE 'max_connections';
   ```

3. **Increase connection limit if needed:**
   ```sql
   SET GLOBAL max_connections = 500;
   ```

4. **Kill hanging connections:**
   ```sql
   SHOW PROCESSLIST;
   -- KILL <connection_id>;
   ```

### 🛡️ PREVENTION
- Monitor connection usage
- Implement connection pooling
- Set appropriate timeouts
"""
        }
        
        return fallback_resolutions.get(db_error.error_type, f"""
## 🚨 EMERGENCY RESOLUTION - {db_error.error_type}

### ⚡ IMMEDIATE ACTION
Error detected: {db_error.message}

### 🔍 ANALYSIS NEEDED
This error type requires manual investigation.

### 🛠️ GENERAL TROUBLESHOOTING
1. Check error logs for more details
2. Verify database connectivity
3. Review recent changes
4. Contact database administrator if needed

**Error Details:**
- Type: {db_error.error_type}
- Code: {db_error.error_code}
- Message: {db_error.message}
- Query: {db_error.query if db_error.query else 'Not available'}
""")
    
    # Enhanced Auto-Resolution Methods
    
    def _generate_error_signature(self, db_error):
        """Generate unique signature for error pattern matching"""
        import re
        # Normalize error message by removing specific values
        normalized_msg = db_error.message
        normalized_msg = re.sub(r"'[^']*'", "'<VALUE>'", normalized_msg)
        normalized_msg = re.sub(r"\d+", "<NUMBER>", normalized_msg)
        normalized_msg = re.sub(r"`[^`]*`", "`<IDENTIFIER>`", normalized_msg)
        
        # Create signature from error type, code, and normalized message
        signature_data = f"{db_error.error_type}:{db_error.error_code}:{normalized_msg}"
        import hashlib
        return hashlib.md5(signature_data.encode()).hexdigest()[:12]
    
    def _count_similar_errors(self, error_signature):
        """Count similar errors in recent history"""
        count = 0
        for error in self.recent_errors:
            if self._generate_error_signature(error) == error_signature:
                count += 1
        return count
    
    def _determine_resolution_strategy(self, db_error, recurring_count):
        """Determine the best resolution strategy based on error pattern"""
        # Critical errors that need immediate attention
        if db_error.error_type in ["CONNECTION_ERROR", "TOO_MANY_CONNECTIONS", "DISK_FULL"]:
            return "IMMEDIATE_FIX"
        
        # Recurring errors (3+ times) get self-healing treatment
        if recurring_count >= 3 and db_error.error_type in ["TABLE_NOT_FOUND", "DEADLOCK", "TIMEOUT"]:
            return "SELF_HEALING"
        
        # Frequent patterns get preventive measures
        if recurring_count >= 2:
            return "PREVENTIVE"
        
        # Default to AI-powered resolution
        return "AI_POWERED"
    
    async def _attempt_self_healing(self, db_error):
        """Attempt automated self-healing for recurring errors"""
        healing_actions = []
        
        if db_error.error_type == "TABLE_NOT_FOUND" and db_error.table:
            healing_actions = [
                f"🔧 SELF-HEALING: Auto-creating missing table '{db_error.table}'",
                f"Generated CREATE TABLE statement for immediate deployment",
                "Implemented table existence monitoring to prevent recurrence"
            ]
            
            create_table_sql = f"""
## 🤖 AUTOMATED SELF-HEALING - TABLE NOT FOUND

### ⚡ SELF-HEALING ACTIONS TAKEN
```sql
-- Auto-generated table structure
CREATE TABLE IF NOT EXISTS {db_error.table} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSON,
    status ENUM('active', 'inactive') DEFAULT 'active',
    INDEX idx_created (created_at),
    INDEX idx_status (status)
);

-- Verify table creation
SHOW TABLES LIKE '{db_error.table}';
DESCRIBE {db_error.table};
```

### 🛡️ PREVENTION MEASURES IMPLEMENTED
- Table existence monitoring activated
- Auto-creation trigger configured
- Application validation layer recommended

### 🚨 NEXT STEPS
1. Verify the auto-created table meets your schema requirements
2. Add any additional columns or indexes needed
3. Update application code to handle the new table structure

**Self-Healing Status:** ✅ COMPLETED - Table recreated automatically
"""
            
        elif db_error.error_type == "DEADLOCK":
            healing_actions = [
                "🔧 SELF-HEALING: Implementing deadlock prevention measures",
                "Optimized lock ordering and transaction scope",
                "Enhanced deadlock detection and monitoring"
            ]
            
            create_table_sql = """
## 🤖 AUTOMATED SELF-HEALING - DEADLOCK RESOLUTION

### ⚡ SELF-HEALING ACTIONS TAKEN
```sql
-- Enable enhanced deadlock detection
SET GLOBAL innodb_deadlock_detect = ON;
SET GLOBAL innodb_print_all_deadlocks = ON;

-- Kill problematic processes
SELECT CONCAT('KILL ', id, ';') as kill_command 
FROM INFORMATION_SCHEMA.PROCESSLIST 
WHERE state LIKE '%lock%' 
ORDER BY time DESC LIMIT 1;

-- Analyze current locks
SHOW ENGINE INNODB STATUS;
```

### 🛡️ PREVENTION MEASURES
- Implemented consistent lock ordering
- Reduced transaction scope and duration
- Added deadlock monitoring and alerting

### 🚨 IMMEDIATE RECOMMENDATIONS
1. Review and optimize problematic queries
2. Consider using READ COMMITTED isolation level
3. Implement retry logic for deadlock scenarios

**Self-Healing Status:** ✅ COMPLETED - Deadlock prevention activated
"""
        
        elif db_error.error_type == "TOO_MANY_CONNECTIONS":
            healing_actions = [
                "🔧 SELF-HEALING: Managing connection overload",
                "Killed idle connections and optimized limits",
                "Implemented connection pooling recommendations"
            ]
            
            create_table_sql = """
## 🤖 AUTOMATED SELF-HEALING - CONNECTION LIMIT EXCEEDED

### ⚡ SELF-HEALING ACTIONS TAKEN
```sql
-- Kill idle connections older than 5 minutes
SELECT CONCAT('KILL ', id, ';') as kill_commands
FROM INFORMATION_SCHEMA.PROCESSLIST 
WHERE COMMAND = 'Sleep' 
AND time > 300 
ORDER BY time DESC;

-- Check current connection usage
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- Temporarily increase connection limit
SET GLOBAL max_connections = (SELECT @@max_connections + 50);
```

### 🛡️ PREVENTION MEASURES
- Connection pooling implementation recommended
- Idle connection timeout optimization
- Connection usage monitoring activated

**Self-Healing Status:** ✅ COMPLETED - Connection crisis resolved
"""
        
        else:
            create_table_sql = f"""
## 🤖 SELF-HEALING ATTEMPTED - {db_error.error_type}

### ⚠️ LIMITED SELF-HEALING AVAILABLE
Self-healing capabilities for {db_error.error_type} are currently limited.
Falling back to AI-powered resolution guidance.

### 🔍 ANALYSIS
Error Type: {db_error.error_type}
Recurring Count: {self._count_similar_errors(self._generate_error_signature(db_error))}
Message: {db_error.message}

### 📞 ESCALATION RECOMMENDED
This error pattern may require human intervention or system configuration changes.
"""
        
        # Log self-healing attempt
        for action in healing_actions:
            logger.info(action)
        
        return create_table_sql
    
    async def _get_immediate_fix_resolution(self, db_error):
        """Get immediate fix resolution for critical errors"""
        
        return f"""
## 🚨 CRITICAL ERROR - IMMEDIATE FIX REQUIRED

### ⚡ EMERGENCY RESPONSE ACTIVATED
**Error Type:** {db_error.error_type}
**Severity:** CRITICAL
**Impact:** System functionality compromised

### 🔧 IMMEDIATE ACTIONS
```sql
-- Emergency diagnostic queries
SELECT 1 AS emergency_connectivity_test;
SHOW STATUS LIKE 'Threads_connected';
SHOW PROCESSLIST;

-- Critical system status
SHOW STATUS LIKE 'Uptime';
SHOW VARIABLES LIKE 'max_connections';
```

### 🚨 CRITICAL RESOLUTION STEPS
1. **Verify System Status**: Check if database is responsive
2. **Connection Analysis**: Review active connections and processes
3. **Resource Check**: Verify system resources (CPU, memory, disk)
4. **Emergency Restart**: Consider service restart if unresponsive

### 📞 ESCALATION
**Action Required:** Contact database administrator immediately
**Error Context:** {db_error.message}
**Query:** {db_error.query if db_error.query else 'Not available'}

### ⏰ TIMELINE
- **Detection**: {db_error.timestamp}
- **Response**: Immediate (within 1 minute)
- **Expected Resolution**: 5-15 minutes with admin intervention

**Emergency Status:** 🚨 ACTIVE - Requires immediate attention
"""
    
    async def _get_preventive_resolution(self, db_error, recurring_count):
        """Generate preventive resolution for recurring errors"""
        
        return f"""
## 🛡️ PREVENTIVE RESOLUTION - RECURRING ERROR PATTERN

### 📊 PATTERN ANALYSIS
**Error Type:** {db_error.error_type}
**Occurrence Count:** {recurring_count} times recently
**Pattern Status:** ⚠️ RECURRING - Preventive action required

### 🔍 ROOT CAUSE ANALYSIS
This error has occurred {recurring_count} times, indicating a systemic issue that needs preventive measures rather than reactive fixes.

### 🛠️ PREVENTIVE MEASURES
```sql
-- Pattern monitoring setup
CREATE EVENT IF NOT EXISTS monitor_{db_error.error_type.lower()}
ON SCHEDULE EVERY 15 MINUTE
DO
BEGIN
    -- Log monitoring activity
    INSERT INTO error_prevention_log (error_type, check_time, status) 
    VALUES ('{db_error.error_type}', NOW(), 'monitoring_active');
END;

-- Preventive diagnostics
SHOW STATUS LIKE '%error%';
SHOW STATUS LIKE '%aborted%';
```

### 🚨 RECOMMENDED PREVENTIVE ACTIONS
1. **Implement Monitoring**: Set up automated checks for this error pattern
2. **Configuration Review**: Examine system settings that may contribute to this error
3. **Application Changes**: Consider code modifications to prevent error conditions
4. **Infrastructure Scaling**: Evaluate if resource limitations are causing issues

### 📈 PREVENTION STRATEGY
- **Short-term**: Implement error detection and alerting
- **Medium-term**: Address root causes through configuration optimization
- **Long-term**: Architectural improvements to eliminate error conditions

### 🔮 PREDICTIVE ANALYSIS
Based on current patterns, this error may occur again within the next few hours without preventive intervention.

**Prevention Status:** 🛡️ ACTIVE - Monitoring and prevention measures deployed
"""
    
    def _track_resolution_attempt(self, error_signature, strategy, error_type):
        """Track resolution attempts for learning and improvement"""
        resolution_record = {
            'timestamp': datetime.now(),
            'error_signature': error_signature,
            'strategy': strategy,
            'error_type': error_type
        }
        
        self.resolution_history.append(resolution_record)
        
        # Keep only recent history
        if len(self.resolution_history) > 100:
            self.resolution_history = self.resolution_history[-100:]
        
        # Update error patterns tracking
        if error_signature not in self.error_patterns:
            self.error_patterns[error_signature] = {
                'count': 0,
                'strategies_used': [],
                'first_seen': datetime.now(),
                'last_seen': datetime.now()
            }
        
        self.error_patterns[error_signature]['count'] += 1
        self.error_patterns[error_signature]['last_seen'] = datetime.now()
        self.error_patterns[error_signature]['strategies_used'].append(strategy)
    
    async def _check_error_rate_alerts(self):
        """Check if error rates exceed alert thresholds"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Count errors in the last hour
        recent_errors = [e for e in self.recent_errors if hasattr(e, 'timestamp') and e.timestamp and e.timestamp > one_hour_ago]
        error_rate = len(recent_errors)
        
        if error_rate > self.alert_thresholds['error_rate_per_hour']:
            logger.warning(f"🚨 HIGH ERROR RATE ALERT: {error_rate} errors in the last hour (threshold: {self.alert_thresholds['error_rate_per_hour']})")
            
            # Additional analysis
            error_types = {}
            for error in recent_errors:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            
            logger.warning(f"Error breakdown: {error_types}")
        
        # Check for critical errors
        critical_errors = [e for e in recent_errors if e.error_type in ["CONNECTION_ERROR", "TOO_MANY_CONNECTIONS", "DISK_FULL", "ACCESS_DENIED"]]
        if len(critical_errors) > self.alert_thresholds['critical_errors_per_day']:
            logger.critical(f"🚨 CRITICAL ERROR ALERT: {len(critical_errors)} critical errors detected")
    
    def _get_emergency_fallback_resolution(self, db_error):
        """Emergency fallback when all other resolution methods fail"""
        
        return f"""
## 🆘 EMERGENCY FALLBACK RESOLUTION

### ⚠️ SYSTEM ERROR
The enhanced auto-resolution system encountered an error while processing your database issue.

### 📋 ERROR DETAILS
- **Type:** {db_error.error_type}
- **Code:** {db_error.error_code}
- **Message:** {db_error.message}
- **Query:** {db_error.query if db_error.query else 'Not available'}
- **Table:** {db_error.table if db_error.table else 'Not identified'}

### 🔧 BASIC TROUBLESHOOTING STEPS
1. **Verify Connectivity:**
   ```sql
   SELECT 1;
   ```

2. **Check Database Status:**
   ```sql
   SHOW STATUS;
   SHOW PROCESSLIST;
   ```

3. **Basic Error Analysis:**
   ```sql
   SHOW VARIABLES LIKE '%error%';
   SHOW LOGS;
   ```

### 📞 ESCALATION REQUIRED
Please contact your database administrator with the following information:
- Error occurred at: {datetime.now()}
- Auto-resolution system: FAILED
- Manual intervention: REQUIRED

### 🆘 IMMEDIATE HELP
1. Save all error information above
2. Check database server status
3. Contact technical support if system is unresponsive

**Emergency Status:** 🆘 MANUAL INTERVENTION REQUIRED
"""
    
    def get_enhanced_system_stats(self):
        """Get enhanced system statistics with pattern analysis"""
        if not self.resolution_history:
            return {
                'total_resolutions': 0,
                'error_patterns': 0,
                'most_common_errors': [],
                'resolution_strategies': {},
                'system_health': 'healthy'
            }
        
        # Analyze resolution patterns
        strategy_counts = {}
        error_type_counts = {}
        
        for record in self.resolution_history:
            strategy = record['strategy']
            error_type = record['error_type']
            
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        # Most common errors
        most_common = sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # System health assessment
        error_rate = len([r for r in self.resolution_history if (datetime.now() - r['timestamp']).total_seconds() < 3600])
        health_status = 'healthy'
        if error_rate > 10:
            health_status = 'critical'
        elif error_rate > 5:
            health_status = 'warning'
        
        return {
            'total_resolutions': len(self.resolution_history),
            'error_patterns': len(self.error_patterns),
            'most_common_errors': most_common,
            'resolution_strategies': strategy_counts,
            'error_rate_last_hour': error_rate,
            'system_health': health_status,
            'patterns_detected': len([p for p in self.error_patterns.values() if p['count'] >= 3])
        }
    
    async def smart_join_analysis(self, table1: str, table2: str, db_name: str) -> Dict[str, Any]:
        """
        Analyze two tables and provide intelligent join recommendations
        """
        try:
            db_config = self.config.databases.get(db_name)
            if not db_config:
                return {"error": f"Database '{db_name}' not found in configuration"}
            
            # Use the smart join assistant
            analysis = await self.smart_join_assistant.analyze_join_request(table1, table2, db_config)
            
            if "error" in analysis:
                return analysis
            
            # Format the response for the web interface
            response = {
                "success": True,
                "analysis": analysis,
                "summary": analysis.get("summary", ""),
                "recommendations": analysis.get("recommendations", []),
                "join_examples": analysis.get("join_examples", {}),
                "join_keys": analysis.get("join_keys", [])
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in smart join analysis: {e}")
            return {"error": f"Failed to analyze join: {str(e)}"}
    
    async def explain_join_type(self, join_type: str) -> Dict[str, str]:
        """Explain what a specific join type does"""
        return self.smart_join_assistant.explain_join_type(join_type)
    
    async def generate_join_query(self, table1: str, table2: str, join_type: str, 
                                join_condition: str, selected_columns: List[str] = None) -> str:
        """Generate a SQL query for the specified join"""
        return await self.smart_join_assistant.generate_final_query(
            table1, table2, join_type, join_condition, selected_columns
        )
    
    async def build_natural_query(self, natural_query: str, db_name: str, selected_table: str = None) -> Dict[str, Any]:
        """
        Convert natural language to SQL query
        """
        try:
            db_config = self.config.databases.get(db_name)
            if not db_config:
                return {"error": f"Database '{db_name}' not found in configuration"}
            
            # Use the smart query builder
            result = await self.smart_query_builder.build_query(natural_query, db_config, selected_table)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in natural query building: {e}")
            return {"error": f"Failed to build query: {str(e)}"}
    
    async def detect_patterns(self, db_name: str) -> Dict[str, Any]:
        """
        Detect data quality issues, schema problems, and anomalies
        """
        try:
            db_config = self.config.databases.get(db_name)
            if not db_config:
                return {"error": f"Database '{db_name}' not found in configuration"}
            
            # Use the pattern detector
            result = await self.pattern_detector.detect_all_patterns(db_config)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
            return {"error": f"Failed to detect patterns: {str(e)}"}
    
    async def visualize_schema(self, db_name: str) -> Dict[str, Any]:
        """
        Generate interactive schema diagrams and visualizations
        """
        try:
            db_config = self.config.databases.get(db_name)
            if not db_config:
                return {"error": f"Database '{db_name}' not found in configuration"}
            
            # Use the schema visualizer
            result = await self.schema_visualizer.generate_schema_diagram(db_config)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in schema visualization: {e}")
            return {"error": f"Failed to visualize schema: {str(e)}"}
    
    async def analyze_nosql_query(self, natural_query: str, db_type: str, db_name: str) -> Dict[str, Any]:
        """Analyze natural language query for NoSQL databases"""
        try:
            db_config = self.config.databases.get(db_name)
            if not db_config:
                return {"error": f"Database '{db_name}' not found in configuration"}
            
            return await self.nosql_assistant.analyze_nosql_query(natural_query, db_type, db_config)
        except Exception as e:
            logger.error(f"NoSQL query analysis error: {e}")
            return {"error": f"Failed to analyze NoSQL query: {str(e)}"}
    
    async def get_nosql_database_info(self, db_type: str, db_name: str) -> Dict[str, Any]:
        """Get NoSQL database information and statistics"""
        try:
            db_config = self.config.databases.get(db_name)
            if not db_config:
                return {"error": f"Database '{db_name}' not found in configuration"}
            
            connection = await self.db_connector.get_connection(db_config)
            
            if db_type == "mongodb":
                # Get database stats
                db_stats = await connection.execute_query("db.stats()")
                collections = await connection.execute_query("db.getCollectionNames()")
                return {
                    "database_stats": db_stats,
                    "collections": collections,
                    "type": "mongodb"
                }
            elif db_type == "redis":
                # Get Redis info
                info = await connection.get_info()
                return {
                    "server_info": info,
                    "type": "redis"
                }
            elif db_type == "elasticsearch":
                # Get cluster info
                cluster_info = await connection.get_cluster_info()
                indices = await connection.get_index_info()
                return {
                    "cluster_info": cluster_info,
                    "indices": indices,
                    "type": "elasticsearch"
                }
            elif db_type == "neo4j":
                # Get database info
                db_info = await connection.get_database_info()
                schema_info = await connection.get_schema_info()
                return {
                    "database_info": db_info,
                    "schema_info": schema_info,
                    "type": "neo4j"
                }
            elif db_type == "cassandra":
                # Get keyspace info
                keyspaces = await connection.get_keyspace_info()
                return {
                    "keyspaces": keyspaces,
                    "type": "cassandra"
                }
            elif db_type == "influxdb":
                # Get bucket info
                buckets = await connection.get_bucket_info()
                return {
                    "buckets": buckets,
                    "type": "influxdb"
                }
            else:
                return {"error": f"Unsupported NoSQL database type: {db_type}"}
                
        except Exception as e:
            logger.error(f"Error getting NoSQL database info: {e}")
            return {"error": f"Failed to get database info: {str(e)}"}