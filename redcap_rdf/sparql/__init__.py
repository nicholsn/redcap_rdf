##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import os

queries = dict()

query_dir = os.path.dirname(__file__)
for filename in os.listdir(query_dir):
    if filename not in ['__init__.py', '__init__.pyc']:
        key, _ = os.path.splitext(filename)
        absfilename = os.path.join(query_dir, filename)
        with open(os.path.abspath(absfilename), 'r') as fi:
            query = fi.read()
        queries.update({key: query})
