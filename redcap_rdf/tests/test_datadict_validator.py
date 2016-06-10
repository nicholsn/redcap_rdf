##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import pytest

from redcap_rdf.tests.data import test_files
from redcap_rdf.datadict_validator import Validator

datadict = test_files.get('datadict_test_cases')


def test_file_exists():
    validator = Validator()
    fake_file = '/tmp/foo.csv'
    with pytest.raises(IOError):
        validator.process(fake_file, [])


def test_check_headers():
    validator = Validator()
    corrupt_header = test_files.get('datadict_corrupt_header')
    validator.process(corrupt_header, [])
    code = "HEADERS"
    assert code in validator.errors.keys()


def test_check_first_rows():
    validator = Validator()
    case = "FAKE_FIRST_ROW"
    code = "field should be"
    validator.process(datadict, [case])
    assert code in validator.errors.get('missing_field_type')[0]


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


def test_incorrect_max_lt_min():
    validator = Validator()
    validator.process(datadict, [])
    case = "incorrect_max_lt_min"
    code = "should not be less than min"
    assert code in validator.errors.get(case)[0]


def test_incorrect_field_type():
    validator = Validator()
    validator.process(datadict, [])
    case = "incorrect_field_type"
    code = "Skipping validation of type"
    assert code in validator.warnings.get(case)[0]


def test_correct_choice():
    validator = Validator()
    validator.process(datadict, [])
    case = "correct_choice"
    assert case not in validator.warnings.keys()