
if [ $1 = "test" ]; then
    docker run -v $(pwd)/share:/home/$USER/papdl/share --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 --runtime=nvidia --user $(id -u):$(id -g) --rm -it tf2-papdl pytest
fi

if [ $1 = "bash" ]; then
    docker run -v $(pwd)/share:/home/$USER/papdl/share --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 --runtime=nvidia --user $(id -u):$(id -g) --rm -it tf2-papdl bash
fi
