import BaseHTTPServer
import cgi


class BardunSimplePath(object):
    def __init__(self, path):
        self._path = path

    def matches(self, path):
        return self._path == path

    def get_matches(self):
        # Return values from last match.
        return []


class BardunComplexPath(BardunSimplePath):
    def __init__(self, path):
        super(BardunComplexPath, self).__init__(path)
        paths, keys, constants = self._parse_path(path)
        self._paths = paths
        self._keys = keys
        self._constants = constants
        self._matches = []

    def matches(self, path):
        self._matches = []

        # No keys means a simple path.
        if len(self._keys) == 0:
            return super(BardunComplexPath, self).matches(path)

        paths, _, _ = self._parse_path(path)

        # If the count between our paths and the tokenized path differ, it's
        # not a match.
        if len(paths) != len(self._paths):
            return False

        # Constants must match.
        for idx, const in self._constants:
            if paths[idx] != const:
                return False

        # Keys must have a value
        for idx, keys in self._keys:
            if not paths[idx]:
                return False
            self._matches.append(paths[idx])

        return True

    def get_matches(self):
        return self._matches

    def _parse_path(self, path):
        """Tokenizes the path, splitting it into components: paths, keys and
        constants. Returns a tuple of lists of paths, keys and constants."""
        paths = []
        keys = []
        constants = []
        key_mode = False

        for char in path:
            if char == "/":
                paths.append("")
                key_mode = False
                continue

            if char == ":":
                key_mode = True
                keys.append((len(paths) - 1, ""))

            tmp = paths[len(paths) - 1]
            paths[len(paths) - 1] = tmp + char

            if key_mode:
                idx, key = keys[len(keys) - 1]
                key = key + char
                keys[len(keys) - 1] = (idx, key)

        # Builds a list of (index, constant) by inferring constants from paths
        # that are not keys.
        key_indices = [x for x, _ in keys]
        for idx, path in enumerate(paths):
            if idx not in key_indices:
                constants.append((idx, path))
        return (paths, keys, constants)


class BardunResponse(object):
    @property
    def status_code(self):
        return 200

    def __init__(self, content):
        self.content = content


class BardunResponse404(BardunResponse):
    @property
    def status_code(self):
        return 404


class BardunResponse500(BardunResponse):
    @property
    def status_code(self):
        return 500


class BardunServer(BaseHTTPServer.HTTPServer):
    def __init__(self, server_address, request_handler_class):
        BaseHTTPServer.HTTPServer.__init__(self, server_address,
                                           request_handler_class)
        # Key/val where key is the path, and the value is a tuple of (methods,
        # path, handler) where methods is a list of
        # methods to handle, e.g. GET, PUT, DELETE, etc. Path is an instance of
        # a BardunSimplePath or BardunComplexPath.
        self.routes = {}


class BardunHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        route = None
        for path in self.server.routes:
            _, path_instance, _ = self.server.routes[path]
            if path_instance.matches(self.path):
                route = self.server.routes[path]
                break

        if not route:
            return self._render(BardunResponse404(
                """<h1>404 not found</h1>
                   <p>%s was not found on this server.</p>""" %
                cgi.escape(self.path))
            )

        methods, path, handler = route

        try:
            methods.index("GET")
        except ValueError:
            return self._render(
                BardunResponse500(
                    "<h1>500 Error</h1><p>Method not allowed</p>"
                )
            )

        try:
            return self._render(handler(self, *path.get_matches()))
        except Exception as e:
            return self._render(
                BardunResponse500("<h1>500 Error</h1><p>%s</p>" % e)
            )

    def _render(self, response):
        self.send_response(response.status_code)
        self.end_headers()
        self.wfile.write(response.content)


class Bardun:
    def __init__(self, address, port, server_class=BardunServer,
                 handler_class=BardunHandler):
        server_address = (address, port)
        self._running = True
        self._server = server_class(server_address, handler_class)

    def run(self):
        self._server.serve_forever()
        while self._running:
            self._server.handle_request()

    def stop(self):
        self._running = False
        print("\nShutting down.")

    def add_route(self, methods, path, handler):
        cls = BardunSimplePath
        try:
            path.index(":")
        except ValueError:
            pass
        else:
            cls = BardunComplexPath

        path_instance = cls(path)

        self._server.routes[path] = (methods, path_instance, handler)


def my_index(request):
    return BardunResponse("Hello world --- Bardun.")


def my_hello(request, name):
    return BardunResponse("Hello %s!" % cgi.escape(name))


if __name__ == "__main__":

    my_app = Bardun("0.0.0.0", 8000)
    my_app.add_route(["GET"], "/", my_index)
    my_app.add_route(["GET"], "/foo/:bar", my_hello)

    try:
        my_app.run()
    except KeyboardInterrupt:
        my_app.stop()
