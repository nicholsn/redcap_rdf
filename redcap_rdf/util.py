""" Utility functions for the REDCap Data Tools.
"""
import os
import csv
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


def get_dict_reader(csv_file):
    """Read a csv file as a dictionary.

    Args:
        csv_file (str): Path to a csv file.

    Returns:
        An instance of csv.DictReader.
    """
    if not csv_file:
        log("File not provided.")
        return

    if not os.path.isfile(csv_file):
        log("{} file not found".format(csv_file))
        return
    with open(csv_file) as fi:
        return list(csv.DictReader(fi))