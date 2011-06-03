__all__ = ['HeaderDict']


class HeaderDict(dict):
    """Class for representing a dictionary where keys are header names."""

    def __contains__(self, k):
        """Override dict.__contains__() to title-case keys."""

        return super(HeaderDict, self).__contains__(k.title())

    def __delitem__(self, k):
        """Override dict.__delitem__() to title-case keys."""

        return super(HeaderDict, self).__delitem__(k.title())

    def __init__(self, d=None, **kwargs):
        """Override dict.__init__() to title-case keys."""

        # Initialize ourself as if we were empty...
        super(HeaderDict, self).__init__()

        # Use our own update method
        self.update(d, **kwargs)

    def __getitem__(self, k):
        """Override dict.__getitem__() to title-case keys."""

        return super(HeaderDict, self).__getitem__(k.title())

    def __setitem__(self, k, v):
        """Override dict.__setitem__() to title-case keys."""

        return super(HeaderDict, self).__setitem__(k.title(), v)

    def copy(self):
        """Override dict.copy() to return a HeaderDict instance."""

        return self.__class__(self)

    @classmethod
    def fromkeys(cls, seq, v=None):
        """Override dict.fromkeys() to title-case keys."""

        return super(HeaderDict, cls).fromkeys(cls,
                                               [s.title() for s in seq], v)

    def get(self, k, d=None):
        """Override dict.get() to title-case keys."""

        return super(HeaderDict, self).get(k.title(), d)

    def has_key(self, k):
        """Override dict.has_key() to title-case keys."""

        return super(HeaderDict, self).has_key(k.title())

    def setdefault(self, k, d=None):
        """Override dict.setdefault() to title-case keys."""

        return super(HeaderDict, self).setdefault(k.title(), d)

    def update(self, e=None, **f):
        """Override dict.update() to title-case keys."""

        # Handle e first
        if e is not None:
            if hasattr(e, 'keys'):
                for k in e:
                    self[k.title()] = e[k]
            else:
                for (k, v) in e:
                    self[k.title()] = v

        # Now handle f
        if len(f):
            for k in f:
                self[k.title()] = f[k]
