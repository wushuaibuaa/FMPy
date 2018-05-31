from __future__ import print_function

import sys
import os
import numpy as np

from fmpy import read_model_description
from fmpy.util import read_ref_opt_file, read_csv


def read_csv(filename, variable_names=None, max_size=1024**2):
    """ Read a CSV file that conforms to the FMI cross-check rules

    Parameters:
        filename        name of the CSV file to read
        variable_names  list of legal variable names
        max_size        max. file size in bytes

    Returns:
        traj             the trajectoies read from the CSV file
    """

    if max_size is not None:

        file_size = os.path.getsize(filename)

        if file_size > max_size:
            raise Exception("Maximum file size is %d bytes but file has %d bytes" % (max_size, file_size))

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

    if os.path.isfile(os.path.join(model_dir, 'notCompliantWithLatestRules')):
        return []

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
    for suffix, required in [('_cc.csv', True), ('_in.csv', False), ('_ref.csv', True)]:

        csv_filename = os.path.join(model_dir, model_name + suffix)

        if not required and not os.path.isfile(csv_filename):
            continue

        try:
            read_csv(csv_filename, variable_names=variable_names)
        except Exception as e:
            problems.append("Error in %s. %s" % (csv_filename, e))

    # check compliance checker log file
    cc_logfile = model_name + '_cc.log'

    if not os.path.isfile(os.path.join(model_dir, cc_logfile)):
        problems.append("%s is missing in %s" % (cc_logfile, model_dir))

    # check ReadMe
    if not os.path.isfile(os.path.join(model_dir, 'ReadMe.txt')) and not os.path.isfile(os.path.join(model_dir, 'ReadMe.pdf')):
        problems.append("Readme.[txt|pdf] is missing in %s" % model_dir)

    if platform in ['win32', 'win64']:
        cc_script = model_name + '_cc.bat'
    else:
        cc_script = model_name + '_cc.sh'

    if not os.path.isfile(os.path.join(model_dir, cc_script)):
        problems.append("%s is missing in %s" % (cc_script, model_dir))

    return problems


def validate_cross_check_result(result_dir, tools):
    """ Validate a cross-check result

    Parameters:
        result_dir  path to the directory that contains the results

    Returns:
        a list of problems
    """

    # check if the import has claims 'passed' state
    claims_passsed = os.path.isfile(os.path.join(result_dir, 'passed'))

    if not claims_passsed:
        return []  # skip this result

    problems = []

    path, model_name = os.path.split(result_dir)
    path, exporting_tool_version = os.path.split(path)
    path, exporting_tool_name = os.path.split(path)
    path, importing_tool_version = os.path.split(path)
    path, importing_tool_name = os.path.split(path)
    path, fmi_platform = os.path.split(path)
    path, fmi_type = os.path.split(path)
    path, fmi_version = os.path.split(path)
    path, _ = os.path.split(path)
    path, vendor = os.path.split(path)

    if exporting_tool_name not in tools:
        problems.append('Unknown tool "%s"' % exporting_tool_name)
        return problems

    exporting_vendor = tools[exporting_tool_name]

    # path to the FMU's directory
    ref_dir = os.path.join(path, exporting_vendor, 'Test_FMUs', fmi_version, fmi_type, platform, exporting_tool_name, exporting_tool_version, model_name)

    # check if the FMU complies to the XC rules
    if os.path.isfile(os.path.join(ref_dir, 'doesNotComplyWithLatestRules')):
        problems.append('The exported FMU does not comply with the cross-check rules')
        return problems

    # check the output file
    ref_csv_filename = os.path.join(ref_dir, model_name + '_ref.csv')

    # check if the reference result exists
    if not os.path.isfile(ref_csv_filename):
        problems.append('The reference result "%s" was not found' % ref_csv_filename)
        return problems

    try:
        # read the reference result
        ref = read_csv(ref_csv_filename)
    except Exception as e:
        problems.append("Error in %s. %s" % (ref_csv_filename, e))
        return problems

    csv_filename = os.path.join(result_dir, model_name + '_out.csv')

    try:
        # read the result
        res = read_csv(csv_filename)
    except Exception as e:
        problems.append("Error in %s. %s" % (csv_filename, e))
        return problems

    # validate the results
    problem = validate_result(result=res, reference=ref)

    if problem is not None:
        problems.append('Error in %s: %s' % (csv_filename, problem))

    return problems


def validate_result(result, reference, stop_time=None):
    """ Validate a simulation result against a reference result

    Parameters:
        result      structured NumPy array where the first column is the time
        reference   same as result

    Returns:
        problems    a list of problems
    """

    t_ref = reference[reference.dtype.names[0]]
    t_res = result[result.dtype.names[0]]

    # at least two samples are required
    if result.size < 2:
        return 'The result must have at least two samples'

    # check if stop time has been reached
    if stop_time is not None and t_res[-1] < stop_time:
        return 'The stop time %g has not been reached'

    # check if all reference signals are contained in the result
    for name in reference.dtype.names[1:]:
        if name not in result.dtype.names:
            return 'Variable "%s" is missing' % name

    rel_out = 0

    # find the signal with the most outliers
    for name in result.dtype.names[1:]:

        if name not in reference.dtype.names:
            continue

        y_ref = reference[name]
        y_res = result[name]
        _, _, _, outliers = validate_signal(t=t_res, y=y_res, t_ref=t_ref, y_ref=y_ref)
        rel_out = np.max([np.sum(outliers) / float(len(outliers)), rel_out])

    # TODO: check rel_out

    return None


def validate_signal(t, y, t_ref, y_ref, num=1000, dx=20, dy=0.1):
    """ Validate a signal y(t) against a reference signal y_ref(t_ref) by creating a band
    around y_ref and finding the values in y outside the band

    Parameters:

        t       time of the signal
        y       values of the signal
        t_ref   time of the reference signal
        y_ref   values of the reference signal
        num     number of samples for the band
        dx      horizontal width of the band in samples
        dy      vertical distance of the band to y_ref

    Returns:

        t_band  time values of the band
        y_min   lower limit of the band
        y_max   upper limit of the band
        i_out   indices of the values in y outside the band
    """

    from scipy.ndimage.filters import maximum_filter1d, minimum_filter1d

    # re-sample the reference signal into a uniform grid
    t_band = np.linspace(start=t_ref[0], stop=t_ref[-1], num=num)

    # sort out the duplicate samples before the interpolation
    m = np.concatenate(([True], np.diff(t_ref) > 0))

    y_band = np.interp(x=t_band, xp=t_ref[m], fp=y_ref[m])

    y_band_min = np.min(y_band)
    y_band_max = np.max(y_band)

    # calculate the width of the band
    if y_band_min == y_band_max:
        w = 0.5 if y_band_min == 0 else np.abs(y_band_min) * dy
    else:
        w = (y_band_max - y_band_min) * dy

    # calculate the lower and upper limits
    y_min = minimum_filter1d(input=y_band, size=dx) - w
    y_max = maximum_filter1d(input=y_band, size=dx) + w

    # find outliers
    y_min_i = np.interp(x=t, xp=t_band, fp=y_min)
    y_max_i = np.interp(x=t, xp=t_band, fp=y_max)
    i_out = np.logical_or(y < y_min_i, y > y_max_i)

    # do not count outliers outside the t_ref
    i_out = np.logical_and(i_out, t > t_band[0])
    i_out = np.logical_and(i_out, t < t_band[-1])

    return t_band, y_min, y_max, i_out


def segments(path):
    """ Split a path into segments """

    s = []

    head, tail = os.path.split(path)

    while tail:
        s.insert(0, tail)
        head, tail = os.path.split(head)

    s.insert(0, head)

    return s


def get_exporting_tools(repos_dir):
    """ Collect the tools for all vendors """

    tools = {}

    for vendor in os.listdir(repos_dir):
        for fmi_version in ['FMI_1.0', 'FMI_2.0']:
            for fmi_type in ['CoSimulation', 'ModelExchange']:
                for platform in ['darwin64', 'linux32', 'linux64', 'win32', 'win64']:
                    platform_dir = os.path.join(repos_dir, vendor, 'Test_FMUs', fmi_version, fmi_type, platform)
                    if os.path.isdir(platform_dir):
                        for tool in os.listdir(platform_dir):
                            tool_dir = os.path.join(platform_dir, tool)
                            if os.path.isdir(tool_dir):
                                tools[tool] = vendor

    return tools


if __name__ == '__main__':

    import argparse
    import textwrap

    description = "Validate cross-check results and test FMUs in vendor repositories"

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(description))

    parser.add_argument('repo_path', nargs='?', help="path to the vendor repository")
    parser.add_argument('--json', help="JSON file to save the problems")

    args = parser.parse_args()

    problems = []

    if args.repo_path:
        vendor_dir = args.repo_path
    else:
        vendor_dir = os.getcwd()

    repos_dir, _ = os.path.split(vendor_dir)

    tools = get_exporting_tools(repos_dir)

    s = segments(vendor_dir)

    # validate the cross-check results
    for subdir, dirs, files in os.walk(os.path.join(vendor_dir, 'CrossCheck_Results')):

        t = segments(subdir)

        if len(t) - len(s) != 9:
            continue

        xc_type, fmi_version, fmi_type, platform = t[-9:-5]

        if fmi_version not in ['FMI_1.0', 'FMI_2.0']:
            continue

        if fmi_type not in ['CoSimulation', 'ModelExchange']:
            continue

        if platform not in ['c-code', 'darwin64', 'linux32', 'linux64', 'win32', 'win64']:
            continue

        problems += validate_cross_check_result(subdir, tools)

    # # validate the test FMUs
    # for subdir, dirs, files in os.walk(os.path.join(vendor_dir, 'Test_FMUs')):
    #
    #     t = segments(subdir)
    #
    #     if len(t) - len(s) != 7:
    #         continue
    #
    #     fmi_version, fmi_type, platform = t[-6:-3]
    #
    #     if fmi_version not in ['FMI_1.0', 'FMI_2.0']:
    #         continue
    #
    #     if fmi_type not in ['CoSimulation', 'ModelExchange']:
    #         continue
    #
    #     if platform not in ['c-code', 'darwin64', 'linux32', 'linux64', 'win32', 'win64']:
    #         continue
    #
    #     problems += validate_test_fmu(subdir)


    # filter Unknown...
    problems = [p for p in problems if not p.startswith('Unknown')]

    print()
    print("#################################")
    print("%d problems found in %s" % (len(problems), vendor_dir))
    print("#################################")
    print()

    for problem in problems:
        print()
        print(problem)

    if args.json:
        import json
        with open(args.json, 'w') as outfile:
            json.dump(problems, outfile, indent=2)

    sys.exit(len(problems))
