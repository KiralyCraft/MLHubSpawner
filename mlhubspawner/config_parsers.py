from traitlets import Instance

class DictionaryInstanceParser(Instance):
    """Custom Instance trait that converts dicts to DictionaryInstanceParser instances."""
    def validate(self, obj, value):
        # If a dict is provided, try to convert it into a DictionaryInstanceParser instance.
        if isinstance(value, dict):
            try:
                value = self.klass(**value)
            except Exception as e:
                raise TraitError(f"Could not convert dict to {self.klass}: {e}")
        return super().validate(obj, value)