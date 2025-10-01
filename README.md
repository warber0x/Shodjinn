Shodan API key generator
========================

<img width="457" height="236" alt="image" src="https://github.com/user-attachments/assets/4c6f4101-2619-40a2-be1e-20f4a4c6f807" />

Description:
------------
In the bug bounty world, multiple tools—especially for subdomain enumeration—heavily rely on the Shodan API. This Python script provides a ready-to-use API key for your reconnaissance scripts. Since the free Shodan API has a limited number of requests, this script automates the generation of a new API key, helping you bypass that restriction.

It supports two modes:
- Normal mode: Displays detailed logs
- Pipe mode: Only prints the API key for use with other programs or scripts.

Workflow:
---------
- Automatic temporary email generation.
- Shodan registration and activation link retrieval.
- Login with session persistence.
- API key extraction from the account page.
- Pipe mode for automation and integration with other scripts.

Dependencies:
-------------
Python packages required:
- requests
- beautifulsoup4

Usage:
------
Normal mode (interactive):
    python shodjinn.py

Pipe mode (for automation, only outputs API key):
    python shodjinn.py | ./other_program

Notes:
------
- Ensure Python 3.x is installed.
- Install dependencies before running:
    pip install -r requirements.txt
