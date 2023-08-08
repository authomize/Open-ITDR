import requests
from datetime import datetime
import logging
import json
import os
from dotenv import load_dotenv

load_dotenv('/app/.env') #.env location

# DD API settings

DD_API_KEY = os.getenv('DD_API_KEY') # DD Token
DD_APP_KEY = os.getenv('DD_APP_KEY') # DD Application Key

# Authomize API settings
AUTHOMIZE_DD_TOKEN = os.getenv('AUTHOMIZE_DD_TOKEN') #Authomize API Token
AUTHOMIZE_APP_ID = os.getenv('AUTHOMIZE_DD_APPID')  #Authomize Connector ID (appId) 
authomize_batch_size = int(os.getenv('authomize_batch_size')) # Authomize Max POST Batch Size

#Authomize URLs
user_url = f"https://api.authomize.com/v2/apps/{AUTHOMIZE_APP_ID}/accounts/users"
role_url = f"https://api.authomize.com/v2/apps/{AUTHOMIZE_APP_ID}/access/grouping"
user_to_role_url = f"https://api.authomize.com/v2/apps/{AUTHOMIZE_APP_ID}/association/accounts"
create_privileges_url = f"https://api.authomize.com/v2/apps/{AUTHOMIZE_APP_ID}/privileges"
permission_url = f"https://api.authomize.com/v2/apps/{AUTHOMIZE_APP_ID}/access/permissions"

# Headers for DD
dd_headers = {
    "Accept": "application/json",
    "DD-API-KEY": f"{DD_API_KEY}",
    "DD-APPLICATION-KEY": f"{DD_APP_KEY}",
}

# Authomize header
authomize_headers = {
    'Content-Type': 'application/json',
    'Authorization': f'{AUTHOMIZE_DD_TOKEN}'
}

logging.basicConfig(filename='/app/datadog/datadog.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filemode='w')

dd_accounts_url = "https://api.datadoghq.com/api/v2/users"
page_size = 10
page_number = 0  #start from page 0
total_filtered_count = None
user_data = []
role_data = []
permission_data = []

while total_filtered_count is None or (page_number - 1) * page_size < total_filtered_count:
    params = {
        "page[size]": page_size,
        "page[number]": page_number,
    }
    response = requests.get(dd_accounts_url, headers=dd_headers, params=params)

    if response.status_code == 200:
        json_data = response.json()
        
        for user in json_data.get("data", []):
            if user['type'] == 'users':
                user_data.append(user)
        
        for role in json_data.get("included", []):
            if role['type'] == 'roles':
                role_data.append(role)
                
        for permission in json_data.get("included", []):
            if permission['type'] == 'permissions':
                permission_data.append(permission)
        
        total_filtered_count = json_data["meta"]["page"]["total_filtered_count"]
        page_number += 1
    else:
        print(f"Error - Status Code: {response.status_code} Response Text: {response.text}")
        break

dd_users = []
user_to_role = []

for user in user_data:
    user_info = {
        'uniqueId': user['id'],
        'originId': user['id'],
        'name': user['attributes']['name'],
        'email': user['attributes']['email'],
    }
    
    if user['attributes']['disabled']:
        status = 'Disabled'
    elif user['attributes']['status'] == 'Active':
        status = 'Enabled'
    else:
        status = 'Unknown'
    
    user_info['status'] = status
    dd_users.append(user_info)

    for user_role in user['relationships']['roles']['data']:
        user_relationship = {
            'sourceId': user['id'],
            'targetId': user_role['id'],
        }
    user_to_role.append(user_relationship)

roles = []
role_to_permission = []

for role in role_data:
    if role['type'] == 'roles':
        role_dict = {
            'uniqueId': role['id'],
            'originId': role['id'],
            'name': role['attributes']['name'],
            'originType': 'Role',
            'type': 'Group',
            'isRole': True
        }
        if role_dict not in roles:
            roles.append(role_dict)

        for role_permission in role['relationships']['permissions']['data']:
            permission_dict = {
            'sourceUniqueId': role['id'],
            'sourceType': "Grouping",
            'privilegeId': role_permission['id']
        }
            if permission_dict not in role_to_permission:
                role_to_permission.append(permission_dict)
            
privileges = []

for privilege in permission_data:
    if privilege['type'] == 'permissions':
        uniqueId = privilege['id']
        originId = privilege['id']
        display_type = privilege['attributes']['display_type']
        if display_type == 'read':
            type = "Read"
        elif display_type == 'write':
            type = "Write"
        else:
            type = "Unknown"

        originName = privilege['attributes']['display_name']
        privilege_info = {'uniqueId': uniqueId, 'originId': originId, 'type': type, 'originName': originName}
        
        if privilege_info not in privileges:
            privileges.append(privilege_info)

accepted_timestamps = []

def post_authomize_data(url, data):
    for i in range(0, len(data), authomize_batch_size):
        batch = data[i:i + authomize_batch_size]
        payload = {
            'data': batch,
            'validateOnly': False
        }
        try:
            response = requests.post(url, headers=authomize_headers, json=payload)
            response.raise_for_status()
            # Log the response for both versions of the function
            logging.info("Authomize API Response for %s (Batch %d): %s", url, i // authomize_batch_size + 1, response.text)
            # Handle the accepted_timestamp only if it's present in the response
            response_json = response.json()
            accepted_timestamp = response_json.get("acceptedTimestamp")
            if accepted_timestamp:
                accepted_timestamps.append(accepted_timestamp)
        except requests.exceptions.RequestException as e:
            logging.error("Error occurred while sending data to Authomize API (Batch %d): %s", i // authomize_batch_size + 1, e)
            logging.error("Response body: %s", response.text)  # Log the response body when an error occurs
            logging.error("Data causing the issue: %s", batch)  # Add this line to log the problematic data


# Post users and write to file for troubleshooting
with open('/app/datadog/users_list.json', 'w') as file:
    file.write(json.dumps(dd_users))
post_authomize_data(user_url, dd_users)

# Post roles and write to file for troubleshooting
with open('/app/datadog/roles_list.json', 'w') as file:
    file.write(json.dumps(roles))
post_authomize_data(role_url, roles)

# Post users to roles and write to file for troubleshooting
with open('/app/datadog/user_to_role_list.json', 'w') as file:
    file.write(json.dumps(user_to_role))
post_authomize_data(user_to_role_url, user_to_role)

# Post privileges and write to file for troubleshooting
with open('/app/datadog/privilege_list.json', 'w') as file:
    file.write(json.dumps(privileges))
post_authomize_data(create_privileges_url, privileges)

# Post privileges and write to file for troubleshooting
with open('/app/datadog/permission_list.json', 'w') as file:
    file.write(json.dumps(role_to_permission))
post_authomize_data(permission_url, role_to_permission)

# take first accepted timestamp
timestamp = accepted_timestamps[0][:-6]
delete_url = f'https://api.authomize.com/v2/apps/{AUTHOMIZE_APP_ID}/data?modifiedBefore={timestamp}'
delete_response = requests.delete(delete_url, headers=authomize_headers)
logging.info("Authomize Delete Response for: %s: %s", delete_url, delete_response.text)