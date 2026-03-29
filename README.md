<div align="center">

# 🔥 SMTP Tester Pro v2.0

### Advanced SMTP Credential Testing Tool

**A standalone, asynchronous SMTP testing tool with proxy support, beautiful UI, and comprehensive features**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-green?style=for-the-badge)](https://github.com/Cyber-Dioxide/Gmail-Brute)
[![License](https://img.shields.io/badge/License-Educational-yellow?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Cyber-Dioxide/Gmail-Brute?style=for-the-badge)](https://github.com/Cyber-Dioxide/Gmail-Brute/stargazers)

<img width="1348" height="795" alt="Screenshot from 2026-03-20 12-45-17" src="https://github.com/user-attachments/assets/14a06354-d0bb-4684-992f-790117f86bf8" />

</div>

---

## 🚀 What's New in v2.0

> **Complete Rewrite!** This version has been rebuilt from scratch with modern features:

| Feature | Description |
|---------|-------------|
| ⚡ **Async Support** | Parallel testing with asyncio for 10x faster checks |
| 🎨 **Beautiful UI** | Rich terminal interface with progress bars and colors |
| 🌐 **Multi-Proxy** | HTTP, SOCKS4, SOCKS5, and Rotating proxy support |
| 🔐 **SSL/TLS Options** | STARTTLS, SSL, TLS, and plain text support |
| 📊 **Statistics** | Real-time stats, success rates, and proxy performance |
| 💾 **Export Formats** | TXT, JSON, CSV export options |
| 🔄 **Resume Mode** | Skip already tested credentials |
| ⚙️ **Config Files** | JSON and YAML configuration support |

---

## ⚠️ Important Note

> **Proxy Quality Matters!** If you're experiencing issues where correct passwords aren't being detected, it's likely due to low-quality proxies. Use **HQ checked proxies** for best results.
> 
> The new v2.0 includes optional proxy support - you can now run without proxies for testing!

---

## 📥 Installation

### Windows (One-Click Install)

```batch
# Simply double-click install_windows.bat
# OR run in Command Prompt:
install_windows.bat
```

The Windows installer will:
- ✅ Check if Python is installed
- ✅ Download and install Python automatically if needed
- ✅ Install all dependencies
- ✅ Create sample data files
- ✅ Launch the tool

### Linux / macOS

```bash
# Clone the repository
git clone https://github.com/Cyber-Dioxide/Gmail-Brute
cd Gmail-Brute

# Run installer
chmod +x install.sh
./install.sh

# Or manual install
pip install -r requirements.txt
python smtp_tester.py
```

### Kali Linux

```bash
git clone https://github.com/Cyber-Dioxide/Gmail-Brute
cd Gmail-Brute
pip install -r requirements.txt
python smtp_tester.py
```

---

## 🎯 Quick Start

### Interactive Mode (Easiest)

```bash
python smtp_tester.py
```

Just follow the prompts! No command-line knowledge required.

### Quick Command Line

```bash
# Gmail
python smtp_tester.py -H smtp.gmail.com -P 587 -e data/emails.txt -p data/passwords.txt

# Outlook
python smtp_tester.py -H smtp-mail.outlook.com -P 587 -e data/emails.txt -p data/passwords.txt

# With Proxy
python smtp_tester.py -H smtp.gmail.com -P 587 -e emails.txt -p passwords.txt --proxy-type socks5 --proxy-list proxies.txt
```

---

## 📋 Common SMTP Servers

| Provider | Host | Port | Security |
|----------|------|------|----------|
| Gmail | `smtp.gmail.com` | 587 | STARTTLS |
| Gmail (SSL) | `smtp.gmail.com` | 465 | SSL |
| Outlook | `smtp-mail.outlook.com` | 587 | STARTTLS |
| Yahoo | `smtp.mail.yahoo.com` | 587 | STARTTLS |
| iCloud | `smtp.mail.me.com` | 587 | STARTTLS |
| Office 365 | `smtp.office365.com` | 587 | STARTTLS |

---

## 🎮 Features

### 🌐 Proxy Support

| Type | Description | Use Case |
|------|-------------|----------|
| **HTTP** | Standard HTTP proxy | Basic anonymity |
| **SOCKS4** | SOCKS4 protocol | TCP connections |
| **SOCKS5** | SOCKS5 with auth support | Most compatible |
| **Rotating** | Auto-rotate through list | Large-scale testing |

### ⚡ Performance Options

```bash
--workers 20          # Number of threads (default: 10)
--async-tasks 100     # Async tasks (default: 50)
--rate-limit 10       # Requests per second (0=unlimited)
--retry 3             # Retry attempts (default: 3)
--timeout 60          # Connection timeout (default: 30)
```

### 📊 Export Options

```bash
-f txt      # Plain text report
-f json     # Structured JSON data
-f csv      # Spreadsheet compatible
-f all      # All formats at once
```

---

## 🛠️ Utility Tools

SMTP Tester Pro includes powerful utilities:

```bash
# Grab SMTP banner and server info
python utils.py banner smtp.gmail.com -p 587

# Lookup MX records for a domain
python utils.py mx gmail.com

# Validate email address
python utils.py validate user@gmail.com --verify

# Scan ports for SMTP services
python utils.py scan mail.example.com
```

---

## 📁 Project Structure

```
Gmail-Brute/
├── smtp_tester.py          # Main application
├── utils.py                # Utility tools
├── requirements.txt        # Dependencies
├── config.json             # Sample configuration
├── install_windows.bat     # Windows installer
├── run_interactive.bat     # Interactive mode launcher
├── run_quick.bat           # Quick start wizard
├── run_utils.bat           # Utilities menu
├── install.sh              # Linux/macOS installer
├── SMTP_Tester_Pro_User_Guide.pdf  # Comprehensive guide
└── data/
    ├── emails.txt          # Email list
    ├── passwords.txt       # Password list
    └── proxies.txt         # Proxy list
```

---

## 📖 Documentation

A comprehensive **PDF User Guide** is included:

- ✅ Windows Installation Guide
- ✅ Linux Installation Guide  
- ✅ VirtualBox Setup Instructions
- ✅ Command Line Reference
- ✅ Configuration Files
- ✅ Proxy Configuration
- ✅ Troubleshooting Guide

> 📄 See `SMTP_Tester_Pro_User_Guide.pdf` for complete documentation.

---

## 📺 Screenshots

<div align="center">

<img width="1348" height="795" alt="Screenshot from 2026-03-20 12-45-17" src="https://github.com/user-attachments/assets/233dc852-24a7-46be-9352-ec995521ceaa" />

</div>

---

## ⚙️ Command Line Reference

<details>
<summary>📖 Click to expand full command reference</summary>

### SMTP Settings
| Argument | Description | Default |
|----------|-------------|---------|
| `-H, --host` | SMTP server host | Required |
| `-P, --port` | SMTP server port | 587 |
| `--security` | Security mode (none/ssl/tls/starttls) | starttls |
| `--timeout` | Connection timeout | 30 |

### Input Files
| Argument | Description | Default |
|----------|-------------|---------|
| `-e, --emails` | Email list file | emails.txt |
| `-p, --passwords` | Password list file | passwords.txt |

### Proxy Settings
| Argument | Description | Default |
|----------|-------------|---------|
| `--proxy` | Single proxy (protocol://host:port) | None |
| `--proxy-list` | Proxy list file | None |
| `--proxy-type` | Type (none/http/socks4/socks5/rotating) | none |

### Output Settings
| Argument | Description | Default |
|----------|-------------|---------|
| `-o, --output` | Output directory | results |
| `-f, --format` | Format (txt/json/csv/all) | txt |
| `--no-save-tried` | Don't save tried credentials | False |
| `--no-resume` | Don't resume from previous session | False |

</details>

---

## 💖 Support This Project

<div align="center">

### ⭐ If this tool helped you, please consider supporting development!

[![Donate](https://img.shields.io/badge/💰_Donate-$20-support_development-success?style=for-the-badge&logo=heart&logoColor=white)](https://hiderox.com/payment.html?amt=20)

**Your support keeps this project alive and updated!**

Building and maintaining open-source security tools takes countless hours of development, testing, and documentation. By supporting this project, you help:

- 🚀 **Fund new features** and improvements
- 🐛 **Fix bugs** and issues faster
- 📚 **Create better documentation** and tutorials
- 🔒 **Keep the tool updated** with latest security practices

**Every contribution matters!** Whether it's $5 or $50, your support directly impacts the future of this tool.

[![Support Development](https://img.shields.io/badge/Support_Development-Click_Here-blue?style=for-the-badge)](https://hiderox.com/payment.html?amt=20)

</div>

---

## 📞 Contact & Support

<div align="center">

| Platform | Link |
|----------|------|
| 📱 **Telegram Channel** | [https://t.me/cyox2](https://t.me/cyox2) |
| 💬 **Telegram DM** | [Contact Me](https://t.me/cyberoxide) |
| 📷 **Instagram** | [@coding_memz](https://instagram.com/coding_memz) |
| 🌐 **Website** | [Cyber Dioxide](https://www.cyox2.com) |
| 📧 **Blog Tutorial** | [How to Use Guide](https://www.cyox2.com/2023/11/gmail-bruteforce-how-to-perform-and-how.html) |

</div>

---

## 🎓 Services Offered

| Service | Description | Contact |
|---------|-------------|---------|
| 🔓 **Account Recovery** | Professional bruteforce service | DM on Instagram |
| 🛠️ **Custom Tools** | Get your own custom hacking tool | DM on Instagram |
| 📋 **Password Lists** | 14M+ world's most used passwords | DM on Instagram |
| 📚 **Hacking Course** | Comprehensive ethical hacking course | DM on Instagram |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ⚖️ Legal Disclaimer

> **This tool is for educational and authorized testing purposes only.**
> 
> - Only test accounts you own or have explicit permission to test
> - Use responsibly and comply with local laws and regulations
> - The developers are not responsible for any misuse of this tool
> - Unauthorized access to computer systems is illegal

---

## 📜 License

This project is licensed for educational purposes. See the repository for more details.

---

<div align="center">

**Made with ❤️ by [Cyber Dioxide](https://github.com/Cyber-Dioxide)**

**⭐ Don't forget to star this repo if you found it useful! ⭐**

[![Star](https://img.shields.io/github/stars/Cyber-Dioxide/Gmail-Brute?style=social)](https://github.com/Cyber-Dioxide/Gmail-Brute/stargazers)

</div>
