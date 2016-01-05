ACTIVATE_SCRIPT = """# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly

deactivate () {
    # reset old environment variables
    if [ -n "$_OLD_VIRTUAL_PATH" ] ; then
        PATH="$_OLD_VIRTUAL_PATH"
        export PATH
        unset _OLD_VIRTUAL_PATH
    fi
    # This should detect bash and zsh, which have a hash command that must
    # be called to get it to forget past commands.  Without forgetting
    # past commands the $PATH changes we made may not be respected
    if [ -n "$BASH" -o -n "$ZSH_VERSION" ] ; then
        hash -r
    fi

    if [ -n "$_OLD_PYTHONPATH" ] ; then
        PYTHONPATH="$_OLD_PYTHONPATH"
        export PYTHONPATH
        unset _OLD_PYTHONPATH
    fi

    if [ -n "$_OLD_VIRTUAL_PS1" ] ; then
        PS1="$_OLD_VIRTUAL_PS1"
        export PS1
        unset _OLD_VIRTUAL_PS1
    fi

    unset VIRTUAL_ENV
    if [ ! "$1" = "nondestructive" ] ; then
    # Self destruct!
        unset -f deactivate
    fi
}

# unset irrelavent variables
deactivate nondestructive

VIRTUAL_ENV="{{ venv_path }}"
export VIRTUAL_ENV

VIRTUAL_ENV_PYRUN_VERSION="{{ pyrun_version }}"
export VIRTUAL_ENV_PYRUN_VERSION

_OLD_PYTHONPATH="$PYTHONPATH"
PYTHONPATH="$VIRTUAL_ENV/pip/setuptools.egg:$VIRTUAL_ENV/pip/pip.egg:$PYTHONPATH"
export PYTHONPATH

_OLD_VIRTUAL_PATH="$PATH"
PATH="$VIRTUAL_ENV/bin:$PATH"
export PATH

if [ -z "$VIRTUAL_ENV_DISABLE_PROMPT" ] ; then
    _OLD_VIRTUAL_PS1="$PS1"
    if [ "x({{ venv_name }}) " != x ] ; then
        PS1="({{ venv_name }}) $PS1"
    else
    if [ "`basename \"$VIRTUAL_ENV\"`" = "__" ] ; then
        # special case for Aspen magic directories
        # see http://www.zetadev.com/software/aspen/
        PS1="[`basename \`dirname \"$VIRTUAL_ENV\"\``] $PS1"
    else
        PS1="(`basename \"$VIRTUAL_ENV\"`)$PS1"
    fi
    fi
    export PS1
fi

# This should detect bash and zsh, which have a hash command that must
# be called to get it to forget past commands.  Without forgetting
# past commands the $PATH changes we made may not be respected
if [ -n "$BASH" -o -n "$ZSH_VERSION" ] ; then
    hash -r
fi
"""

PIP_SCRIPT = """#!/usr/bin/env python
import os
import sys
import pkg_resources
import pip
import pip._vendor.pkg_resources

envdir = os.environ['VIRTUAL_ENV']
eggdir = os.path.join(envdir, 'pip')
setuptools_egg = os.path.join(eggdir, 'setuptools.egg')
pip_egg = os.path.join(eggdir, 'pip.egg')

for d in (eggdir, setuptools_egg, pip_egg):
    pkg_resources.working_set.entries.remove(d)
    pip._vendor.pkg_resources.working_set.entries.remove(d)

for p in ('setuptools', 'pip'):
    del pkg_resources.working_set.by_key[p]
    del pip._vendor.pkg_resources.working_set.by_key[p]

sys.exit(pip.main())
"""
