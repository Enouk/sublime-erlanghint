import sublime, sublime_plugin, subprocess, re, os, tempfile

ERLHINT_PLUGIN_FOLDER = os.path.dirname(os.path.realpath(__file__))
SETTINGS_FILE = "erlanghint.sublime-settings"

class ErlangHintEventListener(sublime_plugin.EventListener):
    @staticmethod
    def on_post_save(view): 
        if (view.file_name().endswith(".erl")):
            view.window().run_command("erlang_hint")

class ErlangHintCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        filename = self.view.file_name()
        filedir = os.path.dirname(filename)
        if ".erl" not in filename:
            print("No erl file skipping")
            return
           
        # Set deps in ERL_LIBS
        env = {}
        env.update(os.environ)
        deps = filedir + "/../../../deps" 
        env['ERL_LIBS'] = deps

        include_dir = filedir + "/../include"
        outdir = tempfile.gettempdir()
        cmd = ["erlc", "-I", include_dir, "-o", outdir, filename]
        out = self.exec_cmd(cmd, env)

        poutput = self.process_output(out)
        (warnings, errors) = self.create_regions(poutput)
        self.highlight_file(warnings, errors)
        self.print_status(warnings, errors)

    def create_regions(self, output):
        print(output)
        warnings = [self.create_warning_region(x) for x in output if "Warning" in x[2]]
        errors = [self.create_error_region(x) for x in output if "Warning" not in x[2]]
        return (warnings, errors)

    def create_warning_region(self, warning):
        [fileName, line, msg] = warning
        textPoint = self.view.text_point(int(line)-1, 0)

        if "this expression will fail with a 'badarith'" in msg:
            return [sublime.Region(textPoint, textPoint)]

        match = re.search("variable [']([^']+)'", msg)
        if match:
            return [self.view.find(match.group(1), textPoint)]
        
        match = re.search("function ([a-z_]+)", msg)
        if match:
            return [self.view.find(match.group(1), textPoint)]
        
        match = re.search("Warning: no clause will ever match", msg)
        if match:
            return [sublime.Region(textPoint, textPoint)]

        return [sublime.Region(textPoint, textPoint)]

    def create_error_region(self, warning):
        [fileName, line, msg] = warning
        textPoint = self.view.text_point(int(line)-1, 0)
        match = re.search("syntax error before: ([\w]+)", msg)
        if match:
            regions = []
            regions.append(sublime.Region(textPoint-1, textPoint-1))
            regions.append(self.view.find(match.group(1), textPoint))
            return regions

        match = re.search("unterminated string starting with \"([^[\"]{1})", msg)
        if match:
            return [self.view.find(match.group(1), textPoint)]

        match = re.search("[']([^']+)'", msg)
        if match:
            return [self.view.find(match.group(1), textPoint)]

        match = re.search("function ([\w]+)", msg)
        if match:
            return [self.view.find(match.group(1), textPoint)]

        return [sublime.Region(textPoint, textPoint)]

    def highlight_file(self, warnings, errors):
        warnings = [x for x in warnings if x ]
        warnings = [item for sublist in warnings for item in sublist]

        errors = [x for x in errors if x ]
        errors = [item for sublist in errors for item in sublist]
        print("Warnings", warnings)
        print("Errors", errors)
        #region = self.view.find("BBBB", 0)
        #print(region)
        #self.view.add_regions("Erl", regions, "comment", 0)
        #icon = "Packages/sublime-wrangler/icons/warning.png"
        self.view.add_regions("erlhint_warnings", warnings, "string", "dot",
        sublime.DRAW_EMPTY |
        sublime.DRAW_NO_FILL |
        sublime.DRAW_NO_OUTLINE |
        sublime.DRAW_SQUIGGLY_UNDERLINE |
        sublime.HIDE_ON_MINIMAP)

        self.view.add_regions("erlhint_errors", errors, "keyword", "dot",
        sublime.DRAW_EMPTY |
        sublime.DRAW_NO_FILL |
        sublime.DRAW_NO_OUTLINE |
        sublime.DRAW_SQUIGGLY_UNDERLINE |
        sublime.HIDE_ON_MINIMAP)

    def print_status(self, warnings, errors):
        # TODO add status update here
        if len(warnings) == 0 and len(errors) == 0:
            self.view.set_status("erlanghint", "")        
        else:
            self.view.set_status("erlanghint", "Warnings:{0} Error:{1}".format(len(warnings), len(errors)))

    def process_output(self, output):
        print("process_output: ")
        output = output.decode("utf-8").replace("c:/", "/")
        List = [re.split("^([^:]+):(?:([0-9]+):)?(?:([0-9]+):)? (.*)", s) for s in output.splitlines()]
        List = [ [x for x in l if x] for l in List]
        return List

    def exec_cmd(self, cmd, env):
        print(cmd)
        p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True, env=env)
        (out, stderr) = p.communicate()
        print(out, stderr)
        return out