##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import pytest

import redcap_rdf


def test_check_headers():
    headers = redcap_rdf.HEADERS
    assert redcap_rdf.check_headers(headers) == False

    headers[0] += " fail"
    assert redcap_rdf.check_headers(headers) == False
