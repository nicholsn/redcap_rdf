##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import pytest

from redcap_rdf.transform_to_cube import Transformer


def test_init():
    transformer = Transformer()
    assert isinstance(transformer,Transformer)
