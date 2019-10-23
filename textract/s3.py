import boto3
import botocore
import pickle
import io
import os
import pandas as pd
from time import sleep
import logging
from textract.awssecrets import ACCESS_KEY_ID, SECRET_ACCESS_KEY, BUCKET_NAME


SLEEP_TIME = 0.5


def get_s3_obj():
    s3 = boto3.resource(
        's3',
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY
    )
    return s3


def get_s3_client():
    s3 = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY
    )
    return s3


def get_bucket(bucket_name=BUCKET_NAME, s3=get_s3_obj(), error_on_not_found=False):
    buckets_all = list([bucket.name for bucket in s3.buckets.all()])
    if bucket_name in buckets_all:
        b_obj = s3.Bucket(bucket_name)
    else:
        if error_on_not_found:
            raise FileNotFoundError("Bucket {0} was not found in {1}".format(bucket_name, str(buckets_all)))
        b_obj = s3.create_bucket(ACL='private', Bucket=bucket_name)
    b_obj.wait_until_exists()
    return b_obj


def save(obj, key):
    try:
        key = key.replace('\\', '/')
        b_obj = get_bucket()
        fin = io.BytesIO(pickle.dumps(obj))
        b_obj.upload_fileobj(Key=key, Fileobj=fin)
        fin.close()
    except botocore.exceptions.ClientError as e:
        print("Error saving to s3. Retrying in {0}: {1}".format(SLEEP_TIME, str(e)))
        sleep(SLEEP_TIME)
        save(obj, key)


def save_file(filepath):
    try:
        key = filepath.replace('\\', '/')
        b_obj = get_bucket()
        with open(filepath, 'rb') as file:
            b_obj.upload_file(Filename=filepath, Key=key)
        return key

    except botocore.exceptions.ClientError as e:
        print("Error saving to s3. Retrying in {0}: {1}".format(SLEEP_TIME, str(e)))
        sleep(SLEEP_TIME)
        save_file(filepath)


def load(key):
    try:
        key = key.replace('\\', '/')
        print('reading key: {0}'.format(key))
        b_obj = get_bucket(error_on_not_found=True)
        fout = io.BytesIO()
        b_obj.download_fileobj(Key=key, Fileobj=fout)
        fout.seek(0)  # return to the beginning of the file
        obj = pickle.loads(fout.read())
        # obj = pd.read_pickle(fout.read())
        fout.close()
        return obj
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("{0} doesn't exist.".format(key))
            return pd.DataFrame()
        else:
            print("Error reading from s3. Retrying in {0}: {1}".format(SLEEP_TIME, str(e)))
            sleep(SLEEP_TIME)
        return load(key)


def load_file(filepath, key=None):
    try:
        if key is None:
            key = filepath.replace('\\', '/')
        print('reading key: {0}'.format(key))
        b_obj = get_bucket(error_on_not_found=True)
        b_obj.download_file(Key=key, Filename=filepath)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("{0} doesn't exist.".format(key))
        else:
            print("Error reading from s3. Retrying in {0}: {1}".format(SLEEP_TIME, str(e)))
            sleep(SLEEP_TIME)
        return load_file(filepath)


def key_exists(key):
    key = key.replace('\\', '/')
    b_obj = get_bucket()
    return len(list(b_obj.objects.filter(Prefix=key))) > 0


def safe_save(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pickle.dump(obj, open(path, 'wb'))


def local_load(path):
    if not os.path.exists(path):
        print("Loading from s3: {0}".format(path))
        obj = load(path)
        safe_save(obj, path)
    return pickle.load(open(path, 'rb'))


def local_load_file(path):
    if not os.path.exists(path):
        load_file(path)
