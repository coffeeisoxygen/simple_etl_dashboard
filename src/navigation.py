"""Navigation management untuk ETL Dashboard dengan audit logging integration."""

import uuid
from dataclasses import dataclass
from enum import Enum

import streamlit as st
from loguru import logger

from src.config.logging.logging_config import log_activity  # Updated import


class PageCategory(Enum):
    """Kategori halaman untuk ETL Dashboard."""

    DASHBOARD = "dashboard"
    DATA = "data"
    TOOLS = "tools"


@dataclass
class PageConfig:
    """Page configuration untuk dynamic page management."""

    file_path: str
    title: str
    icon: str
    category: PageCategory
    description: str = ""
    default: bool = False


class SessionContextManager:
    """Manage session context untuk audit logging."""

    @staticmethod
    def ensure_user_context() -> None:
        """Ensure user context exists in session state."""
        if "user_id" not in st.session_state:
            st.session_state.user_id = "demo_user"

    @staticmethod
    def ensure_session_id() -> None:
        """Ensure session ID exists in session state."""
        if "session_id" not in st.session_state:
            # Generate unique session ID
            st.session_state.session_id = str(uuid.uuid4())

    @classmethod
    def setup_audit_context(cls) -> None:
        """Setup complete audit context."""
        cls.ensure_user_context()
        cls.ensure_session_id()


class PageRegistrar:
    """Handle page registration untuk navigation system."""

    @staticmethod
    def get_page_configs() -> dict[str, PageConfig]:
        """Get all page configurations."""
        return {
            # Dashboard Pages
            "dashboard": PageConfig(
                file_path="pages/reports/dashboard.py",
                title="Dashboard",
                icon=":material/dashboard:",
                category=PageCategory.DASHBOARD,
                description="Main overview dashboard",
                default=True,
            ),
            # Data Pages
            "transaksi": PageConfig(
                file_path="pages/data/transaksi.py",
                title="Transaksi",
                icon=":material/receipt:",
                category=PageCategory.DATA,
                description="Transaction data management",
            ),
            "komisi": PageConfig(
                file_path="pages/data/komisi.py",
                title="Komisi",
                icon=":material/payments:",
                category=PageCategory.DATA,
                description="Commission data tracking",
            ),
            "transfer": PageConfig(
                file_path="pages/data/transfer.py",
                title="Transfer",
                icon=":material/swap_horiz:",
                category=PageCategory.DATA,
                description="Transfer operations",
            ),
            "alokasi": PageConfig(
                file_path="pages/data/alokasi.py",
                title="Alokasi",
                icon=":material/pie_chart:",
                category=PageCategory.DATA,
                description="Resource allocation",
            ),
            # Tools Pages
            "debugging": PageConfig(
                file_path="pages/tools/debug_tools.py",
                title="Debugging",
                icon=":material/heap_snapshot_large:",
                category=PageCategory.TOOLS,
                description="System context information",
            ),
            "activity_log": PageConfig(
                file_path="pages/tools/activity_log.py",
                title="Activity Log",
                icon=":material/history:",
                category=PageCategory.TOOLS,
                description="User activity and audit trail",
            ),
        }


class NavigationStructureBuilder:
    """Build navigation structure untuk Streamlit."""

    def __init__(self, pages: dict[str, PageConfig]):
        self.pages = pages

    def get_pages_by_category(self, category: PageCategory) -> dict[str, PageConfig]:
        """Get pages filtered by category."""
        return {
            key: config
            for key, config in self.pages.items()
            if config.category == category
        }

    def build_streamlit_pages(self, category: PageCategory) -> list:
        """Build Streamlit pages for a category."""
        pages = self.get_pages_by_category(category)
        st_pages = []

        for config in pages.values():
            try:
                page = st.Page(
                    page=config.file_path,
                    title=config.title,
                    icon=config.icon,
                    default=config.default,
                )
                st_pages.append(page)
            except Exception as e:
                self._log_page_error(config, e)

        return st_pages

    def _log_page_error(self, config: PageConfig, error: Exception) -> None:
        """Log page loading error dengan audit."""
        logger.error(f"Error loading page {config.title}: {error}")

        # FIXED: Changed log_action to log_activity
        log_activity(
            "PAGE_LOAD_ERROR",
            f"Failed to load page: {config.title}",
            error=str(error),
            file_path=config.file_path,
            page_title=config.title,
        )

    def build_navigation_structure(self) -> dict[str, list]:
        """Build complete navigation structure."""
        navigation = {}

        for category in PageCategory:
            st_pages = self.build_streamlit_pages(category)

            if st_pages:
                category_name = self._get_display_name(category)
                navigation[category_name] = st_pages

        return navigation

    @staticmethod
    def _get_display_name(category: PageCategory) -> str:
        """Get display name untuk category."""
        return "Data" if category == PageCategory.DATA else category.value.title()


class NavigationManager:
    """Centralized navigation management untuk ETL Dashboard."""

    def __init__(self) -> None:
        self._setup_navigation()
        self.pages = PageRegistrar.get_page_configs()
        self._setup_audit_context()
        self.structure_builder = NavigationStructureBuilder(self.pages)

    def _setup_navigation(self) -> None:
        """Setup navigation - guard pattern."""
        if "navigation_manager_initialized" in st.session_state:
            return

        logger.info("Launching navigation system")
        logger.info("Initializing NavigationManager")
        st.session_state.navigation_manager_initialized = True

    def _setup_audit_context(self) -> None:
        """Setup audit logging context for navigation."""
        SessionContextManager.setup_audit_context()

        # Activity logging - updated
        log_activity(
            "NAV_INIT",
            "Navigation system initialized",
            pages_registered=len(self.pages),
        )

    def run(self) -> None:
        """Run navigation system dengan audit logging."""
        try:
            nav_structure = self.structure_builder.build_navigation_structure()

            self._log_navigation_start(nav_structure)

            nav = st.navigation(nav_structure)
            nav.run()

        except Exception as e:
            self._handle_navigation_error(e)

    def _log_navigation_start(self, nav_structure: dict) -> None:
        """Log navigation system start."""
        log_activity(
            "NAV_START",
            "Navigation system started",
            categories=len(nav_structure),
            total_pages=sum(len(pages) for pages in nav_structure.values()),
        )

    def _handle_navigation_error(self, error: Exception) -> None:
        """Handle navigation system errors."""
        logger.error(f"Navigation system failed: {error}")

        log_activity(
            "NAV_ERROR",
            f"Navigation system failed: {str(error)}",
            error=str(error),
        )

        st.error(
            "❌ Navigation system encountered an error. Check debug tools for details."
        )
        raise


def run_navigation() -> None:
    """Run navigation system."""
    if "nav_manager" not in st.session_state:
        st.session_state.nav_manager = NavigationManager()

    # Activity logging - updated
    log_activity(
        "NAV_ACCESS",
        "User accessed navigation system",
    )

    st.session_state.nav_manager.run()
