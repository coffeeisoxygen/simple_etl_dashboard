"""Business-Focused Database Schema - Fresh Implementation.

Focused on actual business operations:
- 5 daily data streams (transaction, transfer, sellin, commission, retailer)
- 4 master data tables (villages, sites, staff, user auth)
- Clean structure aligned with business requirements
"""


class DatabaseSchema:
    """Business-focused database schema for telecom distribution."""

    # ================================
    # AUTHENTICATION & SYSTEM
    # ================================

    @staticmethod
    def get_user_table() -> str:
        """User authentication table."""
        return """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    @staticmethod
    def get_upload_batch_table() -> str:
        """Track CSV upload batches."""
        return """
        CREATE TABLE IF NOT EXISTS upload_batch (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL UNIQUE,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            records_count INTEGER DEFAULT 0,
            upload_status TEXT DEFAULT 'pending',
            error_message TEXT,
            uploaded_by TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        )
        """

    # ================================
    # DAILY OPERATIONS TABLES (5 core)
    # ================================

    @staticmethod
    def get_transaction_table() -> str:
        """Transaction data - customer purchases (11 core fields + metadata)."""
        return """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- Core business fields (11 required)
            datetime TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            transaction_id TEXT NOT NULL UNIQUE,
            organization_id TEXT NOT NULL,
            operator_id TEXT NOT NULL,
            product_group TEXT NOT NULL,
            product_name TEXT NOT NULL,
            main_price REAL NOT NULL DEFAULT 0,
            final_transaction_status TEXT NOT NULL,
            service_type TEXT,
            sp_status TEXT,

            -- Metadata JSON for additional fields
            metadata JSON,

            -- System fields
            upload_batch TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    @staticmethod
    def get_transfer_table() -> str:
        """Transfer data - balance distribution audit."""
        return """
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            transaction_id TEXT NOT NULL UNIQUE,
            organization_id TEXT NOT NULL,
            credit_party_name TEXT,
            amount REAL DEFAULT 0,
            debit_party_pre_balance REAL DEFAULT 0,
            debit_party_post_balance REAL DEFAULT 0,
            credit_party_pre_balance REAL DEFAULT 0,
            credit_party_post_balance REAL DEFAULT 0,
            transaction_status TEXT,

            -- Metadata JSON for additional fields
            metadata JSON,

            -- System fields
            upload_batch TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    @staticmethod
    def get_sellin_table() -> str:
        """Sellin data - staff KPI & distribution."""
        return """
        CREATE TABLE IF NOT EXISTS sellin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_datetime TEXT NOT NULL,
            transaction_id TEXT NOT NULL UNIQUE,
            organization_id TEXT NOT NULL,
            operator_id TEXT,
            operator_name TEXT,
            product_name TEXT,
            qty REAL DEFAULT 0,
            final_value REAL DEFAULT 0,

            -- Metadata JSON for additional fields
            metadata JSON,

            -- System fields
            upload_batch TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    @staticmethod
    def get_commission_table() -> str:
        """Commission data - sales margin analysis."""
        return """
        CREATE TABLE IF NOT EXISTS commissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            transaction_id TEXT NOT NULL UNIQUE,
            organization_id TEXT,
            incentive_source_organization TEXT,
            incentive_balance_amount REAL DEFAULT 0,
            schema_name TEXT,
            transaction_type TEXT,

            -- Metadata JSON for additional fields
            metadata JSON,

            -- System fields
            upload_batch TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    @staticmethod
    def get_retailer_table() -> str:
        """Retailer data - comprehensive retailer information + manual enhancements."""
        return """
        CREATE TABLE IF NOT EXISTS retailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- Core retailer info (from CSV)
            organization_id TEXT NOT NULL UNIQUE,
            organization_name TEXT NOT NULL,
            contact_number TEXT,
            province TEXT,
            city_district TEXT,
            districts TEXT,
            street_address TEXT,
            status TEXT,

            -- Manual enhancement fields (default values)
            longitude REAL DEFAULT 0.0,
            latitude REAL DEFAULT 0.0,
            chip_type TEXT DEFAULT 'unknown',
            notes TEXT DEFAULT '',
            is_manually_updated INTEGER DEFAULT 0,

            -- Complete retailer data as JSON
            metadata JSON,

            -- System fields
            upload_batch TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    # ================================
    # MASTER DATA TABLES (4 additional)
    # ================================

    @staticmethod
    def get_villages_table() -> str:
        """Villages data for geographic analysis."""
        return """
        CREATE TABLE IF NOT EXISTS villages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_name TEXT NOT NULL,
            district TEXT,
            city TEXT,
            province TEXT,
            population INTEGER DEFAULT 0,
            latitude REAL,
            longitude REAL,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    @staticmethod
    def get_sites_table() -> str:
        """Sites/BTS data for coverage analysis."""
        return """
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id TEXT NOT NULL UNIQUE,
            site_name TEXT NOT NULL,
            site_type TEXT DEFAULT 'BTS',
            village_name TEXT,
            latitude REAL,
            longitude REAL,
            address TEXT,
            coverage_radius REAL DEFAULT 0,
            status TEXT DEFAULT 'Active',
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    @staticmethod
    def get_staff_table() -> str:
        """Staff data for employee tracking."""
        return """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            contact TEXT,
            role TEXT,
            territory TEXT,
            supervisor_id TEXT,
            join_date TEXT,
            status TEXT DEFAULT 'Active',
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

    # ================================
    # SCHEMA MANAGEMENT
    # ================================

    @classmethod
    def get_core_tables(cls) -> list[str]:
        """Get core business tables creation SQL."""
        return [
            # System tables
            cls.get_user_table(),
            cls.get_upload_batch_table(),
            # Daily operations (5 core)
            cls.get_transaction_table(),
            cls.get_transfer_table(),
            cls.get_sellin_table(),
            cls.get_commission_table(),
            cls.get_retailer_table(),
            # Master data (4 additional)
            cls.get_villages_table(),
            cls.get_sites_table(),
            cls.get_staff_table(),
        ]

    @classmethod
    def get_core_indexes(cls) -> list[str]:
        """Get essential indexes for performance."""
        return [
            # User indexes
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users (is_active)",
            # Transaction indexes (most critical)
            "CREATE INDEX IF NOT EXISTS idx_transactions_id ON transactions (transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_org ON transactions (organization_id)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (datetime)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_product ON transactions (product_group)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_batch ON transactions (upload_batch)",
            # Transfer indexes
            "CREATE INDEX IF NOT EXISTS idx_transfers_id ON transfers (transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_transfers_org ON transfers (organization_id)",
            "CREATE INDEX IF NOT EXISTS idx_transfers_date ON transfers (datetime)",
            # Sellin indexes (staff KPI)
            "CREATE INDEX IF NOT EXISTS idx_sellin_id ON sellin (transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_sellin_org ON sellin (organization_id)",
            "CREATE INDEX IF NOT EXISTS idx_sellin_operator ON sellin (operator_id)",
            "CREATE INDEX IF NOT EXISTS idx_sellin_date ON sellin (transaction_datetime)",
            # Commission indexes
            "CREATE INDEX IF NOT EXISTS idx_commissions_id ON commissions (transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_commissions_org ON commissions (organization_id)",
            "CREATE INDEX IF NOT EXISTS idx_commissions_date ON commissions (datetime)",
            # Retailer indexes
            "CREATE INDEX IF NOT EXISTS idx_retailers_org ON retailers (organization_id)",
            "CREATE INDEX IF NOT EXISTS idx_retailers_district ON retailers (districts)",
            "CREATE INDEX IF NOT EXISTS idx_retailers_status ON retailers (status)",
            "CREATE INDEX IF NOT EXISTS idx_retailers_chip_type ON retailers (chip_type)",
            # Master data indexes
            "CREATE INDEX IF NOT EXISTS idx_villages_name ON villages (village_name)",
            "CREATE INDEX IF NOT EXISTS idx_villages_district ON villages (district)",
            "CREATE INDEX IF NOT EXISTS idx_sites_id ON sites (site_id)",
            "CREATE INDEX IF NOT EXISTS idx_sites_village ON sites (village_name)",
            "CREATE INDEX IF NOT EXISTS idx_staff_id ON staff (staff_id)",
            "CREATE INDEX IF NOT EXISTS idx_staff_role ON staff (role)",
            # Batch tracking
            "CREATE INDEX IF NOT EXISTS idx_batch_id ON upload_batch (batch_id)",
            "CREATE INDEX IF NOT EXISTS idx_batch_type ON upload_batch (file_type)",
        ]

    @classmethod
    def get_expected_table_names(cls) -> list[str]:
        """Get list of expected table names - NEW STRUCTURE."""
        return [
            # System
            "users",
            "upload_batch",
            # Daily operations
            "transactions",
            "transfers",
            "sellin",
            "commissions",
            "retailers",
            # Master data
            "villages",
            "sites",
            "staff",
        ]

    @classmethod
    def get_deprecated_tables(cls) -> list[str]:
        """Get list of OLD tables to remove - FRESH START."""
        return [
            # Old system tables
            "user",  # Rename to users
            "profile",
            "territory",
            "desa",
            # Remove unused tables
            "ioh_kecamatan",
            "ioh_desa",
            "podes",
            "spv",
            "kecamatan",
            # Old CSV tables (rename)
            "commission_data",  # → commissions
            "retailer_data",  # → retailers
            "sellin_data",  # → sellin
            "transaction_data",  # → transactions
            "transfer_data",  # → transfers
            "site",  # → sites
        ]

    @classmethod
    def cleanup_old_schema(cls, database_service) -> bool:
        """Remove deprecated tables - FRESH START approach."""
        try:
            deprecated_tables = cls.get_deprecated_tables()

            for table in deprecated_tables:
                try:
                    database_service.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"✅ Removed deprecated table: {table}")
                except Exception as e:
                    print(f"⚠️ Could not remove {table}: {e}")

            print("🧹 Schema cleanup completed")
            return True

        except Exception as e:
            print(f"❌ Schema cleanup failed: {e}")
            return False

    # ================================
    # BUSINESS LOGIC HELPERS
    # ================================

    @staticmethod
    def get_product_group_normalization_rule() -> str:
        """Business rule for product group normalization."""
        return """
        -- Product Group Normalization Logic:
        -- If product_name is all numeric → product_group = 'Pulsa'
        -- Example: product_name = '5000' → product_group = 'Pulsa'
        """

    @staticmethod
    def get_metadata_fields_mapping() -> dict[str, list[str]]:
        """Define which fields go to metadata JSON for each table."""
        return {
            "transactions": [
                "discount_idr",
                "discount_rule_name",
                "wallet_type",
                "region",
                "area",
                "channel",
                "msisdn",
                "bill_number",
                "voucher_type",
                "organization_name",
                "operator_name",
            ],
            "transfers": [
                "channel",
                "region",
                "area",
                "sales_area",
                "cluster",
                "organization_name",
                "operator_name",
                "status_description",
            ],
            "sellin": [
                "distribution_type",
                "product_category",
                "from_node",
                "dest_region",
                "discount_value",
                "rate_per_unit",
            ],
            "commissions": [
                "channel",
                "region",
                "area",
                "account_type",
                "incentive_koin_amount",
                "schema_id",
            ],
            "retailers": [
                "channel",
                "circle",
                "regional",
                "area",
                "branch",
                "micro_cluster",
                "partner_territory",
                "outlet_type",
                "organization_category",
                "visit_frequency",
            ],
        }


# TODO: Add migration script for existing data
# REMINDER: Business profile stored as JSON file (config/business_profile.json)
# NOTE: Product group normalization implemented in service layer
# FUTURE: Add data validation rules for each table
