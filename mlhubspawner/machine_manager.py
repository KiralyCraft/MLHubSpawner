import socket
from typing import Any, Dict, List, Optional
from .remote_hosts.remote_generic_host import RemoteGenericHost

class MachineManager:
    def __init__(self, upstream_logger , remote_hosts: List[RemoteGenericHost]):
        self.upstream_logger = upstream_logger
        self.remote_hosts = remote_hosts
        # Maps unique_identifier -> allocation details
        self.allocations: Dict[str, Dict[str, Any]] = {}
        # Maps hostname -> list of unique_identifiers allocated to that hostname
        self.hostname_allocations: Dict[str, List[str]] = {}


    def is_machine_online(self, hostname_ip: str) -> bool:
        """
        Check if the machine at hostname_ip (format "ip:port") is online by trying to connect
        to the specified port with a 2-second timeout.
        """
        try:
            ip, port_str = hostname_ip.split(":")
            port = int(port_str)
            with socket.create_connection((ip, port), timeout=2):
                return True
        except Exception:
            return False

    def find_machine(self, chosen_machine_type: RemoteGenericHost, requested_shared_mode: bool) -> Optional[str]:
        """
        Return an available machine hostname for the given machine type and requested access mode.

        For an exclusive request (requested_shared_mode == False):
        - The machine is eligible if it is completely free (no allocations) and is online.

        For a shared request (requested_shared_mode == True):
        - The chosen machine type must support sharing.
        - A machine is eligible if it is online and none of its current allocations were taken exclusively.
        - Among eligible machines, the one with the fewest current allocations is returned,
            but if any eligible machine has zero allocations, it’s returned immediately.

        Note: This method must be called under an external mutex lock.
        """
        # If they asked for shared but the type doesn’t support it, bail out
        if requested_shared_mode and not chosen_machine_type.shared_access_enabled:
            self.upstream_logger.info("[MachineManager] Requested shared mode but machine type %s does not support shared access.", chosen_machine_type.codename)
            return None

        # Exclusive request: choose the first online host with zero allocations
        if not requested_shared_mode:
            for hostname in chosen_machine_type.hostnames:
                self.upstream_logger.info("[MachineManager] Attempting hostname: %s (type: %s)", hostname, chosen_machine_type.codename)
                if not self.is_machine_online(hostname):
                    self.upstream_logger.info("[MachineManager] Hostname %s is offline, skipping.", hostname)
                    continue
                allocs = self.hostname_allocations.get(hostname, [])
                self.upstream_logger.info("[MachineManager] %s allocation count: %d", hostname, len(allocs))
                if not allocs:
                    self.upstream_logger.info("[MachineManager] Hostname %s is free, selecting for exclusive allocation.", hostname)
                    return hostname
            self.upstream_logger.info("[MachineManager] No online, free hostname found for exclusive allocation for type %s.", chosen_machine_type.codename)
            return None

        # Shared request: prefer the first zero-allocation host, otherwise track the fewest
        selected_hostname = None
        for hostname in chosen_machine_type.hostnames:
            self.upstream_logger.info("[MachineManager] Attempting hostname: %s (type: %s)", hostname, chosen_machine_type.codename)
            if not self.is_machine_online(hostname):
                self.upstream_logger.info("[MachineManager] Hostname %s is offline, skipping.", hostname)
                continue
            allocs = self.hostname_allocations.get(hostname, [])
            self.upstream_logger.info("[MachineManager] %s allocation count: %d", hostname, len(allocs))
            # skip if any allocation was exclusive
            if any(not self.allocations[UID]['shared_access_enabled'] for UID in allocs):
                self.upstream_logger.info("[MachineManager] Exclusive allocation present on %s, skipping.", hostname)
                continue
            # immediate pick if free
            if not allocs:
                self.upstream_logger.info("[MachineManager] Hostname %s is free, selecting for shared allocation.", hostname)
                return hostname
            # otherwise pick the least-burdened so far
            if selected_hostname is None or len(allocs) < len(self.hostname_allocations[selected_hostname]):
                selected_hostname = hostname

        if selected_hostname:
            self.upstream_logger.info("[MachineManager] Selected hostname %s with allocation count %d for shared allocation.", selected_hostname, len(self.hostname_allocations[selected_hostname]))
            return selected_hostname

        self.upstream_logger.info("[MachineManager] No eligible hostname found for shared access for type %s.", chosen_machine_type.codename)
        return None


    def take_machine(self, chosen_machine_type: RemoteGenericHost, machine_ip_port: str, unique_identifier: str, requested_shared_mode: bool):
        """
        Reserve the machine (hostname) for the given unique identifier.
        
        For an exclusive request (requested_shared_mode == False):
          - The hostname must be completely free (no allocations).
        
        For a shared request (requested_shared_mode == True):
          - The chosen machine type must support sharing.
          - The hostname must not have any allocation that was taken exclusively.
        
        This function must be executed atomically (i.e. under an external mutex lock).
        """
        self.upstream_logger.info("[MachineManager] Attempting to take machine with codename %s, address %s, with UID %s (shared: %s)", 
                     chosen_machine_type.codename, machine_ip_port, unique_identifier, requested_shared_mode)

        if requested_shared_mode and not chosen_machine_type.shared_access_enabled:
            self.upstream_logger.info("[MachineManager] Machine type with codename %s does not support shared access for machine %s", 
                         chosen_machine_type.codename, machine_ip_port)
            return False

        if not requested_shared_mode:
            if machine_ip_port in self.hostname_allocations and self.hostname_allocations[machine_ip_port]:
                self.upstream_logger.info("[MachineManager] Machine %s (codename: %s) is already allocated exclusively. Cannot take machine.", 
                             machine_ip_port, chosen_machine_type.codename)
                return False
        else:
            uids = self.hostname_allocations.get(machine_ip_port, [])
            for uid in uids:
                if self.allocations[uid]['shared_access_enabled'] is False:
                    self.upstream_logger.info("[MachineManager] Machine %s (codename: %s) already has an exclusive allocation (UID: %s). Cannot share.", 
                                 machine_ip_port, chosen_machine_type.codename, uid)
                    return False

        # Register the allocation.
        self.allocations[unique_identifier] = {
            'machine': chosen_machine_type,
            'hostname': machine_ip_port,
            'shared_access_enabled': requested_shared_mode
        }

        if machine_ip_port not in self.hostname_allocations:
            self.hostname_allocations[machine_ip_port] = []
        self.hostname_allocations[machine_ip_port].append(unique_identifier)

        self.upstream_logger.info("[MachineManager] Successfully allocated machine %s (codename: %s) to UID %s. Current allocations:\n%s", 
                     machine_ip_port, chosen_machine_type.codename, unique_identifier,
                     "\n".join(str(uid) for uid in self.hostname_allocations[machine_ip_port]))
        return True

    def release_machine(self, unique_identifier: str):
        """
        Release the allocation associated with the given unique identifier.
        This method removes the allocation from both the allocations and the hostname_allocations dictionaries.
        """
        if unique_identifier not in self.allocations:
            self.upstream_logger.info("[MachineManager] Attempted to release non-existing allocation with UID %s", unique_identifier)
            return

        allocation = self.allocations[unique_identifier]
        hostname = allocation['hostname']
        codename = allocation['machine'].codename

        self.upstream_logger.info("[MachineManager] Releasing machine %s (codename: %s) allocated to UID %s", hostname, codename, unique_identifier)

        # Remove from the allocations dictionary.
        del self.allocations[unique_identifier]

        # Remove from the hostname_allocations dictionary.
        if hostname in self.hostname_allocations:
            if unique_identifier in self.hostname_allocations[hostname]:
                self.hostname_allocations[hostname].remove(unique_identifier)
                self.upstream_logger.info("[MachineManager] Removed UID %s from machine %s (codename: %s). Remaining allocations:\n%s", 
                             unique_identifier, hostname, codename,
                             "\n".join(str(uid) for uid in self.hostname_allocations[hostname]))
            if not self.hostname_allocations[hostname]:
                del self.hostname_allocations[hostname]
                self.upstream_logger.info("[MachineManager] No more allocations for machine %s (codename: %s). Hostname removed from records.", hostname, codename)

    def get_available_types(self, user_privilege_level: int) -> List[RemoteGenericHost]:
        """
        Return a list of remote host types available to a user with the given privilege level.
        Machine types that require privileged access are only included if the user has sufficient privileges.
        """
        available = []
        for host in self.remote_hosts:
            if host.privileged_access_required and user_privilege_level < 1:
                continue
            available.append(host)
        return available
