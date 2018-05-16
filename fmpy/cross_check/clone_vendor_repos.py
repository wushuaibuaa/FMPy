from __future__ import print_function


def clone_vendor_repos(destination=None, vendors=None):
    """
    Clone or update the cross-check vendor repositories
    """

    import requests
    import git
    from git import Repo, NoSuchPathError
    import os

    if destination is None:
        destination = os.getcwd()

    # get a list of the cross-check repositories
    repos = requests.get('https://api.github.com/orgs/fmi-crosscheck/repos?per_page=100').json()

    # TODO: get more than 100

    for entry in repos:
        _, vendor = os.path.split(entry['full_name'])

        if vendors is None or vendor in vendors:
            clone_url = entry['clone_url']
            repo_dir = os.path.join(destination, vendor)

            try:
                # pull from the remote
                repo = Repo(path=repo_dir)
                print('Pulling %s' % vendor)
                o = repo.remotes.origin
                o.pull()

            except NoSuchPathError:

                class Progress(git.remote.RemoteProgress):

                    def update(self, op_code, cur_count, max_count=None, message=''):
                        # show progress
                        print(self._cur_line)

                # clone the repository if it doesn't exist yet
                print('Cloning %s...' % vendor)
                print()

                Repo.clone_from(url=clone_url, to_path=repo_dir, progress=Progress())


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description="Clone or update the cross-check vendor repositories")

    parser.add_argument('--destination', help="destination directory for the cloned repositories")
    parser.add_argument('--vendors', nargs='+', help="vendor repositories to clone")

    args = parser.parse_args()

    clone_vendor_repos(destination=args.destination, vendors=args.vendors)
