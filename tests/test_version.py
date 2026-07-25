import re

from version import __version__


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__), (
        f"__version__ debe seguir SemVer (X.Y.Z), no cumple: {__version__!r}"
    )
