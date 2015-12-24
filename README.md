# ansible-lambda V0.0.0
Custom Ansible modules for AWS Lambda support

Just starting!  Will be using Boto3 but not through its CloudFormation functionality. 

## Modules

### lambda_facts

`> ansible localhost -m lambda_facts`

### lambda

`> ansible localhost -m lambda -a"state=present"`