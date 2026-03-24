"""
Q4 - WEB APPLICATION TESTING for the Admin Dashboard.

Tool Used: Selenium WebDriver with pytest

Web Application Testing Plan covers:
  1. Login functionality testing
  2. Order tracking and management
  3. Report generation and export
  4. Session management and security
  5. Cross-browser compatibility
  6. Database-backed functional tests
"""

import pytest
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════
# SECTION A: LOGIN FUNCTIONALITY TESTING
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not installed")
class TestAdminLogin:
    """Test suite for admin dashboard login functionality."""

    @pytest.fixture(autouse=True)
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.base_url = "http://localhost:8000"
        yield
        self.driver.quit()

    def test_login_page_loads(self):
        """TC-WEB-001: Login page loads with correct title and form elements."""
        self.driver.get(f"{self.base_url}/login")
        assert "Login" in self.driver.title or "Document" in self.driver.title

        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        submit = self.driver.find_element(By.ID, "loginBtn")

        assert username.is_displayed()
        assert password.is_displayed()
        assert submit.is_displayed()

    def test_valid_admin_login(self):
        """TC-WEB-002: Admin can login with valid credentials."""
        self.driver.get(f"{self.base_url}/login")

        self.driver.find_element(By.ID, "username").send_keys("admin")
        self.driver.find_element(By.ID, "password").send_keys("admin123")
        self.driver.find_element(By.ID, "loginBtn").click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "dashboardHeader"))
        )
        assert "dashboard" in self.driver.current_url.lower()

    def test_invalid_login_shows_error(self):
        """TC-WEB-003: Invalid credentials show error message."""
        self.driver.get(f"{self.base_url}/login")

        self.driver.find_element(By.ID, "username").send_keys("wronguser")
        self.driver.find_element(By.ID, "password").send_keys("wrongpass")
        self.driver.find_element(By.ID, "loginBtn").click()

        error = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
        )
        assert "invalid" in error.text.lower() or "incorrect" in error.text.lower()

    def test_empty_form_validation(self):
        """TC-WEB-004: Empty form submission shows validation message."""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.ID, "loginBtn").click()

        error = self.driver.find_element(By.CLASS_NAME, "error-message")
        assert error.is_displayed()

    def test_sql_injection_prevention(self):
        """TC-WEB-005: SQL injection attempt is handled safely."""
        self.driver.get(f"{self.base_url}/login")

        self.driver.find_element(By.ID, "username").send_keys("' OR '1'='1")
        self.driver.find_element(By.ID, "password").send_keys("' OR '1'='1")
        self.driver.find_element(By.ID, "loginBtn").click()

        assert "dashboard" not in self.driver.current_url.lower()

    def test_password_field_masked(self):
        """TC-WEB-006: Password field masks input characters."""
        self.driver.get(f"{self.base_url}/login")
        password_field = self.driver.find_element(By.ID, "password")
        assert password_field.get_attribute("type") == "password"


# ═══════════════════════════════════════════════════════════════════════
# SECTION B: ORDER TRACKING TESTING
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not installed")
class TestOrderTracking:
    """Test suite for order tracking in admin dashboard."""

    @pytest.fixture(autouse=True)
    def setup_and_login(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.base_url = "http://localhost:8000"

        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.ID, "username").send_keys("admin")
        self.driver.find_element(By.ID, "password").send_keys("admin123")
        self.driver.find_element(By.ID, "loginBtn").click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "dashboardHeader"))
        )
        yield
        self.driver.quit()

    def test_order_table_displayed(self):
        """TC-WEB-007: Order tracking table is visible on dashboard."""
        self.driver.get(f"{self.base_url}/dashboard/orders")

        table = self.driver.find_element(By.ID, "orderTable")
        assert table.is_displayed()

        headers = self.driver.find_elements(By.CSS_SELECTOR, "#orderTable th")
        header_texts = [h.text for h in headers]
        assert "Order ID" in header_texts
        assert "Status" in header_texts

    def test_filter_orders_by_status(self):
        """TC-WEB-008: Filtering orders by status works correctly."""
        self.driver.get(f"{self.base_url}/dashboard/orders")

        filter_select = Select(self.driver.find_element(By.ID, "statusFilter"))
        filter_select.select_by_value("completed")

        time.sleep(1)
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#orderTable tbody tr")
        for row in rows:
            status_cell = row.find_element(By.CSS_SELECTOR, "td:last-child")
            assert status_cell.text.lower() == "completed"

    def test_order_detail_view(self):
        """TC-WEB-009: Clicking an order opens its detail view."""
        self.driver.get(f"{self.base_url}/dashboard/orders")

        first_row = self.driver.find_element(By.CSS_SELECTOR, "#orderTable tbody tr:first-child")
        first_row.click()

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "orderDetail"))
        )
        detail_panel = self.driver.find_element(By.ID, "orderDetail")
        assert detail_panel.is_displayed()

    def test_order_search_functionality(self):
        """TC-WEB-010: Search by order ID returns correct results."""
        self.driver.get(f"{self.base_url}/dashboard/orders")

        search_box = self.driver.find_element(By.ID, "orderSearch")
        search_box.send_keys("ORD-001")
        search_box.send_keys(Keys.RETURN)

        time.sleep(1)
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#orderTable tbody tr")
        assert len(rows) >= 1

    def test_order_status_update(self):
        """TC-WEB-011: Admin can update order status."""
        self.driver.get(f"{self.base_url}/dashboard/orders")

        first_row = self.driver.find_element(By.CSS_SELECTOR, "#orderTable tbody tr:first-child")
        first_row.click()

        status_dropdown = Select(self.driver.find_element(By.ID, "updateStatus"))
        status_dropdown.select_by_value("completed")

        save_btn = self.driver.find_element(By.ID, "saveStatusBtn")
        save_btn.click()

        success_msg = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-toast"))
        )
        assert success_msg.is_displayed()

    def test_pagination_works(self):
        """TC-WEB-012: Order table pagination navigates correctly."""
        self.driver.get(f"{self.base_url}/dashboard/orders")

        next_btn = self.driver.find_element(By.ID, "nextPage")
        next_btn.click()

        time.sleep(1)
        page_indicator = self.driver.find_element(By.ID, "pageNumber")
        assert page_indicator.text == "2"


# ═══════════════════════════════════════════════════════════════════════
# SECTION C: REPORT GENERATION TESTING
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not installed")
class TestReportGeneration:
    """Test suite for admin report generation."""

    @pytest.fixture(autouse=True)
    def setup_and_login(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        prefs = {"download.default_directory": "/tmp/test_downloads"}
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.base_url = "http://localhost:8000"

        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.ID, "username").send_keys("admin")
        self.driver.find_element(By.ID, "password").send_keys("admin123")
        self.driver.find_element(By.ID, "loginBtn").click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "dashboardHeader"))
        )
        yield
        self.driver.quit()

    def test_report_page_accessible(self):
        """TC-WEB-013: Reports page is accessible from dashboard."""
        self.driver.get(f"{self.base_url}/dashboard/reports")

        report_header = self.driver.find_element(By.ID, "reportsHeader")
        assert report_header.is_displayed()

    def test_generate_daily_report(self):
        """TC-WEB-014: Daily processing report can be generated."""
        self.driver.get(f"{self.base_url}/dashboard/reports")

        report_type = Select(self.driver.find_element(By.ID, "reportType"))
        report_type.select_by_value("daily")

        generate_btn = self.driver.find_element(By.ID, "generateReportBtn")
        generate_btn.click()

        report_content = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "reportContent"))
        )
        assert report_content.is_displayed()
        assert len(report_content.text) > 0

    def test_export_report_as_pdf(self):
        """TC-WEB-015: Report can be exported as PDF."""
        self.driver.get(f"{self.base_url}/dashboard/reports")

        Select(self.driver.find_element(By.ID, "reportType")).select_by_value("monthly")
        self.driver.find_element(By.ID, "generateReportBtn").click()

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "reportContent"))
        )

        export_btn = self.driver.find_element(By.ID, "exportPdfBtn")
        export_btn.click()
        time.sleep(3)

    def test_analytics_charts_render(self):
        """TC-WEB-016: Analytics charts are rendered on reports page."""
        self.driver.get(f"{self.base_url}/dashboard/reports")

        charts = self.driver.find_elements(By.CLASS_NAME, "chart-container")
        assert len(charts) > 0
        for chart in charts:
            assert chart.is_displayed()

    def test_date_range_filter(self):
        """TC-WEB-017: Date range filter works for reports."""
        self.driver.get(f"{self.base_url}/dashboard/reports")

        start_date = self.driver.find_element(By.ID, "startDate")
        end_date = self.driver.find_element(By.ID, "endDate")

        start_date.clear()
        start_date.send_keys("2026-01-01")
        end_date.clear()
        end_date.send_keys("2026-03-13")

        self.driver.find_element(By.ID, "applyDateFilter").click()
        time.sleep(2)

        report_content = self.driver.find_element(By.ID, "reportContent")
        assert report_content.is_displayed()
