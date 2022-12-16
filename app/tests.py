import binascii
import os

import shopify

from app import config



# https://github.com/Shopify/shopify_python_api


# TODO: change this when I have a proper app
redirect_uri = "https://66a3-47-144-146-221.ngrok.io/auth/callback"


shopify.Session.setup(api_key=config.SHOPIFY_CLIENT_ID, secret=config.SHOPIFY_SECRET)


shop = 're2-dev1'
shop_url = "%s.myshopify.com" % shop

api_version = '2022-07'
state = binascii.b2a_hex(os.urandom(15)).decode("utf-8")


scopes = ['read_products', 'read_orders']

session = shopify.Session(shop_url, api_version)
auth_url = session.create_permission_url(scopes, redirect_uri, state)

# redirect to auth_url

print(auth_url)

"""
"https://re2-dev1.myshopify.com/admin/apps/1d2e1e4cc907cad3c742235108d665be/auth/callback" \
"?" \
"code=4d8928b1d34837ecac8ecd45241e4eb7" \
"hmac=500ea7db0601e50cb7d847290ee762f3b48ec1c0ee9f1526a8748ebc4cbfa315" \
"host=cmUyLWRldjEubXlzaG9waWZ5LmNvbS9hZG1pbg" \
"shop=re2-dev1.myshopify.com" \
"state=0a7b24ff3d48befbe25daa11acb3f2" \
"timestamp=1671071916'

"""


