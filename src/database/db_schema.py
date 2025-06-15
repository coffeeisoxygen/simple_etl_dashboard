"""Database schema based on finalized apps.dbml - Single Source of Truth."""

from typing import TypedDict


class SchemaValidationResult(TypedDict):
    """Type definition for schema validation results."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    statistics: dict[str, int]


class DatabaseSchema:
    """Database schema aligned with apps.dbml - Master/Monthly partitioning strategy."""

    # ================================
    # MASTER DATABASE TABLES
    # ================================

    @staticmethod
    def get_user_table() -> str:
        """User authentication table."""
        return """
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                CHECK (length(username) >= 3),
                CHECK (length(password_hash) > 0),
                CHECK (is_active IN (0, 1)),
                CHECK (is_admin IN (0, 1))
            )
        """

    @staticmethod
    def get_profile_table() -> str:
        """Business entity profile information."""
        return """
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                org_id TEXT NOT NULL UNIQUE,
                org_name TEXT NOT NULL,
                business_type TEXT NOT NULL,
                business_name TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                pic_name TEXT NOT NULL,
                pic_phone TEXT NOT NULL,
                circle_name TEXT NOT NULL,
                region_name TEXT NOT NULL,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE ON UPDATE CASCADE,

                CHECK (length(org_id) > 0),
                CHECK (length(org_name) > 0),
                CHECK (business_type IN ('perorangan', 'PT', 'CV', 'UD')),
                CHECK (length(phone) >= 10),
                CHECK (email LIKE '%@%')
            )
        """

    @staticmethod
    def get_territory_table() -> str:
        """Territory management - each territory managed by one business entity."""
        return """
            CREATE TABLE IF NOT EXISTS territory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                territory_type TEXT NOT NULL,
                territory_name TEXT NOT NULL,
                territory_code TEXT UNIQUE,
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (profile_id) REFERENCES profile(id) ON DELETE CASCADE ON UPDATE CASCADE,

                CHECK (territory_type IN ('MC', 'PT')),
                CHECK (length(territory_name) > 0)
            )
        """

    @staticmethod
    def get_desa_table() -> str:
        """Village master data - administrative boundaries represented by center coordinates."""
        return """
            CREATE TABLE IF NOT EXISTS desa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                nama_desa TEXT NOT NULL,
                kode_desa TEXT UNIQUE,
                populasi INTEGER NOT NULL,
                luas_wilayah REAL NOT NULL,
                kecamatan TEXT NOT NULL,
                kabupaten TEXT NOT NULL,
                provinsi TEXT NOT NULL,
                koordinat_center_lat REAL,
                koordinat_center_lng REAL,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,

                CHECK (length(nama_desa) > 0),
                CHECK (populasi >= 0),
                CHECK (luas_wilayah > 0),
                CHECK (koordinat_center_lat IS NULL OR (koordinat_center_lat >= -90 AND koordinat_center_lat <= 90)),
                CHECK (koordinat_center_lng IS NULL OR (koordinat_center_lng >= -180 AND koordinat_center_lng <= 180))
            )
        """

    @staticmethod
    def get_site_table() -> str:
        """Telecom site/tower data - exact point coordinates for technical infrastructure."""
        return """
            CREATE TABLE IF NOT EXISTS site (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                site_code TEXT NOT NULL UNIQUE,
                site_name TEXT NOT NULL,
                site_type TEXT NOT NULL,
                koordinat_lat REAL NOT NULL,
                koordinat_lng REAL NOT NULL,
                tinggi_menara INTEGER,
                alamat TEXT,
                status_operasi TEXT DEFAULT 'active',
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,

                CHECK (length(site_code) > 0),
                CHECK (length(site_name) > 0),
                CHECK (site_type IN ('BTS', 'NodeB', 'eNodeB', 'gNodeB', 'Femtocell', 'Microcell')),
                CHECK (koordinat_lat >= -90 AND koordinat_lat <= 90),
                CHECK (koordinat_lng >= -180 AND koordinat_lng <= 180),
                CHECK (tinggi_menara IS NULL OR tinggi_menara > 0),
                CHECK (status_operasi IN ('active', 'inactive', 'maintenance', 'decommissioned'))
            )
        """

    @staticmethod
    def get_monthly_database_registry_table() -> str:
        """Registry for monthly database file tracking - supports partitioning strategy."""
        return """
            CREATE TABLE IF NOT EXISTS monthly_database_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_period TEXT NOT NULL UNIQUE,
                database_file TEXT NOT NULL,
                territory_id INTEGER NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                total_records INTEGER DEFAULT 0,
                file_size INTEGER DEFAULT 0,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_access_date DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,

                CHECK (month_period LIKE '____-__'),
                CHECK (status IN ('ACTIVE', 'ARCHIVED', 'DELETED')),
                CHECK (total_records >= 0),
                CHECK (file_size >= 0)
            )
        """

    @staticmethod
    def get_activity_log_table() -> str:
        """Enhanced activity audit trail including retailer data synchronization.

        NOTE: This table exists for future database-based activity logging if needed.
        Currently using file-based logging approach for better reliability.
        """
        return """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                session_id TEXT,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL ON UPDATE CASCADE,

                CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'IMPORT', 'SYNC_RETAILER')),
                CHECK (status IN ('success', 'failed', 'unauthorized')),
                CHECK (length(action) > 0)
            )
        """

    # ================================
    # MONTHLY DATABASE TABLES
    # ================================

    @staticmethod
    def get_csv_import_log_table() -> str:
        """ETL import log - tracks CSV processing per month including retailer data updates."""
        return """
            CREATE TABLE IF NOT EXISTS csv_import_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'PENDING',
                total_records INTEGER,
                processed_records INTEGER,
                error_records INTEGER,
                error_details TEXT,
                territory_id INTEGER NOT NULL,
                month_period TEXT NOT NULL,

                CHECK (file_type IN ('TRANSACTION', 'KOMISI', 'TRANSFER', 'SELLIN', 'VISIT', 'ALLOC', 'RETAILER')),
                CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'PARTIAL')),
                CHECK (file_size IS NULL OR file_size > 0),
                CHECK (total_records IS NULL OR total_records >= 0),
                CHECK (processed_records IS NULL OR processed_records >= 0),
                CHECK (error_records IS NULL OR error_records >= 0),
                CHECK (month_period LIKE '____-__')
            )
        """

    @staticmethod
    def get_ioh_transaction_data_table() -> str:
        """IOH transaction data storage - JSON format for flexibility with retailer linkage."""
        return """
            CREATE TABLE IF NOT EXISTS ioh_transaction_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                data_date DATE NOT NULL,
                transaction_id TEXT,
                retailer_code TEXT,
                data_json TEXT NOT NULL,
                import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                csv_import_log_id INTEGER,

                CHECK (json_valid(data_json)),
                CHECK (length(data_json) > 0)
            )
        """

    @staticmethod
    def get_ioh_commission_data_table() -> str:
        """IOH commission data storage - JSON format for flexibility with retailer linkage."""
        return """
            CREATE TABLE IF NOT EXISTS ioh_commission_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                data_date DATE NOT NULL,
                transaction_id TEXT,
                retailer_code TEXT,
                commission_amount REAL,
                data_json TEXT NOT NULL,
                import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                csv_import_log_id INTEGER,

                CHECK (json_valid(data_json)),
                CHECK (length(data_json) > 0),
                CHECK (commission_amount IS NULL OR commission_amount >= 0)
            )
        """

    @staticmethod
    def get_ioh_transfer_data_table() -> str:
        """IOH transfer data storage - JSON format for flexibility with retailer linkage."""
        return """
            CREATE TABLE IF NOT EXISTS ioh_transfer_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                data_date DATE NOT NULL,
                transfer_id TEXT,
                retailer_code TEXT,
                amount REAL,
                data_json TEXT NOT NULL,
                import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                csv_import_log_id INTEGER,

                CHECK (json_valid(data_json)),
                CHECK (length(data_json) > 0),
                CHECK (amount IS NULL OR amount >= 0)
            )
        """

    @staticmethod
    def get_ioh_sellin_data_table() -> str:
        """IOH sell-in/distribution data storage - JSON format for flexibility with retailer linkage."""
        return """
            CREATE TABLE IF NOT EXISTS ioh_sellin_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                data_date DATE NOT NULL,
                transaction_id TEXT,
                reference_order_number TEXT,
                organization_id TEXT,
                dest_organization_id TEXT,
                product_code TEXT,
                quantity INTEGER,
                final_value REAL,
                data_json TEXT NOT NULL,
                import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                csv_import_log_id INTEGER,

                CHECK (json_valid(data_json)),
                CHECK (length(data_json) > 0),
                CHECK (quantity IS NULL OR quantity >= 0),
                CHECK (final_value IS NULL OR final_value >= 0)
            )
        """

    @staticmethod
    def get_ioh_retailer_data_table() -> str:
        """Monthly retailer data - consistent with other IOH data patterns."""
        return """
            CREATE TABLE IF NOT EXISTS ioh_retailer_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                data_date DATE NOT NULL,
                retailer_code TEXT NOT NULL,
                retailer_name TEXT NOT NULL,
                koordinat_lat REAL,
                koordinat_lng REAL,
                chip_type TEXT,
                data_json TEXT NOT NULL,
                import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                csv_import_log_id INTEGER,

                CHECK (json_valid(data_json)),
                CHECK (length(data_json) > 0),
                CHECK (length(retailer_code) > 0),
                CHECK (length(retailer_name) > 0),
                CHECK (koordinat_lat IS NULL OR (koordinat_lat >= -90 AND koordinat_lat <= 90)),
                CHECK (koordinat_lng IS NULL OR (koordinat_lng >= -180 AND koordinat_lng <= 180)),
                CHECK (chip_type IS NULL OR chip_type IN ('REAL', 'ON_HAND', 'REVITALISASI', 'EDIT_ENTI')),

                UNIQUE (territory_id, retailer_code, data_date)
            )
        """

    @staticmethod
    def get_daily_summary_table() -> str:
        """Enhanced daily summaries including retailer geographic and chip type metrics."""
        return """
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                summary_date DATE NOT NULL,
                transaction_count INTEGER DEFAULT 0,
                total_transaction_amount REAL DEFAULT 0,
                total_commission_amount REAL DEFAULT 0,
                total_transfer_amount REAL DEFAULT 0,
                total_sellin_amount REAL DEFAULT 0,
                sellin_transaction_count INTEGER DEFAULT 0,
                active_retailers INTEGER DEFAULT 0,
                retailers_with_coordinates INTEGER DEFAULT 0,
                retailers_by_chip_type_json TEXT,
                summary_json TEXT,
                calculated_date DATETIME DEFAULT CURRENT_TIMESTAMP,

                CHECK (transaction_count >= 0),
                CHECK (total_transaction_amount >= 0),
                CHECK (total_commission_amount >= 0),
                CHECK (total_transfer_amount >= 0),
                CHECK (total_sellin_amount >= 0),
                CHECK (sellin_transaction_count >= 0),
                CHECK (active_retailers >= 0),
                CHECK (retailers_with_coordinates >= 0),
                CHECK (retailers_by_chip_type_json IS NULL OR json_valid(retailers_by_chip_type_json)),
                CHECK (summary_json IS NULL OR json_valid(summary_json)),

                UNIQUE (territory_id, summary_date)
            )
        """

    # ================================
    # SCHEMA MANAGEMENT METHODS
    # ================================

    @classmethod
    def get_master_database_tables(cls) -> list[str]:
        """Get master database table creation statements in dependency order."""
        return [
            cls.get_user_table(),
            cls.get_profile_table(),
            cls.get_territory_table(),
            cls.get_desa_table(),
            cls.get_site_table(),
            cls.get_monthly_database_registry_table(),
            cls.get_activity_log_table(),  # REVIEW: Consider removing if file-based logging is permanent
        ]

    @classmethod
    def get_monthly_database_tables(cls) -> list[str]:
        """Get monthly database table creation statements."""
        return [
            cls.get_csv_import_log_table(),
            cls.get_ioh_transaction_data_table(),
            cls.get_ioh_commission_data_table(),
            cls.get_ioh_transfer_data_table(),
            cls.get_ioh_sellin_data_table(),
            cls.get_ioh_retailer_data_table(),
            cls.get_daily_summary_table(),
        ]

    @classmethod
    def get_master_indexes(cls) -> list[str]:
        """Get indexes for master database."""
        return [
            # User table indexes
            "CREATE INDEX IF NOT EXISTS idx_user_username ON user(username)",
            "CREATE INDEX IF NOT EXISTS idx_user_active ON user(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_tgl_data ON user(tgl_data)",
            # Profile table indexes
            "CREATE INDEX IF NOT EXISTS idx_profile_user_id ON profile(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_profile_org_id ON profile(org_id)",
            "CREATE INDEX IF NOT EXISTS idx_profile_circle_region ON profile(circle_name, region_name)",
            # Territory table indexes
            "CREATE INDEX IF NOT EXISTS idx_territory_profile_id ON territory(profile_id)",
            "CREATE INDEX IF NOT EXISTS idx_territory_code ON territory(territory_code)",
            "CREATE INDEX IF NOT EXISTS idx_territory_type ON territory(territory_type)",
            # Desa table indexes
            "CREATE INDEX IF NOT EXISTS idx_desa_territory_id ON desa(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_desa_kode ON desa(kode_desa)",
            "CREATE INDEX IF NOT EXISTS idx_desa_admin ON desa(kecamatan, kabupaten, provinsi)",
            "CREATE INDEX IF NOT EXISTS idx_desa_koordinat ON desa(koordinat_center_lat, koordinat_center_lng)",
            # Site table indexes
            "CREATE INDEX IF NOT EXISTS idx_site_territory_id ON site(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_site_code ON site(site_code)",
            "CREATE INDEX IF NOT EXISTS idx_site_type ON site(site_type)",
            "CREATE INDEX IF NOT EXISTS idx_site_koordinat ON site(koordinat_lat, koordinat_lng)",
            "CREATE INDEX IF NOT EXISTS idx_site_status ON site(status_operasi)",
            # Monthly database registry indexes
            "CREATE INDEX IF NOT EXISTS idx_monthly_registry_period ON monthly_database_registry(month_period)",
            "CREATE INDEX IF NOT EXISTS idx_monthly_registry_territory ON monthly_database_registry(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_monthly_registry_status ON monthly_database_registry(status)",
            # Activity log indexes - REVIEW: Remove if file-based logging is permanent
            "CREATE INDEX IF NOT EXISTS idx_activity_user_id ON activity_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action)",
            "CREATE INDEX IF NOT EXISTS idx_activity_table_name ON activity_log(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_activity_user_timestamp ON activity_log(user_id, timestamp)",
        ]

    @classmethod
    def get_monthly_indexes(cls) -> list[str]:
        """Get indexes for monthly database."""
        return [
            # CSV import log indexes
            "CREATE INDEX IF NOT EXISTS idx_csv_import_file_type ON csv_import_log(file_type)",
            "CREATE INDEX IF NOT EXISTS idx_csv_import_status ON csv_import_log(status)",
            "CREATE INDEX IF NOT EXISTS idx_csv_import_date ON csv_import_log(import_date)",
            "CREATE INDEX IF NOT EXISTS idx_csv_import_territory ON csv_import_log(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_csv_import_month_period ON csv_import_log(month_period)",
            # IOH transaction data indexes
            "CREATE INDEX IF NOT EXISTS idx_transaction_territory_date ON ioh_transaction_data(territory_id, data_date)",
            "CREATE INDEX IF NOT EXISTS idx_transaction_retailer_code ON ioh_transaction_data(retailer_code)",
            "CREATE INDEX IF NOT EXISTS idx_transaction_date ON ioh_transaction_data(data_date)",
            "CREATE INDEX IF NOT EXISTS idx_transaction_import_date ON ioh_transaction_data(import_date)",
            # IOH commission data indexes
            "CREATE INDEX IF NOT EXISTS idx_commission_territory_date ON ioh_commission_data(territory_id, data_date)",
            "CREATE INDEX IF NOT EXISTS idx_commission_retailer_code ON ioh_commission_data(retailer_code)",
            "CREATE INDEX IF NOT EXISTS idx_commission_transaction_id ON ioh_commission_data(transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_commission_date ON ioh_commission_data(data_date)",
            # IOH transfer data indexes
            "CREATE INDEX IF NOT EXISTS idx_transfer_territory_date ON ioh_transfer_data(territory_id, data_date)",
            "CREATE INDEX IF NOT EXISTS idx_transfer_retailer_code ON ioh_transfer_data(retailer_code)",
            "CREATE INDEX IF NOT EXISTS idx_transfer_date ON ioh_transfer_data(data_date)",
            # IOH sell-in data indexes
            "CREATE INDEX IF NOT EXISTS idx_sellin_territory_date ON ioh_sellin_data(territory_id, data_date)",
            "CREATE INDEX IF NOT EXISTS idx_sellin_transaction_id ON ioh_sellin_data(transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_sellin_organization_id ON ioh_sellin_data(organization_id)",
            "CREATE INDEX IF NOT EXISTS idx_sellin_dest_organization_id ON ioh_sellin_data(dest_organization_id)",
            "CREATE INDEX IF NOT EXISTS idx_sellin_product_code ON ioh_sellin_data(product_code)",
            "CREATE INDEX IF NOT EXISTS idx_sellin_date ON ioh_sellin_data(data_date)",
            # IOH retailer data indexes
            "CREATE INDEX IF NOT EXISTS idx_retailer_territory_date ON ioh_retailer_data(territory_id, data_date)",
            "CREATE INDEX IF NOT EXISTS idx_retailer_code ON ioh_retailer_data(retailer_code)",
            "CREATE INDEX IF NOT EXISTS idx_retailer_chip_type ON ioh_retailer_data(chip_type)",
            "CREATE INDEX IF NOT EXISTS idx_retailer_koordinat ON ioh_retailer_data(koordinat_lat, koordinat_lng)",
            # Daily summary indexes
            "CREATE INDEX IF NOT EXISTS idx_daily_summary_territory_date ON daily_summary(territory_id, summary_date)",
            "CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_summary(summary_date)",
        ]

    @classmethod
    def get_master_views(cls) -> list[str]:
        """Get views for master database analytics."""
        return [
            """
            CREATE VIEW IF NOT EXISTS v_territory_overview AS
            SELECT
                t.id as territory_id,
                t.territory_name,
                t.territory_type,
                p.org_name,
                p.business_name,
                p.circle_name,
                p.region_name,
                COUNT(DISTINCT d.id) as total_desa,
                COUNT(DISTINCT s.id) as total_sites,
                SUM(d.populasi) as total_populasi,
                AVG(d.luas_wilayah) as avg_luas_wilayah
            FROM territory t
            LEFT JOIN profile p ON t.profile_id = p.id
            LEFT JOIN desa d ON t.id = d.territory_id
            LEFT JOIN site s ON t.id = s.territory_id
            GROUP BY t.id, t.territory_name, t.territory_type, p.org_name, p.business_name, p.circle_name, p.region_name
            """,
            """
            CREATE VIEW IF NOT EXISTS v_monthly_database_status AS
            SELECT
                mdr.month_period,
                t.territory_name,
                mdr.status,
                mdr.total_records,
                ROUND(mdr.file_size / 1024.0 / 1024.0, 2) as file_size_mb,
                mdr.created_date,
                mdr.last_access_date,
                julianday('now') - julianday(mdr.last_access_date) as days_since_access
            FROM monthly_database_registry mdr
            LEFT JOIN territory t ON mdr.territory_id = t.id
            ORDER BY mdr.month_period DESC, t.territory_name
            """,
            """
            CREATE VIEW IF NOT EXISTS v_site_coverage_analysis AS
            SELECT
                d.nama_desa,
                d.populasi,
                d.luas_wilayah,
                t.territory_name,
                COUNT(s.id) as site_count,
                CASE
                    WHEN COUNT(s.id) = 0 THEN 'No Coverage'
                    WHEN COUNT(s.id) = 1 THEN 'Single Site'
                    ELSE 'Multiple Sites'
                END as coverage_status,
                ROUND(d.populasi / NULLIF(COUNT(s.id), 0), 0) as population_per_site
            FROM desa d
            LEFT JOIN territory t ON d.territory_id = t.id
            LEFT JOIN site s ON t.id = s.territory_id AND s.status_operasi = 'active'
            GROUP BY d.id, d.nama_desa, d.populasi, d.luas_wilayah, t.territory_name
            ORDER BY population_per_site DESC NULLS LAST
            """,
        ]

    @classmethod
    def get_monthly_views(cls) -> list[str]:
        """Get views for monthly database analytics."""
        return [
            """
            CREATE VIEW IF NOT EXISTS v_daily_performance_summary AS
            SELECT
                ds.summary_date,
                ds.territory_id,
                ds.transaction_count,
                ds.total_transaction_amount,
                ds.total_commission_amount,
                ds.total_sellin_amount,
                ds.sellin_transaction_count,
                ds.active_retailers,
                ds.retailers_with_coordinates,
                CASE
                    WHEN ds.active_retailers > 0
                    THEN ROUND(ds.transaction_count / CAST(ds.active_retailers AS REAL), 2)
                    ELSE 0
                END as avg_transactions_per_retailer,
                CASE
                    WHEN ds.transaction_count > 0
                    THEN ROUND(ds.total_transaction_amount / ds.transaction_count, 0)
                    ELSE 0
                END as avg_transaction_amount
            FROM daily_summary ds
            ORDER BY ds.summary_date DESC, ds.territory_id
            """,
            """
            CREATE VIEW IF NOT EXISTS v_retailer_latest_data AS
            SELECT
                territory_id,
                retailer_code,
                retailer_name,
                koordinat_lat,
                koordinat_lng,
                chip_type,
                data_date,
                CASE
                    WHEN koordinat_lat IS NOT NULL AND koordinat_lng IS NOT NULL THEN 1
                    ELSE 0
                END as has_coordinates,
                ROW_NUMBER() OVER (PARTITION BY retailer_code ORDER BY data_date DESC) as rn
            FROM ioh_retailer_data
            """,
            """
            CREATE VIEW IF NOT EXISTS v_csv_import_summary AS
            SELECT
                territory_id,
                file_type,
                COUNT(*) as total_imports,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_imports,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_imports,
                MAX(import_date) as last_import_date,
                SUM(COALESCE(total_records, 0)) as total_records_processed,
                SUM(COALESCE(error_records, 0)) as total_error_records
            FROM csv_import_log
            GROUP BY territory_id, file_type
            ORDER BY territory_id, file_type
            """,
            """
            CREATE VIEW IF NOT EXISTS v_sellin_distribution_summary AS
            SELECT
                territory_id,
                data_date,
                COUNT(*) as total_distributions,
                COUNT(DISTINCT organization_id) as source_organizations,
                COUNT(DISTINCT dest_organization_id) as destination_organizations,
                COUNT(DISTINCT product_code) as unique_products,
                SUM(quantity) as total_quantity,
                SUM(final_value) as total_distribution_value,
                AVG(final_value) as avg_distribution_value
            FROM ioh_sellin_data
            GROUP BY territory_id, data_date
            ORDER BY data_date DESC, territory_id
            """,
        ]

    @classmethod
    def validate_schema(cls) -> SchemaValidationResult:
        """Validate schema definitions and return diagnostic info."""
        validation_results: SchemaValidationResult = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {},
        }

        # FUTURE: Add comprehensive schema validation logic
        # FUTURE: Validate foreign key relationships
        # FUTURE: Check for naming convention compliance

        try:
            # Count components
            master_tables = cls.get_master_database_tables()
            monthly_tables = cls.get_monthly_database_tables()
            master_indexes = cls.get_master_indexes()
            monthly_indexes = cls.get_monthly_indexes()
            master_views = cls.get_master_views()
            monthly_views = cls.get_monthly_views()

            validation_results["statistics"] = {
                "master_table_count": len(master_tables),
                "monthly_table_count": len(monthly_tables),
                "total_table_count": len(master_tables) + len(monthly_tables),
                "master_index_count": len(master_indexes),
                "monthly_index_count": len(monthly_indexes),
                "master_view_count": len(master_views),
                "monthly_view_count": len(monthly_views),
            }

            # Basic validation
            if len(master_tables) == 0:
                validation_results["errors"].append("No master tables defined")
                validation_results["valid"] = False

            if len(monthly_tables) == 0:
                validation_results["errors"].append("No monthly tables defined")
                validation_results["valid"] = False

            # Check for required tables
            required_master_tables = ["user", "profile", "territory"]
            for table_sql in master_tables:
                for required_table in required_master_tables:
                    if f"CREATE TABLE IF NOT EXISTS {required_table}" in table_sql:
                        required_master_tables.remove(required_table)
                        break

            if required_master_tables:
                validation_results["warnings"].append(
                    f"Missing required master tables: {', '.join(required_master_tables)}"
                )

            # Check for IOH data tables completeness
            expected_ioh_tables = [
                "ioh_transaction_data",
                "ioh_commission_data",
                "ioh_transfer_data",
                "ioh_sellin_data",
                "ioh_retailer_data",
            ]
            found_ioh_tables = []
            for table_sql in monthly_tables:
                for expected_table in expected_ioh_tables:
                    if f"CREATE TABLE IF NOT EXISTS {expected_table}" in table_sql:
                        found_ioh_tables.append(expected_table)

            missing_ioh_tables = set(expected_ioh_tables) - set(found_ioh_tables)
            if missing_ioh_tables:
                validation_results["warnings"].append(
                    f"Missing IOH data tables: {', '.join(missing_ioh_tables)}"
                )

        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Schema validation error: {str(e)}")

        return validation_results
