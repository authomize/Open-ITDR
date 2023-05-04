# Authomize Splunk Connector (Release - .9 Beta)
- If you come across any issues or problems with a flow please [open an issue](https://github.com/authomize/Open-ITDR/issues).

## Getting Started
- This Splunk Connector should work with both Splunk Enterprise and Splunk Cloud

## Setup Environment Variables
- To add environment variables create a `.env` file and edit the path in splunk.py script to match. 
- Add new lines in the following format for the environment file: ENV_VARIABLE='VALUE'

Example `.env`
splunk_base_url = 'https://<YOUR_IP_OR_HOST_HERE>:8089' #Default PORT is 8089, but this is configurable.
splunk_token = 'Bearer eyJr.......'  # Make Splunk token at https://<YOUR_DOMAIN>:<YOUR_PORT>/en-US/manager/launcher/authorization/tokens
authomize_appId = '<ENTER_YOUR_CONNECTOR_ID_HERE>' # The ID from your Rest API Connector at https://<YOUR_DOMAIN>.authomize.com/settings/integration/data-sources
authomize_api_key = 'atm.........'  # https://<YOUR_DOMAIN>.authomize.com/settings/api-tokens
authomize_batch_size = 1000 # Recommended to leave this at 1000. 

## Other Info
- The created JSON files are only for troubleshooting purposes. These can be safely commented out.
- For Splunk specific API questions refer to the Splunk API documentation here: https://docs.splunk.com/Documentation/Splunk/9.0.4/RESTUM/RESTusing
- For Authomize specific API questions refer to the Authomize API documentation here: https://api.authomize.com/documentation