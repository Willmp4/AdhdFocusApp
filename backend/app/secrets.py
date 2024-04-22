import boto3
import json
from botocore.exceptions import NoCredentialsError, ClientError

def get_database_uri():

    host = 'focus-app-users.cfa9q7ilvqdl.eu-west-2.rds.amazonaws.com'
    dbname = 'focus-app-users'
    secret_name = "rds!db-97cf747e-4207-4529-bd7f-10aceba9e397"  # Ensure correct secret name
    region_name = "eu-west-2"  # Ensure correct region
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        print("Fetched Secret:", secret_dict)  # Log fetched secret

        if 'username' in secret_dict and 'password' in secret_dict:
            database_uri = f"postgresql://{secret_dict['username']}:{secret_dict['password']}@{host}/{dbname}"
            return database_uri
        else:
            print("Secret is missing required keys.")  # Log missing keys

    except NoCredentialsError:
        print("AWS credentials not available.")
    except ClientError as e:
        print(f"Client error: {e}. Check your AWS configuration and permissions.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return 'sqlite:///default.db'  # Fallback URI
