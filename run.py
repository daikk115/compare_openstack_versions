# Author: Nam Nguyen Hoai
# Author: Dai Dang Van

import os
from oslo_config import generator as gn
from oslo_config import cfg

__all__ = ['make_enviroment']


def get_root_path(*directory):
    root_path = os.path.dirname(os.path.abspath(__file__))
    if directory is None:
        return root_path
    else:
        return os.path.join(root_path, *directory)


def gen_yaml_from_dict(deprecated_options, new_options, project):
    name_file_project = project.replace('.', '_') + '.yaml'
    output = get_root_path('template_yaml', name_file_project)
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


def get_conf(conf_file, project):
    conf = cfg.ConfigOpts()
    gn.register_cli_opts(conf)
    oslo_args = ['--config-file', conf_file]
    conf(oslo_args)
    groups = gn._get_groups(gn._list_opts(conf.namespace))

    # Make new CONF
    new_conf = cfg.ConfigOpts()
    for k, v in groups.items():
        group = cfg.OptGroup(k)
        try:
            namespaces = v.get('namespaces', [])
        except:
            namespaces = v
        list_opts = []
        for namespace in namespaces:
            if project in namespace[0].strip():
                list_opts.extend(namespace[1])

        if list_opts:
            new_conf.register_group(group)
            if k == 'DEFAULT':
                new_conf.register_opts(list_opts)
            new_conf.register_opts(list_opts, group=group)
    return new_conf


if __name__ == '__main__':
    project_name = 'cinder'
    target_conf_object = get_conf('/opt/stack/cinder/cinder/config/cinder-config-generator.conf', 'cinder')
    list_fully_deprecated, list_deprecated, new_options = \
        make_deprecate_option_to_dict(target_conf_object)
    # Generate a yaml file.
    gen_yaml_from_dict(list_fully_deprecated, new_options=new_options,
                       project=project_name)
