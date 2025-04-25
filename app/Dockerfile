#
# Run the pmaxperfpy script inside a docker container
#
FROM python:3.12-slim
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY . /pmaxperfpy
EXPOSE  8080
WORKDIR /pmaxperfpy
ENTRYPOINT [ "/pmaxperfpy/pmaxperf.py" ]
