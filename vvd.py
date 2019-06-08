#!/usr/local/bin/python

import argparse, os, re, subprocess
from shutil import copyfile


def parseArgs():
    parser = argparse.ArgumentParser(description='VVD for GitHub')
    parser.add_argument('operation', default='run', nargs='?', choices=['run', 'review', 'install', 'diff'], help='The operation to perform')
    parser.add_argument('--file', help='The file to compare if operation is diff')
    return parser.parse_args()


def p(folder = '', file = ''):
    """Return the os path prefixed with the VVD temp directory."""

    temp = 'vvd-temp'
    return os.path.join(temp, folder, file)

def run():
    """Review changes, install dependencies, and diff each changed file."""

    # Review changes in the latest commit. Prepare a list of changed Dynamo and Grasshopper graphs.
    changed = review()

    if(changed):
        print 'These files have been changed', changed

        # Prepare environment and install VVD and its dependencies.
        install()

        # Prepare each file to diff
        for file in changed:
            prepare(file)
    
    else:
        print 'No Dynamo or Grasshopper files have been changed'


def review():
    """Review changes in the latest commit. Prepare a list of changed Dynamo and Grasshopper graphs."""
    
    # Get all files changed in the last commit
    files = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD', 'HEAD~1'])
    files = files.split('\n')
    
    print 'Files changed in last commit:', files
    # files = ['example-1.3.4.dyn', 'example-2.0.2.dyn', 'example.gh', 'foo.json', 'bar.md']
    
    changed = []
    
    # Check if any changed files are Dynamo or Grasshopper files
    for file in files:
        match = re.search('\\.(dyn|gh|ghx)$', file)
        if(match):
            # Add to array of changed files
            changed.append(file)

    print 'Graphs changed in last commit:', changed
    return changed


def install():
    """Prepare the environment, install VVD and its dependencies."""

    print 'Preparing the environment.'

    # Create VVD directories
    if not os.path.exists(p('latest')):
        os.makedirs(p('latest'))
    if not os.path.exists(p('previous')):
        os.makedirs(p('previous'))

    print 'Installing VVD and its dependencies.'

    # Download VVD
    # @todo If this fails then halt
    subprocess.call(['curl', '-LOk', 'https://github.com/StudioLE/VVD/archive/build.zip'])

    # Extract VVD
    # @todo If this fails then halt
    # @todo this doesn't appear to be extracting sub folders?
    subprocess.call(['7z', 'e', 'build.zip', '-o' + p('build'), '-aoa'])

    # Download Graphviz
    # @todo If this fails then halt

    # Download PyGraphviz
    # @todo If this fails then halt


def prepare(file):
    """Prepare the latest and previous versions of the files to be compared."""

    print 'Preparing changes in', file

    # Store paths
    latest = p('latest', file)
    previous = p('previous', file)

    # Copy the latest commit
    copyfile(file, latest)

    # Checkout the previous commit
    subprocess.call(['git', 'checkout', 'HEAD~1', file])

    # Copy the previous commit
    copyfile(file, previous)

    # Reset git 
    subprocess.call(['git', 'reset', 'HEAD', file])
    subprocess.call(['git', 'checkout', '--', file])

    # Compute differences
    # subprocess.call([p('build', 'diffgh.cmd'), previous, latest, previous + '.diff'])
    diff(file, previous, latest)


def diff(file, previous, latest):
    """Create a .diff file comparing the latest and previous graphs."""

    # This function replaces:
    #
    # diffgh.cmd [old_gh_file] [new_gh_file] [gh_diff_file]
    #
    # VVD-GH-To-CG\VVD-GH-To-CG\bin\Debug\VVD-GH-To-CG.exe %1 %TEMP%.\cgA
    # VVD-GH-To-CG\VVD-GH-To-CG\bin\Debug\VVD-GH-To-CG.exe %2 %TEMP%.\cgB
    # python diffgraph.py %TEMP%.\cgA %TEMP%.\cgB %3
    #
    # diffdy.cmd [old_dy_file] [new_dy_file] [dy_diff_file]
    #
    # DynamoToCG\DynamoToCG\bin\Debug\DynamoToCG.exe %1 %TEMP%.\cgA
    # DynamoToCG\DynamoToCG\bin\Debug\DynamoToCG.exe %2 %TEMP%.\cgB
    # python diffgraph.py %TEMP%.\cgA %TEMP%.\cgB %3

    print 'Creating diff of', file
    
    # Get the file extension
    ext = re.search('\\.(dyn|gh|ghx)$', file).group(1)
    print 'File extension:', ext

    if(ext == 'dyn'):
        graphToCG = 'DynamoToCG\\DynamoToCG\\bin\\Debug\\DynamoToCG.exe'
    elif(ext == 'gh'):
        graphToCG = 'VVD-GH-To-CG\\VVD-GH-To-CG\\bin\\Debug\\VVD-GH-To-CG.exe'
    elif(ext == 'ghx'):
        # @todo Does this actually work for GHX?
        graphToCG = 'VVD-GH-To-CG\\VVD-GH-To-CG\\bin\\Debug\\VVD-GH-To-CG.exe'
    else:
        print 'Unsupported file type', file
        return False

    # Convert Graph to Common Graph format
    # @todo This will fail for Dynamo 2.0 graphs
    print graphToCG
    subprocess.call([
        p('build', graphToCG),
        previous,
        previous + '.cgx'
    ])
    subprocess.call([
        p('build', graphToCG),
        latest,
        latest + '.cgx'
    ])

    diff = p('', file + '.diff')
    
    # Create an empty diff file
    # if not os.path.exists(diff):
    #     open(diff, 'w')

    # Create a diff of the two Common Graphs
    # @todo I think this might fail when file contains a path
    subprocess.call([
        'python',
        p('build', 'diffgraph.py'),
        previous + '.cgx',
        latest + '.cgx',
        diff
    ])

    diffToPNG(previous, diff)


def diffToPNG(previous, diff):
    """Create a PNG of the common graph .diff file"""
    
    # vizdiffgh.cmd [gh_file] [gh_diff_file]
    #
    # VVD-GH-To-CG\VVD-GH-To-CG\bin\Debug\VVD-GH-To-CG.exe %1 %TEMP%.\cgA
    # python grapher.py %TEMP%.\cgA %2 %TEMP%.\graph.png
    #
    # vizdiffdy.cmd [dy_file] [dy_diff_file]
    #
    # DynamoToCG\DynamoToCG\bin\Debug\DynamoToCG.exe %1 %TEMP%.\cgA
    # python grapher.py %TEMP%.\cgA %2 %TEMP%.\graph.png

    # Create a PNG of the common graph .diff file comparing it to latest
    subprocess.call([
        'python',
        p('build', 'grapher.py'),
        previous + '.cgx',
        diff,
        diff + '.png'
    ])

def main():

    print 'Starting VVD for GitHub'
    args = parseArgs()

    if(args.operation == 'run'):
        # Review changes, install dependencies, and diff each changed file.
        run()

    elif(args.operation == 'review'):
        # Review changes in the latest commit. return a list of changed Dynamo and Grasshopper graphs.
        review()

    elif(args.operation == 'install'):
        # Prepare environment and install VVD and its dependencies.
        install()
    
    elif(args.operation == 'diff' and not args.file):
        print 'Please specify the file to diff with --file'
        print 'Example: python vvd.py diff --file example.gh'
    
    elif(args.operation == 'diff'):
        # Create a .diff file comparing the latest and previous graphs.
        # diff('example.gh', 'vvd-temp\\previous\\example.gh', 'vvd-temp\\latest\\example.gh')
        # diff('example-1.3.4.dyn', 'vvd-temp\\previous\\example-1.3.4.dyn', 'vvd-temp\\latest\\example-1.3.4.dyn')
        # diff(args.file, 'vvd-temp\\previous\\' + args.file, 'vvd-temp\\latest\\' + args.file)
        prepare(args.file)
    else:
        print 'Please specify a valid operation'

if __name__ == '__main__':
    main()
