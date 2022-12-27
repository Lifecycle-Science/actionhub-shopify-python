"""
This listener here should be launched as a separate process
as an independent instance of this app. The purpose is to
execute the longer running processes outside of the API threads.

Same code base, two launch points:
1. main.py - starts the api listener
2. backine.py - starts the batch listener
"""

import json

from pyactiveresource import connection
import shopify

from app import programs
from app import dao
from app import auth
from app import config
from app import graphql_queries


shop_tokens = {}


# TODO: web hook listener
# TODO: internal SQS listener


def listenter():
    """
    Will listen to an SQS queue to trigger functions
    described here.
    """
    shop_name = "re2-dev1.myshopify.com"

    onboard_new_shop = True
    load_segments = False

    if onboard_new_shop:
        create_shopify_metafield_defs(shop_name)
        extract_shopify_events(shop_name)
        # start_initial_action_processing(shop_name)

    if load_segments:
        pass

    pass


def extract_shopify_events(shop_name):
    """
    Builds arrays of events and assets for the shop to
    add to RE2.
    """
    # TODO: needs some paging so we don't overload the RE2 server
    # TODO: needs some filtering so we only get what we need
    program_shopify = programs.ProgramShopify(shop_name)
    program_shopify.load()

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
                "asset_id": str(product_id),
                "labels": []
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
                "event_timestamp": customer_journey["firstVisit"]["occurredAt"],
                "event_type": "visit",
                "asset_id": first_lp,
                "labels": []
            })
        if customer_journey["lastVisit"]:
            last_lp = customer_journey["lastVisit"]["landingPage"]
            events.append({
                "user_id": str(customer_id),
                "event_timestamp": customer_journey["lastVisit"]["occurredAt"],
                "event_type": "visit",
                "asset_id": last_lp,
                "labels": []
            })

    program_shopify.add_events(events)

    return {"events": events, "assets": assets}


def update_customer_metafield(shop_name):
    session = get_shop_session(shop_name)
    shopify.ShopifyResource.activate_session(session)


    # metafield =
    # shopify.Customer.metafields(metafield).save()


    # TODO: create a metafield type "list.single_line_text_field" when creating shop
    # https://shopify.dev/api/admin-rest/2022-10/resources/metafield#post-metafields
    # https://shopify.dev/apps/metafields/types#list-types

    # customer = shopify.Customer.find(6724705681722)
    # customer.add_metafield(shopify.Metafield({
    #     'key': 'test_key',
    #     'value': 'test_value,test_value2',
    #     'value_type': 'list.single_line_text_field',
    #     'namespace': 're2'})
    # )
    # customer.save()

    # print(customer.metafields)
    #
    # customer.metafields = [{
    #     "key": "re2-action",
    #     "value": "newvalue",
    #     "type": "text",
    #     "namespace": "custom"
    #     }]
    # customer.save()
    # print(customer.metafields)


def create_shopify_metafield_defs(shop_name):
    """
    Creates the customer metafields which will contain the RE2 outputs
    """
    session = get_shop_session(shop_name)
    shopify.ShopifyResource.activate_session(session)

    query = graphql_queries.create_customer_metafield_gql
    result = shopify.GraphQL().execute(
        query=query,
        variables={"definition": {
            "name": "RE2 Order Actions",
            "namespace": "re2",
            "key": "order_actions",
            "description": "[DO NOT EDIT - required for RE2] A list of recommended product order actions.",
            "type": "list.single_line_text_field",
            "ownerType": "CUSTOMER"
        }}
    )
    print(result)
    result = shopify.GraphQL().execute(
        query=query,
        variables={"definition": {
            "name": "RE2 Landing Page Actions",
            "namespace": "re2",
            "key": "landing_page_actions",
            "description": "[DO NOT EDIT - required for RE2] A list of recommended landing page view actions.",
            "type": "list.single_line_text_field",
            "ownerType": "CUSTOMER"
        }}
    )
    print(result)
    result = shopify.GraphQL().execute(
        query=query,
        variables={"definition": {
            "name": "RE2 Label Preferences",
            "namespace": "re2",
            "key": "label_preferences",
            "description": "[DO NOT EDIT - required for RE2] A list of preferred labels.",
            "type": "list.single_line_text_field",
            "ownerType": "CUSTOMER"
        }}
    )
    print(result)


def get_shop_session(shop_name):
    """
    Create an activated shopify session for calling the Shopify API
    """
    if shop_name not in shop_tokens:
        access_token, status = dao.get_shop_access_token(shop_name)
        if status != 200:
            raise auth.AccessTokenNotFound
        shop_tokens[shop_name] = access_token

    return shopify.Session(shop_name, config.API_VERSION, shop_tokens[shop_name])
