
docker build --build-arg local_uid=$(id -u) --build-arg local_user=$USER -t tf2-custom .
docker run --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 --runtime=nvidia --user $(id -u):$(id -g) --rm -it tf2-custom bash