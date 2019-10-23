import boto3
import time
import pandas as pd
from textract import s3
import json
import os
from os import listdir
from os.path import isfile, join
from PIL import Image


def push_image_to_s3(img_filename):
    # img_key = img_filename.replace('\\', '/')
    img_key = s3.save_file(img_filename)
    return img_key


def get_textract_client():
    client = boto3.client(
        'textract',
        aws_access_key_id=s3.ACCESS_KEY_ID,
        aws_secret_access_key=s3.SECRET_ACCESS_KEY,
        region_name='us-east-1')
    return client


def parse_response_to_json(response):
    return response


def parse_response_to_df(response):
    blocks = response['Blocks']
    extracted_data = []
    for block in blocks:
        if block['BlockType'] != 'PAGE':
            extracted_data.append({
                "text": block['Text'],
                "confidence": block['Confidence'],
            })

    df = pd.DataFrame(extracted_data)
    df = df.drop_duplicates()
    return df


def parse_response_to_textblob(response):
    blocks = response['Blocks']
    extracted_data = []
    for block in blocks:
        if block['BlockType'] != 'PAGE':
            extracted_data.append(block['Text'])
    return '\n'.join(extracted_data)


def parse_document(img_key):
    textract = get_textract_client()
    response = textract.detect_document_text(Document={'S3Object': {'Bucket': s3.BUCKET_NAME, 'Name': img_key}})
    return response


def image_to_text_csv(img_filename, csv_filename, txt_filename, json_filename):
    img_key = push_image_to_s3(img_filename)
    textract_response = parse_document(img_key)
    text_df = parse_response_to_df(textract_response)
    textblob = parse_response_to_textblob(textract_response)
    text_df.to_csv(csv_filename, index=False)
    with open(txt_filename, "w") as text_file:
        text_file.write(textblob)
    with open(json_filename, 'w') as json_file:
        json.dump(textract_response, json_file)


def tiff_to_jpeg(tiff_file, jpeg_file):
    im = Image.open(tiff_file)
    out = im.convert("RGB")
    out.save(jpeg_file, "JPEG", quality=90)


start_time = time.time()

base_folder = r'C:\developer\aws_ocr_test\sample_docs'
folder_list = ['Barcode', 'Business_cards', 'Checkmark', 'Handprint', 'Mobile_Photos', 'Scanned_documents']

for folder_name in folder_list:
    file_list = [f for f in listdir(join(base_folder, folder_name)) if isfile(join(base_folder, folder_name, f))]
    img_list = [f for f in file_list if f.endswith('.tif') or f.endswith('.png') or f.endswith('.jpg')]
    for img_name in img_list:
        print(img_name)
        img_filename = join(base_folder, folder_name, img_name)
        # convert tiff to jpeg
        if img_name.endswith('tif'):
            tiff_file = img_filename
            jpeg_file = img_filename[:-3] + 'jpg'
            if not os.path.exists(jpeg_file):
                tiff_to_jpeg(tiff_file, jpeg_file)
            img_filename = jpeg_file
        csv_filename = img_filename[:-3] + 'csv'
        txt_filename = img_filename[:-3] + 'txt'
        json_filename = img_filename[:-3] + 'json'
        if not os.path.exists(json_filename):
            image_to_text_csv(img_filename, csv_filename, txt_filename, json_filename)

end_time = time.time()
run_time = end_time - start_time
print(run_time)