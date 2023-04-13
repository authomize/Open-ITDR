
# PagerDuty + Authomize Integration Benefits


* ***Notify on-call responders based on security and identity events sent from Authomize.***
* ***Send enriched event data from Authomize indicating what triggered the event.***
* ***Create high and low urgency incidents based on the severity of the event from the Authomize event payload.***

# How it Works
* When authomize finds an anomoly in your identity infrastructure it generates an event. Some events will be critical in nature while others are informational. For example a user without MFA as opposed to finding a new EC2 instance exposed on the internet in AWS.
* When you configure the webhooks in Authomize to send the events to PagerDuty using this integration the Authomize tenant will send the events directly to PagerDuty about once every two to three hours. ***ONLY*** new events are sent. If an event is automatically resolved by Authomize and then reopens again, the event will be sent again as if it was a new event.
* PagerDuty maps specific custom data to the generated PagerDuty ticket to assist in determining what type of priority you should apply to the ticket or other actions you may need to take.
* Authomize does not send any other events to indicate any process change, you will need to click on the URL pointing to the event back on Authomize to determine additional details and to perform any further investigations.


# Requirements
* PagerDuty integrations require an Admin base role for account authorization. If you do not have this role, please reach out to an Admin or Account Owner within your organization to configure the integration.
* Authomize configuration of webhooks requires an Admin based role for the creation and configration of webhooks. If you do not have this role, you will need to reach out to your Admin or Account Owner within your organization to finalize the configuration.

# Support

If you need help with this integration, please contact support@authomize.com. 

# Integration Walkthrough
## In PagerDuty
### Integrating With a PagerDuty Service
1. From the **Configuration** menu, select **Services**.
2. There are two ways to add an integration to a service:
   * **If you are adding your integration to an existing service**: Click the **name** of the service you want to add the integration to. Then, select the **Integrations** tab and click the **New Integration** button.
   * **If you are creating a new service for your integration**: Please read our documentation in section [Configuring Services and Integrations](https://support.pagerduty.com/docs/services-and-integrations#section-configuring-services-and-integrations) and follow the steps outlined in the [Create a New Service](https://support.pagerduty.com/docs/services-and-integrations#section-create-a-new-service) section, selecting ***Authomize*** as the **Integration Type** in step 4. Continue with the In  ***Authomize***  section (below) once you have finished these steps.
3. Enter an **Integration Name** in the format `monitoring-tool-service-name` (e.g.  ***Authomize***-Shopping-Cart) and select  ***Authomize***  from the Integration Type menu.
4. Click the **Add Integration** button to save your new integration. You will be redirected to the Integrations tab for your service.
5. An **Integration Key** will be generated on this screen. Keep this key saved in a safe place, as it will be used when you configure the integration with  ***Authomize***  in the next section.
![](https://pdpartner.s3.amazonaws.com/ig-template-copy-integration-key.png)

## In Authomize
1. **Login** to your Authomize tenant with **Admin** priveleges.
2. From the **Configuration** menu found on the top right of your screen, select **Webhooks** located on the menu bar to the left.
3. Click the **Create Webhook** button found top right.
4. When the **Create Webhook** dialogue box comes up you will see three fields:
   * **Webhook Name**
   * **URL**
   * **Events to subscribe**
5. On the **Webhook Name** field enter a meaningful name such as `PagerDuty-Authomize-Events`.
6. On the **URL** field enter the url ```https://events.pagerduty.com/integration/```[YOUR-INTEGRATION-KEY]```/enqueue``` .
   * **YOUR-INTEGRATION-KEY** is the PagerDuty **Integration key** generated from point 5 above under the **Integrating With a PagerDuty Service** heading.
7. On the **Events to subscribe** field select **Incident Created**
8. Click the **Create** button to save your settings.

You are now complete, you should monitor the **Webhook logs** found on the left bar to determine when events are being sent. Authomize customer success team work closley with all Authomize customers and will be able to support you in the process. If you have any questions or issues please reach out to us on support@authomize.com and a success team member will respond to you.

# How to Uninstall

To delete the integration on **Authomize** use the following steps:
1. **Login** to your Authomize tenant with **Admin** priveleges.
2. From the **Configuration** menu found on the top right of your screen, select **Webhooks** located on the menu bar to the left.
3. Find the name of your webhook if you followed the naming above it will be `PagerDuty-Authomize-Events`.
4. Find the **elipses** button found on the far right and click then select **delete** option.
5. You will be prompted with a **Delete Webhook** dialogue box. Click **Yes, Delete Webhook** button to remove the webhook.
6. The Webhook item will be removed from your list.

This completes the uninstall process from **Authomize**.