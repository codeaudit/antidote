from itertools import chain


class SlotReprMixin:
    __slots__ = ()

    def __repr__(self):
        slots = chain.from_iterable(getattr(cls, '__slots__', [])
                                    for cls in type(self).__mro__)
        return "{type}({slots})".format(
            type=type(self).__name__,
            slots=', '.join((
                '{}={!r}'.format(name, getattr(self, name))
                for name in slots
            ))
        )
