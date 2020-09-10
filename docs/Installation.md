### Note: If you are upgrading from a previous Timesketch release, please see the [upgrading guide](Upgrading.md) instead.

# Install Timesketch from scratch

NOTE: It is not recommended to try to run on a system with less than 8 GB of RAM.

#### Install Ubuntu

This installation guide is based on Ubuntu 18.04LTS Server edition. Follow the installation guide for Ubuntu and install the base system.
After the installation is done, login and update the system.

    $ sudo apt-get update
    $ sudo apt-get dist-upgrade

#### Install Elasticsearch

Install apt-get HTTPS support

    $ sudo apt-get install apt-transport-https

Install the latest Elasticsearch 7 release:

    $ sudo wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
    $ sudo echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
    $ sudo apt-get update
    $ sudo apt-get install elasticsearch

**Configure Elasticsearch**

This is up to your specific environment, but if you run elasticsearch on the same host as Timesketch you should lock it down to only listen to localhost.
The configuration for Elasticsearch is located in `/etc/elasticsearch/elasticsearch.yml`

Make sure that Elasticsearch is started on boot:

    /bin/systemctl daemon-reload
    /bin/systemctl enable elasticsearch.service
    /bin/systemctl start elasticsearch.service

Make sure that Elasticsearch is running:

    /bin/systemctl status elasticsearch.service

#### Install PostgreSQL

    $ sudo apt-get install postgresql python3-psycopg2

**Configure PostgreSQL**

    $ sudo vim /etc/postgresql/10/main/pg_hba.conf

Configure PostgreSQL to allow the timesketch user to authenticate and use the database:

    local   all             timesketch                              md5

Then you need to restart PostgreSQL:

    $ sudo /etc/init.d/postgresql restart

Create the Timesketch PostgreSQL database and user:

    $ sudo -u postgres createuser -d -P -R -S timesketch
    $ sudo -u postgres createdb -O timesketch timesketch

#### Install Timesketch

Now it is time to install Timesketch. First we need to install some dependencies:

    $ sudo apt-get install python3-pip python3-dev libffi-dev

Then install Timesketch itself:

    $ sudo pip3 install timesketch

**Configure Timesketch**

Copy the configuration file to `/etc/timesketch/` and configure it. The file is well commented and it should be pretty straight forward.

    $ mkdir /etc/timesketch
    $ sudo cp /usr/local/share/timesketch/timesketch.conf /etc/timesketch/
    $ sudo chmod 600 /etc/timesketch/timesketch.conf

Generate a secret key and configure `SECRET_KEY` in `/etc/timesketch/timesketch.conf`

    $ openssl rand -base64 32

In the timesketch.conf file, edit the following using the username and password you used in the previous step:

    SQLALCHEMY_DATABASE_URI = u'postgresql://<USERNAME>:<PASSWORD>@localhost/timesketch'

Add the first user

    $ tsctl add_user -u <username>

Start the HTTP server (**NOTE: This is unencrypted. Use SSL for production deployments**):

    $ tsctl runserver -h 0.0.0.0 -p 5000

Go to `http://<SERVER IP>:5000/`
