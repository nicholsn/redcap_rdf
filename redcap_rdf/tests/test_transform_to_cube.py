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


def test_add_dsd():
    dimensions_csv = 'subject,arm,visit'
    slices = test_files.get('slices')
    transformer = Transformer()
    transformer.add_dsd(dimensions_csv, slices)
    subjects = [i.n3() for i in transformer._g.subjects()]
    assert "<http://sibis.sri.com/terms#sliceByArmVisit>" in subjects


def test_add_observations():
    observation = test_files.get('observation')
    transformer = Transformer()
    transformer.add_observations(observation)
    subjects = [i.n3() for i in transformer._g.subjects()]
    iri = "<http://sibis.sri.com/iri/0251ee3ec64386df9864ff27219610488c61792a>"
    assert iri in subjects