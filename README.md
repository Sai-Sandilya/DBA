# DBA-GPT: Generative AI Agent for Proactive Database Administration

## Overview

DBA-GPT is an autonomous Generative AI agent specialized in proactive database administration, monitoring, and automated remediation. It combines the power of local AI models with comprehensive database monitoring to ensure optimal database health, performance, and stability.

## 🚀 Key Features

### 🤖 AI-Powered Database Administration
- **Local AI Model Integration**: Runs completely offline using Ollama and local LLMs
- **Professional DBA Recommendations**: Provides expert-level database advice and solutions
- **Natural Language Interface**: ChatGPT-like interaction for database queries and recommendations
- **Contextual Understanding**: Understands database-specific terminology and scenarios

### 📊 Proactive Monitoring & Analysis
- **Real-time Database Monitoring**: Continuous monitoring of multiple database types
- **Performance Metrics Collection**: CPU, memory, I/O, query performance tracking
- **Anomaly Detection**: AI-powered detection of performance issues and bottlenecks
- **Predictive Analytics**: Forecast potential issues before they occur

### 🔧 Automated Remediation
- **Intelligent Issue Resolution**: Automatic detection and fixing of common database problems
- **Performance Optimization**: AI-driven query optimization and index recommendations
- **Backup and Recovery**: Automated backup scheduling and recovery procedures
- **Security Monitoring**: Detection of security vulnerabilities and access anomalies

### 🎯 Multi-Database Support
- **PostgreSQL**: Full monitoring and optimization support
- **MySQL/MariaDB**: Comprehensive performance analysis
- **MongoDB**: Document database monitoring and optimization
- **Redis**: In-memory database performance tracking
- **SQL Server**: Enterprise database monitoring (via extensions)

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Docker (optional, for containerized deployment)
- Ollama (for local AI model inference)

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd DBA
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Ollama and download models**
```bash
# Install Ollama (follow instructions at https://ollama.ai)
# Download recommended models
ollama pull llama2:13b
ollama pull codellama:13b
```

4. **Configure the system**
```bash
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your database connections
```

5. **Start DBA-GPT**
```bash
python main.py
```

## 📁 Project Structure

```
DBA/
├── core/                    # Core DBA-GPT functionality
│   ├── ai/                 # AI model integration
│   ├── monitoring/         # Database monitoring
│   ├── remediation/        # Automated remediation
│   └── analysis/           # Performance analysis
├── config/                 # Configuration files
├── models/                 # AI model configurations
├── scripts/                # Utility scripts
├── web/                    # Web interface
├── tests/                  # Test suite
├── docs/                   # Documentation
└── examples/               # Usage examples
```

## 🎮 Usage Examples

### 1. Interactive DBA Assistant
```python
from core.ai.dba_assistant import DBAAssistant

assistant = DBAAssistant()
response = assistant.get_recommendation(
    "My PostgreSQL database is running slow. What should I check first?"
)
print(response)
```

### 2. Proactive Monitoring
```python
from core.monitoring.monitor import DatabaseMonitor

monitor = DatabaseMonitor()
monitor.start_monitoring()
# Automatically detects and resolves issues
```

### 3. Performance Analysis
```python
from core.analysis.analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
report = analyzer.generate_performance_report("my_database")
print(report)
```

### 4. Web Interface
```bash
# Start the web interface
streamlit run web/interface.py
```

## 🔧 Configuration

### Database Connections
Edit `config/config.yaml` to configure your database connections:

```yaml
databases:
  postgresql:
    host: localhost
    port: 5432
    database: mydb
    username: myuser
    password: mypassword
    
  mysql:
    host: localhost
    port: 3306
    database: mydb
    username: myuser
    password: mypassword
```

### AI Model Configuration
```yaml
ai:
  model: llama2:13b
  temperature: 0.7
  max_tokens: 2048
  context_window: 4096
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `docs/` directory
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas

## 🔮 Roadmap

- [ ] Support for more database types (Oracle, SQLite)
- [ ] Advanced ML models for better predictions
- [ ] Cloud database integration (AWS RDS, Azure SQL)
- [ ] Mobile app for remote monitoring
- [ ] Integration with popular monitoring tools (Grafana, Prometheus)
- [ ] Advanced security features and compliance reporting

---

**DBA-GPT**: Your AI-powered database administration companion! 🚀 