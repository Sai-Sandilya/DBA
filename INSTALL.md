# DBA-GPT Installation Guide

## Prerequisites

Before installing DBA-GPT, ensure you have the following:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Database Server** - PostgreSQL, MySQL, MongoDB, or Redis
- **8GB+ RAM** - Recommended for running local AI models
- **20GB+ Disk Space** - For AI models and database storage

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd DBA
```

## Step 2: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Install Ollama

Ollama is required for running local AI models. Follow the instructions for your operating system:

### Windows
1. Download from [https://ollama.ai/download](https://ollama.ai/download)
2. Run the installer
3. Restart your terminal
4. Verify installation: `ollama --version`

### macOS
```bash
# Using Homebrew
brew install ollama

# Or download from https://ollama.ai/download
```

### Linux
```bash
# Install using the official script
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai/download
```

## Step 4: Download AI Models

```bash
# Start Ollama service
ollama serve

# In a new terminal, download recommended models
ollama pull llama2:13b
ollama pull codellama:13b
ollama pull mistral:7b
```

**Note:** Model downloads may take 10-30 minutes depending on your internet connection.

## Step 5: Configure DBA-GPT

1. Copy the example configuration:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Edit `config/config.yaml` with your database connections:

```yaml
# Example PostgreSQL configuration
databases:
  my_postgres:
    host: "localhost"
    port: 5432
    database: "my_database"
    username: "my_user"
    password: "my_password"
    db_type: "postgresql"

# Example MySQL configuration
  my_mysql:
    host: "localhost"
    port: 3306
    database: "my_database"
    username: "root"
    password: "my_password"
    db_type: "mysql"
```

## Step 6: Test Installation

Run the setup script to verify everything is working:

```bash
python scripts/setup_ollama.py
```

Or run the basic examples:

```bash
python examples/basic_usage.py
```

## Step 7: Start DBA-GPT

### Command Line Interface (CLI)
```bash
python main.py --mode cli
```

### Web Interface
```bash
python main.py --mode web
```
Then open http://localhost:8501 in your browser.

### API Server
```bash
python main.py --mode api
```
API will be available at http://localhost:8000

### All Services
```bash
python main.py --mode all
```

## Troubleshooting

### Common Issues

#### 1. Ollama Connection Error
```
Error: Failed to connect to Ollama server
```
**Solution:**
- Ensure Ollama is running: `ollama serve`
- Check if port 11434 is available
- Restart Ollama service

#### 2. Model Not Found
```
Error: Model 'llama2:13b' not found
```
**Solution:**
```bash
ollama pull llama2:13b
```

#### 3. Database Connection Error
```
Error: Could not connect to database
```
**Solution:**
- Verify database server is running
- Check connection details in `config.yaml`
- Ensure firewall allows connections
- Test connection manually

#### 4. Python Dependencies Error
```
Error: Module not found
```
**Solution:**
```bash
pip install -r requirements.txt
```

#### 5. Permission Errors
```
Error: Permission denied
```
**Solution:**
- On Linux/macOS: `chmod +x scripts/*.py`
- On Windows: Run as Administrator if needed

### Performance Optimization

#### For Better AI Performance:
1. **Use SSD storage** for faster model loading
2. **Increase RAM** to 16GB+ for larger models
3. **Use GPU acceleration** if available:
   ```bash
   # Install CUDA version of PyTorch
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

#### For Database Performance:
1. **Optimize database settings** based on your workload
2. **Use connection pooling** for high-traffic applications
3. **Monitor query performance** regularly

### Security Considerations

1. **Secure Database Connections:**
   - Use strong passwords
   - Enable SSL/TLS
   - Restrict network access

2. **API Security:**
   - Change default ports
   - Use HTTPS in production
   - Implement authentication

3. **Model Security:**
   - Keep models updated
   - Monitor for vulnerabilities
   - Use trusted model sources

## Advanced Configuration

### Custom AI Models

You can use different AI models by modifying the configuration:

```yaml
ai:
  model: "codellama:13b"  # Alternative models
  temperature: 0.5        # Lower for more focused responses
  max_tokens: 4096        # Higher for longer responses
```

### Monitoring Configuration

```yaml
monitoring:
  interval: 30            # Check every 30 seconds
  alert_thresholds:
    cpu_usage: 70.0       # Alert at 70% CPU
    memory_usage: 80.0    # Alert at 80% memory
```

### Logging Configuration

```yaml
logging:
  level: "DEBUG"          # More detailed logs
  file: "logs/dbagpt.log"
  max_size: "50MB"        # Larger log files
```

## Production Deployment

### Docker Deployment

1. Create a Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000 8501

CMD ["python", "main.py", "--mode", "all"]
```

2. Build and run:
```bash
docker build -t dbagpt .
docker run -p 8000:8000 -p 8501:8501 dbagpt
```

### Systemd Service (Linux)

1. Create service file `/etc/systemd/system/dbagpt.service`:
```ini
[Unit]
Description=DBA-GPT Service
After=network.target

[Service]
Type=simple
User=dbagpt
WorkingDirectory=/opt/dbagpt
ExecStart=/opt/dbagpt/venv/bin/python main.py --mode all
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl enable dbagpt
sudo systemctl start dbagpt
```

## Support

If you encounter issues:

1. **Check the logs:** `logs/dbagpt.log`
2. **Run diagnostics:** `python examples/basic_usage.py`
3. **Verify Ollama:** `ollama list`
4. **Test database connections** manually
5. **Check system resources:** CPU, memory, disk space

For additional help, please refer to the documentation or create an issue in the repository.

## Next Steps

After successful installation:

1. **Configure your databases** in `config.yaml`
2. **Test the AI assistant** with database questions
3. **Set up monitoring** for your databases
4. **Explore the web interface** for visual monitoring
5. **Integrate with your workflow** using the API

Welcome to DBA-GPT! 🚀 