# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False, annotation_typing=False

# @formatter:off
cimport cython
from cpython.dict cimport PyDict_Contains, PyDict_Copy, PyDict_SetItem
from libcpp cimport bool as cbool

# noinspection PyUnresolvedReferences
from ..container cimport DependencyContainer, DependencyContainer, Instance
from ..exceptions import DependencyNotFoundError
# @formatter:on


cdef class InjectionBlueprint:
    cdef:
        tuple injections

    def __init__(self, tuple injections):
        self.injections = injections

@cython.freelist(5)
cdef class Injection:
    cdef:
        readonly str arg_name
        readonly cbool required
        readonly object dependency_id

    def __repr__(self):
        return "{}(arg_name={!r}, required={!r}, dependency_id={!r})".format(
            type(self).__name__,
            self.arg_name,
            self.required,
            self.dependency_id
        )

    def __init__(self, str arg_name, cbool required, object dependency_id):
        self.arg_name = arg_name
        self.required = required
        self.dependency_id = dependency_id

cdef class InjectedCallableWrapper:
    cdef:
        public __module__
        public __name__
        public __qualname__
        public __doc__
        public __annotations__
        object __wrapped
        DependencyContainer __container
        InjectionBlueprint __blueprint
        int __injection_offset

    def __init__(self,
                 DependencyContainer container,
                 InjectionBlueprint blueprint,
                 object wrapped,
                 cbool skip_self = False):
        self.__container = container
        self.__wrapped = wrapped
        self.__blueprint = blueprint
        self.__injection_offset = 1 if skip_self else 0

    def __call__(self, *args, **kwargs):
        kwargs = _inject_kwargs(
            self.__container,
            self.__blueprint,
            self.__injection_offset + len(args),
            kwargs
        )
        return self.__wrapped(*args, **kwargs)

    def __get__(self, instance, owner):
        skip_self = instance is not None
        func = self.__wrapped.__get__(instance, owner)
        return InjectedBoundCallableWrapper(self.__container, self.__blueprint,
                                            func, skip_self=skip_self)

cdef class InjectedBoundCallableWrapper(InjectedCallableWrapper):
    def __get__(self, instance, owner):
        return self

cdef dict _inject_kwargs(DependencyContainer container,
                         InjectionBlueprint blueprint,
                         int offset,
                         dict kwargs):
    cdef:
        Injection injection
        object instance
        cbool dirty_kwargs = False
        int i

    for i in range(offset, len(blueprint.injections)):
        injection = blueprint.injections[i]
        if injection.dependency_id is not None \
                and PyDict_Contains(kwargs, injection.arg_name) == 0:
            instance = container.provide(injection.dependency_id)
            if instance is not container.SENTINEL:
                if not dirty_kwargs:
                    kwargs = PyDict_Copy(kwargs)
                    dirty_kwargs = True
                PyDict_SetItem(kwargs, injection.arg_name, <object> instance)
            elif injection.required:
                raise DependencyNotFoundError(injection.dependency_id)

    return kwargs
