#!/usr/bin/python

'''
AWS Lambda WIP
'''

try:
    import boto3
    from boto.exception import *
    from botocore.exceptions import *
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def all_details(client, module):

    if module.params.get('max_items') or module.params.get('next_marker'):
        module.fail_json(msg='Cannot specify max_items nor next_marker for query=all.')

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        lambda_facts.update(config_details(client, module))
        lambda_facts.update(alias_details(client, module))
        lambda_facts.update(policy_details(client, module))
        lambda_facts.update(version_details(client, module))
    else:
        lambda_facts.update(config_details(client, module))
        lambda_facts.update(mapping_details(client, module))

    return lambda_facts


def config_details(client, module):

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        try:
            lambda_facts.update(client.get_function_configuration(FunctionName=function_name))
        except (BotoServerError, ClientError), e:
            module.fail_json(msg='Unable to get {0} configuration, error: {1}'.format(function_name, e))
    else:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        try:
            lambda_facts.update(client.list_functions(**params))
        except (BotoServerError, ClientError), e:
            module.fail_json(msg='Unable to get function list, error: {0}'.format(e))

    return lambda_facts


def alias_details(client, module):

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')
        try:
            lambda_facts.update(client.list_aliases(FunctionName=function_name, **params))
        except (BotoServerError, ClientError), e:
            module.fail_json(msg='Unable to get {0} aliases, error: {1}'.format(function_name, e))
    else:
        module.fail_json(msg='Parameter function_name required for query=aliases.')

    return lambda_facts


def policy_details(client, module):

    if module.params.get('max_items') or module.params.get('next_marker'):
        module.fail_json(msg='Cannot specify max_items nor next_marker for query=policy.')

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        try:
            # get_policy returns a JSON string so must convert to dict before reassigning to its key
            lambda_facts.update(Policy=json.loads(client.get_policy(FunctionName=function_name)['Policy']))
        except (BotoServerError, ClientError), e:
            module.fail_json(msg='Unable to get {0} policy, error: {1}'.format(function_name, e))
    else:
        module.fail_json(msg='Parameter function_name required for query=policy.')

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
    except (BotoServerError, ClientError), e:
        module.fail_json(msg=str(e))


    return lambda_facts


def version_details(client, module):

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        try:
            lambda_facts.update(client.list_versions_by_function(FunctionName=function_name, **params))
        except (BotoServerError, ClientError), e:
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
        mutually_exclusive=[],
        required_together=[]
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='Both boto and boto3 are required for this module.')

    # validate function_name if present
    function_name = module.params['function_name']
    if function_name:
        if not re.search('^[\w\-]+$', function_name):
            module.fail_json(
                    msg='Function name {0} is invalid. Names must contain only alphanumeric characters and hyphens.'.format(function_name)
            )
        if len(function_name) > 64:
            module.fail_json(msg='Function name "{0}" exceeds 64 character limit'.format(function_name))

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
