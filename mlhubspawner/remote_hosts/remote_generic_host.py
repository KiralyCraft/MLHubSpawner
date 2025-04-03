from traitlets.config import Configurable
from traitlets import  Unicode, Integer, Bool, List
import json

class RemoteGenericHost(Configurable):
    # The codename for this machine. There can be multiple instances of this type.
    codename = Unicode(help="The unique codename for this machine").tag(config=True)

    # Define fields for a remote host.
    hostnames = List(Unicode(), help="List of hostnames where this machine type is available").tag(config=True, private_info = True)

    # Whether shared access is enabled (True/False)
    shared_access_enabled = Bool(help="Whether shared access is enabled").tag(config=True, private_info = True)


    # ==== METHODS ====

    def total_instances(self):
        return len(self.hostnames)

    # ====
    def toDictionary(self):
        # Iterate over all configurable traits and return a dict of name: value.
        data = {}
        for name, trait in self.traits(config=True).items():
            if not trait.metadata.get("private_info", False):
                data[name] = getattr(self, name)

        # Include metadata about the host here, such as the number of total instances
        data["total_instances"] = self.total_instances()

        return data

    def toJSON(self):
        # Return the JSON string representation of the dict.
        return json.dumps(self.toDictionary())