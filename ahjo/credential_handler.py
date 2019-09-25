# Ahjo - Database deployment framework
#
# Copyright 2019 ALM Partners Oy
# SPDX-License-Identifier: Apache-2.0

"""Password information handling."""
from base64 import b64decode, b64encode
from getpass import getpass
from logging import getLogger
from pathlib import Path

console_logger = getLogger('ahjo.console')


def obfuscate_credentials(credentials):
    """Not secure encryption of credentials.
    At least it is not in plain text.
    """
    username, password = credentials
    obfuscated_password = b64encode(password.encode()).decode()
    return username, obfuscated_password


def deobfuscate_credentials(credentials):
    """Reverse of obfuscate_credentials.
    """
    username, obfuscated_password = credentials
    password = b64decode(obfuscated_password.encode()).decode()
    return username, password


def lookup_from_file(key, filename):
    """Return value from file.
    In cases where key exists but value doesn't (case: trusted connection), returns empty string.
    """
    if not Path(filename).is_file():
        return None
    with open(filename, "r") as f:
        for line in f:
            try:
                linekey, val = line.split('=', 1)
                if linekey == key:
                    return val
            except:
                return ""
    return None


def store_to_file(key, val, filename):
    """Write key and value pairs to file.
    If file directory does not exists, create directory before writing.
    """
    if not Path(filename).parent.exists():
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "a+") as f:
        f.writelines(str(key)+'='+str(val))


def get_credentials(usrn_file_path=None, pw_file_path=None, cred_key='cred', usrn_prompt="Username: ", pw_prompt="Password: "):
    """Retrieves credentials or asks for them.
    The credentials are stored in a global variable.

    Arguments
    ---------
    usrn_file_path:str
        The username file path or None for no storing
    pw_file_path:str
        The password file path or None for no storing
    cred_file_path: str
        The path to the credentials file.
        If None, the credentials are not stored.
    usrn_prompt: str
        How the username is asked
    pw_prompt: str
        How the password is asked

    Returns
    -------
    Tuple(str, str)
        The username and the password in a tuple.
    """
    global cred_dict

    if 'cred_dict' not in globals():
        cred_dict = {}

    if cred_key not in cred_dict:
        if usrn_file_path is not None and pw_file_path is not None:
            username = lookup_from_file(cred_key, usrn_file_path)
            password = lookup_from_file(cred_key, pw_file_path)
            if username is not None and password is not None:
                pass
            else:
                console_logger.info("Credentials are not yet defined.")
                console_logger.info(f"The credentials will be stored in files {usrn_file_path} and {pw_file_path}")
                username = input(usrn_prompt)
                new_password = getpass(pw_prompt)
                username, password = obfuscate_credentials((username, new_password))
                store_to_file(cred_key, username, usrn_file_path)
                store_to_file(cred_key, password, pw_file_path)
        else:
            username = input(usrn_prompt)
            new_password = getpass(pw_prompt)
            username, password = obfuscate_credentials((username, new_password))
        cred_dict[cred_key] = (username, password)
    return deobfuscate_credentials(cred_dict[cred_key])
