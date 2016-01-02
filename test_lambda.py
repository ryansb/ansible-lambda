import importlib
from nose.tools import assert_equals

try:
    import importlib
except ImportError:
    pass

# from lambda import DOCUMENTATION, EXAMPLES, RETURN
lambda_mod = importlib.import_module('lambda')


def test_documentation_yaml():
    print 'Testing documentation YAML...'

    assert_equals(lambda_mod.DOCUMENTATION.startswith(('---', '\n---')), True)

    assert_equals(lambda_mod.EXAMPLES.startswith(('---', '\n---')), True)

    assert_equals(lambda_mod.RETURN.startswith(('---', '\n---')), True)
