#!/usr/bin/python
#
# Copyright (c) 2017 Yunge Zhu, <yungez@microsoft.com>
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
version_added: "2.6"
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
    - "Yunge Zhu(@yungezz)"

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
        site_config, app_service_plan, Site,
        AppServicePlan, SkuDescription, NameValuePair

    )
except ImportError:
    # This is handled in azure_rm_common
    pass


app_service_plan_spec = dict(
    resource_group=dict(type='str'),
    name=dict(type='str', required=True),
    is_linux=dict(type='bool'),
    number_of_workers=dict(type='int'),
    sku=dict(type='str')
)

container_settings_spec = dict(
    name=dict(type='str', required=True),
    registry_server_url=dict(type='str'),
    registry_server_user=dict(type='str'),
    registry_server_password=dict(type='str')
)

java_container_settings_spec = dict(
    name=dict(type='str', required=True),
    version=dict(type='str', required=True)
)

deployment_source_spec = dict(
    url=dict(type='str'),
    branch=dict(type='str')
)


def _normalize_sku(sku):
    if sku is None:
        return sku

    sku = sku.upper()
    if sku == 'FREE':
        return 'F1'
    elif sku == 'SHARED':
        return 'D1'
    return sku


def get_sku_name(tier):
    tier = tier.upper()
    if tier == 'F1' or tier == "FREE":
        return 'FREE'
    elif tier == 'D1' or tier == "SHARED":
        return 'SHARED'
    elif tier in ['B1', 'B2', 'B3', 'BASIC']:
        return 'BASIC'
    elif tier in ['S1', 'S2', 'S3']:
        return 'STANDARD'
    elif tier in ['P1', 'P2', 'P3']:
        return 'PREMIUM'
    elif tier in ['P1V2', 'P2V2', 'P3V2']:
        return 'PREMIUMV2'
    else:
        raise CLIError(
            "Invalid sku(pricing tier), please refer to command help for valid values")


class Actions:
    NoAction, Create, Update, UpdateSiteConfig, Delete = range(5)


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
            location=dict(
                type='str'
            ),
            plan=dict(
                type='dict',
                options=app_service_plan_spec
            ),
            net_framework_version=dict(
                type='str',
            ),
            java_version=dict(
                type='str',
            ),
            php_version=dict(
                type='str'
            ),
            python_version=dict(
                type='str'
            ),
            node_version=dict(
                type='str'
            ),
            java_container_settings=dict(
                type='dict',
                options=java_container_settings_spec
            ),
            container_settings=dict(
                type='dict',
                options=container_settings_spec
            ),
            scm_type=dict(
                type='dict',
            ),
            deployment_source=dict(
                type='dict',
                options=deployment_source_spec
            ),
            git_token=dict(
                type='str'
            ),
            startup_file=dict(
                type='str'
            ),
            linux_fx_version=dict(
                type='str'
            ),
            client_affinity_enabled=dict(
                type='bool',
                default=True
            ),
            force_dns_registration=dict(
                type='bool'
            ),
            https_only=dict(
                type='bool'
            ),
            skip_dns_registration=dict(
                type='bool'
            ),
            skip_custom_domain_verification=dict(
                type='bool'
            ),
            ttl_in_seconds=dict(
                type='int'
            ),
            app_settings=dict(
                type='dict'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None

        # update in create_or_update as parameters
        self.client_affinity_enabled = True
        self.force_dns_registration = None
        self.skip_dns_registration = None
        self.skip_custom_domain_verification = None
        self.ttl_in_seconds = None
        self.https_only = None

        self.tags = None

        # site config, e.g app settings, ssl
        self.site_config = dict()
        self.app_settings = dict()
        self.app_settings_strDic = None

        # app service plan
        self.plan = None
        # siteSourceControl
        self.deployment_source = dict()

        # site, used at level creation, or update. e.g windows/linux, client_affinity etc first level args
        self.site = None

        # property for internal usage, not used for sdk
        self.container_settings = None

        self.results = dict(changed=False)
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMWebApps, self).__init__(derived_arg_spec=self.module_arg_spec,
                                             supports_check_mode=True,
                                             supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        # for key in list(self.module_arg_spec.keys()) + ['tags']:
        #     setattr(self, key, kwargs[key])
        setattr(self, 'tags', kwargs['tags'])

        # set site_config value from kwargs
        site_config_properties = ["net_framework_version",
                                  "java_version",
                                  "php_version",
                                  "python_version",
                                  "linux_fx_version"]

        # updatable_properties
        updatable_properties = ["client_affinity_enabled",
                                "force_dns_registration",
                                "https_only",
                                "skip_custom_domain_verification",
                                "skip_dns_registration",
                                "ttl_in_seconds"]

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key in site_config_properties:

                    self.site_config[key] = kwargs[key]
                if key == "java_container_settings":
                    if 'name' in kwargs['java_container_settings']:
                        self.site_config['java_container'] = kwargs['java_container_settings']['name']
                    if 'version' in kwargs['java_container_settings']:
                        self.site_config['java_container_version'] = kwargs['java_container_settings']['version']

                # if key == "deployment_source":
                #     self.site_source_control['repo_url'] = kwargs['deployment_source']['url']
                #     self.site_source_control['branch'] = kwargs['deployment_source']['branch']

        # start main flow
        old_response = None
        response = None
        to_be_updated = False

        if self.container_settings is not None:

            if hasattr(self.site_config, 'linux_fx_version'):
                self.fail(
                    "Cannot set linux_fx_version with container_settings at same time.")

            linux_fx_version = 'DOCKER|'

            if self.container_settings.get('registry_server_url', None) is not None:
                self.app_settings['DOCKER_REGISTRY_SERVER_URL'] = 'https://' + \
                    self.container_settings['registry_server_url']

                linux_fx_version += self.container_settings['registry_server_url']

            linux_fx_version += self.container_settings['name']

            self.site_config['linux_fx_version'] = linux_fx_version

            if self.container_settings.get('registry_server_user', None) is not None:
                self.app_settings['DOCKER_REGISTRY_SERVER_USERNAME'] = self.container_settings['registry_server_user']

            if self.container_settings.get('registry_server_password', None) is not None:
                self.app_settings['DOCKER_REGISTRY_SERVER_PASSWORD'] = self.container_settings['registry_server_password']

        # set location
        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        # get existing web app
        old_response = self.get_webapp()

        # check if the web app already present in the resource group
        if not old_response:
            self.log("Web App instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
                to_be_updated = True

                # service plan is required for creation
                if not self.plan:
                    self.fail(
                        "Please specify app service plan in plan parameter.")

                # if not specify resource group in plan, then use same one as webapp
                if "resource_group" not in self.plan:
                    self.plan['resource_group'] = self.resource_group

                # get app service plan
                old_plan = self.get_app_service_plan()

                if not old_plan:
                    # no existing service plan, create one
                    if ('name' not in self.plan or
                        'is_linux' not in self.plan or
                            'sku' not in self.plan):
                        self.fail(
                            'Please specify name, is_linux, sku in plan')

                    if 'location' not in self.plan:
                        plan_resource_group = self.get_resource_group(
                            self.plan['resource_group'])
                        self.plan['location'] = plan_resource_group.location

                    old_plan = self.create_app_service_plan()

                plan_id = old_plan['id']

                if hasattr(old_plan, "is_linux"):
                    old_plan['reserved'] = old_plan['is_linux']

                # prepare to create web app

                # if linux, setup linux_fx_version
                # linux_fx_version is mapping to sdk linux_fx_version, which is only for linux web app
                # linux_fx_version for docker web app is like DOCKER|imagename:tag
                # xxx_version is mapping to sdk xxx_version, which is only for windows web app
                if old_plan['reserved']:
                    if hasattr(self, 'startup_file'):
                        self.site_config['app_command_line'] = self.startup_file

                self.site = Site(server_farm_id=plan_id,
                                 location=self.location, site_config=self.site_config)

                if hasattr(self, "client_affinity_enabled"):
                    self.site.client_affinity_enabled = self.client_affinity_enabled

                # set app setting
                if self.app_settings is not None:
                    app_settings = []
                    for key in self.app_settings.keys():
                        app_settings.append(NameValuePair(
                            key, self.app_settings[key]))

                    self.site_config['app_settings'] = app_settings

                # create web app
                response = self.create_update_webapp()

        else:
            # existing web app, do update
            self.log("Web App instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete

            elif self.state == 'present':
                self.log(
                    "Need to check if Web App instance has to be deleted or may be updated")
                self.to_do = Actions.Update

                self.log('Result: {0}'.format(old_response))

                update_tags, old_response['tags'] = self.update_tags(
                    old_response.get('tags', dict()))

                if old_response['state'] == "Running":
                    if update_tags:
                        to_be_updated = True

                    self.site = Site(location=self.location,
                                     site_config=self.site_config)

                    # if root level property changed, call create_or_update
                    if self.is_updatable_property_changed(old_response) or is_site_config_fx_version_changed(old_response):

                        to_be_updated = True
                        response = self.create_update_webapp()

                    # get existing app_settings
                    self.app_settings_strDic = self.list_app_settings()

                    if self.is_app_settings_changed():
                        # if app_settings changed, call create_or_update_appsetting
                        self.app_settings_strDic.properties = dict()
                        for key in self.app_settings.keys():
                            self.app_settings_strDic.properties[key] = self.app_settings[key]

                        to_be_updated = True
                        update_as_response = self.update_app_settings()

                    # if deployment_source changed, call create_or_update_source_control
                    if self.is_deployment_source_changed(old_response):

                        to_be_updated = True
                        update_sc_response = self.create_or_update_source_control()

        if to_be_updated:
            self.log('Need to Create/Update web app')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            if response:
                self.results["id"] = response["id"]
                self.results["state"] = response["state"]

        if self.to_do == Actions.Delete:
            self.log("Web App instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_webapp()

            self.log('web app deleted')

        return self.results

    # compare existing web app with input, determine weather it's update operation
    def is_updatable_property_changed(self, existing_webapp):
        for property in updatable_properties:
            if hasattr(self, property_name) and getattr(self, property_name) != property_value:
                return True

        return False

    # compare xxx_version
    def is_site_config_fx_version_changed(self, existing_webapp):
        for fx_version in site_config_properties:
            if self.site_config.get(fx_version, None) != existing_webapp.get(fx_version, None):
                return True

        return False

    # comparing existing app setting with input, determine whether it's changed
    def is_app_settings_changed(self):
        if self.app_settings is not None:
            if len(self.app_settings_strDic.properties) != len(self.app_settings):
                return True

            elif self.app_settings_strDic.properties is not None and len(self.app_settings_strDic.properties) > 0:
                for key in self.app_settings.keys():
                    if self.app_settings_strDic.properties[key] is None \
                            or self.app_settings[key] != self.app_settings_strDic.properties[key]:
                        return True
        return False

    # comparing deployment source with input, determine wheather it's changed
    def is_deployment_source_changed(self, existing_webapp):
        if self.deployment_source is not None:
            if self.deployment_source.get('url', None) is not None \
                    and self.deployment_source['url'] != existing_webapp.get('site_source_control')['url']:
                return True

            if self.deployment_source.get('branch', None) is not None \
                    and self.deployment_source['branch'] != existing_webapp.get('site_source_control')['branch']:
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
            response = self.web_client.web_apps.create_or_update(resource_group_name=self.resource_group,
                                                                 name=self.name,
                                                                 site_envelope=self.site,
                                                                 skip_dns_registration=self.skip_dns_registration,
                                                                 skip_custom_domain_verification=self.skip_custom_domain_verification,
                                                                 force_dns_registration=self.force_dns_registration,
                                                                 ttl_in_seconds=self.ttl_in_seconds)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

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
            response = self.web_client.web_apps.delete(resource_group_name=self.resource_group,
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

        response = None

        try:
            response = self.web_client.web_apps.get(resource_group_name=self.resource_group,
                                                    name=self.name)

            self.log("Response : {0}".format(response))
            self.log("Web App instance : {0} found".format(response.name))
            return response.as_dict()

        except CloudError as ex:
            self.log("Didn't find web app {0} in resource group {1}".format(
                self.name, self.resource_group))

        return False

    def get_app_service_plan(self):
        '''
        Gets app service plan
        :return: deserialized app service plan dictionary
        '''
        self.log("Get App Service Plan {0}".format(self.plan['name']))

        try:
            response = self.web_client.app_service_plans.get(
                self.plan['resource_group'], self.plan['name'])
            self.log("Response : {0}".format(response))
            self.log("App Service Plan : {0} found".format(response.name))

            return response.as_dict()
        except CloudError as ex:
            self.log("Didn't find app service plan {0} in resource group {1}".format(
                self.plan['name'], self.plan['resource_group']))

        return False

    def create_app_service_plan(self):
        '''
        Creates app service plan
        :return: deserialized app service plan dictionary
        '''
        self.log("Create App Service Plan {0}".format(self.plan['name']))

        try:
            # normalize sku
            sku = _normalize_sku(self.plan['sku'])

            sku_def = SkuDescription(tier=get_sku_name(
                sku), name=sku, capacity=(self.plan['number_of_workers'] or None))
            plan_def = AppServicePlan(
                location=self.plan['location'], app_service_plan_name=self.plan['name'], sku=sku_def, reserved=(self.plan['is_linux'] or None))

            poller = self.web_client.app_service_plans.create_or_update(
                self.plan['resource_group'], self.plan['name'], plan_def)

            if isinstance(poller, AzureOperationPoller):
                response = self.get_poller_result(poller)

            self.log("Response : {0}".format(response))

            return response.as_dict()
        except CloudError as ex:
            self.fail("Failed to create app service plan {0} in resource group {1}: {2}".format(
                self.plan['name'], self.plan['resource_group'], str(ex)))

    def list_app_settings(self):
        '''
        List application settings
        :return: deserialized list response
        '''
        self.log("List application setting")

        try:

            response = self.web_client.web_apps.list_application_settings(
                resource_group_name=self.resource_group, name=self.name)
            self.log("Response : {0}".format(response))

            return response
        except CloudError as ex:
            self.log("Failed to list application settings for web app {0} in resource group {1}".format(
                self.name, self.resource_group))

            return False

    def update_app_settings(self):
        '''
        Update application settings
        :return: deserialized updating response
        '''
        self.log("Update application setting")

        try:
            response = self.web_client.web_apps.update_application_settings(
                resource_group_name=self.resource_group, name=self.name, app_settings=self.app_settings_strDic)
            self.log("Response : {0}".format(response))

            return response.as_dict()
        except CloudError as ex:
            self.log("Failed to update application settings for web app {0} in resource group {1}".format(
                self.name, self.resource_group))

        return False

    def create_or_update_source_control(self):
        '''
        Update site source control
        :return: deserialized updating response
        '''
        self.log("Update site source control")

        if self.deployment_source is None:
            return False

        self.deployment_source['is_manual_integration'] = False
        self.deployment_source['is_mercurial'] = False

        try:
            response = self.web_client.web_client.create_or_update_source_control(
                self.resource_group, self.name, self.deployment_source)
            self.log("Response : {0}".format(response))

            return response.as_dict()
        except CloudError as ex:
            self.fail("Failed to update site source control for web app {0} in resource group {1}".format(
                self.name, self.resource_group))


def main():
    """Main execution"""
    AzureRMWebApps()


if __name__ == '__main__':
    main()
