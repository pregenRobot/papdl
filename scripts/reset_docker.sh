#! /bin/bash

docker system prune -ay
docker stop $(docker ps -a -q)
docker rm -f $(docker ps -a -q)
docker volume prune -y
docker rmi -f $(docker images -a -q)
