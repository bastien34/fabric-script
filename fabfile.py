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
from fabric import (task)
from fabric2 import Connection

REPO_URL = "git@bitbucket.org:bastien_roques/rdt_2.0.git"
PROJECT_NAME = 'dev_rdt2'
ROOT_DIR = '/opt/dev_rdt2'
APP_DIR = f'{ROOT_DIR}/project'
GUNICORN_SERVICE = f'gunicorn_{PROJECT_NAME}'
VENV = f'/opt/.virtualenvs/{PROJECT_NAME}'
SSH_KEY = '/home/bastien/.ssh/id_rsa'
db_name = 'rd_transcription'
db_user = 'rdt_user'


def get_connection(ctx):
    if isinstance(ctx, Connection):
        conn = ctx
    else:
        conn = Connection(ctx.host, ctx.user,
                          connect_kwargs=ctx.connect_kwargs)
    if conn is None:
        sys.exit("Failed to get connection")
    return conn


@task
def develop(ctx):
    """Devfine a context. ctx.user is defaulted on current user."""
    ctx.host = "rdtone"
    ctx.branch = 'develop'
    ctx.connect_kwargs.key_filename = SSH_KEY


@task
def pull(ctx, branch="develop"):
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run("git pull origin {}".format(branch))


@task
def checkout(ctx):
    if ctx.branch is None:
        sys.exit("branch name is not specified")
    print(f"Checkout branch-name: {ctx.branch}")
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"git checkout {ctx.branch}")


@task
def migrate(ctx):
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"{VENV}/bin/python manage.py migrate")


@task
def compilemessages(ctx):
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"{VENV}/bin/python manage.py compilemessages")


@task
def collectstatic(ctx):
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"{VENV}/bin/python manage.py collectstatic --noinput")


@task
def start(ctx):
    with get_connection(ctx) as c:
        c.sudo("supervisorctl start all")


@task
def restart(ctx):
    with get_connection(ctx) as c:
        print("restarting supervisor...")
        c.run(f"sudo supervisorctl restart {GUNICORN_SERVICE}")


@task
def stop(ctx):
    with get_connection(ctx) as c:
        c.sudo(f"supervisorctl stop {GUNICORN_SERVICE}")


@task
def status(ctx):
    with get_connection(ctx) as c:
        c.sudo("supervisorctl status")


# deploy task
@task
def deploy(ctx):
    checkout(ctx)
    pull(ctx)
    migrate(ctx)
    compilemessages(ctx)
    collectstatic(ctx)
    restart(ctx)


@task
def debug(ctx):
    with get_connection(ctx) as c:
        print(ctx.branch)
        c.sudo("supervisorctl status")


@task
def dump(ctx):
    with get_connection(ctx) as c:
        c.run(f"pg_dump {db_name} -U {db_user} --no-owner --no-privileges"
              f" > /tmp/output-{db_name}.sql")
