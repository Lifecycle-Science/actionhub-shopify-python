import time
import datetime
from app import dao


class ShopNotFound(Exception):
    pass


class SlopAlreadyExists(Exception):
    pass


class Shop:

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
            self.ts_updated = shop["ts_updates"]
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

    def add(self):
        if self.loaded:
            raise SlopAlreadyExists


        dao.create_shop(
            shop_name=self.shop_name,
            re2_program_id=self.re2_program_id,
            re2_api_key=self.re2_api_key,
            permissions=self.permissions,
            ts_added=self.ts_added,
            ts_updated=self.ts_updated
        )
        pass
