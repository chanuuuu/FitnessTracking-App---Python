def navigation(links):
    """Generate a set of navigation links enclosed in 
    a UL element from a list of
    links, each link is a pair (url, text) which is 
    turned into the HTML <a href="url">text</a>, each
    link is embedded in a <li> inside a <ul>  
    Return the HTML as a string"""
    
    nav = "<ul class='nav'>\n"
    for link in links:
        nav += "<li><a href='%s'>%s</a></li>\n" % link
    nav += "</ul>\n"
    
    return nav
    
def quote_content(content):
    """Return a sanitised version of the text"""
    
    text = str(content)
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    
    return text
    

def table(headings, data):
    """Generate an HTML table with column
    headings taken from the list headings (a list of strings) 
    and the cell entries taken from data (a list of lists).
    Return a string containing the generated table HTML"""
        
    table = "<table><tr>"
    for head in headings:
        table += "<th>"+head+"</th>"
    table += "</tr>\n"
    for row in data:
        table += "<tr>"
        for cell in row:
            table += "<td>"+quote_content(cell)+"</td>"
        table += "</tr>\n"
    table += "</table>\n"
    
    return table


def insert_values(content, template):
    import re
    
    if content.has_key('message') and content['message'] != '':
        content['message'] = "<div class='alert'><p>%s</p></div>" % content['message']

    page = template
    for key in content.keys():
        page = page.replace("%"+key, content[key])
    
    page = re.sub("%[a-z]+", "", page)
    
    return page

def load_page(content, path):
    f = open(path, 'r')
    return insert_values(content, f.read())