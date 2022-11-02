
FROM nvcr.io/nvidia/tensorflow:22.05-tf2-py3
 

USER root
ENV PATH="/root/.local/bin:${PATH}"

RUN mkdir /home/app
WORKDIR /home/app

COPY requirements.txt /home/requirements.txt
RUN pip3 install --user --upgrade pip
RUN pip3 install --user -r /home/requirements.txt

RUN echo $PATH
RUN which watchmedo

# ENTRYPOINT [ "watchmedo", "auto-restart", "--pattern", "*.py", "--recursive", "--signal" "SIGTERM", "--directory", "/home/app", "python3", "/home/app/server.py"]