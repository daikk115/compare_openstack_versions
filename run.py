# Author: Nam Nguyen Hoai
# Author: Dai Dang Van

import os
import tempfile
import shutil
import importlib
import sys

from oslo_config import cfg

__all__ = ['make_enviroment']


def import_opts(project_name):
    # Make setup.cfg url
    dir_path = os.getcwd()
    sys.path.insert(0, dir_path)
    setup_cfg = "{}/setup.cfg".format(dir_path)
    # Get list module should be called with
    setup_conf = cfg.ConfigOpts()
    setup_args = ['--config-file', setup_cfg]
    setup_conf(setup_args)
    section_options = setup_conf._namespace._parsed[0]
    _list = section_options['entry_points']['oslo.config.opts'][0].split('\n')
    _list_opts = []
    for option in _list:
        try:
            option = option.replace(':', '=')
            opts_module = option.split('=')[1].strip()
            _module = importlib.import_module(opts_module)
        except Exception as e:
            pass
        else:
            _list_opts.extend(_module.list_opts())
            # No need these any more
            # del _module
            # sys.modules.pop(opts_module)
    del sys.path[0]
    sys.modules.pop(project_name)  # We only need to pop top level module
    return _list_opts


def make_enviroment(project_name, branch):
    # Backup working directory
    working_directory = os.getcwd()

    # Make random directory
    # tmp = tempfile.mkdtemp()
    if branch == 'stable/ocata':
        tmp = '/home/stack/daidv_workspace/tmp/ocata'
    else:
        tmp = '/home/stack/daidv_workspace/tmp/mitaka/'
    # Jump into random directory
    os.chdir(tmp)
    # Clone code from git/home/stack/daidv_workspace/get_difference
    url = "git clone https://github.com/openstack/{} -b {}".format(
                                                        project_name, branch)
    os.system(url)
    os.chdir(project_name) # not really need for now

    # Do something here
    new_conf = cfg.ConfigOpts()
    list_opts = import_opts(project_name)
    for opt in list_opts:
        new_conf.register_opts(opt[1], group=opt[0])
        if not opt[0]:
            new_conf.register_opts(opt[1], group='DEFAULT')

    # Clean up temporary directory
    os.chdir(working_directory)
    # shutil.rmtree(tmp)

    return new_conf


if __name__ == '__main__':
    project_name = 'keystone'
    mitaka_branch = 'mitaka-eol'
    ocata_branch = 'stable/ocata'

    mitaka = make_enviroment(project_name, mitaka_branch)
    ocata = make_enviroment(project_name, ocata_branch)

    print(mitaka)
    print(ocata)
