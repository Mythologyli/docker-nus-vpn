FROM python:3.12-slim-bookworm

COPY ./ /app
WORKDIR /app

# Install iputils-ping
RUN apt update && apt install -y iputils-ping

# Install gost
RUN apt install -y wget && wget https://github.com/go-gost/gost/releases/download/v3.0.0/gost_3.0.0_linux_amd64.tar.gz
RUN tar -xvf gost_3.0.0_linux_amd64.tar.gz

# Install openconnect
RUN apt install -y openconnect

# Install requirements
RUN pip install -r requirements.txt --break-system-packages

ENV VPN_HOST_TO_PING="sm05.stf.nus.edu.sg"
ENV GOST_PARAMS="-L socks5://:10800"

ENTRYPOINT ["bash", "entrypoint.sh"]
