def spawner_load_state(spawner_self, state):
    """
    Load the spawner's state from a saved state dictionary.
    It sets the PID, remote IP, codename, and hostname.
    Validates that the codename and hostname are still valid,
    and if not, clears the state.
    """
    if "pid" in state:
        spawner_self.state_pid = state["pid"]
    if "remote_ip" in state:
        spawner_self.state_remote_ip = state["remote_ip"]
    if "codename" in state:
        spawner_self.state_codename = state["codename"]
    if "hostname" in state:
        spawner_self.state_hostname = state["hostname"]

    # Validate that the saved codename and hostname are still valid.
    valid = False
    for host in spawner_self.remote_hosts:
        if host.codename == spawner_self.state_codename:
            if spawner_self.state_hostname in host.hostnames:
                valid = True
                break
    if not valid:
        SpawnerStateManager.clear_state(spawner_self)

def spawner_get_state(spawner_self):
    """
    Retrieve the current state from the spawner instance as a dictionary.
    """
    state = {}
    if spawner_self.state_pid:
        state["pid"] = spawner_self.state_pid
    if spawner_self.state_remote_ip:
        state["remote_ip"] = spawner_self.state_remote_ip
    if spawner_self.state_codename:
        state["codename"] = spawner_self.state_codename
    if spawner_self.state_hostname:
        state["hostname"] = spawner_self.state_hostname
    return state

def spawner_clear_state(spawner_self):
    """
    Clear the spawner state, resetting remote IP, PID, codename, and hostname.
    """
    spawner_self.state_remote_ip = "remote_ip"  # Retaining the default behavior.
    spawner_self.state_pid = 0
    spawner_self.state_codename = None
    spawner_self.state_hostname = None
