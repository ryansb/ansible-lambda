#!/usr/bin/python
# This module is a candidate for Ansible module extras.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: lambda_facts
short_description: Gathers AWS Lambda function details as Ansible facts 
description:
    - Gathers various details related to Lambda functions, including aliases, versions and event source mappings.
version_added: "2.0"
author: Pierre Jodouin (@pjodouin)
requirements: [ boto3 ]
options:
  query:
    description:
      - Specifies the resource type for which to gather facts.  Leave blank to retrieve all facts.
    required: false
    choices: [
            "aliases",
            "all",
            "config",
            "mappings",
            "policy",
            "versions",
            ]
    default: "all"
  function_name:
    description:
      - The name of the lambda function for which facts are requested.
    required: false
    default: none
  max_items:
    description:
      - Maximum number of items to return for various fact requests.
    required: false
    default: none
  next_marker:
    description:
      - "Some queries such as 'versions' or 'mappings' will return a maximum
        number of entries - EG 100. If the number of entries exceeds this maximum
        another request can be sent using the NextMarker entry from the first response
        to get the next page of results."
    required: false
    default: none
extends_documentation_fragment:
  - aws
'''

EXAMPLES = '''
---
# Simple example of listing all info for a function
- name: List all for a specific function
  lambda_facts:
    query: all
    function_name: myFunction
  register: my_function_details
# List all versions of a function
- name: List function versions
  lambda_facts:
    query: versions
    function_name: myFunction
  register: my_function_versions
# List all lambda functions
- name: List all functions
  lambda_facts:
    query: versions
    max_items: 20
- name: show Lambda facts
  debug: var=Versions
'''

RETURN = '''
ansible_facts:
    description: lambda function related facts
    type: dict
'''

try:
    import boto
    import boto3
    from boto.exception import BotoServerError, NoAuthHandlerFound
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def alias_details(client, module):
    """
    Returns list of aliases for a specified function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

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


def all_details(client, module):
    """
    Returns all lambda related facts.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

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
    """
    Returns configuration details for one or all lambda functions.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

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


def mapping_details(client, module):
    """
    Returns all lambda event source mappings.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    lambda_facts = dict()
    params = dict()

    if module.params.get('function_name'):
        params['FunctionName'] = module.params.get('function_name')

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    if module.params.get('next_marker'):
        params['Marker'] = module.params.get('next_marker')

    try:
        lambda_facts.update(client.list_event_source_mappings(**params))
    except (BotoServerError, ClientError), e:
        module.fail_json(msg='Unable to get source event mappings, error: {0}'.format(e))

    return lambda_facts


def policy_details(client, module):
    """
    Returns policy attached to a lambda function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

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


def version_details(client, module):
    """
    Returns all lambda function versions.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

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
            module.fail_json(msg='Unable to get {0} versions, error: {1}'.format(function_name, e))
    else:
        module.fail_json(msg='Parameter function_name required for query=versions.')

    return lambda_facts


def main():
    """
    Main entry point.

    :return dict: ansible facts
    """
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            function_name=dict(required=False, default=None),
            query=dict(required=False, choices=['aliases', 'all', 'config', 'mappings', 'policy',  'versions'], default='all'),
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

    try:
        #TODO: don't want to use devel branch so wait until boto3_connect is in main release branch -- use boto3.client until then
        # region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)
        # client = boto_conn(module, conn_type='client', resource='lambda', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        client = boto3.client('lambda')
    except NoAuthHandlerFound, e:
        module.fail_json(msg="Can't authorize connection - {0}".format(e))

    invocations = {
        'aliases': alias_details,
        'all': all_details,
        'config': config_details,
        'mappings': mapping_details,
        'policy': policy_details,
        'versions': version_details,
    }
    lambda_facts = invocations[module.params.get('query')](client, module)

    # remove unnecessary ResponseMetadata from ansible facts before returning results
    if 'ResponseMetadata' in lambda_facts:
        del lambda_facts['ResponseMetadata']
    results = dict(ansible_facts=lambda_facts, changed=False)
    module.exit_json(**results)


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
