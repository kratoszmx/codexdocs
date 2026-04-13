import sys

import project_env


def test_project_env_adds_myutils_to_sys_path() -> None:
    assert project_env.MYUTILS_ROOT.name == "myutils"
    assert str(project_env.MYUTILS_ROOT) in sys.path
