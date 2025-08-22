# 📋 Database-Specific Questions Guide

This guide shows example questions you can ask DBA-GPT for each supported database type.

## 🗄️ SQL Databases

### MySQL Database Questions
- "What tables do I have in my database?"
- "Show me the schema of the users table"
- "How many records are in my orders table?"
- "Find all indexes in my database"
- "What's the size of my database?"
- "Show me active processes"
- "Check for slow queries"
- "Analyze table performance"
- "Show me recent errors"
- "What's the current connection count?"
- "Show me the slow query log"
- "Check for table fragmentation"
- "Analyze index usage"
- "Show me table statistics"

### PostgreSQL Database Questions
- "What tables do I have in my database?"
- "Show me the schema of the users table"
- "How many records are in my orders table?"
- "Find all indexes in my database"
- "What's the size of my database?"
- "Show me active connections"
- "Check for table bloat"
- "Analyze query performance"
- "Show me recent slow queries"
- "What's the current connection count?"
- "Show me the query statistics"
- "Check for table vacuum status"
- "Analyze index usage"
- "Show me table statistics"

### SQLite Database Questions
- "What tables do I have in my database?"
- "Show me the schema of the users table"
- "How many records are in my orders table?"
- "Find all indexes in my database"
- "What's the size of my database?"
- "Show me recent transactions"
- "Find duplicate records"
- "Optimize my database performance"
- "Check for database integrity"
- "Show me table information"
- "Analyze query performance"
- "Check for unused indexes"
- "Show me database statistics"

## 🍃 NoSQL Databases

### MongoDB NoSQL Questions
- "What collections do I have in my database?"
- "Show me documents from user_profiles collection"
- "How many documents are in product_catalog?"
- "Find all indexes in my database"
- "What's the structure of order_transactions?"
- "Show me the latest orders from today"
- "Find users with specific criteria"
- "Aggregate data by category"
- "Show me collection statistics"
- "Check for slow queries"
- "Analyze index usage"
- "Show me database stats"
- "Find documents by date range"
- "Show me collection sizes"

### Redis Database Questions
- "What keys do I have in my database?"
- "Show me the value of a specific key"
- "How many keys are in my database?"
- "Find all keys matching a pattern"
- "What's the memory usage of my database?"
- "Show me key expiration times"
- "Monitor real-time operations"
- "Check Redis performance metrics"
- "Show me memory statistics"
- "Check for slow commands"
- "Analyze key patterns"
- "Show me client connections"
- "Check for memory fragmentation"
- "Show me replication status"

### Elasticsearch Questions
- "What indices do I have in my cluster?"
- "Show me documents from a specific index"
- "How many documents are in my index?"
- "Find all mappings in my cluster"
- "What's the cluster health status?"
- "Show me search query performance"
- "Analyze index performance"
- "Check for failed shards"
- "Show me cluster statistics"
- "Check for slow queries"
- "Analyze index settings"
- "Show me node information"
- "Check for index optimization"
- "Show me search performance"

### Neo4j Graph Database Questions
- "What node labels do I have in my database?"
- "Show me relationships between nodes"
- "How many nodes are in my database?"
- "Find all indexes in my database"
- "What's the database size?"
- "Show me the graph schema"
- "Find shortest paths between nodes"
- "Analyze graph performance"
- "Show me relationship types"
- "Check for slow queries"
- "Analyze node properties"
- "Show me database statistics"
- "Check for graph optimization"
- "Show me query performance"

### Cassandra Database Questions
- "What keyspaces do I have in my cluster?"
- "Show me tables in a keyspace"
- "How many rows are in my table?"
- "Find all indexes in my keyspace"
- "What's the cluster status?"
- "Show me table schemas"
- "Check for compaction status"
- "Analyze query performance"
- "Show me cluster statistics"
- "Check for slow queries"
- "Analyze table performance"
- "Show me node information"
- "Check for repair status"
- "Show me query performance"

### InfluxDB Time Series Questions
- "What measurements do I have in my database?"
- "Show me data from a specific measurement"
- "How many data points are in my measurement?"
- "Find all tags in my database"
- "What's the database size?"
- "Show me recent time series data"
- "Analyze data retention policies"
- "Check for data compression"
- "Show me measurement statistics"
- "Check for slow queries"
- "Analyze time range queries"
- "Show me tag cardinality"
- "Check for data optimization"
- "Show me query performance"

## ☁️ Cloud Databases

### AWS Athena Questions
- "What databases do I have in my catalog?"
- "Show me tables in a database"
- "How many rows are in my table?"
- "Find all partitions in my table"
- "What's the query execution history?"
- "Show me recent query results"
- "Analyze query performance"
- "Check for failed queries"
- "Show me query statistics"
- "Check for data scanning costs"
- "Analyze partition usage"
- "Show me workgroup information"
- "Check for query optimization"
- "Show me billing information"

### Azure SQL Database Questions
- "What tables do I have in my database?"
- "Show me the schema of the users table"
- "How many records are in my orders table?"
- "Find all indexes in my database"
- "What's the database size?"
- "Show me active connections"
- "Check for performance issues"
- "Analyze query performance"
- "Show me database statistics"
- "Check for slow queries"
- "Analyze index usage"
- "Show me DTU/vCore usage"
- "Check for performance recommendations"
- "Show me query performance"

## 🎯 General Database Topics

When no specific database is selected, you can ask about:

### SQL Concepts
- "What is a SELECT statement?"
- "Explain the LIKE operator"
- "How do I use WHERE clauses?"
- "What are database JOINs?"
- "Explain database normalization"
- "What are indexes and how do they work?"
- "How do transactions work?"
- "What is ACID compliance?"

### Performance Optimization
- "Database performance optimization tips"
- "How to optimize slow queries"
- "Best practices for indexing"
- "Query optimization techniques"
- "Database tuning strategies"
- "How to analyze query execution plans"
- "Performance monitoring best practices"

### Database Administration
- "How to backup a database"
- "Database security best practices"
- "How to monitor database health"
- "Database maintenance tasks"
- "How to handle database errors"
- "Database scaling strategies"
- "Disaster recovery planning"

## 💡 Tips for Better Questions

1. **Be Specific:** Instead of "Show me data", try "Show me recent orders from the last 7 days"

2. **Use Database-Specific Terms:**
   - MySQL/PostgreSQL: "tables", "records", "indexes"
   - MongoDB: "collections", "documents", "aggregations"
   - Redis: "keys", "values", "memory usage"
   - Elasticsearch: "indices", "documents", "queries"

3. **Ask for Analysis:** 
   - "Analyze the performance of..."
   - "Check for issues in..."
   - "Optimize the query..."

4. **Request Specific Information:**
   - "Show me the top 10 slowest queries"
   - "Find all tables larger than 1GB"
   - "Check for unused indexes"

## 🔧 Adding New Database Types

To add support for a new database type:

1. **Update the configuration** in `config/config.yaml`
2. **Add database-specific questions** in `core/web/interface.py`
3. **Implement database connector** in `core/database/connector.py`
4. **Add query analysis logic** in the appropriate assistant modules

## 📊 Database Status Indicators

- 🟢 **Connected** - Database is configured and accessible
- 🔴 **Not Configured** - Database is not set up
- 📚 **Knowledge Base** - Educational content mode
- ⚪ **No Selection** - No database selected

---

**Remember:** The more specific your questions, the better the AI can help you with your database administration tasks!
