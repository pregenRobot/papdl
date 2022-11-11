FROM nvcr.io/nvidia/tensorflow:22.05-tf2-py3
 

USER root
ENV PATH="/root/.local/bin:${PATH}"

RUN mkdir /home/app
WORKDIR /home/app

# FORWARD RESULT RETURN
EXPOSE 8765

# FORWARD INPUT
EXPOSE 8766

COPY requirements.txt requirements.txt
RUN pip3 install --user --upgrade pip
RUN pip3 install --user -r requirements.txt