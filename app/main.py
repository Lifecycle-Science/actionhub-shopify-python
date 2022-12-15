import binascii
import os
import shopify
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi import Depends, HTTPException, Query, Header, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from typing import Union

from app import config

app = FastAPI()


@app.get("/")
def read_root(
        hmac: Union[str, None] = None,
        host: Union[str, None] = None,
        shop: Union[str, None] = None
):
    """
    The URL follows the format https://[tunnel_url]?shop=[dev_store].myshopify.com&host=[host],
    where [host] is the base64-encoded host parameter used by App Bridge,
    and represents the container the app is running in.
    (According to this guide: https://shopify.dev/apps/getting-started/create)
    """

    if shop:
        # create the session
        shopify.Session.setup(
            api_key=config.SHOPIFY_CLIENT_ID,
            secret=config.SHOPIFY_SECRET
        )
        session = shopify.Session(shop, config.API_VERSION)

        # get the authorization url
        scopes = ['read_products', 'read_orders']
        state = binascii.b2a_hex(os.urandom(15)).decode("utf-8")
        auth_url = session.create_permission_url(scopes, config.AUTH_CALLBACK_URL, state)

        # return {"url":auth_url}
        # return RedirectResponse(auth_url)


    else:
        return {"message": "no shop"}


@app.get("/auth/callback")
def auth_callback(
        code: Union[str, None] = None,
        hmac: Union[str, None] = None,
        host: Union[str, None] = None,
        shop: Union[str, None] = None,
        state: Union[str, None] = None,
        timestamp: Union[str, None] = None
    ):
    params = {
        'code': code,
        'hmac': hmac,
        'host': host,
        'shop': shop,
        'state': state,
        'timestamp': timestamp
    }
    shopify.Session.setup(
        api_key=config.SHOPIFY_CLIENT_ID,
        secret=config.SHOPIFY_SECRET
    )
    session = shopify.Session(shop, config.API_VERSION)
    # return params
    access_token = session.request_token(params)

    # save access_token with shop_url
    # we can redirect and start calling the apis now

    return {"access_token": access_token}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}