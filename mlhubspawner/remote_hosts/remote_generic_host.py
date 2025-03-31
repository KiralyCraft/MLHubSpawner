from traitlets.config import Configurable

from traitlets import  Unicode, Integer, Bool

class RemoteGenericHost(Configurable):
    # Define fields for a remote host.
    hostname = Unicode(help="The remote host address").tag(config=True)
    port = Integer(help="The port for the remote host").tag(config=True)
        
    # Total instances available for this configuration
    total_instances = Integer(help="Total instances available").tag(config=True)

    # Whether exclusive access is enabled (True/False)
    exclusive_access_enabled = Bool(help="Whether exclusive access is enabled").tag(config=True)