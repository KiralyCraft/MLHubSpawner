
# JupyterHub imports
from traitlets import List, Instance
from jupyterhub.spawner import Spawner

# Local imports
from .remote_hosts.remote_ml_host import RemoteMLHost
from .config_parsers import DictionaryInstanceParser
from .form_builder import JupyterFormBuilder
from .exceptions.jupyter_html_exception import JupyterHubHTMLException
from .state_manager import spawner_load_state, spawner_get_state, spawner_clear_state
from .account_manager import get_privilege, get_safe_username

# Python imports
import time

class MLHubSpawner(Spawner):

    # Remote hosts read from the configuration file
    remote_hosts = List(DictionaryInstanceParser(RemoteMLHost), help="Possible remote hosts from which to choose remote_host.", config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form_builder = JupyterFormBuilder()

        self.state_codename = None
        self.state_hostname = None


    #==== STARTING, STOPPPING, POLLING ====
    def __slowError(self, errorMessage):
        time.sleep(10) # Needed until https://github.com/jupyterhub/jupyterhub/pull/5020 is merged
        raise JupyterHubHTMLException(errorMessage) 

    async def start(self):
        starting_username = self.user.name
        safe_username = get_safe_username(starting_username)

        machine_select = self.user_options['machineSelect']
        exclusive_access_desired = self.user_options['exclusiveAccess']
        is_privileged = (get_privilege(starting_username) >= 1)

        if exclusive_access_desired == True and is_privileged == False:
            self.__slowError("Your account privilege does not allow for exclusive access to GPU machines.")
        
        #=== FIND MACHINE ===
        self.log.info("yeah" + safe_username)
        return ("0.0.0.0","3306")

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
        return self.form_builder.get_form_options(formdata)
