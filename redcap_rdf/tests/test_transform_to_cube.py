##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import pytest

from redcap_rdf.tests.data import test_files
from redcap_rdf.transform_to_cube import Transformer


def test_init():
    transformer = Transformer()
    assert isinstance(transformer, Transformer)


def test_build_graph():
    dd = test_files.get('observation_datadict')
    config = test_files.get('mapping')
    transformer = Transformer()
    transformer.build_graph(dd, config)
    subjects = [i.n3() for i in transformer._g.subjects()]
    assert '<http://ncanda.sri.com/terms.ttl#subject>' in subjects


def test_add_metadata():
    metadata_path = test_files.get('dataset')
    transformer = Transformer()
    transformer.add_metadata(metadata_path)
    subjects = [i.n3() for i in transformer._g.subjects()]
    assert "<http://sibis.sri.com/iri/ncanda-public-release-1.0.0>" in subjects