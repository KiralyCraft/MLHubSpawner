
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
from .machine_manager import MachineManager
from .notebook_manager import NotebookManager

# Python imports
import time

class MLHubSpawner(Spawner):

    # Remote hosts read from the configuration file. This is initialized per-instance!!
    remote_hosts = List(DictionaryInstanceParser(RemoteMLHost), help="Possible remote hosts from which to choose remote_host.", config=True)

    # Class-level MachineManager for load balancing
    _machine_manager = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #=== SINGLETONS ===
        cls = type(self)
        if cls._machine_manager is None:
            # Here, self.remote_hosts is fully initialized by traitlets.
            cls._machine_manager = MachineManager(self.remote_hosts)

        #=== NORMAL INIT ===

        self.form_builder = JupyterFormBuilder()
        self.notebook_manager = NotebookManager()

        self.state_pid = 0
        self.state_hostname = None
        self.state_notebook_port = None

        self.user_unique_identifier = self.user.name
        self.user_safe_username = get_safe_username(self.user.name) # This is already set here already
        self.user_privilege_level = get_privilege(self.user.name)

        self.machine_offers = {}

    #==== STARTING, STOPPPING, POLLING ====
    def __slowError(self, errorMessage : str):
        time.sleep(10) # Needed until https://github.com/jupyterhub/jupyterhub/pull/5020 is merged
        raise JupyterHubHTMLException(errorMessage) 

    async def start(self):

        selected_machine_index = self.user_options['machineSelect']
        shared_access_enabled = self.user_options['sharedAccess']

        chosen_machine_type = self.machine_offers[self.user_unique_identifier][selected_machine_index]
        is_privileged = (self.user_privilege_level >= 1)

        if shared_access_enabled == False and is_privileged == False:
            self.__slowError("Your account privilege does not allow for exclusive access to GPU machines.")
        
        #=== FIND MACHINE ===
        found_machine_ip_port = self.__class__._machine_manager.find_machine(chosen_machine_type, shared_access_enabled)

        if found_machine_ip_port == None:
            self.__slowError("We're sorry, but there is no available machine that meets your current requirements.")

        #=== RESERVE SPOT ===
        if not self.__class__._machine_manager.take_machine(chosen_machine_type, found_machine_ip_port, self.user_unique_identifier, shared_access_enabled):
            self.__slowError("We're sorry, but we were unable to reserve you a spot on your desired machine.")

        self.state_hostname = found_machine_ip_port

        #=== LAUNCH NOTEBOOK ===
        split_hostname = found_machine_ip_port.split(":")
        host_ip = split_hostname[0]
        host_port = split_hostname[1] 

        (notebook_port, notebook_pid) = self.notebook_manager.launch_notebook(host_ip, host_port, self.user_safe_username)

        if notebook_port == None or notebook_pid == None:
            self.__class__._machine_manager.release_machine(self.user_unique_identifier)
            self.__slowError("We're sorry, we were unable to launch your notebook instance. Your reserved spot was therefore released.")

        self.state_notebook_port = notebook_port
        self.state_pid = notebook_pid

        return (host_ip, notebook_port)

    async def poll(self):
        #=== NOT CONFIGURED ===
        if not self.state_pid or self.state_pid == 0:
            self.clear_state()
            return 0
        
        #=== NOTEBOOK DEAD ===
        notebook_alive = self.notebook_manager.check_notebook_alive()
        if not notebook_alive:
            return 0

        #=== ALL GOOD ===
        return None

    async def stop(self, now = False):
        #=== KILL THE NOTEBOOK ===
        self.notebook_manager.kill_notebook()

        #=== RELEASE THE SPOT ===
        self.__class__._machine_manager.release_machine(self.user_unique_identifier)
        self.clear_state()

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

    # Return the actual HTML page for the form. Only show users things they have access to.
    def _options_form_default(self):
        available_remote_hosts = self.__class__._machine_manager.get_available_types(self.user_privilege_level)

        self.machine_offers[self.user_unique_identifier] = available_remote_hosts

        available_remote_hosts_dictionary = [iterated_host.toDictionary() for iterated_host in available_remote_hosts]
        return self.form_builder.get_html_page(available_remote_hosts_dictionary)

    # Parse the form data into the correct types. The values here are available in the "start" method as "self.user_options"
    def options_from_form(self, formdata):
        return self.form_builder.get_form_options(formdata)

