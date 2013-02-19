# -*- coding: utf-8 -*-
# 
#  github.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-02-18.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

import bs4
import urllib2

def get_dependencies(file="setup.py"):
    """Get file dependencies from a setup.py file."""
    

def get_depend_url(module,user,github="https://github.com"):
    """Get the latest dependency URL from github for a specific package."""
    url = "{github}/{user}/{module}/tags".format(user=user,module=module,github=github)
    data = urllib2.urlopen(url).read()
    soup = bs4.BeautifulSoup(data)
    link = soup.select(".tag-list .tag-info li a")[1]
    href = link.attrs["href"]
    version = href.split("/")[-1]
    setup_href = "{github}{href}#egg={module}-{version}"
    return setup_href
    
def get_blind_depend_url(tag,module,user,github="https://github.com"):
    """Blindly get the url of a package given a tag."""
    version = tag.lstrip("v")
    url = "{github}/{user}/{module}/{archive}/{tag}#egg={module}-{version}".format(
        tag = tag,
        module = module,
        user = user,
        github = github,
        version = version
    )
    return url