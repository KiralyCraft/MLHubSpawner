from traitlets.config import Configurable
from traitlets import  Unicode, Integer, Bool, List
import json

class RemoteGenericHost(Configurable):
    # The codename for this machine. There can be multiple instances of this type.
    codename = Unicode(help="The unique codename for this machine").tag(config=True)

    # Define fields for a remote host.
    hostnames = List(Unicode(), help="List of hostnames where this machine type is available").tag(config=True)
    port = Integer(help="The port for the remote host").tag(config=True)

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