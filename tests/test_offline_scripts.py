"""Check the shared subprocess wrapper's network guard and argument forwarding."""
import subprocess

import pytest


@pytest.mark.parametrize('connect', [
    "socket.create_connection(('example.invalid', 21))",
    # Invoke the patched method without constructing an OS socket: some test
    # sandboxes prohibit socket creation before the connection guard can run.
    "socket.socket.connect(None, ('127.0.0.1', 21))",
])
def test_wrapper_blocks_connections(tmp_path, install_offline_scripts, connect):
    script = tmp_path / 'connection_probe.py'
    script.write_text('import socket, sys\nassert sys.argv[1:] == ["value with spaces"]\n' + connect + '\n')
    scripts = install_offline_scripts(script)
    result = subprocess.run([str(scripts / script.name), 'value with spaces'],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'AssertionError: Network access is disabled in this test' in result.stderr
