# admin-services

* Description

The admin-services ansible scripts are a set of scripts that will be user by the admin server on startup to configure the application level admin components and configure remaining AWS components that couldn't be configured directly by the init cloud formation template

Will do the following:

1. Install Jenkins and any other supporting components. Attach to the EFS and configure Jenkins to use this directory for all persistent data.
2. A. If data already exists on the EFS, ensure Jenkins is running and terminate. This indicates an existing install and as such no other AWS components need to be configured. This pattern will occur if a host is terminated and a new one is brought up in it's place
2. B. If data is not found on the EFS, run initialization module to create default user and install basic plugins
3. Create custom policies
4. Create custom roles
5. Create internal keypairs
6. Create SSL Certificates
7. Apply new cloud formation template which will do the following: 
7.1 Assign EC2 and Admin Stack to correct roles and remove from temporary admin role
7.2 Create ALB to access admin server
7.3 Create S3 Bucket
8. Upload private key to s3 so it can be used by utility

* Usage

Scripts are intended to be run automatically on startup but they can be run manually for testing purposes. Must be run as root

ansible-playbook -i inventory/adminstack init-aws.yml --extra-vars "efsfqdn=<efsfqdn> username=<rootuname> password=<rootpw> email=<rootemail> utilityip=<utilityip> adminextip=<adminextip> baseami=<baseami> stackname=<stackname> region=<aws-region>" -vvvv