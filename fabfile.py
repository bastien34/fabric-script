#!/usr/bin/python3
# -*- coding: utf-8> -*-

"""

To run fabric using ``develop`` environment:

    > fab develop <task>

Installation:

    > pip install fabric
    > pip install fabric2

"""

import sys
from fabric import (task)
from fabric2 import Connection
from datetime import datetime


REPO_URL = "your_reepo"
PROJECT_NAME = 'dev_project'
ROOT_DIR = f'/opt/{dev_project}'
APP_DIR = f'{ROOT_DIR}/project'
GUNICORN_SERVICE = f'gunicorn_{PROJECT_NAME}'
VENV = f'/opt/.virtualenvs/{PROJECT_NAME}'
SSH_KEY = '%h/.ssh/id_rsa'
db_name = 'db_name'
db_user = 'db_user'


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
def pipreq(ctx):
    with get_connection(ctx) as c:
        with c.prefix(f'source {VENV}/bin/activate'):
            with c.cd(APP_DIR):
                c.run("pip install -r requirements/base.txt")


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


@task
def deploy(ctx):
    """
    Main task.
    """
    checkout(ctx)
    pull(ctx)
    pipreq(ctx)
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

 
@task
def djangodump(ctx):
    dump_name = 'rdt_front_{:%Y-%m-%d}'.format(datetime.now())
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"{VENV}/bin/python manage.py dumpdata > /tmp/{dump_name}.json")
            c.get(f'/tmp/{dump_name}.json', f'dumped_data/{dump_name}.json')
       
        
