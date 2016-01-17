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
module: s3_lambda_event
short_description: Creates, updates or deletes s3 notification events for Lambda functions.
description:
    - This module is used to create or delete s3 event notifications, which trigger Lambda functions.  
version_added: "2.0"
author: Pierre Jodouin (@pjodouin)
options:
  bucket:
    description:
      -  Bucket name
    required: true
    default: null
  lambda_function_arn:
    description:
      - Lambda cloud function ARN that Amazon S3 can invoke when it detects events of the specified type. 
    required: false
    aliases: [ "function" ]
  state:
    description:
      - Describes the desired state of the resource and defaults to "present"
    required: false
    default: "present"
    choices: ["present", "absent", "updated"]
  events:
    description:
      - List of bucket events for which to send notifications.
    required: false
    default: null
  id:
    description:
      -  Optional unique identifier for configurations in a notification configuration. If you don't 
         provide one, Amazon S3 will assign an ID. 
    required: false
    default: null 
  filter:
    description:
      - Container for object key name filtering rules. For information about key name filtering, go to 
        Configuring Event Notifications in the Amazon Simple Storage Service Developer Guide.
    required: false
'''


EXAMPLES = '''
---
# add an s3 event notification to a lambda function
- name: add event mapping
  s3_lambda_event:
    lambda_function_arn: arn:aws:lambda:region:id:function:my_function_name:my_alias
    events: [ 's3:ObjectCreated:*']

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
            if not isinstance(value, basestring):
                value = check_sub_params(value)

            api_params[pc(param)] = value
        else:
            if required:
                module.fail_json(msg='Parameter {0} required for this action on resource type {1}'.format(param, resource_type))

    return api_params


def check_sub_params(value):
    """
    Not so much checking as converting key case.  Let the API do most of the checking.

    :param value:
    :return:
    """

    if isinstance(value, dict):
        sub_params = dict()
        for key in value.keys():
            sub_params[pc(key)] = check_sub_params(value[key])
    elif isinstance(value, list):
        sub_params = list()
        for item in value:
            sub_params.append(check_sub_params(item))
    else:
        sub_params = value

    return sub_params


# ----------------------------------
#   Resource management functions
# ----------------------------------

def lambda_event_notification(client, module):
    """
    Adds, updates or deletes lambda event notifications in s3.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    results = dict()
    changed = False
    api_params = dict()
    current_state = None

    state = module.params.get('state')
    resource = 's3_lambda_event'

    required_params = ('bucket', )
    api_params.update(get_api_params(required_params, module, resource, required=True))

    # check if event notifications exist
    try:
        results = client.get_bucket_notification_configuration(**api_params)
        if 'NotificationConfiguration' in results:
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
            # delete the event notifications

            api_params.update(NotificationConfiguration=dict())

            try:
                results = client.put_bucket_notification_configuration(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error deleting {0}: {1}'.format(resource, e))

        elif state == 'present':
            # create event notifications

            required_params = ('lambda_function_configurations',)
            api_params.update(get_api_params(required_params, module, resource, required=True))

            bucket = api_params.pop('Bucket')
            api_params = dict(NotificationConfiguration=api_params, Bucket=bucket)

            try:
                results = client.put_bucket_notification_configuration(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error creating {0}: {1}'.format(resource, e))

        else:  
            # update the event notifications
            if current_state == 'absent':
                module.fail_json(msg='Must create event notification before updating it.')

            required_params = ('lambda_function_configurations',)
            api_params.update(get_api_params(required_params, module, resource, required=True))

            bucket = api_params.pop('Bucket')
            api_params = dict(NotificationConfiguration=api_params, Bucket=bucket)

            try:
                results = client.put_bucket_notification_configuration(**api_params)
                changed = True
            except ClientError, e:
                module.fail_json(msg='Error updating {0}: {1}'.format(resource, e))

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
        bucket=dict(default=None,required=True),
        lambda_function_configurations=dict(type='list', default=None, required=False),
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
        module.fail_json(msg='boto3 is required for this module.')

    try:
        region, endpoint, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        aws_connect_kwargs.update(dict(region=region,
                                       endpoint=endpoint,
                                       conn_type='client',
                                       resource='s3'
                                       ))
        client = boto3_conn(module, **aws_connect_kwargs)
    except ClientError, e:
        module.fail_json(msg="Can't authorize connection - {0}".format(e))
    except Exception, e:
        module.fail_json(msg="Connection Error - {0}".format(e))

    response = lambda_event_notification(client, module)

    results = dict(ansible_facts=dict(results=response['results']), changed=response['changed'])

    module.exit_json(**results)


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
