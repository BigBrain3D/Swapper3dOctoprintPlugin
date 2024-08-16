# Octoprint plugin name: Swapper3D, File: setup.py, Author: BigBrain3D, License: AGPLv3

plugin_identifier = "Swapper3D"
plugin_package = "Swapper3D_Package"
plugin_name = "Swapper3D"
plugin_version = "0.3.1"
plugin_description = "Connect to Swapper3D and coordinate swaps with the 3D printer"
plugin_author = "BigBrain3D"
plugin_author_email = "info@bigbrain3D.com"
plugin_url = "https://github.com/BigBrain3D/Swapper3dOctoprintPlugin/"
plugin_license = "AGPLv3"
plugin_requires = ["pyserial>=3.5,<4"]
plugin_additional_data = []
plugin_additional_packages = []
plugin_ignored_packages = []
additional_setup_parameters = {"python_requires": ">=3.7,<4"}

try:
    import octoprint_setuptools
except:
    import sys
    sys.exit(-1)

setup_parameters = octoprint_setuptools.create_plugin_setup_parameters(
    identifier=plugin_identifier,
    package=plugin_package,
    name=plugin_name,
    version=plugin_version,
    description=plugin_description,
    author=plugin_author,
    mail=plugin_author_email,
    url=plugin_url,
    license=plugin_license,
    requires=plugin_requires,
    additional_packages=plugin_additional_packages,
    ignored_packages=plugin_ignored_packages,
    additional_data=plugin_additional_data,
)

if len(additional_setup_parameters):
    from octoprint.util import dict_merge
    setup_parameters = dict_merge(setup_parameters, additional_setup_parameters)

from setuptools import setup
setup(**setup_parameters)
