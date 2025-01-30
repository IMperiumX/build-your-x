import argparse
import sys

from .request_handler import HTTPRequestHandler
from .server import TCPServer, _get_best_family

parser = argparse.ArgumentParser()
parser.add_argument(
    "--bind",
    "-b",
    metavar="ADDRESS",
    help="specify alternate bind address " "(default: all interfaces)",
)
parser.add_argument(
    "port",
    action="store",
    default=8000,
    type=int,
    nargs="?",
    help="specify alternate port (default: 8000)",
)
args = parser.parse_args()

TCPServer.address_family, addr = _get_best_family(args.bind, args.port)

with TCPServer(addr, HTTPRequestHandler) as httpd:
    host, port = httpd.socket.getsockname()[:2]
    url_host = f"[{host}]" if ":" in host else host
    print(f"Serving HTTP on {host} port {port} " f"(http://{url_host}:{port}/) ...")
    print(f"Server name: {httpd.server_name}")
    print(f"Server port: {httpd.server_port}")
    print("Use Control-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        sys.exit(0)
