const axios = require('axios');

module.exports = function(RED) {
    function azure_get_access_token_Node(config) {
        RED.nodes.createNode(this, config);
        var node = this;
                
        node.on('input', async function(msg) {
            const https = require('https');

            const clientId = msg.config.clientId;
            const clientSecret = msg.config.clientSecret;
            const tenantId = msg.config.tenantId;
            
            const tokenEndpoint = 'https://login.microsoftonline.com/' + tenantId + '/oauth2/v2.0/token';

			
            const formUrlEncoded = x =>
                Object.keys(x).reduce((p, c) => p + `&${c}=${encodeURIComponent(x[c])}`, '');

            const bodyFormData = {
                grant_type: 'client_credentials',
                client_id: clientId,
                client_secret: clientSecret,
                scope: 'https://graph.microsoft.com/.default'
            };

            try {
                const response = await axios({
                    url: tokenEndpoint,
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    data: formUrlEncoded(bodyFormData)
                });

				msg.access_token = response.data.access_token;
                node.send(msg);
				

            } catch (error) {
                node.warn(error);
            }
        });
    }

    RED.nodes.registerType("azure_get_access_token", azure_get_access_token_Node);
};
