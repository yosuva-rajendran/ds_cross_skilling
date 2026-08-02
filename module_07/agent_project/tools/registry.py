from . import calculator, orders, weather, web_search

_REGISTRY = {
    "calculate": {"schema": calculator.SCHEMA, "execute": calculator.execute},
    "get_weather": {"schema": weather.SCHEMA, "execute": weather.execute},
    "web_search": {"schema": web_search.SCHEMA, "execute": web_search.execute},
    "search_customer": {"schema": orders.SEARCH_CUSTOMER_SCHEMA, "execute": orders.search_customer},
    "get_orders": {"schema": orders.GET_ORDERS_SCHEMA, "execute": orders.get_orders},
    "delete_order": {"schema": orders.DELETE_ORDER_SCHEMA, "execute": orders.delete_order},
}


def get_tools():
    return [entry["schema"] for entry in _REGISTRY.values()]


def get_executor(name):
    return _REGISTRY[name]["execute"] if name in _REGISTRY else None
