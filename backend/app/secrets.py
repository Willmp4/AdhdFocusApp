import psycopg2
import boto3
import json
from botocore.exceptions import NoCredentialsError, ClientError

def get_database_uri():
    host = 'focus-app.cfa9q7ilvqdl.eu-west-2.rds.amazonaws.com'
    dbname = 'focus-app'
    default_db = 'postgres'  # Default database you can connect to
    secret_name = "rds!db-ae373175-5f02-46bb-86f9-a5dacbd77a96"
    region_name = "eu-west-2"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        print("Fetched Secret:", secret_dict)  # Log fetched secret

        if 'username' in secret_dict and 'password' in secret_dict:
            # Connect to the default database to check if 'focus-app' exists and create it if it does not
            connection = psycopg2.connect(
                dbname=default_db,
                user=secret_dict['username'],
                password=secret_dict['password'],
                host=host
            )
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(f"CREATE DATABASE \"{dbname}\"")
                print(f"Database {dbname} created successfully.")
            cursor.close()
            connection.close()

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

