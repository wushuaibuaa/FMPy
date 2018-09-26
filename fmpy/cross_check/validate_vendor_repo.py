from __future__ import print_function

import sys
import os
import numpy as np
import shutil

from fmpy import read_model_description
from fmpy.util import read_ref_opt_file


def read_csv(filename, variable_names=None):
    """ Read a CSV file that conforms to the FMI cross-check rules

    Parameters:
        filename         name of the CSV file to read
        variable_names   list of legal variable names

    Returns:
        traj             the trajectoies read from the CSV file
    """

    # pass an empty string as deletechars to preserve special characters
    traj = np.genfromtxt(filename, delimiter=',', names=True, deletechars='')

    # get the time
    time = traj[traj.dtype.names[0]]

    # check if the time is monotonically increasing
    if traj.size > 1 and np.any(np.diff(time) < 0):
        raise Exception("Values in first column (time) are not monotonically increasing")

    # check if all variables exist in the FMU
    if variable_names is not None:
        for name in traj.dtype.names[1:]:
            if name not in variable_names:
                raise Exception("Variable '%s' does not exist in the FMU" % name)

    # # check if the variable names match the trajectory names
    # for variable_name in variable_names:
    #     if variable_name not in traj_names:
    #         raise ValidationError("Trajectory of '" + variable_name + "' is missing")

    return traj


def validate_test_fmu(model_dir):
    """ Validate an exported FMU

    Parameters:
        model_dir  path to the directory that contains the exported FMU

    Returns:
        a list of problems
    """

    problems = []

    _, model_name = os.path.split(model_dir)

    # if os.path.isfile(os.path.join(model_dir, 'notCompliantWithLatestRules')):
    #     return []

    fmu_filename = os.path.join(model_dir, model_name + '.fmu')

    # validate the modelDescription.xml
    try:
        model_description = read_model_description(fmu_filename, validate=True)
    except Exception as e:
        problems.append("Error in %s. %s" % (fmu_filename, e))
        return problems  # stop here

    # collect the variable names
    variable_names = [v.name for v in model_description.modelVariables]

    # check the reference options file
    try:
        ref_opts_filename = os.path.join(model_dir, model_name + '_ref.opt')
        read_ref_opt_file(ref_opts_filename)
    except Exception as e:
        problems.append("Error in %s. %s" % (ref_opts_filename, e))

    # check the CSVs
    # for suffix, required in [('_cc.csv', True), ('_in.csv', False), ('_ref.csv', True)]:
    for suffix, required in [('_in.csv', False), ('_ref.csv', True)]:

        csv_filename = os.path.join(model_dir, model_name + suffix)

        if not required and not os.path.isfile(csv_filename):
            continue

        try:
            read_csv(csv_filename, variable_names=variable_names)
        except Exception as e:
            problems.append("Error in %s. %s" % (csv_filename, e))

    # # check compliance checker log file
    # cc_logfile = model_name + '_cc.log'

    # if not os.path.isfile(os.path.join(model_dir, cc_logfile)):
    #     problems.append("%s is missing in %s" % (cc_logfile, model_dir))

    # check ReadMe
    # if not os.path.isfile(os.path.join(model_dir, 'ReadMe.txt')) and not os.path.isfile(os.path.join(model_dir, 'ReadMe.pdf')):
    #    problems.append("Readme.[txt|pdf] is missing in %s" % model_dir)

    # if platform in ['win32', 'win64']:
    #     cc_script = model_name + '_cc.bat'
    # else:
    #     cc_script = model_name + '_cc.sh'
    #
    # if not os.path.isfile(os.path.join(model_dir, cc_script)):
    #     problems.append("%s is missing in %s" % (cc_script, model_dir))

    return problems


def validate_cross_check_result(result_dir):
    """ Validate a cross-check result

    Parameters:
        result_dir  path to the directory that contains the results

    Returns:
        a list of problems
    """

    problems = []

    # if os.path.isfile(os.path.join(result_dir, 'notCompliantWithLatestRules')):
    #     return problems

    # check ReadMe
    # if not os.path.isfile(os.path.join(result_dir, 'ReadMe.txt')) and not os.path.isfile(os.path.join(result_dir, 'ReadMe.pdf')):
    #    problems.append("Readme.[txt|pdf] is missing in %s" % result_dir)

    if not os.path.isfile(os.path.join(result_dir, 'passed')):
        return problems

    _, model_name = os.path.split(result_dir)

    # check the output file
    csv_filename = os.path.join(result_dir, model_name + '_out.csv')

    try:
        read_csv(csv_filename)
    except Exception as e:
        problems.append("Error in %s. %s" % (csv_filename, e))

    return problems


def segments(path):
    """ Split a path into segments """

    s = []

    head, tail = os.path.split(path)

    while tail:
        s.insert(0, tail)
        head, tail = os.path.split(head)

    s.insert(0, head)

    return s


def validate_repo(vendor_dir, clean_up=False):

    problems = []

    s = segments(vendor_dir)

    # validate the cross-check results
    for subdir, dirs, files in os.walk(os.path.join(vendor_dir, 'results')):

        # passed_file = os.path.join(subdir, 'passed')

        # if not os.path.isfile(passed_file):
        #     continue  # ignore

        t = segments(subdir)

        if len(t) - len(s) != 9:
            continue

        fmi_version, fmi_type, platform, importing_tool_name, importing_tool_version, exporting_tool_name, exporting_tool_version, model_name = t[-8:]

        if fmi_version not in ['1.0', '2.0']:
            continue

        if fmi_type not in ['cs', 'me']:
            continue

        if platform not in ['c-code', 'darwin64', 'linux32', 'linux64', 'win32', 'win64']:
            continue

        new_problems = validate_cross_check_result(subdir)

        if new_problems and clean_up:
            print("Removing %s" % subdir)
            shutil.rmtree(subdir)

            #os.remove(passed_file)

        problems += new_problems

    # validate the test FMUs
    for subdir, dirs, files in os.walk(os.path.join(vendor_dir, 'fmus')):

        # not_compliant_file = os.path.join(subdir, 'notCompliantWithLatestRules')

        # if os.path.isfile(not_compliant_file):
        #     continue  # ignore

        t = segments(subdir)

        if len(t) - len(s) != 7:
            continue

        fmi_version, fmi_type, platform, tool_name, tool_version, model_name = t[-6:]

        if fmi_version not in ['1.0', '2.0']:
            continue

        if fmi_type not in ['cs', 'me']:
            continue

        if platform not in ['c-code', 'darwin64', 'linux32', 'linux64', 'win32', 'win64']:
            continue

        new_problems = validate_test_fmu(subdir)

        if clean_up:
            # with open(not_compliant_file, 'a'):
            #     pass
            if new_problems:
                print("Removing %s" % subdir)
                shutil.rmtree(subdir)
            else:
                for file in files:
                    if file.endswith(('_cc.bat', '_cc.csv', '_cc.log')):
                        cc_file = os.path.join(subdir, file)
                        print("Removing %s" % cc_file)
                        os.remove(cc_file)

        problems += new_problems

    return problems


if __name__ == '__main__':

    import argparse
    import textwrap

    description = """\
    Validate cross-check results and test FMUs in vendor repositories 
    """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(description))

    parser.add_argument('xc_repo', nargs='?', help="path to the vendor repository")
    parser.add_argument('--clean-up', action='store_true', help="remove 'passed' file")

    args = parser.parse_args()

    if args.xc_repo:
        xc_repo = args.xc_repo
    else:
        xc_repo = os.getcwd()

    problems = validate_repo(xc_repo, args.clean_up)

    print()
    print("#################################")
    print("%d problems found in %s" % (len(problems), xc_repo))
    print("#################################")
    print()

    for problem in problems:
        print()
        print(problem)

    sys.exit(len(problems))
