"""Compatibility constants and helpers for Python 2.x and 3.x.
"""

# NB If this module grows to more than a handful of items it is probably
#    to bite the bullet and depend on the six package.
__all__ = [
    'string_types',
]

# Needed for isinstance() checks
# Same behaviour as six.string_types https://pythonhosted.org/six/#constants
try:
    # Python 2.x
    string_types = basestring
except NameError:
    # Python 3.x
    string_types = str

