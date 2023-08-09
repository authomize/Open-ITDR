# Authomize DataDog Connector (Release - .9 Beta)
- If you come across any issues or problems with a flow please [open an issue](https://github.com/authomize/Open-ITDR/issues).<br>

## Setup Environment Variables
- Leave the path as `/app/.env` in datadog.py if using the Authomize Docker Container.
- Else, to add environment variables create a `.env` file and edit the path in datadog.py file to match. Example `\<PATH>\<TO>\<YOUR>\.env` <br>
- Add new lines in the following format for the environment file: ENV_VARIABLE='VALUE'<br>

# Required Authomize & DataDog Environment Variables
DD_API_KEY = '<YOUR_DD_API_KEY_HERE>' <br>
DD_APP_KEY = '<YOUR_DD_APP_KEY>' <br>
AUTHOMIZE_DD_APPID = '<ENTER_YOUR_CONNECTOR_ID_HERE>' # The ID from your Rest API Connector at https://<YOUR_DOMAIN>.authomize.com/settings/integration/data-sources <br>
AUTHOMIZE_DD_TOKEN = 'atm.........'  # https://<YOUR_DOMAIN>.authomize.com/settings/api-tokens <br>
authomize_batch_size = 1000 # Recommended to leave this at 1000. <br>

## Other Info
- The created JSON files are only for troubleshooting purposes. These can be safely commented out.
- This script does NOT utilize the DataDog Python client. `datadog-api-client`
- For DataDog specific API questions refer to the DataDog API documentation here: https://docs.datadoghq.com/api/latest/
- For Authomize specific API questions refer to the Authomize API documentation here: https://api.authomize.com/documentation

## Data Collected
- Users
- Roles
- User to Role relationships
- Privileges
- Role to Privilege relationships