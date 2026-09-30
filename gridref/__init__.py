"""KiCad loads a plugin folder through this file, so importing the module is
all it takes: the module body registers the plugin with pcbnew as it runs.
"""

from . import gridref  # noqa: F401
