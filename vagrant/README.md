# Vagrant

NOTE: Due to a bug with Yarn and Vagrant on Windows, Windows is not supported at the moment. Please use Linux or MacOS as host.

Timesketch has support for Vagrant. This is a convenient way of getting up and running with Timesketch development, or just to test Timesketch.

1. Install VirtualBox for your operating system
2. Install Vagrant for your operating system
3. Clone the Timesketch repository
4. Create your Timesketch box

### Install VirtualBox
Follow the official instructions [here](https://www.virtualbox.org/wiki/Downloads)

### Install Vagrant
Follow the official instructions [here](https://www.vagrantup.com/docs/installation/)

### Clone Timesketch
    $ git clone https://github.com/google/timesketch.git

### Create Timesketch Vagrant box
    $ cd timesketch/vagrant
    $ vagrant plugin install vagrant-disksize
    $ vagrant up
    .. wait until the installation process is complete
    $ vagrant ssh
    $ tsctl runserver -h 0.0.0.0

### Access Timesketch
* Got to: http://127.0.0.1:5000/
* Login: spock/spock

### How to test your installation
1. You can now create your first sketch by pressing the green button on the middle of the page
2. Add the test timeline under the [Timeline](http://127.0.0.1:5000/sketch/1/timelines/) tab in your new sketch
3. Go to http://127.0.0.1:5000/explore/ and have fun exploring!

## Development
The Timesketch source is installed in development mode (using pip install -e ..) so you can use your favourite text editor to edit the source code and it will be automatically reflected in your Vagrant box.
