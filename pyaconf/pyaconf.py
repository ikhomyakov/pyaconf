"""Yet another config library that is built around python dict and supports json, yaml
"""
# Copyright (c) 2002-2019 Aware Software, inc. All rights reserved.
# Copyright (c) 2005-2019 ikh software, inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

#
# pyaconf/pyaconf.py
#
import io
import sys
import collections.abc
import json
import yaml
import itertools
import pathlib
import configparser
import jinja2

LOAD_KEY = "__include__"


def logg(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# --- load ---


def load(src, *, format="auto", path=None, context={}):
    """ loads a dict that may include special keyword '__include__' at multiple levels,
   and resolves these includes and returns a dict without includes. It can also read the input dict from a file
   src -- dict|Mapping, FILE|io.StringIO(s), pathlib.Path|str
   format -- 'auto' | 'pyaconf' | 'json' | 'yaml' | 'ini'
   path -- is used only when src doesn't contain path info, it is used for error messages and resolve relative include paths
   context -- is a dict that is used as context for template rendering if src is a template
   """
    if path is not None and not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    if isinstance(src, collections.abc.Mapping):
        r = _load_dict(src, path)
    elif isinstance(src, io.IOBase):
        if format == "auto":
            raise Exception(
                f"pyaconf.load: specify format (format={format}, path={path})"
            )
        r = _load_file(src, format, path, context)
    elif isinstance(src, str):
        r = load(pathlib.Path(src), format=format, path=path, context=context)
    elif isinstance(src, pathlib.Path):
        if format == "auto":
            ext = "".join(src.suffixes)
            if ext in _input_extensions:
                format = _input_extensions[ext]
            else:
                raise Exception(
                    f"pyaconf.load: cannot derive format from file extension, specify format (path={src}, context={context})"
                )

        if path is not None and not src.is_absolute():
            src = path.parent / src

        with open(src, "r") as f:
            r = _load_file(f, format, src, context)
    else:
        raise Exception(f"pyaconf.load: illegal type of src (type={typ}, path={path})")
    return r


_input_extensions = {
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".pyaconf": "pyaconf",
    ".ini": "ini",
    ".yaml.jinja2": "yaml.jinja2",
    ".yml.jinja2": "yaml.jinja2",
    ".json.jinja2": "json.jinja2",
    ".pyaconf.jinja2": "pyaconf.jinja2",
    ".ini.jinja2": "ini.jinja2",
    ".yaml.j2": "yaml.jinja2",
    ".yml.j2": "yml.jinja2",
    ".json.j2": "json.jinja2",
    ".pyaconf.j2": "pyaconf.jinja2",
    ".ini.j2": "ini.jinja2",
}

_output_extensions = {".yaml": "yaml", ".yml": "yaml", ".json": "json"}


def _load(x, path):
    if isinstance(x, collections.abc.Mapping):
        r = _load_dict(x, path)
    elif isinstance(x, list):
        r = _load_list(x, path)
    else:
        r = x
    return r


def _load_dict(x, path):
    c = {}
    for k, v in x.items():
        if k != LOAD_KEY:
            c[k] = _load(v, path)

    rs = []
    if LOAD_KEY in x:
        loads = x[LOAD_KEY]
        for v in loads if isinstance(loads, list) else [loads]:
            rs.append(
                load(**v, path=path, context=c)
                if isinstance(v, collections.abc.Mapping)
                else load(v, path=path, context=c)
            )

    r = merge(rs) if rs != [] else c

    return r


def _load_list(x, path):
    return [_load(a, path) for a in x]


def _load_file(f, format, path, context):
    cf, tf = (format.split(".") + [None] * 2)[:2]
    if tf is not None:
        if tf == "jinja2":
            spath = path.parent if path is not None else "."
            tloader = jinja2.FileSystemLoader(searchpath=str(spath))
            tenv = jinja2.Environment(loader=tloader)
            t = tenv.from_string(f.read())
            f = io.StringIO(t.render(context))
        else:
            raise Exception(
                f"pyaconf.load: template engine is not supported (format={format}, path={path}, context={context})"
            )

    if cf == "yaml":
        x = yaml.load(f, Loader=yaml.Loader)
    elif cf == "json":
        x = json.load(f)
    elif cf == "pyaconf":
        c = f.read()
        genv = {}
        exec(compile(c, path, "exec"), genv)
        x = eval("config()", genv)
    elif cf == "ini":
        x = _load_ini(f, path)
    else:
        raise Exception(
            f"pyaconf.load: config format is not supported (format={format}, path={path}, context={context})"
        )

    r = _load(x, path)
    if tf is None:
        r = merge([r, context])
    return r


def _load_ini(f, path):
    c = configparser.ConfigParser()
    c.read_file(f)
    r = {}
    for s in c.sections():
        if s != "DEFAULT":
            r[s] = dict(c[s])
    return r


# --- merge ---


def merge(xs):
    """ merges the list of dicts (that dont contain includes) and returns a new dict
   where the values of the first dict are updated recursively by the values of the second dict.
   xs -- a list of dicts
   """
    if len(xs) == 0:
        r = {}
    elif len(xs) == 1:
        r = xs[0]
    else:
        r = xs[0]
        for x in xs[1:]:
            r = _deep_merge(r, x)
    return r


def _deep_merge(z, x):
    if isinstance(z, collections.abc.Mapping) and isinstance(
        x, collections.abc.Mapping
    ):
        r = _deep_merge_dicts(z, x)
    elif isinstance(z, list) and isinstance(x, list):
        r = _deep_merge_lists(z, x)
    else:
        r = x
    return r


def _deep_merge_dicts(z, x):
    r = {}
    for k, v in z.items():
        if k in x:
            r[k] = _deep_merge(v, x[k])
        else:
            r[k] = v
    for k, v in x.items():
        if k not in r:
            r[k] = v
    return r


def _deep_merge_lists(z, x):
    return [
        _deep_merge(a, b)
        for (a, b) in (itertools.zip_longest(z, x) if len(x) > len(z) else zip(z, x))
    ]


# --- dump ---


def dump(x, dst=sys.stdout, *, format="auto"):
    """ Dumps resolved (without includes) config in json or yaml format. It doesn't preserve comments either. 
   x -- dict|Mapping
   dst -- FILE|io.StringIO(s), pathlib.Path|str
   format -- 'auto' | 'json' | 'yaml'
   """
    if isinstance(dst, io.IOBase):
        if format == "auto":
            raise Exception(f"pyaconf.dump: specify format (format={format})")
        r = _dump_file(x, dst, format)
    elif isinstance(dst, str):
        r = dump(x, pathlib.Path(dst), format=format)
    elif isinstance(dst, pathlib.Path):
        if format == "auto":
            ext = dst.suffix
            if ext in _output_extensions:
                format = _output_extensions[ext]
            else:
                raise Exception(
                    f"pyaconf.dump: cannot derive format from file extension, specify format (path={dst})"
                )
        with open(dst, "w") as f:
            r = _dump_file(x, f, format)
    else:
        raise Exception(f"pyaconf.dump: illegal type of dst")


def _dump_file(x, f, format):
    if format == "json":
        json.dump(x, f, sort_keys=True, indent=3)
    elif format == "yaml":
        yaml.dump(x, f, default_style="", default_flow_style=False)
    else:
        raise Exception(f"pyaconf.dump: illegal format (format={format})")
