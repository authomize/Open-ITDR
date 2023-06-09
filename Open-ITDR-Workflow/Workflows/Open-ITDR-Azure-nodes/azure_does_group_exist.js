const axios = require('axios');

module.exports = function(RED) {
    function azure_does_group_exist_Node(config) {
        RED.nodes.createNode(this, config);
        var node = this;
        var results = [];
        var access_token = '';
        
        node.on('input', async function(msg) {
            const https = require('https');
            const access_token = msg.access_token;
			const groupName = msg.group_name;
			
            try {
				var searchURL = 'https://graph.microsoft.com/v1.0/groups/?$filter=displayName%20eq%20%27' + encodeURIComponent(groupName) + '%27';
				const response = await axios.get(searchURL, {
					headers: {
					  Authorization: 'Bearer ' + access_token
					}
				});

				if (response.data.value.length == 1) {
					node.warn(response);
					msg.groupID = response.data.value[0].id;
					node.send([msg, null]);
				} else if (response.data.value.length > 1){
					throw new Error('There is more than one group with the suggested name');
				} else {
					node.send([null, msg])
				}
            } catch (error) {
                node.warn(error);
            }
        });
    }

    RED.nodes.registerType("azure_does_group_exist", azure_does_group_exist_Node);
};