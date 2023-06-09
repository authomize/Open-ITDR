const axios = require('axios');
module.exports = function(RED) {
    function add_user_to_group(config) {
        RED.nodes.createNode(this, config);
        var node = this;
        node.on('input', function(msg) {

        try{
            const apiKey = msg.config.OktaKEY;
            const oktaDomain = msg.config.Domain;
            const group_id = msg.groupID;
            const user_id = msg.create_user;

            headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': 'SSWS ' + apiKey
            };

            const url = 'https://' + oktaDomain + '.okta.com/api/v1/groups/' + group_id + '/users/' + user_id;
	    axios.put(url, {}, { headers })
          .then(response => {
            msg.response = response.data;
            node.send(msg);
          })
          .catch(error => {
            node.warn(error);
          });
      } catch(error) {
        node.warn(error);
      }
    });
  }

  RED.nodes.registerType("add_user_to_group", add_user_to_group);
};
