from ..._internal.utils import SlotsReprMixin


class Tag(SlotsReprMixin):
    """
    Tags are a way to expose a dependency indirectly. Instead of explicitly
    defining a list of dependencies to retrieve, one can just mark those with
    tags and retrieve them. This helps decoupling dependencies, and may be used
    to add extensions to another service typically.

    The tag itself has a name (string) attribute, with which it is identified.
    One may add others attributes to pass additional information to the services
    retrieving it.

    .. doctest::

        >>> from antidote import Tag
        >>> t = Tag('dep', info=1)
        >>> t.info
        1

    """
    __slots__ = ('name', '_attrs')

    def __init__(self, name: str, **attrs):
        """
        Args:
            name: Name which identifies the tag.
            **attrs: Any other parameters will be accessible as an attribute.
        """
        self.name = name
        self._attrs = attrs

    def __getattr__(self, item):
        return self._attrs.get(item)


class Tagged(SlotsReprMixin):
    """
    Custom dependency used to retrieve all dependencies tagged with by with the
    name.
    """
    __slots__ = ('name',)

    def __init__(self, name: str):
        """
        Args:
            name: Name of the tags which shall be retrieved.
        """
        self.name = name

    __str__ = SlotsReprMixin.__repr__

    def __hash__(self):
        return object.__hash__(self)

    def __eq__(self, other):
        return object.__eq__(self, other)
