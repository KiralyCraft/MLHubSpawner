def spawner_load_state(spawner_self, state):
    """
    Load the spawner's state from a saved state dictionary.
    It sets the PID, remote IP, and hostname.
    Validates that the hostname is still valid,
    and if not, clears the state.
    """
    if "pid" in state:
        spawner_self.state_pid = state["pid"]
    if "hostname" in state:
        spawner_self.state_hostname = state["hostname"]
    if "notebook_port" in state:
        spawner_self.state_notebook_port = state["notebook_port"]

    # Only validate if both codename and hostname are present.
    if not spawner_self.state_hostname:
        spawner_clear_state(spawner_self)
        return

    valid = False
    for host in spawner_self.remote_hosts:
        if spawner_self.state_hostname in host.hostnames:
            valid = True
            break

    if not valid:
        spawner_clear_state(spawner_self)

def spawner_get_state(spawner_self):
    """
    Retrieve the current state from the spawner instance as a dictionary.
    """
    state = {}
    if spawner_self.state_pid:
        state["pid"] = spawner_self.state_pid
    if spawner_self.state_hostname:
        state["hostname"] = spawner_self.state_hostname
    if spawner_self.state_notebook_port:
        state["notebook_port"] = spawner_self.state_notebook_port
    return state

def spawner_clear_state(spawner_self):
    """
    Clear the spawner state, resetting remote IP, PID, codename, and hostname.
    """
    spawner_self.state_pid = 0
    spawner_self.state_hostname = None
    spawner_self.state_notebook_port = None
