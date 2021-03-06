# -*- coding: utf-8 -*-

import glob
import os
import sys
import types


class optional(str):

    """Wrap a file path with this class to mark it as optional.

    Optional paths don't raise an IOError if file is not found.
    """
    pass


def include(*args, **kwargs):
    """Used for including Django project settings from multiple files.

    Note: Expects to get ``scope=locals()`` as a keyword argument.

    Usage::

        from split_settings.tools import optional, include

        include(
            'components/base.py',
            'components/database.py',
            optional('local_settings.py'),

            scope=locals()
        )

    Parameters:
        *args: File paths (``glob``-compatible wildcards can be used)
        scope: The context for the settings, should always be ``locals()``
    Raises:
        IOError: if a required settings file is not found
    """
    scope = kwargs.pop("scope")
    including_file = scope.get('__included_file__', scope['__file__'])
    confpath = os.path.dirname(including_file)
    for conffile in args:
        saved_included_file = scope.get('__included_file__')
        pattern = os.path.join(confpath, conffile)

        # find files per pattern, raise an error if not found (unless file is
        # optional)
        files_to_include = glob.glob(pattern)
        if not files_to_include and not isinstance(conffile, optional):
            raise IOError('No such file: %s' % pattern)

        for included_file in files_to_include:
            scope['__included_file__'] = included_file

            relative_path = conffile[:conffile.rfind('.')].replace('/', '.')

            # check python version
            if sys.version_info[0] < 3:
                execfile(included_file, {}, scope)
            else:
                exec(
                    compile(
                        open(included_file, "rb").read(),
                        included_file,
                        'exec'),
                    {},
                    scope)

            # add dummy modules to sys.modules to make runserver autoreload
            # work with settings components
            modulename = '_split_settings.%s' % relative_path
            module = types.ModuleType(modulename)
            module.__file__ = included_file
            sys.modules[modulename] = module
        scope['__included_file__'] = saved_included_file
