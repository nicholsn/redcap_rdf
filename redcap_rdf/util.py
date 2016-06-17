""" Utility functions for the REDCap Data Tools.

@author: Victor Meyerson
"""

import sys


def log(msg):
    """Prints a message to standard error

        Args:
            msg (str): Message to be printed

        Returns:
            None

    """
    sys.stderr.write(msg)
    sys.stderr.write("\n")


class AttrDict(dict):
    """Attribute based access to a dictionary.

    Returns:
        An instance of an attributed dictionary.

    """
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self