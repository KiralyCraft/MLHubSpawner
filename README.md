# UBB's MLHub Spawner Plugin for JupyterHub (TLJH Variant)

This repository contains the source code for UBB's MLHub spawner plugin, designed for The Littlest JupyterHub (TLJH) variant. It enables machine learning users to access high-performance machines through JupyterHub, providing them with powerful computing resources tailored for ML workloads.

The machines need to also have 'jupyterlab' installed for this to work. 

TODO: Document more about the host setup

## Specific requirements

Since this spawner is closely integrated with MinIO, some specific setup is required for the authenticator. In this particular instance, authentication is done with OAuthenticator, and some fields are used internally, such as the `oid` field. For this reason, storing the full authentication data for users is required, using `c.OAuthenticator.enable_auth_state = True` in Jupyter's config file. 

## Features

- **High-Performance Access:**  
  Connect to remote machines equipped with advanced hardware (multiple GPUs, high core counts, large memory, etc.).

- **Tailored for Machine Learning:**  
  Designed specifically to meet the needs of ML users, allowing seamless integration of powerful compute resources into their JupyterHub experience.

## License

This project is licensed under the GNU General Public License v3 (GPLv3).
