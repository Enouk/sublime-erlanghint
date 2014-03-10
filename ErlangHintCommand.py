import sublime, sublime_plugin, subprocess, re

class ErlangHintEventListener(sublime_plugin.EventListener):  
    @staticmethod
    def on_post_save(view): 
        if (view.file_name().endswith(".erl")):
            print(view.file_name(), "Erlang file saved performing hint")
            view.window().run_command("erlang_hint")

class ErlangHintCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        filename = self.view.file_name()
        if ".erl" not in filename:
            print("No erl file skipping")
            return
            
        include_dir = "../include"
        out_dir = "../ebin"
        cmd = ["erlc", "-I", include_dir, filename]
        out = self.exec_cmd(cmd)

        # p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        # (out, stderr) = p.communicate()
        #print(out, stderr)
        poutput = self.process_output(out)
        (warnings, errors) = self.create_regions(poutput)
        self.highlight_file(warnings, errors)

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
            print(match.group(1))
            print(textPoint)
            return [self.view.find(match.group(1), textPoint)]
        
        match = re.search("function ([a-z]+)", msg)
        if match:
            print(match.group(1))
            print(textPoint)
            return [self.view.find(match.group(1), textPoint)]
        
        match = re.search("Warning: no clause will ever match", msg)
        if match:
            return [sublime.Region(textPoint, textPoint)]

        return [sublime.Region(textPoint, textPoint)]

    def create_error_region(self, warning):
        regions = []
        [fileName, line, msg] = warning
        textPoint = self.view.text_point(int(line)-1, 0)
        match = re.search("syntax error before: ([\w]+)", msg)
        if match:
            print(match.group(1))
            print(textPoint)
            regions.append(sublime.Region(textPoint-1, textPoint-1))
            regions.append(self.view.find(match.group(1), textPoint))

        match = re.search("unterminated string starting with \"([^[\"]{1})", msg)
        if match:
            print(match.group(1))
            print(textPoint)
            regions.append(self.view.find(match.group(1), textPoint))            

        match = re.search("[']([^']+)'", msg)
        if match:
            print(match.group(1))
            print(textPoint)
            regions.append(self.view.find(match.group(1), textPoint)) 

        return [sublime.Region(textPoint, textPoint)]

    def highlight_file(self, warnings, errors):
        warnings = [x for x in warnings if x ]
        warnings = [item for sublist in warnings for item in sublist]

        errors = [x for x in errors if x ]
        errors = [item for sublist in errors for item in sublist]
        print(warnings)
        print(errors)
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

    def process_output(self, output):
        print("process_output: ")
        output = output.decode("utf-8").replace("c:/", "/")
        List = [re.split("^([^:]+):(?:([0-9]+):)?(?:([0-9]+):)? (.*)", s) for s in output.splitlines()]
        List = [ [x for x in l if x] for l in List]
        return List

    def exec_cmd(self, cmd):
        p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        (out, stderr) = p.communicate()
        print(out, stderr)
        return out