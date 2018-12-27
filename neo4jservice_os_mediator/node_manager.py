from flatten_json import flatten
from graphserviceschema.serviceschema import *
from mediator.caller import *
from openstackqueryapi.queryos import CustomVirtualMachineQuerier
import json
import os


class NodeManager(object):
    NEO4J_SERVICE_URL = ""
    NEO4J_SERVICE_GET_ALL_RELATIVE_PATH = "/nodes/get_all"
    NEO4J_SERVICE_GET_NODE_RELATIVE_PATH = "/nodes/get_node"
    NEO4J_SERVICE_CREATE_NODE_RELATIVE_PATH = "/nodes/create_node"
    NEO4J_SERVICE_DELETE_NODE_RELATIVE_PATH = "/nodes/delete_node"
    NEO4J_SERVICE_DELETE_GRAPH_RELATIVE_PATH = "/delete_graph"

    vmSshQuerier = CustomVirtualMachineQuerier()

    @classmethod
    def create_node(self, id_key, node_type, node_attrributtes_dict):
        node_attributes = NodeAttributes(node_attrributtes_dict)
        node = Node(id_key=id_key, node_type=node_type, node_attributes=node_attributes)
        data = node.toJSON()
        callServicePost(url=NodeManager.NEO4J_SERVICE_URL + NodeManager.NEO4J_SERVICE_CREATE_NODE_RELATIVE_PATH,
                        data=data.replace("\n", ""))
        return node

    @classmethod
    def prepare_node_data(self, data_list, node_type, id_key="id"):
        nodes = []
        for i in data_list:
            info = i if type(i) is dict else i.__dict__
            # label = info.pop(label_key, None)
            flatten_info_dict = flatten(info, separator="___")
            node = NodeManager.create_node(id_key, node_type, flatten_info_dict)
            nodes.append(node)
        return nodes

    @classmethod
    def create_containers_nodes(self, node_type, server_name_attr, openstack_info, private_keys_folder, nova_querier,
                                vm_username):
        if not openstack_info["SERVERS"]["data"]:
            return
        command = "sudo docker ps --format \"{{json .}}\""
        for s in openstack_info["SERVERS"]["data"]:
            server_id = s.node_attributes.__dict__["id"]
            server = nova_querier.getServer(server_id)  # TODO: MOVE IT TO main.py

            ip = server.addresses[list(server.addresses.keys())[0]][1]["addr"]
            private_key_path = os.path.join(private_keys_folder, server.user_id)
            if not os.path.exists(private_key_path):
                continue
            self.vmSshQuerier.connect(ip=ip, username=vm_username, private_key_file_path=private_key_path)

            stdin, stdout, stderr = self.vmSshQuerier.executeCommandOnVM(command)
            containers_string_info = stdout.readlines()
            containers_list = []
            for c in containers_string_info:
                container_info_dict = {}
                container_info = json.loads(c)
                container_info_dict["id"] = container_info["ID"]
                container_info_dict["container_name"] = container_info["Names"]
                container_info_dict["name"] = container_info["Image"]
                container_info_dict["ports"] = container_info["Ports"]
                container_info_dict["networks"] = container_info["Networks"]
                container_info_dict["mounts"] = container_info["Mounts"]
                container_info_dict["server_name"] = s.node_attributes.__dict__[server_name_attr]
                container_info_dict["server_id"] = server_id
                containers_list.append(container_info_dict)
            nodes = NodeManager.prepare_node_data(data_list=containers_list, node_type=node_type, id_key="id")
            try:
                self.vmSshQuerier.closeConnection()
            except:
                pass
            return nodes

    @classmethod
    def delete_node(cls, node_type, query_attribute, query_attribute_value):
        data = {'node_type': node_type, 'query_attribute': query_attribute,
                'query_attribute_value': query_attribute_value}
        callServicePost(url=NodeManager.NEO4J_SERVICE_URL + NodeManager.NEO4J_SERVICE_DELETE_NODE_RELATIVE_PATH,
                        data=json.dumps(data))

    @classmethod
    def update_node(cls, node_type, query_attribute, query_attribute_value):
        data = {'node_type': node_type, 'query_attribute': query_attribute,
                'query_attribute_value': query_attribute_value}
        callServicePost(url=NodeManager.NEO4J_SERVICE_URL + NodeManager.NEO4J_SERVICE_DELETE_NODE_RELATIVE_PATH,
                        data=json.dumps(data))

    @classmethod
    def get_node(cls, node_type, query_attribute, query_attribute_value):
        data = {'node_type': node_type, 'node_query_attr': query_attribute,
                'query_attribute_value': query_attribute_value}
        callServicePost(url=NodeManager.NEO4J_SERVICE_URL + NodeManager.NEO4J_SERVICE_GET_NODE_RELATIVE_PATH,
                        data=json.dumps(data))

    @classmethod
    def get_all_nodes(cls):
        callServiceGet(url=NodeManager.NEO4J_SERVICE_URL + NodeManager.NEO4J_SERVICE_GET_ALL_RELATIVE_PATH)

    @classmethod
    def delete_graph(cls):
        callServiceGet(url=NodeManager.NEO4J_SERVICE_URL + NodeManager.NEO4J_SERVICE_DELETE_GRAPH_RELATIVE_PATH)