#!/usr/bin/python

'''
AWS Lambda WIP
'''

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def all_details(client, module):
    lambda_facts = dict()

    function_name = module.params['function_name']

    if function_name:
        try:
            lambda_facts.update(client.get_function_configuration(FunctionName=function_name))
            lambda_facts.update(client.list_aliases(FunctionName=function_name))
            # get_policy returns a JSON string so must convert to dict before reassigning to its key
            lambda_facts.update(Policy=json.loads(client.get_policy(FunctionName=function_name)['Policy']))

            lambda_facts.update(client.list_versions_by_function(FunctionName=function_name))
        except Exception as e:
            module.fail_json(msg=str(e))
    else:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        try:
            lambda_facts.update(client.list_functions(**params))
            lambda_facts.update(client.list_event_source_mappings(**params))
        except Exception as e:
            module.fail_json(msg=str(e))

    return lambda_facts


def config_details(client, module):
    lambda_facts = dict()

    function_name = module.params['function_name']
    if function_name:
        try:
            lambda_facts.update(client.get_function_configuration(FunctionName=function_name))
        except Exception as e:
            module.fail_json(msg=str(e))
    else:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        try:
            lambda_facts.update(client.list_functions(**params))
        except Exception as e:
            module.fail_json(msg=str(e))


    return lambda_facts


def alias_details(client, module):
    lambda_facts = dict()

    function_name = module.params['function_name']
    if function_name:
        try:
            lambda_facts.update(client.list_aliases(FunctionName=function_name))
        except Exception as e:
            module.fail_json(msg=str(e))

    return lambda_facts


def policy_details(client, module):
    lambda_facts = dict()

    function_name = module.params['function_name']
    if function_name:
        try:
            # get_policy returns a JSON string so must convert to dict before reassigning to its key
            lambda_facts.update(Policy=json.loads(client.get_policy(FunctionName=function_name)['Policy']))
        except Exception as e:
            module.fail_json(msg=str(e))

    return lambda_facts


def mapping_details(client, module):
    lambda_facts = dict()

    if module.params.get('function_name'):
        module.fail_json(msg='Invalid parameter function_name for mappings query.')

    params = dict()
    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    if module.params.get('next_marker'):
        params['Marker'] = module.params.get('next_marker')

    try:
        lambda_facts.update(client.list_event_source_mappings(**params))
    except Exception as e:
        module.fail_json(msg=str(e))


    return lambda_facts


def version_details(client, module):
    lambda_facts = dict()

    function_name = module.params['function_name']
    if function_name:
        try:
            lambda_facts.update(client.list_versions_by_function(FunctionName=function_name))
        except Exception as e:
            module.fail_json(msg=str(e))

    return lambda_facts


def main():
    argument_spec = dict()
    argument_spec.update(dict(
            aws_profile=dict(required=False, default=None),
            function_name=dict(required=False, default=None),
            # show_versions=dict(required=False, default=False, type='bool'),
            query=dict(required=False, choices=['all', 'config', 'aliases', 'policy', 'mappings', 'versions'], default='all'),
            max_items=dict(type='int'),
            next_marker=dict()
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['function_name', 'max_items'],
            ['show_versions', 'max_items'],
            ['mappings', 'function_name']
        ],
        required_together=[

        ]
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module and can coexist with boto.')

    # validate function_name if present
    function_name = module.params['function_name']
    if function_name:
        if not re.search('^[a-zA-z][a-zA-Z0-9\-_]+$', function_name):
            module.fail_json(msg='Function name %s is invalid. Names must contain only alphanumeric characters and hyphens.' % function_name)

        if len(function_name) > 64:
            module.fail_json(msg='Function name "%s" exceeds 64 character limit' % function_name)


    client = boto3.client('lambda')

    invocations = {
        'config': config_details,
        'aliases': alias_details,
        'policy': policy_details,
        'mappings': mapping_details,
        'versions': version_details,
        'all': all_details,
    }
    lambda_facts = invocations[module.params.get('query')](client, module)

    if 'ResponseMetadata' in lambda_facts:
        del lambda_facts['ResponseMetadata']
    results = dict(ansible_facts=lambda_facts, changed=False)
    module.exit_json(**results)


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
