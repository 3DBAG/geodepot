from logging import getLogger, basicConfig, DEBUG, INFO

from click import (
    group,
    command,
    pass_context,
    option,
    version_option,
    argument,
    Context,
)

from geodepot.case import CaseSpec
from geodepot.config import (
    config_list,
    configure,
    remote_list,
    remote_add,
    remote_remove,
)
from geodepot.errors import GeodepotInvalidRepository
from geodepot.repository import Repository


@group()
@version_option()
@option(
    "--verbose",
    " /-v",
    is_flag=True,
    default=False,
    help="Be verbose in reporting the progress.",
)
@pass_context
def geodepot_grp(ctx, verbose):
    loglevel = DEBUG if verbose else INFO
    basicConfig(level=loglevel)
    ctx.ensure_object(dict)
    ctx.obj["logger"] = getLogger(__name__)


@command(name="add", help="Add or update a case or a data item.")
@argument("casespec")
@argument("path", required=False, nargs=-1, type=str)
@option("--license", "data_license", help="A license to add to the data.")
@option("--description", help="A description to add to the case or data.")
@option(
    "--format",
    "data_format",
    help="A format to force on the data in case it cannot be inferred automatically, or the inferred format is not correct.",
)
@option("--as-data", is_flag=True, default=False, help="Add a whole directory as a single data entry.")
@pass_context
def add_cmd(ctx, casespec, path, data_license, description, data_format, as_data):
    repo = get_repository(ctx)
    if path is not None:
        for p in path:
            repo.add(
                casespec=casespec,
                pathspec=p,
                license=data_license,
                description=description,
                format=data_format,
                as_data=as_data,
            )
    else:
        repo.add(
            casespec=casespec,
            license=data_license,
            description=description,
            format=data_format,
            as_data=as_data,
        )


@group(name="config", help="Query or set configuration options.")
@pass_context
def config_grp(ctx):
    pass


@config_grp.command(
    name="list",
    help="List all variables set in the config files, along with their values.",
)
@pass_context
def config_list_cmd(ctx):
    output = config_list()
    if len(output) > 0:
        ctx.obj["logger"].info("\n" + "\n".join(output))


@config_grp.command(
    name="get",
    help="Emits the value of the specified key. If key is present multiple times in the configuration, emits the last value.",
)
@option(
    "--global",
    "global_config",
    default=False,
    help="Read only from the global configuration file rather than the repository configuration.",
)
@argument("name")
@pass_context
def config_get_cmd(ctx, name, global_config):
    val = configure(key=name, global_config=global_config)
    if val is not None:
        ctx.obj["logger"].info(f"{name}={val}")
    else:
        ctx.obj["logger"].info(f"{name} is not set")


@config_grp.command(name="set", help="Set the value for one configuration option.")
@option(
    "--global",
    "global_config",
    default=False,
    help="Write to the global configuration file rather than the repository configuration.",
)
@argument("name")
@argument("value")
@pass_context
def config_set_cmd(ctx, name, value, global_config):
    configure(key=name, value=value, global_config=global_config)


@command(name="get", help="Return the full local path to the specified data item.")
@argument("casespec")
@pass_context
def get_cmd(ctx, casespec):
    repo = get_repository(ctx)
    cs = CaseSpec.from_str(casespec)
    data_path = repo.get_data_path(cs)
    ctx.obj["logger"].info(f"{data_path}")


@command(
    name="init",
    help="Initialise a Geodepot repository in the current directory. With a URL to a remote repository as an argument, download the remote repository except its data, to make it available in the current working directory.",
)
@argument("url", required=False)
@pass_context
def init_cmd(ctx, url):
    do_create = True if url is None else False
    ctx.obj["repo"] = Repository(path=url, create=do_create)


@command(name="list", help="List the cases and data items in the repository.")
@pass_context
def list_cmd(ctx):
    repo = get_repository(ctx)
    for case_name, case in repo.cases.items():
        print(f"{case_name}")
        for data_name, data in case.data.items():
            print(f"\t/{data_name}")


@command(name="pull")
@pass_context
def pull_cmd(ctx):
    repo = get_repository(ctx)


@command(name="push")
@pass_context
def push_cmd(ctx):
    repo = get_repository(ctx)


@group(name="remote", help="Connect an existing remote Geodepot repository.")
@pass_context
def remote_grp(ctx):
    pass


@remote_grp.command(name="list", help="List the available remote repositories.")
@pass_context
def remote_list_cmd(ctx):
    output = remote_list()
    if len(output) > 0:
        ctx.obj["logger"].info("\n" + "\n".join(output))


@remote_grp.command(
    name="add",
    help="Add a remote repository to track. The remote repository must exist.",
)
@argument("name")
@argument("url")
@pass_context
def remote_add_cmd(ctx, name, url):
    remote_add(name, url)


@remote_grp.command(
    name="remove",
    help="Remove the remote from the tracked remotes. The remote repository is not deleted.",
)
@argument("name")
@pass_context
def remote_remove_cmd(ctx, name):
    remote_remove(name)


@command(name="remove", help="Delete a case or a data item from the repository.")
@argument("casespec")
@pass_context
def remove_cmd(ctx, casespec):
    cs = CaseSpec.from_str(casespec)
    repo = get_repository(ctx)
    repo.remove(cs)


@command(name="show", help="Show the details of a data item.")
@argument("casespec")
@pass_context
def show_cmd(ctx, casespec):
    repo = get_repository(ctx)
    cs = CaseSpec.from_str(casespec)
    case = repo.get_case(cs)
    if case is not None:
        if cs.data_name is None:
            ctx.obj["logger"].info("\n" + case.to_pretty())
        else:
            data = repo.get_data(cs)
            if data is not None:
                ctx.obj["logger"].info("\n" + data.to_pretty())


@command(name="verify")
@pass_context
def verify_cmd(ctx):
    repo = get_repository(ctx)


def get_repository(ctx: Context) -> Repository:
    try:
        return Repository()
    except GeodepotInvalidRepository as e:
        ctx.obj["logger"].critical(e)
        exit(1)


geodepot_grp.add_command(add_cmd)
geodepot_grp.add_command(config_grp)
geodepot_grp.add_command(get_cmd)
geodepot_grp.add_command(init_cmd)
geodepot_grp.add_command(list_cmd)
geodepot_grp.add_command(pull_cmd)
geodepot_grp.add_command(push_cmd)
geodepot_grp.add_command(remote_grp)
geodepot_grp.add_command(remove_cmd)
geodepot_grp.add_command(show_cmd)
geodepot_grp.add_command(verify_cmd)

if __name__ == "__main__":
    geodepot_grp()
