
# JupyterHub imports
from traitlets import List, Instance
from jupyterhub.spawner import Spawner

# Local imports
from .remote_hosts.remote_ml_host import RemoteMLHost
from .config_parsers import DictionaryInstanceParser
from .form_builder import JupyterFormBuilder

class MLHubSpawner(Spawner):

    # Remote hosts read from the configuration file
    remote_hosts = List(DictionaryInstanceParser(RemoteMLHost), help="Possible remote hosts from which to choose remote_host.", config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form_builder = JupyterFormBuilder()

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
            self.state_pid = state["pid"]
        if "remote_ip" in state:
            self.state_remote_ip = state["remote_ip"]

    # Retrieve the current state of the spawner as a dictionary.
    def get_state(self):
        state = super().get_state()
        if self.state_pid:
            state["pid"] = self.state_pid
        if self.state_remote_ip:
            state["remote_ip"] = self.state_remote_ip
        return state

    # Clear the spawner state, resetting remote IP and PID.
    def clear_state(self):
        super().clear_state()
        self.state_remote_ip = "remote_ip"
        self.state_pid = 0

    #==== FORM DATA ====
    def _options_form_default(self):
        localMachineDictionary = [host.toDictionary() for host in self.remote_hosts]
        return self.form_builder.get_html_page(localMachineDictionary)

    def options_from_form(self, formdata):
        pass