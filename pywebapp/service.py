"""This is experimental abstract base classes for implementing
services.

A container might use this, but it's very optional.
"""

import sys
import traceback


class AbstractService(object):

    name = None

    def __init__(self, app, service_settings):
        self.app = app
        self.service_settings = service_settings
        assert self.name is not None

    def settings(self):
        """Return the settings that should be put into websettings"""
        raise NotImplemented

    def install(self):
        """Implement per-service and per-tool installation for this service"""
        raise NotImplemented

    def backup(self, output_dir):
        """Back up this service to files in output_dir"""
        raise NotImplemented

    def restore(self, input_dir):
        """Restore from files, the inverse of backup"""
        raise NotImplemented

    def clear(self):
        """Clear the service's data, if applicable"""
        raise NotImplemented

    def check_setup(self):
        """Checks that the service is working, raise an error if not,
        return a string if there is a warning.

        For instance this might try to open a database connection to
        confirm the database is really accessible.
        """
        raise NotImplemented


class ServiceFinder(object):

    def __init__(self, module=None, package=None,
                 class_template='%(capital)sService'):
        if not module and not package:
            raise ValueError("You must pass in module or package")
        self.module = module
        self.package = package
        self.class_template = class_template

    def get_module(self):
        if isinstance(self.module, basestring):
            self.module = self.load_module(self.module)
        return self.module

    def get_package(self, name):
        if self.package is None:
            return None
        if not isinstance(self.package, basestring):
            self.package = self.package.__name__
        module = self.package + '.' + name
        return self.load_module(module)

    def load_module(self, module_name):
        if module_name not in sys.modules:
            __import__(module_name)
        return sys.modules[module_name]

    def get_service(self, name):
        class_name = self.class_template % dict(
            capital=name.capitalize(),
            upper=name.upper(),
            lower=name.lower(),
            name=name)
        module = self.get_module()
        obj = None
        if module:
            if self.package:
                obj = getattr(module, class_name, None)
            else:
                obj = getattr(module, class_name)
        if obj is None:
            package = self.get_package(name)
            if package:
                obj = getattr(package, class_name)
        if obj is None:
            raise ImportError("Could not find service %r" % name)
        return obj


def load_services(app, finder, services=None):
    result = {}
    if services is None:
        services = app.services
    for service_name in services:
        ServiceClass = finder.get_service(service_name)
        service = ServiceClass(app, services[service_name])
        result[service_name] = service
    return result


def call_services_method(failure_callback, services, method_name, *args, **kw):
    result = []
    last_exc = None
    for service_name, service in sorted(services.items()):
        method = getattr(service, method_name)
        try:
            result.append((service_name, method(*args, **kw)))
        except NotImplemented:
            failure_callback(
                service_name, '%s does not implement %s' % (service_name, method_name))
        except:
            last_exc = sys.exc_info()
            exc = traceback.format_exc()
            failure_callback(
                service_name, 'Exception in %s.%s:\n%s' % (service_name, method_name, exc))
    if last_exc:
        raise last_exc[0], last_exc[1], last_exc[2]
    return result
