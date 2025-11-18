# CLAUDE.md - ERPNext Codebase Guide for AI Assistants

> Last updated: 2025-11-18
>
> This document provides a comprehensive guide to the ERPNext codebase structure, development workflows, and conventions to help AI assistants effectively navigate and contribute to the project.

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Technology Stack](#technology-stack)
3. [Directory Structure](#directory-structure)
4. [Architecture & Design Patterns](#architecture--design-patterns)
5. [Development Setup](#development-setup)
6. [Code Organization](#code-organization)
7. [Coding Conventions](#coding-conventions)
8. [Testing Guidelines](#testing-guidelines)
9. [Git Workflow & Commit Conventions](#git-workflow--commit-conventions)
10. [Key Concepts](#key-concepts)
11. [Common Patterns & Best Practices](#common-patterns--best-practices)
12. [Module Reference](#module-reference)

---

## Repository Overview

**ERPNext** is a 100% open-source Enterprise Resource Planning (ERP) system built on the Frappe Framework. It provides comprehensive business management capabilities including accounting, inventory management, manufacturing, CRM, projects, and more.

### Key Statistics
- **~2,503 Python files** across 21 functional modules
- **~621 JavaScript/Vue files** for frontend functionality
- **~621 DocTypes** (data models/entities)
- **License**: GNU General Public License v3.0
- **Repository**: https://github.com/frappe/erpnext
- **Documentation**: https://docs.frappe.io/erpnext/

### Core Principles
- **Modular Design**: Business logic organized into domain-specific modules
- **DocType-Centric**: Entity-based architecture where each business object is a DocType
- **Event-Driven**: Extensive hooks system for extensibility
- **Multi-tenant**: Supports multiple sites/companies from single deployment
- **Regional Customization**: Country-specific tax, compliance, and business rules

---

## Technology Stack

### Backend
- **Python**: 3.10+ (target 3.12 for CI)
- **Framework**: Frappe Framework (>=16.0.0-dev, <17.0.0)
- **Database**: MariaDB 10.6+
- **ORM**: Frappe's built-in ORM (abstraction over MariaDB)

### Frontend
- **UI Framework**: Vue.js 3 (via Frappe UI)
- **Legacy**: jQuery (being phased out)
- **Build Tool**: Rollup/Webpack (managed by Frappe)
- **Styling**: CSS/SCSS

### Development Tools
- **Linting**: Ruff (Python), ESLint (JavaScript)
- **Formatting**: Ruff (Python), Prettier (JS/Vue)
- **Pre-commit**: Configured with multiple hooks
- **Testing**: Pytest with parallel execution
- **CI/CD**: GitHub Actions

### Key Dependencies
```python
# Core
frappe>=16.0.0-dev
Unidecode~=1.4.0
rapidfuzz~=3.12.2
holidays~=0.75

# Data Processing
pandas~=2.2.2
statsmodels~=0.14.5

# Integrations
googlemaps~=4.10.0
plaid-python~=7.2.1
python-youtube~=0.9.7
```

---

## Directory Structure

```
erpnext/
├── .github/                    # GitHub workflows, issue templates
│   ├── workflows/             # CI/CD pipelines
│   │   ├── server-tests-mariadb.yml
│   │   └── ...
│   └── helper/                # CI helper scripts
├── erpnext/                   # Main application directory
│   ├── accounts/              # Financial accounting module
│   ├── assets/                # Asset management
│   ├── buying/                # Purchase orders, suppliers
│   ├── crm/                   # Lead, opportunity, customer management
│   ├── controllers/           # Base controllers & shared logic
│   ├── edi/                   # Electronic Data Interchange
│   ├── erpnext_integrations/  # Third-party integrations
│   ├── manufacturing/         # Production, BOM, work orders
│   ├── projects/              # Project management, tasks, timesheets
│   ├── quality_management/    # Quality procedures & reviews
│   ├── regional/              # Country-specific customizations
│   ├── selling/               # Sales orders, quotations
│   ├── setup/                 # Initial setup, company config
│   ├── stock/                 # Inventory, warehouses, serial numbers
│   ├── subcontracting/        # Subcontracting workflows
│   ├── support/               # Issue tracking, SLA, warranties
│   ├── telephony/             # Call log integration
│   ├── utilities/             # Common utilities
│   ├── public/                # Static assets (JS, CSS, images)
│   │   ├── js/               # Frontend JavaScript
│   │   ├── css/              # Stylesheets
│   │   ├── images/           # Images and icons
│   │   └── dist/             # Built/bundled assets
│   ├── templates/             # Jinja templates for web views
│   ├── patches/               # Database migration patches
│   ├── tests/                 # Global test utilities
│   ├── hooks.py              # Application hooks configuration
│   └── __init__.py
├── requirements.txt           # Python dependencies (if exists)
├── pyproject.toml            # Python project config & dependencies
├── package.json              # Node.js dependencies
├── .pre-commit-config.yaml   # Pre-commit hook configuration
├── commitlint.config.js      # Commit message linting rules
└── README.md                 # Main documentation
```

### Module Directory Structure

Each business module follows a consistent pattern:

```
erpnext/<module_name>/
├── doctype/                   # Data models
│   ├── <doctype_name>/
│   │   ├── <doctype_name>.py         # Python controller (business logic)
│   │   ├── <doctype_name>.js         # Frontend JavaScript
│   │   ├── <doctype_name>.json       # DocType metadata (fields, permissions)
│   │   ├── test_<doctype_name>.py    # Unit tests
│   │   └── __init__.py
│   └── ...
├── report/                    # Custom reports
│   ├── <report_name>/
│   │   ├── <report_name>.py          # Report logic
│   │   ├── <report_name>.js          # Frontend filters/UI
│   │   └── <report_name>.json        # Report metadata
│   └── ...
├── page/                      # Custom pages/dashboards
├── dashboard_chart_source/    # Dashboard data sources
├── workspace/                 # Workspace definitions
├── print_format/              # Custom print templates
├── <module>_dashboard.py      # Dashboard configuration
└── __init__.py
```

---

## Architecture & Design Patterns

### 1. DocType-Centric Architecture

The core building block is the **DocType** - a metadata-driven entity definition:

- **Metadata (JSON)**: Defines fields, permissions, naming, behavior
- **Controller (Python)**: Business logic, validation, hooks
- **Frontend (JavaScript)**: UI customizations, client-side logic
- **Tests**: Unit tests with fixtures

### 2. Event-Driven Hooks System

ERPNext uses Frappe's hooks system (`hooks.py`) for extensibility:

```python
# Document lifecycle hooks
doc_events = {
    "Sales Invoice": {
        "on_submit": "path.to.function",
        "on_cancel": "path.to.function",
        "validate": "path.to.function",
    },
    "*": {  # All doctypes
        "validate": "global.validation.function"
    }
}

# Scheduled events
scheduler_events = {
    "hourly": ["module.task.hourly_job"],
    "daily": ["module.task.daily_job"],
    "cron": {
        "0/15 * * * *": ["module.task.every_15_minutes"]
    }
}
```

### 3. Base Controllers Pattern

Shared business logic is centralized in base controllers:

```
erpnext/controllers/
├── accounts_controller.py      # Accounting entry generation
├── buying_controller.py        # Purchase workflow logic
├── selling_controller.py       # Sales workflow logic
├── stock_controller.py         # Inventory movements
├── taxes_and_totals.py        # Tax calculations
└── transaction_controller.py  # Base for all transactions
```

Specific doctypes inherit from these:
```python
from erpnext.controllers.selling_controller import SellingController

class SalesOrder(SellingController):
    def validate(self):
        super().validate()  # Inherited logic
        # Custom validation
```

### 4. Regional Override Pattern

Country-specific customizations use the `@erpnext.allow_regional` decorator:

```python
# Base implementation
def calculate_tax(doc):
    # Standard tax calculation
    pass

# Regional override (erpnext/regional/italy/utils.py)
def calculate_tax(doc):
    # Italy-specific tax rules
    pass

# Configuration (hooks.py)
regional_overrides = {
    "Italy": {
        "erpnext.accounts.calculate_tax": "erpnext.regional.italy.utils.calculate_tax"
    }
}
```

### 5. Naming Series Pattern

Flexible naming for documents:
```python
naming_series_variables = {
    "FY": "erpnext.accounts.utils.parse_naming_series_variable",  # Fiscal year
    "ABBR": "erpnext.accounts.utils.parse_naming_series_variable", # Company abbreviation
}
# Example: SINV-.FY.-.##### → SINV-2025-00001
```

---

## Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- MariaDB 10.6+
- Redis
- wkhtmltopdf (for PDF generation)

### Installation (using Bench)

```bash
# 1. Install bench
pip install frappe-bench

# 2. Initialize bench
bench init frappe-bench --frappe-branch develop
cd frappe-bench

# 3. Create a new site
bench new-site erpnext.localhost

# 4. Get ERPNext app
bench get-app https://github.com/frappe/erpnext --branch develop

# 5. Install ERPNext on site
bench --site erpnext.localhost install-app erpnext

# 6. Start development server
bench start
```

Access at: `http://erpnext.localhost:8000/app`

### Development Commands

```bash
# Start development server
bench start

# Run tests
bench --site erpnext.localhost run-tests --app erpnext

# Run tests for specific module
bench --site erpnext.localhost run-tests --app erpnext --module erpnext.accounts

# Run linting
ruff check .
ruff format .

# Run pre-commit hooks
pre-commit run --all-files

# Build assets
bench build --app erpnext

# Clear cache
bench --site erpnext.localhost clear-cache

# Console access
bench --site erpnext.localhost console
```

---

## Code Organization

### Python Module Organization

#### DocType Controllers

```python
# erpnext/accounts/doctype/sales_invoice/sales_invoice.py
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.controllers.selling_controller import SellingController

class SalesInvoice(SellingController):
    """Sales Invoice DocType controller"""

    def validate(self):
        """Called before saving (insert/update)"""
        super().validate()
        self.validate_posting_date()
        self.calculate_taxes_and_totals()

    def on_submit(self):
        """Called when document is submitted"""
        self.make_gl_entries()
        self.update_stock_ledger()

    def on_cancel(self):
        """Called when document is cancelled"""
        self.cancel_gl_entries()
        self.update_stock_ledger()

    def validate_posting_date(self):
        """Custom validation method"""
        if self.posting_date > frappe.utils.today():
            frappe.throw(_("Posting date cannot be future date"))
```

#### Utility Functions

```python
# erpnext/accounts/utils.py
import frappe

@frappe.whitelist()
def get_account_balance(account, date=None):
    """Whitelisted function - callable from frontend"""
    # Implementation
    return balance

def internal_helper_function():
    """Not whitelisted - internal use only"""
    pass
```

### JavaScript Organization

#### DocType Frontend

```javascript
// erpnext/accounts/doctype/sales_invoice/sales_invoice.js
frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        // Called when form is loaded/refreshed
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Make Payment'), () => {
                // Custom button action
            });
        }
    },

    customer: function(frm) {
        // Triggered when customer field changes
        frappe.call({
            method: 'erpnext.accounts.utils.get_customer_details',
            args: { customer: frm.doc.customer },
            callback: (r) => {
                if (r.message) {
                    frm.set_value('customer_address', r.message.address);
                }
            }
        });
    },

    validate: function(frm) {
        // Client-side validation before save
        if (!frm.doc.items || frm.doc.items.length === 0) {
            frappe.throw(__('Please add items'));
        }
    }
});

// Child table (items) events
frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        // Triggered when item is selected in child table
        let row = locals[cdt][cdn];
        // Update row
    }
});
```

### Test Organization

```python
# erpnext/accounts/doctype/sales_invoice/test_sales_invoice.py
import frappe
import unittest
from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return

class TestSalesInvoice(unittest.TestCase):
    """Test cases for Sales Invoice"""

    def setUp(self):
        """Run before each test"""
        frappe.set_user("Administrator")

    def tearDown(self):
        """Run after each test"""
        frappe.db.rollback()

    def test_sales_invoice_submission(self):
        """Test invoice submission creates GL entries"""
        invoice = make_test_sales_invoice()
        invoice.submit()

        # Verify GL entries created
        gl_entries = frappe.get_all('GL Entry',
            filters={'voucher_no': invoice.name},
            fields=['account', 'debit', 'credit'])

        self.assertTrue(len(gl_entries) > 0)

    def test_sales_return(self):
        """Test return invoice creation"""
        invoice = make_test_sales_invoice()
        invoice.submit()

        return_invoice = make_sales_return(invoice.name)
        self.assertEqual(return_invoice.is_return, 1)

def make_test_sales_invoice():
    """Test fixture for creating sales invoice"""
    invoice = frappe.get_doc({
        'doctype': 'Sales Invoice',
        'customer': '_Test Customer',
        'items': [{
            'item_code': '_Test Item',
            'qty': 1,
            'rate': 100
        }]
    })
    invoice.insert()
    return invoice
```

---

## Coding Conventions

### Python Style Guide

ERPNext follows **Ruff** linting and formatting rules (configured in `pyproject.toml`):

#### General Rules
- **Line Length**: 110 characters
- **Indentation**: Tabs (not spaces) - this is project convention
- **Quote Style**: Double quotes `"` for strings
- **Target Version**: Python 3.10+
- **Docstrings**: Google-style docstrings preferred

#### Naming Conventions
```python
# Variables and functions: snake_case
customer_name = "John"
def calculate_total_amount():
    pass

# Classes: PascalCase
class SalesInvoice:
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_CURRENCY = "USD"
MAX_ITEMS = 100

# Private/internal: prefix with _
def _internal_helper():
    pass
```

#### Import Order (Ruff isort)
```python
# 1. Standard library
import os
import sys
from datetime import datetime

# 2. Third-party
import pandas as pd

# 3. Frappe framework
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate

# 4. ERPNext modules
from erpnext.controllers.selling_controller import SellingController
from erpnext.stock.utils import get_stock_balance
```

#### Common Patterns

**Database Queries:**
```python
# Get single document
doc = frappe.get_doc("Sales Invoice", "SINV-00001")

# Get list of documents
invoices = frappe.get_all("Sales Invoice",
    filters={"customer": "CUST-001", "docstatus": 1},
    fields=["name", "grand_total", "posting_date"],
    order_by="posting_date desc",
    limit=10)

# Raw SQL (use sparingly)
result = frappe.db.sql("""
    SELECT name, grand_total
    FROM `tabSales Invoice`
    WHERE customer = %s
""", (customer,), as_dict=True)

# Get single value
customer_name = frappe.db.get_value("Customer", customer, "customer_name")
```

**Error Handling:**
```python
# User-facing error
frappe.throw(_("Customer {0} not found").format(customer))

# Validation error with field
frappe.throw(_("Invalid quantity"), frappe.ValidationError)

# Message to user (warning)
frappe.msgprint(_("Stock may not be available"))

# Log for debugging
frappe.log_error("Error details", "Title")
```

**Translations:**
```python
# Always wrap user-facing strings with _()
frappe.throw(_("Cannot submit invoice without items"))
frappe.msgprint(_("Invoice {0} created successfully").format(invoice.name))
```

### JavaScript Style Guide

#### General Rules
- **Linting**: ESLint (see `.pre-commit-config.yaml`)
- **Formatting**: Prettier (automatic formatting)
- **Indentation**: Tabs
- **Semicolons**: Optional but consistent

#### Common Patterns

```javascript
// API calls
frappe.call({
    method: 'erpnext.accounts.doctype.sales_invoice.sales_invoice.make_payment_entry',
    args: {
        invoice: frm.doc.name,
        amount: 1000
    },
    callback: function(r) {
        if (r.message) {
            frappe.msgprint(__('Payment entry created'));
            frm.reload_doc();
        }
    }
});

// Setting field values
frm.set_value('customer_address', address);

// Field properties
frm.set_df_property('posting_date', 'read_only', 1);
frm.toggle_reqd('payment_terms_template', !frm.doc.immediate_payment);

// Filtering link fields
frm.set_query('account', function() {
    return {
        filters: {
            'account_type': 'Receivable',
            'company': frm.doc.company
        }
    };
});

// Custom buttons
if (frm.doc.docstatus === 1) {
    frm.add_custom_button(__('Create Payment'), function() {
        // Action
    }, __('Actions'));
}
```

---

## Testing Guidelines

### Test Structure

ERPNext uses **pytest** for testing with parallel execution support.

#### Running Tests

```bash
# All tests
bench --site erpnext.localhost run-tests --app erpnext

# Specific module
bench --site erpnext.localhost run-tests --app erpnext --module erpnext.accounts

# Specific doctype
bench --site erpnext.localhost run-tests --app erpnext \
    --doctype "Sales Invoice"

# Parallel tests (CI mode - 4 containers)
bench --site erpnext.localhost run-parallel-tests --app erpnext \
    --total-builds 4 --build-number 1
```

### Writing Tests

```python
# test_my_feature.py
import frappe
import unittest

class TestMyFeature(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run once before all tests in class"""
        # Setup test data
        pass

    def setUp(self):
        """Run before each test"""
        frappe.set_user("Administrator")

    def tearDown(self):
        """Run after each test"""
        frappe.db.rollback()

    def test_basic_functionality(self):
        """Test description"""
        # Arrange
        doc = frappe.get_doc({
            'doctype': 'Sales Invoice',
            'customer': '_Test Customer'
        })

        # Act
        doc.insert()

        # Assert
        self.assertEqual(doc.docstatus, 0)
        self.assertIsNotNone(doc.name)
```

### Test Fixtures

Create reusable test data:
```python
def create_test_customer(customer_name="_Test Customer"):
    """Test fixture for customer"""
    if not frappe.db.exists("Customer", customer_name):
        customer = frappe.get_doc({
            'doctype': 'Customer',
            'customer_name': customer_name,
            'customer_type': 'Individual',
            'customer_group': '_Test Customer Group',
            'territory': '_Test Territory'
        })
        customer.insert(ignore_permissions=True)
    return frappe.get_doc("Customer", customer_name)
```

### CI/CD Testing

GitHub Actions runs tests on every PR:
- **4 parallel containers** for faster execution
- **MariaDB 10.6** database
- **Python 3.12**
- **Code coverage** tracking (Codecov)

See `.github/workflows/server-tests-mariadb.yml` for full configuration.

---

## Git Workflow & Commit Conventions

### Branch Strategy

- **`develop`**: Main development branch (default)
- **`version-15`**, **`version-14`**: Stable release branches
- **Feature branches**: `feature/description` or `fix/description`
- **NO direct commits to `develop`**: Always create PR

### Commit Message Format

ERPNext uses **Conventional Commits** enforced by `commitlint`:

```
<type>: <subject>

[optional body]

[optional footer]
```

#### Allowed Types
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring (no behavior change)
- `perf`: Performance improvement
- `style`: Code style changes (formatting, semicolons)
- `test`: Adding or modifying tests
- `docs`: Documentation changes
- `chore`: Maintenance tasks (dependencies, build)
- `ci`: CI/CD configuration changes
- `revert`: Reverting previous commit

#### Examples

```bash
# Good commits
feat: add multi-currency support to payment entry
fix: prevent duplicate serial numbers in stock entry
refactor: optimize gl entry query performance
docs: update installation instructions in README
test: add test cases for sales return

# Bad commits (will be rejected)
updated files
fix bug
changes
```

### Pull Request Guidelines

1. **Create PR against `develop`** branch
2. **Clear title** explaining the change
3. **Description** with:
   - What changed and why
   - Related issue number (#1234)
   - Screenshots/GIFs for UI changes
4. **Tests**: Add/update tests for changes
5. **Lint**: Ensure pre-commit hooks pass
6. **Review**: Address review comments

### Pre-commit Hooks

Configured in `.pre-commit-config.yaml`:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Hooks include:**
- Trailing whitespace removal
- YAML/JSON/TOML validation
- No direct commits to `develop`
- Merge conflict markers check
- Python AST validation
- Ruff linting & formatting (Python)
- Prettier formatting (JS/Vue)
- ESLint linting (JavaScript)

---

## Key Concepts

### 1. DocTypes

**DocTypes** are metadata-driven entity definitions. Each DocType has:

- **Fields**: Text, Number, Date, Link, Table, etc.
- **Permissions**: Role-based access control
- **Naming**: Auto-naming patterns
- **Validation**: Required fields, validation rules
- **Submission**: Draft → Submitted → Cancelled workflow
- **Amendments**: Modify cancelled/submitted docs

### 2. Document States (docstatus)

```python
docstatus = 0  # Draft (editable)
docstatus = 1  # Submitted (locked, creates ledger entries)
docstatus = 2  # Cancelled (creates reverse ledger entries)
```

### 3. Naming Series

Flexible document naming:
```
Pattern: SINV-.FY.-.#####
Result: SINV-2025-00001, SINV-2025-00002, ...

Variables:
- .FY. = Fiscal year
- .YY. = 2-digit year
- .YYYY. = 4-digit year
- .MM. = Month
- .DD. = Day
- .##### = Counter (5 digits)
```

### 4. Links and Child Tables

```python
# Link field (foreign key)
customer = doc.customer  # Links to Customer DocType

# Child table (one-to-many)
for item in doc.items:  # 'items' is child table
    print(item.item_code, item.qty)
```

### 5. Accounting Ledger Entries

Financial transactions create:
- **GL Entry**: General Ledger (accounting entries)
- **SL Entry**: Stock Ledger (inventory movements)
- **Payment Ledger Entry**: Payment tracking

### 6. Permission System

```python
# Check permission
if frappe.has_permission("Sales Invoice", "write", doc):
    # Allow edit
    pass

# Role-based permissions defined in DocType JSON
# Can be dynamically controlled via Permission Manager
```

### 7. Hooks System

See `erpnext/hooks.py` for comprehensive list:

```python
# Document hooks
doc_events = {
    "Sales Invoice": {
        "validate": "path.to.validation_function",
        "on_submit": "path.to.submit_function",
        "on_cancel": "path.to.cancel_function",
        "on_trash": "path.to.delete_function"
    }
}

# Scheduler hooks
scheduler_events = {
    "hourly": ["erpnext.module.task.run_hourly"],
    "daily": ["erpnext.module.task.run_daily"],
    "cron": {
        "0/15 * * * *": ["erpnext.module.task.every_15_min"]
    }
}

# Global hooks
override_whitelisted_methods = {
    "frappe.path.method": "erpnext.custom.method"
}
```

---

## Common Patterns & Best Practices

### 1. Creating Documents

```python
# Method 1: Direct creation
doc = frappe.get_doc({
    'doctype': 'Sales Invoice',
    'customer': 'CUST-001',
    'items': [
        {'item_code': 'ITEM-001', 'qty': 5, 'rate': 100}
    ]
})
doc.insert()
doc.submit()

# Method 2: Using new_doc
doc = frappe.new_doc('Sales Invoice')
doc.customer = 'CUST-001'
doc.append('items', {
    'item_code': 'ITEM-001',
    'qty': 5,
    'rate': 100
})
doc.insert()
```

### 2. Updating Documents

```python
# Get and modify
doc = frappe.get_doc('Sales Invoice', 'SINV-00001')
doc.remarks = 'Updated remarks'
doc.save()  # Only if draft (docstatus=0)

# Direct DB update (use cautiously)
frappe.db.set_value('Sales Invoice', 'SINV-00001', 'remarks', 'New remarks')
```

### 3. Querying with Filters

```python
# Complex filters
invoices = frappe.get_all('Sales Invoice',
    filters=[
        ['customer', '=', 'CUST-001'],
        ['posting_date', '>=', '2025-01-01'],
        ['grand_total', '>', 1000],
        ['docstatus', '=', 1]
    ],
    or_filters=[
        ['payment_status', '=', 'Paid'],
        ['payment_status', '=', 'Partially Paid']
    ],
    fields=['name', 'grand_total', 'outstanding_amount'])
```

### 4. Transactions & Error Handling

```python
try:
    # DB operations are automatically in transaction
    doc.save()
    doc.submit()
    frappe.db.commit()  # Explicitly commit if needed
except Exception as e:
    frappe.db.rollback()  # Rollback on error
    frappe.log_error(frappe.get_traceback(), "Invoice Submission Error")
    frappe.throw(_("Failed to submit invoice: {0}").format(str(e)))
```

### 5. API Whitelisting

```python
@frappe.whitelist()
def get_customer_balance(customer):
    """This function can be called from frontend"""
    # frappe.whitelist() makes it accessible via API
    balance = frappe.db.get_value('Customer', customer, 'outstanding_amount')
    return balance

# Not whitelisted - internal use only
def internal_calculation():
    pass
```

### 6. Background Jobs

```python
# Queue a background job
frappe.enqueue(
    method='erpnext.accounts.utils.process_bulk_invoices',
    queue='long',  # short, default, long
    timeout=3000,
    is_async=True,
    **{'customer': 'CUST-001'}
)
```

### 7. Caching

```python
# Cache function result
@frappe.whitelist()
def get_exchange_rate(from_currency, to_currency):
    cache_key = f"exchange_rate:{from_currency}:{to_currency}"
    rate = frappe.cache().get(cache_key)

    if not rate:
        rate = fetch_from_api(from_currency, to_currency)
        frappe.cache().setex(cache_key, rate, 3600)  # 1 hour

    return rate
```

### 8. Regional Customizations

```python
# Base function
def calculate_gst(doc):
    # Standard GST calculation
    pass

# Regional override
@erpnext.allow_regional
def calculate_gst(doc):
    # Country-specific GST
    pass
```

### 9. Performance Optimization

```python
# Bad: N+1 query problem
for invoice in invoices:
    customer = frappe.get_doc('Customer', invoice.customer)
    print(customer.customer_name)

# Good: Fetch in single query
invoices = frappe.get_all('Sales Invoice',
    filters={'docstatus': 1},
    fields=['name', '`tabCustomer`.customer_name'],
    join='`tabCustomer` on `tabSales Invoice`.customer = `tabCustomer`.name')
```

### 10. Testing Best Practices

```python
# Use test records (fixtures)
def setUp(self):
    self.customer = create_test_customer()
    self.item = create_test_item()

# Clean up after tests
def tearDown(self):
    frappe.db.rollback()  # Rollback test data

# Use meaningful assertions
self.assertEqual(invoice.grand_total, 1100)
self.assertTrue(invoice.docstatus == 1, "Invoice should be submitted")
self.assertRaises(frappe.ValidationError, doc.submit)
```

---

## Module Reference

### Core Business Modules

#### 1. **accounts** (185 DocTypes)
Financial accounting, GL entries, invoices, payments, bank reconciliation, taxes
- Key: `sales_invoice`, `purchase_invoice`, `payment_entry`, `journal_entry`, `gl_entry`

#### 2. **stock** (78 DocTypes)
Inventory management, warehouses, serial/batch tracking, stock movements
- Key: `stock_entry`, `delivery_note`, `purchase_receipt`, `item`, `warehouse`

#### 3. **manufacturing** (48 DocTypes)
Production planning, BOM, work orders, job cards
- Key: `bom`, `work_order`, `job_card`, `production_plan`

#### 4. **selling** (27 DocTypes)
Sales orders, quotations, customers, sales teams
- Key: `sales_order`, `quotation`, `customer`

#### 5. **buying** (25 DocTypes)
Purchase orders, supplier management, RFQs
- Key: `purchase_order`, `supplier`, `request_for_quotation`

#### 6. **crm** (20 DocTypes)
Leads, opportunities, campaigns, prospects
- Key: `lead`, `opportunity`, `prospect`, `crm_note`

#### 7. **projects** (13 DocTypes)
Project management, tasks, timesheets, activity tracking
- Key: `project`, `task`, `timesheet`

#### 8. **assets** (11 DocTypes)
Asset tracking, depreciation, maintenance
- Key: `asset`, `asset_category`, `asset_movement`

#### 9. **support** (6 DocTypes)
Issue tracking, SLA management, warranties
- Key: `issue`, `service_level_agreement`, `warranty_claim`

#### 10. **quality_management** (4 DocTypes)
Quality procedures, reviews, goals
- Key: `quality_procedure`, `quality_review`

### Supporting Modules

- **setup**: Company, users, authorization, initial configuration
- **controllers**: Base controllers for shared business logic
- **regional**: Country-specific tax & compliance (India, UAE, Italy, etc.)
- **erpnext_integrations**: Third-party integrations (Plaid, Shopify, etc.)
- **telephony**: Call log integration
- **utilities**: Common utilities, reports, bulk operations
- **portal**: Customer portal views
- **templates**: Web templates and routes

---

## Common Commands Reference

### Development

```bash
# Start server
bench start

# Restart after code changes
bench restart

# Update bench
bench update

# Migrate database
bench --site erpnext.localhost migrate

# Clear cache
bench --site erpnext.localhost clear-cache

# Build assets
bench build --app erpnext

# Console
bench --site erpnext.localhost console

# Backup
bench --site erpnext.localhost backup

# Restore
bench --site erpnext.localhost restore /path/to/backup
```

### Testing

```bash
# All tests
bench --site erpnext.localhost run-tests --app erpnext

# Verbose output
bench --site erpnext.localhost run-tests --app erpnext -v

# Specific module
bench --site erpnext.localhost run-tests --app erpnext \
    --module erpnext.accounts.doctype.sales_invoice.test_sales_invoice

# Profile slow tests
bench --site erpnext.localhost run-tests --app erpnext --profile
```

### Code Quality

```bash
# Ruff linting
ruff check .
ruff check . --fix

# Ruff formatting
ruff format .

# Pre-commit hooks
pre-commit run --all-files

# Type checking (if enabled)
mypy erpnext/
```

---

## Important Files

### Configuration
- `pyproject.toml` - Python dependencies & Ruff config
- `package.json` - Node.js dependencies
- `.pre-commit-config.yaml` - Pre-commit hooks
- `commitlint.config.js` - Commit message rules

### Core Application
- `erpnext/hooks.py` - Application hooks & configuration
- `erpnext/__init__.py` - Version & package initialization
- `erpnext/controllers/` - Base controllers
- `erpnext/patches/` - Database migration patches

### CI/CD
- `.github/workflows/server-tests-mariadb.yml` - Test pipeline
- `.github/helper/install.sh` - CI installation script

### Documentation
- `README.md` - Main project README
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Community guidelines
- `SECURITY.md` - Security policy

---

## Tips for AI Assistants

### When Working with ERPNext:

1. **Always check DocType metadata** (`.json` files) to understand field structure
2. **Look for base controllers** before implementing common logic
3. **Use hooks.py** to understand event-driven architecture
4. **Check regional/** for country-specific implementations
5. **Maintain tab indentation** (project convention)
6. **Use double quotes** for Python strings
7. **Wrap user-facing strings with `_()`** for translation
8. **Write tests** for new features
9. **Follow conventional commits** format
10. **Run pre-commit hooks** before committing

### Common Pitfalls to Avoid:

1. ❌ Don't commit directly to `develop` branch
2. ❌ Don't use spaces for indentation (use tabs)
3. ❌ Don't bypass validation in production code
4. ❌ Don't create GL entries manually (use controller methods)
5. ❌ Don't modify submitted documents (docstatus=1) without canceling
6. ❌ Don't forget to check permissions before operations
7. ❌ Don't use raw SQL when ORM methods are available
8. ❌ Don't hardcode company/currency (make it configurable)
9. ❌ Don't skip writing tests
10. ❌ Don't forget to update documentation

### Before Making Changes:

1. ✅ Read existing implementation in the module
2. ✅ Check if base controller already provides the functionality
3. ✅ Look for similar patterns in the codebase
4. ✅ Verify DocType structure and field names
5. ✅ Review related tests
6. ✅ Check hooks.py for existing event handlers
7. ✅ Consider backward compatibility
8. ✅ Plan for regional variations if applicable

---

## Resources

- **Official Documentation**: https://docs.frappe.io/erpnext/
- **Frappe Framework Docs**: https://frappeframework.com/docs
- **Developer Forum**: https://discuss.frappe.io/c/erpnext/6
- **Source Code**: https://github.com/frappe/erpnext
- **API Reference**: https://frappeframework.com/docs/user/en/api
- **Frappe School**: https://frappe.school (tutorials & courses)

---

## Version Info

- **Current Version**: 15.x.x-develop (targeting v16)
- **Frappe Framework**: >=16.0.0-dev, <17.0.0
- **Python**: 3.10+ (CI uses 3.12)
- **Node.js**: 18+
- **Database**: MariaDB 10.6+

---

*This document is maintained for AI assistants working with the ERPNext codebase. For general contribution guidelines, see [CONTRIBUTING.md](.github/CONTRIBUTING.md).*
