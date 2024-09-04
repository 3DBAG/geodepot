#!/usr/bin/env bash

apt-get update
apt-get install -y nginx

sudo cp /vagrant/vagrant/nginx_server.conf /etc/nginx/sites-available/geodepot.conf
sudo chmod 644 /etc/nginx/sites-available/geodepot.conf
if ! [ -f /etc/nginx/sites-enabled/geodepot.conf ]; then
  sudo ln -s /etc/nginx/sites-available/geodepot.conf /etc/nginx/sites-enabled/geodepot.conf
fi

sudo rm /etc/nginx/sites-available/default
sudo rm /etc/nginx/sites-enabled/default

sudo service nginx restart
