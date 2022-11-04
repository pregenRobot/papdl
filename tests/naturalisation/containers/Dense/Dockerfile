
FROM nvcr.io/nvidia/tensorflow:22.05-tf2-py3
 

USER root
ENV PATH="/root/.local/bin:${PATH}"

RUN mkdir /home/app
RUN mkdir /home/model
WORKDIR /home

COPY requirements.txt requirements.txt
RUN pip3 install --user --upgrade pip
RUN pip3 install --user -r requirements.txt