
class DotDict(dict):
    """
    DotDict is a Dictionary with dot notation in the keys. 

    Example:

        >>> foo = DotDict()
        >>> foo["this.is.a.test"] = "bar"
        >>> foo
        {'this.is.a.test': 'bar'}

        >>> foo["this"]
        {'is.a.test': 'bar'}

        >>> foo["this.is"]
        {'a.test': 'bar'}

        >>> foo["this.is.a.test"]
        'bar'

    Internally, every dot stands for a new dictionary. The foo DotDict actually looks as follows:

        {
            "this": {
                "is": {
                    "a": {
                        "test": "bar"
                    }
                }
            }
        }
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # now we update every value that is a dict
        for k, v in super().items():
            if type(v) is dict:
                v = DotDict(v)
                self[k] = v

    @staticmethod
    def _get_subkeys(key, required=True):
        if type(key) is not str:
            raise KeyError("Keys must be strings in DotDict.")

        subitems = key.split(".", 1)

        if required and len(subitems) == 0:
            raise KeyError("A key must be specified")

        return subitems

    def __setitem__(self, key, value):
        subkeys = self._get_subkeys(key)

        if len(subkeys) == 1:
            super().__setitem__(subkeys[0], value)
        else:
            child_dotdict = super().setdefault(subkeys[0], DotDict())

            if type(child_dotdict) != DotDict:
                child_dotdict = DotDict()
                super().__setitem__(subkeys[0], child_dotdict)

            child_dotdict[subkeys[1]] = value

    def setdefault(self, key, default=None):
        try:
            result = self[key]
        except KeyError:
            result = default
            self[key] = result

        return result

    def __getitem__(self, key):
        subkeys = self._get_subkeys(key)

        result = super().__getitem__(subkeys[0])

        if len(subkeys) == 2:
            result = result[subkeys[1]]

        return result

    def __delitem__(self, key):
        subkeys = self._get_subkeys(key)

        if len(subkeys) == 1:
            super().__delitem__(subkeys[0])
        else:
            self[subkeys[0]].__delitem__(subkeys[1])

    def __contains__(self, key):
        subkeys = self._get_subkeys(key, required=False)

        result = len(subkeys) > 0 and super().__contains__(subkeys[0])

        if len(subkeys) == 2:
            result = result and self[subkeys[0]].__contains__(subkeys[1])

        return result

    def get(self, key, default_value=None):
        try:
            result = self[key]
        except KeyError:
            result = default_value

        return result

    def _flatkeys(self):

        keys = []

        for k, v in super().items():
            if type(v) is DotDict:
                subkeys = v._flatkeys()
                keys.extend([f"{k}.{sk}" for sk in subkeys])
            else:
                keys.append(k)

        return keys

    def keys(self):
        yield from self._flatkeys()

    def values(self):
        for k in self.keys():
            yield self[k]

    def __iter__(self):
        yield from self.keys()

    def items(self):
        for k in self:
            yield k, self[k]

    def to_dict(self):
        """
        Converts this instance into a normal dictionary.
        :return: normal nested dictionary
        """
        return {k: (v if type(v) is not DotDict else v.to_dict()) for k, v in super().items()}
