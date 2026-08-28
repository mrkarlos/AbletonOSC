import os

from ..abletonosc.version import read_version


def test_read_version_strips_whitespace(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("0.1.0\n")

    assert read_version(str(version_file)) == "0.1.0"


def test_read_version_missing_file_returns_unknown(tmp_path):
    missing_path = str(tmp_path / "does-not-exist" / "VERSION")

    assert read_version(missing_path) == "unknown"


def test_read_version_empty_file_returns_unknown(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("   \n")

    assert read_version(str(version_file)) == "unknown"


def test_read_version_default_path_reads_repo_root_version_file():
    #--------------------------------------------------------------------------------
    # Sanity check that the default path actually resolves to the real VERSION file
    # at the repo root, not just that read_version() works given an explicit path.
    #--------------------------------------------------------------------------------
    repo_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    expected = open(os.path.join(repo_root, "VERSION")).read().strip()

    assert read_version() == expected
    assert read_version() != "unknown"
