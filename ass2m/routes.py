# -*- coding: utf-8 -*-

# Copyright(C) 2011  Romain Bignon, Laurent Bachelier
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


__all__ = ['View', 'Router']


class View(object):
    def __init__(self, name, object_type = None, mimetype = None,
            verbose_name = None, public = True):
        """
        name: Arbitrary name.
        object_type: "file" or "directory", or None for both.
        mimetype = mimetypes for which the view is available. Can be \
            a partial mimetype (for instance "image")
        verbose_name: Name to show in the available views list.
        public: Show in in the available views list.
        """
        self.name = name
        self.object_type = object_type
        self.mimetype = mimetype
        self.verbose_name = verbose_name or name.replace('_', ' ').title()
        self.public = public

    def match_mimetype(self, mimetype):
        """
        Checks if the mimetype can be handled by the View.
        If the View mimetype is None, it will accept anything.
        If the View mimetype exactly the provided mimetype, it will be accepted.
        If the View mimetype is partial, it will accept any mimetype starting by it,
        i.e. "image" will accept "image/png" and "image/jpeg".
        Returns a boolean.
        """
        return self.mimetype is None or \
            self.mimetype == mimetype or \
            (mimetype and self.mimetype == mimetype.split('/')[0])

    def match(self, object_type, mimetype):
        """
        Checks if the View is suitable for given the parameters.
        Returns a boolean.
        """
        return self.match_mimetype(mimetype) and \
            (self.object_type == object_type or self.object_type is None)

    def guess_priority(self):
        """
        Guess the priority of a view.
        The more precise it is, the more priority it will get.
        """
        priority = 0
        if self.object_type:
            priority += 1
        if self.mimetype:
            priority += 1
            if '/' in self.mimetype:
                priority += 1
        return priority


    def __str__(self):
        return self.name


class Router(object):
    def __init__(self):
        self.actions = {}
        self.views = {}

    def register_action(self, name, action):
        """
        Register an action. An action is global, not related to a file.
        name: Arbitrary name
        action: Action class to use if the route is matched
        """
        self.actions[name] = action

    def register_view(self, view, action, priority = None):
        """
        Register a view. A view is related to a file.
        See the View class for more details.
        view: View
        action: Action class to use if the route is matched
        priority: int
        """
        if priority is None:
            priority = view.guess_priority()
        self.views.setdefault(priority, []).append((view, action))

    def find_action(self, name):
        """
        name: str
        Returns the Action class for an action name.
        """
        return self.actions.get(name)

    def find_view(self, f, name = None):
        """
        Find a view suitable for a file
        f: File
        name: Provide the view name if we already know it
        Returns the view and the related Action class.

        Even if we know the view name, this function is useful to validate we can
        actually use the view on it.
        """
        # use the default file view if no view was requested
        if name is None:
            name = f.view
        object_type = f.get_object_type()
        mimetype = f.get_mimetype()

        for priority in sorted(self.views.keys(), reverse=True):
            for view, action in self.views[priority]:
                if view.match(object_type, mimetype):
                    # if no view was requested, or if we found the requested view
                    if name is None or view.name == name:
                        return (view, action)
        return (None, None)

    def get_available_views(self, f):
        """
        f: File
        Get all the available views for a file.
        """
        object_type = f.get_object_type()
        mimetype = f.get_mimetype()

        for views in self.views.itervalues():
            for view, action in views:
                if view.match(object_type, mimetype):
                    yield view
