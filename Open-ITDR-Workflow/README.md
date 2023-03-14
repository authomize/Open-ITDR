# OpenITDR Workflow Usage (_Alpha Version - EA_)
Here are the details for working directly with the existing Authomize workflows. If you come across any issues or problems with a flow please [open an issue](https://github.com/authomize/Open-ITDR/issues).

## Getting Started

- Ensure you have docker installed, the following example assumes a docker environment
- Clone the repository into a working directory, by using git clone like the following - 
```git clone https://github.com/authomize/Open-ITDR ```
- Once you have cloned, change directory to ```<yourworkingdirectory>/Open-ITDR/Open-ITDR-Workflow/Workflows```
- Now create your image by typing in the following docker command note the period '.' at the end of the line - ``` docker build -t node-red:latest . ```
- Now start the image by running the following command - ```docker run --rm -e "NODE_RED_CREDENTIAL_SECRET=T0pSecret" -p 1880:1880 -v node_red_data:/data --name mynodered001 node-red```
  - Note that node_red_data is a volume. While this volume exists your changes and updates will persist. If you delete the volume your changes will be removed.
- Get into the initial console by clicking on the following link as indicated when you started the image ```http://127.0.0.1:1880/```

Congrats you are now running with Node-Red with an Authomize OpenITDR Workflow.

## Configuring the Flow
At this point you have the flows loaded in front of you. There are still a few more steps to follow, depending on the flows you need to configure. Lets concentrate on each flow specifically.

### Okta application exfiltration
- Find the Global Variables node, it is labelled USER TO UPDATE. Double click on the node and open it up
- Update the variables listed in the node, specifcially you will need
  - ```AuthToken``` - this is the Token generated in your Authomize tenant. Go to the configurations page, click API Tokens and select a Platform Token. Insert that token here.
  - ```OktaAPI``` - this is the domain of your Okta tenant.
  - ```OktaKEY``` - this is the developnment key issued, it will need access to the API's specifically we use the referenced password reset https://developer.okta.com/docs/reference/api/users/#reset-password 

Click Done and Click "Deploy" found top right on the webpage

Now watch the [video](https://app.box.com/s/8y5l5j0ba65ujfbxaijm8g4bw1jfzold) showing how to switch on and update the other nodes within this flow. You may need to *download* before you can watch.

### Other workflows
We will document the other workflows and update content as they become available.
