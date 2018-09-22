def generate_result_tables(repo_dir, data_dir):
    """ Generate the cross-check result tables """

    import os
    from fmpy.cross_check import get_vendor_ids

    combinations = []  # all permutations of FMI version, type and platform

    for fmi_version in ['FMI_1.0', 'FMI_2.0']:
        for fmi_type in ['CoSimulation', 'ModelExchange']:
            for platform in ['c-code', 'darwin64', 'linux32', 'linux64', 'win32', 'win64']:
                combinations.append((fmi_version, fmi_type, platform))

    tools_csv = os.path.join(data_dir, 'tools.csv')

    vendors = get_vendor_ids(tools_csv)

    tools = {}  # tool_id -> tool_name

    for tool_infos in vendors.values():
        for tool_id, tool_name in tool_infos:
            tools[tool_id] = tool_name

    def split_path(path):

        segments = []

        while True:
            path, segment = os.path.split(path)
            if not segment:
                break
            segments.insert(0, segment)

        return segments

    def collect_results():

        results = []

        for vendor in sorted(vendors.keys()):

            vendor_repo = os.path.join(repo_dir, vendor, 'CrossCheck_Results')

            for root, dirs, files in os.walk(vendor_repo):

                if 'passed' not in files:
                    continue

                segments = split_path(root)

                results.append(segments[-8:])

        return results

    def build_matrix(results, fmi_version, fmi_type, platform):
        """ Build the result matrix for an FMI version, type and platform """

        importing_tools = set()
        exporting_tools = set()

        filtered = []

        # get the tools
        for fmi_version_, fmi_type_, platform_, importing_tool_name, importing_tool_version, exporting_tool_name, exporting_tool_version, model_name in results:

            if fmi_version_ != fmi_version or fmi_type_ != fmi_type or platform_ != platform:
                continue

            importing_tools.add(importing_tool_name)
            exporting_tools.add(exporting_tool_name)

            filtered.append((importing_tool_name, importing_tool_version, exporting_tool_name, exporting_tool_version, model_name))

        # build matrix
        importing_tools = sorted(importing_tools, key=lambda s: s.lower())
        exporting_tools = sorted(exporting_tools, key=lambda s: s.lower())

        matrix = []

        for importing_tool in importing_tools:
            row = []
            for exporting_tool in exporting_tools:
                count = 0
                for r in filtered:
                    if r[0] == importing_tool and r[2] == exporting_tool:
                        count += 1
                row.append(count)
            matrix.append(row)

        return importing_tools, exporting_tools, matrix

    results = collect_results()

    # filter tool IDs
    results = [r for r in results if r[3] in tools and r[5] in tools]

    matrices = {}

    for combination in combinations:
        matrices[combination] = build_matrix(results, *combination)

    for fmi_version, fmi_type, platform in combinations:

        importing_tools, exporting_tools, matrix = matrices[(fmi_version, fmi_type, platform)]

        importing_tools = [tools[tool_id] for tool_id in importing_tools]
        exporting_tools = [tools[tool_id] for tool_id in exporting_tools]

        csv_filename = 'fmi1' if fmi_version == 'FMI_1.0' else 'fmi2'
        csv_filename += '-'
        csv_filename += 'cs' if fmi_type == 'CoSimulation' else 'me'
        csv_filename += '-'
        csv_filename += platform + '.csv'

        with open(os.path.join(data_dir, 'cross-check', csv_filename), 'w') as f:
            f.write(','.join([''] + exporting_tools) + '\n')
            for importing_tool, row in zip(importing_tools, matrix):
                f.write(','.join([importing_tool] + list(map(str, row))) + '\n')


if __name__ is '__main__':

    import argparse

    parser = argparse.ArgumentParser(description="Generate the cross-check result tables")

    parser.add_argument('vendor_repos_dir', help="Directory that contains the vendor repositories")
    parser.add_argument('data_dir', help="_data directory in the fmi-standard.org repository")

    args = parser.parse_args()

    generate_result_tables(repo_dir=args.vendor_repos_dir, data_dir=args.data_dir)
