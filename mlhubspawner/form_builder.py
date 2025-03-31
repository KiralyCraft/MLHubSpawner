import json
import os

try:
    import pkg_resources
except ImportError:
    pkg_resources = None

class JupyterFormBuilder():
    def __init__(self):
        # Read the default template for the form
        if pkg_resources is not None:
            try:
                resource_path = pkg_resources.resource_filename('mlhubspawner', 'resources/form.html')
                with open(resource_path, 'r') as file:
                    self.form_html_content = file.read()
            except Exception as e:
                self.form_html_content = f"FORM_TEMPLATE_ERROR: {e}"
        else:
            # When pkg_resources is not available, assume that the 'resources' folder
            # is in the same directory as this file.
            try:
                resource_path = os.path.join(os.path.dirname(__file__), 'resources', 'form.html')
                with open(resource_path, 'r') as file:
                    self.form_html_content = file.read()
            except Exception as e:
                self.form_html_content = f"FORM_TEMPLATE_ERROR (local): {e}"

    def get_html_page(self, dicitonaryList):
        jsonDictionary = json.dumps(dicitonaryList)
        return self.form_html_content.replace("{machineData}",jsonDictionary)