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
