const axios = require('axios');
module.exports = function(RED) {
    function remove_user_from_group(config) {
        RED.nodes.createNode(this, config);
        var node = this;
        node.on('input', function(msg) {

		try{
            const apiKey = msg.config.OktaKEY;
            const oktaDomain = msg.config.Domain;
            const group_id = msg.groupID;
            const user_id = msg.remove_user;

			headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': 'SSWS ' + apiKey
            };

            const url = 'https://' + oktaDomain + '.okta.com/api/v1/groups/' + group_id + '/users/' + user_id;
            const res = axios.delete(url, { headers }); // Make the axios.put() call awaitabl
		}catch(error) {
			node.warn(error);
		}			
        });
    }
    RED.nodes.registerType("remove_user_from_group", remove_user_from_group);
};
