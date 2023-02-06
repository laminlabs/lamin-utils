import logging

try:
    import boto3

    # this gets logged 6 times
    boto3.set_stream_logger(name="botocore.credentials", level=logging.WARNING)
    # the 7th logging message of credentials came from aiobotocore
    boto3.set_stream_logger(name="aiobotocore.credentials", level=logging.WARNING)
    boto3.set_stream_logger(name="urllib3.connectionpool", level=logging.WARNING)
except ImportError:
    pass
