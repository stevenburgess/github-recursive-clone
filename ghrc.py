import github3
from cherrypy.lib.static import serve_file
import cherrypy
import os
import shutil
import random
import tarfile
import configparser
# Given a repository, recursivley pull all its submodules via GH API calls

config = configparser.ConfigParser()
config.read('configs.cfg')
external_token = config['github-recursive-clone']['external_token']
internal_token = config['github-recursive-clone']['internal_token']
internal_url = config['github-recursive-clone']['internal_url']

# All work will take place inside the working directory
workdir_base = '/opt/ghrc/'

github_internal = github3.github.GitHubEnterprise(
    token=internal_token,
    url=internal_url
    )

github_external = github3.github.GitHub(token=external_token)


def parse_owner(URL):
    """
    There are two common ways to specify a submolde URL, either with the git@
    syntax, or the http/git syntax. Examples:
    git@github.com:zfsonlinux/zfs.git
    https://github.com/zfsonlinux/zfs.git
    git://github.com/zfsonlinux/zfs.git
    one trick is that the owner and repo have to be seperated by a /, the other
    is that both : and / are invalid characters on github, so if you encounter
    one, you have hit a divider.
    """
    split_url = URL.rsplit('/', maxsplit=1)
    repo = split_url[1]
    if repo.endswith('.git'):
        repo = repo[:-4]
    try:
        owner = split_url[0].rsplit('/', maxsplit=1)[1]
        return(owner, repo)
    except IndexError:
        owner = split_url[0].rsplit(':', maxsplit=1)[1]
        return(owner, repo)


def recursive_pull(URL, sha, workdir, depth):
    """
    URL - The URL of a git repository, what you would pass to git clone
    sha - The SHA of the repo to pull
    workdir - The directory you are working in
    depth - The path so far on top of workdir
    """
    # some helpful locations
    final_location = workdir + 'final/'
    tarfile_path = workdir + 'current.tar.gz'
    # From the URL, determine which instance it is on
    if 'github.com' in URL:
        gh = github_external
    else:
        gh = github_internal
    owner, repo = parse_owner(URL)
    # This is going to be the most problematic section, you could get problems
    # because:
    # -The github instance you were talking to is unreachable/offline
    # -Mis spellings of the owner or repository
    # -The owner or repository do not exist
    # -They do exist, but the specified SHA does not
    try:
        repository = gh.repository(owner=owner, repository=repo)
        tarball = repository.archive(format="tarball",
                                     path=tarfile_path, ref=sha)
        tar = tarfile.open(mode='r|gz', name=tarfile_path)
        tar.extractall(workdir)
        tar.close()
    except:
        raise NameError("Error pulling " + URL + " " + sha + "\n" +
                        "Ensure that the URL is properly formated, and that " +
                        "the specified SHA exists.")

    # move it into the correct place
    internal_name = workdir + owner + '-' + repo + '-' + sha[:7] + '/'
    os.rename(internal_name, final_location + depth)
    # Now get and parse the .submodules file
    modulefile = final_location + depth + '.gitmodules'
    if not os.path.exists(modulefile):
        # Then there is no submodules here
        return
    moduleparser = configparser.ConfigParser()
    moduleparser.read(modulefile)
    for submodule in moduleparser.sections():
        # determine the SHA for this submodule
        content = repository.contents(
            ref=sha,
            path=moduleparser[submodule]['path']
            )
        submodulesha = content.to_json()['sha']
        recursive_pull(
            moduleparser[submodule]['url'],
            submodulesha,
            workdir,
            depth + moduleparser[submodule]['path'] + '/'
            )


# There needs to be some way to identify this call from the others. I use
# the cherrypy tools to assign a 6 digit random number to this call. This
# number is used as a unique identifer thoughout the call.
def mkrand():
    req = cherrypy.request
    randint = str(random.randint(100000, 999999))
    req.params['rand'] = randint


def delrand():
    req = cherrypy.request
    randint = req.params['rand']
    workdir = workdir_base + randint + '/'
    shutil.rmtree(workdir)


cherrypy.tools.mkrand = cherrypy.Tool('before_handler', mkrand)
cherrypy.tools.delrand = cherrypy.Tool('on_end_request', delrand)


class GithubRecusiveClone(object):

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.mkrand()
    @cherrypy.tools.delrand()
    def ghrc(self, rand):
        # The user passed in a JSON of data, pull what we need from it
        data = cherrypy.request.json
        URL = data['URL']
        sha = data['sha']
        # setup working space
        workdir = workdir_base + rand + '/'
        os.mkdir(workdir)
        final_location = workdir + 'final/'
        os.mkdir(final_location)
        # do the actual work
        recursive_pull(URL, sha, workdir, '')
        # tar up the results directory
        os.chdir(workdir)
        # make the subdirectory name look like it came from github
        owner, repo = parse_owner(URL)
        gh_shortname = owner + '-' + repo + '-' + sha[:7]
        os.rename('final', gh_shortname)
        tarpath = workdir + sha + ".tar.gz"
        tar = tarfile.open(tarpath, "w:gz")
        tar.add(gh_shortname)
        tar.close()
        return serve_file(
            tarpath,
            "application/x-gzip",
            "attachment"
            )

if __name__ == '__main__':
    cherrypy.quickstart(GithubRecusiveClone(), config='/opt/code/server.conf')
