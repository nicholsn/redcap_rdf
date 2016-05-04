##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import pytest

from redcap_rdf import datadict_validator


def test_check_headers():
    headers = datadict_validator.HEADERS
    assert datadict_validator.check_headers(headers) == False

    headers[0] += " fail"
    assert datadict_validator.check_headers(headers) == False
