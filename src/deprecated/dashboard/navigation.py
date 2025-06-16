"""Clean Navigation Management integrated with State Management.

Simplified navigation without session conflicts or over-engineering.
Delegates session management to UserStateManager.
"""

from dataclasses import dataclass
from enum import Enum

import streamlit as st
from loguru import logger

from src.core.state_management import get_user_state


class PageCategory(Enum):
    """Page categories for ETL Dashboard navigation."""

    AUTH = "auth"
    DASHBOARD = "dashboard"
    DATA = "data"
    TOOLS = "tools"


@dataclass
class PageConfig:
    """Clean page configuration."""

    file_path: str
    title: str
    icon: str
    category: PageCategory
    description: str = ""
    default: bool = False
    requires_auth: bool = True


class NavigationManager:
    """Clean navigation manager integrated with state management.

    Responsibilities:
    - Page registration and routing
    - Authentication-aware navigation
    - Integration with UserStateManager

    NOT responsible for:
    - Session management (delegated to UserStateManager)
    - Authentication logic (delegated to UserStateManager)
    - Audit logging (delegated to state_management)
    """

    def __init__(self) -> None:
        """Initialize navigation manager."""
        self._pages = self._register_pages()
        self._user_state = get_user_state()

    def _register_pages(self) -> dict[str, PageConfig]:
        """Register all application pages.

        Returns:
            dict: Page configurations by page key
        """
        return {
            # Authentication pages
            "login": PageConfig(
                file_path="pages/auth/login.py",
                title="Login",
                icon=":material/login:",
                category=PageCategory.AUTH,
                description="User authentication",
                default=True,
                requires_auth=False,
            ),
            # Dashboard pages
            "dashboard": PageConfig(
                file_path="pages/reports/dashboard.py",
                title="Dashboard",
                icon=":material/dashboard:",
                category=PageCategory.DASHBOARD,
                description="Main overview dashboard",
            ),
            # Data pages
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
            # Tools pages
            "debugging": PageConfig(
                file_path="pages/tools/debug_tools.py",
                title="Debug Tools",
                icon=":material/bug_report:",
                category=PageCategory.TOOLS,
                description="System debugging information",
            ),
            "activity_log": PageConfig(
                file_path="pages/tools/activity_log.py",
                title="Activity Log",
                icon=":material/history:",
                category=PageCategory.TOOLS,
                description="System activity monitoring",
            ),
        }

    def get_available_pages(self) -> dict[str, PageConfig]:
        """Get pages available to current user based on authentication status.

        Returns:
            dict: Available page configurations
        """
        is_authenticated = self._user_state.is_authenticated()

        available_pages = {}

        for page_key, config in self._pages.items():
            # Include page if:
            # 1. Page doesn't require auth, OR
            # 2. User is authenticated
            if not config.requires_auth or is_authenticated:
                available_pages[page_key] = config

        return available_pages

    def get_default_page(self) -> str:
        """Get default page based on authentication status.

        Returns:
            str: Default page key
        """
        if self._user_state.is_authenticated():
            # Authenticated users go to dashboard
            return "dashboard"
        else:
            # Unauthenticated users go to login
            return "login"

    def build_navigation_structure(self) -> dict[str, list[st.Page]]:
        """Build Streamlit navigation structure.

        Returns:
            dict: Navigation structure for st.navigation()
        """
        available_pages = self.get_available_pages()

        if not available_pages:
            logger.warning("No pages available for navigation")
            return {}

        # Group pages by category
        navigation_structure = {}

        for category in PageCategory:
            category_pages = [
                config
                for config in available_pages.values()
                if config.category == category
            ]

            if not category_pages:
                continue

            # Build Streamlit pages for this category
            st_pages = []
            for config in category_pages:
                try:
                    # Determine if this should be the default page
                    is_default = (
                        config.file_path.split("/")[-1].replace(".py", "")
                        == self.get_default_page()
                    )

                    st_page = st.Page(
                        page=config.file_path,
                        title=config.title,
                        icon=config.icon,
                        default=is_default,
                    )
                    st_pages.append(st_page)

                except Exception as e:
                    logger.error(f"Failed to create page {config.title}: {e}")
                    continue

            if st_pages:
                category_name = self._get_category_display_name(category)
                navigation_structure[category_name] = st_pages

        return navigation_structure

    def _get_category_display_name(self, category: PageCategory) -> str:
        """Get display name for page category.

        Args:
            category: Page category enum

        Returns:
            str: Display name for category
        """
        display_names = {
            PageCategory.AUTH: "Authentication",
            PageCategory.DASHBOARD: "Dashboard",
            PageCategory.DATA: "Data Management",
            PageCategory.TOOLS: "Tools & Utilities",
        }
        return display_names.get(category, category.value.title())

    def run_navigation(self) -> None:
        """Run Streamlit navigation system.

        Handles authentication checks and page routing.
        """
        try:
            # Check if user should be redirected
            current_page = self._user_state.get_current_page()
            should_redirect = self._check_authentication_redirect(current_page)

            if should_redirect:
                # Handle redirect by updating user state
                target_page = self.get_default_page()
                self._user_state.navigate_to(target_page)
                logger.info(f"Redirecting to {target_page} based on auth status")

            # Build navigation structure
            nav_structure = self.build_navigation_structure()

            if not nav_structure:
                self._handle_no_pages_available()
                return

            # Run Streamlit navigation
            nav = st.navigation(nav_structure)
            nav.run()

        except Exception as e:
            logger.error(f"Navigation system error: {e}")
            self._handle_navigation_error(e)

    def _check_authentication_redirect(self, current_page: str) -> bool:
        """Check if user should be redirected based on authentication status.

        Args:
            current_page: Current page name

        Returns:
            bool: True if redirect is needed
        """
        is_authenticated = self._user_state.is_authenticated()
        page_config = self._pages.get(current_page)

        if not page_config:
            # Unknown page, redirect to default
            return True

        # Redirect if:
        # 1. Page requires auth but user is not authenticated
        # 2. User is authenticated but on login page
        return (page_config.requires_auth and not is_authenticated) or (
            is_authenticated and current_page == "login"
        )

    def _handle_no_pages_available(self) -> None:
        """Handle case when no pages are available."""
        st.error("❌ No pages available for navigation")
        st.info("This might be a configuration issue. Please contact support.")

        # Show debug info in development
        if st.button("🔧 Show Debug Info"):
            st.json(
                {
                    "total_pages": len(self._pages),
                    "authenticated": self._user_state.is_authenticated(),
                    "current_page": self._user_state.get_current_page(),
                    "session_id": self._user_state.get_session_id(),
                }
            )

    def _handle_navigation_error(self, error: Exception) -> None:
        """Handle navigation system errors.

        Args:
            error: Exception that occurred
        """
        st.error("❌ Navigation system encountered an error")

        with st.expander("Error Details"):
            st.code(str(error))
            st.json(
                {
                    "error_type": type(error).__name__,
                    "authenticated": self._user_state.is_authenticated(),
                    "current_page": self._user_state.get_current_page(),
                    "available_pages": len(self.get_available_pages()),
                }
            )

        # Recovery option
        if st.button("🔄 Reset Navigation State"):
            self._user_state.navigate_to(self.get_default_page())
            st.rerun()


# Global navigation manager (cached resource)
@st.cache_resource
def get_navigation_manager() -> NavigationManager:
    """Get cached navigation manager instance.

    Returns:
        NavigationManager: Cached navigation manager
    """
    return NavigationManager()


# Public API function
def run_navigation() -> None:
    """Run navigation system integrated with state management.

    This is the main entry point for navigation.
    Call this from main.py after state initialization.
    """
    try:
        nav_manager = get_navigation_manager()
        nav_manager.run_navigation()

    except Exception as e:
        logger.error(f"Navigation system failed: {e}")

        st.error("❌ Navigation system failed to start")
        st.exception(e)

        # Show recovery options
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Retry Navigation"):
                st.rerun()

        with col2:
            if st.button("🏠 Go to Login"):
                user_state = get_user_state()
                user_state.navigate_to("login")
                st.rerun()


# TODO: Add page permission system
# PINNED: Consider adding breadcrumb navigation
# REVIEW: Add page analytics if needed later
# REMINDER: Navigation now cleanly integrated with state management
