#!/usr/bin/python
# (c) 2016, Pierre Jodouin <pjodouin@virtualcomputing.solutions>
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

import hashlib
import base64
import os

try:
    import boto3
    from botocore.exceptions import ClientError, ParamValidationError, MissingParametersError
    from boto3.s3.transfer import S3Transfer
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


DOCUMENTATION = '''
---
module: lambda
short_description: Creates, updates or deletes AWS Lambda functions, configs and versions.
description:
    - This module allows the management of AWS Lambda functions and their related resources via the Ansible
      framework.  It is idempotent and supports "Check" mode. Use M(lambda_alias) to manage lambda function aliases,
      M(lambda_event) to manage event source mappings such as Kinesis streams, M(lambda_invoke)
      to execute a lambda function and M(lambda_facts) to gather facts relating to one or more lambda functions.

version_added: "2.2"

author: Pierre Jodouin (@pjodouin)
options:
  name:
    description:
      - The name you want to assign to the function. You can specify an unqualified function
        name (for example, "Thumbnail") or you can specify Amazon Resource Name (ARN) of the function
        (for example, 'arn:aws:lambda:us-west-2:account-id:function:ThumbNail'). AWS Lambda also allows you to
        specify only the account ID qualifier (for example, 'account-id:Thumbnail'). Note that the length
        constraint applies only to the ARN. If you specify only the function name, it is limited to 64 character
        in length.
    required: true
    aliases: [ "function_name" ]
  state:
    description:
      - Describes the desired state.
    required: true
    default: "present"
    choices: ["present", "absent"]
  runtime:
    description:
      - Runtime environment of the Lambda function. Cannot be changed after creating the function.
    required: true
  code_s3_bucket:
    description:
      - S3 bucket name where the .zip file containing your deployment package is stored.
        This bucket must reside in the same AWS region where you are creating the Lambda function.
    required: true
    aliases: ['s3_bucket']
  code_s3_key:
    description:
      - S3 object (the deployment package) key name you want to upload.
    required: true
    aliases: ['s3_key']
  code_s3_object_version:
    description:
      - S3 object (the deployment package) version you want to upload.
    required: false
    aliases: ['s3_object_version']
  local_path:
    description:
      - Complete local file path of the deployment package bundled in a ZIP archive.
    required: true
  handler:
    description:
      - The function within your code that Lambda calls to begin execution.
    required: true
  role:
    description:
      - The Amazon Resource Name (ARN) of the IAM role that Lambda assumes when it executes your function to access
        any other AWS resources.  If the role belongs to the same account, the simple role name can be used.
    required: true
  timeout:
    description:
      - The function execution time (in seconds) at which Lambda should terminate the function. Because the execution
        time has cost implications, we recommend you set this value based on your expected execution time.
    required: false
    default: 3
  memory_size:
    description:
      - The amount of memory, in MB, your Lambda function is given. Lambda uses this memory size to infer the amount of
        CPU and memory allocated to your function. Your function use-case determines your CPU and memory requirements.
        For example, a database operation might need less memory compared to an image processing function.
        The value must be a multiple of 64 and between 128 and 1536.
    required: false
    default: 128
  publish:
    description:
      - This boolean parameter is used to publish a version of the function from the current snapshot of $LATEST.
        The code and configuration cannot be modified after publication.
    required: false
    default: false
  description:
    description:
      - A short, user-defined function description. Lambda does not use this value. Assign a meaningful description
        as you see fit. There is no documented limit.
    required: false
  version:
    description:
      -  Version number of the Lambda function to be deleted. This parameter cannot be used with I(state=present).
         A value of 0 is ignored.
    required: false
  vpc_subnet_ids:
    description:
      -  If your Lambda function accesses resources in a VPC, you provide this parameter identifying the list of
         subnet IDs. These must belong to the same VPC. You must provide at least one subnet ID.
    required: false
    aliases: ['subnet_ids']
  vpc_security_group_ids:
    description:
      -  If your Lambda function accesses resources in a VPC, you provide this parameter identifying the list of
         security group IDs. You must provide at least one security group ID.
    required: false
    aliases: ['security_group_ids']
requirements:
    - boto3
extends_documentation_fragment:
    - aws
notes:
    - Parameter C(version) is only used to deleted a specific version of a lambda function.  It cannot be used for
      anything else as new versions get I(published) after which they cannot be modified.

'''

EXAMPLES = '''
---
# Simple example to create a lambda function and publish a version
- hosts: localhost
  gather_facts: no
  vars:
    state: present
    project_folder: /path/to/deployment/package
    deployment_package: lambda.zip
    account: 123456789012
    version_to_delete: 0
  tasks:
  - name: AWS Lambda Function
    lambda:
      state: "{{ state | default('present') }}"
      name: myLambdaFunction
      publish: True
      description: lambda function description
      code_s3_bucket: package-bucket
      code_s3_key: "lambda/{{ deployment_package }}"
      local_path: "{{ project_folder }}/{{ deployment_package }}"
      runtime: python2.7
      timeout: 5
      handler: lambda.handler
      memory_size: 128
      role: API2LambdaExecRole
      version: "{{ version_to_delete }}"
      vpc_subnet_ids:
        - subnet-9993085c
        - subnet-99910cc3
      vpc_security_group_ids:
        - sg-999b9ca8
  - name: show results
    debug: var=lambda_facts
'''

RETURN = '''
---
code_sha256:
    description: SHA256 hash of the code currently uploaded as $LATEST to Lambda
    returned: success
    type: string
    sample: IfQ6LngBe98CGyGgLRI0Q8M403AV7lWEdzm0jsiXluM=
code_size:
    description: size in bytes of the code package uploaded to Lambda
    returned: success
    type: integer
    sample: 8428
description:
    description: Description (provided by you) applied to the Lambda function
    returned: success
    type: string
    sample: This is a test description of a Lambda function
function_arn:
    description: Full ARN referring to the function. Will not include a version qualifier or alias
    returned: success
    type: string
    sample: arn:aws:lambda:us-west-2:123456789012:function:myFunction
function_name:
    description: Name selected for the function
    returned: success
    type: string
    sample: myFunction
handler:
    description: dotted notation for the handler function. For a file called "lambda.py" with a function called "handler" it would be "lambda.handler"
    returned: success
    type: string
    sample: lambda.handler
last_modified:
    description: Timestamp of the last modification of the function
    returned: success
    type: string
    sample: 2016-08-25T20:22:46.472+0000
memory_size:
    description: Memory allocated to the function (in megabytes)
    returned: success
    type: integer
    sample: 128
timeout:
    description: Timeout in seconds before the function is terminated by Lambda
    returned: success
    type: integer
    sample: 128
role:
    description: Full ARN of the role the Lambda function will execute as
    returned: success
    type: string
    sample: arn:aws:iam::123456789012:role/SomeLambdaRole
runtime:
    description: Language runtime for the function
    returned: success
    type: string
    sample: python2.7
'''

MIN_MEMORY_SIZE = 2 * 64
MAX_MEMORY_SIZE = 24 * 64


class AWSConnection:
    """
    Create the connection object and client objects as required.
    """

    def __init__(self, ansible_obj, resources, boto3=True):

        try:
            self.region, self.endpoint, aws_connect_kwargs = get_aws_connection_info(ansible_obj, boto3=boto3)

            self.resource_client = dict()
            if not resources:
                resources = ['lambda']

            resources.append('iam')

            for resource in resources:
                aws_connect_kwargs.update(dict(region=self.region,
                                               endpoint=self.endpoint,
                                               conn_type='client',
                                               resource=resource
                                               ))
                self.resource_client[resource] = boto3_conn(ansible_obj, **aws_connect_kwargs)

            # if region is not provided, then get default profile/session region
            if not self.region:
                self.region = self.resource_client['lambda'].meta.region_name

        except (ClientError, ParamValidationError, MissingParametersError) as e:
            ansible_obj.fail_json(msg="Unable to connect, authorize or access resource: {0}".format(e))

        try:
            self.account_id = self.resource_client['iam'].get_user()['User']['Arn'].split(':')[4]
        except (ClientError, ValueError, KeyError, IndexError):
            self.account_id = ''

    def client(self, resource='lambda'):
        return self.resource_client[resource]


def pc(key):
    """
    Changes python key into Pascale case equivalent. For example, 'this_function_name' becomes 'ThisFunctionName'.

    :param key:
    :return:
    """

    return "".join([token.capitalize() for token in key.split('_')])


def set_api_params(module, module_params):
    """
    Sets module parameters to those expected by the boto3 API.

    :param module:
    :param module_params:
    :return:
    """

    api_params = dict()

    for param in module_params:
        module_param = module.params.get(param, None)
        if module_param:
            api_params[pc(param)] = module_param

    return api_params


def validate_params(module, aws):
    """
    Performs basic parameter validation.

    :param module: Ansible module reference
    :param aws: AWS client connection
    :return:
    """

    function_name = module.params['function_name']

    # validate function name
    if not re.search('^[\w\-:]+$', function_name):
        module.fail_json(
            msg='Function name {0} is invalid. Names must contain only alphanumeric characters and hyphens.'.format(function_name)
        )
    if len(function_name) > 64:
        module.fail_json(msg='Function name "{0}" exceeds 64 character limit'.format(function_name))

    # validate local path of deployment package
    local_path = module.params['local_path']

    if not os.path.isfile(local_path):
        module.fail_json(msg='Invalid local file path for deployment package: {0}'.format(local_path))

    # parameter 'version' can only be used with state=absent
    if module.params['state'] == 'present' and module.params['version'] > 0:
        module.fail_json(msg="Cannot specify a version with state='present'.")

    # validate memory_size
    memory_size = module.params['memory_size']
    if memory_size not in range(MIN_MEMORY_SIZE, MAX_MEMORY_SIZE + 1, 64):
        module.fail_json(
            msg='Parameter "memory_size" must be between {0} and {1} and be a multiple of 64.'.format(MIN_MEMORY_SIZE, MAX_MEMORY_SIZE)
        )

    # check if 'role' needs to be expanded in full ARN format
    if not module.params['role'].startswith('arn:aws:iam:'):
        role = module.params['role']
        module.params['role'] = 'arn:aws:iam::{0}:role/{1}'.format(aws.account_id, role)

    return


def upload_to_s3(module, aws):
    """
    Upload local deployment package to s3.

    :param module: Ansible module reference
    :param aws: AWS client connection
    :return:
    """

    client = aws.client('s3')
    s3 = S3Transfer(client)

    local_path = module.params['local_path']
    s3_bucket = module.params['s3_bucket']
    s3_key = module.params['s3_key']

    try:
        s3.upload_file(local_path, s3_bucket, s3_key)
    except Exception as e:
        module.fail_json(msg='Error uploading package to s3: {0}'.format(e))

    return


def get_local_package_hash(module):
    """
    Returns the base64 encoded sha256 hash value for the deployment package at local_path.

    :param module:
    :return:
    """

    local_path = module.params['local_path']

    block_size = os.statvfs(local_path).f_bsize
    hash_lib = hashlib.sha256()

    with open(local_path, 'rb') as zip_file:
        for data_chunk in iter(lambda: zip_file.read(block_size), b''):
            hash_lib.update(data_chunk)

    return base64.b64encode(hash_lib.digest())


def get_lambda_config(module, aws):
    """
    Returns the lambda function configuration if it exists.

    :param module: Ansible module reference
    :param aws: AWS client connection
    :return:
    """

    client = aws.client('lambda')

    # set API parameters
    api_params = dict(FunctionName=module.params['function_name'])

    if module.params['version'] > 0:
        api_params.update(Qualifier=str(module.params['version']))

    # check if function exists and get facts, including sha256 hash
    try:
        results = client.get_function_configuration(**api_params)

    except (ClientError, ParamValidationError, MissingParametersError) as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            results = None
        else:
            module.fail_json(msg='Error retrieving function configuration: {0}'.format(e))

    return results


def lambda_function(module, aws):
    """
    Adds, updates or deletes lambda function code and configuration.

    :param module: Ansible module reference
    :param aws: AWS client connection
    :return dict:
    """
    client = aws.client('lambda')
    results = dict()
    changed = False
    current_state = 'absent'
    state = module.params['state']

    facts = get_lambda_config(module, aws)
    if facts:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present':

            # check if the code has changed
            s3_hash = facts.get(pc('code_sha256'))
            local_hash = get_local_package_hash(module)

            if s3_hash != local_hash:
                # code has changed so upload to s3
                if not module.check_mode:
                    upload_to_s3(module, aws)

                api_params = set_api_params(module, ('function_name', ))
                api_params.update(set_api_params(module, ('s3_bucket', 's3_key', 's3_object_version')))

                try:
                    if not module.check_mode:
                        results = client.update_function_code(**api_params)
                    changed = True
                except (ClientError, ParamValidationError, MissingParametersError) as e:
                    module.fail_json(msg='Error updating function code: {0}'.format(e))

            # check if config has changed
            config_changed = False
            config_params = ('role', 'handler', 'description', 'timeout', 'memory_size')
            for param in config_params:
                if module.params.get(param) != facts.get(pc(param)):
                    config_changed = True
                    break

            # check if VPC config has changed
            vpc_changed = False
            vpc_params = ('subnet_ids', 'security_group_ids')
            for param in vpc_params:
                current_vpc_config = facts.get('VpcConfig', dict())
                if sorted(module.params.get(param, [])) != sorted(current_vpc_config.get(pc(param), [])):
                    vpc_changed = True
                    break

            if config_changed or vpc_changed:
                api_params = set_api_params(module, ('function_name', ))
                api_params.update(set_api_params(module, config_params))

                if module.params.get('subnet_ids'):
                    api_params.update(VpcConfig=set_api_params(module, vpc_params))
                else:
                    # to remove the VPC config, its parameters must be explicitly set to empty lists
                    api_params.update(VpcConfig=dict(SubnetIds=[], SecurityGroupIds=[]))

                try:
                    if not module.check_mode:
                        results = client.update_function_configuration(**api_params)
                    changed = True
                except (ClientError, ParamValidationError, MissingParametersError) as e:
                    module.fail_json(msg='Error updating function config: {0}'.format(e))

            # check if function needs to be published
            if changed and module.params['publish']:
                api_params = set_api_params(module, ('function_name', 'description'))

                try:
                    if not module.check_mode:
                        results = client.publish_version(**api_params)
                    changed = True
                except (ClientError, ParamValidationError, MissingParametersError) as e:
                    module.fail_json(msg='Error publishing version: {0}'.format(e))

        else:  # create function
            if not module.check_mode:
                upload_to_s3(module, aws)

            api_params = set_api_params(module, ('function_name', 'runtime', 'role', 'handler'))
            api_params.update(set_api_params(module, ('memory_size', 'timeout', 'description', 'publish')))
            api_params.update(Code=set_api_params(module, ('s3_bucket', 's3_key', 's3_object_version')))
            api_params.update(VpcConfig=set_api_params(module, ('subnet_ids', 'security_group_ids')))

            try:
                if not module.check_mode:
                    results = client.create_function(**api_params)
                changed = True
            except (ClientError, ParamValidationError, MissingParametersError) as e:
                module.fail_json(msg='Error creating: {0}'.format(e))

    else:  # state = 'absent'
        if current_state == 'present':
            # delete the function
            api_params = set_api_params(module, ('function_name', ))

            version = module.params['version']
            if version > 0:
                api_params.update(Qualifier=str(version))

            try:
                if not module.check_mode:
                    results = client.delete_function(**api_params)
                changed = True
            except (ClientError, ParamValidationError, MissingParametersError) as e:
                module.fail_json(msg='Error deleting function: {0}'.format(e))

    return dict(changed=changed, **dict(results or facts))


def main():
    """
    Main entry point.

    :return dict: ansible facts
    """
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(required=False, default='present', choices=['present', 'absent']),
            function_name=dict(required=True, default=None, aliases=['name']),
            runtime=dict(required=True, default=None),
            role=dict(required=True, default=None),
            handler=dict(required=True, default=None),
            s3_bucket=dict(required=True, default=None, aliases=['code_s3_bucket']),
            s3_key=dict(required=True, default=None, aliases=['code_s3_key']),
            s3_object_version=dict(required=False, default=None, aliases=['code_s3_object_version']),
            local_path=dict(required=True, default=None),
            subnet_ids=dict(type='list', required=False, default=[], aliases=['vpc_subnet_ids']),
            security_group_ids=dict(type='list', required=False, default=[], aliases=['vpc_security_group_ids']),
            timeout=dict(type='int', required=False, default=3),
            memory_size=dict(type='int', required=False, default=128),
            description=dict(required=False, default=None),
            publish=dict(type='bool', required=False, default=False),
            version=dict(type='int', required=False, default=0),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[],
        required_together=[['subnet_ids', 'security_group_ids']]
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module.')

    aws = AWSConnection(module, ['lambda', 's3'])

    validate_params(module, aws)

    results = lambda_function(module, aws)

    module.exit_json(**camel_dict_to_snake_dict(results))


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
