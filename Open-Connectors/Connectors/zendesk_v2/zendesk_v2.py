import requests
import json
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

#.env location
load_dotenv('.env') 

#ZenDesk token
zendesk_token = os.getenv('zendesk_token') 
zendesk_base_url = os.getenv('zendesk_base_url') 
zendesk_user_email = os.getenv('zendesk_user_email')

# Authomize API settings
appId = os.getenv('zendesk_authomize_appId')  # Authomize Connector ID (appId) 
authomize_api_key = os.getenv('authomize_api_key') # Authomize Connector API Token
authomize_batch_size = 1000 # Authomize Max POST Batch Size

logging.basicConfig(filename='/app/zendesk_v2/zendesk_v2.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filemode='w')

# Headers 
authomize_headers = {
    'Content-Type': 'application/json',
    'Authorization': f'{authomize_api_key}'
}

zendesk_headers = {
	"Content-Type": "application/json",
}

#Authomize URLs
accounts_url = f"https://api.authomize.com/v2/apps/{appId}/accounts/users"
grouping_url = f"https://api.authomize.com/v2/apps/{appId}/access/grouping"
accounts_to_groups_url = f"https://api.authomize.com/v2/apps/{appId}/association/accounts"
privileges_url = f"https://api.authomize.com/v2/apps/{appId}/privileges"
permission_url = f"https://api.authomize.com/v2/apps/{appId}/access/permissions"

#zendesk
zendesk_users_url = f'{zendesk_base_url}/api/v2/users'
zendesk_groups_url = f'{zendesk_base_url}/api/v2/groups'

account_data = []
groups_data = []
account_to_group_data = []
privileges_data = []
permissions_data = []

def format_datetime(date_str):
    # Parse the datetime from the original format
    dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
    # Return the datetime in the desired format
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')

session = requests.Session()

group_id_list = []
while zendesk_groups_url:
    response = session.get(
        zendesk_groups_url,
        auth=(f'{zendesk_user_email}/token', f'{zendesk_token}'),
        headers=zendesk_headers
    )
    data = response.json()

    # Transforming the data
    current_page_groups_data = [{
        'uniqueId': str(group['id']),
        'name': group['name'],
        'alternativeName': group.get('description', ''),
    } for group in data['groups']]
    
    groups_data.extend(current_page_groups_data)
    
    current_page_group_ids = [group['id'] for group in data['groups']]
    group_id_list.extend(current_page_group_ids)
        
    # Proceeding to the next page, if it exists
    zendesk_groups_url = data.get('next_page')
    
for group_id in group_id_list:
    #print(group_id)
    groups_users_url = f'{zendesk_base_url}/api/v2/groups/{group_id}/users'
    
    while groups_users_url:
        response = session.get(
            groups_users_url,
            auth=(f'{zendesk_user_email}/token', f'{zendesk_token}'),
            headers=zendesk_headers
        )
        data = response.json()
        #print(data)
        
            # Extracting account to group data
        for users in data['users']:

            if group_id:  # Checking for existence
                account_to_group = {
                    'sourceId': str(users['id']),
                    'targetId': str(group_id)
                }
                account_to_group_data.append(account_to_group)
        
        
        # Proceeding to the next page, if it exists
        groups_users_url = data['next_page']
        
#print(account_to_group_data)

_role_name_to_Authomize_mappings = {
    "end-user": "Use",
    "agent": "Administrative",
    "admin": "Administrative"
}

_mfa_enabled= {
    None: False,
    False: False,
    True: True
}

while zendesk_users_url:
    response = session.get(
        zendesk_users_url,
        auth=(f'{zendesk_user_email}/token', f'{zendesk_token}'),
        headers=zendesk_headers
    )
    data = response.json()
    
    # Extracting account data
    account_data.extend([{
        'uniqueId': str(users['id']),
        'name': users['name'],
        'email': users['email'],
        'status': "Suspended" if users['suspended'] else ("Enabled" if users['active'] else "Disabled"),
        'lastLoginAt': format_datetime(users['last_login_at']) if users['last_login_at'] else None,
        'hasMFA': _mfa_enabled[users['two_factor_auth_enabled']],
        'tags': users['tags'],  
    } for users in data['users']])
    
    # Extracting account to role data
    for users in data['users']:
        role = users.get('role')
        if role:  # Checking for existence
            privilege = {
                'uniqueId': users['role'],
                'type': _role_name_to_Authomize_mappings.get(users['role'], 'Unknown'),
                'originName': users['role']
            }
            privileges_data.append(privilege)
            
            permission = {
                'sourceUniqueId': str(users['id']),
                'sourceType': 'User',
                'privilegeId': users['role'],
                'isRole': True,
            }
            permissions_data.append(permission)

    # Proceeding to the next page, if it exists
    zendesk_users_url = data['next_page']

#Drop Duplicate privileges
seen = set()
no_duplicates = []
for d in privileges_data:
    # Convert the dictionary into a tuple containing its items to make it hashable
    t = tuple(d.items())
    if t not in seen:
        seen.add(t)
        no_duplicates.append(d)

privileges_data = no_duplicates


# Print the results after the while loop concludes
#print(account_data)
#print(account_to_group_data)
#print(privileges_data)
#print(permissions_data)

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

# Post user_dicts and write to file for troubleshooting
# with open('/app/zendesk_v2/accounts.json', 'w') as file:
#     file.write(json.dumps(account_data))
post_authomize_data(accounts_url, account_data)

# Post role_dicts and write to file for troubleshooting
# with open('/app/zendesk_v2/groups.json', 'w') as file:
#     file.write(json.dumps(groups_data))
post_authomize_data(grouping_url, groups_data)

# Post use to role and write to file for troubleshooting
# with open('/app/zendesk_v2/account_to_group.json', 'w') as file:
#     file.write(json.dumps(account_to_group_data))
post_authomize_data(accounts_to_groups_url, account_to_group_data)

# Post privilege_dict and write to file for troubleshooting
# with open('/app/zendesk_v2/privileges.json', 'w') as file:
#     file.write(json.dumps(privileges_data))
post_authomize_data(privileges_url, privileges_data)

# Post role_association_dict and write to file for troubleshooting
# with open('/app/zendesk_v2/permissions.json', 'w') as file:
#     file.write(json.dumps(permissions_data))
post_authomize_data(permission_url, permissions_data)

# extract first Accepted_timestamps of a list of timestamp strings
timestamp = accepted_timestamps[0]

#remove time zone from timestamp
timestamp = timestamp[:-6]

# Send the DELETE request using the first user's timestamp
delete_url = f'https://api.authomize.com/v2/apps/{appId}/data?modifiedBefore={timestamp}'
delete_response = requests.delete(delete_url, headers=authomize_headers)
logging.info("Authomize Delete Response for: %s: %s", delete_url, delete_response.text)
