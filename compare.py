
#!/usr/bin/env python3
import sys
import os
import csv
import argparse
import json
import codecs
import queue
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor,as_completed
from threading import Thread
import re
#from collections import ChainMap



findings = {}
installer_scripts = []
extracted_obj = {}
extracted_files = {}

                    ###FOLDER###               ####COMPARE_TO####
 # structure  [ {folder:[{fname :{"path":'./asd'}}]}, {folder2:[{fname :{"path":'./asd'}}]}]
all_files = {}


called_by_files = {}
queue_files = queue.Queue()

options = {} # {'FOLDER': 'asdas', 'csv': None, 'folder': 'deas', 'score': 0.7, 'matches': 3, 'force': False, 'json': False, 'in_files': None, 'thread': None}

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s FOLDER",# (-c | -f )",
        description="Compare file names given a csv or folder"
    )
    parser.add_argument('FOLDER')
    parser.add_argument(
        "-v", "--version", action="version",
        version = f"{parser.prog} version '0.2"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c","--csv",
        help='csv file that has the list of filenames to check'
    )
    group.add_argument(
        "-f","--folder",
        help='folder to compare'
    )
    parser.add_argument(
        "-s","--score",
        type=float,
        default=0.7,
        help='minimum score to achieve 0 - 1'
    )
    parser.add_argument(
        "-m","--matches",
        type=int,
        default=3,
        help='top matches'
    )
    parser.add_argument(
        "--force",
        action='store_true',
        help='do not use cached file list'
    )
    parser.add_argument(
        "--obj-in-installers",
        help='given a file with the installers script names, search for DB objects/operation within those script or their children and output obj.csv'
    )
    parser.add_argument(
        "--unique-obj",
        action='store_true',
        help='to be used with --obj-in-installers, outputs unique_obj.csv with only the objects extracted'
    )
    parser.add_argument(
        "-t","--thread",
        help='number of threads to use',
        type=int, default=1
    )
    parser.add_argument(
        "--compare-simple",
        action='store_true',
        help='simple compare, exact filename'
    )
    parser.add_argument(
        "--compare",
        action='store_true',
        help='simple compare + boyer moore compare'
    )
    parser.add_argument(
        "--files-in-file",
        help='search within file for references of files'
    )

    parser.add_argument(
        "--not-in-file",
        action='store_true',
        help='modifier for --files-in-file only output those that are not in the file'
    )

    parser.add_argument(
        "--forms-files",
        action='store_true',
        help='search for Forms files (.fmb)'
    )

    parser.add_argument(
        "--reports-files",
        action='store_true',
        help='search for Report files (.xdrz)'
    )

    parser.add_argument(
        "--proc-files",
        action='store_true',
        help='search for Forms files (.mk/.pc)'
    )

    parser.add_argument(
        "--sh-files",
        action='store_true',
        help='search for Forms files (.sh/ksh)'
    )

    parser.add_argument(
        "--adf-files",
        action='store_true',
        help='search for Forms files (.ear)'
    )




    return parser

#######


############# UTILS ##################
def load_json(fname):  
    dic = None
    try:
        with open('./'+fname,'r') as f:

            dic = json.load(f)                            

        print("loaded json: " + fname) 
        return dic
    except IOError:
        return None

def write_json(fname, dic):
    
    try:
        with open('./'+fname,'w') as f:
            json.dump(dic,f)          

        print("wrote json: " + fname)
                        
        return dic
    except IOError:
        return None

def write_lines_to_csv(lines,path):

    try:
        
        with open(path,'w', newline='') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=';', lineterminator='\n')
            print(f"writing {path}!")
            for line in lines:
                spamwriter.writerow(  line)
        #print("def write_files_from_dir_csv: " + str(len(all_files)))
    except Exception:
        print("write_files_from_dir_csv EXCEPTION: " + sys.exc_info()[0])

def read_lines_from_csv(path):
    lines = []
    try:
        
        with open(path,'r') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=';')
            for row in spamreader:
                #remove empty
                if len(row) > 0:
                    lines += [row]#[[ x for x in row if len(x) > 1]]# all_files[row[0]] = {"path":row[1]}
        print(f'From {path} read: ' + str(len(lines)))
        return lines
    except IOError:
        print(f'{path}: unable to read, does it exist?')
        return None

######################################

####### folder get all files #########

def get_files_from_dir(path) -> dict:
    path_files = {}
    try:
        for root, directories, files in os.walk(path, topdown=False):
            if root.find('.git') == -1:
                
                for name in files:
                    path_files[name.upper()] = {"path":os.path.join(root, name)}
        
        return path_files
    except IOError as ex:
        print(f'FATAL ERROR: {ex}')
        sys.exit()

def write_files_from_dir_csv(path):
    realpath = os.path.realpath(path)
    fname = os.path.basename(realpath) +'.csv'

    lines = [[n,all_files[n]["path"]] for n in all_files]

    write_lines_to_csv(lines,fname)

def read_files_from_dir_csv(path):
    global all_files

    realpath = os.path.realpath(path)
    fname = os.path.basename(realpath) +'.csv'

    lines = read_lines_from_csv(fname)

    if lines:
        all_files =  { r[0]:{"path":r[1]} for r in lines}

    return len(all_files) > 0

########################################

####
def simple_compare():
    keys = list(all_files.keys()) 
    if len(keys) == 2:
        for name in all_files[keys[0]]:
            if name in all_files[keys[1]]:
                #print(os.path.join(root, name))\
                if name in findings: 
                    findings[name]["found"] = True
                    findings[name]["path"] = all_files[keys[0]][name]["path"]
                    if 'path' in all_files[keys[1]][name]:
                        all_files[keys[0]][name]["path2"] = all_files[keys[1]][name]["path"]
    else:
        print('ERROR only 1 dict of files')
        sys.exit()

####
def boyer_moore_compare():
    keys = list(all_files.keys()) 

    file1_components = {}
    for name in all_files['main']:
        comps = [name] + name.split('.')
        file1_components[name] = comps[:] + name.split('_')
        file1_components[name] = [ x.strip() for x in file1_components[name]]

    boyer_moore_compare_task(all_files['main'],file1_components,all_files['optional'])


def boyer_moore_compare_task(files1,files1_component,files2):
    to_check_components = {}

    for name in files2:
        comps = [name] + name.split('.')
        to_check_components[name] = comps[:] + name.split('_')
        to_check_components[name] = [ x.strip() for x in to_check_components[name]]

    #actual compare
    for name in to_check_components:
        if findings[name]["found"] == False:
            for n in to_check_components[name]:
                if len(n) > 0:
                    for fc in files1_components:
                        if n in files1_components[fc]:
                            match = {
                                    "name": fc, 
                                    "path": all_files[0][fc]["path"],
                                    "score": len(n)/len(name)
                                }

                            mm = findings[name]["matches"]

                            if fc in mm:
                                mm[fc]["score"] = mm[fc]["score"] + match["score"]
                            else:
                                mm[fc] = match
    
def trim_score():
    for n in findings:        
        to_remove_matches = []
        for m in findings[n]["matches"]:
            mm = findings[n]["matches"][m]

            #get the items with bad score
            if mm["score"] < options["score"]:
                to_remove_matches = to_remove_matches + [m]

        for r in to_remove_matches:
            findings[n]["matches"].pop(r)

        if len(findings[n]["matches"]) > options["matches"]:
            #keep only top matches
            to_remove_matches = []

            mm = findings[n]["matches"]

            tpls = [(mm[k]["score"],k) for k in mm]
            sorted_tuples = sorted(tpls ) 

            to_remove_matches = sorted_tuples[:-1*options["matches"]]
            sorted_tuples = sorted_tuples[-1*options["matches"]:]
            
            mm = {v:mm[v] for k, v in sorted_tuples}
            findings[n]["matches"] = mm
####


############# Extract from Files ############

def extract_file_from_line(line,pre_file_char='') -> list:
    regex_str = pre_file_char + r'([\w\./]+\.[a-z]+)'
    regex_match = re.compile(regex_str,re.IGNORECASE)
    found = regex_match.search(line)
    if found:
        reg_capture = found.groups()
        fname = os.path.basename(reg_capture[0])
        
        return [{fname.upper():fname}]
    return None

def extract_file_with_space_from_line(line,pre_file_char='') -> list:
    regex_str = pre_file_char + r'([\w\./\s]+\.[a-z]+)'
    regex_match = re.compile(regex_str,re.IGNORECASE)
    found = regex_match.search(line)
    if found:
        reg_capture = found.groups()
        fname = os.path.basename(reg_capture[0])
        
        return [{fname.upper():fname}]
    return None

def extract_objects_from_line(line) -> list:
    regex_match = re.compile(r'^\s*(?P<oper>(?:MERGE)|(?:UPDATE(?!\s+SET\s+)(?![\s\w]+\.\s+))|(?:DELETE(?!\s+WHERE))|(?:INSERT(?=\s+INTO\s))|(?:ALTER)|(?:DROP(?!\s*COLUMN))|(?:CREATE(?:\s+OR\s+REPLACE)?))\s+(?:\b(?:UNIQUE)|(?:FORCE)|(?:PUBLIC)|(?:COLUMN)|(?:GLOBAL\s+TEMPORARY)|(?:MATERIALIZED))?(?:\s*EDITIONABLE)?\s*(?!OR)(?P<dbtype>\w+)\s+(?:BODY\s+)?(?:\"?\w+\"?\.\"?)?\"?(?P<obj>\w+)(?:\"|\s|$)(?!@)', re.IGNORECASE)
    #regex_match = re.compile(r'^\s*((?:UPDATE)|(?:DELETE)|(?:INSERT)|(?:ALTER)|(?:DROP(?!\s*COLUMN))|(?:CREATE OR REPLACE)|(?:CREATE))\s+(?:\b(?:UNIQUE)|(?:FORCE)|(?:PUBLIC)|(?:COLUMN)|(?:GLOBAL TEMPORARY)|(?:MATERIALIZED))?(?:\s*EDITIONABLE)?\s*(?!OR)(\w+)\s+(?:BODY\s+)?([\w\"\.]+)', re.IGNORECASE)
    found = regex_match.search(line)
    if found:
        grps = [x.upper() for x in found.groups()]

        if len(grps) == 3:        
            #update and delete have an error OBJ_TYPE is the OBJ_NAME and OBJ_NAME should be garbage
            if grps[0] == 'UPDATE':
                grps[2] = grps[1]
            elif grps[0] == 'DELETE':
                if grps[1] != 'FROM':
                    grps[2] = grps[1]

        return [grps + [line]]
                
    return None


def extract_from_file(file, regex_funcs = [], args = []) -> list:
    ngroups = [ [] for x in regex_funcs]
    fname = os.path.basename(file).upper()
    
    if len(args) == 0:
        args = [[] for x in regex_funcs]

    try:
        with codecs.open(file, mode='r', encoding='utf_8', errors='ignore', buffering=-1) as f:

            for line in f.readlines():
                i = 0
                for reg in regex_funcs:
                    extr = None
                    if len(args[i]) > 0:
                        extr = reg(line,*args[i])
                    else:    
                        extr = reg(line)
                    if extr:

                        if not ngroups[i]:
                            ngroups[i] = {fname:[]}

                        if not ngroups[i][fname]:
                            ngroups[i][fname] = []
                            
                        ngroups[i][fname] += extr

                    i+=1

        return ngroups
    except IOError:
        return []



def from_queue_extract_from_file() :
    while True:
    
        new_files = []


        fname = queue_files.get()

        if fname:
            fname = fname.upper()

        if fname in all_files['main']:
            path = all_files['main'][fname]["path"]

            if fname not in extracted_files:
                ex = extract_from_file(path,regex_funcs= [extract_file_from_line,extract_objects_from_line],args=[['@'],[]])

                #extract files
                if ex[0] and ex[0][fname]:
                    flat = {}
                    if len(ex[0][fname]) > 1:
                        flat = {k:x[k] for x in ex[0][fname] for k in x } #ex[0][fname] = [{'':''},...]

                    new_files += {x for x in flat}

                    extracted_files[fname] = flat

                #extract objects



                if ex[1] and ex[1][fname]:

                #if obj type: 'PACKAGE' 'PROCEDURE'  'FUNCTION'  TABLE' 'TRIGGER'
                #  ignore objects within
                    obj = []
                    for arr in ex[1][fname]:
                        if arr[0] not in ['DROP','ALTER'] and arr[1] in ['PACKAGE','PROCEDURE','FUNCTION','TRIGGER']:
                            obj = [arr]
                            break
                        else:
                            obj += [arr]

                    if fname in extracted_obj:
                        extracted_obj[fname] += obj   
                    else:
                        extracted_obj[fname] = obj

        #if there are more files to extract from add to queue

        queue_files.task_done()

        if len(new_files) > 0:
            for f in new_files:
                queue_files.put_nowait(f)

def load_from_installers():

    for f in installer_scripts:
        queue_files.put_nowait(*f)

    #IO is best done through threads
    
    for i in range(options['thread']):
        worker = Thread(target=from_queue_extract_from_file )
        worker.setDaemon(True)
        worker.start()

    queue_files.join()



def write_objs_to_file_csv(output_file):
    ## create lines
    ## Object Name;Object Type;Install Script;Script Name
    
    #{file:{obj_name: line}} -> 1 opertype per obj; if file called more than once append to Install Script
    file_obj_lines = {}
    file_called_tree = {}
    lines = []
    csv_obj_type = {
        'PACKAGE'    : ['DDL',1], # if creating a package, ignore everything else
        'PROCEDURE'  : ['DDL',1], # if creating a PROCEDURE, ignore everything else
        'FUNCTION'   : ['DDL',1], # if creating a FUNCTION, ignore everything else
        'TABLE'      : ['DML',2],
        'SYNONYM'    : ['DDL',3],
        'INDEX'      : ['DDL',3],
        'TRIGGER'    : ['DDL',3],
        'CONSTRAINT' : ['DDL',3],
        'VIEW'       : ['DDL',2],
        'SEQUENCE'   : ['DDL',3],
        'DIRECTORY'  : ['DCL',3],
        'CONTEXT'    : ['DCL',3],
        'ROLE'       : ['DCL',3],
        'USER'       : ['DCL',3]
        }

    oper_priority = {
        'CREATE OR REPLACE' : 1,
        'CREATE'            : 1,
        'DROP'              : 3,
        'ALTER'             : 2,
        'INSERT'            : 2,
        'UPDATE'            : 3,
        'DELETE'            : 3,
        'MERGE'             : 2
    }

    for f in extracted_obj: #file key
        install_script = f

        ############
        ### get most top level installers (can be more than one)
        ############
        current_to = [f]
        while_continue =True
        while(while_continue):
            
            new = []
            for scr in extracted_files:
                for c in current_to:
                    if c in extracted_files[scr]:
                        new += [scr]
            

            while_continue = False
            for fi in current_to:
                if fi not in install_script:
                    while_continue = True
                    break

            if while_continue and current_to == new:
                print(f'ERROR Script {f} has no to level installers...')
                break
            elif len(new) > 0:
                current_to = new
            
        install_script = '/'.join(current_to)
        

        #########
        #extract objects to lines
        ###########
    
        #using this dict I can remove duplicate entries ex: "create package body x" and "create package x"
        to_write_obj = {}
        #obj_arr = ['DROP', 'PACKAGE', 'MMR_VALIDATION_RESA_SALES','DROP PACKAGE MMR_VALIDATION_RESA_SALES;\n']
        for obj_arr in extracted_obj[f]:
            oper, obj_type, obj_name, line  = [ x.upper() for x in obj_arr]
            script_name = f
            obj_name = obj_name.replace('"','')


            db_obj_oper_type = csv_obj_type.get(obj_type,'ERROR')
            oper_priority_val = oper_priority.get(oper,4)


            if db_obj_oper_type == 'ERROR':

                db_obj_oper_type = csv_obj_type.get('TABLE')
                
            obj_type = db_obj_oper_type[0]
            
            arr = [db_obj_oper_type[1],oper_priority_val,obj_name,obj_type,install_script,f]

            if obj_name not in to_write_obj:                
                to_write_obj[obj_name] = arr 
            
            elif db_obj_oper_type[1] == 1:                 
                #if this is file is a create package, function or procedure
                #  we need to ignore the rest of the operations done in code
                to_write_obj = { obj_name: arr }
                break

            
            elif to_write_obj[obj_name][0] > db_obj_oper_type[1]:                    
                to_write_obj[obj_name] = arr 

                #same obj_oper_priority but operation priority differs
            elif to_write_obj[obj_name][0] == db_obj_oper_type[1] and to_write_obj[obj_name][1] > oper_priority_val:                
                to_write_obj[obj_name] = arr 


        if len(to_write_obj)>0: 
            lines += [ to_write_obj[j][2:] for j in to_write_obj]

    write_lines_to_csv(lines,output_file)

def write_unique_objs_csv(output_file):
    csv_obj_type = ['PACKAGE','PROCEDURE','FUNCTION','TABLE','SYNONYM','INDEX',
                    'TRIGGER','VIEW','SEQUENCE']
    remove_obj_type = ['CONSTRAINT','DIRECTORY','CONTEXT',
                    'ROLE','USER']
    objs = {}
    for f in extracted_obj:
        for o in extracted_obj[f]:
            if o[2] not in objs and o[1] not in remove_obj_type:
                ob_type = o[1]
                if ob_type not in csv_obj_type:
                    ob_type = 'TABLE'

                objs[o[2]] = [o[2],ob_type]

    write_lines_to_csv(objs.values(), output_file)

def search_in_installers(unique=False):
    global extracted_obj
    global extracted_files

    if not extracted_obj or not extracted_files:
        load_from_installers()
        write_json('extracted.json',extracted_obj)
        write_json('extracted_files.json',extracted_files)

    write_objs_to_file_csv('obj.csv')
    if unique:
        write_unique_objs_csv('unique_obj.csv')


###############################################


############## File Types ##############
        
def search_file_types(regex,to_file=None,append_for_csv = [],limit_path=None,in_rn=False) -> list:
    match = re.compile(regex,re.IGNORECASE)

    found = []

    for f in all_files['main']:
        if limit_path:
            if all_files['main'][f]['path'].find(limit_path) < 0:
                continue

        groups = match.search(f) 
        if groups:
            ficheiro = os.path.basename(all_files['main'][f]['path'])

            if in_rn:
                if 'in_rn' in all_files['main'][f] and all_files['main'][f]['in_rn']:
                    found += [[ficheiro]+append_for_csv]
            else:
                if 'in_rn' not in all_files['main'][f] or not all_files['main'][f]['in_rn']:
                    found += [[ficheiro]+append_for_csv]

    if to_file:
        write_lines_to_csv(found,to_file)

    return found

#############################

#options =  {'FOLDER': None, 'csv': None, 'folder': None, 'score': 0.7, 'matches': 3, 'force': False, 'json': False, 'in_files': None, 'thread': None}

def option_folder(path):    
    files = None

    realpath = os.path.realpath(path)

    fname = os.path.basename(realpath)
    fname = fname.upper()

    if not options['force']:
        print('loading cache json')
        files = load_json(f'{fname}.json')

    if not files:
        print("Gathering Files from: " + path)
        files = get_files_from_dir(path)
        write_json(f'{fname}.json',files)

    return files


def option_folders():
    global all_files
    folders = {}

    print('load folder(s)')

    #if there is a need for both folder better to use threads
    if options['FOLDER'] and options['folder'] and options['thread'] > 1:
        data = []
        #IO is best done through threads
        #with ThreadPoolExecutor(max_workers=options["thread"]) as executor:
        with ThreadPoolExecutor(max_workers=2) as executor:
            jobs = [executor.submit(option_folder,options['FOLDER']),
                    executor.submit(option_folder,options['folder'])]
            for job in as_completed(jobs):
                #fname = jobs[job]
                try:
                    data += [job.result()]
                except Exception as exc:
                    print('FATAL ERROR: generated an exception: %s' % ( exc))
                    sys.exit()
                else:
                    print('folder loaded')                    
        
        folders['main'] = data[0]
        folders['optional'] = data[1]


    elif options['FOLDER']:
        folders['main'] = option_folder(options['FOLDER'])

        if options['folder']:
            folders['optional'] = option_folder(options['folder'])
    
    all_files = folders


def option_csv():
    global all_files

    if(options['csv']):
                
        print('load csv')                

        lines = read_lines_from_csv(options['csv'])

        all_files['optional'] = lines


def option_compare():
    #with concurrent.futures.ProcessPoolExecutor() as executor:
    #    for number, prime in zip(PRIMES, executor.map(is_prime, PRIMES)):
    #        print('%d is prime: %s' % (number, prime))


    if options['compare_simple'] or options['compare']:
        print('simple compare')
        simple_compare()

    if options['compare']:
        print('boyer_moore_compare')
        boyer_moore_compare()
        trim_score()
    if options['compare_simple'] or options['compare']:
        write_json('findings.json',findings)


def option_obj_in_installers():
    global installer_scripts

    if options['obj_in_installers']:
        installer_scripts = read_lines_from_csv(options['obj_in_installers'])
        search_in_installers(unique=options['unique_obj'])


def option_files_in_file():
    files = []
    file_extensions = ['FMB','XDRZ','MK','PC','EAR','SH','KSH']

    if options['files_in_file']:
        files = extract_from_file(options['files_in_file'],regex_funcs= [extract_file_with_space_from_line])
        # from [{file:[{file1:file1},{file2:file2}]}] to {file1:file1,file2:file2}
        if len(files) == 1:
            files = {f:y[f] for x in files[0] for y in files[0][x] for f in y }

            by_ext = {x:re.sub(r'.+\.',r'',x) for x in files}
            
            
            filtered = { x:files[x] for x in by_ext if by_ext[x] in file_extensions}

            all_files_ext = {x:all_files['main'][x] for x in all_files['main'] if re.sub(r'.+\.',r'',x) in file_extensions}


            for x in all_files_ext:
                for y in filtered:
                    if x in y:
                        all_files_ext[x]['in_rn'] = True
                        all_files['main'][x]['in_rn'] = True

            write_json('all_files_ext.json', all_files_ext)

            #write_json('files_in_file.json', files)


def option_file_types():        
    in_rn = not options["not_in_file"]
    found = []

    if options["proc_files"]:
        print("search for files: PROC")
        found += search_file_types(r'\w+\.(mk|pc)$',append_for_csv = ['ProC'],in_rn=in_rn)


    if options["forms_files"]:
        print("search for files: FORMS")
        found += search_file_types(r'\w+\.fmb$',append_for_csv = ['Forms'],in_rn=in_rn)

    if options["reports_files"]:
        print("search for files: REPORTS")
        found += search_file_types(r'\w+\.xdrz$',append_for_csv = ['Reports'],in_rn=in_rn)

    if options["sh_files"]:
        print("search for files: shell script")
        found += search_file_types(r'\w+\.(sh|ksh)$',append_for_csv = ['Shell script extension'],in_rn=in_rn)

    if options["adf_files"]:
        print("search for files: ADF")
        found += search_file_types(r'\w+\.ear$',append_for_csv = ['ADF'],in_rn=in_rn)

    if len(found) > 0:
        write_lines_to_csv(found,'binary_files.csv')

def main():    

    option_folders()
        
    option_csv()

    option_compare()

    option_obj_in_installers()

    option_files_in_file()

    option_file_types()

    
    # print("simple_compare") 
    # simple_compare()

    # if not options['simple']:
    #     print("boyer_moore_compare")
    #     boyer_moore_compare()

    #     print("trim_score")
    #     trim_score()

    # if options['in_files']:
    #     search_in_files()


    # print("write findings to findings.json")
    # write_json(findings,'findings.json')
    
    # print('writing csv')
    # write_findings_to_csv()

if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()

    options = vars(args)

    main()


