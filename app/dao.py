import boto3
import psycopg2
import psycopg2.extras
from psycopg2 import sql

from boto3.dynamodb.conditions import Key

from app import config


def get_db_connection(program_id=""):

    host = config.AWS_AURORA_DB_HOST
    username = config.AWS_AURORA_DB_USERNAME
    password = config.AWS_AURORA_DB_PASSWORD

    options = "-c search_path=re2_ix_shopify"
    conn = psycopg2.connect(
        "dbname='re2' user='" + username + "' host='" + host + "' password='" + password + "' options='" + options + "'"
    )
    return conn


def select_shop(shop_name):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        select shop_name, 
            ts_added, ts_updated,
            re2_program_id, re2_api_key,
            permissions
        from re2_ix_shopify.dim_shops 
        where shop_name = %s
    """, [shop_name, ])
    row = cur.fetchone()
    conn.close()
    return row


def get_shop_access_token(shop: str):
    """Retrieve the store's access_token.
    Will return 404 if token not found.

    :param shop: str | the partition key
    :return: (str, int) | access_token, status
    """
    ddb = boto3.resource('dynamodb', region_name='us-west-2')
    table = ddb.Table('shopify_re2_shop_tokens')

    results = table.query(
        KeyConditionExpression=Key('shop').eq(shop)
    )
    try:
        return results["Items"][0]["access_token"], 200
    except IndexError:
        return "Shop not found", 404


def put_shop_access_token(shop: str, access_token: str):
    """Save the store's access_token

    :param shop: str | the partition key
    :param access_token: str
    :return:
    """
    ddb = boto3.resource('dynamodb', region_name='us-west-2')
    table = ddb.Table('shopify_re2_shop_tokens')

    result = table.update_item(
        Key={"shop": shop},
        UpdateExpression="set access_token = :val",
        ExpressionAttributeValues={":val": access_token},
        ReturnValues="UPDATED_NEW"
    )
    return result["Attributes"], 200


