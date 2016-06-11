##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
import pytest

from redcap_rdf.sparql import queries
from redcap_rdf.tests.data import test_files
from redcap_rdf.transform_to_cube import Transformer


# Load test data.
metadata_path = test_files.get('dataset')
dd = test_files.get('observation_datadict')
slices = test_files.get('slices')
dimensions_csv = 'subject,arm,visit'
observation = test_files.get('observation')
mapping = test_files.get('mapping')

# Setup for integrity constraint checks
ic_transformer = Transformer()
ic_transformer.build_graph(dd, mapping)
ic_transformer.add_metadata(metadata_path)
ic_transformer.add_dsd(dimensions_csv, slices)
ic_transformer.add_observations(observation)


def test_init():
    transformer = Transformer()
    assert isinstance(transformer, Transformer)


def test_build_graph():
    transformer = Transformer()
    transformer.build_graph(dd, mapping)
    subjects = [i.n3() for i in transformer._g.subjects()]
    assert '<http://ncanda.sri.com/terms.ttl#subject>' in subjects


def test_add_metadata():
    transformer = Transformer()
    transformer.add_metadata(metadata_path)
    subjects = [i.n3() for i in transformer._g.subjects()]
    assert "<http://sibis.sri.com/iri/ncanda-public-release-1.0.0>" in subjects


def test_add_dsd():
    transformer = Transformer()
    transformer.add_dsd(dimensions_csv, slices)
    subjects = [i.n3() for i in transformer._g.subjects()]
    assert "<http://sibis.sri.com/terms#sliceByArmVisit>" in subjects


def test_add_observations():
    transformer = Transformer()
    transformer.add_observations(observation)
    subjects = [i.n3() for i in transformer._g.subjects()]
    iri = "<http://sibis.sri.com/iri/0251ee3ec64386df9864ff27219610488c61792a>"
    assert iri in subjects


def test_ic1():
    result = ic_transformer.query(queries.get("ic-1_unique_dataset"))
    assert result.askAnswer is False


def test_ic2():
    result = ic_transformer.query(queries.get("ic-2_unique_dsd"))
    assert result.askAnswer is False
