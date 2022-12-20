import json
import time
import datetime
import requests
from app import dao
from app import config


SCOPES_STAGE_1 = ['read_products', 'read_orders']

shops = {}


def use_shop(shop_name):
    """
    Keeps in memory collection of shops for easy access.
    """
    if shop_name not in shops:
        re2shop = Re2Shop(shop_name)
        re2shop.load()
        shops[shop_name] = re2shop
    return shops[shop_name]


class ShopNotFound(Exception):
    pass


class SlopAlreadyExists(Exception):
    pass


class Re2ProgramAlreadyExists(Exception):
    pass


class Re2Shop:

    ts_added: int = 0
    ts_updated: int = 0
    re2_program_id: str = ""
    re2_api_key: str = ""
    permissions: [str] = []
    loaded: bool = False

    def __init__(self, shop_name):
        self.shop_name = shop_name

    def load(self):
        shop = dao.select_shop(self.shop_name)
        if shop:
            self.ts_added = shop["ts_added"]
            self.ts_updated = shop["ts_updated"]
            self.re2_program_id = shop["re2_program_id"]
            self.re2_api_key = shop["re2_api_key"]
            self.permissions = shop["permissions"]
            self.loaded = True
        else:
            raise ShopNotFound

    @classmethod
    def new(cls,
            shop_name,
            permissions):

        # TODO: add some validation
        cls.shop_name = shop_name
        cls.permissions = permissions
        cls.ts_added = int(time.mktime(datetime.datetime.now().timetuple()))
        cls.ts_updated = int(time.mktime(datetime.datetime.now().timetuple()))
        return cls(shop_name)

    def add_scope(self, scope):
        self.permissions.append(scope)
        dao.update_ix_shop_permission(self.shop_name, self.permissions)

    def add(self):
        if self.loaded:
            raise SlopAlreadyExists

        # create the RE2 program
        # same as the shop. i.e. one shop = one program

        # host = "https://api.re2.live"
        host = "http://localhost:8000"
        resource = "/programs"
        body = {
            "program_name": self.shop_name,
            "description": "Shopify shot: " + self.shop_name
        }
        headers = {
            "access_token": config.RE2_API_KEY,
            "program-id": config.RE2_API_PROGRAM
        }
        uri = host + resource
        r = requests.post(uri, data=json.dumps(body), headers=headers)
        if r.status_code == 401:
            raise Re2ProgramAlreadyExists

        program = json.loads(r.text)

        self.re2_program_id = program["program_id"]
        self.re2_api_key = program["api_key"]

        dao.create_ix_shop(
            shop_name=self.shop_name,
            re2_program_id=self.re2_program_id,
            re2_api_key=self.re2_api_key,
            permissions=self.permissions
        )
        pass
