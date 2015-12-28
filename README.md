# ansible-lambda V0.1.0
Custom Ansible modules for AWS Lambda support

Will be using Boto3 but not through its CloudFormation functionality.

## Modules

### lambda_facts
Gathers facts related to AWS Lambda functions.

`> ansible localhost -m lambda_facts`

### lambda
Add, Update or Delete Lambda related resources.

`> ansible localhost -m lambda -a"state=present function_name=myFunction"`

## Playbook Examples

```yaml
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
```

## indented
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