import os
import time
from typing import Optional

import paramiko

from .builder import build
from .bundle import ResourceBundle


def iter_chunks(channel: paramiko.Channel):
    while not channel.exit_status_ready():
        while channel.recv_ready():
            yield channel.recv(1024)
        time.sleep(0.1)

    while channel.recv_ready():
        yield channel.recv(1024)


def iter_lines(channel: paramiko.Channel):
    buffer = bytearray()
    for chunk in iter_chunks(channel):
        buffer.extend(chunk)

        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            yield line.decode("utf-8")


def execute_via_ssh(
    transport: paramiko.Transport,
    bundle: ResourceBundle,
    dry_run: bool = False,
    username: Optional[str] = "root",
    sudo_password: Optional[str] = None,
):
    """
    transport = paramiko.Transport(("localhost", 22))
    transport.connect(
        username="ubuntu",
        password="password55",
    )
    execute(transport, bundle, "root", "mysudopassword")
    """
    payload = build(bundle)

    sftp = transport.open_sftp_client()
    sftp.chdir(".")

    path = os.path.join(sftp.getcwd(), ".payload.pex")

    command_parts = [path, "--resume"]

    if dry_run:
        command_parts.append("--simulate")

    command = " ".join(command_parts)

    channel = transport.open_session()
    channel.get_pty()
    channel.set_combine_stderr(1)

    try:
        sftp.putfo(payload, path)
        sftp.chmod(path, 0o755)

        try:
            if username and username != transport.get_username():
                command = f"sudo -u {username} {command}"
                channel.exec_command(command)

                if sudo_password:
                    first_line = channel.recv(1024)

                    if b"[sudo]" not in first_line and not first_line.startswith(
                        b"Password:"
                    ):
                        raise RuntimeError(f"Expected sudo, got {first_line!r}")

                    channel.sendall((sudo_password + "\n").encode("utf-8"))
            else:
                channel.exec_command(path)

            channel.shutdown_write()

            try:
                for line in iter_lines(channel):
                    print(line)

                return channel.recv_exit_status()
            finally:
                channel.close()
        finally:
            sftp.remove(path)
    finally:
        sftp.close()
