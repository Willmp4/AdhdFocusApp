import boto3
import json
from botocore.exceptions import NoCredentialsError

def get_database_uri():
    secret_name = "rds!db-97cf747e-4207-4529-bd7f-10aceba9e397"
    region_name = "eu-west-2"
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        if 'username' in secret_dict and 'password' in secret_dict:
            return f"postgresql://{secret_dict['username']}:{secret_dict['password']}@localhost/"
    except NoCredentialsError:
        print("Credentials not available")
    return 'sqlite:///default.db'
