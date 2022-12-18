import base64
import binascii
import os
import shopify
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fastapi import Depends, HTTPException, Query, Header, BackgroundTasks
from starlette.status import HTTP_307_TEMPORARY_REDIRECT

from typing import Union

from app import config
from app import auth
from app import shops

from shopify import session_token


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
    shop = params["shop"]
    response.headers["Content-Security-Policy"] = "frame-ancestors https://%s https://admin.shopify.com;" % shop

    return templates.TemplateResponse(
        "main.html",{"request": request, "client_id": config.SHOPIFY_CLIENT_ID}
    )


@app.get("/test_client")
async def test_client(
        session: shopify.Session = Depends(auth.get_session_from_client_token)):
    shopify.ShopifyResource.activate_session(session)
    shop_name = session.url

    product = shopify.Product.find("8049048289594")  # Get a specific product

    print(product)
    return session.token


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
    params = dict(request.query_params)
    shop_name = params["shop"]
    host = params["host"]
    shopify.Session.setup(
        api_key=config.SHOPIFY_CLIENT_ID,
        secret=config.SHOPIFY_SECRET
    )
    session = shopify.Session(shop_name, config.API_VERSION)
    access_token = session.request_token(params)

    auth.save_shop_access_token(shop_name, access_token)

    # create the new shop program
    ix_shop = shops.IxShop.new(shop_name, shops.SCOPES_STAGE_1)
    try:
        ix_shop.add()
    except shops.Re2ProgramAlreadyExists:
        # TODO: implement app uninstall webhooks to clean out RE2 data
        return """
            The is already an RE2 program registered for this store.
            This could be the result of uninstalling and reinstalling the app.
            <b>To be implemented: app uninstall webhooks to clean up RE2 programs</b>
        """

    host_decoded = base64.b64decode(host + "===").decode("ascii")
    redirect_url = "https://%s/apps/%s/" % (host_decoded, config.SHOPIFY_CLIENT_ID)

    # Now that we have the token stored we will redirect
    # back to our embedded app main page to load the scaffolding
    return RedirectResponse(redirect_url)


@app.exception_handler(auth.EmbeddedAuthRedirectException)
async def embedded_auth_redirect_exception_handler(
        request: Request,
        exc: auth.EmbeddedAuthRedirectException):
    """
    We can't redirect to the auth page until we pop out of the Shopify iframe.
    *This exception is thrown by the auth.get_access_token process.*
    """
    query_params_in = dict(request.query_params)
    query_params_in.pop('embedded')

    # create the cleaned query string
    query_params_out = '&'.join([
        '%s=%s' % (key, value)
        for key, value in sorted(query_params_in.items())
    ])
    redirect_url = "https://" + request.url.hostname + "?" + query_params_out

    return templates.TemplateResponse(
        exc.redirect_to,
        {"request": request, "redirect_url": redirect_url, "client_id": config.SHOPIFY_CLIENT_ID}
    )
