import os
import re
import sys

class IllegalArgError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class ParseError(Exception):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return repr(self.value)

# For now, simply prints the given string
# I made it a function in case we want to allow
# a silent run later on
def output(text):
    print text

# Given the name of a file, it will scan the file
# for lines starting with "req" or "del", ignoring
# lines commented with '#', and return two arrays
# containing the lines that followed req and the
# lines that followed del. Prints warnings for 
# any lines that do not meet these criteria, but
# runs anyway
def parse_instructions(instr_path):
    if not os.path.exists(instr_path):
        raise IllegalArgError("Instructions file does not exist: " + instr_path)
    else:
        instr_f = open(instr_path)
        req_files = []
        del_files = []
        line_count = 0
        for line in instr_f:
            line_count += 1
            # Filter out newlines
            line = re.sub("\n", "", line)
            # Filter out comments, but save original live
            raw_line = line
            line = re.sub(r"#.*", "", line)
            # Escape periods
            line = re.sub(r"\.", r"\.", line)
            # Replace wildcards with nearest regex equivalent
            line = re.sub(r"\*", ".*", line)
            line = re.sub(r"\?", ".", line)
            if line:
                m = re.match("^req (.*)", line)
                m2 = re.match("^del (.*)", line)
                if m:
                    req_files.append(m.group(1).strip())
                elif m2:
                    del_files.append(m2.group(1).strip())
                else:
                    output("Parse warning: skipping invalid line " + line_count + " in " + instr_path)
        # Check that no file is both required and deleted
        for del_file in del_files:
            for req_file in req_files:
                for part in req_file.split(","):
                    if part.strip() == del_file:
                        raise ParseError("File both required and deleted: " + part)
        return (req_files, del_files)
                    
def main(instr_path, dir_to_clean):
    # First, get the required files and the files to be deleted
    (req_files, del_files) = parse_instructions(instr_path)
    req_files_found = [False for i in range(len(req_files))]
    unrecognized_files = []
    if not os.path.exists(dir_to_clean):
        raise IllegalArgError("Given directory does not exist: " + dir_to_clean)
    for filename in os.listdir(dir_to_clean):
        deleted = False
        for del_file in del_files:
            if re.match(del_file, filename):
                deleted = True
                try:
                    os.remove(dir_to_clean + "/" + filename)
                except OSError:
                    # If it can't delete for some reason, move on
                    pass
        if not deleted:
            required = False
            for i in range(len(req_files)):
                for part in req_files[i].split(","):
                    part = part.strip()
                    if re.match(part, filename):
                        req_files_found[i] = True
                        required = True
            if not required:
                unrecognized_files.append(filename)
    for filename in unrecognized_files:
        output("Warning: unrecognized file " + filename + " in " + dir_to_clean)
    for i in range(len(req_files)):
        if not req_files_found[i]:
            output("Error: required file " + req_files[i] + " not found in " + dir_to_clean)

            
if __name__ == "__main__":
    if len(sys.argv) < 3:
        output("usage: python clean_folder.py instructions.fi directory/to/clean/")
    else:
        main(sys.argv[1], sys.argv[2])
