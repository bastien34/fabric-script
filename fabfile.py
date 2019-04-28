#!/usr/bin/python3
# -*- coding: utf-8> -*-

"""

List of tasks:

    > fab -l

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
BACKUP_DIR = 'front_data_backup'


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
    """Define a context to run tasks. Default user is current user."""
    ctx.host = "rdtone"
    ctx.branch = 'develop'
    ctx.connect_kwargs.key_filename = SSH_KEY


def pull(ctx, branch="develop"):
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run("git pull origin {}".format(branch))


def checkout(ctx):
    if ctx.branch is None:
        sys.exit("branch name is not specified")
    print(f"Checkout branch-name: {ctx.branch}")
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"git checkout {ctx.branch}")


def migrate(ctx):
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"{VENV}/bin/python manage.py migrate")


def pipreq(ctx):
    with get_connection(ctx) as c:
        with c.prefix(f'source {VENV}/bin/activate'):
            with c.cd(APP_DIR):
                c.run("pip install -r requirements/base.txt")


def compilemessages(ctx):
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"{VENV}/bin/python manage.py compilemessages")


def collectstatic(ctx):
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"{VENV}/bin/python manage.py collectstatic --noinput")


def start(ctx):
    with get_connection(ctx) as c:
        c.sudo("supervisorctl start all")


def restart(ctx):
    """Restart supervisor project service."""
    with get_connection(ctx) as c:
        print("restarting supervisor...")
        c.run(f"sudo supervisorctl restart {GUNICORN_SERVICE}")


@task
def stop(ctx):
    """Stop supervisor service for the project only."""
    with get_connection(ctx) as c:
        c.sudo(f"supervisorctl stop {GUNICORN_SERVICE}")


@task
def status(ctx):
    """Supervisor status."""
    with get_connection(ctx) as c:
        c.sudo("supervisorctl status")


@task
def deploy(ctx):
    """
    Runs checkout, pull, pip requirements, migrate, compilemessages,
    collectstatic and restarts supervisor service.
    """
    checkout(ctx)
    pull(ctx)
    pipreq(ctx)
    migrate(ctx)
    compilemessages(ctx)
    collectstatic(ctx)
    restart(ctx)


def debug(ctx):
    with get_connection(ctx) as c:
        c.sudo("supervisorctl status")


@task
def pgdump(ctx):
    """Dump database using <pg_dump> and returns a sql files."""
    dump_name = '_all_{:%Y-%m-%d}'.format(datetime.now())
    with get_connection(ctx) as c:
        c.run(f"pg_dump {db_name} -U {db_user} --no-owner --no-privileges"
              f" > /tmp/{db_name}{dump_name}.sql")
        c.get(f'/tmp/{db_name}{dump_name}.sql', f'{db_name}{dump_name}.sql')


@task
def dumpall(ctx):
    """Dump all project using 'manage.py dumpdata'. Returns a json file."""
    dump_name = 'rdt_all_{:%Y-%m-%d}'.format(datetime.now())
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"{VENV}/bin/python manage.py dumpdata > /tmp/{dump_name}.json")
            c.get(f'/tmp/{dump_name}.json', f'{dump_name}.json')


def _dump(c, app, dump_name):
    output = os.path.join(BACKUP_DIR, dump_name)
    with c.cd(APP_DIR):

        c.run(f"{VENV}/bin/python manage.py dumpdata {app} > /tmp/{dump_name}")
        c.get(f'/tmp/{dump_name}', output)


@task
def frontdump(ctx):
    """Dump front data only in different files."""
    dump_name = 'pwd_front_{:%Y-%m-%d}'.format(datetime.now())
    # dump_name = 'front'
    apps_to_dump = ['slider', 'blurb', 'page', 'paragraph', 'sitesettings']
    with get_connection(ctx) as c:
        for app in apps_to_dump:
            _dump(c, f"pwd_front.{app}", f"{dump_name}_{app}.json")


@task
def loadinitials(ctx):
    """Load initials data into a fresh installed version."""
    with get_connection(ctx) as c:
        with c.cd(APP_DIR):
            c.run(f"{VENV}/bin/python manage.py load_initials")
            c.run(f"{VENV}/bin/python manage.py load_legacy")
