import unittest
from fmpy import simulate_fmu, read_model_description
from fmpy.util import write_sdf, write_csv, download_test_file


class WriteResultsTest(unittest.TestCase):

    def test_write_results(self):

        filename = 'CoupledClutches.fmu'

        download_test_file('2.0', 'CoSimulation', 'MapleSim', '2017', 'CoupledClutches', filename)

        model_description = read_model_description(filename)

        names = []

        # collect all non-internal variable names
        for variable in model_description.modelVariables:
            if variable.description == 'internal variable':
                continue
            if variable.description and variable.description.startswith('msim_RVAR'):
                continue
            names.append(variable.name)

        # run the simulation and store all variables
        result = simulate_fmu(filename, output=names)

        # save CSV
        write_csv('CoupledClutches.csv', result)

        # save SDF structured
        write_sdf('CoupledClutches_structured.sdf', result, model_description)

        # save SDF flat
        model_description.variableNamingConvention = 'flat'
        write_sdf('CoupledClutches_flat.sdf', result, model_description)


if __name__ == '__main__':

    unittest.main()
