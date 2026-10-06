"""Opt-in wrappers for running pipeline Python scripts in offline integrations."""
from pathlib import Path
import shlex
import sys

import pytest


@pytest.fixture
def install_offline_scripts(tmp_path):
    """Install named repo scripts (or explicit paths) into the test workflow's bin/."""
    repo_bin = Path(__file__).resolve().parents[1] / 'bin'

    def install(*sources):
        scripts = tmp_path / 'bin'
        scripts.mkdir(exist_ok=True)
        for source in sources:
            source = Path(source)
            if not source.is_absolute():
                source = repo_bin / source
            runner = tmp_path / ('run_' + source.name)
            runner.write_text('''import runpy, socket, sys, types
try:
    import nameparser
except ImportError:
    module = types.ModuleType('nameparser')
    module.HumanName = object
    sys.modules['nameparser'] = module
def no_network(*args, **kwargs):
    raise AssertionError('Network access is disabled in this test')
socket.socket.connect = no_network
socket.create_connection = no_network
''' + f"sys.path.insert(0, {str(source.parent)!r})\nrunpy.run_path({str(source)!r}, run_name='__main__')\n")
            wrapper = scripts / source.name
            wrapper.write_text(f'#!/bin/bash\nexec {shlex.quote(sys.executable)} -B {shlex.quote(str(runner))} "$@"\n')
            wrapper.chmod(0o755)
        return scripts

    return install
