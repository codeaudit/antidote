import pkg_resources as _pkg_resources

from .core import inject
from .helpers.attrs import attrib
from .helpers.container import context, new_container
from .helpers.registration import factory, provider, register, resource
from .helpers.wiring import wire
from .providers.factory import Build
from .providers.tag import Tag, Tagged, TaggedDependencies

try:
    __version__ = _pkg_resources.get_distribution(__name__).version
except _pkg_resources.DistributionNotFound:  # pragma: no cover
    # package is not installed
    pass

__all__ = [
    'Build',
    'Tag',
    'Tagged',
    'TaggedDependencies',
    'attrib',
    'context',
    'factory',
    'inject',
    'new_container',
    'provider',
    'register',
    'resource',
    'wire'
]

world = new_container()
