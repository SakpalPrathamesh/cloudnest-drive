import logging
import mimetypes
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from config import Config

logger = logging.getLogger(__name__)


def _get_s3_client():
    """Create and return an S3 client using credentials from .env"""
    return boto3.client(
        "s3",
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        region_name=Config.AWS_REGION,
    )


def upload_file_to_s3(file_obj, user_id: str, filename: str) -> dict:
    """Upload a file to S3 under the user's folder"""
    s3 = _get_s3_client()

    # Each user gets their own folder: users/user123/myfile.pdf
    s3_key = f"users/{user_id}/{filename}"

    # Detect file type
    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        content_type = "application/octet-stream"

    # Get file size
    file_obj.seek(0, 2)
    file_size = file_obj.tell()
    file_obj.seek(0)

    try:
        s3.upload_fileobj(
            file_obj,
            Config.S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": content_type}
        )
        logger.info(f"Uploaded {s3_key} successfully")
        return {
            "s3_key": s3_key,
            "filename": filename,
            "size": file_size,
            "content_type": content_type,
        }

    except NoCredentialsError:
        raise RuntimeError("AWS credentials missing. Check your .env file.")
    except ClientError as e:
        raise RuntimeError(f"S3 upload failed: {e.response['Error']['Message']}")


def generate_presigned_download_url(s3_key: str, expiry: int = 3600) -> str:
    """Generate a temporary download link for a file"""
    s3 = _get_s3_client()

    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": Config.S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expiry
        )
        return url
    except ClientError as e:
        raise RuntimeError(f"Could not generate download URL: {e.response['Error']['Message']}")


def list_user_files_from_s3(user_id: str) -> list:
    """List all files belonging to a specific user"""
    s3 = _get_s3_client()
    prefix = f"users/{user_id}/"
    files = []

    try:
        response = s3.list_objects_v2(
            Bucket=Config.S3_BUCKET_NAME,
            Prefix=prefix
        )

        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key == prefix:
                continue

            filename = key.replace(prefix, "")

            files.append({
                "s3_key": key,
                "filename": filename,
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })

        return files

    except NoCredentialsError:
        raise RuntimeError("AWS credentials missing.")
    except ClientError as e:
        raise RuntimeError(f"Could not list files: {e.response['Error']['Message']}")


def delete_file_from_s3(s3_key: str, user_id: str) -> bool:
    """Delete a file from S3 (only if it belongs to this user)"""
    s3 = _get_s3_client()

    # Security check — make sure user owns this file
    if not s3_key.startswith(f"users/{user_id}/"):
        raise PermissionError("You cannot delete this file.")

    try:
        s3.delete_object(Bucket=Config.S3_BUCKET_NAME, Key=s3_key)
        logger.info(f"Deleted {s3_key}")
        return True
    except ClientError as e:
        raise RuntimeError(f"Delete failed: {e.response['Error']['Message']}")