FROM nvcr.io/nvidia/tensorflow:22.05-tf2-py3
 
ARG local_uid
ARG local_user

RUN adduser --uid ${local_uid} --gecos "" --disabled-password ${local_user}

WORKDIR /home/${local_user}

USER ${local_user}

ENV PATH="/home/${local_user}/.local/bin:${PATH}"

RUN mkdir ./papdl
COPY requirements.txt ./papdl/requirements.txt
COPY tests ./papdl/tests
COPY papdl ./papdl/papdl
RUN mkdir ./papdl/share
WORKDIR /home/${local_user}/papdl

RUN pip install --user --upgrade pip

RUN pip install --user --no-cache-dir -r requirements.txt

