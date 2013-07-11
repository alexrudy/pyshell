# PyShell: Command Line Tools in Python

This distribution, which consists solely of the `pyshell` module, is my attempt to port more complex `bash` scripts into python. Mostly, it has become a proving ground for my pythonic shell scripting architecutre. The documentation is on [Github Pages](http://alexrudy.github.com/pyshell/).

## Installation

To install this module, download it, and then change into the base directory (the first pyshell directory), then install it with the standard python distutils installation script:
	
	$ cd path/to/pyshell
	$ sudo python setup.py install
	

This will provide the `pyshell` module which contains both `config` and `base`, useful modules for your code in general. It also installs the `BackUp` script and the `PyPackage` script. Each is a command line tool for performing a basic task.

## `BackUp` Shell Script

The `BackUp` script is used to create backups of entire directories or volumes using RSYNC. The idea behind BackUp is that you configure it once, then use one of your configured commands to BackUp your files. It should turn this:
	
	$ rsync -av /path/to/original/somewhere /path/to/backup/somewhere
	
into:
	
	$ BackUp somewhere
	

And lets you forget about the paths you set as `BackUp` destinations. To configure the `BackUp` script, provide a YAML file similar to `examples/Backup.yml`.

## `PyPackage` Shell Script

This script is a first pass at a basic distribution creation script. It walks the user through the creation of the files necessary for a basic python distribution. Currently, only the `dist` subcommand is available to create distributions. Use it like:
	
	$ PyPackage dist somename
	
Where you'd like to create a module called `somename` in a python distribution in the current directory.

## Modules

Two useful modules are provided. The `config` module provides a sturcture which broadly represents a nested dictionary similar to a YAML file. The `base` module provides a base class for shell scripts and is used as the base of the `BackUp` and `PyPackage` script. The architecture of the `BackUp` script (in `pyshell/backup.py`) is the cleanest, so examine that first. 