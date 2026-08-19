import json
import os
from datetime import date
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP
from pydantic import Field

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

_DATA_PATH = Path(__file__).parent / "data" / "netsuite.json"
_db: dict = json.loads(_DATA_PATH.read_text())


def _match(record: dict, field: str, value: str) -> bool:
    """Case-insensitive substring match on a field."""
    return value.lower() in str(record.get(field, "")).lower()


def _date_in_range(record: dict, field: str, start_date: Optional[str], end_date: Optional[str]) -> bool:
    """Return True if record[field] falls within [start_date, end_date] (inclusive ISO strings)."""
    val = record.get(field, "")
    if not val:
        return True
    if start_date and val < start_date:
        return False
    if end_date and val > end_date:
        return False
    return True


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="netsuite-mock",
    version="1.0.0",
    instructions=(
        "Mock NetSuite ERP for Harbour Outdoor luxury furniture. Query and manage customers, "
        "items, inventory, sales orders, invoices, purchase orders, vendors, fulfillments, "
        "and transactions."
    ),
)

# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

@mcp.tool()
def get_customers(
    id: Optional[str] = Field(default=None, description="Filter by customer ID, e.g. C-001"),
    name: Optional[str] = Field(default=None, description="Filter by customer name (partial match)"),
    customer_type: Optional[str] = Field(default=None, description="Filter by type: distributor | retail_chain | dtc | ecommerce"),
    status: Optional[str] = Field(default=None, description="Filter by status: active | inactive"),
    account_rep: Optional[str] = Field(default=None, description="Filter by account rep name (partial match)"),
) -> list[dict]:
    """List customers. Optionally filter by ID, name, type, status, or account rep."""
    results = _db["customers"]
    if id:
        results = [r for r in results if r["id"].upper() == id.upper()]
    if name:
        results = [r for r in results if _match(r, "name", name)]
    if customer_type:
        results = [r for r in results if _match(r, "customer_type", customer_type)]
    if status:
        results = [r for r in results if _match(r, "status", status)]
    if account_rep:
        results = [r for r in results if _match(r, "account_rep", account_rep)]
    return results


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

@mcp.tool()
def get_items(
    id: Optional[str] = Field(default=None, description="Filter by item ID, e.g. I-101"),
    sku: Optional[str] = Field(default=None, description="Filter by SKU (partial match)"),
    name: Optional[str] = Field(default=None, description="Filter by item name (partial match)"),
    category: Optional[str] = Field(default=None, description="Filter by category: still_water | sparkling_water | alkaline_water"),
    status: Optional[str] = Field(default=None, description="Filter by status: active | discontinued"),
) -> list[dict]:
    """List product SKUs. Optionally filter by ID, SKU, name, category, or status."""
    results = _db["items"]
    if id:
        results = [r for r in results if r["id"].upper() == id.upper()]
    if sku:
        results = [r for r in results if _match(r, "sku", sku)]
    if name:
        results = [r for r in results if _match(r, "name", name)]
    if category:
        results = [r for r in results if _match(r, "category", category)]
    if status:
        results = [r for r in results if _match(r, "status", status)]
    return results


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@mcp.tool()
def get_inventory(
    item_id: Optional[str] = Field(default=None, description="Filter by item ID, e.g. I-101"),
    item_name: Optional[str] = Field(default=None, description="Filter by item name (partial match)"),
    location_id: Optional[str] = Field(default=None, description="Filter by location ID, e.g. LOC-01"),
    location_name: Optional[str] = Field(default=None, description="Filter by location name (partial match)"),
    low_stock: bool = Field(default=False, description="If true, return only records where quantity_available <= reorder_point"),
) -> list[dict]:
    """List inventory by item and location. Filter by item, location, or flag low-stock."""
    results = _db["inventory"]
    if item_id:
        results = [r for r in results if r["item_id"].upper() == item_id.upper()]
    if item_name:
        results = [r for r in results if _match(r, "item_name", item_name)]
    if location_id:
        results = [r for r in results if r["location_id"].upper() == location_id.upper()]
    if location_name:
        results = [r for r in results if _match(r, "location_name", location_name)]
    if low_stock:
        results = [r for r in results if r["quantity_available"] <= r["reorder_point"]]
    return results


# ---------------------------------------------------------------------------
# Sales Orders
# ---------------------------------------------------------------------------

@mcp.tool()
def get_sales_orders(
    id: Optional[str] = Field(default=None, description="Filter by order ID, e.g. SO-1001"),
    order_number: Optional[str] = Field(default=None, description="Filter by order number (partial match)"),
    customer_id: Optional[str] = Field(default=None, description="Filter by customer ID, e.g. C-001"),
    customer_name: Optional[str] = Field(default=None, description="Filter by customer name (partial match)"),
    status: Optional[str] = Field(default=None, description="Filter by status: pending_approval | approved | partially_fulfilled | fulfilled | closed | cancelled"),
    account_rep: Optional[str] = Field(default=None, description="Filter by account rep name (partial match)"),
    start_date: Optional[str] = Field(default=None, description="Filter by created_date >= this ISO date, e.g. 2026-07-01"),
    end_date: Optional[str] = Field(default=None, description="Filter by created_date <= this ISO date, e.g. 2026-07-31"),
) -> list[dict]:
    """List sales orders. Filter by ID, customer, status, account rep, or date range."""
    results = _db["sales_orders"]
    if id:
        results = [r for r in results if r["id"].upper() == id.upper()]
    if order_number:
        results = [r for r in results if _match(r, "order_number", order_number)]
    if customer_id:
        results = [r for r in results if r["customer_id"].upper() == customer_id.upper()]
    if customer_name:
        results = [r for r in results if _match(r, "customer_name", customer_name)]
    if status:
        results = [r for r in results if _match(r, "status", status)]
    if account_rep:
        results = [r for r in results if _match(r, "account_rep", account_rep)]
    if start_date or end_date:
        results = [r for r in results if _date_in_range(r, "created_date", start_date, end_date)]
    return results


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

@mcp.tool()
def get_invoices(
    id: Optional[str] = Field(default=None, description="Filter by invoice ID, e.g. INV-2001"),
    invoice_number: Optional[str] = Field(default=None, description="Filter by invoice number (partial match)"),
    customer_id: Optional[str] = Field(default=None, description="Filter by customer ID, e.g. C-001"),
    customer_name: Optional[str] = Field(default=None, description="Filter by customer name (partial match)"),
    status: Optional[str] = Field(default=None, description="Filter by status: open | partially_paid | paid | overdue"),
    start_date: Optional[str] = Field(default=None, description="Filter by created_date >= this ISO date"),
    end_date: Optional[str] = Field(default=None, description="Filter by created_date <= this ISO date"),
) -> list[dict]:
    """List invoices. Filter by ID, customer, status, or date range."""
    results = _db["invoices"]
    if id:
        results = [r for r in results if r["id"].upper() == id.upper()]
    if invoice_number:
        results = [r for r in results if _match(r, "invoice_number", invoice_number)]
    if customer_id:
        results = [r for r in results if r["customer_id"].upper() == customer_id.upper()]
    if customer_name:
        results = [r for r in results if _match(r, "customer_name", customer_name)]
    if status:
        results = [r for r in results if _match(r, "status", status)]
    if start_date or end_date:
        results = [r for r in results if _date_in_range(r, "created_date", start_date, end_date)]
    return results


# ---------------------------------------------------------------------------
# Purchase Orders
# ---------------------------------------------------------------------------

@mcp.tool()
def get_purchase_orders(
    id: Optional[str] = Field(default=None, description="Filter by PO ID, e.g. PO-3001"),
    po_number: Optional[str] = Field(default=None, description="Filter by PO number (partial match)"),
    vendor_id: Optional[str] = Field(default=None, description="Filter by vendor ID, e.g. V-001"),
    vendor_name: Optional[str] = Field(default=None, description="Filter by vendor name (partial match)"),
    status: Optional[str] = Field(default=None, description="Filter by status: open | partially_received | received | closed"),
) -> list[dict]:
    """List purchase orders. Filter by ID, vendor, or status."""
    results = _db["purchase_orders"]
    if id:
        results = [r for r in results if r["id"].upper() == id.upper()]
    if po_number:
        results = [r for r in results if _match(r, "po_number", po_number)]
    if vendor_id:
        results = [r for r in results if r["vendor_id"].upper() == vendor_id.upper()]
    if vendor_name:
        results = [r for r in results if _match(r, "vendor_name", vendor_name)]
    if status:
        results = [r for r in results if _match(r, "status", status)]
    return results


# ---------------------------------------------------------------------------
# Vendors
# ---------------------------------------------------------------------------

@mcp.tool()
def get_vendors(
    id: Optional[str] = Field(default=None, description="Filter by vendor ID, e.g. V-001"),
    name: Optional[str] = Field(default=None, description="Filter by vendor name (partial match)"),
    vendor_type: Optional[str] = Field(default=None, description="Filter by type: supplier | co-packer | logistics"),
    status: Optional[str] = Field(default=None, description="Filter by status: active | inactive"),
) -> list[dict]:
    """List vendors. Filter by ID, name, type, or status."""
    results = _db["vendors"]
    if id:
        results = [r for r in results if r["id"].upper() == id.upper()]
    if name:
        results = [r for r in results if _match(r, "name", name)]
    if vendor_type:
        results = [r for r in results if _match(r, "vendor_type", vendor_type)]
    if status:
        results = [r for r in results if _match(r, "status", status)]
    return results


# ---------------------------------------------------------------------------
# Item Fulfillments
# ---------------------------------------------------------------------------

@mcp.tool()
def get_item_fulfillments(
    id: Optional[str] = Field(default=None, description="Filter by fulfillment ID, e.g. IF-4001"),
    sales_order_id: Optional[str] = Field(default=None, description="Filter by linked sales order ID, e.g. SO-1001"),
    customer_name: Optional[str] = Field(default=None, description="Filter by customer name (partial match)"),
    status: Optional[str] = Field(default=None, description="Filter by status: picked | packed | shipped | delivered"),
    carrier: Optional[str] = Field(default=None, description="Filter by carrier name (partial match)"),
) -> list[dict]:
    """List item fulfillments. Filter by ID, sales order, customer, status, or carrier."""
    results = _db["item_fulfillments"]
    if id:
        results = [r for r in results if r["id"].upper() == id.upper()]
    if sales_order_id:
        results = [r for r in results if r["sales_order_id"].upper() == sales_order_id.upper()]
    if customer_name:
        results = [r for r in results if _match(r, "customer_name", customer_name)]
    if status:
        results = [r for r in results if _match(r, "status", status)]
    if carrier:
        results = [r for r in results if _match(r, "carrier", carrier)]
    return results


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@mcp.tool()
def get_transactions(
    transaction_type: Optional[str] = Field(default=None, description="Filter by type: invoice | payment | credit_memo | journal_entry"),
    account: Optional[str] = Field(default=None, description="Filter by account name (partial match)"),
    start_date: Optional[str] = Field(default=None, description="Filter by date >= this ISO date, e.g. 2026-07-01"),
    end_date: Optional[str] = Field(default=None, description="Filter by date <= this ISO date, e.g. 2026-07-31"),
) -> list[dict]:
    """List general ledger / financial transactions. Filter by type, account, or date range."""
    results = _db["transactions"]
    if transaction_type:
        results = [r for r in results if _match(r, "transaction_type", transaction_type)]
    if account:
        results = [r for r in results if _match(r, "account", account)]
    if start_date or end_date:
        results = [r for r in results if _date_in_range(r, "date", start_date, end_date)]
    return results


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

_SEARCH_NAME_FIELDS: dict[str, list[str]] = {
    "customers": ["name", "email"],
    "items": ["name", "sku", "description"],
    "sales_orders": ["order_number", "customer_name", "po_number", "memo"],
    "invoices": ["invoice_number", "customer_name", "memo"],
    "purchase_orders": ["po_number", "vendor_name", "memo"],
    "vendors": ["name", "email"],
}


@mcp.tool()
def search_records(
    record_type: str = Field(description="Collection to search: customers | items | sales_orders | invoices | purchase_orders | vendors"),
    query: str = Field(description="Partial match query string applied across name and subject fields"),
) -> list[dict]:
    """Search any collection by record_type with a partial match across name and subject fields."""
    collection = _db.get(record_type)
    if collection is None:
        return [{"error": f"Unknown record_type '{record_type}'. Valid options: {list(_SEARCH_NAME_FIELDS.keys())}"}]
    fields = _SEARCH_NAME_FIELDS.get(record_type, ["name"])
    q = query.lower()
    return [
        r for r in collection
        if any(q in str(r.get(f, "")).lower() for f in fields)
    ]


# ---------------------------------------------------------------------------
# Write — Sales Orders
# ---------------------------------------------------------------------------

@mcp.tool()
def create_sales_order(
    customer_id: str = Field(description="Customer ID, e.g. C-001"),
    line_items_json: str = Field(description='JSON array of line items, e.g. [{"item_id":"I-101","quantity":100,"unit_price_usd":1.58}]'),
    ship_date: Optional[str] = Field(default=None, description="Requested ship date (ISO date)"),
    shipping_method: Optional[str] = Field(default=None, description="Shipping method, e.g. LTL Freight"),
    po_number: Optional[str] = Field(default=None, description="Customer PO number"),
    memo: Optional[str] = Field(default=None, description="Order memo / notes"),
    account_rep: Optional[str] = Field(default=None, description="Account rep name"),
) -> dict:
    """Create a new sales order. Returns the created order record."""
    # Resolve customer
    customer_matches = [c for c in _db["customers"] if c["id"].upper() == customer_id.upper()]
    if not customer_matches:
        return {"error": f"Customer '{customer_id}' not found."}
    customer = customer_matches[0]

    # Parse line items
    try:
        raw_lines = json.loads(line_items_json)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid line_items_json: {exc}"}

    line_items = []
    subtotal = 0.0
    for line in raw_lines:
        item_matches = [i for i in _db["items"] if i["id"].upper() == str(line.get("item_id", "")).upper()]
        if not item_matches:
            return {"error": f"Item '{line.get('item_id')}' not found."}
        item = item_matches[0]
        qty = int(line.get("quantity", 0))
        price = float(line.get("unit_price_usd", item["unit_price_usd"]))
        amount = round(qty * price, 2)
        subtotal += amount
        line_items.append({
            "item_id": item["id"],
            "item_name": item["name"],
            "quantity": qty,
            "unit_price_usd": price,
            "amount_usd": amount,
        })

    subtotal = round(subtotal, 2)
    total = subtotal  # no tax/shipping calculated server-side

    # Generate new ID
    existing_ids = [int(r["id"].split("-")[1]) for r in _db["sales_orders"] if "-" in r["id"]]
    new_num = max(existing_ids, default=1000) + 1
    new_id = f"SO-{new_num}"

    order = {
        "id": new_id,
        "order_number": new_id,
        "customer_id": customer["id"],
        "customer_name": customer["name"],
        "status": "pending_approval",
        "created_date": str(date.today()),
        "ship_date": ship_date,
        "po_number": po_number,
        "line_items": line_items,
        "subtotal_usd": subtotal,
        "tax_usd": 0.00,
        "shipping_usd": 0.00,
        "total_usd": total,
        "shipping_method": shipping_method,
        "account_rep": account_rep,
        "memo": memo,
    }
    _db["sales_orders"].append(order)
    return order


@mcp.tool()
def update_sales_order(
    id: str = Field(description="Sales order ID to update, e.g. SO-1001"),
    status: Optional[str] = Field(default=None, description="New status: pending_approval | approved | partially_fulfilled | fulfilled | closed | cancelled"),
    ship_date: Optional[str] = Field(default=None, description="Updated ship date (ISO date)"),
    memo: Optional[str] = Field(default=None, description="Updated memo / notes"),
) -> dict:
    """Update an existing sales order's status, ship date, or memo. Returns updated record."""
    matches = [r for r in _db["sales_orders"] if r["id"].upper() == id.upper()]
    if not matches:
        return {"error": f"Sales order '{id}' not found."}
    order = matches[0]
    if status is not None:
        order["status"] = status
    if ship_date is not None:
        order["ship_date"] = ship_date
    if memo is not None:
        order["memo"] = memo
    return order


# ---------------------------------------------------------------------------
# Write — Invoices
# ---------------------------------------------------------------------------

@mcp.tool()
def create_invoice(
    sales_order_id: str = Field(description="Sales order ID to invoice, e.g. SO-1001"),
    memo: Optional[str] = Field(default=None, description="Invoice memo / notes"),
) -> dict:
    """Create an invoice from an existing sales order. Copies line items and customer. Returns new invoice."""
    so_matches = [r for r in _db["sales_orders"] if r["id"].upper() == sales_order_id.upper()]
    if not so_matches:
        return {"error": f"Sales order '{sales_order_id}' not found."}
    so = so_matches[0]

    existing_ids = [int(r["id"].split("-")[1]) for r in _db["invoices"] if "-" in r["id"]]
    new_num = max(existing_ids, default=2000) + 1
    new_id = f"INV-{new_num}"

    # Calculate due date based on customer payment terms (simple offset)
    customer_matches = [c for c in _db["customers"] if c["id"].upper() == so["customer_id"].upper()]
    terms_days = 30
    if customer_matches:
        terms = customer_matches[0].get("payment_terms", "Net30")
        if terms == "Net15":
            terms_days = 15
        elif terms == "Net60":
            terms_days = 60
        elif terms == "COD":
            terms_days = 0

    from datetime import timedelta
    today = date.today()
    due = today + timedelta(days=terms_days)

    invoice = {
        "id": new_id,
        "invoice_number": new_id,
        "customer_id": so["customer_id"],
        "customer_name": so["customer_name"],
        "sales_order_id": so["id"],
        "status": "open",
        "created_date": str(today),
        "due_date": str(due),
        "paid_date": None,
        "line_items": so.get("line_items", []),
        "subtotal_usd": so.get("subtotal_usd", 0.0),
        "tax_usd": so.get("tax_usd", 0.0),
        "total_usd": so.get("total_usd", 0.0),
        "amount_paid_usd": 0.00,
        "amount_due_usd": so.get("total_usd", 0.0),
        "payment_terms": customer_matches[0].get("payment_terms", "Net30") if customer_matches else "Net30",
        "memo": memo or f"Invoice for {so['id']}",
    }
    _db["invoices"].append(invoice)
    return invoice


@mcp.tool()
def update_invoice(
    id: str = Field(description="Invoice ID to update, e.g. INV-2001"),
    status: Optional[str] = Field(default=None, description="New status: open | partially_paid | paid | overdue"),
    amount_paid_usd: Optional[float] = Field(default=None, description="Total amount paid to date"),
    paid_date: Optional[str] = Field(default=None, description="Date payment was received (ISO date)"),
) -> dict:
    """Update an invoice's payment status, amount paid, or paid date. Returns updated record."""
    matches = [r for r in _db["invoices"] if r["id"].upper() == id.upper()]
    if not matches:
        return {"error": f"Invoice '{id}' not found."}
    invoice = matches[0]
    if status is not None:
        invoice["status"] = status
    if amount_paid_usd is not None:
        invoice["amount_paid_usd"] = round(amount_paid_usd, 2)
        invoice["amount_due_usd"] = round(invoice["total_usd"] - amount_paid_usd, 2)
    if paid_date is not None:
        invoice["paid_date"] = paid_date
    return invoice


# ---------------------------------------------------------------------------
# Write — Purchase Orders
# ---------------------------------------------------------------------------

@mcp.tool()
def create_purchase_order(
    vendor_id: str = Field(description="Vendor ID, e.g. V-001"),
    line_items_json: str = Field(description='JSON array of line items, e.g. [{"item_id":"I-101","quantity":1000,"unit_cost_usd":0.72}]'),
    expected_date: Optional[str] = Field(default=None, description="Expected delivery date (ISO date)"),
    memo: Optional[str] = Field(default=None, description="PO memo / notes"),
) -> dict:
    """Create a new purchase order for a vendor. Returns the created PO record."""
    vendor_matches = [v for v in _db["vendors"] if v["id"].upper() == vendor_id.upper()]
    if not vendor_matches:
        return {"error": f"Vendor '{vendor_id}' not found."}
    vendor = vendor_matches[0]

    try:
        raw_lines = json.loads(line_items_json)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid line_items_json: {exc}"}

    line_items = []
    total = 0.0
    for line in raw_lines:
        item_matches = [i for i in _db["items"] if i["id"].upper() == str(line.get("item_id", "")).upper()]
        if not item_matches:
            return {"error": f"Item '{line.get('item_id')}' not found."}
        item = item_matches[0]
        qty = int(line.get("quantity", 0))
        cost = float(line.get("unit_cost_usd", item["unit_cost_usd"]))
        amount = round(qty * cost, 2)
        total += amount
        line_items.append({
            "item_id": item["id"],
            "item_name": item["name"],
            "quantity": qty,
            "unit_cost_usd": cost,
            "amount_usd": amount,
        })

    total = round(total, 2)

    existing_ids = [int(r["id"].split("-")[1]) for r in _db["purchase_orders"] if "-" in r["id"]]
    new_num = max(existing_ids, default=3000) + 1
    new_id = f"PO-{new_num}"

    po = {
        "id": new_id,
        "po_number": new_id,
        "vendor_id": vendor["id"],
        "vendor_name": vendor["name"],
        "status": "open",
        "created_date": str(date.today()),
        "expected_date": expected_date,
        "line_items": line_items,
        "total_usd": total,
        "memo": memo,
    }
    _db["purchase_orders"].append(po)
    return po


@mcp.tool()
def update_purchase_order(
    id: str = Field(description="Purchase order ID to update, e.g. PO-3001"),
    status: Optional[str] = Field(default=None, description="New status: open | partially_received | received | closed"),
    memo: Optional[str] = Field(default=None, description="Updated memo / notes"),
) -> dict:
    """Update a purchase order's status or memo. Returns updated record."""
    matches = [r for r in _db["purchase_orders"] if r["id"].upper() == id.upper()]
    if not matches:
        return {"error": f"Purchase order '{id}' not found."}
    po = matches[0]
    if status is not None:
        po["status"] = status
    if memo is not None:
        po["memo"] = memo
    return po


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
