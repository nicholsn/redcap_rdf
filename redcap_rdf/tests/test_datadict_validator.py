##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import os

import pytest

from redcap_rdf.datadict_validator import Validator

datadict = os.path.join(os.path.dirname(__file__),
                        'data',
                        'datadict_test_cases.csv')


def test_file_exists():
    validator = Validator()
    fake_file = '/tmp/foo.csv'
    with pytest.raises(IOError):
        validator.process(fake_file, [])


def test_check_headers():
    validator = Validator()
    corrupt_header = os.path.join(os.path.dirname(__file__),
                                  'data',
                                  'datadict_corrupt_header.csv')
    validator.process(corrupt_header, [])
    assert 'HEADERS' in validator.errors.keys()


def test_missing_field_type():
    validator = Validator()
    validator.process(datadict, [])
    case = "missing_field_type"
    code = "Skipping validation of type"
    assert code in validator.warnings.get(case)[0]


def test_missing_field_label():
    validator = Validator()
    validator.process(datadict, [])
    case = "missing_field_label"
    code = "No label is present."
    assert code in validator.warnings.get(case)[0]


def test_missing_choices():
    validator = Validator()
    validator.process(datadict, [])
    case = "missing_choices"
    code = "There should be at least one choice."
    assert code in validator.errors.get(case)[0]


def test_missing_min():
    validator = Validator()
    validator.process(datadict, [])
    case = "missing_min"
    code = "No minimum value set."
    assert code in validator.warnings.get(case)[0]


def test_missing_max():
    validator = Validator()
    validator.process(datadict, [])
    case = "missing_max"
    code = "No maximum value set."
    assert code in validator.warnings.get(case)[0]


def test_missing_max_min():
    validator = Validator()
    validator.process(datadict, [])
    case = "missing_max_min"
    code = "No maximum or minimum value set."
    assert code in validator.warnings.get(case)[0]


def test_incorrect_field_type():
    validator = Validator()
    validator.process(datadict, [])
    case = "incorrect_field_type"
    code = "Skipping validation of type"
    assert code in validator.warnings.get(case)[0]
