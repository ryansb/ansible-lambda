# ansible-lambda
####Version 0.1 [![Build Status](https://travis-ci.org/pjodouin/ansible-lambda.svg)](https://travis-ci.org/pjodouin/ansible-lambda)

Custom Ansible modules for AWS Lambda support

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

`> ansible localhost -m lambda_invoke -a"function_name=myFunction"


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

