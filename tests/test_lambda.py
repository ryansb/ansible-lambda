from nose.tools import assert_equals
import yaml

# can't import 'lambda' since it's a keyword so must work around with importlib
try:
    import importlib
except ImportError:
    # then it must be built-in (>=2.7)
    pass

lambda_mod = importlib.import_module('modules.lambda')


def test_documentation_yaml():
    print 'Testing documentation YAML...'

    assert_equals(lambda_mod.DOCUMENTATION.startswith(('---', '\n---')), True)

    assert_equals(lambda_mod.EXAMPLES.startswith(('---', '\n---')), True)


def test_validate_yaml():

    documentation_yaml = yaml.load(lambda_mod.DOCUMENTATION)

    example_yaml = yaml.load(lambda_mod.EXAMPLES)

    print documentation_yaml['short_description']
