
if [ $1 = "test" ]; then
    docker run -v $(pwd)/share:/home/$USER/papdl/share --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 --runtime=nvidia --user $(id -u):$(id -g) --rm -it tf2-papdl pytest --disable-pytest-warnings
fi

if [ $1 = "bash" ]; then
    docker run -v $(pwd)/share:/home/$USER/papdl/share --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 --runtime=nvidia --user $(id -u):$(id -g) --rm -it tf2-papdl bash
fi

if [ $1 = "build" ]; then
    docker build --build-arg local_uid=$(id -u) --build-arg local_user=$USER -t tf2-papdl .
fi

if [ $1 = "run" ]; then
    docker run -v $(pwd)/share:/home/$USER/papdl/share --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 --runtime=nvidia --user $(id -u):$(id -g) --rm -it tf2-papdl python3 /home/$USER/papdl/tests/test_dev.py
fi