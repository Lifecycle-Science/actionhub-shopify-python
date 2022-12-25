# Shopify App for integrating RE2

## Overview

This app does not use the Shopify CLI, rather it relies heavily on https://github.com/Shopify/shopify_python_api. The backend uses FastAPI (https://github.com/tiangolo/fastapi). The front end uses then environments (window) Shopify AppBridge with vanilla JavaScript.

## Event Types

The Shopify app reports two kinds of events: "orders" and "views"

### "Order" Event Types

Order events are obtained from Shopify via the `orders = shopify.Order.find()` method.
At this time the Shopify order instance does not contain any values to be used as labels. 
The "order" event mappings are below:

| RE2 Event Field | Shopify Order Field |
| --- | --- |
| `user_id` | `order.customer_id` |
| `event_timestamp` | `order.created_at` |
| `event_type` | "order" |
| `asset_id` | `order.product_id` |
| `labels` | `[]` |


### View Event Types

View events are obtained from `customerJourneySummary` data contained in the `order` object.
Specifically, the first and last landing pages are recorded as "view" events.
The "view" event mappings are below:

| RE2 Event Field | Shopify Order Field |
| --- | --- |
| `user_id` | `order.customer_id` |
| `event_timestamp` | `order.created_at` |
| `event_type` | "visit" |
| `asset_id` | `customer_journey["firstVisit"]["landingPage"]` or `customer_journey["lastVisit"]["landingPage"]` |
| `labels` | `[]` |
