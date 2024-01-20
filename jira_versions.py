import json
from enum import Enum

import click
import requests

from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth

BASE_URL = "https://examity.atlassian.net"
API_URL = "/rest/api/3"
POST_VERSION = f"{BASE_URL}{API_URL}/version"
POST_ISSUE = f"{BASE_URL}{API_URL}/issue"
GET_PROJECT = f"{BASE_URL}{API_URL}/project"
DATE_FORMAT = "%Y-%m-%d"
STATUS_SUCCESS = [200, 201]

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Dictionary with JIRA's project IDs where the version will be created
# PROJECT_IDS = {"Dummy": 10013}
PROJECT_IDS = {
               }
# JIRA's custom issue type 'Release' ID
RELEASE_ISSUE_ID = 10194

cli = click.Group()


class VersionParts(Enum):
    YEAR = 0
    MONTH = 1
    SEQUENCE = 2


def get_date(iteration: int, date: str):
    if iteration == 0:
        return date
    return (datetime.strptime(date, DATE_FORMAT) + timedelta(weeks=2)).strftime(DATE_FORMAT)


def get_version(iteration: int, version: str, release_date: str):
    if iteration == 0:
        return version
    version_month = int(version.split('.')[VersionParts.MONTH.value])
    release_month = datetime.strptime(release_date, DATE_FORMAT).month
    if release_month == version_month:
        version_sequence = int(version.split('.')[VersionParts.SEQUENCE.value]) + 1
        return f"{version[0:version.rfind('.')]}.{version_sequence}"
    return f"{version[0:version.find('.')]}.{release_month}.0"


def get_version_id(username: str, api_token: str, project_id: int, version: str):
    get_url = f"{GET_PROJECT}/{project_id}"
    response = send_request(username, api_token, "GET", get_url)

    if response and response.status_code in STATUS_SUCCESS:
        for i in response.json()['versions']:
            if i['name'] == version:
                return i['id']

    return None


def send_request(username: str, api_token: str, req_method: str, url: str, data=None):
    auth = HTTPBasicAuth(username, api_token)
    response = requests.request(
        req_method,
        url,
        data=data,
        headers=HEADERS,
        auth=auth
    )
    return response


@cli.command()
@click.option('--start_date', prompt='Sprint start date (format - yyyy-mm-dd)',
              help='When does the sprint starts? (yyyy-mm-dd)')
@click.option('--release_date', prompt='release date (format - yyyy-mm-dd)',
              help='Planned date for the release (yyyy-mm-dd)')
@click.option('--version', prompt='version (ex 22.1.0)', help='initial version to be created (yy.m.sequence)')
@click.option('--username', prompt='username', help='Your JIRA username / email')
@click.option('--api_token', prompt='api token', help='Your JIRA api token')
@click.option('--count', default=6, help='number of versions to create')
def create_versions(start_date, release_date, version, username, api_token, count):
    """ This function will create the 'Releases' versions in each of the projects defined in PROJECT_IDS
    :param start_date: Sprint start date (format - yyyy-mm-dd)
    :param release_date: release date (format - yyyy-mm-dd)
    :param version: initial version to be created (format - yy.m.sequence, ex - 22.1.0)
    :param username: Jira user name / email
    :param api_token: Jira api token. Can be obtained from https://id.atlassian.com/manage-profile/security/api-tokens
    :param count: number of versions to create. Default is 6.
    """
    url = POST_VERSION
    for x in range(count):
        start_date = get_date(x, start_date)
        release_date = get_date(x, release_date)
        version = get_version(x, version, release_date)
        for project, value in PROJECT_IDS.items():
            payload = json.dumps({
                "archived": False,
                "releaseDate": release_date,
                "startDate": start_date,
                "name": version,
                "projectId": value,
                "released": False
            })
            response = send_request(username, api_token, "POST", url, data=payload)

            if response.status_code in STATUS_SUCCESS:
                print(f"Version {version} created successfully in project {project}.")
            else:
                print(f"Couldn't create version {version} in project {project}."
                      f"\nStatus Code {response.status_code}-{response.text}")

            if value == PROJECT_IDS['RM']:
                create_ticket(release_date=release_date,
                              version=version,
                              username=username,
                              api_token=api_token)


def create_ticket(release_date, version, username, api_token):
    """ This function will create the Release ticket on the RM board (ID specified in RM_PROJECT_ID)
    :param release_date: release date (format - yyyy-mm-dd)
    :param version: initial version to be created (format - yy.m.sequence, ex - 22.1.0)
    :param username: Jira user name / email
    :param api_token: Jira api token. Can be obtained from https://id.atlassian.com/manage-profile/security/api-tokens
    """
    url = POST_ISSUE
    release_date = get_date(0, release_date)
    version = get_version(0, version, release_date)
    version_id = get_version_id(username, api_token, PROJECT_IDS['RM'], version)
    payload = json.dumps({
        "fields": {
            "project": {
                "id": PROJECT_IDS['RM']
            },
            "issuetype": {
                "id": RELEASE_ISSUE_ID
            },
            "summary": f"Release {version}",

            "fixVersions": [
                {
                    "id": version_id
                }
            ],

            # "Requires downtime"
            "customfield_10237": {
                "value": "No",
                "id": "11048"
            },

            # "Release Date"
            "customfield_10162": release_date,

            # "Product Components"
            "customfield_10160": [
                {
                    "value": "Other",
                    "id": "10954"
                }
            ],

            # "Release Approver"
            "customfield_10166": [
                {
                    "accountId": "",
                    "emailAddress": "",
                    "active": True
                }
            ],

            # "QA Approver"
            "customfield_10164": [
                {
                    "accountId": "",
                    "emailAddress": "",
                    "active": True,
                }
            ],

            # "Release Type"
            "customfield_10161":
                {
                    "value": "Regular Release",
                    "id": "10942"
                },

            # "Teams Releasing"
            "customfield_10173": [
                {
                    "value": "",
                    "id": ""
                },
            ],
            #  "Platform"
            "customfield_10308":
                {
                    "value": "",
                    "id": ""
                }
        }})

    response = send_request(username, api_token, "POST", url, data=payload)
    if response.status_code in STATUS_SUCCESS:
        print(f"RM ticket for version {version} created successfully.")
    else:
        print(f"Couldn't create RM ticket for version {version}."
              f"\nStatus Code {response.status_code}-{response.text}")


@cli.command()
@click.option('--release_date', prompt='release date (format - yyyy-mm-dd)',
              help='Planned date for the release (yyyy-mm-dd)')
@click.option('--version', prompt='version (ex 22.1.0)', help='initial version to be created (yy.m.sequence)')
@click.option('--username', prompt='username', help='Your JIRA username / email')
@click.option('--api_token', prompt='api token', help='Your JIRA api token')
def create_rm_ticket(release_date, version, username, api_token):
    """ This function will create the Release ticket on the RM board (ID specified in RM_PROJECT_ID)
    :param release_date: release date (format - yyyy-mm-dd)
    :param version: initial version to be created (format - yy.m.sequence, ex - 22.1.0)
    :param username: Jira user name / email
    :param api_token: Jira api token. Can be obtained from https://id.atlassian.com/manage-profile/security/api-tokens
    """
    return create_ticket(release_date=release_date,
                         version=version,
                         username=username,
                         api_token=api_token)


@cli.command()
@click.option('--release_date', prompt='release date (format - yyyy-mm-dd)',
              help='Planned date for the release (yyyy-mm-dd)')
@click.option('--version', prompt='version (ex 22.1.0)', help='initial version to be created (yy.m.sequence)')
@click.option('--username', prompt='username', help='Your JIRA username / email')
@click.option('--api_token', prompt='api token', help='Your JIRA api token')
def release_version(release_date, version, username, api_token):
    """ This function will change the status of a specified version from Unreleased to Released
    :param release_date: release date (format - yyyy-mm-dd)
    :param version: version to be released.
    :param username: Jira username / email
    :param api_token: Jira api token. Can be obtained from https://id.atlassian.com/manage-profile/security/api-tokens
    """
    for project_name, project_id in PROJECT_IDS.items():
        version_id = get_version_id(username, api_token, project_id, version)
        if version_id:
            put_url = f"{POST_VERSION}/{version_id}"
            payload = json.dumps({
                "releaseDate": release_date,
                "released": True
            })
            response = send_request(username, api_token, "PUT", put_url, data=payload)
            if response.status_code in STATUS_SUCCESS:
                print(f"version {version} successfully released in project {project_name}")
            else:
                print(f"Something failed.\n{response.text}")
        else:
            print(f"version {version} was not found on project {project_name}")


@cli.command()
@click.option('--username', prompt='username', help='Your JIRA username / email')
@click.option('--api_token', prompt='api token', help='Your JIRA api token')
def get_unreleased_versions(username: str, api_token: str):
    """ This function will return all the versions that are not released per project
    :param username: Jira username / email
    :param api_token: Jira api token. Can be obtained from https://id.atlassian.com/manage-profile/security/api-tokens
    """
    for project_name, project_id in PROJECT_IDS.items():
        get_url = f"{GET_PROJECT}/{project_id}"
        response = send_request(username, api_token, "GET", get_url)
        unreleased_versions = []
        for versions in response.json()['versions']:
            if not versions['released']:
                unreleased_versions.append(versions)
        print(f"Unreleased versions for {project_name}")
        for versions in unreleased_versions:
            print(versions['name'])


if __name__ == '__main__':
    cli()
