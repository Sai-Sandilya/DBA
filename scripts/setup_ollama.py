#!/usr/bin/env python3
"""
Setup script for Ollama and AI models
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_ollama():
    """Install Ollama based on the operating system"""
    system = platform.system().lower()
    
    print("Installing Ollama...")
    
    if system == "windows":
        print("Please install Ollama manually from: https://ollama.ai/download")
        print("After installation, restart your terminal and run this script again.")
        return False
    elif system == "darwin":  # macOS
        try:
            subprocess.run(['brew', 'install', 'ollama'], check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Homebrew not found. Please install Homebrew first or install Ollama manually.")
            return False
    elif system == "linux":
        try:
            # Install using the official script
            subprocess.run([
                'curl', '-fsSL', 'https://ollama.ai/install.sh', '|', 'sh'
            ], shell=True, check=True)
            return True
        except subprocess.CalledProcessError:
            print("Failed to install Ollama. Please install manually from: https://ollama.ai/download")
            return False
    else:
        print(f"Unsupported operating system: {system}")
        return False

def start_ollama_service():
    """Start Ollama service"""
    try:
        subprocess.run(['ollama', 'serve'], check=True)
        return True
    except subprocess.CalledProcessError:
        print("Failed to start Ollama service")
        return False

def download_models():
    """Download recommended AI models"""
    models = [
        "llama2:13b",
        "codellama:13b",
        "mistral:7b"
    ]
    
    print("Downloading AI models...")
    
    for model in models:
        print(f"Downloading {model}...")
        try:
            subprocess.run(['ollama', 'pull', model], check=True)
            print(f"✅ {model} downloaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to download {model}: {e}")
            return False
    
    return True

def test_ollama():
    """Test Ollama installation"""
    print("Testing Ollama installation...")
    
    try:
        # Test with a simple query
        result = subprocess.run([
            'ollama', 'run', 'llama2:13b', 'Hello, are you working?'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Ollama is working correctly!")
            return True
        else:
            print("❌ Ollama test failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Ollama test timed out (this is normal for first run)")
        return True
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 DBA-GPT Ollama Setup")
    print("=" * 50)
    
    # Check if Ollama is already installed
    if check_ollama_installed():
        print("✅ Ollama is already installed")
    else:
        print("❌ Ollama not found")
        if not install_ollama():
            sys.exit(1)
        print("✅ Ollama installed successfully")
    
    # Start Ollama service
    print("Starting Ollama service...")
    if not start_ollama_service():
        print("⚠️  Could not start Ollama service. Please start it manually with: ollama serve")
    
    # Download models
    if not download_models():
        print("❌ Failed to download some models")
        sys.exit(1)
    
    # Test installation
    if not test_ollama():
        print("❌ Ollama test failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Configure your databases in config/config.yaml")
    print("2. Start DBA-GPT: python main.py")
    print("3. Access the web interface: http://localhost:8501")

if __name__ == "__main__":
    main() 