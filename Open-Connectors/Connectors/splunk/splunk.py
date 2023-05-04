import requests
import json
from datetime import datetime #, timedelta
import logging
import os
from dotenv import load_dotenv

#.env location
load_dotenv('/app/.env') 

# Splunk API settings
splunk_base_url = os.getenv('splunk_base_url') # Atlassian  Domain
splunk_token = os.getenv('splunk_token') # Splunk API Token

# Authomize API settings
appId = os.getenv('authomize_appId')  # Authomize Connector ID (appId) 
authomize_api_key = os.getenv('authomize_api_key') # Authomize Connector API Token
authomize_batch_size = int(os.getenv('authomize_batch_size')) # Authomize Max POST Batch Size

# Set the output format to JSON
string_query_output_mode = "?output_mode=json"

#Splunk URLs
authentication_users = f"{splunk_base_url}/services/authentication/users{string_query_output_mode}"
authorization_roles_url = f"{splunk_base_url}/services/authorization/roles{string_query_output_mode}"

#Authomize URLs
user_dicts_url = f"https://api.authomize.com/v2/apps/{appId}/accounts/users"
role_url = f"https://api.authomize.com/v2/apps/{appId}/access/grouping"
user_role_dicts_url = f"https://api.authomize.com/v2/apps/{appId}/association/accounts"
create_privileges_url = f"https://api.authomize.com/v2/apps/{appId}/privileges"
role_association_url = f"https://api.authomize.com/v2/apps/{appId}/association/groupings"
permission_url = f"https://api.authomize.com/v2/apps/{appId}/access/permissions"

# Headers 
splunk_header = {"Authorization": splunk_token}
authomize_headers = {
    'Content-Type': 'application/json',
    'Authorization': f'{authomize_api_key}'
}

# Initial variables for handling paging for Users
offset = 0
per_page = 30
total = None

#create lists
user_dicts = []
user_role_dicts = []
role_dicts = []
privilege_dicts = []
role_association_dicts = []
permission_dicts = []

logging.basicConfig(filename='/app/splunk/splunk.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filemode='w')

while total is None or offset < total:
    #request for each user
    response = requests.get(authentication_users, headers=splunk_header, params={"count": per_page, "offset": offset} )
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON results
        user_data = response.json()
        users = user_data["entry"]

        # Process each user
        for user in users:
            # Map the fields to a dictionary
            user_dict = {
                "uniqueId": user["name"],
                "originId": user["id"],
                "name": user["content"]["realname"] if user["content"]["realname"] else user["name"],
                "email": user["content"]["email"],
                "lastLoginAt": datetime.utcfromtimestamp(user["content"].get("last_successful_login")).isoformat() if user["content"].get("last_successful_login") else None
            }
            user_dicts.append(user_dict)

            # Map the roles to a dictionary and include the user["id"] as the "sourceId"
            for role in user["content"]["roles"]:
                user_role_dict = {
                    "sourceId": user["name"],
                    "targetId": role
                }
                user_role_dicts.append(user_role_dict)

        # Update the total and offset values for the next iteration
        total = user_data["paging"]["total"]
        offset += per_page

    else:
        logging.error("Error: %s on Splunk Endpoint %s", response.status_code, authentication_users)
        logging.error("Response text: %s", response.text)
        break

# Reset variables for handling paging for Roles
offset = 0
per_page = 30
total = None

while total is None or offset < total:
    #request for each role
    response = requests.get(authorization_roles_url, headers=splunk_header, params={"count": per_page, "offset": offset} )

    # Check if the request was successful
    if response.status_code == 200:
        
        # Parse the JSON results
        role_data = response.json()
        roles = role_data["entry"]
        
        # Process each role
        for role in roles:
            # Create each Role as a Group
            role_dict = {
                "uniqueId": role["name"],
                "originId": role["id"],
                "name": role["name"],
                "type": "Group",
                "isRole": True
            }
            role_dicts.append(role_dict)
            
            # Create each Privilege
            for privilege in role['content']['capabilities']:
                privilege_dict = {
                    "uniqueId": privilege,
                    "originId": privilege,
                    "type": "Use",
                    "originName": privilege,
                }
                privilege_dicts.append(privilege_dict)
            
            # Role Associations
            for role_association in role['content']['imported_roles']:
                role_association_dict = {
                    "sourceId": role_association,
                    "targetId": role['name']
                }
                role_association_dicts.append(role_association_dict)
            
            #Create Permissions
            for permission in role['content']['capabilities']:
                permission_dict = {
                    "sourceUniqueId": role['name'],
                    "sourceType": "Grouping",
                    "privilegeId": permission,
                }
                permission_dicts.append(permission_dict)   
                    
        # Update the total and offset values for the next iteration
        total = user_data["paging"]["total"]
        offset += per_page

    else:
        logging.error("Error: %s on Splunk Endpoint %s", response.status_code, authorization_roles_url)
        logging.error("Response text: %s", response.text)
        break
             
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
with open('/app/splunk/users.json', 'w') as file:
    file.write(json.dumps(user_dicts))
post_authomize_data(user_dicts_url, user_dicts)

# Post role_dicts and write to file for troubleshooting
with open('/app/splunk/roles.json', 'w') as file:
    file.write(json.dumps(role_dicts))
post_authomize_data(role_url, role_dicts)

# Post use to role and write to file for troubleshooting
with open('/app/splunk/user_to_role.json', 'w') as file:
    file.write(json.dumps(user_role_dicts))
post_authomize_data(user_role_dicts_url, user_role_dicts)

# Post privilege_dict and write to file for troubleshooting
with open('/app/splunk/privilege.json', 'w') as file:
    file.write(json.dumps(privilege_dicts))
post_authomize_data(create_privileges_url, privilege_dicts)

# Post role_association_dict and write to file for troubleshooting
with open('/app/splunk/role_association.json', 'w') as file:
    file.write(json.dumps(role_association_dicts))
post_authomize_data(role_association_url, role_association_dicts)

# Post permission_dicts and write to file for troubleshooting
with open('/app/splunk/permission.json', 'w') as file:
    file.write(json.dumps(permission_dicts))
post_authomize_data(permission_url, permission_dicts)

# extract first Accepted_timestamps of a list of timestamp strings
timestamp = accepted_timestamps[0]
#dt = datetime.fromisoformat(timestamp)

# Subtract one second
#dt_minus_one_second = dt - timedelta(seconds=1)

# Update the first element of the list
#timestamp = dt_minus_one_second.isoformat()

# Send the DELETE request using the first user's timestamp
delete_url = f'https://api.authomize.com/v2/apps/{appId}/data?=modifiedBefore={timestamp}'
delete_response = requests.delete(delete_url, headers=authomize_headers)
logging.info("Authomize Delete Response for: %s: %s", delete_url, delete_response.text)