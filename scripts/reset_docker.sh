#! /bin/bash

docker system prune -ay
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker volume prune -y
docker rmi $(docker images -a -q)
