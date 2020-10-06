"""CLI commands for Invenio-MaDMP."""

import json
import os.path
import sys

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier

from .convert import convert_dmp
from .models import DataManagementPlan


@click.group()
def madmp():
    """Commands for maDMPs."""
    pass


@madmp.command("list")
@with_appcontext
def madmp_list():
    """List all stored DMPs along with their datasets."""
    for dmp in DataManagementPlan.query.all():
        click.echo("[DMP] %s" % dmp.dmp_id)

        for dataset in dmp.datasets:
            recid = "[no record]"

            if dataset.record:
                pid = PersistentIdentifier.get_by_object(
                    "recid", "rec", dataset.record.id
                )
                recid = "[recid: %s]" % pid.pid_value

            click.echo("  [DS] %s %s" % (dataset.dataset_id, recid))
        click.echo("")


@madmp.command("import")
@click.argument("file")
@click.option("--dry-run", "-d", is_flag=True, default=False)
@click.option(
    "--hard-sync/--soft-sync",
    "-h/-s",
    default=False,
    help="whether to only check for new/removed datasets (soft sync) or to also force updates on existing datasets (hard sync)",  # noqa
)
@with_appcontext
def madmp_import(file, dry_run, hard_sync):
    """Import maDMP from the specified JSON file."""
    if not file or not os.path.isfile(file):
        click.secho("'%s' is not a file" % file, file=sys.stderr, fg="red")
        return

    with open(file, "r") as dmp_file:
        dmp_dict = json.load(dmp_file).get("dmp", {})
        dmp = convert_dmp(dmp_dict, hard_sync=hard_sync)

        click.echo("DMP %s has %s datasets" % (dmp.dmp_id, len(dmp.datasets)))

        for dataset in dmp.datasets:
            recid = "[no record]"

            if dataset.record:
                pid = PersistentIdentifier.get_by_object(
                    "recid", "rec", dataset.record.id
                )
                recid = "[recid: %s]" % pid.pid_value

            click.echo("  DS: %s %s" % (dataset.dataset_id, recid))

    if dry_run:
        db.session.rollback()
    else:
        db.session.add(dmp)
        db.session.commit()
