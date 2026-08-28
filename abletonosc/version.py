import os

#--------------------------------------------------------------------------------
# Single source of truth for AbletonOSC's own version, kept in a plain-text VERSION
# file at the repo root (sibling to manager.py/__init__.py -- the actual Remote
# Script directory Live loads), not in this package. Standalone (no Live-dependent
# imports) so it can be read both from manager.py (inside Live) and from a unit test
# (outside Live) without pulling in any of the Live API stubbing in tests_unit/conftest.py.
#--------------------------------------------------------------------------------

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_VERSION_FILE_PATH = os.path.join(_REPO_ROOT, "VERSION")


def read_version(version_file_path: str = DEFAULT_VERSION_FILE_PATH) -> str:
    """
    Read and return the version string from `version_file_path` (a plain-text file
    containing a single line, e.g. "0.1.0"), stripped of surrounding whitespace.

    Returns "unknown" if the file is missing or unreadable -- this must never prevent
    AbletonOSC from starting up.
    """
    try:
        with open(version_file_path, "r") as version_file:
            version = version_file.read().strip()
        return version if version else "unknown"
    except OSError:
        return "unknown"
