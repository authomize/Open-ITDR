
** NOTE requirements.txt is just a dump - check py scripts for specifics (but a pip install of the requirements will get you all that you need)
***************************************
************NEEDS UPDATE***************
***************************************

DO NOT JUST GIVE AWAY!!!
CHECK the parameters.json file it has private Tokens - don't release to public without removing
- How it works
1) Create App in Authomize
2) Get app ID from app
3) Create Token in Authomize store in safe place
4) Create application secret from Azure Portal store in safe place
5) Apply the correct scope rights to the app "secret" within the Azure Portal
6) Get your AD client id store in safe place
7) update the paarameters.json file with all the above collected data
8) setup a cron job to run the code on a 15/30 minute cycle
9) note a file is created to track the date. Do not delete this file. If the file is deleted, then all incidents from the very beginning will be collected
10) **** THESE ARE BROAD INSTRUCTIONS **** I will update once I do final cut of code.



  "authority": "https://login.microsoftonline.com/{AzureTenantID}"
  "client_id": "<Application (client) ID>" <- This is the ID from the app registeration [GUID]
  "scope": ["https://graph.microsoft.com/.default"] <- Leave this alone and do not touch
  "secret": "<Secret Value>", <- This is the SECRET Value (Not the Secret ID - the Secret ID looks like a GUID) You create a secret key after creating the application (client_id)
  "endpoint": "https://graph.microsoft.com/v1.0/identityProtection/riskDetections",<- Leave this alone and do not touch
  "authomizeAPIkey": "<Create Token Access for API in Authomize>",
  "authomizeBaseURL": "https://api.authomize.com/v2/apps/", <- Leave this alone and do not touch unless directed to do so
  "authomizeRestAPIid": "7afc0ec3-b86c-40fe-80d0-8d2b42f16e8e" <- This is the application ID created in Authomize - It is created when you create the API Application (See documentation)
