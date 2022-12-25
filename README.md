# Shopify App for integrating RE2

This app does not use the Shopify CLI, rather it relies heavily on https://github.com/Shopify/shopify_python_api

The backend uses FastAPI (https://github.com/tiangolo/fastapi)

The front end uses then environments (window) Shopify AppBridge with vanilla JavaScript.

Two event types: Orders and Views

## Order Event Types
`orders = shopify.Order.find()`

| RE2 Event Field | Shopify Order Field |
| --- | --- |
| `user_id` | `order.customer_id` |


## View Event Types


Events are created from page views views and orders.
