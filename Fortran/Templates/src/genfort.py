#!/prod/anaconda3/bin/python

import sys
import os
import random
import string

import re
import subprocess


class Template:
    def __init__(self, name, types, text):
        self.name = name
        self.types = types
        self.text = text
        self.forms = []
        
    def add_form(self, form):
        if len(form) != len(self.types):
            print("Error: Invalid template call")
            sys.exit()
        if form not in self.forms:
            self.forms.append(form)


def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def find_function(gimports, target):
    template_start = re.compile(
        r"template type ((?:\w,?\s?)*) function (\w+)",
        re.IGNORECASE
    )
    template_end = re.compile(
        r"end\s*template",
        re.IGNORECASE
    )
    
    target = target.upper()
    
    for gfilename in gimports:
        with open(gfilename, "r") as gfile:
            in_template = False
            function = None
            types = None
            text = None
            
            for line in gfile:
                m = re.match(template_end, line)
                if m is not None:
                    in_template = False
                    if function == target:
                        return Template(function, types, text)
                    
                if in_template:
                    text += line

                m = re.match(template_start, line)
                if m is not None:
                    types, function = m.groups()
                    function = function.upper()
                    types = [t.strip() for t in types.split(",")]
                    in_template = True
                    text = ""
                


function_call = re.compile(r"(\w+)@((.*?)*)@")

compiler = "gfortran"


try:
    ifilename = sys.argv[1]
except KeyError:
    print("usage: parser <file>")
    sys.exit()
    
try:
    args = sys.argv[2:]
except KeyError:
    args = []

stub, ext = os.path.splitext(ifilename)
ext = ext.replace("g","")
ident = get_random_string(8)
ofilename = stub + "_" + ident + ext

gimports = []
templates = {}

body = []
use_added = False
with open(ifilename, "r") as ifile:
    for line in ifile:
        line = line.strip()
        if "@GIMPORT" in line.upper():
            gimports.append(line.split()[1])
            if not use_added:
                use_added = True
                line = "use {}".format(ident)
            else:
                line = ""
        elif "@" in line:
            match = re.finditer(function_call, line)
            if match is not None:
                replacements = []
                for m in match:
                    function, form, dummy = m.groups()
                    function = function.upper()
                    form = [f.strip() for f in form.upper().split(",")]
                    if function not in templates.keys():
                        print("Searching for function: {}".format(function))
                        f = find_function(gimports, function)
                        if f is None:
                            print("Error: Not found")
                            sys.exit()
                        templates[f.name] = f
                        
                    templates[function].add_form(form)
                    form_text = "_".join(form)
                    form_text = form_text.replace("(", "_")
                    form_text = form_text.replace(")", "_")
                    form_text = form_text.replace("=", "_")
                    specific = "{}##{}".format(function, form_text)
                    line = line[:m.start()] + specific + line[m.end():]
        body.append(line.replace("##", "_{}_".format(ident)) + "\n")
                    

functions = []
for t in templates.keys():
    template = templates[t]
    
    for forms in template.forms:
        form_text = "_".join(forms)
        form_text = form_text.replace("(", "_")
        form_text = form_text.replace(")", "_")
        form_text = form_text.replace("=", "_")
        text = template.text.replace(
            "%N", "{}_{}_{}".format(template.name, ident, form_text)
        )
        for i in range(len(forms)):
            text = text.replace("@{}@".format(template.types[i]), forms[i])
        
        functions.append(text)
        
        
with open(ofilename, "w") as ofile:
    ofile.write("module {}\nuse ISO_FORTRAN_ENV\ncontains\n".format(ident))
    for f in functions:
        ofile.write(f)
    ofile.write("end module {}\n\n\n".format(ident))
        
    for b in body:
        ofile.write(b)
        
        
args.append(ofilename)
args.insert(0, compiler)

result = subprocess.run(args, capture_output=True)
print(result)

print(args)