class SlotReprMixin:
    __slots__ = ()

    def __repr__(self):
        return "{type}({slots})".format(
            type=type(self).__name__,
            slots=', '.join((
                '{}={!r}'.format(name, getattr(self, name))
                for name in self.__slots__
            ))
        )
