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
short_description: Creates, updates or deletes AWS Lambda functions, related configs, aliases and mappings.
description:
    - This module allows the mamangement of AWS Lambda functions and their related resources via the Ansible
      framework.  It provides CRUD functionality, is idempotent?? and supports the "Check" state??
version_added: "1.9"
author: Pierre Jodouin (@pjodouin)
options:
  type:
    description:
      - specifies the resource type on which to take action
    required: false
    choices: [ "alias", "code", "config", "mapping", "policy", "version" ]
    default: "code"
  function_name:
    description:
      - The name you want to assign to the function you are uploading. You can specify an unqualified function 
        name (for example, "Thumbnail") or you can specify Amazon Resource Name (ARN) of the function 
        (for example, 'arn:aws:lambda:us-west-2:account-id:function:ThumbNail'). AWS Lambda also allows you to
        specify only the account ID qualifier (for example, 'account-id:Thumbnail'). Note that the length
        constraint applies only to the ARN. If you specify only the function name, it is limited to 64 character 
        in length.
    required: false
    aliases: [ "function" ]
  state:
    description:
      - Describes the desired state of the resource and defaults to "present"
    required: false
    default: "present"
    choices: ["present", "absent", "updated"]
  runtime:
    description:
      - Runtime environment of the Lambda function.
    required: false
  code:
    description:
      - Dictionary of items which describe where to find the function code to be uploaded to AWS.  Typically, this
        is a simple file or deployment package bundled in a ZIP archive file.  The dictionary keys are s3_bucket,
        S3 Key name, s3_object_version and zip_file.
    required: false
  handler:
    description:
      - The function within your code that Lambda calls to begin execution.
    required: false
  role:
    description:
      - The Amazon Resource Name (ARN) of the IAM role that Lambda assumes when it executes your function to access 
        any other Amazon Web Services (AWS) resources.
    required: false
  timeout:
    description:
      - The function execution time at which Lambda should terminate the function. Because the execution time has cost 
        implications, we recommend you set this value based on your expected execution time. The default is 3 seconds.
    required: false
  memory:
    description:
      - The amount of memory, in MB, your Lambda function is given. Lambda uses this memory size to infer the amount of 
        CPU and memory allocated to your function. Your function use-case determines your CPU and memory requirements. 
        For example, a database operation might need less memory compared to an image processing function. The default 
        value is 128 MB. The value must be a multiple of 64 MB.
    required: false
  publish:
    description:
      - This boolean parameter can be used to request AWS Lambda to create the Lambda function and publish a version as 
        an atomic operation.
    required: false
  description:
    description:
      - A short, user-defined function description. Lambda does not use this value. Assign a meaningful description 
        as you see fit.
    required: false
  uuid:
    description:
      - The AWS Lambda assigned ID of the event source mapping.
    required: false
  name:
    description:
      -  Name of the function alias.
    required: false
  function_version:
    description:
      -  Version number of the Lambda function.
    required: false
    aliases: [ "version" ]
  qualifier:
    description:
      - You can specify this optional query parameter to specify function version or alias name in which case this 
        API will return all permissions associated with the specific ARN. If you don't provide this parameter, the 
        API will return permissions that apply to the unqualified function ARN.
    required: false
  statement_id:
    description:
      -  A unique statement identifier.
    required: false
    aliases: [ "sid" ]
  action:
    description:
      -  The AWS Lambda action you want to allow in this permission statement. Each Lambda action is a string starting
         with "lambda:" followed by the API name
    required: false
  principal:
    description:
      -  The principal who is getting this permission. It can be Amazon S3 service Principal ("s3.amazonaws.com") if
         you want Amazon S3 to invoke the function, an AWS account ID if you are granting cross-account permission, or
         any valid AWS service principal such as "sns.amazonaws.com".
    required: false
  source_account:
    description:
      -  The AWS account ID (without a hyphen) of the source owner. For example, if the SourceArn identifies a bucket,
         then this is the bucket owner's account ID. You can use this additional condition to ensure the bucket you
         specify is owned by a specific account.
    required: false
  source_arn:
    description:
      -  This is optional; however, when granting Amazon S3 permission to invoke your function, you should specify this
         field with the bucket Amazon Resource Name (ARN) as its value. This ensures that only events generated from
         the specified bucket can invoke the function.
    required: false
  starting_position:
    description:
      -  The position in the stream where AWS Lambda should start reading ('TRIM_HORIZON' or 'LATEST').
    required: false
    choices: [ "TRIM_HORIZON", "LATEST" ]
  enabled:
    description:
      -  Indicates whether AWS Lambda should begin polling the event source. By default, Enabled is true.
    required: false
  batch_size:
    description:
      -  The largest number of records that AWS Lambda will retrieve from your event source at the time of invoking
         your function. Your function receives an event with all the retrieved records. The default is 100 records.
    required: false
  event_source_arn:
    description:
      -  The Amazon Resource Name (ARN) of the Amazon Kinesis or the Amazon DynamoDB stream that is the event source.
         Any record added to this stream could cause AWS Lambda to invoke your Lambda function, it depends on the
         BatchSize . AWS Lambda POSTs the Amazon Kinesis event, containing records, to your Lambda function as JSON.
    required: false
  code_sha256:
    description:
      -  The SHA256 hash of the deployment package you want to publish. This provides validation on the code you are
         publishing. If you provide this parameter value must match the SHA256 of the HEAD version for the publication
         to succeed.
    required: false
extends_documentation_fragment: aws
'''

EXAMPLES = '''
---
# Simple example to create a lambda function and publish a version
- name: Create Lambda Function
  lambda:
    type: code
    function_name: myFunction
    state: present
    runtime: python2.7
    code:
      S3Bucket: lambda-function-packages
      S3Key: system1/lambda_deployment.zip
    timeout: 3
    handler: lambda.handler
    role: arn:aws:iam::999999999999:role/API2LambdaExecRole
    description: This is a Lambda function
    publish: True
  register: my_function_details
'''

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


# ----------------------------------
#          Helper functions
# ----------------------------------

def pc(key):
    """
    Changes python key into Pascale case equivalent. For example, 'this_function_name' becomes 'ThisFunctionName'.

    :param key:
    :return:
    """

    return "".join([token.capitalize() for token in key.split('_')])


def get_api_params(params, module, resource_type, required=False):
    """
    Check for presence of parameters, required or optional and change parameter case for API.

    :param params: AWS parameters needed for API
    :param module: Ansible module reference
    :param resource_type:
    :param required:
    :return:
    """

    api_params = dict()

    for param in params:
        value = module.params.get(param)
        if value:
            if param == 'code':
                value = check_code_params(module)

            api_params[pc(param)] = value
        else:
            if required:
                module.fail_json(msg='Parameter {0} required for this action on resource type {1}'.format(param, resource_type))

    return api_params


def check_code_params(module):
    """
    Not so much checking as converting key case.  Let the API do most of the checking.

    :param module:
    :return:
    """

    code_params = module.params.get('code')

    if not isinstance(code_params, dict):
        module.fail_json(msg="Parameter 'code' must be a dictionary. Found: {0}".format(code_params))

    api_params = dict()

    for key in ('zip_file', 's3_bucket', 's3_key', 's3_object_version'):
        if key in code_params:
            api_params[pc(key)] = code_params[key]

    return api_params


# ----------------------------------
#   Resource management functions
# ----------------------------------

def alias_resource(client, module):
    """
    Adds, updates or deletes lambda function aliases for specified version.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    results = dict()
    changed = False
    api_params = dict()
    current_state = None

    state = module.params.get('state')
    resource = 'alias'

    required_params = ('function_name', 'name')
    api_params.update(get_api_params(required_params, module, resource, required=True))

    # check if alias exists
    try:
        results = client.get_alias(**api_params)
        current_state = 'present'
    except ClientError, e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            current_state = 'absent'
        else:
            module.fail_json(msg='Error retrieving {0}: {1}'.format(resource, e))

    if state == current_state:
        # nothing to do but exit
        changed = False
    else:
        if state == 'absent':
            # delete function
            try:
                results = client.delete_alias(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error deleting {0}: {1}'.format(resource, e))

        elif state == 'present':
            # create alias
            required_params = ('function_version', )
            optional_params = ('description', )

            api_params.update(get_api_params(required_params, module, resource, required=True))
            api_params.update(get_api_params(optional_params, module, resource, required=False))

            try:
                results = client.create_alias(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error creating {0}: {1}'.format(resource, e))

        else:  
            # update the alias if necessary
            if current_state == 'absent':
                module.fail_json(msg='Must create alias before updating it.')

            optional_params = ('function_version', 'description')
            api_params.update(get_api_params(optional_params, module, resource, required=False))

            try:
                results = client.update_alias(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error updating {0}: {1}'.format(resource, e))

    return dict(changed=changed, results=results)


def lambda_code(client, module):
    """
    Adds, updates or deletes lambda function code.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """
    results = dict()
    changed = False
    api_params = dict()
    current_state = None
    last_modified = None

    state = module.params.get('state')
    resource = 'code'

    required_params = ('function_name',)
    api_params.update(get_api_params(required_params, module, resource, required=True))

    optional_params = ('qualifier',)
    api_params.update(get_api_params(optional_params, module, resource, required=False))

    # check if function exists and get facts
    try:
        results = client.get_function_configuration(**api_params)
        current_state = 'present'
        last_modified = results.get('LastModified')
        #TODO: need to determine how to retain short-term 'updated' state--will continusouly update until then
        #     if last_modified:
        #         current_state = 'updated'
    except ClientError, e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            current_state = 'absent'
            last_modified = None
        else:
            module.fail_json(msg='Error retrieving function {0}: {1}'.format(resource, e))

    if state == current_state:
        # nothing to do but exit
        changed = False             
    else:
        if state == 'absent':
            # delete function
            try:
                results = client.delete_function(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error deleting function {0}: {1}'.format(resource, e))

        elif state == 'present':
            # create the function
            required_params = ('code', 'runtime', 'role', 'handler')
            optional_params = ('memory_size', 'timeout', 'description', 'publish')

            api_params.update(get_api_params(required_params, module, resource, required=True))
            api_params.update(get_api_params(optional_params, module, resource, required=False))

            try:
                results = client.create_function(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error creating {0}: {1}'.format(resource, e))
        else:  
            # update the function if it exists
            if current_state == 'absent':
                module.fail_json(msg='Function {0} does not exist--must create before.'.format(module.params.get('function_name')))

            required_params = ('code', )
            optional_params = ('publish', )

            api_params.update(get_api_params(required_params, module, resource, required=True))
            api_params.update(get_api_params(optional_params, module, resource, required=False))

            try:
                results = client.update_function_code(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error updating function {0} code: {1}'.format(resource, e))

    return dict(changed=changed, results=results)


def config_details(client, module):
    """
    Updates function configuration details for a lambda functions if it exists.  Resource type 'code' should be used
    to create or delete lambda functions.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    results = dict()
    changed = False
    api_params = dict()
    current_state = None

    state = module.params.get('state')
    resource = 'config'

    required_params = ('function_name',)
    api_params.update(get_api_params(required_params, module, resource, required=True))

    fetch_api_params = api_params
    optional_params = ('qualifier',)
    fetch_api_params.update(get_api_params(optional_params, module, resource, required=False))

    # check if function exists and get facts
    try:
        results = client.get_function_configuration(**fetch_api_params)
        current_state = 'present'
    except ClientError, e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            current_state = 'absent'
        else:
            module.fail_json(msg='Error retrieving function {0}: {1}'.format(resource, e))

    if state == current_state:
        # nothing to do but exit
        changed = False
    else:
        if state == 'absent':
            # lambda functions cannot be deleted using resource type 'config'.
            module.fail_json(msg="Cannot delete lambda function using resource type 'config'.")

        elif state == 'present':
            # lambda functions cannot be created using resource type 'config'.
            module.fail_json(msg="Cannot create lambda function using resource type 'config'.")
        else:
            # update the function if it exists
            if current_state == 'absent':
                module.fail_json(msg='Must create function before updating its config.')

            optional_params = ('role', 'handler', 'description', 'timeout', 'memory_size')
            api_params.update(get_api_params(optional_params, module, resource, required=False))

            try:
                results = client.update_function_configuration(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error updating function {0}: {1}'.format(resource, e))

    return dict(changed=changed, results=results)


def mapping_resource(client, module):
    """
    Adds, updates or deletes lambda event source mappings.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    results = dict()
    changed = False
    api_params = dict()
    current_state = None

    state = module.params.get('state')
    resource = 'mapping'

    required_params = ('uuid',)
    fetch_api_params = get_api_params(required_params, module, resource, required=True)

    # check if mapping exists
    try:
        results = client.get_event_source_mapping(**fetch_api_params)
        current_state = 'present'
    except ClientError, e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            current_state = 'absent'
        else:
            module.fail_json(msg='Error retrieving {0}: {1}'.format(resource, e))

    if state == current_state:
        # nothing to do but exit
        changed = False
    else:
        if state == 'absent':
            # delete event source mapping
            try:
                results = client.delete_event_source_mapping(**fetch_api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error deleting {0}: {1}'.format(resource, e))

        elif state == 'present':
            # create event source mapping
            required_params = ('function_name', 'event_source_arn', 'starting_position')
            optional_params = ('enabled', 'batch_size')

            api_params.update(get_api_params(required_params, module, resource, required=True))
            api_params.update(get_api_params(optional_params, module, resource, required=False))

            try:
                results = client.create_event_source_mapping(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error creating {0}: {1}'.format(resource, e))

        else:
            # update the event source mapping
            if current_state == 'absent':
                module.fail_json(msg='Must create event source mapping before updating it.')

            required_params = ('uuid',)
            optional_params = ('function_name', 'enabled', 'batch_size')

            api_params.update(get_api_params(required_params, module, resource, required=True))
            api_params.update(get_api_params(optional_params, module, resource, required=False))

            try:
                results = client.update_alias(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error updating {0}: {1}'.format(resource, e))

    return dict(changed=changed, results=results)


def policy_resource(client, module):
    """
    Returns policy attached to a lambda function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    results = dict()
    changed = False
    api_params = dict()
    current_state = None

    state = module.params.get('state')
    resource = 'policy'

    required_params = ('function_name',)
    api_params.update(get_api_params(required_params, module, resource, required=True))

    optional_params = ('qualifier',)
    api_params.update(get_api_params(optional_params, module, resource, required=False))

    # check if function exists
    try:
        # get_policy returns a JSON string so must convert to dict before reassigning to its key
        policy_results = client.get_policy(**api_params)
        policy_results['Policy'] = json.loads(policy_results.get('Policy', '{}'))
    except ClientError, e:
        module.fail_json(msg='Error retrieving {0}: {1}'.format(resource, e))

    # now that we have the policy, check if required permission statement is present
    required_params = ('statement_id',)
    api_params.update(get_api_params(required_params, module, resource, required=True))

    current_state = 'absent'
    for statement in policy_results['Policy']['Statement']:
        if statement['Sid'] == api_params['StatementId']:
            results = statement
            current_state = 'present'
            break

    if state == current_state:
        # nothing to do but exit
        changed = False
    else:
        if state == 'absent':
            # remove permission
            try:
                results = client.remove_permission(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error removing policy permission: {0}'.format(e))

        elif state == 'present':

            required_params = ('statement_id', 'action', 'principal', )
            api_params.update(get_api_params(required_params, module, resource, required=True))

            optional_params = ('source_arn', 'source_account')
            api_params.update(get_api_params(optional_params, module, resource, required=False))

            try:
                results = client.add_permission(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error adding permission to policy: {0}'.format(e))

        else:
            # Policy permission cannot be updated
            module.fail_json(msg="Cannot update policy permission. Use 'present' or 'absent' only.")

    return dict(changed=changed, results=results)


def publish_version(client, module):
    """
    Publishes a version of your function from the current snapshot of HEAD.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    results = dict()
    changed = False
    api_params = dict()
    current_state = None

    state = module.params.get('state')
    resource = 'version'

    required_params = ('function_name',)
    api_params.update(get_api_params(required_params, module, resource, required=True))

    # check if function exists and get facts
    try:
        results = client.get_function_configuration(**api_params)
        current_state = 'present'
    except ClientError, e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            current_state = 'absent'
        else:
            module.fail_json(msg='Error retrieving function: {1}'.format(e))

    if state == current_state:
        # nothing to do but exit
        changed = False
    else:
        if state == 'absent':
            # lambda functions cannot be deleted using resource type 'config'.
            module.fail_json(msg="Cannot delete lambda function version using resource type 'version'.")

        elif state == 'present':
            # lambda functions cannot be created using resource type 'config'.
            module.fail_json(msg="Cannot create lambda function using resource type 'config'.")
        else:
            # update will publish a new version of the lambda function
            if current_state == 'absent':
                module.fail_json(msg='Must create function before publishing a version.')

            optional_params = ('code_sha256', 'description')
            api_params.update(get_api_params(optional_params, module, resource, required=False))

            try:
                results = client.publish_version(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error updating function {0}: {1}'.format(resource, e))

    return dict(changed=changed, results=results)


# ----------------------------------
#           Main function
# ----------------------------------

def main():
    """
    Main entry point.

    :return dict: ansible facts
    """
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', required=False, choices=['present', 'absent', 'updated']),
        function_name=dict(required=False, default=None, aliases=['function']),
        type=dict(default='code', required=False, choices=['alias', 'code', 'config', 'mapping', 'policy', 'version']),
        runtime=dict(default=None, required=False),
        role=dict(default=None, required=False),
        handler=dict(default=None, required=False),
        code=dict(type='dict', default=None, required=False),
        timeout=dict(type='int', default=3, required=False),
        memory_size=dict(type='int', default=128, required=False),
        publish=dict(type='bool', default=False, required=False),
        name=dict(default=None, required=False),
        function_version=dict(default=None, required=False, aliases=['version']),
        qualifier=dict(default=None, required=False),
        statement_id=dict(default=None, required=False, aliases=['sid']),
        action=dict(default=None, required=False),
        principal=dict(default=None, required=False),
        source_account=dict(default=None, required=False),
        source_arn=dict(default=None, required=False),
        description=dict(default=None, required=False),
        uuid=dict(default=None, required=False),
        starting_position=dict(default=None, required=False, choices=['TRIM_HORIZON', 'LATEST']),
        enabled=dict(type='bool', default=True, required=False),
        batch_size=dict(type='int', default=100, required=False),
        event_source_arn=dict(default=None, required=False),
        code_sha256=dict(default=None, required=False)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        mutually_exclusive=[],
        required_together=[]
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module and can coexist with boto.')

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
    except ClientError, e:
        module.fail_json(msg="Can't authorize connection - {0}".format(e))

    invocations = {
        'alias': alias_resource,
        'code': lambda_code,
        'config': config_details,
        'mapping': mapping_resource,
        'policy': policy_resource,
        'version': publish_version,
    }
    response = invocations[module.params.get('type')](client, module)

    results = dict(ansible_facts=dict(results=response['results']), changed=response['changed'])
    module.exit_json(**results)


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
