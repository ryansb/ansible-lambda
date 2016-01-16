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
#           Main function
# ----------------------------------

def main():
    """
    Main entry point.

    :return dict: ansible facts
    """
    argument_spec = ec2_argument_spec()

    #TODO: Much to do.....


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
