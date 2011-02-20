class Route(object):
    def __init__(self, object_type, action, view = None, method = 'GET'):
        """
        object_type: "file" or "directory", or None for global actions
        action: Arbitrary name
        view: Arbitrary name. If none, will accept anything
        method: HTTP method, GET by default
        """
        self.object_type = object_type
        self.action = action
        self.view = view
        self.method = method

    def match(self, object_type, action, view, method):
        return \
            self.object_type == object_type and \
            self.action == action and \
            (self.view == view or self.view is None) and \
            self.method == method

class Router(object):
    def __init__(self):
        self.routes = []
        self.default_actions = {}
        self.default_views = {}
        self.default_view = None

    def connect(self, route, call):
        """
        Register an action. Last added actions are prioritized.
        route: Route object
        call: method to call if the route is matched
        """
        self.routes.insert(0, (route, call))

    def set_default_action(self, object_type, action):
        self.default_actions[object_type] = action

    def set_default_view(self, action, view):
        if action is None:
            self.default_view = view
        else:
            self.default_views[action] = view

    def match(self, object_type, req):
        action = req.str_GET.get("action", self.default_actions.get(object_type))
        view = req.str_GET.get("view", self.default_views.get(action, self.default_view))
        method = req.method

        for route, call in self.routes:
            if route.match(object_type, action, view, method):
                return call

        return False
