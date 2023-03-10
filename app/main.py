import base64
import json
from urllib.parse import parse_qs
from fastapi import FastAPI, Request, Response
from fastapi import Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import shopify

from app import config
from app import auth
from app import programs
from app import graphql_queries
from app import models


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/",
         dependencies=[Depends(auth.verify_shop_access)])
async def home(
        request: Request,
        response: Response):
    """
    This method just delivers the scaffolding for the rest of the app which is called
    from the client using the authenticated app-bridge. It also will kick off the app
    approval oauth flow via the "verify_shop_access" dependency.

    The calling uri follows the format:
    https://[tunnel_url]?shop=[dev_store].myshopify.com&host=[host],
    where [host] is the base64-encoded host parameter used by App Bridge,
    and represents the container the app is running in.
    (According to this guide: https://shopify.dev/apps/getting-started/create)
    """
    params = dict(request.query_params)
    hmac = params["hmac"]
    shop = params["shop"]
    response.headers["Content-Security-Policy"] = "frame-ancestors https://%s https://admin.shopify.com;" % shop

    return templates.TemplateResponse(
        "main.html",{
            "request": request,
            "client_id": config.SHOPIFY_CLIENT_ID,
            "hmac": hmac}
    )


@app.get('/program')
async def get_program(
        request: Request,
        session: shopify.Session = Depends(auth.get_session_from_client_token)):
    """
    Return the HTML with program details
    """
    shopify.ShopifyResource.activate_session(session)
    shop_name = session.url
    program_shopify = programs.ProgramShopify(shop_name)
    program_shopify.load()
    template_file = "re2_program_details.html"
    return templates.TemplateResponse(
        template_file, {"request": request, "program_shopify": program_shopify}
    )


@app.put('/program')
async def put_program(
        program: models.ProgramConfiguration,
        session: shopify.Session = Depends(auth.get_session_from_client_token)):
    """
    Return the HTML with program details
    """
    # TODO: add some error handling
    shopify.ShopifyResource.activate_session(session)
    shop_name = session.url
    program_shopify = programs.ProgramShopify(shop_name)
    program_shopify.load()
    program_shopify.high_engagement_threshold = program.high_engagement_threshold
    program_shopify.event_relevance_decay = program.event_relevance_decay
    program_shopify.action_weight_floor = program.action_weight_floor
    program_shopify.save()
    return {"status": "success"}


@app.put("/product/assets")
async def refresh_product_assets(
        request: Request,
        session: shopify.Session = Depends(auth.get_session_from_client_token)):
    """
    Update the ActionHub assets with the latest products
    """
    shopify.ShopifyResource.activate_session(session)
    shop_name = session.url

    program_shopify = programs.use_program(shop_name)
    #if "read_product_listings" not in program_shopify.permissions:
       # auth.send_request_permission_redirect(request, "read_product_listings")

    pass


# TODO: turn this into the "populate actionhub method"
@app.get("/test_client")
async def test_client(
        session: shopify.Session = Depends(auth.get_session_from_client_token)):
    shopify.ShopifyResource.activate_session(session)
    # do something here...
    shop_name = session.url

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
    print(orders)
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
        print(order.customer.id)

    return {"assets": assets, "events": events}


# -------------------------------------------------------------
# JAVASCRIPT PROTECTION
# -------------------------------------------------------------


@app.get("/js/config.js")
async def js_config(
        hmac: str,
        request: Request,):
    try:
        referer = request.headers["referer"]
    except KeyError:
        return {"config": ""}

    referer_hmac = parse_qs(referer)["hmac"][0]
    if referer_hmac != hmac:
        return "invalid session"

    return templates.TemplateResponse(
        "config.js", {"request": request, "client_id": config.SHOPIFY_CLIENT_ID}
    )


# -------------------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------------------


@app.get("/auth/callback")
async def auth_callback(
        request: Request):
    """
    This is destination of the post-approval redirect from Shopify.
    This function will obtain the access key from Shopify and
    save it on our end for future use.

    For this call the shop was just approved the installation.
    """
    query_params = dict(request.query_params)
    shop_name = query_params["shop"]
    shopify.Session.setup(
        api_key=config.SHOPIFY_CLIENT_ID,
        secret=config.SHOPIFY_SECRET
    )
    session = shopify.Session(shop_name, config.API_VERSION)
    access_token = session.request_token(query_params)
    scopes = str(session.access_scopes).split(',')

    program_shopify = programs.ProgramShopify(shop_name)
    try:
        program_shopify.load()
        auth.save_shop_access_token(
            shop_name,
            access_token,
            scopes)
    except programs.Re2ShopNotFound:
        program_shopify = programs.ProgramShopify.new(shop_name, scopes)
        program_shopify.add()

    # Now that we have the token stored we will redirect
    # back to our embedded app main page to load the scaffolding
    return RedirectResponse(shopify_app_url(query_params))


@app.exception_handler(auth.EmbeddedAuthRedirectException)
async def embedded_auth_redirect_exception_handler(
        request: Request,
        exc: auth.EmbeddedAuthRedirectException):
    """
    We can't redirect to the auth page until we pop out of the Shopify iframe.
    *This exception is thrown by the auth.get_access_token process.*
    """
    redirect_url = disembedded_app_url(request, resource="/")
    print("redirect_url", redirect_url)
    return templates.TemplateResponse(
        exc.redirect_to,
        {"request": request, "redirect_url": redirect_url, "client_id": config.SHOPIFY_CLIENT_ID}
    )


@app.get("/scope/read_product_listings", dependencies=[Depends(auth.verify_shop_access)])
async def home(request: Request):
    """If we're here then we have permission, return to home
    """
    return RedirectResponse(shopify_app_url(dict(request.query_params)))


# -------------------------------------------------------------
# UTILS
# -------------------------------------------------------------


def send_request_permission_redirect(request: Request, scope):
    resource = "/scope/" + scope
    # redirect_url = disembedded_app_url(request, resource=resource)
    return {"request_scope": True, "request_scope_resource": resource}


def shopify_app_url(query_params):
    """Returns the top window url that is the shopify app wrapper,
    which loads the app in its iframe.
    """
    host = query_params["host"]
    host_decoded = base64.b64decode(host + "===").decode("ascii")
    return "https://%s/apps/%s/" % (host_decoded, config.SHOPIFY_CLIENT_ID)


def disembedded_app_url(request, resource="/"):
    """Returns the ActionHub url without the "embedded" flag so can
    do an auth redirect if necessary.
    """
    query_params_in = dict(request.query_params)
    query_params_in.pop('embedded')

    # create the cleaned query string
    query_params_out = '&'.join([
        '%s=%s' % (key, value)
        for key, value in sorted(query_params_in.items())
    ])
    return "https://" + request.url.hostname + resource + "?" + query_params_out

