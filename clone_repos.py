import os
from common import execute_command
from dotenv import load_dotenv

load_dotenv()

DIR_PATH = os.getenv('REPO_DIR')

REPOS = [
    os.getenv('MULTITENANT_URL'),
    os.getenv('EXAMITYPY_URL'),
    os.getenv('TEST_TAKER_UI_URL'),
    os.getenv('OPSCONSOLE_UI_URL'),
    os.getenv('EXAMITY_BILLING_URL'),
    os.getenv('PROCTORING_UI_URL'),
    os.getenv('EXAMITYEXTENSION_URL')
]


def main():
    dirs = []  # { dir: '', env_name: ''}

    print(f'Changing current working directory to {DIR_PATH}')
    os.chdir(DIR_PATH)
    for repo in REPOS:
        print(f'Cloning {repo}')
        execute_command(f'git clone {repo}')

        repo_name = repo.split('/')[-1]
        i = {'dir': repo_name}

        env_name = repo_name.upper() + '_REPO'
        for replacement in ['.', '-']:
            env_name = env_name.replace(replacement, '_')

        i['env_name'] = env_name

        dirs.append(i)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print('Updating .env file')
    with open('.env', 'w') as f:
        for dir in dirs:
            path = f"{DIR_PATH}/{dir['dir']}"
            f.write(f"{dir['env_name']} = {path}\n")

        branch_prefix = input('What is the prefix for release branches?\n')
        release_prefix = input('What is the prefix for release tags?\n')
        f.write(f"BRANCH_PREFIX = {branch_prefix}\n")
        f.write(f"RELEASE_PREFIX = {release_prefix}\n")


if __name__ == '__main__':
    main()
