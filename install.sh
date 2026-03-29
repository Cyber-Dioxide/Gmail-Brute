#!/bin/bash
# SMTP Tester Pro - Installation Script
# ======================================

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     SMTP Tester Pro v2.0 - Installation Script               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "[*] Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "[!] Python not found. Please install Python 3.x first."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "[+] Found Python $PYTHON_VERSION"

# Create virtual environment (optional)
read -p "Create virtual environment? (y/n): " CREATE_VENV
if [[ $CREATE_VENV == "y" || $CREATE_VENV == "Y" ]]; then
    echo "[*] Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
    echo "[+] Virtual environment activated"
fi

# Install dependencies
echo "[*] Installing dependencies..."
pip install -r requirements.txt

# Check if installation was successful
echo ""
echo "[*] Checking installation..."

$PYTHON_CMD -c "
try:
    import rich
    print('[+] rich: OK')
except ImportError:
    print('[-] rich: NOT INSTALLED')

try:
    import socks
    print('[+] PySocks: OK')
except ImportError:
    print('[-] PySocks: NOT INSTALLED')

try:
    import dns.resolver
    print('[+] dnspython: OK')
except ImportError:
    print('[-] dnspython: NOT INSTALLED (optional, for utils)')
"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Installation Complete!                          ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  Quick Start:                                                ║"
echo "║  $ python smtp_tester.py --help                              ║"
echo "║                                                              ║"
echo "║  Interactive Mode:                                           ║"
echo "║  $ python smtp_tester.py                                     ║"
echo "║                                                              ║"
echo "║  Command Line Mode:                                          ║"
echo "║  $ python smtp_tester.py -H smtp.gmail.com -P 587 \\          ║"
echo "║      -e data/emails.txt -p data/passwords.txt                ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
