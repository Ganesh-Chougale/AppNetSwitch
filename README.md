# AppNetSwitch

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PyPI - PyQt6](https://img.shields.io/badge/PyQt6-6.1.0-41cd52)](https://pypi.org/project/PyQt6/)

A powerful application firewall and network manager that allows you to control network access for your applications. Built with Python and PyQt6, AppNetSwitch provides an intuitive interface to manage which applications can access the internet.

## ✨ Features

- 📱 View all running applications
- 🔄 Block/Unblock internet access for specific applications
- 🛡️ Windows firewall integration
- 🔍 Quick search and filter applications
- 🎨 Modern and responsive UI
- 💾 Persistent settings storage

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Windows OS (Linux support planned)
- Administrator privileges (required for firewall rules)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Ganesh-Chougale/AppNetSwitch.git
   cd AppNetSwitch/App
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Run the application with administrator privileges:
   ```bash
   python main.py
   ```

   Note: Administrator rights are required to manage Windows Firewall rules.

## 🛠️ Building from Source

To create a standalone executable:

```bash
pyinstaller --onefile --windowed --icon=Extras/File_Icon.ico --name AppNetSwitch main.py
```

The executable will be available in the `dist` directory.

## 📦 Dependencies

- PyQt6 >= 6.1.0
- psutil
- pywin32

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

- **Ganesh Chougale**
  - [GitHub](https://github.com/Ganesh-Chougale)
  - [Portfolio](https://ganesh-chougale.github.io/)
  - [LinkedIn](https://www.linkedin.com/in/ganesh-chougale-512449215/)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📌 Note

- This application requires administrator privileges to manage Windows Firewall rules.
- Make sure to run the application as administrator for full functionality.
- Use at your own risk. The developers are not responsible for any network or system issues.

---

<div align="center">
  Made with ❤️ by Ganesh Chougale
</div>
