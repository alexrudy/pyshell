#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pyshell

class WorldCLI(pyshell.CLIEngine):
    
    defaultcfg = False
    
    def do(self):
        print("CLIs make the world go round!")        


if __name__ == '__main__':
    WorldCLI.script()