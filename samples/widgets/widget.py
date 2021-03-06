# -*- coding: utf-8 -*-


class Widget(object):

    """
    You can define a class which extends Widget for collecting samples
    from Internet.
    """

    def run(self):
        """
        Any module that extends class Widget should implemented this method,
        or this method will raise 'NotImplementedError'.
        """
        raise NotImplementedError
