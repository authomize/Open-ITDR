# Authomize-Sentinel-Webhook-Reciever
## Initial Setup on Azure
This logic app for MS Sentinel and Authomize. It will recieve a webhook from Authomize, send the data to Log Analytics and create Authomize_v1_CL and then create an an unassigned open incident in MS Sentinel

<a href="https://portal.azure.com/#create/Microsoft.Template" target="_blank">
    <img src="https://aka.ms/deploytoazurebutton"/>
</a>

**Additional Post Install Notes**
Edit the Logic App or go to Logic app designer. 
Expand both the connectors and add a new connection by signing-in to your existing one or entering your workspace ID and key as needed.
NOTE: Connection name for the first connector will be LogCollector-Authomize-Sentinel-Webhook-Reciever. By default Authomize_v1_CL will be created in your Custom Logs.
Copy the URL 'HTTP POST URL' from the 'When a HTTP request is recieved' task at the very top. Save the Logic app.

## Create a Webhook In Authomize
1. **Login** to your Authomize tenant with **Admin** priveleges.
2. From the **Configuration** menu found on the top right of your screen, select **Webhooks** located on the menu bar to the left.
3. Click the **Create Webhook** button found top right.
4. When the **Create Webhook** dialogue box comes up you will see three fields:
   * **Webhook Name**
   * **URL**
   * **Events to subscribe**
5. On the **Webhook Name** field enter a meaningful name such as `Sentinel-Authomize-Events`.
6. On the **URL** field enter the url you just cpied from above.
7. On the **Events to subscribe** field select **Incident Created**
8. Click the **Create** button to save your settings.