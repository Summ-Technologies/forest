import errno
import os
import sys
import types


"""
This class probably doesn't belong in the redwood-core package.
It should probably live in a summn-foundation package, maybe logging and config
related functionality could form a summn-common (or redwood-common) package
that is imported into every module used, web, runner, jobs, etc

But for now, redwood-core will do.
"""


class Config(dict):
    """
    Mimics flask app config object directly for convenience.
    Copied straight from their codebase.
    """

    def from_pyfile(self, filename, silent=False):
        """https://github.com/pallets/flask/blob/024f0d384cf5bb65c76ac59f8ddce464b2dc2ca1/src/flask/config.py#L27"""
        filename = os.path.join(os.getcwd(), filename)
        d = types.ModuleType("config")
        d.__file__ = filename
        try:
            with open(filename, mode="rb") as config_file:
                exec(compile(config_file.read(), filename, "exec"), d.__dict__)
        except OSError as e:
            if silent and e.errno in (errno.ENOENT, errno.EISDIR, errno.ENOTDIR):
                return False
            e.strerror = f"Unable to load configuration file ({e.strerror})"
            raise
        self.from_object(d)
        return True

    def from_object(self, obj):
        if isinstance(obj, str):
            obj = import_string(obj)
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)


def import_string(import_name: str, silent: bool = False):
    """https://github.com/pallets/werkzeug/blob/ef545f0d0bf28cbad02066b4cb7471bea50a93ee/src/werkzeug/utils.py#L783"""
    import_name = import_name.replace(":", ".")
    try:
        try:
            __import__(import_name)
        except ImportError:
            if "." not in import_name:
                raise
        else:
            return sys.modules[import_name]

        module_name, obj_name = import_name.rsplit(".", 1)
        module = __import__(module_name, globals(), locals(), [obj_name])
        try:
            return getattr(module, obj_name)
        except AttributeError as e:
            raise ImportError(e)

    except ImportError as e:
        if not silent:
            raise ImportError(e)

    return None
