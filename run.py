# Author: Nam Nguyen Hoai
# Author: Dai Dang Van

import os
import tempfile
import shutil

from oslo_config import cfg
from oslo_config import generator as gn

__all__ = ['get_conf']


def get_conf(namespaces_file):
    conf = cfg.ConfigOpts()
    gn.register_cli_opts(conf)
    oslo_args = ['--config-file', namespaces_file]
    conf(oslo_args)
    groups = gn._get_groups(gn._list_opts(conf.namespace))

    new_conf = cfg.ConfigOpts()
    all_namespaces = []
    for k, v in groups.items():
        group = cfg.OptGroup(k)
        try:
            namespaces = v.get('namespaces', [])
        except:
            namespaces = v
        list_opts = []
        for namespace in namespaces:
            all_namespaces.append(namespace[0])
            list_opts.extend(namespace[1])
        new_conf.register_group(group)
        if k == 'DEFAULT':
            new_conf.register_opts(list_opts)
        new_conf.register_opts(list_opts, group=group)

    return new_conf


def make_enviroment(project_name, branch, namespaces_file):
    # Backup working directory
    working_directory = os.getcwd()

    # Make random directory
    # tmp = tempfile.mkdtemp()
    tmp = '/tmp'
    # Jump into random directory
    os.chdir(tmp)
    # Clone code from git/home/stack/daidv_workspace/get_difference
    url = "git clone https://github.com/openstack/{} -b {}".format(project_name, branch)
    os.system(url)
    os.chdir(project_name)

    # Do something here
    conf = get_conf(namespaces_file)

    # Clean up temporary directory
    os.chdir(working_directory)
    # shutil.rmtree(tmp)

    return conf


if __name__ == '__main__':
    project_name = 'neutron'
    mitaka_branch = 'mitaka-eol'
    ocata_branch = 'stable/ocata'
    namespaces_file = '/home/stack/daidv_workspace/get_difference/project_namespaces/keystone/keystone.conf'

    mitaka = make_enviroment(project_name, mitaka_branch, namespaces_file)
    ocata = make_enviroment(project_name, ocata_branch, namespaces_file)

    print(ocata)
