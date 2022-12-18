from app import config_local

# AWS credentials
AWS_AURORA_DB_USERNAME = config_local.AWS_AURORA_DB_USERNAME
AWS_AURORA_DB_PASSWORD = config_local.AWS_AURORA_DB_PASSWORD
AWS_AURORA_DB_HOST = config_local.AWS_AURORA_DB_HOST

# Shopify credentials
SHOPIFY_CLIENT_ID = config_local.SHOPIFY_CLIENT_ID
SHOPIFY_SECRET = config_local.SHOPIFY_SECRET
AUTH_CALLBACK_URL = config_local.AUTH_CALLBACK_URL
API_VERSION = "2022-07"

# RE2 credentials
RE2_API_KEY = config_local.RE2_API_KEY
RE2_API_PROGRAM = config_local.RE2_API_PROGRAM
