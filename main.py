# Concordia Genome Foundry
# author: Flavia Araujo
# date: February 25th, 2026
# Main script to process Echo 550 XML files and generate CSVs for skipped wells

import configparser
import csv
import operator
import os
import sys
from datetime import datetime
from xml.dom import minidom


class TerminalColor:
    ERROR = '\033[91m' # RED
    PASS = '\033[92m' # GREEN
    WARNING = '\033[93m' # YELLOW
    RESET = '\033[0m'


config_file = 'config.ini'

# Check if config.ini file exists, if not create one with default values and exit the program
if not os.path.isfile(config_file):
    config = configparser.ConfigParser()
    config['Paths'] = {
        'input_dir': '/path/to/input/directory',
        'output_dir': '/path/to/output/directory'
    }
    with open(config_file, 'w') as f:
        config.write(f)
    print(f'{TerminalColor.ERROR}Error: config.ini file not found. A new config.ini has been created. Please fill in input_dir and output_'
          'dir and re-run the script.')
    sys.exit(1)

config = configparser.ConfigParser()
config.read(config_file)

input_dir = config['Paths']['input_dir']
output_dir = config['Paths']['output_dir']


def create(filename, mode):
    """Create and return new file object."""
    return open(filename, mode)


def create_writer_csv(newfile):
    """Create and return a CSV writer object for the given file."""
    return csv.writer(newfile, dialect='excel')


def print_csv_files(filepath, files_output):
    """
    Write output lists to CSV files in output_dir.
    Returns a list of created filenames.
    """
    filenames = []
    for list_file in files_output:
        filename = 'echo_' + str(datetime.now().strftime("%Y%m%d-%H%M%S.%f")) + '.csv'
        file_path = os.path.join(output_dir, filename)
        with open(file_path, 'w', newline='') as file:
            csv_file = csv.writer(file, dialect='excel')
            header = 'file', 'source_barcode', 'source_well', 'destination_barcode', 'destination_well', \
                     'actual_vol_transferred', 'volume_transferred'
            csv_file.writerow(header)
            sorted_list_file = sorted(list_file, key=operator.itemgetter(1))
            for well in sorted_list_file:
                csv_file.writerow(well)
        filenames.append(filename)
    return filenames


def list_group_files(files_skippedwells):
    """
    Group files by time difference (<30min).
    Returns a list of grouped file info.
    """
    sorted_files_skippedwells = sorted(files_skippedwells, key=operator.itemgetter(2))
    file, num_skippedwells, start_date = sorted_files_skippedwells[0]

    group_files_list = []
    actual_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S.%f')
    count = 1
    for file_list in sorted_files_skippedwells:
        file, num_skippedwells, file_date = file_list
        obj_file_date = datetime.strptime(file_date, '%Y-%m-%d %H:%M:%S.%f')
        difference = obj_file_date - actual_date

        '''Check if the time between files less then 30min'''
        if difference.seconds < 1800:
            list = count, file, num_skippedwells, file_date
            group_files_list.append(list)
        else:
            count += 1
            list = count, file, num_skippedwells, file_date
            group_files_list.append(list)
        actual_date = obj_file_date

    return group_files_list


def print_skippedwells_list(filepath, group_files_list):
    """
    Parse XML files in each group and collect skipped wells info.
    Returns a list of lists for CSV output.
    """
    actual_group = 1
    file_output = []
    files_output = []
    for xml in group_files_list:
        file_group = xml[0]
        xml_file = xml[1]
        num_skippedwells = int(xml[2])
        file_datetime = xml[3]

        if file_group == actual_group:
            xmldoc = minidom.parse(os.path.join(filepath, xml_file))

            w = xmldoc.getElementsByTagName('w')
            skippedwells = xmldoc.getElementsByTagName('skippedwells')
            printmap = xmldoc.getElementsByTagName('printmap')
            transfer = xmldoc.getElementsByTagName('transfer')
            platebarcode = xmldoc.getElementsByTagName('plate')

            plate_source_barcode = platebarcode[0].attributes['barcode'].value
            plate_destination_barcode = platebarcode[1].attributes['barcode'].value
            date = transfer[0].attributes['date'].value
            num_skippedwells = int(skippedwells[0].attributes['total'].value)
            num_printmapwells = int(printmap[0].attributes['total'].value)

            for i in range(0 + num_printmapwells, num_skippedwells + num_printmapwells):
                source_well = w[i].attributes['n'].value
                destination_well = w[i].attributes['dn'].value
                actual_vol_transferred = w[i].attributes['avt'].value
                volume_transferred = w[i].attributes['vt'].value
                file_output.append([xml_file, plate_source_barcode, source_well, plate_destination_barcode, destination_well, actual_vol_transferred, volume_transferred])
        else:
            actual_group = file_group
            files_output.append(file_output)
            file_output = []
            xmldoc = minidom.parse(os.path.join(filepath, xml_file))
            w = xmldoc.getElementsByTagName('w')
            skippedwells = xmldoc.getElementsByTagName('skippedwells')
            printmap = xmldoc.getElementsByTagName('printmap')
            transfer = xmldoc.getElementsByTagName('transfer')
            platebarcode = xmldoc.getElementsByTagName('plate')

            plate_source_barcode = platebarcode[0].attributes['barcode'].value
            plate_destination_barcode = platebarcode[1].attributes['barcode'].value
            date = transfer[0].attributes['date'].value
            num_skippedwells = int(skippedwells[0].attributes['total'].value)
            num_printmapwells = int(printmap[0].attributes['total'].value)

            for i in range(0 + num_printmapwells, num_skippedwells + num_printmapwells):
                source_well = w[i].attributes['n'].value
                destination_well = w[i].attributes['dn'].value
                actual_vol_transferred = w[i].attributes['avt'].value
                volume_transferred = w[i].attributes['vt'].value
                file_output.append([xml_file, plate_source_barcode, source_well, plate_destination_barcode, destination_well, actual_vol_transferred, volume_transferred])
    files_output.append(file_output)
    return files_output


def check_barcode_skippedwells(filepath, xml_files, barcode, s_or_d):
    """
    Check XML files for skipped wells matching barcode and created today.
    Returns lists of files with skipped wells and print results.
    """
    today = datetime.now()
    files_skippedwells = []
    empty_files = []
    print_result = []
    for xml in xml_files:
        try:
            xmldoc = minidom.parse(os.path.join(filepath, xml))
            skippedwells = xmldoc.getElementsByTagName('skippedwells')
            platebarcode = xmldoc.getElementsByTagName('plate')
            transfer = xmldoc.getElementsByTagName('transfer')

            num_skippedwells = int(skippedwells[0].attributes['total'].value)
            plate_barcode = platebarcode[s_or_d].attributes['barcode'].value
            date = transfer[0].attributes['date'].value

            obj_file_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
            dif_time = today - obj_file_date

            if num_skippedwells > 0 and barcode == plate_barcode and dif_time.days < 1:
                files_skippedwells.append([xml, num_skippedwells, date])
            elif num_skippedwells == 0 and barcode == plate_barcode and dif_time.days < 1:
                print_result.append([str(xml) + ' with ' + str(barcode) + ' has 0 skippedwells.'])
        except Exception as e:
            empty_files.append(xml)
            print(f'{TerminalColor.ERROR}Error processing file {xml}: {e}')
    return files_skippedwells, print_result


def get_xml_files(path):
    """
    List all XML files in the directory containing 'PrintResult'.
    Returns a filtered list of filenames.
    """
    list_all_files = os.listdir(path)
    filtered_files = []
    for file in list_all_files:
        if file.endswith(".xml") and 'PrintResult' in file:
            filtered_files.append(file)
    return filtered_files


def print_help():
    print(f'{TerminalColor.RESET}'
        "Echo Print Check\n"
        "Usage:\n"
        "  .\echo_print_check.exe <source_or_destination> <barcode>\n\n"
        "Parameters:\n"
        "  <source_or_destination>   0 for source plate, 1 for destination plate\n"
        "  <barcode>                 Plate barcode to verify\n\n"
        "Example:\n"
        "  .\echo_print_check.exe 0 GF00001\n"
        "  .\echo_print_check.exe 1 GF12345\n\n"
        "Configuration:\n"
        "  Set input_dir and output_dir in config.ini before running.\n"
    )


def main(argv):
    """
    Main entry point. Parses arguments and processes XML files.
    """
    if len(argv) > 0 and argv[0] in ('-h', '--help', 'help'):
        print_help()
        sys.exit(0)
    if len(sys.argv) > 2:
        source_or_destination = int(sys.argv[1])
        barcode = str(sys.argv[2])
        plate_type = "source" if source_or_destination == 0 else "destination"
        print(f'{TerminalColor.PASS}Verifying {plate_type} plate with barcode: {barcode}')
        filepath = input_dir

        # Get all xml files with Print Result
        xml_files = get_xml_files(filepath)

        # Filter the files created today with skipped wells > 0 and the barcode
        if len(xml_files) > 0:
            files_skippedwells, print_result = check_barcode_skippedwells(filepath, xml_files, barcode, source_or_destination)

            if len(files_skippedwells) > 0:
                group_files_list = list_group_files(files_skippedwells)
                files_output = print_skippedwells_list(filepath, group_files_list)
                filenames = print_csv_files(filepath, files_output)
                print(f'{TerminalColor.PASS}CSV files created for skipped wells: {filenames}')
                sys.exit(1) # Return 1 if files created with skipped wells > 0
            else:
                if len(print_result) > 0:
                    for result in print_result:
                        print(result)
                else:
                    print(f'{TerminalColor.PASS}Barcode {barcode} not found in any .xml files')
                sys.exit(0)

        else:
            print(f'{TerminalColor.ERROR}Error: No .xml files found. Please verify the input_dir path in config.ini file.')
            sys.exit(1)
    else:
        print(f'{TerminalColor.ERROR}Error: Missing arguments.\n')
        print_help()
        sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
