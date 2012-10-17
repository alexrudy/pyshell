# -*- coding: utf-8 -*-
# 
#  util.py
#  jaberwocky
#  
#  Created by Jaberwocky on 2012-10-16.
#  Copyright 2012 Jaberwocky. All rights reserved.
# 

import os

def force_dir_path(path):
    """Force the input path to be a directory."""
    path = os.path.normpath(path)
    if path.endswith("/"):
        return path.rstrip("/") + "/"
    else:
        return path + "/"