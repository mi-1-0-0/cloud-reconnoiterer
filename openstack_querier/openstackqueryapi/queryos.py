from keystoneauth1 import loading, session
import paramiko

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

class OpenstackConnector(object):
    def __init__(self, auth_url, username, password, project_name, os_user_domain_name="Default",
                 os_project_domain_id="default", api_version="2", loader_option="password"):
        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.project_name = project_name
        self.project_domain_id = os_project_domain_id
        self.user_domain_name = os_user_domain_name
        self.api_version = api_version
        self.loader_option=loader_option  #for loader_option other than password or v3password, different parameters might be needed

    def get_session(self):
        loader = loading.get_plugin_loader(self.loader_option)
        auth = loader.load_from_options(auth_url=self.auth_url,
                                        username=self.username,
                                        password=self.password,
                                        project_name=self.project_name,
                                        user_domain_name=self.user_domain_name,
                                        project_domain_id=self.project_domain_id
                                        )
        sess = session.Session(auth=auth)
        return sess

class NovaQuerier(object):
    def __init__(self, os_connector):
        self.nova = None
        self.os_connector = os_connector

    def connect(self):
        from novaclient.v2 import client
        sess=self.os_connector.get_session()
        self.nova = client.client.Client(version=self.os_connector.api_version, session=sess)

    def get_flavors(self):
        flavors_list = self.nova.flavors.list()
        return flavors_list

    def get_host_aggregates(self):
        host_aggregates_list = self.nova.aggregates.list()
        return host_aggregates_list

    def get_services(self, id):
        services_list = self.nova.services.list()
        return services_list

    def get_hypervisors(self):
        hypervisors_list = self.nova.hypervisors.list()
        return hypervisors_list

    def get_servers(self):
        servers_list = self.nova.servers.list(search_opts={'all_tenants': 1})
        return servers_list

    def get_availability_zones(self):
        availability_zones = self.nova.availability_zones.list()
        return availability_zones

    def get_key_pairs(self):
        keypairs_list = self.nova.keypairs.list()
        return keypairs_list

    def get_server(self, id):
        return self.nova.servers.get(id)

class NeutronQuerier(object):
    def __init__(self, os_connector):
        self.neutron = None
        self.os_connector = os_connector

    def connect(self):
        from neutronclient.v2_0 import client as neutronclient
        sess = self.os_connector.get_session()
        self.neutron = neutronclient.Client(session=sess)

    def get_networks(self):
        networks = self.neutron.list_networks()["networks"]
        return networks

    def get_subnets(self):
        subnets = self.neutron.list_subnets()["subnets"]
        return subnets

    def get_routers(self):
        routers = self.neutron.list_routers()["routers"]
        return routers

class GlanceQuerier(object):
    def __init__(self, os_connector):
        self.glance = None
        self.os_connector = os_connector

    def connect(self):
        import glanceclient
        sess = self.os_connector.get_session()
        self.glance = glanceclient.Client('2', session=sess)

    def get_images(self):
        images_list=[]
        for img in self.glance.images.list():
            images_list.append(img.__dict__["__original__"])
        return images_list

    def get_image_members(self, image_id):
        image_members_list = self.glance.image_members.list(image_id)
        return image_members_list

class KeystoneQuerier(object):
    def __init__(self, os_connector):
        self.keystone = None
        self.os_connector = os_connector

    def connect(self):
        from keystoneclient.v3 import client as keystoneclient
        sess = self.os_connector.get_session()
        self.keystone = keystoneclient.Client(session=sess)

    def get_users(self):
        users_list = self.keystone.users.list()
        return users_list

    def get_services(self):
        services_list = self.keystone.services.list()
        return services_list

    def get_tenants(self):
        tenants_list = self.keystone.tenants.list()
        return tenants_list

    def get_roles(self):
        roles_list = self.keystone.roles.list()
        return roles_list

class CinderQuerier(object):
    def __init__(self, os_connector):
        self.cinder = None
        self.os_connector = os_connector

    def connect(self):
        import cinderclient.v2
        sess = self.os_connector.get_session()
        self.cinder = cinderclient.v2.Client(session=sess)

    def get_volumes(self):
        volumes_list = self.cinder.volumes.list()
        return volumes_list

class ManilaQuerier(object):
    def __init__(self, os_connector):
        self.manila = None
        self.os_connector = os_connector

    def connect(self):
        import manilaclient.v2
        sess = self.os_connector.get_session()
        self.manila = manilaclient.v2.client.Client('2', session=sess)

class IronicQuerier(object):
    def __init__(self, os_connector):
        self.ironic = None
        self.os_connector = os_connector

    def connect(self):
        import ironicclient.v1.client
        sess = self.os_connector.get_session()
        self.ironic = ironicclient.v1.client.Client('1', session=sess)

class SwiftQuerier(object):
    def __init__(self, os_connector):
        self.swift = None
        self.os_connector = os_connector

    def connect(self):
        import swiftclient
        sess = self.os_connector.get_session()
        self.swift = swiftclient.client.Connection(session=sess)

class ShellCommandExecutor(object):
    def __init__(self):
        self.ssh = None

    def connect(self, ip, username, private_key_file_path):
        key = paramiko.RSAKey.from_private_key_file(private_key_file_path)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=ip, username=username, pkey=key, timeout=15)

    def execute_command(self, command):
        stdin, stdout, stderr = self.ssh.exec_command(command)
        return stdin, stdout, stderr

    def close_connection(self):
        self.ssh.close()