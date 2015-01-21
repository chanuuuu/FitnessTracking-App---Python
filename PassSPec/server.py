from wsgiref import simple_server
from collections import OrderedDict
import cgi
import fnmatch
import static_files
import templating
import time
from datetime import datetime
from sqlite3 import dbapi2 as sqlite
import json

def get_series():
    conn = sqlite.connect("tml.db")
    cur = conn.cursor()
    conn.text_factory = str
    cur.execute("select distinct series from data")
    series = []
    for row in cur.fetchall():
      series.append(row[0])
    return series

def get_data(series):
    conn = sqlite.connect("tml.db")
    cur = conn.cursor()
    conn.text_factory = str
    cur.execute("select value, at from data where series = ?", [series])
    data = {}
    for row in cur.fetchall():
      data[time.mktime(datetime.strptime(row[1], '%Y-%m-%d').timetuple())] = float(row[0])
    return data


def not_found(environ, start_response):
    start_response('404 Not Found', [('content-type','text/html')])
    return ["""<html><h1>Page not Found</h1><p>That page is unknown. Return to the <a href="/">home page</a></p></html>""",]  

def index(environ, start_response):
    start_response('200 OK', [('content-type','text/html')])
    values = {}
    values["graphs"] = ""

    for s in get_series():
      print s
      params={}
      vs = get_data(s)
      vs = OrderedDict(sorted(vs.items(), key=lambda t: t[0]))
      print vs
      params["id"] = s
      def normalise(v, vs):
        if (max(vs) - min(vs) <= 0):
          return (v - min(vs))
        else:
          return ((v - min(vs)) / (max(vs) - min(vs)))
      params["points"] = "["
      for k in vs.keys():
        kn = normalise(k,vs.keys())
        vn = normalise(vs[k],vs.values())
        params["points"] += "{x:"+str(kn)+",y:"+str(vn)+"},"
      params["points"] += "]"
      g = templating.load_page(params, "graph.html")
      values["graphs"] += g

    page = templating.load_page(values, "index.html")
    return [page,]  

def add_value(environ, start_response):
    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)

    conn = sqlite.connect("tml.db")
    cur = conn.cursor()
    cur.execute("insert into data values (?,?,?)", [form.getvalue("date", ""),
                                                    form.getvalue("value", ""), 
                                                    form.getvalue("series", ""),
                                                   ])
    conn.commit()
    start_response('302 Redirect', [('Location', '/index.html')])
    return []

def prac(environ,start_response):

    start_response('200 OK', [('content-type','application/json')])
    
    conn = sqlite.connect("tml.db")
    cur = conn.cursor()
    cur.execute("select * from data")

    d=[]
    v=[]
    u=[]
    s=[]
    w=[]

    

    for row in cur.fetchall():
      if environ['PATH_INFO'] == '/series/{}'.format(row[2]):
         d.append(row[0])
         v.append(row[1])  
      if environ['PATH_INFO'] == '/series/{}/{}'.format(row[2],row[0]):
          u.append(row[1])

          
    if len(d)!=0:
         return json.dumps({'dates':d,'values':v})
    if len(u)!=0:
         return json.dumps({'values':u})

    cur.execute("select * from data order by at")
    for row in cur.fetchall():

        path = environ['PATH_INFO']
        print path
      
        if path.startswith('/series/'):
           path = path[len('/series/'):]
           print path
           if path.startswith(row[2]):
              path = path[len(row[2])+1:]  
              print path           
               
        if environ['PATH_INFO'] == '/series/{}/{}'.format(row[2],path):
           s.append(row[1]) 
           w.append(path)

    if len(s)!=0:
        if path.find('first')!=-1:
            return json.dumps({'value':s[0]})
        if path.find('last')!=-1:
            return json.dumps({'value':s[len(s)-1]})
        else:
            return json.dumps({'value':s[int(w[0])-1]})
    else:
         print "Invalid url"



routes = [('/static/*',     static_files.make_static_application('/static/', 'static', not_found)),
          ('/',             index),
          ('/index.html',   index),
          ('/form/new_value*', add_value),
          ('/series*',prac)
         ]

def application(environ, start_response):
    for path, app in routes: 
        if fnmatch.fnmatch(environ['PATH_INFO'], path): 
            return app(environ, start_response)
    return not_found(environ, start_response)

if __name__ == '__main__':
#    conn = sqlite.connect("tml.db")
#    cur = conn.cursor()
#    cur.execute("drop table if exists data")
#    cur.execute("create table data (at date, value int, series varchar)")
#    conn.commit()
    server = simple_server.make_server('localhost', 8080, application)
    print "Listening for requests on http://localhost:8080/"
    server.serve_forever()    
    