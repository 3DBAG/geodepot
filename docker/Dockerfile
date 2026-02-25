FROM ubuntu:22.04

RUN apt-get update && apt-get install -y nginx openssh-server && rm -rf /var/lib/apt/lists/*

COPY nginx_server.conf /etc/nginx/sites-available/geodepot.conf
RUN ln -s /etc/nginx/sites-available/geodepot.conf /etc/nginx/sites-enabled/geodepot.conf \
    && rm /etc/nginx/sites-enabled/default

RUN mkdir -p /srv/geodepot /run/sshd /root/.ssh
RUN chmod 700 /root/.ssh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 22
ENTRYPOINT ["/entrypoint.sh"]
