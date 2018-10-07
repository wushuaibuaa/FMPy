import argparse
import os
import sys
import fmpy
from fmpy.util import read_csv
from fmpy.cross_check.cross_check import cross_check

parser = argparse.ArgumentParser(description='run the FMI cross-check')

parser.add_argument('--xc_repo', default=os.getcwd(), help='the directory that contains the test FMUs')
parser.add_argument('--include', nargs='+', default=[], help='path segments to include')
parser.add_argument('--exclude', nargs='+', default=[], help='path segments to exclude')

# parse the command line arguments
args = parser.parse_args()


def skip(options):

    fmu_filename = options['fmu_filename']

    # skip all models that match any of the exclude patterns
    for pattern in args.exclude:
        if pattern in fmu_filename:
            return True

    # only include models that match all include patterns
    for pattern in args.include:
        if pattern not in fmu_filename:
            return True

    if options['fmi_type'] == 'me' and options['model_name'] == 'PneumaticActuator':
        return True  # cannot be solved

    if options['tool_name'] == 'Adams':
        return True  # requires Adams installation

    # Sort out the FMUs that crash the process
    #
    # # linux64
    # if 'FMI_1.0/ModelExchange/linux64/JModelica.org/1.15' in fmu_filename:
    #     return True  # exit code 139 (interrupted by signal 11: SIGSEGV)
    #
    # if 'FMI_1.0/ModelExchange/linux64/AMESim' in fmu_filename:
    #     return True  # exit code 139 (interrupted by signal 11: SIGSEGV)

    return False


def simulate(options):

    # read the input file
    if 'input_filename' in options:
        input = read_csv(options['input_filename'])
    else:
        input = None

    # simulate the FMU
    result = fmpy.simulate_fmu(filename=options['fmu_filename'],
                               validate=False,
                               step_size=None if options['step_size'] <= 0 else options['step_size'],  # quick-fix
                               stop_time=options['stop_time'],
                               input=input,
                               output=options['output_variable_names'])

    return result


cross_check(xc_repo=args.xc_repo,
            simulate=simulate,  # if args.simulate else None,
            tool_name='FMPy',
            tool_version=fmpy.__version__,
            skip=skip)
