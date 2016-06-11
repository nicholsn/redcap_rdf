##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import os

test_files = dict()

test_data_dir = os.path.dirname(__file__)
for filename in os.listdir(test_data_dir):
    if filename not in ['__init__.py', '__init__.pyc']:
        key, _ = os.path.splitext(filename)
        absfilename = os.path.join(test_data_dir, filename)
        test_files.update({key: os.path.abspath(absfilename)})
