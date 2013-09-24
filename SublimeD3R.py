# Simple class to allow running some common D3R core tools from within ST3
# Author: Ronan Chilvers 2013
# License: GPL V2 - http://www.gnu.org/licenses/gpl-2.0.html
#
import sublime
import sublime_plugin
import threading
import subprocess
import os

def find_base_directory(rootDir = False):
    debug = True
    if False == rootDir:
        debug = False
        rootDir = sublime.active_window().active_view().file_name()

    root = os.path.abspath(os.path.join(rootDir, os.pardir))

    for dirname in os.listdir(root):
        if "." == dirname or ".." == dirname:
            continue
        if "home" == dirname:
            return False
        if "/" == dirname:
            return False
        if "core" == dirname:
            return root
    return find_base_directory(root)


class SublimeD3rCommand(sublime_plugin.WindowCommand):

    options = ['Update DB', 'Run Queue', 'New Model' ]
    commands = ['update_db', 'run_queue', 'new_model' ]
    base = False

    def run(self):
        self.base = find_base_directory()
        # if False == self.base:
        #     sublime.error_message('Project doesn\'t seem to be a core project')
        #     return
        self.window.show_quick_panel(self.options, self.on_done)

    def on_done(self, idx):
        #if -1 < idx and False != self.base:
        if -1 < idx:
            command = self.commands[idx]
            print('running command : ' + command)
            func = getattr(self, command)
            func()

    def update_db(self):
        sublime.status_message('Updating db for base path ' + self.base)
        DBThread(self.base, self.log_output).start()

    def run_queue(self):
        sublime.status_message('Running local queue for base path ' + self.base)
        RunQueueThread(self.base, self.log_output).start()

    def new_model(self):
        sublime.status_message('Creating new model')
        self.window.run_command('sublime_d3r_new_model')

    def log_output(self, message):
        print("status is : " + str(message[0]))
        if 0 == message[0]:
            sublime.status_message('Command completed ok')
        else:
            sublime.error_message('Command had errors')
        self._output_to_view(message[1])

    def _output_to_view(self, message):
        msg = sublime.active_window().new_file()
        msg.set_scratch(True) # Don't mark as dirty - handy trick!
        msg.set_name("D3R_OUTPUT")
        msg.run_command('output_result', { "message": message })


class SublimeD3rNewModelCommand(sublime_plugin.WindowCommand):
    def run(self):
        win = self.window
        win.show_input_panel("Model name", "", self.on_done, None, None)

    def on_done(self, name):
        writer = ModelWriterPhp()
        writer.write(name)
        xmlwriter = ModelWriterXml()
        xmlwriter.write(name)



class FileWriter():
    def write(self, name):
        name = self.normalise_name(name)
        tpl = self.replace_tags(self.template(), name)
        # print("template : " + tpl)
        path = self.get_path(name)
        # print("path : " + path)
        if (False == self.write_file(path, tpl)):
            print("Unable to write file")
        else:
            print("File written ok")
        
    def write_file(self, path, tpl):
        if os.path.exists(path):
            print("path already exists : " + path)
            return False
        return open(path, "w+").write(tpl)

    def normalise_name(self, name):
        return name

    def replace_tags(self, tpl):
        return tpl

    def get_module_name(self, name):
        parts = name.partition('_')
        return parts[0]

    def get_path(self, name):
        return false

    def template(self):
        return None

class ModelWriter(FileWriter):
    extension = False

    def normalise_name(self, name):
        return name.lower().title()

    def replace_tags(self, tpl, name):
        parts  = name.partition('_')
        module = parts[0].capitalize()
        model  = parts[2][0].upper() + parts[2][1:]
        name   = module + '_' + model
        edits  = [ (':NAME:', name), (':TABLE_NAME:', name.lower()), (':ITEM_NAME:', model.lower()) ]
        for tag,val in edits:
            tpl = tpl.replace(tag, val)
        return tpl

    def get_path(self,name):
        basedir = find_base_directory()
        module = self.get_module_name(name)
        # print("basedir : " + basedir)
        # print("module : " + module)
        # print("name : " + name)
        path = os.path.join(basedir, 'modules', module, 'models', name + "." + self.get_extension())
        return path

    def get_extension(self):
        return self.extension

class ModelWriterPhp(ModelWriter):
    extension = "php"

    def template(self):
        return """\
<?php

class :NAME: extends D3R_Model 
{
    protected $_tableName = ':TABLE_NAME:';
    protected $_itemName  = ':ITEM_NAME:';
}

"""

class ModelWriterXml(ModelWriter):
    extension = "xml"

    def template(self):
        return """\
<?xml version='1.0' encoding='UTF-8'?>

<!-- XML Definition for :NAME: -->

<fields>

    <field>
        <name>Created</name>
        <dbname>created</dbname>
        <type>DateTime</type>
        <default>now</default>
        <required>False</required>
        <listing>False</listing>
    </field>
    <field>
        <name>Updated</name>
        <dbname>updated</dbname>
        <type>Updated</type>
        <required>False</required>
        <listing>False</listing>
    </field>
</fields>
"""



class OutputResultCommand(sublime_plugin.TextCommand):
    def run(self, edit, message):
        self.view.insert(edit, 0, message)

class BaseThread(threading.Thread):
    base = False
    callback = False

    def __init__(self, base, callback):
        self.base = base
        self.callback = callback
        threading.Thread.__init__(self)

    def get_command(self):
        return False

    def run(self):
        if False != self.base:
            core_command = self.get_command()
            print("core_command : " + core_command)
            if False == core_command:
                return

            command = '/usr/bin/env php ' + os.path.join(self.base, core_command + ' local')
            print("command : " + command)
            result  = subprocess.getstatusoutput(command)

            if False != self.callback:
                self.callback(result)

class DBThread(BaseThread):
    def get_command(self):
        return 'core/tools/update_db.php'

class RunQueueThread(BaseThread):
    def get_command(self):
        return 'core/tools/run_queue.php'
