import binascii
import hashlib
import hmac
import os

from fastapi import Request, Response, HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST
from starlette.status import HTTP_307_TEMPORARY_REDIRECT, HTTP_205_RESET_CONTENT

import shopify

from app import config
from app import dao

# https://shopify.dev/apps/auth/oauth/getting-started

shop_access_tokens = {}


class EmbeddedAuthRedirectException(Exception):
    """We can't redirect to the auth page
    until we pop out of the Shopify iframe.
    The exception handler is in the main module.
    """
    def __init__(self):
        self.redirect_to = "exit_frame.html"


def get_access_token(request: Request):
    query_params = dict(request.query_params)

    try:
        shop = query_params["shop"]
    except KeyError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="could not find shop"
        )

    try:
        access_token = shop_access_tokens[shop]
        return access_token
    except KeyError:
        access_token, status = dao.get_shop_access_token(shop)

    if status == 404:
        if "embedded" in query_params and query_params["embedded"] == "1":
            # client redirect to same url process
            raise EmbeddedAuthRedirectException

        else:
            # install request needs hmac verification
            verify_hmac(query_params)

            # not embedded so create the auth url and do the redirect
            shopify.Session.setup(
                api_key=config.SHOPIFY_CLIENT_ID,
                secret=config.SHOPIFY_SECRET
            )
            session = shopify.Session(shop, config.API_VERSION)

            # get the authorization url
            scopes = ['read_products', 'read_orders']
            state = binascii.b2a_hex(os.urandom(15)).decode("utf-8")
            auth_url = session.create_permission_url(scopes, config.AUTH_CALLBACK_URL, state)

            raise HTTPException(
                status_code=HTTP_307_TEMPORARY_REDIRECT,
                headers={'Location':auth_url}
            )

    else:
        return access_token


def save_shop_access_token(shop, access_token):
    """Pass through function so we don't have direct dao access in the main function

    :param shop:
    :param access_token:
    :return:
    """
    global tokens
    shop_access_tokens[shop] = access_token
    dao.put_shop_access_token(shop, access_token)


def verify_hmac(query_params: dict):
    """Verifies hmac value as part of the oath process.
    Documented here:
    https://shopify.dev/apps/auth/oauth/getting-started#step-2-verify-the-installation-request
    """
    hmac_value_received = query_params.pop('hmac')

    if hmac_value_received:
        # create the cleaned query string
        cleaned_query = '&'.join([
            '%s=%s' % (key, value)
            for key, value in sorted(query_params.items())
        ])

        # get hmac value to compare
        hmac_value_created = hmac.new(
            config.SHOPIFY_SECRET.encode("utf8"),
            msg=cleaned_query.encode("utf8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Compare digests
        if not hmac.compare_digest(hmac_value_created, hmac_value_received):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="hmac could not be verified"
            )

