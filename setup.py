##
##  See COPYING file distributed along with the redcap_rdf package for the
##  copyright and license terms
##
from setuptools import setup

setup(name='redcap_rdf',
      version='0.0.1',
      description='REDCap utility for mapping data/datadict to RDF.',
      url='http://github.com/sibis-platform/redcap_rdf',
      author='Nolan Nichols',
      author_email='nolan.nichols@gmail.com',
      license='BSD',
      packages=['redcap_rdf'],
      package_data={"redcap_rdf": []},
      include_package_data=True,
      zip_safe=False,
      install_requires=['rdflib==4.2.1'],
      setup_requires=['pytest-runner'],
      tests_require=['pytest', 'coverage'],
      scripts=[])
