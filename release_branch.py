import os
import json
from common import execute_command, get_release
from dotenv import load_dotenv

load_dotenv()

BRANCH_PREFIX = os.getenv('BRANCH_PREFIX')

MULTITENANT_PATH = os.getenv('MULTITENANT_REPO')
EXAMITY_UI_PATH = os.getenv('EXAMITY_UI_REPO')
MULTITENANT_APPSETTINGS_PATH = f'{MULTITENANT_PATH}/Application/Examity.STS/Examity.STS/appsettings.json'
EXAMITY_UI_CONSTANTS_PATH = f'{EXAMITY_UI_PATH}/src/app/models/constants.ts'
MULTITENANT_SQL_PATH = f'{MULTITENANT_PATH}/Database/Scripts/Examity_V5_Appointments/Changes/Changes_Appointments_Current.sql'
MULTITENANT_README_PATH = f'{MULTITENANT_PATH}/README.md'

REPOS = [
    os.getenv('MULTITENANT_REPO'),
    os.getenv('EXAMITYPY_REPO'),
    os.getenv('TEST_TAKER_UI_REPO'),
    os.getenv('OPSCONSOLE_UI_REPO'),
    os.getenv('EXAMITY_BILLING_REPO'),
    os.getenv('PROCTORING_UI_REPO'),
    os.getenv('EXAMITY_UI_REPO')
]


def create_branch(release_version: str):
    branch_name = f'{BRANCH_PREFIX}{release_version}'
    print('Updating develop')
    execute_command(f'git checkout develop')
    execute_command(f'git pull')

    print(f'Creating new branch {branch_name}')
    execute_command(f'git checkout -b {branch_name}')


def push_changes(commit: bool = False):
    print(f'Publishing branch')
    if commit:
        execute_command(f'git commit -a -m "Creating Release Branch"')
    execute_command(f'git push -u origin head')


def update_file(file_name: str, file_path: str, json_file: bool = False):
    def wrapper(func):
        print(f'Updating {file_name} ({file_path})')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f) if json_file else f.readlines()
        with open(file_path, 'w', encoding='utf-8') as f:
            func(data, f)
    return wrapper


def multitenant_file_changes(release_version: str):
    @update_file('STS App Settings', MULTITENANT_APPSETTINGS_PATH, json_file=True)
    def sts(data, f):
        data['Version'] = release_version
        json.dump(data, f, indent=2)

    @update_file('Appointments SQL', MULTITENANT_SQL_PATH)
    def sql(data, f):
        index = 0
        for i, line in enumerate(data):
            if line.startswith('DECLARE @V_RELEASE varchar(16) ='):
                index = i
                break
        data[index] = f"DECLARE @V_RELEASE varchar(16) = '{release_version}';\n"
        f.write(''.join(data))

    @update_file('README', MULTITENANT_README_PATH)
    def readme(data, f):
        f.write(f"# MultiTenant\n\nCode for Examity Multi-Tenant (version 5 and up)-Release branch {release_version}\n")


def examity_ui_file_changes(release_version: str):
    @update_file('UI Constants', EXAMITY_UI_CONSTANTS_PATH)
    def constants(data, f):
        data[0] = f"export const VERSION = '{release_version}';\n"
        f.write(''.join(data))


def main(release_version: str):
    for repo in REPOS:
        print(f'Start creating Release branch for {repo}')
        os.chdir(repo)

        create_branch(release_version)
        if repo is MULTITENANT_PATH:
            multitenant_file_changes(release_version)
        if repo is EXAMITY_UI_PATH:
            examity_ui_file_changes(release_version)
        push_changes(commit=(repo in [MULTITENANT_PATH, EXAMITY_UI_PATH]))
        print(f'Finished creating Release branch for {repo}')


if __name__ == '__main__':
    release = get_release()
    main(release)
