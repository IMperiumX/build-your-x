import socket
import sys
import threading

"""
Process requests synchronously;
each request must be completed before the next request can be started.
This isn’t suitable if each request takes a long time to complete,
because it requires a lot of computation, or because it returns a lot
of data which the client is slow to process. The solution is to create
a separate process or thread to handle each request;
TODO: the ForkingMixIn and ThreadingMixIn mix-in classes can be used to support asynchronous behaviour.
"""


def _get_best_family(*address):
    infos = socket.getaddrinfo(
        *address,
        type=socket.SOCK_STREAM,
        flags=socket.AI_PASSIVE,
    )
    family, type, proto, canonname, sockaddr = next(iter(infos))
    return family, sockaddr


class BaseServer:
    def __init__(self, server_address, RequestHandlerClass):
        """Constructor.  May be extended, do not override."""
        self.server_address = server_address
        self.RequestHandlerClass = RequestHandlerClass
        self.__is_shut_down = threading.Event()
        self.__shutdown_request = False

    def server_activate(self):
        """Called by constructor to activate the server.

        May be overridden.

        """
        pass

    def server_close(self):
        """Called to clean-up the server.

        May be overridden.

        """
        pass

    def verify_request(self, request, client_address):
        """Verify the request.  May be overridden.

        Return True if we should proceed with this request.

        """
        return True

    def process_request(self, request, client_address):
        """Call finish_request.

        Overridden by ForkingMixIn and ThreadingMixIn.

        """
        self.finish_request(request, client_address)
        self.shutdown_request(request)

    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(request, client_address, self)

    def serve_forever(self, poll_interval=0.5):
        """Handle one request at a time until shutdown."""
        self.__is_shut_down.clear()
        try:
            # XXX: Consider using another file descriptor or connecting to the
            # socket to wake this up instead of polling. Polling reduces our
            # responsiveness to a shutdown request and wastes cpu at all other
            # times.

            while not self.__shutdown_request:
                if self.__shutdown_request:
                    break
                self._handle_request_noblock()

        finally:
            self.__shutdown_request = False
            self.__is_shut_down.set()

    def handle_request(self):
        """Handle one request, possibly blocking."""

        while True:
            return self._handle_request_noblock()

    def _handle_request_noblock(self):
        """Handle one request, without blocking."""
        try:
            request, client_address = self.get_request()
        except OSError:
            return
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except Exception:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
            except Exception as e:
                print(e)
                self.shutdown_request(request)
                raise
        else:
            self.shutdown_request(request)

    def handle_error(self, request, client_address):
        """Handle an error gracefully.  May be overridden.

        The default is to print a traceback and continue.

        """
        print("-" * 40, file=sys.stderr)
        print(
            "Exception occurred during processing of request from",
            client_address,
            file=sys.stderr,
        )
        import traceback

        traceback.print_exc()
        print("-" * 40, file=sys.stderr)

    def shutdown_request(self, request):
        """Called to shutdown and close an individual request."""
        self.close_request(request)

    def close_request(self, request):
        """Called to clean up an individual request."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.server_close()


class TCPServer(BaseServer):
    address_family = socket.AF_INET

    socket_type = socket.SOCK_STREAM
    request_queue_size = 5

    allow_reuse_address = 1  # XXX: Make sense in testing environment

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        """Constructor.  May be extended, do not override."""
        BaseServer.__init__(self, server_address, RequestHandlerClass)
        self.socket = socket.socket(self.address_family, self.socket_type)
        if bind_and_activate:
            try:
                self.server_bind()
                self.server_activate()
            except Exception as e:
                print(e)
                self.server_close()
                raise

    def get_request(self):
        """Get the request and client address from the socket.

        May be overridden.

        """
        return self.socket.accept()

    def server_bind(self):
        """Called by constructor to bind the socket."""
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()

        # Store the server name
        host, port = self.server_address[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

    def server_activate(self):
        """Called by constructor to activate the server."""
        self.socket.listen(self.request_queue_size)

    def server_close(self):
        """Called to clean-up the server."""
        self.socket.close()

    def shutdown_request(self, request):
        """Called to shutdown and close an individual request."""
        try:
            # explicitly shutdown.  socket.close() merely releases
            # the socket and waits for GC to perform the actual close.
            request.shutdown(socket.SHUT_WR)
        except OSError:
            pass  # some platforms may raise ENOTCONN here
        self.close_request(request)
