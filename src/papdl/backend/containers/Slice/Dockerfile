FROM tensorflow/tensorflow

ARG local_uid
ARG local_user
# ARG model

RUN adduser --uid ${local_uid} --gecos "" --disabled-password ${local_user}

RUN apt update -y
RUN apt install -y iputils-ping
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
RUN apt-get install -y nodejs
RUN npm install --global wscat

USER ${local_user}
ENV PATH="/home/${local_user}/.local/bin:${PATH}"

RUN mkdir /home/${local_user}/model
RUN mkdir /home/${local_user}/app
WORKDIR /home/${local_user}/app

ADD app /home/${local_user}/app

# FORWARD INPUT
EXPOSE 8765

COPY requirements.txt requirements.txt
RUN pip install --user --upgrade pip
RUN pip install --user --no-cache-dir -r requirements.txt
COPY model /home/${local_user}/model