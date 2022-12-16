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

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


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


@app.get("/")
async def home(
        request: Request,
        response: Response,
        response_class=HTMLResponse,
        access_token: str = Depends(auth.get_access_token)):
    """
    The URL follows the format https://[tunnel_url]?shop=[dev_store].myshopify.com&host=[host],
    where [host] is the base64-encoded host parameter used by App Bridge,
    and represents the container the app is running in.
    (According to this guide: https://shopify.dev/apps/getting-started/create)
    """
    params = dict(request.query_params)
    shop = params["shop"]

    # only add this if not doing a redirect...
    response.headers["Content-Security-Policy"] = "frame-ancestors https://%s https://admin.shopify.com;" % shop

    return {"message": access_token}


@app.get("/auth/callback")
async def auth_callback(
        request: Request,
        response: Response):

    params = dict(request.query_params)
    shop = params["shop"]
    shopify.Session.setup(
        api_key=config.SHOPIFY_CLIENT_ID,
        secret=config.SHOPIFY_SECRET
    )
    session = shopify.Session(shop, config.API_VERSION)
    access_token = session.request_token(params)

    auth.save_shop_access_token(shop, access_token)

    return RedirectResponse("/?")
