FROM tensorflow/tensorflow

ARG local_uid
ARG local_user
RUN adduser --system --uid ${local_uid} --gecos "" --disabled-password ${local_user} 
RUN apt update
RUN apt install -y iperf3 iputils-ping
RUN apt install -y iputils-ping
# USER ${local_user}

ENV PATH="/home/${local_user}/.local/bin:${PATH}"

RUN mkdir /home/${local_user}/model
RUN mkdir /home/${local_user}/app
WORKDIR /home/${local_user}/app
COPY models /home/${local_user}/models
RUN chmod 777 /home/${local_user}/app

ADD app /home/${local_user}/app

# FORWARD INPUT
EXPOSE 8765

COPY requirements.txt requirements.txt

RUN pip install --user --upgrade pip
RUN pip install --user --no-cache-dir -r requirements.txt