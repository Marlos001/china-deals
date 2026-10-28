"""Check the Linux container's IPv4 route is unavailable in two processes."""
import errno
import socket
import subprocess
import sys


def check():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        error = sock.connect_ex(('1.1.1.1', 443))
    if error != errno.ENETUNREACH:
        raise RuntimeError(f'Expected network unreachable, got socket error {error}')


if __name__ == '__main__':
    check()
    if '--child' not in sys.argv:
        subprocess.run([sys.executable, __file__, '--child'], check=True)
        print('External IPv4 route unavailable in parent and subprocess')
