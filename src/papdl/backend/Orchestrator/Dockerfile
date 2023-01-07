FROM tensorflow/tensorflow
 
ARG local_uid
ARG local_user

RUN adduser --uid ${local_uid} --gecos "" --disabled-password ${local_user}

USER ${local_user}
ENV PATH="/home/${local_user}/.local/bin:${PATH}"

RUN mkdir /home/${local_user}/app
WORKDIR /home/${local_user}/app

# FORWARD RESULT RETURN
EXPOSE 8765

# FORWARD INPUT
EXPOSE 8766

COPY requirements.txt requirements.txt
RUN pip install --user --upgrade pip
RUN pip install --user --no-cache-dir -r requirements.txt