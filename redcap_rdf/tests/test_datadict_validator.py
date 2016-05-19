##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import os

from redcap_rdf.datadict_validator import Validator

validator = Validator()
datadict = os.path.join(os.path.dirname(__file__),
                        'data',
                        'datadict_test_cases.csv')


def test_check_headers():
    corrupt_header = os.path.join(os.path.dirname(__file__),
                                  'data',
                                  'datadict_corrupt_header.csv')
    validator.process(corrupt_header, [])
    assert 'HEADERS' in validator.errors.keys()
