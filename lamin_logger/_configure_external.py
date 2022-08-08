import logging

try:
    import boto3
    boto3.set_stream_logger("boto3", logging.WARNING)
    import botocore
    logger = logging.getLogger("botocore")
    logger.setLevel(logging.WARNING)
    logger = logging.getLogger("botocore.credentials")
    logger.setLevel(logging.WARNING)
except ImportError:
    pass
