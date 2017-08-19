# Author: Nam Nguyen Hoai
# Author: Dai Dang Van

import os
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
            module_function = option.split(':')
            opts_module = ".".join(tree.strip() for
                                   tree in module_function[0].split('=')[1:])
            _module = importlib.import_module(opts_module)
        except Exception as e:
            continue
        else:
            _list_opts.extend(getattr(_module, module_function[1])())
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
    good_branch = 'stable/' + branch
    alternative = branch + '-eol'
    tmp = '/home/stack/projects/' + branch
    # Jump into random directory
    try:
        os.chdir(tmp)
    except OSError:
        os.mkdir(tmp)
        os.chdir(tmp)
    try:
        # Clone code from git/home/stack/daidv_workspace/get_difference
        url = "git clone https://github.com/openstack/{} -b {}".format(
                                                            project_name, good_branch)
        os.system(url)
        os.chdir(project_name) # not really need for now
    except OSError:
        # When this exception occurs, it means that we can not clone the
        # project with good_branch. It needs to reclone with new branch.
        url = "git clone https://github.com/openstack/{} -b {}".format(
            project_name, alternative)
        os.system(url)
        os.chdir(project_name)  # not really need for now

    # Do something here
    new_conf = cfg.ConfigOpts()
    list_opts = import_opts(project_name.replace(".", "_"))
    for opt in list_opts:
        try:
            new_conf.register_opts(opt[1], group=opt[0])
            if not opt[0]:
                new_conf.register_opts(opt[1], group='DEFAULT')
        except cfg.DuplicateOptError as e:
            continue

    # Clean up temporary directory
    os.chdir(working_directory)
    # shutil.rmtree(tmp)

    return new_conf


def get_root_path(*directory):
    root_path = os.path.dirname(os.path.abspath(__file__))
    if directory is None:
        return root_path
    else:
        return os.path.join(root_path, *directory)


def make_conf_to_dict(input_conf):
    conf_dict = {}
    for name, section in input_conf._groups.items():
        conf_dict[name] = section._opts.keys()
    return conf_dict


def compare_two_dicts(input_dict1, input_dict2):
    """
    :param input_dict1:
    :param input_dict2:
    :return:
    """
    dict_diff = {}
    for key, options12 in input_dict1.items():
        if key not in input_dict2:
            dict_diff[key] = options12
        else:
            list1_diff = [option for option in options12 if option
                          not in input_dict2[key]]
            if list1_diff:
                dict_diff[key] = list1_diff
    return dict_diff


def gen_yaml_from_dict(deprecated_options, new_options, project):
    name_file_project = project.replace('.', '_') + '.yaml'
    output = get_root_path('template_yaml', 'n_to_o', name_file_project)
    with open(output, mode='w+') as f:
        f.write('deprecated_options:\n')
        for section, options in deprecated_options.items():
            f.write('  %s:\n' % section)
            for option in options:
                f.write('  - name: %s\n' % option['name'])
                f.write('    replacement_group: %s\n' % option['new_section'])
                f.write('    replacement_name: %s\n' % option['new_name'])
        f.write('new_options:\n')
        for new_section, new_opts in new_options.items():
            f.write('  %s:\n' % new_section)
            for new_opt in new_opts:
                f.write('  - name: %s\n' % new_opt)
                f.write('    value: None\n')
                f.write('    template: None\n')
                f.write('    mapping: None\n')


def make_deprecate_option_to_dict(CONF):
    """
    :param CONF: This is list_opt.
    :return:
    output1: List all deprecated options with full information.
    output2: List all deprecated options.
    output3: List all new options.
    """
    output1 = {}
    output2 = {}
    output3 = {}

    for section, options in CONF._groups.items():
        for new_name, k in options._opts.items():
            list_deprecated = k['opt'].deprecated_opts
            if len(list_deprecated) == 0:
                continue
            else:
                group_deprecated = list_deprecated[0].group
                if str(group_deprecated) == 'None':
                    group_deprecated = section
                name_deprecated = list_deprecated[0].name
                if str(name_deprecated) == 'None':
                    name_deprecated = new_name
                if group_deprecated not in output1:
                    output1[group_deprecated] = [{
                        'name': name_deprecated,
                        'new_name': new_name,
                        'new_section': section
                    }]
                    output2[group_deprecated] = [name_deprecated]
                else:
                    output1[group_deprecated].append({
                        'name': name_deprecated,
                        'new_name': new_name,
                        'new_section': section
                    })
                    output2[group_deprecated].append(name_deprecated)
                if section not in output3:
                    output3[section] = [new_name]
                else:
                    output3[section].append(new_name)
    return output1, output2, output3


if __name__ == '__main__':
    project_name = 'keystone'
    base_branch = 'newton'
    target_branch = 'ocata'

    base_conf_object = make_enviroment(project_name, base_branch)
    target_conf_object = make_enviroment(project_name, target_branch)
    # Create a conf with type is dict from conf object
    base_conf_dict = make_conf_to_dict(base_conf_object)
    target_conf_dict = make_conf_to_dict(target_conf_object)

    # Show difference options between base release and target release
    base_with_target = compare_two_dicts(base_conf_dict, target_conf_dict)
    target_with_base = compare_two_dicts(target_conf_dict, base_conf_dict)

    list_fully_deprecated, list_deprecated, new_options = \
        make_deprecate_option_to_dict(target_conf_object)

    # Generate a yaml file.
    gen_yaml_from_dict(list_fully_deprecated, new_options=new_options,
                       project=project_name)
