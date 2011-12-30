"""Validate all aspects of an application"""

import re
import os


def validate(app):
    errors = []
    if not re.search(r'^[a-zA-Z][a-zA-Z0-9_-]*$', app.name):
        errors.append(
            "Application name (%r) must be letters and number, _, and -" % app.name)
    if app.static_path:
        if not os.path.exists(app.static_path):
            errors.append(
                "Application static path (%s) does not exist" % app.static_path)
        elif not os.path.isdir(app.static_path):
            errors.append(
                "Application static path (%s) must be a directory" % app.static_path)
    if not app.runner:
        errors.append(
            "Application runner is not set")
    elif not os.path.exists(app.runner):
        errors.append(
            "Application runner file (%s) does not exist" % app.runner)
    ## FIXME: validate config_template and config_validator
    if app.config_default:
        if not os.path.exists(app.config_default):
            errors.append(
                "Application config.default (%s) does not exist" % app.config_default)
        elif not os.path.isdir(app.config_default):
            errors.append(
                "Application config.default (%s) is not a directory" % app.config_default)
    if app.add_paths:
        for index, path in enumerate(app.add_paths):
            if not os.path.exists(path):
                errors.append(
                    "Application add_paths[%r] (%s) does not exist"
                    % (index, path))
            elif not os.path.isdir(path):
                ## FIXME: I guess it could be a zip file?
                errors.append(
                    "Application add_paths[%r] (%s) is not a directory"
                    % (index, path))
    return errors


if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        print 'Usage: %s APP_DIR' % sys.argv[0]
        sys.exit(1)
    import pywebapp
    app = pywebapp.PyWebApp.from_path(sys.argv[1])
    errors = validate(app)
    if not errors:
        print 'Application OK'
    else:
        print 'Errors in application:'
        for line in errors:
            print ' * %s' % line
