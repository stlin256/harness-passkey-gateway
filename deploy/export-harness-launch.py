#!/usr/bin/env python3
"""ExecStartPost adapter: write the private launch URL without logging it.

Run as the Harness user with access to its journal, e.g. SupplementaryGroups=adm.
Runtime directory: Harness-user:harness-access, mode 0710, created by tmpfiles.
The reader service joins harness-access; no broader agent directory is shared.
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

service = os.environ.get('HARNESS_SERVICE', 'deepseek-harness.service')
target = Path(os.environ.get('HARNESS_LAUNCH_FILE', '/run/harness-gateway/launch-url'))
for _ in range(60):
    pid = subprocess.check_output(['systemctl', 'show', service, '-p', 'MainPID', '--value'], text=True).strip()
    if pid != '0':
        log = subprocess.check_output(['journalctl', '_PID=' + pid, '--no-pager', '-o', 'cat', '-n', '200'], text=True)
        urls = re.findall(r'http://(?:127\.0\.0\.1|localhost):3080/\?[^\s\x1b]+', log)
        if urls:
            value = urls[-1].rstrip(')\'".,')
            temporary = target.with_name('.launch-' + str(os.getpid()))
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640)
            with os.fdopen(descriptor, 'w') as output:
                output.write(value.replace('localhost', '127.0.0.1') + '\n')
            os.chmod(temporary, 0o640)
            import grp
            os.chown(temporary, -1, grp.getgrnam('harness-access').gr_gid)
            os.replace(temporary, target)
            sys.exit(0)
    time.sleep(1)
sys.exit('Harness launch credential not available')
