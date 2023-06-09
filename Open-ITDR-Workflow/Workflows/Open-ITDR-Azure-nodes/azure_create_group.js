const axios = require('axios');

module.exports = function(RED) {
    function azure_create_group(config) {
        RED.nodes.createNode(this, config);
        var node = this;
        node.on('input', async function(msg) {

            const groupName = msg.group_name;
            const group_desc = msg.group_desc;
            const access_token = msg.access_token;
            const headers = {Authorization: 'Bearer ' + access_token, "Content-Type": 'application/json' };
            const url = 'https://graph.microsoft.com/v1.0/groups';

            const postData = {
                description: group_desc,
                displayName: groupName,
                groupTypes: [],
                mailEnabled: false,
                mailNickname: 'mailnick',
                securityEnabled: true
            };

			try {
				const response = await axios({
					method: 'post',
					url: url,
					headers: headers,
					data: postData
				});
				
				msg.groupID = response.data.id;
				node.send(msg);

			  } catch (error) {
					node.warn(error);
                    node.warn(error.message);
			  }

        });
    }
    RED.nodes.registerType("azure_create_group", azure_create_group);
};
