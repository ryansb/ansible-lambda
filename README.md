# ansible-lambda
####Version 0.2 [![Build Status](https://travis-ci.org/pjodouin/ansible-lambda.svg)](https://travis-ci.org/pjodouin/ansible-lambda)

Custom Ansible modules for AWS Lambda support.  These modules help manage AWS Lambda resources including code, configuration, event source mappings and policy permissions.

## Requirements
- Boto3.

## Modules

#### lambda_facts
Gathers facts related to AWS Lambda functions.

`> ansible localhost -m lambda_facts`

#### lambda
Add, Update or Delete Lambda related resources.

`> ansible localhost -m lambda -a"state=present function_name=myFunction"`

#### lambda_invoke
Use to invoke a specific Lambda function.

`> ansible localhost -m lambda_invoke -a"function_name=myFunction"`

#### s3_lambda_event
Use to add an s3 event notification to lambda.

`> ansible localhost -m s3_lambda_event -a"function_arn=..."`


## Installation

Until these custom module are included in the Ansible distro, do the following to install the lambda modules in your Ansible environment:

1. Clone this repository or download the ZIP file.

2. copy the *.py modules to your installation custom module directory (usually /etc/ansible/modules).





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

