FROM debian:8

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install github3.py
RUN pip3 install cherrypy
RUN useradd ghrc -r -d /opt/grc/ -s /bin/bash
RUN mkdir /opt/ghrc/
RUN chown -R ghrc:ghrc /opt/ghrc/
COPY . /opt/code
WORKDIR /opt/code
USER ghrc
CMD python3 /opt/code/ghrc.py
