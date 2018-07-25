FROM python:3.7

RUN pip install --upgrade pip
RUN pip install --upgrade google-api-python-client oauth2client

RUN mkdir /fastq /output /project

COPY generate-lims-data.py /project/generate-lims-data.py

VOLUME ["/fastq", "/output"]

WORKDIR /project

ENTRYPOINT ["python", "generate-lims-data.py"]
CMD ["--help"]