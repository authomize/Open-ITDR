const axios = require('axios');

module.exports = function(RED) {
    function azure_users_to_id_Node(config) {
        RED.nodes.createNode(this, config);
        var node = this;
        var results = [];
        var access_token = '';
        
        node.on('input', async function(msg) {
            const https = require('https');
            const access_token = msg.access_token;
			const emails = msg.emails || (msg.payload.data.entities[0] ? [msg.payload.data.entities[0].email] : []);
			
            try {
               	const userIds = [];

				for (const email of emails) {
					var searchURL = 'https://graph.microsoft.com/v1.0/users?$filter=mail%20eq%20%27' + email + '%27';
					const response = await axios.get(searchURL, {
						headers: {
						  Authorization: 'Bearer ' + access_token
						}
				  });

				  if (response.data.value.length > 0) {
						userIds.push(response.data.value[0].id);
				  } else {
						userIds.push(null); // User not found for the email
				  }
				}

				msg.userIds = userIds;			
                node.send(msg);
				

            } catch (error) {
                console.log(error);
            }
        });
    }

    RED.nodes.registerType("azure_users_to_id", azure_users_to_id_Node);
};
