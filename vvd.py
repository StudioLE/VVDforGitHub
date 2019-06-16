#!/usr/local/bin/python

import argparse, os, re, subprocess, sys
from shutil import copyfile


def parseArgs():
    parser = argparse.ArgumentParser(description='VVD for GitHub')
    parser.add_argument('operation', default='run', nargs='?', choices=[
        'run', 'review', 'install', 'diff', 'commitDiff', 'comment'
    ], help='The operation to perform')
    parser.add_argument('--file', help='The file to compare if operation is diff')
    return parser.parse_args()


def p(folder = '', file = ''):
    """Return the os path prefixed with the VVD temp directory."""

    temp = 'vvd-temp'
    return os.path.join(temp, folder, file)


def hr(n = 100, character = '-'):
    """Return a horizontal rule"""
    hr = ''
    for i in range(n):
        hr += character
    return '\n' + hr + '\n'


def run():
    """Review changes, install dependencies, and diff each changed file."""

    print hr() + 'VVD run()' + hr()
    print 'Starting by reviewing changes'

    # Review changes in the latest commit. Prepare a list of changed Dynamo and Grasshopper graphs.
    changed = review()

    if(changed):
        # Prepare environment and install VVD and its dependencies.
        install()

        # Prepare each file to diff
        for file in changed:
            prepare(file)
    
    else:
        print 'No Dynamo or Grasshopper files have been changed'


def review():
    """Review changes in the latest commit. Prepare a list of changed Dynamo and Grasshopper graphs."""
    
    print hr() + 'VVD review()' + hr()

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

    print hr() + 'VVD install()' + hr()

    print 'Preparing the environment.'

    # Create VVD directories
    for folder in ['dl', 'latest', 'previous', 'diff']:
        if not os.path.exists(p(folder)):
            os.makedirs(p(folder))

    print 'Installing VVD and its dependencies.'

    # Change the working directory to dl
    print p('dl')
    # subprocess.call(['cd', ])
    os.chdir(p('dl'))

    # Download & Extract VVD
    # @todo If this fails then halt
    subprocess.call(['curl', '-LOk', 'https://github.com/StudioLE/VVD/archive/build.zip'])
    subprocess.call(['7z', 'x', 'build.zip', '-aoa'])

    # Download & Extract Graphviz
    # @todo If this fails then halt
    subprocess.call(['curl', '-LOk', 'https://graphviz.gitlab.io/_pages/Download/windows/graphviz-2.38.zip'])
    subprocess.call(['7z', 'x', 'graphviz-2.38.zip', '-o' + 'graphviz', '-aoa'])
    
    # Add Graphviz to path
    # This is super hacky... Currently adding all graphviz binaries to the npm bin folder because it's already in %PATH%
    # @todo Add graphviz to path correctly.
    subprocess.call(['cp', '-a', 'graphviz\\release\\bin\\.', os.getenv('APPDATA') + '\\npm\\'])
    # graphviz = os.path.abspath(p('graphviz\\release\\bin'))
    # print graphviz
    # print sys.path
    # subprocess.call(['echo', '%PATH%'])
    # subprocess.call(['setx', 'path', graphviz])
    # subprocess.call(['ls', graphviz])
    # subprocess.call(['echo', '%PATH%'])
    # sys.path.append(graphviz)
    # print sys.path

    # Download & Install PyGraphviz
    # @todo If this fails then halt
    subprocess.call(['curl', '-LOk', 'https://download.lfd.uci.edu/pythonlibs/t4jqbe6o/pygraphviz-1.3.1-cp27-none-win32.whl'])
    subprocess.call(['pip', 'install', 'pygraphviz-1.3.1-cp27-none-win32.whl'])
    
    # Install PyGithub
    subprocess.call(['pip', 'install', '--trusted-host', 'pypi.org', '--trusted-host', 'files.pythonhosted.org', 'PyGithub'])

    # List directory contents
    #subprocess.call(['ls'])

    # Return to the original working directory
    # subprocess.call(['cd', '../../'])
    os.chdir('../../')

def prepare(file):
    """Prepare the latest and previous versions of the files to be compared."""

    print hr() + 'VVD prepare()' + hr()

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
    # subprocess.call([p('VVD-build', 'diffgh.cmd'), previous, latest, previous + '.diff'])
    diff(file, previous, latest)


def diff(file, previous, latest):
    """Create a .diff file comparing the latest and previous graphs."""

    print hr() + 'VVD diff()' + hr()

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
    print 'Using executable:', graphToCG
    subprocess.call([
        p('dl\\VVD-build', graphToCG),
        previous,
        previous + '.cgx'
    ])
    subprocess.call([
        p('dl\\VVD-build', graphToCG),
        latest,
        latest + '.cgx'
    ])

    diff = p('diff', file + '.diff')
    
    # Create an empty diff file
    # if not os.path.exists(diff):
    #     open(diff, 'w')

    # Create a diff of the two Common Graphs
    # @todo I think this might fail when file contains a path
    subprocess.call([
        'python',
        p('dl\\VVD-build', 'diffgraph.py'),
        previous + '.cgx',
        latest + '.cgx',
        diff
    ])

    diffToPNG(previous, diff)
    commitDiff(file)


def diffToPNG(previous, diff):
    """Create a PNG of the common graph .diff file"""

    print hr() + 'VVD diffToPNG()' + hr()
    
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
        p('dl\\VVD-build', 'grapher.py'),
        previous + '.cgx',
        diff,
        diff + '.png'
    ])


def commitDiff(file):
    """Deploy .diff and .diff.png assets to GitHub"""

    print hr() + 'VVD commitDiff()' + hr()

    # On first deploy
    # git checkout --orphan vvd
    # git rm -r --cached .
    # Create .gitignore

    # On subsequent deploys
    # git checkout vvd

    # Both
    # git add vvd-temp\
    # git commit -m "VVD Updates"
    # git push --set-upstream origin vvd
    
    # Get the SHA hash of the latest commit
    graph_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'])

    # Checkout a new orphaned branch. If the branch already exists this will fail. That's fine.
    subprocess.call(['git', 'checkout', '--orphan', 'vvd'])

    # Remove all staged files
    # @todo This causes a ton of problems. I think we need to accept that all files from master will be copied to vvd...
    # subprocess.call(['git', 'rm', '-r', '--cached', '.'])

    # Checkout the branch again in case it already existed
    subprocess.call(['git', 'checkout', 'vvd'])

    # Download the .gitignore
    subprocess.call(['curl', '-LOk', 'https://raw.githubusercontent.com/StudioLE/VVDforGitHub/master/vvd/.gitignore'])

    # Copy changes
    subprocess.call(['cp', '-rv', 'vvd-temp/diff/*', 'diff'])

    # Git add all files. .gitignore will ensure it's only .diff and .diff.png files
    subprocess.call(['git', 'add', 'diff/'])

    # Git commit
    subprocess.call(['git', 'commit', '-m', '\"VVD Updates\"'])

    # Get the SHA hash of the vvd diff files
    diff_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'])

    # Git push
    subprocess.call(['git', 'remote', '-v'])
    subprocess.call(['git', 'status'])
    subprocess.call(['git', 'push', '--set-upstream', 'origin', 'vvd'])

    # Git return to start branch
    subprocess.call(['git', 'checkout', os.environ.get('APPVEYOR_REPO_BRANCH')])

    print 'Graph SHA:', graph_sha
    print 'Diff SHA:', diff_sha

    # Create a GitHub comment linking to the .diff.png
    comment(file, graph_sha, diff_sha)

    # https://raw.githubusercontent.com/StudioLE/VVDExample/vvd/vvd-temp/diff/example-1.3.4.dyn.diff.png
    # https://raw.githubusercontent.com/StudioLE/VVDExample/1a7680c436ce0aedcd6124104ca110768ab7a4ce/vvd-temp/  diff/example-1.3.4.dyn.diff.png


def comment(file, graph_sha, diff_sha):
    """Post the commit to GitHub"""
    
    from github import Github
    from github import enable_console_debug_logging

    # Get ENV variables
    access_token = os.environ.get('GITHUB_ACCESS_TOKEN')
    user = os.environ.get('GITHUB_USER')
    repo = os.environ.get('APPVEYOR_REPO_NAME')

    # Prepare the comment
    img = 'https://raw.githubusercontent.com/' + repo +'/' + diff_sha + '/diff/' + file + '.diff.png'
    body = '[VVD for GitHub](https://github.com/StudioLE/VVDforGitHub) has calculated the following Visual Diff for `' + file + '` \n\n ![VVD Diff Graph](' + img + ')'
    position = 1

    # POST to the GitHub API with PyGitHub
    # Docs:
    # https://pygithub.readthedocs.io/en/latest/github_objects/Commit.html#github.Commit.Commit.create_comment
    # https://developer.github.com/v3/repos/comments/#create-a-commit-comment
    g = Github(user, access_token)
    enable_console_debug_logging()
    repo = g.get_repo(repo)
    commit = repo.get_commit(graph_sha)
    out = commit.create_comment(body, position=position, path=file)

    print out

def main():

    print hr() + 'Starting VVD for GitHub' + hr()
    args = parseArgs()

    # Output the python version
    subprocess.call(['python', '--version'])

    # If running on Appveyor
    if(os.environ.get('APPVEYOR_BUILD_ID')):
        subprocess.call(['git', 'config', '--global', 'user.email', os.environ.get('GIT_EMAIL')])
        subprocess.call(['git', 'config', '--global', 'user.name', os.environ.get('GIT_USER')])
    else:
        # Set the environment variables
        import env

    print 'GitHub User:', os.environ.get('GITHUB_USER')
    print 'GitHub Repo:', os.environ.get('APPVEYOR_REPO_NAME')
    print 'GitHub Branch:', os.environ.get('APPVEYOR_REPO_BRANCH')

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

    elif(args.operation == 'comment'):
        # Prepare environment and install VVD and its dependencies.
        comment('example-1.3.4.dyn', 'ec7d974f81cb4dd1a0fceaf8b2f4cc36e15b18bb', '1a7680c436ce0aedcd6124104ca110768ab7a4ce') 

    elif(args.operation == 'commitDiff'):
        # Prepare environment and install VVD and its dependencies.
        commitDiff('example-1.3.4.dyn') 

    else:
        print 'Please specify a valid operation'

if __name__ == '__main__':
    main()
