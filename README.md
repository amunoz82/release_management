# Release Automation
## Requirements
- Git Bash
- GitHub CLI
- Latest version of Python

## Setup
### Windows
```
python -m venv venv
venv/Scripts/activate
pip install -r requirements
```

### Mac / Linux
```
python -m venv venv
venv/bin/activate
pip install -r requirements
```

## .env
Please create a copy of '.env.template' and rename to '.env'. Follow further instruction inside file

## How to run

### Clone repositories onto machine (only if not already cloned)
```
python clone_repos.py
```

### Create Release branch for all repositories
```
python release_branch.py -r <RELEASE NUMBER>
```

### Create Release tag, release, and PR into master/develop for all repositores
```
python tag_merge_release.py -r <RELEASE NUMBER>
```

### Jira commands (follow prompts)
```
python jira_versions.py <COMMAND>
```

| Command          | Description                                                               |
|------------------|---------------------------------------------------------------------------|
| create-versions  | Create the 'Releases' versions in each projects                           |
| create-rm-ticket | Create the Release ticket on the RM board                                 |
| release-version  | Change the status of a specified version from 'Unreleased' to 'Released'  |
