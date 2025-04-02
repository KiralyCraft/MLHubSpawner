
# JupyterHub imports
from traitlets import List, Instance
from jupyterhub.spawner import Spawner

# Local imports
from .remote_hosts.remote_ml_host import RemoteMLHost
from .config_parsers import DictionaryInstanceParser
from .form_builder import JupyterFormBuilder
from .state_manager import spawner_load_state, spawner_get_state, spawner_clear_state

class MLHubSpawner(Spawner):

    # Remote hosts read from the configuration file
    remote_hosts = List(DictionaryInstanceParser(RemoteMLHost), help="Possible remote hosts from which to choose remote_host.", config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form_builder = JupyterFormBuilder()

    #==== STARTING, STOPPPING, POLLING ====
    async def start(self):
        self.log.info("Remote cmd: " + str(self.user_options))

    async def poll(self):
        pass

    async def stop(self):
        pass

    #==== STATE RESTORE ===

    # Load spawner state from a saved state dictionary.
    def load_state(self, state):
        super().load_state(state)
        spawner_load_state(self, state)

    # Retrieve the current state of the spawner as a dictionary.
    def get_state(self):
        state = super().get_state()
        state.update(spawner_get_state(self))
        return state

    # Clear the spawner state, resetting remote IP, PID, codename, and hostname.
    def clear_state(self):
        super().clear_state()
        spawner_clear_state(self)

    #==== FORM DATA ====

    # Return the actual HTML page for the form
    def _options_form_default(self):
        localMachineDictionary = [host.toDictionary() for host in self.remote_hosts]
        return self.form_builder.get_html_page(localMachineDictionary)

    # Parse the form data into the correct types. The values here are available in the "start" method as "self.user_options"
    def options_from_form(self, formdata):
        options = {}
        options['machineSelect'] = int(formdata['machineSelect'][0]) # The index of the remote_hosts machine
        return options