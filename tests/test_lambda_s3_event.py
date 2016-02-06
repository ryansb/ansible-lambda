from nose.tools import assert_equals
import yaml


from modules.lambda_s3_event import DOCUMENTATION, EXAMPLES


def test_documentation_yaml():
    print 'Testing documentation YAML...'

    assert_equals(DOCUMENTATION.startswith(('---', '\n---')), True)

    assert_equals(EXAMPLES.startswith(('---', '\n---')), True)


def test_validate_yaml():

    documentation_yaml = yaml.load(DOCUMENTATION)

    example_yaml = yaml.load(EXAMPLES)

    print documentation_yaml['short_description']

