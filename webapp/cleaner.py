from subprocess import check_output
from operator import itemgetter
from glob import glob
import shutil
import json

def availdisk():
    
    df = str ( check_output(['df']) ) 
    lines = df.split('\\n')

    header = lines[0].split()
    for index, col in enumerate(header):
        if col.lower().startswith('av'):
            break

    for line in lines:
        if line.startswith('overlay'):
            break
    line = line.split()

    return int(line[index])
    
def list_projects():
    projects = []
    fnames = glob("/output/*/*/*/*/context.json")
    for fname in fnames:
        with open(fname) as f:
            projects.append(json.load(f))
    projects = sorted(projects, key=itemgetter('created_time'), reverse=True)        
    return projects

def cleaner():
    while availdisk() < 250000:
        # Delete oldest project
        projects = list_projects()
        path = projects[-1]['project_path'].replace('project', 'output')
        shutil.rmtree(path)
