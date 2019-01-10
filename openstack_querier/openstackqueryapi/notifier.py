from oslo_config import cfg
import oslo_messaging

# Available notification list is given in: https://github.com/openstack/nova/blob/master/nova/rpc.py
class NotificationEndpoint(object):
    def __init__(self, event_type, publisher_id, callback):
        self.filter_rule = oslo_messaging.NotificationFilter(
            event_type=event_type,
            publisher_id=publisher_id)
        self.callback = callback # function is passed here and will be called upon occurence on an event defined in filter_rule

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        self.callback(event_type, payload)

class NotifierStarter(object):
    def __init__(self, transport_url):
        self.transport_url = transport_url

    def start(self, event_type, publisher_id, topic_names, callback):
        """

        :param event_type: regex (of full name ) for the events to register
        :param publisher_id:
        :param topic_names: one or more topics to subscribe. e.g. notifications, docker_notifications, etc...
        :param callback:
        :return:
        """
        transport = oslo_messaging.get_notification_transport(cfg.CONF, url=self.transport_url)
        targets = []
        for topic_name in topic_names:
            targets.append(oslo_messaging.Target(topic=topic_name))
        endpoints = [
            NotificationEndpoint(event_type=event_type, publisher_id=publisher_id, callback=callback)
        ]
        server = oslo_messaging.get_notification_listener(transport, targets,
                                                          endpoints, executor='threading')
        print('Starting server...')
        server.start()
        print('Started server...')
        server.wait()