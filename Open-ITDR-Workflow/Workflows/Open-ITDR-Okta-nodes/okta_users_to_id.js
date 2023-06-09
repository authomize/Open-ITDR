module.exports = function(RED) {
    function okta_users_to_id_Node(config) {
        RED.nodes.createNode(this, config);
        var node = this;
        var results = [];
        
        node.on('input', async function(msg) {
            const https = require('https');

            const apiKey = msg.config.OktaKEY;
            const oktaDomain = msg.config.Domain;
            const emails = msg.emails;
            const options = {
                headers: {
                    Accept: 'application/json',
                    'Content-Type': 'application/json',
                    Authorization: 'SSWS ' + apiKey
                }
            };

            try {
                for (const email of emails) {
                    const url = 'https://' + oktaDomain + '.okta.com/api/v1/users?search=profile.email+eq+%22' + email + '%22';
                    const rawData = await new Promise((resolve, reject) => {
                        const req = https.get(url, options, (res) => {

                            let rawData = '';
                            res.on('data', (chunk) => {
                                rawData += chunk;
                            });

                            res.on('end', () => {
                                resolve(rawData);
                            });
                        });

                        req.on('error', (error) => {
                            reject(error);
                        });

                        req.end();
                    });

                    const parsedData = JSON.parse(rawData);
                    const userId = parsedData[0].id;
                    results.push(userId);
                }

                msg.users_id = results;
                node.send(msg);
            } catch (error) {
                node.error(error);
            }
        });
    }

    RED.nodes.registerType("okta_users_to_id", okta_users_to_id_Node);
};
