# Authomize-Sentinel-Webhook-Reciever
author: Steven Riley

This logic app for MS Sentinel and Authomize. It will recieve a webhook from Authomize, send the data to Log Analytics and create Authomize_v1_CL and then create an an unassigned open incident in MS Sentinel

<a href="https://portal.azure.com/#create/Microsoft.Template" target="_blank">
    <img src="https://aka.ms/deploytoazurebutton"/>
</a>

**Additional Post Install Notes**
Edit the Logic App or go to Logic app designer. 
Expand both the connectors and add a new connection by signing-in to your existing one or entering your workspace ID abd key as needed.
NOTE: Connection name for the first connector will be LogCollector-Authomize-Sentinel-Webhook-Reciever. By default Authomize_v1_CL will be created in your Custom Logs.
Copy the URL 'HTTP POST URL' from the 'When a HTTP request is recieved' task at the very top.
Save the Logic app.

***** LOGIN TO AUTHOMIZE TENANT AS ADMIN ***** 
Under settings (icon in top right corner) you will find webhook. Create a webhook, give it a name and enter the URL you just copied
