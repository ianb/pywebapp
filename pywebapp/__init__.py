import os
import pyyaml
import zipfile
import tempfile


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
            self.read_config()
        return self._config

    def read_config(self):
        fp = self.get_file('app.yaml')
        try:
            return pyyaml.load(fp)
        finally:
            fp.close()

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

    @property
    def runner(self):
        """The filename of the runner for this application"""
        return self.abspath(self.config['runner'])

    @property
    def static_path(self):
        if 'static' in self.config:
            return self.abspath(self.config['static'])
        elif self.exists('static'):
            return self.abspath('static')
        else:
            return None

    ## FIXME: don't like this name (Silver Lining: .packages)
    @property
    def requires(self):
        v = self.config.get('requires')
        if not v:
            return []
        if isinstance(v, basestring):
            v = [v]
        return v

    @property
    def config_required(self):
        return self.config.get('config', {}).get('required')

    @property
    def config_template(self):
        v = self.config.get('config', {}).get('template')
        if v:
            return self.abspath(v)
        return None

    @property
    def config_checker(self):
        v = self.config.get('config', {}).get('checker')
        if v:
            return self.objloader(v, 'config.checker')
        return None

    @property
    def config_default(self):
        dir = self.config.get('config', {}).get('default')
        if dir:
            return self.abspath(dir)
        return None

    def activate_path(self):
        norm_paths = [os.path.normcase(os.path.abspath(p)) for p in sys.path
                      if os.path.exists(p)]
        lib_path = self.abspath('lib/python%s/site-packages' % sys.version[:3])
        if lib_path not in norm_path and os.path.exists(lib_path):
            addsitedir(lib_path)
        sitecustomize = self.abspath('lib/python%s/sitecustomize.py' % sys.version[:3])
        if os.path.exists(sitecustomize):
            ns = {'__file__': sitecustomize, '__name__': 'sitecustomize'}
            execfile(sitecustomize, ns)
        lib_path = self.abspath('lib/python')
        if lib_path not in norm_path and os.path.exists(lib_path):
            addsitedir(lib_path)
