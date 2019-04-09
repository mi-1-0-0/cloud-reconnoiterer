import re
import os
import node_data_assembler
from graphelementsdispatcher.node_manager import NodeManager
from graphelementsdispatcher.relationship_manager import *
import envvars
from logging_config import Logger

logger = Logger(log_file_path=envvars.LOGS_FILE_PATH, log_level=envvars.LOG_LEVEL, logger_name=os.path.basename(__file__)).logger

def begin_node_create(cloud_config_info):
    nodes = list(cloud_config_info.keys())
    container_key_name = "CONTAINERS"
    nodes.remove(container_key_name)
    # list is ordered in python. so remove key for 'containers' if it is somewhere else and append it at the end, so we can be sured that the container creation code is executed after servers creation code (because containers depend on servers)
    nodes.append(container_key_name)

    for node_type in nodes:
        try:
            logger.info("Creating node %s" % node_type)
            function_name = "".join(["create_", node_type])
            function_to_call = getattr(node_data_assembler, function_name.lower())
            try:
                logger.debug("Calling function %s" % function_to_call)
                # todo: pass parameters as either dict or args and kwargs, because create_container  function accepts different parameters
                function_to_call(node_type=node_type,
                                 node_secondary_labels=cloud_config_info[node_type]['node_secondary_labels'],
                                 label_key=cloud_config_info[node_type]['name_attr'],
                                 id_key=cloud_config_info[node_type][
                                     'id_key'])
            except Exception as ex:
                logger.error("Exception occurred: %s" % str(ex))
        except Exception as ex:
            logger.error("Exception occurred: %s" % str(ex))


def begin_relationship_create(cloud_config_info):
    for source_node_type in cloud_config_info:
        logger.debug("Starting to create relationships for node: %s" % source_node_type)
        relationship_data = cloud_config_info[source_node_type]["RELATIONSHIPS"]
        for relationship_data in relationship_data:
            logger.debug("Getting relationship properties for source node: %s" % source_node_type)
            source_property_name = relationship_data["source_property_name"]
            target_property_name = relationship_data["target_property_name"]
            is_source_attr_name_regex = relationship_data["is_source_attr_name_regex"]

            del relationship_data["is_source_attr_name_regex"]
            del relationship_data["source_property_name"]
            del relationship_data["target_property_name"]

            relationship_data["source_node_type"] = source_node_type
            try:
                query_parameters = {}
                query_parameters["node_type"] = source_node_type
                logger.debug("Fetching information from graph for node {0}".format(source_node_type))
                node_data = NodeManager.get_nodes(query_parameters)  # fetch data directly for this key from graph
                logger.debug("Fetched information from graph for node {0}".format(source_node_type))
            except Exception as ex:
                logger.error("Could not fetch data for {0} . Exception occured: {1}.".format(source_node_type, str(ex)))
            else:
                for datum in node_data:
                    try:
                        if is_source_attr_name_regex:
                            source_property_names = list(filter(re.compile(source_property_name).match,
                                                                datum.keys()))
                            source_node_properties = {}
                            for property_name in source_property_names:
                                source_node_properties[property_name] = datum[property_name]
                                relationship_data["source_node_properties"] = source_node_properties

                                target_node_properties = {target_property_name: datum[property_name]}
                                relationship_data["target_node_properties"] = target_node_properties

                                logger.info("Creating relationship for nodes {0} and {1}".format(source_node_type,
                                            target_property_name))
                                RelationshipManager.create_relationship(relationship_data)
                        else:
                            target_node_properties = {target_property_name: datum[source_property_name]}
                            relationship_data["target_node_properties"] = target_node_properties

                            source_node_properties = {source_property_name: datum[source_property_name]}
                            relationship_data["source_node_properties"] = source_node_properties

                            logger.info("Creating relationship for nodes {0} and {1}".format(source_node_type,
                                        target_property_name))
                            RelationshipManager.create_relationship(relationship_data)
                    except Exception as ex:
                        logger.error("Exception occurred: %s" % str(ex))