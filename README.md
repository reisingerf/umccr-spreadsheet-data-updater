# umccr-spreadsheet-data-updater

A Python script (and accompanying Dockerfile) to generate spreadsheet rows for the UMCCR Samples spreadsheet.

Data is generated from the bcl2fastq output for a specific Illumina run ID.

The script is invoked with a `runID`. It will then scan for bcl2fasta output directories (name being or starting with the run ID) in the configurabnle `bcl2fastq-outdir` location.
For each found `.fastq.gz` file it create a row record for the spreadsheet trying to parse information our of the run ID and FASTQ file name.

The generated data rows can then be written to a CSV file or directly appended to a Google Spreadsheet. The first `use-case` (`CSV`) requires an output location, whereas the second case (`GOOGLE`) requires Google access credentials to the spreadsheet (Google sheets API).

Example use cases (where local/usdu is the Docker container build from the Dockerfile):

```bash
# assumes CSV as default use case
docker run --rm -v /tmp/foo/fastq_base/:/fastq -v /tmp/foo/output/:/output local/usdu:latest 180718_A00130_0067_AH5M5MDSXX
```

```bash
# requires Google credentials
docker run --rm -v /tmp/google-credsdentials-dir/:/creds -v /tmp/fastq-base-dir/:/fastq local/usdu:latest 180718_A00130_0067_AH5M5MDSXX --use-case GOOGLE
```
