# Authomize ZenDesk Connector (Release - .9 Beta)
- If you come across any issues or problems with a flow please [open an issue](https://github.com/authomize/Open-ITDR/issues).<br>

## Setup Environment Variables
- Leave the path as `.env` in zendesk_v2.py if using the Authomize Docker Container.
- Else, to add environment variables create a `.env` file and edit the path in zendesk_v2.py file to match. Example `\<PATH>\<TO>\<YOUR>\.env` <br>
- Add new lines in the following format for the environment file: ENV_VARIABLE='VALUE'<br>

# Required Authomize & Zendesk Environment Variables
zendesk_user_email = '<YOUR_ZENDESK_EMAIL_ADDRESS>' <br>
zendesk_base_url = '<ZENDESK_BASE_URL>' # example: https://authomizehelp.zendesk.com< br>
zendesk_token='ZENDESK_TOKEN' <br>
zendesk_authomize_appId = '<ENTER_YOUR_CONNECTOR_ID_HERE>' # The ID from your Rest API Connector at https://<YOUR_DOMAIN>.authomize.com/data-sources <br>
authomize_api_key = 'atm.........'   <br>

## Other Info
- The created JSON files are only for troubleshooting purposes. These can be safely commented out.
- This script does NOT utilize the Zendesk Python client.
- For ZenDesk specific API questions refer to the ZenDesk API documentation here: https://developer.zendesk.com/api-reference
- For Authomize specific API questions refer to the Authomize API documentation here: https://api.authomize.com/documentation
- See the Zendesk API Token for more information https://developer.zendesk.com/api-reference/introduction/security-and-auth/#api-token

## Data Collected
- Users
- Groups
- User to Groups relationships
- Roles
- User to Role relationships
