#!/usr/bin/python

'''
AWS Lambda WIP
'''

import os
import json

import time
import re
import sys



# contstant(s)
MAX_TEMPLATE_BODY = 51200

try:
    import boto3
    # import boto
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def boto_exception(err):
    '''generic error message handler'''
    if hasattr(err, 'error_message'):
        error = err.error_message
    elif hasattr(err, 'message'):
        error = err.message
    else:
        error = '%s: %s' % (Exception, err)

    return error



def main():
    argument_spec = dict() #ec2_argument_spec()
    argument_spec.update(dict(
            aws_profile=dict(required=False, default=None),
            function_name=dict(required=False, default=None),
            show_versions=dict(required=False, default=False, type='bool'),
            max_items=dict(type='int'),
            next_marker=dict()
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module and can coexist with boto.')

    function_name = module.params['function_name']

    # validate function_name
    if function_name:
        if not re.search('^[a-zA-z][a-zA-Z0-9\-_]+$', function_name):
            module.fail_json(msg='Lambda name %s is invalid. Names must contain only alphanumeric characters and hyphens and must start with an alphabetic character.' % function_name)

        if len(function_name) > 64:
            module.fail_json(msg='Lambda name "%s" exceeds 255 character limit' % function_name)

    lambda_facts = dict()

    c = boto3.client('lambda')
    if function_name:
        try:
            lambda_facts.update(c.get_function_configuration(FunctionName=function_name))
            lambda_facts.update(c.list_aliases(FunctionName=function_name))
            ret = c.get_policy(FunctionName=function_name)
            ret['Policy'] = json.loads(ret['Policy'])
            lambda_facts.update(ret)
            show_versions = module.params['show_versions']
            if show_versions:
                lambda_facts.update(c.list_versions_by_function(FunctionName=function_name))
        except Exception as e:
            module.fail_json(msg=str(e))
    else:
        try:
            params = dict()
            if module.params.get('max_items'):
                params['MaxItems'] = module.params.get('max_items')

            if module.params.get('next_marker'):
                params['Marker'] = module.params.get('next_marker')

            lambda_facts.update(c.list_functions(**params))
            lambda_facts.update(c.list_event_source_mappings(**params))
        except Exception as e:
            module.fail_json(msg=str(e))

    del lambda_facts['ResponseMetadata']
    results = dict(ansible_facts=lambda_facts, changed=False)
    module.exit_json(**results)

# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
