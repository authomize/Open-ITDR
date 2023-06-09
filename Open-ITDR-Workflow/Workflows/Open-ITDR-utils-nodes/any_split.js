module.exports = function(RED) {
  function AnySplitNode(config) {
    RED.nodes.createNode(this, config);
    var node = this;
    var property = config.property || "payload"; // Default property to split is "payload"

    node.on("input", function(msg) {
      if (msg.hasOwnProperty(property)) {
        var values = msg[property];
        if (!Array.isArray(values)) {
          values = [values];
        }
        values.forEach(function(value) {
          var newMsg = RED.util.cloneMessage(msg);
          newMsg[config.output_field_name] = value;
          node.send(newMsg);
        });
      } else {
        node.error("Property '" + property + "' not found in the message.");
      }
    });
  }

  RED.nodes.registerType("any_split", AnySplitNode);
};
