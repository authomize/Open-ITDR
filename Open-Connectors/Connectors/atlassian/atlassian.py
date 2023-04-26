import requests
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv
import time

if __name__ == '__main__':

    load_dotenv('/app/.env') #.env location
    
    # Atlassian API settings
    ATLASSIAN_DOMAIN = os.getenv('ATLASSIAN_DOMAIN') # Atlassian  Domain
    ATLASSIAN_EMAIL = os.getenv('ATLASSIAN_EMAIL') # JIRA email with Admin access
    ATLASSIAN_API_KEY = os.getenv('ATLASSIAN_API_KEY') # JIRA API Token
    ATLASSIAN_MAX_RESULTS = int(os.getenv('ATLASSIAN_MAX_RESULTS')) # Atlassian Max GET Results Per Page
    
    # Authomize API settings
    AUTHOMIZE_ATLASSIAN_CONN_APP_ID = os.getenv('AUTHOMIZE_ATLASSIAN_CONN_APP_ID')  # Authomize Connector ID (appId) 
    AUTHOMIZE_ATLASSIAN_CONN_API_KEY = os.getenv('AUTHOMIZE_ATLASSIAN_CONN_API_KEY') # Authomize Connector API Token
    AUTHOMIZE_ATLASSIAN_CONN_BATCH_SIZE = int(os.getenv('AUTHOMIZE_ATLASSIAN_CONN_BATCH_SIZE')) # Authomize Max POST Batch Size
    
    # Headers for JIRA
    jira_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Headers for Authomize
    authomize_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'{AUTHOMIZE_ATLASSIAN_CONN_API_KEY}'
    }
    
    # JIRA API URLs
    jira_users_url = f'https://{ATLASSIAN_DOMAIN}/rest/api/2/users/search'
    jira_groups_url = f'https://{ATLASSIAN_DOMAIN}/rest/api/2/group/bulk'
    jira_group_members = f'https://{ATLASSIAN_DOMAIN}/rest/api/2/group/member'
    jira_projects_url = f"https://{ATLASSIAN_DOMAIN}/rest/api/2/project/search"
    jira_role_details_url = f"https://{ATLASSIAN_DOMAIN}/rest/api/2/project"
    jira_permissions_url = f"https://{ATLASSIAN_DOMAIN}/rest/api/2/permissions"
    jira_permission_schemes_url = f"https://{ATLASSIAN_DOMAIN}/rest/api/2/permissionscheme"
    
    # Authomize API URLs
    authomize_users_url = f'https://api.authomize.com/v2/apps/{AUTHOMIZE_ATLASSIAN_CONN_APP_ID}/accounts/users'
    authomize_groups_url = f'https://api.authomize.com/v2/apps/{AUTHOMIZE_ATLASSIAN_CONN_APP_ID}/access/grouping'
    authomize_associations_url = f'https://api.authomize.com/v2/apps/{AUTHOMIZE_ATLASSIAN_CONN_APP_ID}/association/accounts'
    authomize_assets_url = f"https://api.authomize.com/v2/apps/{AUTHOMIZE_ATLASSIAN_CONN_APP_ID}/assets"
    authomize_privileges_url = f"https://api.authomize.com/v2/apps/{AUTHOMIZE_ATLASSIAN_CONN_APP_ID}/privileges"
    authomize_access_permissions_url = f"https://api.authomize.com/v2/apps/{AUTHOMIZE_ATLASSIAN_CONN_APP_ID}/access/permissions"
    
    def get_jira_users(url, ATLASSIAN_MAX_RESULTS=ATLASSIAN_MAX_RESULTS, additional_params=None):
        users = []
        start_at = 0
        while True:
            params = {"startAt": start_at, "maxResults": ATLASSIAN_MAX_RESULTS}
            if additional_params:
                params.update(additional_params)
            response = requests.get(url, auth=requests.auth.HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_KEY), headers=jira_headers, params=params)
            json_data = response.json()
            if response.status_code != 200:
                logging.error("Error while fetching JIRA users:", json_data)
                break
            current_users = json_data if isinstance(json_data, list) else json_data.get("values", [])
            if not current_users:
                break
            users.extend(current_users)
            start_at += ATLASSIAN_MAX_RESULTS
        return users
    
    def get_jira_data(url, additional_params=None):
        data = []
        start_at = 0
        while True:
            params = {"startAt": start_at, "maxResults": ATLASSIAN_MAX_RESULTS}
            if additional_params:
                params.update(additional_params)
            response = requests.get(url, auth=requests.auth.HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_KEY), headers=jira_headers, params=params)
            json_data = response.json()
            if response.status_code != 200:
                logging.error("Error while fetching JIRA data:", json_data)
                return data
            if "values" in json_data:
                data.extend(json_data["values"])
                if len(json_data["values"]) < ATLASSIAN_MAX_RESULTS:
                    break
            else:
                data.extend(json_data)
                break
            start_at += ATLASSIAN_MAX_RESULTS
        return data
    
    accepted_timestamps = []
    
    def post_authomize_data(url, data):
        for i in range(0, len(data), AUTHOMIZE_ATLASSIAN_CONN_BATCH_SIZE):
            batch = data[i:i + AUTHOMIZE_ATLASSIAN_CONN_BATCH_SIZE]
            payload = {
                'data': batch,
                'validateOnly': False
            }
            try:
                response = requests.post(url, headers=authomize_headers, json=payload)
                response.raise_for_status()
                # Log the response for both versions of the function
                logging.info("Authomize API Response for %s (Batch %d): %s", url, i // AUTHOMIZE_ATLASSIAN_CONN_BATCH_SIZE + 1, response.text)
                # Handle the accepted_timestamp only if it's present in the response
                response_json = response.json()
                accepted_timestamp = response_json.get("acceptedTimestamp")
                if accepted_timestamp:
                    accepted_timestamps.append(accepted_timestamp)
            except requests.exceptions.RequestException as e:
                logging.error("Error occurred while sending data to Authomize API (Batch %d): %s", i // AUTHOMIZE_ATLASSIAN_CONN_BATCH_SIZE + 1, e)
                logging.error("Response body: %s", response.text)  # Log the response body when an error occurs
                logging.error("Data causing the issue: %s", batch)  # Add this line to log the problematic data
    
    def transform_users(jira_users):
        return [
            {
                'uniqueId': user['accountId'],
                'originId': user['accountId'],
                'name': user['displayName'],
                'email': user.get('emailAddress', None),
                'status': 'Enabled' if user['active'] else 'Disabled',
                'description': user['accountType']
            }
            for user in jira_users
        ]
    
    def transform_groups(jira_groups):
        return [
            {
                'uniqueId': group['groupId'],
                'originId': group['groupId'],
                'name': group['name'],
                'type': 'Group',
                'isRole': False
            }
            for group in jira_groups
        ]
    
    def get_jira_group_members(group_id):
        members = []
        start_at = 0
    
        while True:
            params = {'groupId': group_id, 'startAt': start_at, 'maxResults': ATLASSIAN_MAX_RESULTS }
            response = requests.get(jira_group_members, auth=requests.auth.HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_KEY), headers=jira_headers, params=params)
            data = response.json()
    
            if 'values' in data:
                members.extend(data['values'])
            else:
                break
            
            if data['isLast']:
                break
            
            start_at += ATLASSIAN_MAX_RESULTS
    
        return members
    
    def transform_account_group_associations(jira_groups):
        associations = []
        for group in jira_groups:
            group_id = group['groupId']
            group_members = get_jira_group_members(group_id)
            for member in group_members:
                associations.append({
                    'sourceId': member['accountId'],
                    'targetId': group_id
                })
        return associations
    
    def transform_projects(jira_projects):
        transformed_projects = []
        project_key_list = []
        for project in jira_projects:
            transformed_project = {
                "uniqueId": project["id"],
                "originId": project["key"],
                "name": project["name"],
                "type": "Project",
                "originType": "JIRA",
                "description": project["description"],
                "href": project["self"],
                "owner": project['lead']['accountId'],
                "lastUsedAt": datetime.strptime(project["insight"]["lastIssueUpdateTime"], '%Y-%m-%dT%H:%M:%S.%f%z').isoformat()
            }
            transformed_projects.append(transformed_project)
            project_key_list.append(project["id"])
        return transformed_projects, project_key_list
    
    def transform_role_details(jira_role_details_list):
        transformed_roles = []
        for jira_role_details in jira_role_details_list:
            transformed_role = {
                "uniqueId": str(jira_role_details["id"]),
                "originId": str(jira_role_details["id"]),
                "name": jira_role_details["name"],
                "originType": "JIRA",
                "type": "Group",
                "isRole": True
            }
            transformed_roles.append(transformed_role)
        return transformed_roles
    
    def get_jira_role_data(project_key_list):
        role_details_list = []
        for project_key in project_key_list:
            modified_jira_role_details_url = f"{jira_role_details_url}/{project_key}/roledetails"
            role_details = get_jira_data(modified_jira_role_details_url)
            role_details_list.extend(role_details)
        return role_details_list
    ## Doesn't Always Capture Every Permission
    #def get_jira_permissions(url):
    #    response = requests.get(url, auth=requests.auth.HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_KEY), headers=jira_headers)
    #    json_data = response.json()
    #    if response.status_code != 200:
    #        logging.info("Error while fetching JIRA permissions:", json_data)
    #        return {}
    #    return json_data["permissions"]
    
    def transform_permissions(jira_permissions):
        return [
            {
                "uniqueId": key,
                "originId": key,
                "type": "Use",
                "originName": value["name"],
            }
            for key, value in jira_permissions.items()
        ]
    
    def get_jira_permission_schemes(url):
        response = requests.get(url, auth=requests.auth.HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_KEY), headers=jira_headers)
        json_data = response.json()
        if response.status_code != 200:
            logging.info("Error while fetching JIRA permission schemes:", json_data)
            return []
        return json_data
    
    def transform_permission_schemes(jira_permission_schemes):
        authomize_access_permissions = []
        distinct_permissions = set()
        for permission_scheme in jira_permission_schemes["permissionSchemes"]:
            scope_project_id = ""
            if "scope" in permission_scheme and "project" in permission_scheme["scope"] and "id" in permission_scheme["scope"]["project"]:
                scope_project_id = permission_scheme["scope"]["project"]["id"]
            for permission in permission_scheme["permissions"]:
                if "holder" not in permission:
                    continue
                if "value" not in permission["holder"]:
                    continue
                
                holder_type = permission["holder"]["type"]
                source_type = "User"
                if holder_type in ["user", "userCustomField", "reporter", "projectLead"]:
                    source_type = "User"
                elif holder_type in ["projectRole", "group", "groupCustomField", "applicationRole"]:
                    source_type = "Grouping"
                authomize_access_permissions.append({
                    "sourceUniqueId": permission["holder"]["value"],
                    "sourceType": source_type,
                    "privilegeId": permission["permission"],
                    "assetId": scope_project_id
                })
                # Add the distinct permissions to the set
                distinct_permissions.add(permission["permission"])
        return authomize_access_permissions, distinct_permissions
    
    def transform_permissions(input_list):
            result = []
            for item in input_list:
                result.append({
                    "uniqueId": item,
                    "type": "Use",
                    "originName": item
                })
            return result
    
    logging.basicConfig(filename='/app/atlassian/atlassian.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filemode='w')
    
    def main():
        # Users import and transform
        jira_users = get_jira_users(jira_users_url)
        authomize_users = transform_users(jira_users)
        
        # Groups import and transform
        jira_groups = get_jira_data(jira_groups_url)
        authomize_groups = transform_groups(jira_groups)
        
        # Account-Group Associations and transform
        authomize_account_group_associations = transform_account_group_associations(jira_groups)
        
        # Projects import and transform
        additional_params = {"expand": "description,lead,insight"}
        jira_projects = get_jira_data(jira_projects_url, additional_params)
        authomize_projects, project_key_list = transform_projects(jira_projects)
        
        # Role Details import and transform
        jira_roles = get_jira_role_data(project_key_list)
        authomize_roles = transform_role_details(jira_roles)
        
        ## Commented out because it will miss some permissions
        # Fetch JIRA permissions and transform them into Authomize privileges
        #jira_permissions = get_jira_permissions(jira_permissions_url)
        #authomize_privileges = transform_permissions(jira_permissions)
        #POST but commented out because it might miss permissions
        #post_authomize_data(authomize_privileges_url, authomize_privileges)
        
        # Permission schemes import and transform them into Authomize access permissions
        jira_permission_schemes = get_jira_permission_schemes(jira_permission_schemes_url)
        authomize_access_permissions, distinct_permissions = transform_permission_schemes(jira_permission_schemes)
        
        # Convert distinct_permissions into authomize array
        distinct_permissions_list = list(distinct_permissions)
        authomize_permissions = transform_permissions(distinct_permissions_list)
          
        # Post data to Authomize
        post_authomize_data(authomize_users_url, authomize_users)
        post_authomize_data(authomize_groups_url, authomize_groups)
        post_authomize_data(authomize_assets_url, authomize_projects)
        post_authomize_data(authomize_groups_url, authomize_roles)
        post_authomize_data(authomize_associations_url, authomize_account_group_associations)
        post_authomize_data(authomize_privileges_url, authomize_permissions)
        post_authomize_data(authomize_access_permissions_url, authomize_access_permissions)
        
        # Assuming accepted_timestamps is a list of timestamp strings
        timestamp = accepted_timestamps[0]
        dt = datetime.fromisoformat(timestamp)
        
        # Subtract one second
        dt_minus_one_second = dt - timedelta(seconds=1)
        
        # Update the first element of the list
        timestamp = dt_minus_one_second.isoformat()
        
        # Send the DELETE request using the first user's timestamp
        delete_url = f'https://api.authomize.com/v2/apps/{AUTHOMIZE_ATLASSIAN_CONN_APP_ID}/data?=modifiedBefore={timestamp}'
        delete_response = requests.delete(delete_url, headers=authomize_headers)
        logging.info("Authomize Delete Response for: %s: %s", delete_url, delete_response.text)
    logging.info("Starting atlassian.py execution.")
    main()
    logging.info("Finished atlassian.py execution. Going to sleep.")