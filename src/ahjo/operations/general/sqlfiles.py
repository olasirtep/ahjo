# Ahjo - Database deployment framework
#
# Copyright 2019, 2020, 2021 ALM Partners Oy
# SPDX-License-Identifier: Apache-2.0

"""Module for SQL script file deploy and drop."""
from collections import defaultdict
from logging import getLogger
from os import listdir, path
from pathlib import Path

from ahjo.database_utilities import execute_from_file, execute_try_catch
from ahjo.operation_manager import OperationManager

logger = getLogger('ahjo')


def deploy_sqlfiles(engine, directory, message, display_output=False, variables=None):
    """Run every SQL script file found in given directory and print the executed file names.
    If any file in directory cannot be deployed after multiple tries, raise an exeption and
    list failed files to user.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        SQL Alchemy engine.
    directory : str
        Path of directory holding the SQL script files.
    message : str
        Message passed to OperationManager.
    display_output : bool
        Indicator to print script output.
    variables : str
        Variables passed to SQL script.

    Raises
    ------
    RuntimeError
        If any of the files in given directory fail to deploy after multiple tries.
    """
    with OperationManager(message):
        if not Path(directory).is_dir():
            logger.warning("Directory not found: " + directory)
            return False
        files = [path.join(directory, f)
                 for f in listdir(directory) if f.endswith('.sql')]
        failed = sql_file_loop(deploy_sql_from_file, engine,
                               display_output, variables, file_list=files, max_loop=len(files))
        if len(failed) > 0:
            error_msg = "Failed to deploy the following files:\n{}".format(
                '\n'.join(failed.keys()))
            for fail_messages in failed.values():
                error_msg = error_msg + ''.join(fail_messages)
            raise RuntimeError(error_msg)
        return True


def drop_sqlfile_objects(engine, object_type, directory, message):
    """Drop all the objects created in SQL script files of an directory.
    The naming of the files should be consistent!

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        SQL Alchemy engine.
    object_type : str
        Type of database object.
    directory : str
        Path of directory holding the SQL script files.
    message : str
        Message passed to OperationManager.

    Raises
    ------
    RuntimeError
        If any of the files in given directory fail to drop after multiple tries.
    """
    with OperationManager(message):
        if not Path(directory).is_dir():
            logger.warning("Directory not found: " + directory)
            return
        files = [path.join(directory, f)
                 for f in listdir(directory) if f.endswith('.sql')]
        failed = sql_file_loop(drop_sql_from_file, engine,
                               object_type, file_list=files, max_loop=len(files))
        if len(failed) > 0:
            error_msg = "Failed to drop the following files:\n{}".format(
                '\n'.join(failed.keys()))
            for fail_messages in failed.values():
                error_msg = error_msg + ''.join(fail_messages)
            raise RuntimeError(error_msg)


def deploy_sql_from_file(file, engine, display_output, variable):
    '''Run single SQL script file.

    Parameters
    ----------
    file : str
        SQL script file path passed to SQLCMD.
    conn_info : dict
        Dictionary holding information needed to establish database connection.
    display_output : bool
        Indicator to print script output.
    '''
    output = execute_from_file(engine, file_path=file, variables=variable)
    logger.info(path.basename(file))
    if display_output:
        logger.info(output)


def drop_sql_from_file(file, engine, object_type):
    '''Run DROP OBJECT command for object in SQL script file.

    The drop command is based on object type and file name.

    Parameters
    ----------
    file : str
        SQL script file path.
    engine : sqlalchemy.engine.Engine
        SQL Alchemy engine.
    object_type : str
        Type of database object.
    '''
    parts = path.basename(file).split('.')
    # SQL files are assumed to be named in format: schema.object.sql
    # The only exception is assemblies. Assemblies don't have schema.
    if object_type == 'ASSEMBLY':
        object_name = parts[0]
    else:
        if len(parts) != 3:
            raise RuntimeError(
                f'File {file} not in <schema.object.sql> format.')
        object_name = parts[0] + '.' + parts[1]
    query = f"DROP {object_type} {object_name}"
    execute_try_catch(engine, query=query)


def sql_file_loop(command, *args, file_list, max_loop=10):
    '''Loop copy of file_list maximum max_loop times and execute the command to every file in
    copy of file_list. If command succeeds, drop the the file from copy of file_list. If command
    fails, keep the file in copy of file_list and execute the command again in next loop.

    When max_loop is reached and there are files in copy of file_list, return the remaining
    file names and related errors that surfaced during executions. Else return empty dict.

    Parameters
    ----------
    command : function
        Command to be executed to every file in file_list.
    *args
        Arguments passed to command.
    file_list : list
        List of file paths.
    max_loop : int
        Maximum number of loops.

    Returns
    -------
    dict
        Failed files and related errors. Empty if no fails.
    '''
    copy_list = file_list.copy()
    copy_list_loop = copy_list.copy()
    errors = defaultdict(set)
    for _ in range(max_loop):
        for file in copy_list_loop:
            try:
                command(file, *args)
                copy_list.remove(file)
            except Exception as error:
                error_str = '\n------\n' + str(error)
                errors[file].add(error_str)
        copy_list_loop = copy_list.copy()
    if len(copy_list) > 0:
        return {f: list(errors[f]) for f in copy_list}
    return {}
