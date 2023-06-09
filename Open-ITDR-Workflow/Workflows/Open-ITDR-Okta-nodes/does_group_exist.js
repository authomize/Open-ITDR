const https = require('https');

module.exports = function(RED) {
    function OktaGroupExistsNode(config) {
        RED.nodes.createNode(this, config);
        var node = this;

        node.on('input', function(msg) {
            const apiKey = msg.config.OktaKEY;
            const oktaDomain = msg.config.Domain;
            const groupName = msg.group_name;

            const url = 'https://' + oktaDomain + '.okta.com/api/v1/groups?search=profile.name+eq+%22' + groupName + '%22';
            const options = {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': 'SSWS ' + apiKey
                }
            };

            const req = https.get(url, options, (res) => {
                let rawData = '';

                res.on('data', (chunk) => {
                    rawData += chunk;
             });

                res.on('end', () => {
                    try {
			const parsedData = JSON.parse(rawData);
			if (parsedData.length > 0) {
				msg.groupID = parsedData[0].id;
				node.send([msg, null]);
			}else{
				node.send([null, msg]);
			}
                    } catch (error) {
                        node.error(error);
                        node.send([null, error]);
                    }
                });
            });

            req.on('error', (error) => {
                node.warn(error);
                node.send([null, error]);
            });


            req.end();
        });
    }

    RED.nodes.registerType("does_group_exist", OktaGroupExistsNode);
};
