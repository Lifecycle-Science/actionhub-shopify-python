# Shopify App for integrating ActionHub

## Overview

This app does not use the Shopify CLI, rather it relies heavily on https://github.com/Shopify/shopify_python_api. The backend uses FastAPI (https://github.com/tiangolo/fastapi). The front end uses the Shopify AppBridge form the window object (`window["app-bridge"]`) with vanilla JavaScript.

## How Shopify Data is Used In ActionHub

### Event Types

**ActionHub does not read (or store) any Shopify or merchant customer data except customer_id, order related data, and the metafields created by ActionHub to store recommended actions. No personal or contact information is used.**

The Shopify app reports two kinds of events: "orders" and "views"

#### "Order" Event Types

Order events are obtained from Shopify via the `orders = shopify.Order.find()` method.
At this time the Shopify order instance does not contain any values to be used as labels. 
The "order" event mappings are below:

| ActionHub Event Field | Shopify Order Field |
| --- | --- |
| `user_id` | `order.customer_id` |
| `event_timestamp` | `order.created_at` |
| `event_type` | "order" |
| `asset_id` | `order.product_id` |
| `labels` | `[]` |


#### View Event Types

View events are obtained from `customerJourneySummary` data contained in the `order` object.
Specifically, the first and last landing page visits are recorded as "view" events.
These two visits are referenced `customerVisit` objecs from either the `customer_journey["firstVisit"]` or
`customer_journey["lastVisit"]` values. The "view" event mappings are below:

| ActionHub Event Field | Shopify Order Field |
| --- | --- |
| `user_id` | `order.customer_id` |
| `event_timestamp` |  `customerVisit["occurredAt"]` |
| `event_type` | "visit" |
| `asset_id` | `customerVisit["landingPage"]` |
| `labels` | `[]` |
