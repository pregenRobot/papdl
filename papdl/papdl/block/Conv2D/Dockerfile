
FROM nvcr.io/nvidia/tensorflow:22.05-tf2-py3
 
ARG local_uid
ARG local_user

RUN adduser --uid ${local_uid} --gecos "" --disabled-password ${local_user}

WORKDIR /home/${local_user}

USER ${local_user}

ENV PATH="/home/${local_user}/.local/bin:${PATH}"

RUN mkdir server
WORKDIR /home/${local_user}/server
COPY server.py /home/${local_user}/server/server.py

ENTRYPOINT ["python3", "/home${local_user}/server/server.py"]

