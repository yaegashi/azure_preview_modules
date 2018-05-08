#!/usr/bin/python
#
# Copyright (c) 2017 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_webapp
version_added: "2.5"
short_description: Manage Web App instance.
description:
    - Create, update and delete instance of Web App.

options:
    resource_group:
        description:
            - Name of the resource group to which the resource belongs.
        required: True
    name:
        description:
            - Unique name of the app to create or update. To create or update a deployment slot, use the {slot} parameter.
        required: True
    kind:
        description:
            - Kind of resource.
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    enabled:
        description:
            - <code>true</code> if the app is enabled; otherwise, <code>false</code>. Setting this value to false disables the app (takes the app offline).

    server_farm_id:
        description:
            - "Resource ID of the associated App Service plan, formatted as:
               '/subscriptions/{subscriptionID}/resourceGroups/{groupName}/providers/Microsoft.Web/serverfarms/{appServicePlanName}'."
    reserved:
        description:
            - <code>true</code> if reserved; otherwise, <code>false</code>.

    scm_site_also_stopped:
        description:
            - <code>true</code> to stop SCM (KUDU) site when the app is stopped; otherwise, <code>false</code>. The default is <code>false</code>.
    hosting_environment_profile:
        description:
            - App Service Environment to use for the app.
        suboptions:
            id:
                description:
                    - Resource ID of the App Service Environment.
    client_affinity_enabled:
        description:
            - "<code>true</code> to enable client affinity; <code>false</code> to stop sending session affinity cookies, which route client requests in the
               same session to the same instance. Default is <code>true</code>."
    client_cert_enabled:
        description:
            - "<code>true</code> to enable client certificate authentication (TLS mutual authentication); otherwise, <code>false</code>. Default is
               <code>false</code>."

    host_names_disabled:
        description:
            - <code>true</code> to disable the public hostnames of the app; otherwise, <code>false</code>.
            -  If <code>true</code>, the app is only accessible via API management process.

    container_size:
        description:
            - Size of the function container.

    daily_memory_time_quota:
        description:
            - Maximum allowed daily memory-time quota (applicable on dynamic apps only).

    https_only:
        description:
            - "HttpsOnly: configures a web site to accept only https requests. Issues redirect for"
            - http requests
    identity:
        description:
        suboptions:
            type:
                description:
                    - Type of managed service identity.
    skip_dns_registration:
        description:
            - If true web app hostname is not registered with DNS on creation. This parameter is
            -  only used for app creation.
    skip_custom_domain_verification:
        description:
            - If true, custom (non *.azurewebsites.net) domains associated with web app are not verified.
    force_dns_registration:
        description:
            - If true, web app hostname is force registered with DNS.
    ttl_in_seconds:
        description:
            - "Time to live in seconds for web app's default domain name."
    site_config:
        description:
            - Site Configuration.
        suboptions:
            app_settings:
                description: List of application settings.
                key:
                    description: Key of application setting.
                value:
                    description: Value of application setting.
            java_container:
                description: Java container.
                default: ""
            java_version:
                description: Java version.
            linux_fx_version:
                description: Linux App Framework and version
            always_on:
                description: True if Always On is enabled; Otherwise, False.
                default: True
            number_of_works:
                description: Number of workers.
                default: 1



    state:
      description:
        - Assert the state of the Web App.
        - Use 'present' to create or update an Web App and 'absent' to delete it.
      default: present
      choices:
        - absent
        - present

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create (or update) Web App
    azure_rm_webapp:
      resource_group: NOT FOUND
      name: NOT FOUND
      location: eastus
      skip_dns_registration: NOT FOUND
      skip_custom_domain_verification: NOT FOUND
      force_dns_registration: NOT FOUND
      ttl_in_seconds: NOT FOUND
'''

RETURN = '''
id:
    description:
        - Resource Id.
    returned: always
    type: str
    sample: id
state:
    description:
        - Current state of the app.
    returned: always
    type: str
    sample: state
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from msrest.serialization import Model
    from azure.mgmt.web.models import (
        site_config, app_service_plan, hosting_environment_profile
    )
except ImportError:
    # This is handled in azure_rm_common
    pass


site_config_spec = dict(
    app_settings=dict(type='list')
)


def create_app_service_plan():
    return True


def create_site_config():
    return True


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMWebApps(AzureRMModuleBase):
    """Configuration class for an Azure RM Web App resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            kind=dict(
                type='str'
            ),
            location=dict(
                type='str'
            ),
            enabled=dict(
                type='str',
                default=True
            ),
            server_farm_id=dict(
                type='str'
            ),
            reserved=dict(
                type='str'
            ),
            scm_site_also_stopped=dict(
                type='str'
            ),
            hosting_environment_profile=dict(
                type='dict'
            ),
            client_affinity_enabled=dict(
                type='str'
            ),
            client_cert_enabled=dict(
                type='str'
            ),
            host_names_disabled=dict(
                type='str'
            ),
            container_size=dict(
                type='int'
            ),
            daily_memory_time_quota=dict(
                type='int'
            ),
            https_only=dict(
                type='str'
            ),
            identity=dict(
                type='dict'
            ),
            skip_dns_registration=dict(
                type='str'
            ),
            skip_custom_domain_verification=dict(
                type='str'
            ),
            force_dns_registration=dict(
                type='str'
            ),
            site_config=dict(
                type='dict',
                elements='dict',
                options=site_config_spec
            )
            ttl_in_seconds=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None
        self.site_envelope = dict()
        self.skip_dns_registration = None
        self.skip_custom_domain_verification = None
        self.force_dns_registration = None
        self.ttl_in_seconds = None
        self.tags = None
        self.site_config = None

        self.results = dict(changed=False)
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMWebApps, self).__init__(derived_arg_spec=self.module_arg_spec,
                                             supports_check_mode=True,
                                             supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "kind":
                    self.site_envelope["kind"] = kwargs[key]
                elif key == "location":
                    self.site_envelope["location"] = kwargs[key]
                elif key == "enabled":
                    self.site_envelope["enabled"] = kwargs[key]
                elif key == "server_farm_id":
                    self.site_envelope["server_farm_id"] = kwargs[key]
                elif key == "reserved":
                    self.site_envelope["reserved"] = kwargs[key]
                elif key == "scm_site_also_stopped":
                    self.site_envelope["scm_site_also_stopped"] = kwargs[key]
                elif key == "hosting_environment_profile":
                    self.site_envelope["hosting_environment_profile"] = kwargs[key]
                elif key == "client_affinity_enabled":
                    self.site_envelope["client_affinity_enabled"] = kwargs[key]
                elif key == "client_cert_enabled":
                    self.site_envelope["client_cert_enabled"] = kwargs[key]
                elif key == "host_names_disabled":
                    self.site_envelope["host_names_disabled"] = kwargs[key]
                elif key == "container_size":
                    self.site_envelope["container_size"] = kwargs[key]
                elif key == "daily_memory_time_quota":
                    self.site_envelope["daily_memory_time_quota"] = kwargs[key]

                elif key == "https_only":
                    self.site_envelope["https_only"] = kwargs[key]
                elif key == "identity":
                    self.site_envelope["identity"] = kwargs[key]
                elif key == "site_config":
                    self.site_envelope["site_config"] = kwargs[key]                

        old_response = None
        response = None
        to_be_updated = False        

        resource_group = self.get_resource_group(self.resource_group)
        if "location" not in self.site_envelope:
            self.site_envelope["location"] = resource_group.location

        old_response = self.get_webapp()

        # check if the web app already present in the resource group
        if not old_response:
            self.log("Web App instance doesn't exist")            

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
                to_be_updated = True

        else:
            self.log("Web App instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete

            elif self.state == 'present':
                self.log(
                    "Need to check if Web App instance has to be deleted or may be updated")
                self.to_do = Actions.Update

                update_tags, old_response['tags'] = self.update_tags(response['tags'])

                if response['state'] == "Running":
                    if is_property_update(self, old_response):
                        to_be_updated = True


        if to_be_updated:
            self.log("Need to Create / Update the Web App instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_webapp()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")

        elif self.to_do == Actions.Delete:
            self.log("Web App instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_webapp()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_webapp():
                time.sleep(20)

        else:
            self.log("Web App instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]
            self.results["state"] = response["state"]

        return self.results

    # compare existing web app with input, determine weather it's update operation
    def is_property_update(self, existing_webapp):
        # enabled
        if is_property_changed(self, 'enabled', existing_webapp('enabled'):
            return True
        if is_property_changed(self, 'server_farm_id', existing_webapp('server_farm_id'):
            return True
        if is_property_changed(self, 'reserved', existing_webapp('reserved'):
            return True
        if is_property_changed(self, 'scm_site_also_stopped', existing_webapp('scm_site_also_stopped'):
            return True
        if is_property_changed(self, 'client_affinity_enabled', existing_webapp('client_affinity_enabled'):
            return True
        if is_property_changed(self, 'client_cert_enabled', existing_webapp('client_cert_enabled'):
            return True
        if is_property_changed(self, 'host_names_disabled', existing_webapp('host_names_disabled'):
            return True
        if is_property_changed(self, 'https_only', existing_webapp('https_only'):
            return True
        if is_property_changed(self, 'container_size', existing_webapp('container_size'):
            return True
        if is_property_changed(self, 'dailyMemoryTimeQuota', existing_webapp('dailyMemoryTimeQuota'):
            return True
        return False

    # compare existing web app site_config with input, determine weather it's update operation
    def is_site_config_update(self, existing_webapp):
        if len(self.site_config.app_settings) != len(existing_webapp['site_config']['application_setting']):
            return True
        return False

    # return weather property in input exists and changed comparing to specific value
    def is_property_changed(self, property_name, property_value):
        if self.site_envelope[property_name] and self.site_envelope[property_name] != property_value:
            return True
        return False


    def create_update_webapp(self):
        '''
        Creates or updates Web App with the specified configuration.

        :return: deserialized Web App instance state dictionary
        '''
        self.log(
            "Creating / Updating the Web App instance {0}".format(self.name))

        try:
            response=self.web_client.web_apps.create_or_update(resource_group_name=self.resource_group,
                                                                 name=self.name,
                                                                 site_envelope=self.site_envelope)
            if isinstance(response, AzureOperationPoller):
                response=self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Web App instance.')
            self.fail(
                "Error creating the Web App instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_webapp(self):
        '''
        Deletes specified Web App instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Web App instance {0}".format(self.name))
        try:
            response=self.web_client.web_apps.delete(resource_group_name=self.resource_group,
                                                       name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the Web App instance.')
            self.fail(
                "Error deleting the Web App instance: {0}".format(str(e)))

        return True

    def get_webapp(self):
        '''
        Gets the properties of the specified Web App.

        :return: deserialized Web App instance state dictionary
        '''
        self.log(
            "Checking if the Web App instance {0} is present".format(self.name))

        try:
            response=self.web_client.web_apps.get(resource_group_name=self.resource_group,
                                                    name=self.name)

            self.log("Response : {0}".format(response))
            self.log("Web App instance : {0} found".format(response.name))
            return response.as_dict()

        except CloudError as ex:
            self.log("Didn't find web app {0} in resource group {1}".format(
                self.name, self.resource_group))

        return False


def main():
    """Main execution"""
    AzureRMWebApps()


if __name__ == '__main__':
    main()
