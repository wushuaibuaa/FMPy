import fmpy
import zipfile
import time
from ..util import *

from jinja2 import Environment, PackageLoader



def cross_check(xc_repo, report, result_dir, simulate, tool_name, tool_version, skip, readme):

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

        #reference, ref_csv_cell = check_csv_file(filename=ref_path, variables=output_variables)

        skipped = True

        if False:
            pass
        # if simulate is None:
        #     sim_cell = '<td class="status" title="Simulation is disabled"><span class="label label-default">skipped</span></td>'
        # elif ref_opts is None:
        #     sim_cell = '<td class="status" title="Failed to read *_ref.opt file"><span class="label label-default">skipped</span></td>'
        # elif input_variables and input is None:
        #     sim_cell = '<td class="status" title="Input file is invalid"><span class="label label-default">skipped</span></td>'
        else:
            skipped = False

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

                sim_cell = '<td class="status"><span class="label label-success">%.2f s</span></td>' % (time.time() - start_time)

                res_cell = "?"

                relative_result_dir = os.path.join('results', options['fmi_version'], options['fmi_type'],
                                                   options['platform'], tool_name, tool_version, options['tool_name'],
                                                   options['tool_version'], options['model_name'])

                # html.write(r'<td>' + options['model_name'] + '</td><td><div class="tooltip">' + res_cell + '<span class="tooltiptext"><img src="'
                #                 + os.path.join(relative_result_dir, 'result.png').replace('\\', '/') + '"/></span ></div></td>')

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
                sim_cell = '<td class="status"><span class="label label-danger" title="' + str(e) + '">failed</span></td>'

        results_.append(result_)

        # ##############
        # # VALIDATION #
        # ##############
        # if skipped:
        #     res_cell = '<span class="label label-default">n/a</span>'
        # else:
        #     try:
        #         rel_out = validate_result(result=result, reference=reference)
        #     except Exception as e:
        #         print(str(e))
        #         rel_out = 1
        #
        #     res_cell = '<span class="label '
        #
        #     if rel_out <= 0:
        #         res_cell += 'label-success'
        #     elif rel_out <= 0.1:
        #         res_cell += 'label-warning'
        #     else:
        #         res_cell += 'label-danger'
        #
        #     res_cell += '">%d %%</span>' % np.floor((1.0 - rel_out) * 100)
        #
        # # this will remove any trailing (back)slashes
        # fmus_dir = os.path.normpath(fmus_dir)
        #
        # model_path = fmu_filename[len(fmus_dir)+1:]
        #
        # model_path = os.path.dirname(model_path)
        #
        # html.write('<tr><td>' + root + '</td>')
        # html.write('\n'.join([xml_cell, ref_opts_cell, in_csv_cell, ref_csv_cell, doc_cell, sim_cell]))
        #
        # if result_dir is not None and result is not None:
        #
        #     relative_result_dir = os.path.join(result_dir, options['fmi_version'], options['fmi_type'],
        #                                        options['platform'], tool_name, tool_version, options['tool_name'],
        #                                        options['tool_version'], options['model_name'])
        #
        #     fmu_result_dir = os.path.join(result_dir, relative_result_dir)
        #
        #     if not os.path.exists(fmu_result_dir):
        #         os.makedirs(fmu_result_dir)
        #
        #     # write the indicator file
        #     if skipped:
        #         indicator_filename = 'rejected'
        #     elif rel_out < 0.1:
        #         indicator_filename = 'passed'
        #     else:
        #         indicator_filename = 'failed'
        #
        #     with open(os.path.join(fmu_result_dir, indicator_filename), 'w') as f:
        #         pass
        #
        #     if readme is not None:
        #         # write the ReadMe.txt file
        #         with open(os.path.join(fmu_result_dir, 'ReadMe.txt'), 'w') as f:
        #             f.write(readme())
        #
        #     result_filename = os.path.join(fmu_result_dir, model_name + '_out.csv')
        #
        #     header = ','.join(map(lambda s: '"' + s + '"', result.dtype.names))
        #     np.savetxt(result_filename, result, delimiter=',', header=header, comments='', fmt='%g')
        #
        #     reference_filename = os.path.join(fmus_dir, model_path, model_name + '_ref.csv')
        #
        #     if os.path.isfile(reference_filename):
        #         # load the reference trajectories
        #         reference = np.genfromtxt(reference_filename, delimiter=',', names=True, deletechars='')
        #     else:
        #         reference = None
        #
        #     plot_filename = os.path.join(fmu_result_dir, 'result.png')
        #     plot_result(result, reference, filename=plot_filename)
        #
        #     html.write(r'<td><div class="tooltip">' + res_cell + '<span class="tooltiptext"><img src="'
        #                + os.path.join(relative_result_dir, 'result.png').replace('\\', '/') + '"/></span ></div></td>')
        # else:
        #     html.write('<td class="status">' + res_cell + '</td>\n')

    # write the report
    env = Environment(loader=PackageLoader('fmpy.cross_check'))

    template = env.get_template('report.html')

    report_filename = os.path.join(xc_repo, 'report.html')

    template.stream(results=results_).dump(report_filename)

    print("Done.")
