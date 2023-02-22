#from dotenv import load_dotenv
#import os
#import pandas as pd
#import numpy as np
#import re as re
import requests
import math
import json


#breaks dataframes into chunks
chunk_size = 9000
def split_df_chunks(data_df,chunk_size):
    total_length     = len(data_df)
    total_chunk_num  = math.ceil(total_length/chunk_size)
    normal_chunk_num = math.floor(total_length/chunk_size)
    chunks = []
    for i in range(normal_chunk_num):
        chunk = data_df[(i*chunk_size):((i+1)*chunk_size)]
        chunks.append(chunk)
    if total_chunk_num > normal_chunk_num:
        chunk = data_df[(normal_chunk_num*chunk_size):total_length]
        chunks.append(chunk)
    return chunks

# Deletes Connector Data
def delete(url_delete, token):
    r = requests.delete(url_delete, headers={'Content-Type': 'application/json', 'Authorization': token})
    file_response = str(r.status_code) + ' ' + str(r.text) + '\n'
    file = open("apiv2_util.log", "a")
    file.write(str(file_response))
    file.close()
    
    
# POST pandas dataframe to endpoint

def post(df, url, token):
    """
    assign Pandas DF, API endpoint including Connector ID in URL & a Token
    """
    for each_list in list(split_df_chunks(df, chunk_size)):
        json_list = json.dumps(json.loads(each_list.to_json(orient='records')))
        json_list = json_list.replace('"[', '[')
        json_list = json_list.replace(']"', ']')
        json_list = json_list.replace('\\"', '"')
        data_string = json.dumps(json_list)
        payload = '{"data": ' +  str(json.loads(data_string)) + '}'
        r = requests.post(url, headers={'Content-Type': 'application/json', 'Authorization': token}, data=payload)
        file_response = str(r.status_code) + ' ' + str(r.text) + '\n'
        file = open("apiv2_util.log", "a")
        file.write(str(file_response))
        file.close()