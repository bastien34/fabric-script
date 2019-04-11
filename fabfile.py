#!/usr/bin/python3
# -*- coding: utf-8> -*-

"""
Fabric is used as following:

    > fab develop deploy

Installation de fabric:
  $ pip install fabric
  $ pip install fabric2

"""

import sys
from fabric import (task, )
from fabric2 import Connection


REPO_URL = "git@bitbucket.org:bastien_roques/rdt_2.0.git"
PROJECT_NAME = 'dev_rdt2'
ROOT_DIR = '/opt/dev_rdt2'
APP_DIR = f'{ROOT_DIR}/project'
GUNICORN_SERVICE = f'gunicorn_{PROJECT_NAME}'
VENV = f'/opt/.virtualenvs/{PROJECT_NAME}'
SSH_KEY = '/home/bastien/.ssh/id_rsa'


def get_connection(ctx):
    try:
        with Connection(ctx.host, ctx.user,
                        connect_kwargs=ctx.connect_kwargs) as conn:
            return conn
    except Exception as e:
        return None


@task
def develop(ctx):
    ctx.user = "bastien"
    ctx.host = "rdtone"
    ctx.connect_kwargs.key_filename = SSH_KEY


# check if file exists in directory(list)
def exists(file, dir):
    return file in dir


# git tasks
@task
def pull(ctx, branch="develop"):
    # check if ctx is Connection object or Context object
    # if Connection object then calling method from program
    # else calling directly from terminal
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)

    with conn.cd(APP_DIR):
        conn.run("git pull origin {}".format(branch))


@task
def checkout(ctx, branch=None):
    if branch is None:
        sys.exit("branch name is not specified")
    print("branch-name: {}".format(branch))
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    with conn.cd(APP_DIR):
        conn.run("git checkout {branch}".format(branch=branch))


@task
def clone(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)

    ls_result = conn.run("ls").stdout
    ls_result = ls_result.split("\n")
    if exists(PROJECT_NAME, ls_result):
        print("project already exists")
        return
    conn.run("git clone {} {}".format(REPO_URL, PROJECT_NAME))


@task
def migrate(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    with conn.cd(APP_DIR):
        conn.run(f"{VENV}/bin/python manage.py migrate")


@task
def compilemessages(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    with conn.cd(APP_DIR):
        conn.run(f"{VENV}/bin/python manage.py compilemessages")


@task
def collectstatic(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    with conn.cd(APP_DIR):
        conn.run(f"{VENV}/bin/python manage.py collectstatic --noinput")


# supervisor tasks
@task
def start(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    conn.sudo("supervisorctl start all")


@task
def restart(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    print("restarting supervisor...")
    conn.run(f"sudo supervisorctl restart {GUNICORN_SERVICE}")


@task
def stop(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    conn.sudo(f"supervisorctl stop {GUNICORN_SERVICE}")


@task
def status(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    conn.sudo("supervisorctl status")


# deploy task
@task
def deploy(ctx):
    conn = get_connection(ctx)
    if conn is None:
        sys.exit("Failed to get connection")
    clone(conn)
    with conn.cd(APP_DIR):
        print("checkout to dev branch...")
        checkout(conn, branch="develop")
        print("pulling latest code from dev branch...")
        pull(conn)
        print("migrating database....")
        migrate(conn)
        print("compile messages...")
        compilemessages(conn)
        print("collect static...")
        collectstatic(conn)
        print("restarting the supervisor...")
        restart(conn)


@task
def debug(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = get_connection(ctx)
    conn.sudo("supervisorctl start all")

# @task
# def dump_database():
#     run("pg_dump {db_name} -U {db_user} --no-owner --no-privileges"
#         " > /tmp/output-{db_name}.sql".format(db_name=env.db_name,
#                                               db_user=env.db_user))
