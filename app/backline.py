"""
This listener here should be launched as a separate process
as an independent instance of this app. The purspose is to
execute the longer running processes outside of the API threads.

Same code base, two launch points:
1. main.py - starts the api listener
2. backine.py - starts the batch listener
"""

import json
import shopify

from app import programs
from app import dao
from app import auth
from app import config
from app import graphql_queries


def listenter():
    """
    Will listen to an SQS queue to trigger functions
    described here.
    """
    pass


def extract_shopify_events(shop_name):
    """
    Builds arrays of events and assets for the shop to
    add to RE2.
    """
    # TODO: needs some paging so we don't overload the RE2 server
    # TODO: needs some filtering so we only get what we need
    program_shopify = programs.ProgramShopify(shop_name)
    session = get_shop_session(shop_name)
    shopify.ShopifyResource.activate_session(session)

    assets = []
    products = shopify.Product.find()  # empty find gets all products
    for product in products:
        labels = []
        if product.tags:
            labels += product.tags

        if product.product_type:
            labels.append(product.product_type)

        if product.vendor:
            labels.append(product.vendor)

        assets.append({
            "asset_id": product.id,
            "asset_name": product.title,
            "labels": labels
        })

    events = []
    orders = shopify.Order.find()
    for order in orders:
        customer_id = order.customer.id
        created_at = order.created_at
        for item in order.line_items:
            product_id = item.product_id
            events.append({
                "user_id": str(customer_id),
                "event_timestamp": created_at,
                "event_type": "order",
                "asset_id": str(product_id)
            })

        query = graphql_queries.get_order_customer_journey_gql
        query = query.format(order_id=order.id)
        result = shopify.GraphQL().execute(
            query=query
        )
        r = json.loads(result)
        customer_journey = r["data"]["order"]["customerJourneySummary"]
        if customer_journey["firstVisit"]:
            first_lp = customer_journey["firstVisit"]["landingPage"]
            events.append({
                "user_id": str(customer_id),
                "event_timestamp": created_at,
                "event_type": "visit",
                "asset_id": first_lp
            })
        if customer_journey["lastVisit"]:
            last_lp = customer_journey["lastVisit"]["landingPage"]
            events.append({
                "user_id": str(customer_id),
                "event_timestamp": created_at,
                "event_type": "visit",
                "asset_id": last_lp
            })

    return {"events": events, "assets": assets}





def get_shop_session(shop_name):
    """
    Create an activated shopify session for calling the Shopify API
    """
    access_token, status = dao.get_shop_access_token(shop_name)
    if status != 200:
        raise auth.AccessTokenNotFound
    return shopify.Session(shop_name, config.API_VERSION, access_token)
