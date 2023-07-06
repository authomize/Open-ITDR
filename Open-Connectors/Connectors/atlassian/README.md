# Authomize Atlassian Connector (Release - .9 Beta)
- If you come across any issues or problems with a flow please [open an issue](https://github.com/authomize/Open-ITDR/issues).

## Getting Started
- This Atlassian Connector pulls Users, Groups, Roles and their relationships.

## Setup Environment Variables
- To add environment variables create a `.env` file and edit the path in atlassian.py script to match. 
- Add new lines in the following format for the environment file: ENV_VARIABLE='VALUE'

## Atlassian API info 
ATLASSIAN_DOMAIN='<YOUR_DOMAIN>.atlassian.net' <br>
ATLASSIAN_EMAIL='<USER_EMAIL>' <br>
ATLASSIAN_API_KEY='<ATLASSIAN_API_KEY>' <br>
ATLASSIAN_MAX_RESULTS='50' #50 is recommended 
<br>
AUTHOMIZE_ATLASSIAN_CONN_APP_ID='<AUTHOMIZE_API_KEY>' <br>
AUTHOMIZE_ATLASSIAN_CONN_API_KEY='<AUTHOMIZE_API_TOKEN' <br>
AUTHOMIZE_ATLASSIAN_CONN_BATCH_SIZE='1000' <br>

## Other Info
- The created JSON files are only for troubleshooting purposes. These can be safely commented out.
- For Atlassian specific API questions refer to the Atlassian API documentation here: https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#about
- For Authomize specific API questions refer to the Authomize API documentation here: https://api.authomize.com/documentation