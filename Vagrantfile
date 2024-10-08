Vagrant.require_version ">= 2.4.1"

Vagrant.configure("2") do |config|
  config.vm.provision "shell", inline: "echo Hello"
  config.vm.provider "virtualbox" do |v|
      v.check_guest_additions = false
  end

  config.vm.define "server" do |server|
    server.vm.box = "ubuntu/jammy64"
    server.vm.hostname = "geodepot-remote.vagrant"
    server.vm.network "private_network",
        ip: "192.168.56.5", hostname: true
    server.vm.provision :shell,
        path: "vagrant/bootstrap_server.sh"
    server.vm.provision "file",
        source: "~/.ssh/id_rsa.pub", destination: "/home/vagrant/.ssh/me.pub"
    server.vm.provision 'shell', inline: 'mkdir -p /root/.ssh'
    server.vm.provision 'shell', inline: "cat /home/vagrant/.ssh/me.pub >> /root/.ssh/authorized_keys"
    server.vm.provision 'shell', inline: "cat /home/vagrant/.ssh/me.pub >> /home/vagrant/.ssh/authorized_keys", privileged: false
    server.vm.synced_folder "tests/data/integration/server", "/srv/geodepot",
        owner: "vagrant", group: "vagrant"
  end

  config.vm.define "client0" do |client0|
    client0.vm.box = "ubuntu/jammy64"
    client0.vm.synced_folder "tests/data/sources", "/home/vagrant/data"
    client0.vm.synced_folder "tests/data/integration/client0", "/home/vagrant/geodepot-repository",
        owner: "vagrant", group: "vagrant"
  end

  config.vm.define "client1" do |client1|
    client1.vm.box = "ubuntu/jammy64"
    client1.vm.synced_folder "tests/data/sources", "/home/vagrant/data"
    client1.vm.synced_folder "tests/data/integration/client1", "/home/vagrant/geodepot-repository",
        owner: "vagrant", group: "vagrant"
  end
end
