# -*- coding: utf-8 -*-

# Copyright(C) 2011  Romain Bignon, Laurent Bachelier
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


__all__ = ['Route', 'Router']


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
        if self.view:
            self.precision = 1
        else:
            self.precision = 0

    def match(self, object_type, action, view, method):
        return \
            self.object_type == object_type and \
            self.action == action and \
            (self.view == view or self.view is None) and \
            self.method == method

class Router(object):
    def __init__(self):
        self.routes = {}
        self.default_actions = {}
        self.default_views = {}
        self.default_view = None

    def connect(self, route, call):
        """
        Register an action. Last added actions are prioritized.
        route: Route object
        call: method to call if the route is matched
        """
        self.routes.setdefault(route.precision, []).append((route, call))

    def set_default_action(self, object_type, action):
        self.default_actions[object_type] = action

    def set_default_view(self, action, view):
        if action is None:
            self.default_view = view
        else:
            self.default_views[action] = view

    def match(self, object_type, req, default_view = None):
        action = req.str_GET.get("action", self.default_actions.get(object_type))
        default_view = default_view or self.default_views.get(action, self.default_view)
        view = req.str_GET.get("view", default_view)
        method = req.method

        for precision in sorted(self.routes.keys(), reverse=True):
            for route, call in self.routes[precision]:
                if route.match(object_type, action, view, method):
                    return call

        return None
