import os
import argparse


def execute_command(command: str):
    result = os.system(command)
    if result != 0:
        print(f'Command "{command}" failed.')
        print('An error occurred, please make sure Git Bash and GH CLI are installed and set up (use `gh auth login`)')
    return result


def get_release():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--release', required=True)
    args = parser.parse_args()
    return args.release
