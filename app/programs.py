import json
import time
import datetime
import requests
from app import dao
from app import config


SCOPES_STAGE_1 = ['read_products', 'read_orders']

programs = {}


def use_program(shop_name):
    """
    Keeps in memory collection of shops for easy access.
    """
    if shop_name not in programs:
        program_shopify = ProgramShopify(shop_name)
        program_shopify.load()
        programs[shop_name] = program_shopify
    return programs[shop_name]


class ProgramShopify:

    ts_added: int = 0
    ts_updated: int = 0
    program_id: str = ""
    re2_api_key: str = ""
    permissions: [str] = []

    high_engagement_threshold: int = 0
    event_relevance_decay: int = 0
    action_weight_floor: float = 0
    program_name: str = ""
    description: str = ""

    loaded: bool = False

    def __init__(self, shop_name):
        self.shop_name = shop_name

    def load(self):
        """
        Get the app shop details, and the get the program details
        """
        shop = dao.select_shop(self.shop_name)
        if shop:
            self.ts_added = shop["ts_added"]
            self.ts_updated = shop["ts_updated"]
            self.program_id = shop["program_id"]
            self.re2_api_key = shop["re2_api_key"]
            self.permissions = shop["permissions"]
        else:
            raise Re2ShopNotFound

        r = requests.get(
            url=config.RE2_API_HOST + "/program",
            headers=self._api_headers())

        if r.status_code == 404:
            raise Re2ProgramNotFound

        program = json.loads(r.text)
        self.high_engagement_threshold = program["high_engagement_threshold"]
        self.event_relevance_decay = program["event_relevance_decay"]
        self.action_weight_floor = program["action_weight_floor"]
        self.program_name = program["program_name"]
        self.description = program["description"]
        self.loaded = True

    def add_events(self, events: [dict]):
        """
        Sends array of events to the RE2 API for inserts
        """
        if not self.loaded:
            raise Re2ShopNotLoaded

        r = requests.put(
            url=config.RE2_API_HOST + "/events",
            data=json.dumps(events),
            headers=self._api_headers())
        print(r.text)

    def update_assets(self, assets: [dict]):
        """
        Sends array of assets to the RE2 API for upsert.
        """
        if not self.loaded:
            raise Re2ShopNotLoaded

        r = requests.put(
            url=config.RE2_API_HOST + "/events",
            data=json.dumps(assets),
            headers=self._api_headers())
        print(r.text)

    def save(self):
        if not self.loaded:
            raise Re2ShopNotLoaded

        body = {
            "program_id": self.program_id,
            "program_name": self.program_name,
            "high_engagement_threshold": self.high_engagement_threshold,
            "event_relevance_decay":  self.event_relevance_decay,
            "action_weight_floor": self.action_weight_floor
        }
        r = requests.put(
            url=config.RE2_API_HOST + "/program",
            data=json.dumps(body),
            headers=self._api_headers())
        print(r.text)

    def add_shopify_scope(self, scope):
        """
        Add/save new scope to the permission.
        This should only happen after we've gotten merchant permission
        """
        self.permissions.append(scope)
        dao.update_ix_shop_permission(self.shop_name, self.permissions)

    @classmethod
    def new(cls,
            shop_name,
            permissions):
        """
        Return a class containing the start of a new shop.
        The data will not be saved until calling the .add() method.
        """
        # TODO: add some validation
        cls.shop_name = shop_name
        cls.permissions = permissions
        cls.ts_added = int(time.mktime(datetime.datetime.now().timetuple()))
        cls.ts_updated = int(time.mktime(datetime.datetime.now().timetuple()))
        return cls(shop_name)

    def add(self):
        """
        Create the RE2 program (same as the shop. i.e. one shop = one program)
        """
        if self.loaded:
            raise Re2ShopAlreadyExists

        body = {
            "program_name": self.shop_name,
            "description":  self.shop_name  # TODO: think of something better
        }
        r = requests.post(
            url=config.RE2_API_HOST + "/programs",
            data=json.dumps(body),
            headers=config.RE2_ADMIN_API_HEADERS)

        if r.status_code == 401:
            raise Re2ProgramAlreadyExists

        program = json.loads(r.text)

        self.program_id = program["program_id"]
        self.re2_api_key = program["api_key"]

        dao.create_ix_shop(
            shop_name=self.shop_name,
            program_id=self.program_id,
            re2_api_key=self.re2_api_key,
            permissions=self.permissions
        )
        pass

    def _api_headers(self):
        """
        Returns headers for calls to the RE2 api
        (Does not include initial admin api call.
        """
        return {
            "access_token": self.re2_api_key,
            "program-id": self.program_id,
            "Content-Type": "application/json"
        }


class Re2ShopNotFound(Exception):
    pass


class Re2ShopNotLoaded(Exception):
    pass


class Re2ShopAlreadyExists(Exception):
    pass


class Re2ProgramNotFound(Exception):
    pass


class Re2ProgramAlreadyExists(Exception):
    pass

