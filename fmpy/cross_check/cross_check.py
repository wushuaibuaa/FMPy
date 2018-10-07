import fmpy
import time
from ..util import *
from jinja2 import Environment, PackageLoader


def cross_check(xc_repo, simulate, tool_name, tool_version, skip):

    results_ = []

    for root, dirs, files in os.walk(xc_repo):

        fmu_filename = None

        for file in files:
            if file.endswith('.fmu'):
                fmu_name, _ = os.path.splitext(file)  # FMU name without file extension
                fmu_filename = os.path.join(root, file)  # absolute path filename
                break

        if fmu_filename is None:
            continue

        # dictionary that contains the information about the FMU
        options = {'fmu_filename': fmu_filename}

        # extract the cross-check info from the path
        options.update(fmu_path_info(root))

        if skip(options):
            continue

        if options['platform'] != fmpy.platform:
            continue

        print(root)

        result_ = {'path': root}

        ##############
        # SIMULATION #
        ##############

        ref_opts = read_ref_opt_file(os.path.join(root, fmu_name + '_ref.opt'))
        reference = read_csv(filename=os.path.join(root, fmu_name + '_ref.csv'))

        in_path = os.path.join(root, fmu_name + '_in.csv')

        if not os.path.isfile(in_path):
            in_path = None

        result_['plot'] = ''
        result_['cpu_time'] = 0.0
        result_['status'] = 'danger'
        result_['rel_out'] = 0.0

        step_size = ref_opts['StepSize']
        stop_time = ref_opts['StopTime']

        if reference is not None:
            output_variable_names = reference.dtype.names[1:]
        else:
            output_variable_names = None

        try:
            start_time = time.time()

            options['fmu_filename'] = fmu_filename
            options['step_size'] = step_size
            options['stop_time'] = stop_time

            if in_path is not None:
                options['input_filename'] = in_path

            options['output_variable_names'] = output_variable_names

            # simulate the FMU
            result = simulate(options)

            result_dir = os.path.join(xc_repo, 'results', options['fmi_version'], options['fmi_type'],
                                           options['platform'], tool_name, tool_version, options['tool_name'],
                                           options['tool_version'], options['model_name'])

            if not os.path.exists(result_dir):
                os.makedirs(result_dir)

            result_filename = os.path.join(result_dir, options['model_name'] + '_out.csv')

            header = ','.join(map(lambda s: '"' + s + '"', result.dtype.names))
            np.savetxt(result_filename, result, delimiter=',', header=header, comments='', fmt='%g')

            model_path = os.path.dirname(fmu_filename)

            reference_filename = os.path.join(model_path, options['model_name'] + '_ref.csv')

            # load the reference trajectories
            reference = np.genfromtxt(reference_filename, delimiter=',', names=True, deletechars='')

            plot_filename = os.path.join(result_dir, 'result.png')
            plot_result(result, reference, filename=plot_filename)

            relative_result_dir = os.path.join('results', options['fmi_version'], options['fmi_type'],
                                               options['platform'], tool_name, tool_version, options['tool_name'],
                                               options['tool_version'], options['model_name'])

            rel_out = validate_result(result=result, reference=reference)

            result_['plot'] = os.path.join(relative_result_dir, 'result.png').replace('\\', '/')

            result_['cpu_time'] = time.time() - start_time

            if rel_out > 0.1:
                result_['status'] = 'danger'
            elif rel_out > 0:
                result_['status'] = 'warning'
            else:
                result_['status'] = 'success'

            result_['rel_out'] = (1 - rel_out) * 100

        except Exception as e:
            result_['status'] = 'danger'
            print(e)

        # write the indicator file
        if rel_out < 0.1:
            indicator_filename = 'passed'
        else:
            indicator_filename = 'failed'

        with open(os.path.join(result_dir, indicator_filename), 'a'):
            pass

        results_.append(result_)

    # write the report
    env = Environment(loader=PackageLoader('fmpy.cross_check'))

    template = env.get_template('report.html')

    report_filename = os.path.join(xc_repo, 'report.html')

    template.stream(results=results_).dump(report_filename)

    print("Done.")
