from nose.tools import assert_equals
import yaml


from lambda_facts import DOCUMENTATION, EXAMPLES, RETURN


def test_documentation_yaml():
    print 'Testing documentation YAML...'

    assert_equals(DOCUMENTATION.startswith(('---', '\n---')), True)

    assert_equals(EXAMPLES.startswith(('---', '\n---')), True)

    assert_equals(RETURN.startswith(('---', '\n---')), True)


def test_validate_yaml():

    documentation_yaml = yaml.load(EXAMPLES)

    print yaml.dump(documentation_yaml)



