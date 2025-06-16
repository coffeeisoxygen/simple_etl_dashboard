# PLAN PROJECT STRUCTURE

src/
├── models/           # Data layer (SQLAlchemy ORM)
│   ├── __init__.py
│   ├── base.py       # Base model class
│   ├── transaction.py
│   ├── retailer.py
│   ├── master_data.py
│   └── database.py   # Connection & setup
├── services/         # Business logic layer
│   ├── __init__.py
│   ├── transaction_etl.py
│   ├── retailer_service.py
│   ├── master_data_service.py
│   └── auth_service.py
├── pages/           # UI layer (Streamlit pages)
│   ├── __init__.py
│   ├── dashboard.py
│   ├── master_data.py
│   ├── etl_monitor.py
│   └── settings.py
├── shared/          # Cross-cutting concerns
│   ├── __init__.py
│   ├── utils.py
│   ├── config.py
│   └── validators.py
└── components/      # Reusable UI components
    ├── __init__.py
    ├── charts.py
    └── forms.py
