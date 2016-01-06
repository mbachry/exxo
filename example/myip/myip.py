import os
import multiprocessing
import pkgutil
import gunicorn.app.base
import io
import mimetypes
from flask import Flask, request, render_template
from flask.helpers import send_file, locked_cached_property
from jinja2 import PackageLoader


PORT = 5000


class ZipFlask(Flask):
    def send_static_file(self, filename):
        static_folder = os.path.relpath(self.static_folder, self.root_path)
        p = '/'.join((static_folder, filename))
        data = pkgutil.get_data(self.import_name, p)
        fp = io.BytesIO(data)
        return send_file(fp, mimetypes.guess_type(filename)[0])

    @locked_cached_property
    def jinja_loader(self):
        return PackageLoader(self.import_name, self.template_folder)


app = ZipFlask('myip')


@app.route('/')
def show_ip():
    return render_template('index.html', ip=request.remote_addr)



class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in self.options.items()
                       if key in self.cfg.settings and value is not None])
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    # app.run(debug=True)
    options = {
        'bind': '%s:%s' % ('127.0.0.1', PORT),
        'workers': (multiprocessing.cpu_count() * 2) + 1,
        'worker_class': 'gevent',
    }
    StandaloneApplication(app, options).run()


if __name__ == '__main__':
    main()
