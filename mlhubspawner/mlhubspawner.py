
# JupyterHub imports
from traitlets import List, Instance
from jupyterhub.spawner import Spawner

# Local imports
from remote_hosts.remote_ml_host import RemoteMLHost
from config_parsers import DictionaryInstanceParser


class MLHubSpawner(Spawner):


    def __init__(self):
        pass

    # Remote hosts read from the configuration file
    remote_hosts = List(DictionaryInstanceParser(RemoteMLHost), help="Possible remote hosts from which to choose remote_host.", config=True)

    #==== STARTING, STOPPPING, POLLING ====
    async def start(self):
        pass

    async def poll(self):
        pass

    async def stop(self):
        pass

    #==== STATE RESTORE ===

    # Load spawner state from a saved state dictionary.
    def load_state(self, state):
        super().load_state(state)
        if "pid" in state:
            self.pid = state["pid"]
        if "remote_ip" in state:
            self.remote_ip = state["remote_ip"]

    # Retrieve the current state of the spawner as a dictionary.
    def get_state(self):
        state = super().get_state()
        if self.pid:
            state["pid"] = self.pid
        if self.remote_ip:
            state["remote_ip"] = self.remote_ip
        return state

    # Clear the spawner state, resetting remote IP and PID.
    def clear_state(self):
        super().clear_state()
        self.remote_ip = "remote_ip"
        self.pid = 0

    