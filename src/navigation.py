"""Navigation management untuk ETL Dashboard dengan clean class structure."""

from dataclasses import dataclass
from enum import Enum

import streamlit as st
from loguru import logger


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


class NavigationManager:
    """Centralized navigation management untuk ETL Dashboard."""

    def __init__(self) -> None:
        self._setup_navigation()
        self.pages = self._register_pages()

    def _setup_navigation(self) -> None:
        """Setup navigation - guard pattern."""
        if "navigation_manager_initialized" in st.session_state:
            return

        logger.info("Launching navigation system")  # Move here
        logger.info("Initializing NavigationManager")
        st.session_state.navigation_manager_initialized = True

    def _register_pages(self) -> dict[str, PageConfig]:
        """Register all pages dengan configurations."""
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
            # Data Pages (Mobo section)
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
            "context_info": PageConfig(
                file_path="pages/tools/context_info.py",
                title="Context Info",
                icon=":material/info:",
                category=PageCategory.TOOLS,
                description="System context information",
            ),
        }

    def get_pages_by_category(self, category: PageCategory) -> dict[str, PageConfig]:
        """Get pages filtered by category."""
        return {
            key: config
            for key, config in self.pages.items()
            if config.category == category
        }

    def get_navigation_structure(self) -> dict[str, list]:
        """Build Streamlit navigation structure."""
        navigation = {}

        for category in PageCategory:
            pages = self.get_pages_by_category(category)

            if pages:
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
                        logger.error(f"Error loading page {config.title}: {e}")

                if st_pages:
                    # Convert category name untuk display
                    category_name = (
                        "Data"
                        if category == PageCategory.DATA
                        else category.value.title()
                    )
                    navigation[category_name] = st_pages

        return navigation

    def get_page_info(self, page_key: str) -> PageConfig | None:
        """Get page configuration by key."""
        return self.pages.get(page_key)

    def run(self) -> None:
        """Run navigation system."""
        nav_structure = self.get_navigation_structure()
        nav = st.navigation(nav_structure)
        nav.run()


def run_navigation() -> None:
    """Run navigation system."""
    if "nav_manager" not in st.session_state:
        st.session_state.nav_manager = NavigationManager()

    st.session_state.nav_manager.run()
