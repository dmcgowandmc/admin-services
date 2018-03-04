#!/usr/bin/python2.7

#Import Modules
import sys
import requests
import json
import base64
import time

#Import Classes
from HTMLParser import HTMLParser

#Because this is an ansible module
ANSIBLE_METADATA = {
        'metadata_version': '1.0',
        'status': ['First Release'],
        'supported_by': 'Douglas McGowan - dmcgowan@iinet.net.au'
}

DOCUMENTATION = '''
---
module: jekinscfg

short_description: Module to automate the setup of a new Jenkins Install.

version_added: "2.4"

description:
    - "Module to automate the setup of a new Jenkins Install. Once completed all recommended plugings will be installed and default user account will be created"

author:
    - Douglas McGowan (dmcgowan@iinet.net.au)
'''

EXAMPLES = '''
# A successful request where nothing changes (determined by the absence of a temporary password)
- name: A successful request where nothing changes
  jenkinscfg:
    username: root
    password: abcd1234
    email: email@myaddress.com

# pass in a message and have changed true (determined by the presence of a temporary password)
- name: A successfuly request where a change occurs
  jenkinscfg:
    username: root
    password: abcd1234
    email: email@myaddress.com

'''

from ansible.module_utils.basic import AnsibleModule

def run_module():
    #Default Vars. Might make these inputs eventually
    username = "admin"

    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        email=dict(type='str', required=True)
    )

    # Configuring result template
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # Once paramters are validated successfully, they are applied to the module object
    module = AnsibleModule(
        argument_spec=module_args,
    )

    #Begining Code Here
    password = getPassword()

    if password == "nopw":
        result['changed']=False
        result['original_message']=password
        result['message']="No Password Found indicates setup is complete. Module exiting"
    else:
        crumb = getCrumb(username,password)
        #crumb = getCrumb(module.params['username'],module.params['password'])
        pluginStatus = defaultPluginInstall(username, password, crumb)
        time.sleep(180) #Since checking current status of installed plugins, setting a time limit of 5 minutes to complete. Ideally it should do checks every few seconds to confirm modules have been installed
        createUserStatus = createRequiredUsers(username, password, crumb, module.params['username'], module.params['password'], module.params['email'])

        result['changed']=True
        result['original_message']="Plugin Status : " + str(pluginStatus.status_code) + "; Create User Status : " + str(createUserStatus.status_code)
        result['message']="Password found. We have installed default plugins and created default admin user. See original_message for further details"

    module.exit_json(**result)



#Get the initial password. If we fail to get the password, this generally means Jenkins is already setup and using proper credentials in a defined user
def getPassword():
        try:
                with open("/opt/jenkins_data/secrets/initialAdminPassword") as pwfile:
                        return pwfile.readline().strip()
        except:
                return "nopw"


#Begin the Login Process. From here we get our crumb
#WARNING : If initial password is incorrect, this will crap out with a generic json error. This is because the failure page is regular html instead of json
def getCrumb(username, password):
        url = "http://127.0.0.1:8080/crumbIssuer/api/json"
        headers = {
                "Content-Type": "application/json",
                "Authorization": "Basic " + base64.b64encode(username + ":" + password)
        }

        response = requests.get(url, headers=headers)


        for key, value in json.loads(response.text).iteritems():
                if key == "crumb":
                        crumb = value
        return crumb

#Trigger the installation of recommended plugins.
def defaultPluginInstall(username, password, crumb):
        url = "http://127.0.0.1:8080/pluginManager/installPlugins"
        headers = {
                "Content-Type": "application/json",
                "Jenkins-Crumb": crumb,
                "Authorization": "Basic " + base64.b64encode(username + ":" + password)
        }

        payload = {
                "dynamicLoad": "true",
                "plugins":[
                        "cloudbees-folder",
                        "antisamy-markup-formatter",
                        "build-timeout",
                        "credentials-binding",
                        "timestamper",
                        "ws-cleanup",
                        "ant",
                        "gradle",
                        "workflow-aggregator",
                        "github-branch-source",
                        "pipeline-github-lib",
                        "pipeline-stage-view",
                        "git",
                        "subversion",
                        "ssh-slaves",
                        "matrix-auth",
                        "pam-auth",
                        "ldap",
                        "email-ext",
                        "mailer"
                ],
                "Jenkins-Crumb": crumb
        }
        response = requests.post(url, headers=headers, json=payload)

        return response

#Create the default root user. This process will also take jenkins out of setup mode and into a mode you can actually use
def createRequiredUsers(username, password, crumb, root_username, root_password, email):
        url = "http://127.0.0.1:8080/setupWizard/createAdminUser"
        headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Jenkins-Crumb": crumb,
                "Authorization": "Basic " + base64.b64encode(username + ":" + password)
        }

        json_payload = {
               "username": root_username,
               "password1": root_password,
               "password2": root_password,
               "fullname": root_username,
               "email": email,
               "Jenkins-Crumb": crumb
        }

        form_payload = {
               "username": root_username,
               "password1": root_password,
               "password2": root_password,
               "fullname": root_username,
               "email": email,
               "Jenkins-Crumb": crumb,
               "json": json.dumps(json_payload),
               "core:apply": " ",
               "Submit": "Save",
               "json": json.dumps(json_payload)
        }
        response = requests.post(url, headers=headers, data=form_payload)

        return response


#Actual Execution Begins Here
def main():
    run_module()

if __name__ == '__main__':
    main()