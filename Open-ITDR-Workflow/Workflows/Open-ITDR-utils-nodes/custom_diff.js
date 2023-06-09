module.exports = function(RED) {
  function DiffNode(config) {
    RED.nodes.createNode(this, config);
    var node = this;

    node.on("input", function(msg) {
      var listA = msg[config.listA_name];
      var listB = msg[config.listB_name];


      if (!Array.isArray(listA) || !Array.isArray(listB)) {
        node.error("Input lists are not valid arrays.");
        return;
      }

      msg.create = [];
      msg.remove = [];
      var create = listA.filter(id => !listB.includes(id));
      var remove = listB.filter(id => !listA.includes(id));

      msg.create = Array.from(new Set(create));
      msg.remove = Array.from(new Set(remove));
      node.send(msg);
    });
  }

  RED.nodes.registerType("custom_diff", DiffNode);
};
