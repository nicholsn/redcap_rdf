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
    assert '<http://ncanda.sri.com/terms#subject>' in subjects


def test_add_metadata():
    transformer = Transformer()
    transformer.add_metadata(metadata_path)
    subjects = [i.n3() for i in transformer._g.subjects()]
    assert "<http://sibis.sri.com/iri/ncanda-public-release-1.0.0>" in subjects


def test_add_dsd():
    transformer = Transformer()
    transformer.add_dsd(dimensions_csv, slices)
    subjects = [i.n3() for i in transformer._g.subjects()]
    assert "<http://ncanda.sri.com/terms#sliceByArmVisit>" in subjects


def test_add_observations():
    transformer = Transformer()
    with pytest.raises(KeyError):
        transformer.add_observations(observation)
        transformer.add_observations(observation)


def test_ic1():
    ic = "ic-1_unique_dataset"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic2():
    ic = "ic-2_unique_dsd"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic3():
    ic = "ic-3_dsd_includes_measure"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic4():
    ic = "ic-4_dimensions_have_range"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic5():
    ic = "ic-5_concept_dimensions_have_code_lists"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic6():
    ic = "ic-6_only_attributes_may_be_optional"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic7():
    ic = "ic-7_slice_keys_must_be_declared"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic8():
    ic = "ic-8_slice_keys_consistent_with_dsd"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic9():
    ic = "ic-9_unique_slice_structure"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic10():
    ic = "ic-10_slice_dimensions_complete"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic11():
    ic = "ic-11_all_dimensions_required"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic12():
    ic = "ic-12_no_duplicate_observations"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic13():
    ic = "ic-13_required_attributes"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic14():
    ic = "ic-14_all_measures_present"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic15():
    ic = "ic-15_measure_dimension_consistent"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic16():
    ic = "ic-16_single_measure_on_measure_dimension_observation"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic17():
    ic = "ic-17_all_measures_present_in_measures_dimension_cube"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic18():
    ic = "ic-18_consistent_dataset_links"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic19a():
    ic = "ic-19a_codes_from_code_list"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic19b():
    ic = "ic-19b_codes_from_code_list"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic20():
    ic = "ic-20_codes_from_hierarchy"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False


def test_ic21():
    ic = "ic-21_codes_from_hierarchy_inverse"
    result = ic_transformer.query(queries.get(ic))
    assert result.askAnswer is False