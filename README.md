# ansible-lambda
####Version 0.1 
Custom Ansible modules for AWS Lambda support

Will be using Boto3 but not through its CloudFormation functionality.

## Modules

#### lambda_facts
Gathers facts related to AWS Lambda functions.

`> ansible localhost -m lambda_facts`

#### lambda
Add, Update or Delete Lambda related resources.

`> ansible localhost -m lambda -a"state=present function_name=myFunction"`

## Installation

Until this custom module is included in the Ansible distro, do the following to install the lambda modules in your Ansible environment:

1. Clone this repository or download the ZIP file.

2. copy the *.py modules to your installation custom module directory (usually /etc/ansible/modules).


## Playbook Syntax

```yaml
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
```

## Playbook Examples

```yaml
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
```

