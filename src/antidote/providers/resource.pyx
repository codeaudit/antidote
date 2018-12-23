# cython: language_level=3, language=c++
# cython: boundscheck=False, wraparound=False
# cython: linetrace=True
import bisect
import re
from typing import Any, Callable, Dict, List

# @formatter:off
from libcpp cimport bool as cbool

# noinspection PyUnresolvedReferences
from ..container cimport Dependency, Instance, Provider
from ..exceptions import GetterPriorityConflict
# @formatter:on


cdef class ResourceProvider(Provider):
    def __init__(self):
        self._priority_sorted_getters_by_namespace = dict()  # type: Dict[str, List[ResourceGetter]]  # noqa

    def __repr__(self):
        return "{}(getters={!r})".format(type(self).__name__,
                                         self._priority_sorted_getters_by_namespace)

    cpdef Instance provide(self, Dependency dependency):
        cdef:
            ResourceGetter getter
            object resource
            str namespace_
            str resource_name
            list getters

        if isinstance(dependency.id, str) and ':' in dependency.id:
            namespace_, resource_name = dependency.id.split(':', 1)
            getters = self._priority_sorted_getters_by_namespace.get(namespace_)
            if getters is not None:
                for getter in getters:
                    try:
                        resource = getter.get(resource_name)
                    except LookupError:
                        pass
                    else:
                        return Instance(resource, singleton=getter.singleton)

    def register(self,
                 resource_getter: Callable[[str], Any],
                 str namespace,
                 float priority = 0,
                 cbool omit_namespace = True,
                 cbool singleton = True):
        if not isinstance(namespace, str):
            raise ValueError(
                "namespace must be a string, not a {!r}".format(type(namespace))
            )
        elif not re.match(r'^\w+$', namespace):
            raise ValueError("namespace can only contain characters in [a-zA-Z0-9_]")

        if not isinstance(priority, (int, float)):
            raise ValueError(
                "priority must be a number, not a {!r}".format(type(priority))
            )

        getters = self._priority_sorted_getters_by_namespace.get(namespace) or []

        for g in getters:
            if g.priority == priority:
                raise GetterPriorityConflict(repr(g), repr(resource_getter))

        # Highest priority should be first
        idx = bisect.bisect([-g.priority for g in getters], -priority)
        getters.insert(idx, ResourceGetter(getter=resource_getter,
                                           namespace=namespace,
                                           priority=priority,
                                           omit_namespace=omit_namespace,
                                           singleton=singleton))

        self._priority_sorted_getters_by_namespace[namespace] = getters

cdef class ResourceGetter:
    cdef:
        readonly str namespace_
        readonly float priority
        readonly object singleton
        readonly object _getter
        readonly cbool _omit_namespace

    def __repr__(self):
        return "{}(getter={!r}, namespace={!r}, omit_namespace={!r}, " \
               "priority={!r}, singleton={!r})".format(
            type(self).__name__,
            self._getter,
            self.namespace_,
            self._omit_namespace,
            self.priority,
            self.singleton
        )

    def __init__(self,
                 getter: Callable[[str], Any],
                 str namespace,
                 float priority,
                 cbool omit_namespace,
                 cbool singleton):
        self._getter = getter
        self._omit_namespace = omit_namespace
        self.namespace_ = namespace
        self.singleton = singleton
        self.priority = priority

    cdef object get(self, str resource_name):
        if self._omit_namespace:
            return self._getter(resource_name)
        return self._getter(self.namespace_ + ':' + resource_name)
