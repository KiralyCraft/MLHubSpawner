from minio import Minio
from minio.error import S3Error

class MinIOManager:
    def __init__(self, minio_url: str, minio_access_key: str, minio_secret_key: str):
        """
        Initialize the MinIOManager with the provided URL and credentials.
        
        The secure flag is determined based on the scheme of the minio_url:
          - True if the URL starts with "https://"
          - False if the URL starts with "http://"
        
        Parameters:
            minio_url (str): URL of the MinIO server, starting with either "http://" or "https://".
            minio_access_key (str): Access key for the MinIO server.
            minio_secret_key (str): Secret key for the MinIO server.
        """
        # Validate and determine the secure flag based on the URL prefix.
        if minio_url.startswith("https://"):
            secure = True
            # Remove the scheme (e.g., "https://") to get the endpoint.
            endpoint = minio_url[len("https://"):]
        elif minio_url.startswith("http://"):
            secure = False
            endpoint = minio_url[len("http://"):]
        else:
            raise ValueError("minio_url must start with either 'http://' or 'https://'.")

        self.client = Minio(endpoint,access_key=minio_access_key,secret_key=minio_secret_key,secure=secure)
    
    def create(self, bucket_name: str) -> bool:
        """
        Create a bucket with the provided name if it does not exist.

        Parameters:
            bucket_name (str): The name of the bucket to be created.
            
        Returns:
            bool: True if the bucket exists or is successfully created; False if there's an error.
        """
        try:
            # Check if the bucket exists.
            if not self.client.bucket_exists(bucket_name):
                # Create the bucket if it does not exist.
                self.client.make_bucket(bucket_name)
            return True
        except Exception as error:
            return False