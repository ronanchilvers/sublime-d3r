# Simple class to allow running some common D3R core tools from within ST3
# Author: Ronan Chilvers 2013
# License: GPL V2 - http://www.gnu.org/licenses/gpl-2.0.html
#
import sublime
import sublime_plugin
import threading
import subprocess
import os

class SublimeD3rCommand(sublime_plugin.WindowCommand):

    options = ['Update DB', 'Run Queue']
    commands = ['update_db', 'run_queue']
    base = False

    def run(self):
        self.base = self.find_base_directory()
        if False == self.base:
            sublime.error_message('Project doesn\'t seem to be a core project')
            return
        self.window.show_quick_panel(self.options, self.on_done)

    def on_done(self, idx):
        if -1 < idx and False != self.base:
            command = self.commands[idx]
            func = getattr(self, command)
            func()

    def update_db(self):
        sublime.status_message('Updating db for base path ' + self.base)
        DBThread(self.base, self.log_output).start()

    def run_queue(self):
        sublime.status_message('Running local queue for base path ' + self.base)
        RunQueueThread(self.base, self.log_output).start()

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

    def find_base_directory(self, rootDir = False):
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
        return self.find_base_directory(root)

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
