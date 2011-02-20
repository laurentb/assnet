class Route(object):
    def __init__(self, object_type, action, view = None, method = 'GET'):
        """
        object_type: "file" or "directory"
        action: arbitrary name
        view: arbitrary name. If none, will
        method: HTTP method, GET by default
        """
        self.object_type = object_type
        self.action = action
        self.view = view
        self.method = method

    def match(self, object_type, req):
        return \
            self.object_type == object_type and \
            req.str_GET.get("action") == self.action and \
            (req.str_GET.get("view") == self.view or self.view is None) and \
            req.method == self.method

class Router(object):
    def __init__(self):
        self.routes = []

    def connect(self, route, call):
        """
        Register an action.
        route: Route object
        call: method to call if the route is matched
        """
        self.routes.insert(0, (route, call))

    def match(self, object_type, req):
        for route, call in self.routes:
            if route.match(object_type, req):
                return call

        return False
