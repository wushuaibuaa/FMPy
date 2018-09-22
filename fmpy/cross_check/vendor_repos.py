"""
Clone or update the cross-check vendor repositories

Clone all repositories into the current directory:
    $ python clone_vendor_repos.py

Clone 3ds and QTronic into /tmp/xc-data:
    $ python clone_vendor_repos.py --destination /tmp/xc-data --vendors 3ds QTronic
"""


def clone_repos(path=None, vendors=None):
    """
    Clone or update the cross-check repositories
    """

    import os
    from subprocess import call
    from fmpy.cross_check import get_vendor_ids

    if path is None:
        path = os.getcwd()

    vendors = get_vendor_ids('/Users/tors10/Development/fmi-standard.org/_data/tools.csv')

    for vendor in sorted(vendors.keys()):

        if vendors is None or vendor in vendors:

            clone_url = 'https://github.com/fmi-crosscheck/%s.git' % vendor

            repo_dir = os.path.join(path, vendor)

            try:
                # pull from the remote
                print('Pulling %s...' % vendor)
                call(['git', 'lfs', 'pull'], cwd=repo_dir)
                # TODO: reset --hard, clean -fd
            except Exception as e1:
                # clone the repository if it doesn't exist yet
                print('Cloning %s...' % vendor)
                try:
                    call(['git', 'clone', clone_url], cwd=path)
                except Exception as e2:
                    # catch problems like empty repo
                    print(e2)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description="Clone or update the cross-check vendor repositories")

    parser.add_argument('tools_csv', help="Path to the tools.csv file from the fmi-standard.org repository")
    parser.add_argument('vendor_repos_dir', help="Directory that contains the vendor repositories")
    parser.add_argument('--vendors', nargs='+', help="Vendor repositories to clone")

    args = parser.parse_args()

    clone_repos(tools_csv=args.tools_csv,
                vendor_repos_dir=args.vendor_repos_dir,
                vendors=args.vendors)
