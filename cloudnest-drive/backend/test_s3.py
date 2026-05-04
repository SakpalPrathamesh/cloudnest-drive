from config import Config
from utils.s3_utils import _get_s3_client

def test_connection():
    try:
        s3 = _get_s3_client()
        response = s3.list_buckets()
        buckets = [b["Name"] for b in response["Buckets"]]
        print("✅ S3 connected successfully!")
        print(f"Your buckets: {buckets}")
        print(f"Your target bucket: {Config.S3_BUCKET_NAME}")
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")

test_connection()