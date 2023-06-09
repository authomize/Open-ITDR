const axios = require('axios');

module.exports = function(RED) {
    function azure_add_user_to_group_Node(config) {
        RED.nodes.createNode(this, config);
        var node = this;
       
        node.on('input', async function(msg) {
            const https = require('https');
            const access_token = msg.access_token;
            const groupID = msg.groupID;
            const userID = msg.userIds[0];
			
			const postData = {
                "@odata.id": 'https://graph.microsoft.com/v1.0/directoryObjects/' + userID
            };
			
			var url = 'https://graph.microsoft.com/v1.0/groups/' + groupID + '/members/$ref';
            const headers = { Authorization: 'Bearer ' + access_token, "Content-Type": 'application/json' };
            
			try {
                axios.post(url, postData, { headers }).then(response => {
                    const res = response.data;
					msg.add_res = res;
					node.send(msg);
                }).catch(error => {
                    node.warn(error);
                    node.warn(error.message);
                });
            } catch (error) {
                node.warn(error);
				node.warn(error.message);
            }
        });
    }

    RED.nodes.registerType("azure_add_user_to_group", azure_add_user_to_group_Node);
};
