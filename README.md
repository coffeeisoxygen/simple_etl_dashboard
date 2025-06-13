# Simple ETL Dashboard

> A streamlined ETL dashboard for sales data processing and visualization

## ✨ Features

- 📊 **Interactive Dashboard** - Real-time sales data visualization
- 🔄 **ETL Pipeline** - Automated data extraction, transformation, and loading
- 🔐 **Secure Authentication** - User management with bcrypt
- 📈 **Analytics** - Sales metrics and KPI tracking
- 🎨 **Modern UI** - Built with Streamlit

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- UV package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/coffeisoxygen/simple-etl-dashboard.git
cd simple-etl-dashboard

# Install dependencies
uv sync

# Run the dashboard
uv run streamlit run src/main.py
```

### Usage

1. **Start the application**

   ```bash
   uv run streamlit run src/main.py
   ```

2. **Access the dashboard**
   - Open <http://localhost:8501>
   - Login with default credentials (admin/admin)

3. **Upload your data**
   - Go to Data Upload page
   - Select your CSV file
   - Configure ETL settings

## 📖 Documentation

For detailed documentation, visit: **[Documentation Site](https://coffeeisoxygen.github.io/simple-etl-dashboard/)**

- [Installation Guide](docs/installation.md)
- [User Guide](docs/usage.md)
- [API Reference](docs/api/)
- [Development Setup](docs/development/)

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](docs/contributing.md) for details.

```bash
# Setup development environment
uv run python scripts/setup_dev.py

# Run tests
uv run pytest

# Check code quality
pre-commit run --all-files
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](https://coffeeisoxygen.github.io/simple-etl-dashboard/)
- 🐛 [Issue Tracker](https://github.com/coffeeisoxygen/simple-etl-dashboard/issues)
- 💬 [Discussions](https://github.com/coffeeisoxygen/simple-etl-dashboard/discussions)
