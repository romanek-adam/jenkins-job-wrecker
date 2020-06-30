import os

from jenkins_job_wrecker.cli import get_xml_root, root_to_yaml
import yaml

def compare_jjb_output(fixtures_path, name, job_name):
    test_filename = os.path.join(fixtures_path, name + '.xml')
    expected_yml_filename = os.path.join(fixtures_path, name + '.yml')
    root = get_xml_root(filename=test_filename)
    actual_yml = root_to_yaml(root, job_name)

    with open(expected_yml_filename) as f:
        expected_yml = f.read()

    # The reason of load->dump is to ensure that the keys
    # in yaml files are sorted. Otherwise, it would be
    # very hard to match each in specific order in
    # comparison test cases.
    expected_yml = yaml.dump(yaml.load(expected_yml, Loader=yaml.FullLoader))

    assert actual_yml is not None
    assert actual_yml == expected_yml
