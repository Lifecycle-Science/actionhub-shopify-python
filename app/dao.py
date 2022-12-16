import boto3
from boto3.dynamodb.conditions import Key


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


