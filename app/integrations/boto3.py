import boto3
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)


def upload_file(file_obj, key: str):
    s3_client.upload_fileobj(
        file_obj,
        AWS_S3_BUCKET,
        key,
        ExtraArgs={"ACL": "private"}
    )
    return True


def generate_presigned_url(key: str, expires: int = 3600):
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )
    return url


def delete_file(key: str):
    s3_client.delete_object(
        Bucket=AWS_S3_BUCKET,
        Key=key,
    )
    return True

def generate_presigned_url(key: str, content_type: str, expires: int = 3600):
    return s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": AWS_S3_BUCKET,
            "Key": key,
            "ContentType": content_type  
        },
        ExpiresIn=expires
    )
