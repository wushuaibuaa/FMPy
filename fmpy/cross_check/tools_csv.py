if __name__ is '__main__':

    import argparse
    import csv
    import sys

    parser = argparse.ArgumentParser(description="Validate the tools.csv file")

    parser.add_argument('tools_csv', help="Path to the tools.csv file from the fmi-standard.org repository")

    args = parser.parse_args()

    problems = []

    tool_names = []
    tool_ids = []

    with open(args.tools_csv, 'r') as csvfile:

        reader = csv.reader(csvfile, delimiter=',', quotechar='"')

        for i, row in enumerate(reader):

            if len(row) != 15:
                problems.append("All rows must have 15 fields")
                break

            if i == 0:
                continue  # skip the header

            tool_name, tool_id, vendor_id = row[:3]

            if tool_name in tool_names:
                problems.append("tool_name '%s' is not unique" % tool_name)
            elif tool_names and tool_name.lower() < tool_names[-1].lower():
                problems.append("tool_name '%s' is not in alphabetical order" % tool_name)

            tool_names.append(tool_name)

            if tool_id in tool_ids:
                problems.append("tool_id '%s' is not unique" % tool_id)

            tool_ids.append(tool_id)

            if row[5] not in ['commercial', 'osi']:
                problems.append("License must be commercial or osi")

            for field in row[7:]:
                if field not in ['', 'available', 'planned']:
                    problems.append("Capabilities must be planned, available or empty")

    print("%d problems found in %s" % (len(problems), args.tools_csv))

    for problem in problems:
        print()
        print(problem)

    sys.exit(len(problems))
