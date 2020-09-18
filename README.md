# pyaconf - yet another config library built around python dictionary

Pyaconf is a config library that is built around python dictionary and supports dynamic python, json, yaml, and ini formats with inheritance.
It features:

## Features

* 4 formats (pyaconf [python], yaml, json, ini) that can be layered on top of each other,
* dynamic pyaconf (python) format,
* __include__ feature that can layer combine the 4 formats hierarchically,
* “merge” capability that allows to override values by the topmost layer,
* jinja2 template substitution capability that can be injected at various layers of override and dictionary hierarchies, 
* simple 3 function (load, merge, and dump) Python API, and  
* command line utility that allows us to use all these features from the command line 


## Notes

* All configs are json compatible dicts.
* Supports layered configs (inheritance) via `__include__` dict entry, for example, the following yaml config would read the dictionary defined from config `boo.json` and then will update it with `user` and `password` from this config:

```yaml
__include__: boo.json
user: romeo
password: romeoalpha
```

* Includes may be used at any level and apply only to its layer. 
* Simple API: `load`, `dump`, and for more advanced use `merge`.
* Supports dynamic configs written in Python `.pyaconf`, for example:

```python
import os
def config():
   return dict(
      __include__ = ["secret.yml"],
      user = "romeo", 
      password = os.environ['PASSWORD'],
      database = dict(
         __include__ = "db.ini",
      ),
   )
```

* Allows to output configs in `.json` and `.yaml`. Provides two shell scripts.
* Supports `.ini` input format as understood by python's `configparser`.
* Supports Jinji2 templates, you just need to add `.j2` or `.jinji2` extension to your config file and it will be processed by Jinji2. For example:

```yaml
user: {{ username }}
password = {{ password }}
```

* The dictionary that contains includes serves as a context for these includes. For template includes, the dictionary is passed as a context to the template processing. For non-template includes, the dictionary merges with the include. When all includes processed this way, they all merge together.

```yaml
__include__: [a.yaml.j2, b.yaml]
x: 1
y: 2
```

* Another example with template:

```yaml
# common.yaml.j2
host: local
user: {{ username }}
password: {{ password }}
credentials: [{{ password }}, {{username}}]
```

```yaml
# devel.yaml
__include__: common.yaml.j2
username: Donald
password: Trump
office: 113D
```

```yaml
# pyaconf_render -f json devel.yaml
{
  "credentials": [
     "Trump",
     "Donald"
  ],
  "host": "local",
  "password": "Trump",
  "user": "Donald"
}
```

## API

### load

```python
def load(src, *, format='auto', path=None, context={}):
   """ loads a dict that may include special keyword '__include__' at multiple levels,
   and resolves these includes and returns a dict without includes. It can also read the input dict from a file
   src -- dict|Mapping, FILE|io.StringIO(s), pathlib.Path|str
   format -- 'auto' | 'pyaconf' | 'json' | 'yaml' | 'ini'
   path -- is used only when src doesn't contain path info, it is used for error messages and resolve relative include paths
   context -- is a dict that is used as context for template rendering if src is a template
   """
```

### dump

```python
def dump(x, dst=sys.stdout, *, format='auto'):
   """ Dumps resolved (without includes) config in json or yaml format. It doesn't preserve comments either. 
   x -- dict|Mapping
   dst -- FILE|io.StringIO(s), pathlib.Path|str
   format -- 'auto' | 'json' | 'yaml'
   """
```


### merge

```python
def merge(xs):
   """ merges the list of dicts (that dont contain includes) and returns a new dict
   where the values of the first dict are updated recursively by the values of the second dict.
   xs -- a list of dicts
   """
```

## Scripts

* pyaconf_render -- loads and merges multiple configs and renders the result in json or yaml format

## License

OSI Approved 3 clause BSD License

## Prerequisites

* Python 3.7+

## Installation

If prerequisites are met, you can install `pyaconf` like any other Python package, using pip to download it from PyPI:

    $ pip install pyaconf

or using `setup.py` if you have downloaded the source package locally:

    $ python setup.py build
    $ sudo python setup.py install
