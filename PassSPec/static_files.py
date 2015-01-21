"""Define a WSGI application to serve static content"""

import os

def make_static_application(basepath, staticdir, not_found):
    """Return a WSGI application procedure that will 
    serve static files from within the given directory
    basepath is a prefix that will be removed from 
    the requested path and replaced with staticdir to
    get the full file name requested.
    not_found is a WSGI application that will be called if the path
    is not found"""
    
    def app(environ, start_response):
         
        path = environ['PATH_INFO']
        if path.startswith(basepath):
            path = path[len(basepath):]
            path = os.path.join(staticdir, path) 
            if os.path.exists(path):
                h = open(path, 'r')
                content = h.read()
                h.close()
                headers = [('Content-Type', content_type(path))]
                start_response("200 OK", headers)
                return [content,]
        
        # either we have a bad path or the path doesn't exist
        # so call the not_found app    
        return not_found(environ, start_response)
    
    return app


def content_type(path):
    """Return a guess at the content type of
    the given file"""
    
    if path.endswith(".css"):
        return "text/css"
    elif path.endswith(".html"):
        return "text/html"
    elif path.endswith(".jpg"):
        return "image/jpeg"    
    elif path.endswith(".js"):
        return "text/javascript"
    else:
        return "application/octet-stream"
    