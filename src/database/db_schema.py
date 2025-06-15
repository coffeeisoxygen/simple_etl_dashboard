"""Final database schema for ETL Dashboard - Business Reality Aligned."""

from typing import Any, TypedDict


class SchemaValidationResult(TypedDict):
    """Type definition for schema validation results."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    statistics: dict[str, int]


class DatabaseSchema:
    """Database schema aligned with actual business flow and ETL requirements."""

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

                -- Constraints
                CHECK (length(username) >= 3),
                CHECK (length(password_hash) > 0),
                CHECK (is_active IN (0, 1)),
                CHECK (is_admin IN (0, 1))
            )
        """

    @staticmethod
    def get_profile_table() -> str:
        """Business profile table - one per user."""
        return """
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                org_id TEXT NOT NULL UNIQUE,
                org_name TEXT NOT NULL,
                bussines_type TEXT NOT NULL,
                bussines_name TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                pic_name TEXT NOT NULL,
                pic_phone TEXT NOT NULL,
                circle_name TEXT NOT NULL,
                region_name TEXT NOT NULL,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
                CHECK (length(org_id) > 0),
                CHECK (length(org_name) > 0),
                CHECK (email LIKE '%@%'),
                CHECK (bussines_type IN ('perorangan', 'PT', 'CV', 'UD', 'Koperasi', 'Yayasan')),
                CHECK (length(phone) >= 10),
                CHECK (length(pic_phone) >= 10)
            )
        """

    @staticmethod
    def get_territory_table() -> str:
        """Territory table - managed by business entity."""
        return """
            CREATE TABLE IF NOT EXISTS territory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                territory_type TEXT NOT NULL,
                territory_name TEXT NOT NULL,
                territory_code TEXT UNIQUE,
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (profile_id) REFERENCES profile(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
                CHECK (territory_type IN ('MC', 'PT')),
                CHECK (length(territory_name) > 0),
                CHECK (territory_code IS NULL OR length(territory_code) > 0)
            )
        """

    @staticmethod
    def get_desa_table() -> str:
        """Village table - belongs to one territory."""
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
                koordinat_lat REAL,
                koordinat_lng REAL,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
                CHECK (length(nama_desa) > 0),
                CHECK (populasi >= 0),
                CHECK (luas_wilayah > 0),
                CHECK (koordinat_lat IS NULL OR (koordinat_lat >= -90 AND koordinat_lat <= 90)),
                CHECK (koordinat_lng IS NULL OR (koordinat_lng >= -180 AND koordinat_lng <= 180))
            )
        """

    @staticmethod
    def get_site_table() -> str:
        """Site/Tower table - belongs to one territory."""
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

                -- Foreign key constraints
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
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
    def get_retailer_table() -> str:
        """Retailer table - can be in grey area between territories."""
        return """
            CREATE TABLE IF NOT EXISTS retailer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                retailer_code TEXT NOT NULL UNIQUE,
                retailer_name TEXT NOT NULL,
                retailer_type TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                alamat TEXT NOT NULL,
                desa_id INTEGER,
                territory_id INTEGER NOT NULL,
                koordinat_lat REAL,
                koordinat_lng REAL,
                status_aktif BOOLEAN DEFAULT 1,
                is_grey_area BOOLEAN DEFAULT 0,
                catatan_territory TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (desa_id) REFERENCES desa(id) ON DELETE SET NULL ON UPDATE CASCADE,
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
                CHECK (length(retailer_code) > 0),
                CHECK (length(retailer_name) > 0),
                CHECK (retailer_type IN ('Dealer', 'Sub-dealer', 'Counter', 'Booth', 'Kiosk', 'Warung')),
                CHECK (length(phone) >= 10),
                CHECK (koordinat_lat IS NULL OR (koordinat_lat >= -90 AND koordinat_lat <= 90)),
                CHECK (koordinat_lng IS NULL OR (koordinat_lng >= -180 AND koordinat_lng <= 180)),
                CHECK (status_aktif IN (0, 1)),
                CHECK (is_grey_area IN (0, 1))
            )
        """

    @staticmethod
    def get_sales_team_table() -> str:
        """Sales team table - DSE and other sales personnel."""
        return """
            CREATE TABLE IF NOT EXISTS sales_team (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL UNIQUE,
                employee_name TEXT NOT NULL,
                employee_phone TEXT NOT NULL,
                employee_email TEXT,
                position TEXT NOT NULL,
                territory_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                hire_date DATE NOT NULL,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
                CHECK (length(employee_id) > 0),
                CHECK (length(employee_name) > 0),
                CHECK (position IN ('DSE', 'Sales Supervisor', 'Area Manager', 'Sales Admin')),
                CHECK (length(employee_phone) >= 10),
                CHECK (employee_email IS NULL OR employee_email LIKE '%@%'),
                CHECK (is_active IN (0, 1)),
                CHECK (hire_date <= DATE('now'))
            )
        """

    @staticmethod
    def get_sales_retailer_assignment_table() -> str:
        """Sales-Retailer assignment junction table."""
        return """
            CREATE TABLE IF NOT EXISTS sales_retailer_assignment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sales_team_id INTEGER NOT NULL,
                retailer_id INTEGER NOT NULL,
                assignment_type TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                is_active BOOLEAN DEFAULT 1,
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (sales_team_id) REFERENCES sales_team(id) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (retailer_id) REFERENCES retailer(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
                CHECK (assignment_type IN ('primary', 'secondary', 'backup')),
                CHECK (start_date <= DATE('now')),
                CHECK (end_date IS NULL OR end_date >= start_date),
                CHECK (is_active IN (0, 1)),

                -- Unique constraint for active assignments
                UNIQUE (sales_team_id, retailer_id, is_active, assignment_type)
            )
        """

    @staticmethod
    def get_activity_log_table() -> str:
        """Activity log table for audit trail."""
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

                -- Foreign key constraints
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL ON UPDATE CASCADE,

                -- Business rules
                CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'IMPORT')),
                CHECK (status IN ('success', 'failed', 'unauthorized', 'error')),
                CHECK (length(action) > 0)
            )
        """

    @staticmethod
    def get_target_table() -> str:
        """Simple target tracking table for IOH KPI targets."""
        return """
            CREATE TABLE IF NOT EXISTS target (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                target_name TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_value REAL NOT NULL,
                target_period TEXT NOT NULL,
                estimated_fee REAL,
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
                CHECK (target_type IN ('TRADE_SUPPLY', 'TRADE_DEMAND', 'RGU_GA', 'REVENUE', 'ACQUISITION', 'OTHER')),
                CHECK (target_period LIKE '____-__'), -- YYYY-MM format
                CHECK (target_value > 0),
                CHECK (length(target_name) > 0),

                -- Unique constraint
                UNIQUE (territory_id, target_name, target_type, target_period)
            )
        """

    @staticmethod
    def get_bonus_table() -> str:
        """Simple bonus tracking table for IOH bonus received."""
        return """
            CREATE TABLE IF NOT EXISTS bonus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                bonus_name TEXT NOT NULL,
                bonus_type TEXT NOT NULL,
                bonus_value REAL NOT NULL,
                bonus_period TEXT NOT NULL,
                received_date DATE,
                status TEXT DEFAULT 'EXPECTED',
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
                CHECK (bonus_type IN ('TRADE_SUPPLY', 'TRADE_DEMAND', 'RGU_GA', 'REVENUE', 'ACQUISITION', 'OTHER')),
                CHECK (bonus_period LIKE '____-__'), -- YYYY-MM format
                CHECK (length(bonus_name) > 0),
                CHECK (status IN ('EXPECTED', 'RECEIVED', 'PARTIAL', 'CANCELLED')),

                -- Unique constraint
                UNIQUE (territory_id, bonus_name, bonus_type, bonus_period)
            )
        """

    @staticmethod
    def get_production_batch_table() -> str:
        """Production batch tracking for self-production cost calculation."""
        return """
            CREATE TABLE IF NOT EXISTS production_batch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                batch_code TEXT NOT NULL UNIQUE,
                product_id INTEGER NOT NULL,
                target_quantity INTEGER NOT NULL,
                actual_quantity INTEGER,
                production_date DATE NOT NULL,
                status TEXT DEFAULT 'PLANNED',
                total_cost REAL,
                cost_per_unit REAL,
                production_reason TEXT,
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE RESTRICT ON UPDATE CASCADE,
                FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT ON UPDATE CASCADE,

                -- Business rules
                CHECK (status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
                CHECK (target_quantity > 0),
                CHECK (actual_quantity IS NULL OR actual_quantity >= 0),
                CHECK (total_cost IS NULL OR total_cost >= 0),
                CHECK (cost_per_unit IS NULL OR cost_per_unit >= 0),
                CHECK (production_reason IN ('KPI_TARGET', 'STOCK_SHORTAGE', 'DEMAND_SPIKE', 'OTHER'))
            )
        """

    @staticmethod
    def get_production_material_table() -> str:
        """Materials used in production for cost calculation."""
        return """
            CREATE TABLE IF NOT EXISTS production_material (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                production_batch_id INTEGER NOT NULL,
                material_product_id INTEGER NOT NULL,
                quantity_used INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                total_cost REAL NOT NULL,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (production_batch_id) REFERENCES production_batch(id) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (material_product_id) REFERENCES product(id) ON DELETE RESTRICT ON UPDATE CASCADE,

                -- Business rules
                CHECK (quantity_used > 0),
                CHECK (unit_cost >= 0),
                CHECK (total_cost >= 0),
                CHECK (total_cost = quantity_used * unit_cost),

                -- Unique constraint
                UNIQUE (production_batch_id, material_product_id)
            )
        """

    @staticmethod
    def get_csv_import_log_table() -> str:
        """Log table for CSV import tracking - core ETL functionality."""
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
                user_id INTEGER,
                territory_id INTEGER,

                -- Foreign key constraints
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL ON UPDATE CASCADE,
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE SET NULL ON UPDATE CASCADE,

                -- Business rules
                CHECK (file_type IN ('TRANSACTION', 'KOMISI', 'TRANSFER', 'SELLIN', 'VISIT', 'ALLOC', 'SALES', 'STOCK', 'OTHER')),
                CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'PARTIAL')),
                CHECK (file_size IS NULL OR file_size > 0),
                CHECK (total_records IS NULL OR total_records >= 0),
                CHECK (processed_records IS NULL OR processed_records >= 0),
                CHECK (error_records IS NULL OR error_records >= 0)
            )
        """

    @staticmethod
    def get_ioh_data_table() -> str:
        """Generic table for IOH CSV data - flexible structure."""
        return """
            CREATE TABLE IF NOT EXISTS ioh_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                data_type TEXT NOT NULL,
                data_period TEXT NOT NULL,
                data_source TEXT NOT NULL,
                data_json TEXT NOT NULL,
                import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                csv_import_log_id INTEGER,

                -- Foreign key constraints
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (csv_import_log_id) REFERENCES csv_import_log(id) ON DELETE SET NULL ON UPDATE CASCADE,

                -- Business rules
                CHECK (data_type IN ('TRANSACTION', 'KOMISI', 'TRANSFER', 'SELLIN', 'VISIT', 'ALLOC')),
                CHECK (data_period LIKE '____-__' OR data_period LIKE '____-__-__'), -- YYYY-MM or YYYY-MM-DD
                CHECK (length(data_json) > 0),
                CHECK (json_valid(data_json)),

                -- Index for efficient querying
                UNIQUE (territory_id, data_type, data_period, data_source)
            )
        """

    @staticmethod
    def get_product_category_table() -> str:
        """Product categories table - Saldo Mobo (virtual), Starter Pack, Voucher (physical)."""
        return """
            CREATE TABLE IF NOT EXISTS product_category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_code TEXT NOT NULL UNIQUE,
                category_name TEXT NOT NULL,
                is_virtual BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Business rules
                CHECK (category_code IN ('SALDO_MOBO', 'STARTER_PACK', 'VOUCHER')),
                CHECK (length(category_name) > 0),
                CHECK (is_virtual IN (0, 1)),
                CHECK (is_active IN (0, 1))
            )
        """

    @staticmethod
    def get_product_table() -> str:
        """Master product table - both virtual (saldo mobo) and physical products."""
        return """
            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT NOT NULL UNIQUE,
                product_name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                denomination INTEGER,
                source_type TEXT NOT NULL,
                supplier_name TEXT,
                unit_type TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                description TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (category_id) REFERENCES product_category(id) ON DELETE RESTRICT ON UPDATE CASCADE,

                -- Business rules
                CHECK (length(product_code) > 0),
                CHECK (length(product_name) > 0),
                CHECK (source_type IN ('IOH', 'SELF_PRODUCED')),
                CHECK (unit_type IN ('PCS', 'MB', 'RUPIAH', 'UNIT')),
                CHECK (denomination IS NULL OR denomination > 0),
                CHECK (is_active IN (0, 1))
            )
        """

    @staticmethod
    def get_product_price_table() -> str:
        """Simple pricing: Purchase price (cost) and Standard selling price (baseline)."""
        return """
            CREATE TABLE IF NOT EXISTS product_price (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price_type TEXT NOT NULL,
                price REAL NOT NULL,
                effective_date DATE NOT NULL,
                end_date DATE,
                is_active BOOLEAN DEFAULT 1,
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE ON UPDATE CASCADE,

                -- Business rules
                CHECK (price_type IN ('PURCHASE', 'SELLING')),
                CHECK (price > 0),
                CHECK (effective_date <= DATE('now')),
                CHECK (end_date IS NULL OR end_date >= effective_date),
                CHECK (is_active IN (0, 1)),

                -- Unique constraint for active prices
                UNIQUE (product_id, price_type, is_active)
            )
        """

    @staticmethod
    def get_sales_transaction_table() -> str:
        """Sales transaction header - records sales to retailers."""
        return """
            CREATE TABLE IF NOT EXISTS sales_transaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_code TEXT NOT NULL UNIQUE,
                retailer_id INTEGER NOT NULL,
                sales_team_id INTEGER,
                territory_id INTEGER NOT NULL,
                transaction_date DATE NOT NULL,
                transaction_type TEXT NOT NULL,
                total_amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                payment_status TEXT DEFAULT 'PENDING',
                due_date DATE,
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (retailer_id) REFERENCES retailer(id) ON DELETE RESTRICT ON UPDATE CASCADE,
                FOREIGN KEY (sales_team_id) REFERENCES sales_team(id) ON DELETE SET NULL ON UPDATE CASCADE,
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE RESTRICT ON UPDATE CASCADE,

                -- Business rules
                CHECK (length(transaction_code) > 0),
                CHECK (transaction_type IN ('SALES', 'RETURN', 'ADJUSTMENT')),
                CHECK (total_amount > 0),
                CHECK (payment_method IN ('CASH', 'TRANSFER', 'CREDIT', 'DEBIT')),
                CHECK (payment_status IN ('PENDING', 'PAID', 'OVERDUE', 'CANCELLED')),
                CHECK (due_date IS NULL OR due_date >= transaction_date)
            )
        """

    @staticmethod
    def get_sales_transaction_detail_table() -> str:
        """Sales transaction detail with natural discount tracking at transaction level."""
        return """
            CREATE TABLE IF NOT EXISTS sales_transaction_detail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                standard_price REAL NOT NULL,
                actual_price REAL NOT NULL,
                discount_amount REAL DEFAULT 0,
                discount_reason TEXT,
                line_total REAL NOT NULL,
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (transaction_id) REFERENCES sales_transaction(id) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT ON UPDATE CASCADE,

                -- Business rules
                CHECK (quantity > 0),
                CHECK (standard_price > 0),
                CHECK (actual_price > 0),
                CHECK (actual_price <= standard_price),
                CHECK (discount_amount >= 0),
                CHECK (discount_amount = (standard_price - actual_price) * quantity),
                CHECK (line_total = actual_price * quantity),
                CHECK (discount_reason IS NULL OR discount_reason IN ('VOLUME', 'LOYALTY', 'PROMO', 'NEGOTIATION', 'OTHER')),

                -- Unique constraint
                UNIQUE (transaction_id, product_id)
            )
        """

    @staticmethod
    def get_stock_movement_table() -> str:
        """Stock movement log with unit cost tracking for margin analysis."""
        return """
            CREATE TABLE IF NOT EXISTS stock_movement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                reference_type TEXT,
                reference_id INTEGER,
                quantity_before INTEGER NOT NULL,
                quantity_movement INTEGER NOT NULL,
                quantity_after INTEGER NOT NULL,
                unit_cost REAL,
                movement_date DATE NOT NULL,
                catatan TEXT,
                tgl_data DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Foreign key constraints
                FOREIGN KEY (territory_id) REFERENCES territory(id) ON DELETE RESTRICT ON UPDATE CASCADE,
                FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT ON UPDATE CASCADE,

                -- Business rules
                CHECK (movement_type IN ('IN', 'OUT', 'ADJUSTMENT')),
                CHECK (reference_type IS NULL OR reference_type IN ('PURCHASE', 'SALES', 'PRODUCTION', 'ADJUSTMENT', 'TRANSFER')),
                CHECK (quantity_before >= 0),
                CHECK (quantity_after >= 0),
                CHECK (quantity_after = quantity_before + quantity_movement),
                CHECK (unit_cost IS NULL OR unit_cost >= 0),
                CHECK (movement_date <= DATE('now'))
            )        """

    @staticmethod
    def get_indexes() -> list[str]:
        """Get all performance indexes."""
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
            "CREATE INDEX IF NOT EXISTS idx_desa_koordinat ON desa(koordinat_lat, koordinat_lng)",
            # Site table indexes
            "CREATE INDEX IF NOT EXISTS idx_site_territory_id ON site(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_site_code ON site(site_code)",
            "CREATE INDEX IF NOT EXISTS idx_site_type ON site(site_type)",
            "CREATE INDEX IF NOT EXISTS idx_site_koordinat ON site(koordinat_lat, koordinat_lng)",
            "CREATE INDEX IF NOT EXISTS idx_site_status ON site(status_operasi)",
            # Retailer table indexes
            "CREATE INDEX IF NOT EXISTS idx_retailer_code ON retailer(retailer_code)",
            "CREATE INDEX IF NOT EXISTS idx_retailer_territory_id ON retailer(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_retailer_desa_id ON retailer(desa_id)",
            "CREATE INDEX IF NOT EXISTS idx_retailer_type ON retailer(retailer_type)",
            "CREATE INDEX IF NOT EXISTS idx_retailer_status ON retailer(status_aktif)",
            "CREATE INDEX IF NOT EXISTS idx_retailer_grey_area ON retailer(is_grey_area)",
            "CREATE INDEX IF NOT EXISTS idx_retailer_koordinat ON retailer(koordinat_lat, koordinat_lng)",
            # Sales team table indexes
            "CREATE INDEX IF NOT EXISTS idx_sales_team_employee_id ON sales_team(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_team_territory_id ON sales_team(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_team_position ON sales_team(position)",
            "CREATE INDEX IF NOT EXISTS idx_sales_team_active ON sales_team(is_active)",
            # Sales assignment table indexes
            "CREATE INDEX IF NOT EXISTS idx_assignment_sales_team_id ON sales_retailer_assignment(sales_team_id)",
            "CREATE INDEX IF NOT EXISTS idx_assignment_retailer_id ON sales_retailer_assignment(retailer_id)",
            "CREATE INDEX IF NOT EXISTS idx_assignment_active ON sales_retailer_assignment(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_assignment_type ON sales_retailer_assignment(assignment_type)",
            "CREATE INDEX IF NOT EXISTS idx_assignment_dates ON sales_retailer_assignment(start_date, end_date)",
            # Activity log table indexes
            "CREATE INDEX IF NOT EXISTS idx_activity_user_id ON activity_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action)",
            "CREATE INDEX IF NOT EXISTS idx_activity_table_record ON activity_log(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_activity_status ON activity_log(status)",
            "CREATE INDEX IF NOT EXISTS idx_activity_user_timestamp ON activity_log(user_id, timestamp)",
            # Product category table indexes
            "CREATE INDEX IF NOT EXISTS idx_product_category_code ON product_category(category_code)",
            "CREATE INDEX IF NOT EXISTS idx_product_category_virtual ON product_category(is_virtual)",
            "CREATE INDEX IF NOT EXISTS idx_product_category_active ON product_category(is_active)",
            # Product table indexes
            "CREATE INDEX IF NOT EXISTS idx_product_code ON product(product_code)",
            "CREATE INDEX IF NOT EXISTS idx_product_category_id ON product(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_product_source_type ON product(source_type)",
            "CREATE INDEX IF NOT EXISTS idx_product_denomination ON product(denomination)",
            "CREATE INDEX IF NOT EXISTS idx_product_active ON product(is_active)",
            # Product price table indexes
            "CREATE INDEX IF NOT EXISTS idx_product_price_product_id ON product_price(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_product_price_type ON product_price(price_type)",
            "CREATE INDEX IF NOT EXISTS idx_product_price_effective_date ON product_price(effective_date)",
            "CREATE INDEX IF NOT EXISTS idx_product_price_active ON product_price(is_active)",
            # Sales transaction table indexes
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_code ON sales_transaction(transaction_code)",
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_retailer_id ON sales_transaction(retailer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_sales_team_id ON sales_transaction(sales_team_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_territory_id ON sales_transaction(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_date ON sales_transaction(transaction_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_type ON sales_transaction(transaction_type)",
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_payment_status ON sales_transaction(payment_status)",
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_retailer_date ON sales_transaction(retailer_id, transaction_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_sales_team_date ON sales_transaction(sales_team_id, transaction_date)",
            # Sales transaction detail table indexes
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_detail_transaction_id ON sales_transaction_detail(transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_transaction_detail_product_id ON sales_transaction_detail(product_id)",
            # Stock movement table indexes
            "CREATE INDEX IF NOT EXISTS idx_stock_movement_territory_id ON stock_movement(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movement_product_id ON stock_movement(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movement_type ON stock_movement(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movement_reference_type ON stock_movement(reference_type)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movement_date ON stock_movement(movement_date)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movement_territory_product_date ON stock_movement(territory_id, product_id, movement_date)",
            # Target table indexes
            "CREATE INDEX IF NOT EXISTS idx_target_territory_id ON target(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_target_type_period ON target(target_type, target_period)",
            # Bonus table indexes
            "CREATE INDEX IF NOT EXISTS idx_bonus_territory_id ON bonus(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_bonus_type_period ON bonus(bonus_type, bonus_period)",
            "CREATE INDEX IF NOT EXISTS idx_bonus_status ON bonus(status)",
            # Production batch indexes
            "CREATE INDEX IF NOT EXISTS idx_production_batch_territory_id ON production_batch(territory_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_batch_product_id ON production_batch(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_batch_date ON production_batch(production_date)",
            "CREATE INDEX IF NOT EXISTS idx_production_batch_status ON production_batch(status)",
            # Production material indexes
            "CREATE INDEX IF NOT EXISTS idx_production_material_batch_id ON production_material(production_batch_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_material_product_id ON production_material(material_product_id)",
            # CSV import log indexes
            "CREATE INDEX IF NOT EXISTS idx_csv_import_file_type ON csv_import_log(file_type)",
            "CREATE INDEX IF NOT EXISTS idx_csv_import_status ON csv_import_log(status)",
            "CREATE INDEX IF NOT EXISTS idx_csv_import_date ON csv_import_log(import_date)",
            "CREATE INDEX IF NOT EXISTS idx_csv_import_territory_id ON csv_import_log(territory_id)",
            # IOH data indexes
            "CREATE INDEX IF NOT EXISTS idx_ioh_data_territory_type ON ioh_data(territory_id, data_type)",
            "CREATE INDEX IF NOT EXISTS idx_ioh_data_period ON ioh_data(data_period)",
            "CREATE INDEX IF NOT EXISTS idx_ioh_data_import_date ON ioh_data(import_date)",
        ]

    @staticmethod
    def get_triggers() -> list[str]:
        """Get database triggers for business logic and audit."""
        return [
            # Auto-update timestamp triggers
            """
            CREATE TRIGGER IF NOT EXISTS trg_profile_updated_at
            AFTER UPDATE ON profile
            FOR EACH ROW
            BEGIN
                UPDATE profile SET tgl_data = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_territory_updated_at
            AFTER UPDATE ON territory
            FOR EACH ROW
            BEGIN
                UPDATE territory SET tgl_data = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS trg_retailer_updated_at
            AFTER UPDATE ON retailer
            FOR EACH ROW
            BEGIN
                UPDATE retailer SET tgl_data = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            # Auto-populate territory_code if not provided
            """
            CREATE TRIGGER IF NOT EXISTS trg_territory_auto_code
            AFTER INSERT ON territory
            FOR EACH ROW
            WHEN NEW.territory_code IS NULL
            BEGIN
                UPDATE territory
                SET territory_code = NEW.territory_type || '-' || NEW.id
                WHERE id = NEW.id;
            END
            """,
            # Validate grey area logic
            """
            CREATE TRIGGER IF NOT EXISTS trg_retailer_grey_area_validation
            BEFORE INSERT ON retailer
            FOR EACH ROW
            WHEN NEW.desa_id IS NOT NULL AND NEW.is_grey_area = 0
            BEGIN
                SELECT CASE
                    WHEN (SELECT territory_id FROM desa WHERE id = NEW.desa_id) != NEW.territory_id
                    THEN RAISE(ABORT, 'Retailer territory mismatch with desa territory - set is_grey_area = 1')
                END;
            END
            """,
            # Prevent overlapping active sales assignments
            """
            CREATE TRIGGER IF NOT EXISTS trg_prevent_duplicate_assignment
            BEFORE INSERT ON sales_retailer_assignment
            FOR EACH ROW
            WHEN NEW.is_active = 1 AND NEW.assignment_type = 'primary'
            BEGIN
                SELECT CASE
                    WHEN EXISTS (
                        SELECT 1 FROM sales_retailer_assignment
                        WHERE retailer_id = NEW.retailer_id
                        AND assignment_type = 'primary'
                        AND is_active = 1
                        AND (end_date IS NULL OR end_date > NEW.start_date)
                    )
                    THEN RAISE(ABORT, 'Retailer already has active primary assignment')
                END;
            END
            """,
        ]

    @staticmethod
    def get_views() -> list[str]:
        """Get useful database views for common queries."""
        return [
            # Territory summary view
            """
            CREATE VIEW IF NOT EXISTS v_territory_summary AS
            SELECT
                t.id as territory_id,
                t.territory_name,
                t.territory_type,
                p.org_name,
                p.circle_name,
                p.region_name,
                COUNT(DISTINCT d.id) as jumlah_desa,
                COUNT(DISTINCT s.id) as jumlah_site,
                COUNT(DISTINCT r.id) as jumlah_retailer,
                COUNT(DISTINCT st.id) as jumlah_staff,
                SUM(d.populasi) as total_populasi
            FROM territory t
            LEFT JOIN profile p ON t.profile_id = p.id
            LEFT JOIN desa d ON t.id = d.territory_id
            LEFT JOIN site s ON t.id = s.territory_id
            LEFT JOIN retailer r ON t.id = r.territory_id AND r.status_aktif = 1
            LEFT JOIN sales_team st ON t.id = st.territory_id AND st.is_active = 1
            GROUP BY t.id, t.territory_name, t.territory_type, p.org_name, p.circle_name, p.region_name
            """,
            # Active sales assignments view
            """
            CREATE VIEW IF NOT EXISTS v_active_sales_assignments AS
            SELECT
                sa.id,
                st.employee_name,
                st.position,
                r.retailer_name,
                r.retailer_type,
                t.territory_name,
                sa.assignment_type,
                sa.start_date,
                sa.catatan
            FROM sales_retailer_assignment sa
            JOIN sales_team st ON sa.sales_team_id = st.id
            JOIN retailer r ON sa.retailer_id = r.id
            JOIN territory t ON r.territory_id = t.id
            WHERE sa.is_active = 1
            AND st.is_active = 1
            AND r.status_aktif = 1
            AND (sa.end_date IS NULL OR sa.end_date > DATE('now'))
            """,
            # Grey area retailers view
            """
            CREATE VIEW IF NOT EXISTS v_grey_area_retailers AS
            SELECT
                r.retailer_code,
                r.retailer_name,
                r.retailer_type,
                d.nama_desa as admin_desa,
                d.kecamatan as admin_kecamatan,
                t1.territory_name as admin_territory,
                t2.territory_name as business_territory,
                r.catatan_territory
            FROM retailer r
            LEFT JOIN desa d ON r.desa_id = d.id
            LEFT JOIN territory t1 ON d.territory_id = t1.id
            JOIN territory t2 ON r.territory_id = t2.id
            WHERE r.is_grey_area = 1
            """,  # Territory performance summary
            """
            CREATE VIEW IF NOT EXISTS v_territory_performance AS
            SELECT
                t.id as territory_id,
                t.territory_name,
                p.org_name,
                COUNT(DISTINCT st.id) as total_sales_transactions,
                SUM(st.total_amount) as total_sales_amount,
                COUNT(DISTINCT pb.id) as total_production_batches,
                SUM(pb.total_cost) as total_production_cost,
                COUNT(DISTINCT tg.id) as total_targets,
                COUNT(DISTINCT b.id) as total_bonuses,
                SUM(CASE WHEN b.status = 'RECEIVED' THEN b.bonus_value ELSE 0 END) as total_bonus_received
            FROM territory t
            LEFT JOIN profile p ON t.profile_id = p.id
            LEFT JOIN sales_transaction st ON t.id = st.territory_id
            LEFT JOIN production_batch pb ON t.id = pb.territory_id
            LEFT JOIN target tg ON t.id = tg.territory_id
            LEFT JOIN bonus b ON t.id = b.territory_id
            GROUP BY t.id, t.territory_name, p.org_name
            """,
            # Monthly margin analysis
            """
            CREATE VIEW IF NOT EXISTS v_monthly_margin AS
            SELECT
                t.id as territory_id,
                t.territory_name,
                strftime('%Y-%m', st.transaction_date) as month,
                SUM(std.line_total) as sales_revenue,
                SUM(std.quantity * std.standard_price - std.line_total) as sales_discount,
                SUM(pb.total_cost) as production_cost,
                SUM(CASE WHEN b.status = 'RECEIVED' THEN b.bonus_value ELSE 0 END) as bonus_received,
                (SUM(std.line_total) + SUM(CASE WHEN b.status = 'RECEIVED' THEN b.bonus_value ELSE 0 END) - SUM(pb.total_cost)) as net_margin
            FROM territory t
            LEFT JOIN sales_transaction st ON t.id = st.territory_id
            LEFT JOIN sales_transaction_detail std ON st.id = std.transaction_id
            LEFT JOIN production_batch pb ON t.id = pb.territory_id AND strftime('%Y-%m', pb.production_date) = strftime('%Y-%m', st.transaction_date)
            LEFT JOIN bonus b ON t.id = b.territory_id AND b.bonus_period = strftime('%Y-%m', st.transaction_date)
            GROUP BY t.id, t.territory_name, strftime('%Y-%m', st.transaction_date)
            """,
            # CSV import status
            """
            CREATE VIEW IF NOT EXISTS v_csv_import_status AS
            SELECT
                t.territory_name,
                cil.file_type,
                COUNT(*) as total_imports,
                SUM(CASE WHEN cil.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_imports,
                SUM(CASE WHEN cil.status = 'FAILED' THEN 1 ELSE 0 END) as failed_imports,
                MAX(cil.import_date) as last_import_date,
                SUM(cil.total_records) as total_records_processed
            FROM csv_import_log cil
            LEFT JOIN territory t ON cil.territory_id = t.id
            GROUP BY t.territory_name, cil.file_type
            """,
        ]

    @classmethod
    def get_all_table_statements(cls) -> list[str]:
        """Get all table creation statements in dependency order."""
        return [
            cls.get_user_table(),
            cls.get_profile_table(),
            cls.get_territory_table(),
            cls.get_desa_table(),
            cls.get_site_table(),
            cls.get_retailer_table(),
            cls.get_sales_team_table(),
            cls.get_sales_retailer_assignment_table(),
            cls.get_activity_log_table(),
            cls.get_product_category_table(),
            cls.get_product_table(),
            cls.get_product_price_table(),
            cls.get_sales_transaction_table(),
            cls.get_sales_transaction_detail_table(),
            cls.get_stock_movement_table(),
            cls.get_target_table(),
            cls.get_bonus_table(),
            cls.get_production_batch_table(),
            cls.get_production_material_table(),
            cls.get_csv_import_log_table(),
        ]

    @classmethod
    def get_create_statements(cls) -> list[str]:
        """Get all creation statements including tables, indexes, triggers, and views."""
        statements = []
        statements.extend(cls.get_all_table_statements())
        statements.extend(cls.get_indexes())
        statements.extend(cls.get_triggers())
        statements.extend(cls.get_views())
        return statements

    @classmethod
    def get_migration_statements(cls) -> list[str]:
        """Get migration statements to drop old tables."""
        return [
            "DROP TABLE IF EXISTS processing_logs",
            "DROP TABLE IF EXISTS file_sources",
            "DROP TABLE IF EXISTS territory_stats",
            "DROP TABLE IF EXISTS dse_info",
            "DROP TABLE IF EXISTS mim3_profile",
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

        try:
            # Count components
            tables = cls.get_all_table_statements()
            indexes = cls.get_indexes()
            triggers = cls.get_triggers()
            views = cls.get_views()

            validation_results["statistics"] = {
                "table_count": len(tables),
                "index_count": len(indexes),
                "trigger_count": len(triggers),
                "view_count": len(views),
                "total_statements": len(cls.get_create_statements()),
            }

            # Basic validation
            if len(tables) == 0:
                validation_results["errors"].append("No tables defined")
                validation_results["valid"] = False

            if len(indexes) < len(tables):
                validation_results["warnings"].append(
                    "Some tables may lack proper indexing"
                )

        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Schema validation error: {str(e)}")

        return validation_results

    @classmethod
    def get_sample_data(cls) -> dict[str, list[dict[str, Any]]]:
        """Get sample data for testing and development."""
        return {
            "user": [
                {
                    "username": "admin",
                    "password_hash": "hashed_password_here",
                    "is_active": 1,
                    "is_admin": 1,
                }
            ],
            "profile": [
                {
                    "user_id": 1,
                    "org_id": "SDP1336",
                    "org_name": "SDP Haurwangi",
                    "bussines_type": "PT",
                    "bussines_name": "PT. Dewi Pratama Putri Internusa",
                    "address": "Jl. Raya Haurwangi No. 123",
                    "phone": "02125889900",
                    "email": "info@sdphaurwangi.com",
                    "pic_name": "Budi Santoso",
                    "pic_phone": "08123456789",
                    "circle_name": "Circle Jaya",
                    "region_name": "Outer Jaya",
                }
            ],
        }
