import sys
import os
import yaml
import zipfile
import tempfile
from site import addsitedir


class PyWebApp(object):

    def __init__(self, path, is_zip, config=None):
        self.path = path
        self.is_zip = is_zip
        self._config = config

    @classmethod
    def from_path(cls, path):
        is_zip = os.path.isfile(path)
        ## FIXME: test if valid zip
        return cls(path, is_zip=is_zip)

    @property
    def config(self):
        if self._config is None:
            fp = self.get_file('app.yaml')
            try:
                return yaml.load(fp)
            finally:
                fp.close()
        return self._config

    ## Helpers for file names and handling:

    def get_file(self, relpath):
        if self.is_zip:
            zf = zipfile.ZipFile(self.path, 'r')
            return zf.open(relpath, 'rb')
        else:
            filename = os.path.join(self.path, relpath)
            return open(filename, 'rb')

    def expanded(self, path=None, tmpdir=None):
        if not self.is_zip:
            return self
        if path is None:
            path = tempfile.mkdtemp(dir=tmpdir)
        zf = zipfile.ZipFile(self.path, 'r')
        ## FIXME: this can escape the path (per zipfile docs):
        zf.extractall(path)
        return self.__class__.from_path(path)

    def abspath(self, *paths):
        return os.path.normcase(os.path.abspath(os.path.join(self.path, *paths)))

    def exists(self, path):
        if self.is_zip:
            zf = zipfile.ZipFile(path, 'r')
            try:
                try:
                    zf.getinfo(path)
                    return True
                except KeyError:
                    return False
            finally:
                zf.close()
        else:
            return os.path.exists(self.abspath(path))

    ## Properties to read and normalize specific configuration values:

    @property
    def static_path(self):
        """The path of static files"""
        if 'static' in self.config:
            return self.abspath(self.config['static'])
        elif self.exists('static'):
            return self.abspath('static')
        else:
            return None

    ## FIXME: don't like this name (Silver Lining: .packages)
    @property
    def requires(self):
        """A list of things the system must supply, e.g., lxml"""
        v = self.config.get('requires')
        if not v:
            return []
        if isinstance(v, basestring):
            v = [v]
        return v

    @property
    def runner(self):
        """The runner value (where the application is instantiated)"""
        runner = self.config.get('runner')
        if not runner:
            return None
        return self.abspath(runner)

    @property
    def config_required(self):
        """Bool: is the configuration required"""
        return self.config.get('config', {}).get('required')

    @property
    def config_template(self):
        """Path: where a configuration template exists"""
        v = self.config.get('config', {}).get('template')
        if v:
            return self.abspath(v)
        return None

    @property
    def config_validator(self):
        """Object: validator for the configuration"""
        v = self.config.get('config', {}).get('validator')
        if v:
            return self.objloader(v, 'config.validator')
        return None

    @property
    def config_default(self):
        """Path: default configuration if no other is provided"""
        dir = self.config.get('config', {}).get('default')
        if dir:
            return self.abspath(dir)
        return None

    @property
    def add_paths(self):
        """List of paths: things to add to sys.path"""
        dirs = self.config.get('add_paths', [])
        if isinstance(dirs, basestring):
            dirs = [dirs]
        ## FIXME: should ensure all paths are relative
        return [self.abspath(dir) for dir in dirs]

    @property
    def services(self):
        """Dict of {service_name: config}: all the configured services.  Config may be None"""
        services = self.config.get('services', [])
        if isinstance(services, list):
            services = dict((v, None) for v in services)
        return services

    ## Process initialization

    def activate_path(self):
        add_paths = list(self.add_paths)
        add_paths.extend([
            self.abspath('lib/python%s' % sys.version[:3]),
            self.abspath('lib/python%s/site-customize' % sys.version[:3]),
            self.abspath('lib/python'),
            ])
        for path in reversed(add_paths):
            self.add_path(path)

    def add_sys_path(self, path):
        """Adds one path to sys.path.

        This also reads .pth files, and makes sure all paths end up at the front, ahead
        of any system paths.
        """
        if not os.path.exists(path):
            return
        old_path = [os.path.normcase(os.path.abspath(p)) for p in sys.path
                    if os.path.exists(p)]
        addsitedir(path)
        new_paths = list(sys.path)
        sys.path[:] = old_path
        new_sitecustomizes = []
        for path in new_paths:
            path = os.path.normcase(os.path.abspath(path))
            if path not in sys.path:
                sys.path.insert(0, path)
                if os.path.exists(os.path.join(path, 'sitecustomize.py')):
                    new_sitecustomizes.append(os.path.join(path, 'sitecustomize.py'))
        for sitecustomize in new_sitecustomizes:
            ns = {'__file__': sitecustomize, '__name__': 'sitecustomize'}
            execfile(sitecustomize, ns)

    @property
    def wsgi_app(self):
        runner = self.runner
        if runner is None:
            raise Exception(
                "No runner has been defined")
        ns = {'__file__': runner, '__name__': 'main_py'}
        execfile(runner, ns)
        if 'application' in ns:
            return ns['application']
        else:
            raise NameError("No application defined in %s" % runner)
