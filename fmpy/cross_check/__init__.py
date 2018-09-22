
def get_vendor_ids(tools_csv):
    """ Get vendor and tool info from tools.csv

    Parameters:
        tools_csv  path to the _data/tools.csv in the fmi-standard.org repository

    Returns:
        a dictionary {vendor_id: (tool_id, tool_name)}
    """

    import csv

    vendors = {}

    with open(tools_csv, 'r') as csvfile:

        reader = csv.reader(csvfile, delimiter=',', quotechar='"')

        next(reader)  # skip the header

        for row in reader:

            tool_name, tool_id, vendor_id = row[:3]

            if vendor_id in vendors:
                vendors[vendor_id].append((tool_id, tool_name))
            else:
                vendors[vendor_id] = [(tool_id, tool_name)]

    return vendors
