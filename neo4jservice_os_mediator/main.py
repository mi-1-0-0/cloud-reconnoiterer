import json
import re
import time
from multiprocessing import Pool

from graphelementsdispatcher.node_manager import NodeManager
from graphelementsdispatcher.relationship_manager import RelationshipManager
from openstackqueryapi import NotifierStarter
from osquerieshandler.osqueriers import *
from utils import *
from event_handlers import *

def prepare_node_data(data_list, node_type, label_key='name', id_key="id"):
    nodes = []
    for i in data_list:
        info = i if type(i) is dict else i.__dict__
        # label = info.pop(label_key, None)
        info['name'] = info[
            label_key]  # property with name 'name' is important for displaying (as a label on node) purpose
        del info[label_key]

        flatten_info_dict = get_flattened_dictionary(info)
        node = NodeManager.create_node(id_key, node_type, flatten_info_dict)
        nodes.append(node)
    return nodes

def create_containers_nodes(node_type, server_name_attr, cloud_config_info, private_keys_folder, nova_querier,
                            vm_username):
    ssh_cmd_executor = ShellCommandExecutor()
    # if not cloud_config_info["SERVERS"]["data"]:
    #     return
    command = "sudo docker ps --format \"{{json .}}\""

    for s in cloud_config_info["SERVERS"]["data"]:
        server_id = s.node_attributes.__dict__["id"]
        server = nova_querier.get_server(server_id)

        ip = server.addresses[list(server.addresses.keys())[0]][1]["addr"]
        private_key_path = os.path.join(private_keys_folder, server.user_id)
        if not os.path.exists(private_key_path):
            continue
        ssh_cmd_executor.connect(ip=ip, username=vm_username, private_key_file_path=private_key_path)

        stdin, stdout, stderr = ssh_cmd_executor.execute_command(command)
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
        nodes = prepare_node_data(data_list=containers_list, node_type=node_type, id_key="id")
        try:
            ssh_cmd_executor.close_connection()
        except:
            pass
        return nodes


def create_servers(node_type):
    prepare_node_data(data_list=novaQuerier.getServers(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_containers(node_type):
    create_containers_nodes(node_type=node_type,
                            server_name_attr=cloud_config_info["SERVERS"][
                                "name_attr"],
                            cloud_config_info=cloud_config_info,
                            private_keys_folder=PRIVATE_KEYS_FOLDER,
                            nova_querier=novaQuerier,
                            vm_username=VM_USERNAME)


def create_host_aggregates(node_type):
    prepare_node_data(data_list=novaQuerier.getHostAggregates(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_availability_zones(node_type):
    prepare_node_data(data_list=novaQuerier.getAvailabilityZones(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_services(node_type):
    prepare_node_data(data_list=novaQuerier.getServices(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_hypervisors(node_type):
    prepare_node_data(data_list=novaQuerier.getHypervisors(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_flavors(node_type):
    prepare_node_data(data_list=novaQuerier.getFlavors(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_volumes(node_type):
    prepare_node_data(data_list=cinderQuerier.getVolumes(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_key_pairs(node_type):
    prepare_node_data(data_list=novaQuerier.getKeyPairs(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_images(node_type):
    prepare_node_data(data_list=glanceQuerier.getImages(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_networks(node_type):
    prepare_node_data(data_list=neutronQuerier.getNetworks(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_subnets(node_type):
    prepare_node_data(data_list=neutronQuerier.getSubNets(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_routers(node_type):
    prepare_node_data(data_list=neutronQuerier.getRouters(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def create_users(node_type):
    prepare_node_data(data_list=keystoneQuerier.getUsers(),
                      node_type=node_type,
                      label_key=cloud_config_info[node_type]["name_attr"],
                      id_key=cloud_config_info[node_type]["id_key"])


def not_supported():
    raise Exception("Not supported yet.")


def create_graph_elements(element_type):
    switcher = {
        "SERVERS": create_servers,
        "HOST_AGGREGATES": create_host_aggregates,
        "AVAILABILITY_ZONES": create_availability_zones,
        "SERVICES": create_services,
        "HYPERVISORS": create_hypervisors,
        "FLAVORS": create_flavors,
        "VOLUMES": create_volumes,
        "KEY_PAIRS": create_key_pairs,
        "IMAGES": create_images,
        "NETWORKS": create_networks,
        "SUBNETS": create_subnets,
        "ROUTERS": create_routers,
        "CONTAINERS": create_containers,
        "USERS": create_users
    }
    func = switcher.get(element_type, lambda: not_supported)
    return func


def begin_node_create():
    nodes = list(cloud_config_info.keys())
    nodes.remove("CONTAINERS")

    for node_type in nodes:
        create_graph_elements(node_type)(node_type)

    # for container (because it depends on SERVERS)
    try:
        create_graph_elements("CONTAINERS")("CONTAINERS")
    except Exception as e:
        print("Exception occured: " + str(e))
        pass


def begin_relationship_create():
    for key in cloud_config_info:
        source_node_type = key
        relationship_infos = cloud_config_info[key]["RELATIONSHIPS"]
        for relationship_info in relationship_infos:
            source_property_name = relationship_info["source_property_name"]
            target_node_type = relationship_info["target_node_type"]
            target_property_name = relationship_info["target_property_name"]
            relationship_name = relationship_info["relationship_name"]
            relationship_properties = relationship_info["relationship_properties"]
            is_source_attr_name_regex = relationship_info["is_source_attr_name_regex"]  # todo: get rid of regexes

            ##todo: fetch data directly for this key from openstack
            data = list()

            for d in data:
                target_node_properties = {target_property_name: d[target_property_name]}
                if is_source_attr_name_regex:
                    source_property_names = list(filter(re.compile(source_property_name).match,
                                              d.node_attributes.__dict__.keys()))

                    for property_name in source_property_names:
                        source_node_properties = {property_name: d[property_name]}
                        RelationshipManager.create_relationship(source_node_type=source_node_type,
                                                                source_node_properties=source_node_properties,
                                                                target_node_type=target_node_type,
                                                                target_node_properties=target_node_properties,
                                                                relationship=relationship_name,
                                                                relationship_properties=relationship_properties)
                else:
                    source_node_properties = {source_property_name: d[source_property_name]}
                    RelationshipManager.create_relationship(source_node_type=source_node_type,
                                                            source_node_properties=source_node_properties,
                                                            target_node_type=target_node_type,
                                                            target_node_properties=target_node_properties,
                                                            relationship=relationship_name,
                                                            relationship_properties=relationship_properties)


def begin_all():
    try:
        begin_node_create()
        # if node creation is asynch, then wait until all nodes are created.
        begin_relationship_create()
    except Exception as e:
        print("Exception occured: " + str(e))
        pass

def main():
    notifier = NotifierStarter(transport_url=NOTIFICATION_TRANSPORT_URL)
    notifier.start(NOTIFICATION_EVENT_TYPE, NOTIFICATION_PUBLISHER_ID, NOTIFICATION_TOPIC_NAME, notifier_callback)
    begin_all()

    ## the following code is commenting only for dev env
    # pool = Pool(processes=2)#todo: get from env
    # pool.apply_async(notifier.start,
    #                  [NOTIFICATION_EVENT_TYPE, NOTIFICATION_PUBLISHER_ID, NOTIFICATION_TOPIC_NAME, notifier_callback],
    #                  notifier_callback)  # callback is none
    # while True:
    #     # check every TIME_TO_WAIT minutes for the changes (in case notifications are not appearing. but as soon as notifcation appears it will immediatly update graph again.)
    #     time.sleep(int(TIME_TO_WAIT))
    #     begin_all()


if __name__ == '__main__':
    NodeManager.NEO4J_SERVICE_URL = RelationshipManager.NEO4J_SERVICE_URL = NEO4J_SERVICE_URL
    configuratons = json.loads(open(CONFIG_FILE_PATH).read())
    cloud_provider = configuratons["cloud_provider"] ##todo: use this to import modules relevant to the cloud type
    cloud_config_info = configuratons["cloud_config_info"]
    main()