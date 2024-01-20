import os
from dotenv import load_dotenv
from common import execute_command, get_release

load_dotenv()

RELEASE_PREFIX = os.getenv('RELEASE_PREFIX')
BRANCH_PREFIX = os.getenv('BRANCH_PREFIX')

DONT_MERGE = [os.getenv('EXAMITYEXTENSION_REPO')]
MASTER_TO_DEVELOP = [os.getenv('EXAMITY_UI_REPO'), os.getenv('MULTITENANT_REPO')]
REPOS = [
    os.getenv('MULTITENANT_REPO'),
    os.getenv('EXAMITYPY_REPO'),
    os.getenv('TEST_TAKER_UI_REPO'),
    os.getenv('OPSCONSOLE_UI_REPO'),
    os.getenv('EXAMITY_BILLING_REPO'),
    os.getenv('PROCTORING_UI_REPO'),
    os.getenv('EXAMITY_UI_REPO')
]


def create_tag(release_version: str):
    branch_name = f'{BRANCH_PREFIX}{release_version}'
    print('Updating Release Branch')
    execute_command(f'git fetch')
    result = execute_command(f'git checkout {branch_name}')
    if result == 0:
        execute_command(f'git pull')
        print('Tagging release branch')
        tag = f'{RELEASE_PREFIX}{release_version}'
        message = f'Tagging {tag}'
        execute_command(f'git tag -a {tag} -m "{message}"')
        execute_command('git push --tags')

        print('Creating Release')
        execute_command(f'gh release create {tag}')
    else:
        print("Couldn't create the release")


def create_pr(master_to_develop: bool = False):
    print('Creating PR into master')
    execute_command('gh pr create -B master -t "Merge release to master" -b ""')

    if master_to_develop:
        print('Creating PR into develop from master')
        execute_command('gh pr create -B develop -H master -t "master to develop after release" -b ""')


def main(release_version: str):
    for repo in REPOS:
        os.chdir(repo)
        print(f'Start creating tag and PRs for {repo}')
        create_tag(release_version)

        if repo not in DONT_MERGE:
            create_pr(master_to_develop=(repo in MASTER_TO_DEVELOP))

        print(f'Finished creating tag and PRs for {repo}')


if __name__ == '__main__':
    release = get_release()
    main(release)
