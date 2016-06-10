##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import os

test_files = dict()

for filename in os.listdir(os.path.dirname(__file__)):
    if filename not in ['__init__.py', '__init__.pyc']:
        key, _ = os.path.splitext(filename)
        test_files.update({key: os.path.abspath(filename)})
