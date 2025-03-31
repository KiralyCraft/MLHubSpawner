from traitlets.config import Configurable
from traitlets import  Unicode, Integer, Bool
import json

class RemoteGenericHost(Configurable):
    # Define fields for a remote host.
    hostname = Unicode(help="The remote host address").tag(config=True)
    port = Integer(help="The port for the remote host").tag(config=True)
        
    # Total instances available for this configuration
    total_instances = Integer(help="Total instances available").tag(config=True)

    # Whether exclusive access is enabled (True/False)
    exclusive_access_enabled = Bool(help="Whether exclusive access is enabled").tag(config=True)

    def toDictionary(self):
        # Iterate over all configurable traits and return a dict of name: value.
        data = {}
        for name, trait in self.traits(config=True).items():
            data[name] = getattr(self, name)
        return data

    def toJSON(self):
        # Return the JSON string representation of the dict.
        return json.dumps(self.toDictionary())