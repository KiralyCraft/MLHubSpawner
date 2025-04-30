import asyncssh
import random

class NotebookManager():
    def __init__(self, logger, launch_command: str, safe_username: str):
        self.notebook_launch_command = launch_command
        self.log = logger
        # These will be set upon a successful launch.
        self.pid = None
        self.port = None
        self.remote_ip = None
        self.host_port = None
        # The safe username is static, unique to this instance of the manager, and never changes. It's therefore safe to set it here, and just re-use it everywhere.
        self.safe_username = safe_username

    async def warmup_connection(self, host_ip: str, host_port: int, ssh_key_path: str):
        """
        Perform a simple SSH connection to trigger user creation on the backend.
        This warmup connection uses password authentication with a hardcoded password "password".
        The result is intentionally ignored.
        """
        self.log.info(f"Performing warmup connection to {host_ip}:{host_port} with user {self.safe_username}.")
        try:
            async with asyncssh.connect(
                host_ip,
                port=host_port,
                username=self.safe_username,
                password="password",  # hardcoded password for warmup
                known_hosts=None,
                connect_timeout=10
            ) as conn:
                # Run a simple echo command; the result is not used.
                await conn.run("echo warmup", check=False)
        except Exception as e:
            self.log.info(f"Warmup connection encountered an exception (expected if user is new): {e}")

    async def launch_notebook(self, jupyter_env: dict, hub_api_url: str, host_ip: str, host_port: str):

        notebook_jupyter_env = jupyter_env
        notebook_jupyter_env['JUPYTERHUB_API_URL'] = hub_api_url

        ssh_key_path = "~/.ssh/id_rsa"  # client key
        max_attempts = 3

        # Save connection info for later use.
        self.remote_ip = host_ip
        self.host_port = int(host_port)

        # Perform a preliminary warmup connection.
        await self.warmup_connection(host_ip, self.host_port, ssh_key_path)

        for attempt in range(max_attempts):
            random_port = random.randint(2000, 65535)
            self.log.info(f"Attempt {attempt+1}: Launching notebook on random port {random_port}.")

            # Build the bash script.
            bash_script_lines = ["#!/bin/bash"]
            for key, value in notebook_jupyter_env.items():
                bash_script_lines.append(f"export {key}='{value}'")
            bash_script_lines += [
                "unset XDG_RUNTIME_DIR",
                "touch .jupyter.log",
                "chmod 600 .jupyter.log",
                "run=true source initialSetup.sh >> .jupyter.log",
                f"{self.notebook_launch_command} --port {random_port} < /dev/null >> .jupyter.log 2>&1 & pid=$!",
                "echo $pid"
            ]
            bash_script_content = "\n".join(bash_script_lines)

            try:
                async with asyncssh.connect(
                    host_ip,
                    port=self.host_port,
                    username=self.safe_username,
                    client_keys=[ssh_key_path],
                    known_hosts=None,
                    connect_timeout=10
                ) as conn:
                    # Execute the constructed bash script.
                    result = await conn.run("bash -s", input=bash_script_content)

                stdout = result.stdout.strip() if result.stdout else ""
                stderr = result.stderr.strip() if result.stderr else ""
                return_code = result.exit_status

                if return_code == 0 and stdout:
                    try:
                        pid = int(stdout)
                        # Save the process ID and port for later operations.
                        self.pid = pid
                        self.port = random_port
                        self.log.info(f"Notebook launched successfully on port {random_port} with PID {pid}.")
                        return (random_port, pid)
                    except ValueError:
                        self.log.info(f"Attempt {attempt+1}: Unexpected output format '{stdout}'. Retrying with a new port...")
                else:
                    self.log.info(f"Attempt {attempt+1}: Error launching notebook on port {random_port}: "
                                  f"{stderr if stderr else 'No output'}. Retrying...")
            except Exception as e:
                self.log.info(f"Attempt {attempt+1}: Exception occurred: {e}. Retrying...")

        # If all attempts fail, return (None, None)
        self.log.info("All attempts to launch the notebook failed.")
        return (None, None)

    async def check_notebook_alive(self):
        """
        Check if the notebook process is running on the remote host by sending signal 0.
        """
        if not self.pid:
            self.log.info("No PID available to check. Notebook is not running.")
            return False

        ssh_key_path = "~/.ssh/id_rsa"

        command = f"kill -s 0 {self.pid} < /dev/null"
        try:
            async with asyncssh.connect(
                self.remote_ip,
                port=self.host_port,
                username=self.safe_username,
                client_keys=[ssh_key_path],
                known_hosts=None,
                connect_timeout=10
            ) as conn:
                result = await conn.run(command)
            alive = (result.exit_status == 0)
            self.log.info(f"Check notebook alive: PID {self.pid} is {'alive' if alive else 'dead'} (exit status {result.exit_status}).")
            return alive
        except Exception as e:
            self.log.info(f"Error checking notebook alive: {e}")
            return False

    async def kill_notebook(self):
        """
        Kill the notebook process on the remote host.
        """
        if not self.pid:
            self.log.info("No PID available to kill. Notebook is not running.")
            return False

        ssh_key_path = "~/.ssh/id_rsa"

        command = f"kill -9 {self.pid} < /dev/null"
        try:
            async with asyncssh.connect(
                self.remote_ip,
                port=self.host_port,
                username=self.safe_username,
                client_keys=[ssh_key_path],
                known_hosts=None,
                connect_timeout=10
            ) as conn:
                result = await conn.run(command)
            if result.exit_status == 0:
                self.log.info(f"Notebook with PID {self.pid} killed successfully.")
                self.pid = None  # Clear the stored PID since the process is terminated.
                return True
            else:
                self.log.info(f"Failed to kill notebook with PID {self.pid}. Exit status: {result.exit_status}")
                return False
        except Exception as e:
            self.log.info(f"Error killing notebook: {e}")
            return False


    def restore_state(self, pid: int, hostname: str, notebook_port: int):
        """
        Restore the last‐saved notebook process info so that future
        alive/poll/kill calls will work after a hub restart.
        - pid: the remote process ID
        - hostname: "ip:ssh_port" string you saved in spawner.state_hostname
        - notebook_port: the port the notebook is listening on
        """
        # If any of the required values are missing or falsy, bail out with a single error.
        if not all([pid, hostname, notebook_port]):
            self.log.info("Unable to restore state: pid, hostname, and notebook_port must all be non-empty.")
            return False

        # Parse out host IP and SSH port
        try:
            ip, ssh_port_str = hostname.split(":", 1)
            ssh_port = int(ssh_port_str)
        except Exception:
            self.log.info(f"Unable to restore state: invalid hostname format {hostname!r}.")
            return False

        # Stash them for later
        self.pid        = pid
        self.port       = notebook_port
        self.remote_ip  = ip
        self.host_port  = ssh_port

        # One-line info log, however long it gets
        self.log.info(f"Successfully restored notebook state: PID={self.pid}, notebook_port={self.port}, remote_ip={self.remote_ip}, ssh_port={self.host_port}")
        return True

