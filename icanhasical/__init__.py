from pyramid.config import Configurator
from wsgiref.simple_server import make_server

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.scan('icanhasical.views')
    return config.make_wsgi_app()
