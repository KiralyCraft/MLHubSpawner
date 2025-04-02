class JupyterHubHTMLException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.jupyterhub_html_message = f"<p><h2>{message}</h2></p>"
