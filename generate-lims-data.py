from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from glob import glob
from datetime import datetime
import os
import argparse
import re
import csv

# TODO: could do with better structure (functions, modules, etc)

# compile regex patterns
run_id_pattern = re.compile('(\d{6})_A\d{5}_(\d{4})_[A,B].{9}')
sample_pattern = re.compile('((.+?)_S\d+)_R[1,2]_\d{3}.fastq.gz')

# argument parsing
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                 description='Generate data for LIMS spreadsheet.')
parser.add_argument('runId',
                    help="The run ID / Illumina ID / runfolder name.")
parser.add_argument('--use-case',
                    default='CSV',
                    help="What to do with the data. Allowed values: CSV, GOOGLE.")
parser.add_argument('--dest-dir',
                    default='/data/cephfs/punim0010/data/Pipeline/prod/Fastq',
                    help="The destination base path (depends on HPC env).")
parser.add_argument('--bcl2fastq-outdir',
                    default='/fastq',
                    help="The source path (where to find the bcl2fastq output).")
parser.add_argument('--csv-outdir',
                    default='/output',
                    help="Where to write the CSV output file to.")
parser.add_argument('--spreadsheet-id',
                    default='1Jh1O7UhDK9ES1kYQI1xg_Rj9gx_FcMKINS8qpwgYY2s',
                    help="The ID of the Google spreadsheet to update.")
parser.add_argument('--token-file',
                    default='/creds/token.json',
                    help="The access token file to use for accessing the Google spreadsheet.")
parser.add_argument('--credentials-file',
                    default='/creds/credentials.json',
                    help="The credentials to use to authenticate against Google.")
args = parser.parse_args()


# extract date and run number from run ID
run_match = re.match(run_id_pattern, args.runId)
if not run_match:
    # TODO: error handling
    print("Provided run ID (%s) not formatted as expected. Aborting!" % args.runId)
    exit()
run_timestamp = datetime.strptime(run_match.group(1), '%y%m%d').strftime('%Y-%m-%d')
run_number = int(run_match.group(2))


# start building the data rows
print("Fastq base dir: %s" % args.bcl2fastq_outdir)
rows = []
# find all fastq directories and all FASTQs within them and for each add a data row
fastq_paths = [p[:-1] for p in glob(os.path.join(args.bcl2fastq_outdir, args.runId + '*/'))]
print(fastq_paths)

for fastq_dir in fastq_paths:
    fastq_dir_name = os.path.basename(fastq_dir)
    fastq_files = glob(os.path.join(fastq_dir, '*.fastq.gz'))
    for fastq_file in fastq_files:
        fastq_filename = os.path.basename(fastq_file)
        sample_match = re.match(sample_pattern, fastq_filename)
        if sample_match:
            sample_id = sample_match.group(1)
            sample_name = sample_match.group(2)
        else:
            # TODO: error handling
            print("Could not parse sample name/id from FASTQ filename (%s)!" % fastq_filename)
            sample_id = ''
            sample_name = ''
        dest_loc = os.path.join(args.dest_dir, args.runId, fastq_dir_name)
        if sample_name == 'Undetermined':
            continue
        value_field = [args.runId, run_number, run_timestamp, sample_id, sample_name,
                       '', '', '', '', dest_loc, '', '', '']
        rows.append(value_field)

print('Generated data rows:')
print(rows)

if args.use_case == 'CSV':
    ################################################################################
    # In case we want to write a CSV ouptut file

    output_file = os.path.join(args.csv_outdir, args.runId + '-sheet.csv')
    print("Writing CSV file: %s" % output_file)

    with open(output_file, 'w', newline='') as csvfile:
        sheetwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        sheetwriter.writerow(["IlluminaID", "Run", "Timestamp", "SampleID", "SampleName", "Project",
                              "SubjectID", "Type", "Phenotype", "FASTQ", "Results", "Trello", "Notes"])
        for row in rows:
            sheetwriter.writerow(row)

    print("All done.")

elif args.use_case == 'GOOGLE':
    ################################################################################

    # in case we want to write to a Google Spreadsheet
    # TODO: spreadsheet_id could be argument
    spreadsheet_id = args.spreadsheet_id
    spreadsheet_range = "Sheet1!A1:N1"
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
    token_file = args.token_file
    credentials_file = args.credentials_file

    # start building the json payload to send to the Google SpreadSheet
    print("Updating Google spreadsheet %s" % spreadsheet_id)
    data = {}
    data['range'] = spreadsheet_range
    data['majorDimension'] = 'ROWS'
    data['values'] = rows

    # create custom ArgumentParser to overwrite the default
    g_parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])
    g_flags = g_parser.parse_args(['--noauth_local_webserver'])

    store = file.Storage(token_file)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(credentials_file, SCOPES)
        creds = tools.run_flow(flow, store, flags=g_flags)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API
    result = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id,
                                                    range=spreadsheet_range,
                                                    body=data,
                                                    valueInputOption='RAW').execute()

    print('SpreadSheet updated:' + result['spreadsheetId'])
    print('TableRange: ' + result['tableRange'])
    print('Updated rows: ' + str(result['updates']['updatedRows']))
    print('Updated range: ' + result['updates']['updatedRange'])
    print(result)

else:
    print("Unsupported use case: %s!" % args.use_case)
