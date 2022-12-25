# Shopify App for integrating RE2

This app does not use the Shopify CLI, rather it relies heavily on https://github.com/Shopify/shopify_python_api

The backend uses FastAPI (https://github.com/tiangolo/fastapi)

The front end uses then environments (window) Shopify AppBridge with vanilla JavaScript.

Two event types: Orders and Views

## "Order" Event Types

Order events are obtained from Shopify via the `orders = shopify.Order.find()` method.
At this time the Shopify order instance does not contain any values to be used as labels. 
The mappings are below:

| RE2 Event Field | Shopify Order Field |
| --- | --- |
| `user_id` | `order.customer_id` |
| `event_timestamp` | `order.created_at` |
| `event_type` | "order" |
| `asset_id` | `order.product_id` |
| `labels` | `[]` |


## View Event Types


Events are created from page views views and orders.
