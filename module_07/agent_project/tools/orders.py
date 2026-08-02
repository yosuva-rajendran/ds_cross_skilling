import sqlite3

_conn = sqlite3.connect(":memory:", check_same_thread=False)
_conn.execute("CREATE TABLE customers (id TEXT PRIMARY KEY, name TEXT, email TEXT)")
_conn.execute("CREATE TABLE orders (id TEXT PRIMARY KEY, customer_id TEXT, status TEXT, total REAL)")
_conn.executemany(
    "INSERT INTO customers VALUES (?, ?, ?)",
    [
        ("cust_001", "Alex Rivera", "alex@example.com"),
        ("cust_002", "Priya Nair", "priya@example.com"),
    ],
)
_conn.executemany(
    "INSERT INTO orders VALUES (?, ?, ?, ?)",
    [
        ("ORD-1001", "cust_001", "delivered", 89.99),
        ("ORD-1002", "cust_002", "pending", 45.50),
        ("ORD-1003", "cust_002", "shipped", 120.00),
    ],
)
_conn.commit()

SEARCH_CUSTOMER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_customer",
        "description": (
            "Look up a customer by name and return their customer_id. Use this "
            "before get_orders if you only have a name, not an ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Customer's full or partial name"}},
            "required": ["name"],
        },
    },
}

GET_ORDERS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_orders",
        "description": (
            "Get orders for a customer_id, optionally filtered by status. "
            "Read-only. Get customer_id from search_customer first if needed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "shipped", "delivered", "cancelled"],
                },
                "limit": {"type": "integer", "default": 20, "maximum": 100},
            },
            "required": ["customer_id"],
        },
    },
}

DELETE_ORDER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "delete_order",
        "description": (
            "Permanently delete an order by ID. Irreversible -- only use this "
            "when the user has explicitly confirmed the deletion."
        ),
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
}


def search_customer(name: str):
    rows = _conn.execute(
        "SELECT id, name, email FROM customers WHERE name LIKE ?", (f"%{name}%",)
    ).fetchall()
    if not rows:
        raise ValueError(f"No customer found matching '{name}'")
    return {"matches": [{"customer_id": r[0], "name": r[1], "email": r[2]} for r in rows]}


def get_orders(customer_id: str, status: str = None, limit: int = 20):
    limit = min(limit, 100)
    sql = "SELECT id, status, total FROM orders WHERE customer_id = ?"
    params = [customer_id]
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " LIMIT ?"
    params.append(limit)

    rows = _conn.execute(sql, params).fetchall()
    return {
        "customer_id": customer_id,
        "orders": [{"order_id": r[0], "status": r[1], "total": r[2]} for r in rows],
    }


def delete_order(order_id: str):
    cur = _conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    _conn.commit()
    if cur.rowcount == 0:
        raise ValueError(f"No order found with id '{order_id}'")
    return {"status": "deleted", "order_id": order_id}
