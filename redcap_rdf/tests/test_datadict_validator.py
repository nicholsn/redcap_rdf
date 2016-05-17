##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import os

from redcap_rdf import datadict_validator


def test_check_headers():
    datadict = os.path.join(os.path.dirname(__file__),
                            'data', 'datadict_test_cases.csv')
    validator = datadict_validator.Validator()
    assert validator.process(datadict, []) is None
