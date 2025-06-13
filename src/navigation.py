import streamlit as st


def run_navigation() -> None:
    """Main navigation system for the application."""
    # Initialize session state for login
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    def login() -> None:
        """Handle user login."""
        if st.button("Log in"):
            st.session_state.logged_in = True
            st.rerun()

    def logout() -> None:
        """Handle user logout."""
        if st.button("Log out"):
            st.session_state.logged_in = False
            st.rerun()

    # Define pages
    login_page = st.Page(login, title="Log in", icon=":material/login:")
    logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

    # Halaman Utama Dashboard
    dashboard = st.Page(
        "pages/reports/dashboard.py",
        title="Dashboard",
        icon=":material/dashboard:",
        default=True,
    )

    # Halaman menampilkan Data Data Dasar Dan Utama
    fundamental = st.Page(
        "pages/core/fundamental.py",
        title="Fundamental",
        icon=":material/business:",
    )

    # Halaman Laporan Yang bersumber dari web mobo
    transaksi = st.Page(
        "pages/mobo/rep_transactions.py",
        title="Transaksi",
        icon=":material/bug_report:",
    )
    komisi = st.Page(
        "pages/mobo/rep_commisions.py",
        title="Komisi",
        icon=":material/attach_money:",
    )
    transfer = st.Page(
        "pages/mobo/rep_transfer.py",
        title="Transfer",
        icon=":material/transfer_within_a_station:",
    )
    alokasi = st.Page(
        "pages/mobo/rep_allocations.py",
        title="Alokasi",
        icon=":material/assignment_returned:",
    )

    # Halaman Laporan Yang Bersumber dari web mobi
    sellin = st.Page(
        "pages/mobi/rep_sellin.py",
        title="Sellin",
        icon=":material/sell:",
    )
    visits = st.Page(
        "pages/mobi/rep_visits.py",
        title="Visits",
        icon=":material/visibility:",
    )

    # Tools pages
    util_upload = st.Page(
        "pages/tools/data_upload.py",
        title="Upload",
        icon=":material/upload_file:",
    )

    context_info = st.Page(
        "pages/tools/context_info.py",
        title="Context Info",
        icon=":material/info:",
    )

    # Setup navigation based on login status
    if st.session_state.logged_in:
        pg = st.navigation({
            "Dashboard": [dashboard],
            "Profile": [fundamental],
            "Mobo": [transaksi, komisi, transfer, alokasi],
            "Mobi": [sellin, visits],
            "Tools": [util_upload, context_info],
            "Account": [logout_page],
        })
    else:
        pg = st.navigation([login_page])

    pg.run()
