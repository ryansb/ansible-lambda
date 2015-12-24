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
module: lambda
short_description: Creates/Updates/Deletes AWS Lambda functions, related configs, aliases, mappings... etc.
    using AWS API methods (boto3)
description:
    - Gets various details related to Lambda functions, including aliases, versions and event source mappings
version_added: "2.0"
author: Pierre Jodouin (@pjodouin)
requirements: [ botocore, boto3 ]
options:
  type:
    description:
      - specifies the resource type on which to take action
    required: False
    choices: [
            'alias',
            'code',
            'config',
            'mapping',
            'policy',
            'version',
            ],
    default: 'all'
  function_name:
    description:
      - The name of the lambda function.
     required: false
  max_items:
    description:
      - Maximum number of items to return for various list requests
    required: false
  next_marker:
    description:
      - "Some queries such as 'versions' or 'mappings' will return a maximum
        number of entries - EG 100. If the number of entries exceeds this maximum
        another request can be sent using the NextMarker entry from the first response
        to get the next page of results"
    required: false

  state:
  runtime:
  code:
  handler:
  role:
  timeout:
  memory:
  publish: ???

extends_documentation_fragment:
  - aws
'''

EXAMPLES = '''
# Simple example of
'''

RETURN = '''
ansible_facts:
    description: ?? lambda function related facts ??
    type: dict
'''

try:
    # import boto
    import boto3
    # from boto.exception import BotoServerError, NoAuthHandlerFound
    from botocore.exceptions import *
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def alias_resource(client, module):
    """
    Adds, updates or deletes lambda function aliases for specified version.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    state = module.params.get('state')
    function_name = module.params.get('function_name')
    if not function_name:
        module.fail_json(msg='Parameter function_name required for resource type alias.')

    name = module.params.get('name')
    if not name:
        module.fail_json(msg='Parameter name required for resource type alias.')

    current_state = None
    changed = False
    response = dict()

    # check if function exists
    try:
        response = client.get_alias(
            FunctionName=function_name,
            Name=name,
        )
        current_state = 'present'
    except ClientError, e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            current_state = 'absent'
        else:
            module.fail_json(msg='Boto3 Client error: {0}'.format(e))

    if state == current_state:
        changed = False
    else:
        if state == 'absent':
            # delete function
            try:
                results = client.delete_alias(
                    FunctionName=function_name,
                    Name=name
                )
                changed = True
            except ClientError, e:
                module.fail_json(msg='Boto3 Client error: {0}'.format(e))

        elif state == 'present':

            version = module.params.get('version')
            if not version:
                module.fail_json(msg='Parameter version required to create resource type alias.')

            changed = False
            response = dict()
            try:
                response = client.create_alias(
                    FunctionName=function_name,
                    Name=name,
                    FunctionVersion=version,
                    Description=module.params.get('description')
                )
                changed = True
            except ClientError, e:
                module.fail_json(msg='Unable to create alias {0} for {1}:{2}, error: {3}'.format(name, function_name, version, e))

        else:  # state == 'updated'
            # update the function if necessary
            if current_state == 'absent':
                module.fail_json(msg='Function {0} does not exist--must create before.'.format(module.params.get('function_name')))

            version = module.params.get('version')
            if not version:
                module.fail_json(msg='Parameter version required to update resource type alias.')

            try:
                response = client.update_alias(
                    FunctionName=function_name,
                    Name=name,
                    FunctionVersion=version,
                    Description=module.params.get('description')

                )
                changed = True
            except ClientError, e:
                module.fail_json(msg='Boto3 Client error: {0}'.format(e))

    return dict(changed=changed, response=response)


def lambda_code(client, module):
    """
    Adds, updates or deletes lambda function code.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    results = dict()

    code = module.params.get('code')
    state = module.params.get('state')

    current_state = None
    last_modified = None
    # check if function exists
    try:
        response = client.get_function_configuration(FunctionName=module.params['function_name'])
        current_state = 'present'
        last_modified = response.get('LastModified')
        #TODO: need to determine how to retain short-term 'updated' state--will continusouly update until then
        #     if last_modified:
        #         current_state = 'updated'
    except ClientError, e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            current_state = 'absent'
            last_modified = None
        else:
            module.fail_json(msg='Boto3 Client error: {0}'.format(e))

    if state == current_state:
        changed = False
    else:
        if state == 'absent':
            # delete function
            try:
                results = client.delete_function(
                    FunctionName=module.params.get('function_name'),
                )
                changed = True
            except ClientError, e:
                module.fail_json(msg='Boto3 Client error: {0}'.format(e))

        elif state == 'present':
            # create the function
            try:
                results = client.create_function(
                    FunctionName=module.params.get('function_name'),
                    Runtime=module.params.get('runtime'),
                    Role=module.params.get('role'),
                    Handler=module.params.get('handler'),
                    Code=module.params.get('code'),
                    Description=module.params.get('description'),
                    Timeout=module.params.get('timeout'),
                    MemorySize=module.params.get('memory_size'),
                    Publish=module.params.get('publish')
                )
                changed = True
            except ClientError, e:
                module.fail_json(msg='Boto3 Client error: {0}'.format(e))
        else:  # state == 'updated'
            # update the function if necessary
            if current_state == 'absent':
                module.fail_json(msg='Function {0} does not exist--must create before.'.format(module.params.get('function_name')))

            try:
                results = client.update_function_configuration(
                    FunctionName=module.params.get('function_name'),
                    Role=module.params.get('role'),
                    Handler=module.params.get('handler'),
                    Description=module.params.get('description'),
                    Timeout=module.params.get('timeout'),
                    MemorySize=module.params.get('memory_size')
                )
                changed = True
            except ClientError, e:
                module.fail_json(msg='Boto3 Client error: {0}'.format(e))

    return dict(changed=changed,
                code=dict(state=state,
                          last_mofidied=results.get('LastModified') or last_modified,
                          function_name=module.params['function_name']
                          )
                )


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
        except ClientError, e:
            module.fail_json(msg='Unable to get {0} configuration, error: {1}'.format(function_name, e))
    else:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        try:
            lambda_facts.update(client.list_functions(**params))
        except ClientError, e:
            module.fail_json(msg='Unable to get function list, error: {0}'.format(e))

    return lambda_facts


def mapping_resource(client, module):
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
    except ClientError, e:
        module.fail_json(msg='Unable to get source event mappings, error: {0}'.format(e))

    return lambda_facts


def policy_resource(client, module):
    """
    Returns policy attached to a lambda function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    state = module.params.get('state')
    function_name = module.params.get('function_name')
    qualifier = module.params.get('qualifier')
    if not function_name:
        module.fail_json(msg='Parameter function_name required for resource type policy.')

    current_state = None
    changed = False
    response = dict()

    # check if function exists
    try:
        # get_policy returns a JSON string so must convert to dict before reassigning to its key
        response = client.get_policy(
            FunctionName=function_name,
            Qualifier=qualifier
        )
        response['Policy'] = json.loads(response.get('Policy', '{}'))
        current_state = 'present'
    except ClientError, e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            current_state = 'absent'
        else:
            module.fail_json(msg='Boto3 Client error: {0}'.format(e))

    if state == current_state:
        changed = False
    else:
        if state == 'absent':

            statement_id = module.params.get('statement_id')
            if not statement_id:
                module.fail_json(msg='Parameter statement_id required to remove resource type policy.')

            # remove permission
            try:
                response = client.remove_permission(
                    FunctionName=function_name,
                    StatementId=statement_id,
                    Qualifier=qualifier
                )
                changed = True
            except ClientError, e:
                module.fail_json(msg='Boto3 Client error: {0}'.format(e))

        elif state in ('present', 'updated'):

            statement_id = module.params.get('statement_id')
            if not statement_id:
                module.fail_json(msg='Parameter statement_id required to add permission to policy-type resource.')

            action = module.params.get('action')
            if not action:
                module.fail_json(msg='Parameter action required to add permission to policy-type resource.')

            principal = module.params.get('principal')
            if not principal:
                module.fail_json(msg='Parameter principal required to add permission to policy-type resource.')

            qualifier = module.params.get('qualifier')
            source_arn = module.params.get('source_arn')
            source_account = module.params.get('qualifier')

            try:
                response = client.add_permission(
                    FunctionName=function_name,
                    StatementId=statement_id,
                    Qualifier=qualifier,
                    Action=action,
                    Principal=principal,
                    SourceArn=source_arn,
                    SourceAccount=source_account
                )
                changed = True
            except ClientError, e:
                module.fail_json(msg='Unable to add permission to {0} to {1}:{2}, error: {3}'.format(statement_id, function_name, qualifier, e))

        else:  # state == 'updated'
            # update the function if necessary
            #TODO needs to be completed
            pass

    return dict(changed=changed, response=response)


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
        except ClientError, e:
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
        state=dict(default=None, required=True, choices=['present', 'absent', 'updated']),
        function_name=dict(required=False, default=None),
        type=dict(default=None, required=True, choices=['alias', 'code', 'config', 'mapping', 'policy', 'version']),
        runtime=dict(default=None, required=False),
        role=dict(default=None, required=False),
        handler=dict(default=None, required=False),
        code=dict(type='dict', default=None, required=False),
        description=dict(default=None, required=False),
        timeout=dict(type='int', default=3, required=False),
        memory_size=dict(type='int', default=128, required=False),
        publish=dict(type='bool', default=True, required=False),
        name=dict(default=None, required=False),
        version=dict(default=None, required=False),
        qualifier=dict(default=None, required=False),
        statement_id=dict(default=None, required=False),
        action=dict(default=None, required=False),
        principal=dict(default=None, required=False),
        source_account=dict(default=None, required=False),
        source_arn=dict(default=None, required=False),
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

    # validate code
    code = module.params['code']

    try:
        #TODO: don't want to use devel branch so wait until boto3_connect is in main release branch -- use boto3.client until then
        # region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)
        # client = boto_conn(module, conn_type='client', resource='lambda', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        client = boto3.client('lambda')
    except Exception, e:
        module.fail_json(msg="Can't authorize connection - {0}".format(e))

    invocations = {
        'alias': alias_resource,
        'code': lambda_code,
        'config': config_details,
        'mapping': mapping_resource,
        'policy': policy_resource,
        'version': version_details,
    }
    lambda_facts = invocations[module.params.get('type')](client, module)

    # remove unnecessary ResponseMetadata from ansible facts before returning results
    if 'ResponseMetadata' in lambda_facts:
        del lambda_facts['ResponseMetadata']
    changed = lambda_facts['changed']
    results = dict(ansible_facts=lambda_facts, changed=changed)
    module.exit_json(**results)


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
