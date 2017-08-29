### Note: If you are upgrading from a previous Timesketch release, please see the [upgrading guide](Upgrading.md) instead.

# Install Timesketch from scratch

#### Install Ubuntu
This installation guide is based on Ubuntu 16.04LTS Server edition. Follow the installation guide for Ubuntu and install the base system.
After the installation is done, login and update the system.

    $ sudo apt-get update
    $ sudo apt-get dist-upgrade

#### Install Elasticsearch

Install Java

    $ sudo apt-get install openjdk-8-jre-headless
    $ sudo apt-get install apt-transport-https

Install the latest Elasticsearch 2.x release (5.x is not yet supported):

    $ wget https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.4.3/elasticsearch-2.4.3.deb
    $ sudo dpkg -i elasticsearch-2.4.3.deb

**Configure Elasticsearch**

This is up to your specific environment, but if you run elasticsearch on the same host as Timesketch you should lock it down to only listen to localhost.
The configuration for Elasticsearch is located in /etc/elasticsearch/elasticsearch.yml

You need to deploy two Groovy scripts. Copy the following two files to /etc/elasticsearch/scripts/:

    https://raw.githubusercontent.com/google/timesketch/master/contrib/add_label.groovy
    https://raw.githubusercontent.com/google/timesketch/master/contrib/toggle_label.groovy

Make sure that Elasticsearch is started on boot:

    /bin/systemctl daemon-reload
    /bin/systemctl enable elasticsearch.service
    /bin/systemctl start elasticsearch.service

#### Install PostgreSQL

    $ sudo apt-get install postgresql
    $ sudo apt-get install python-psycopg2

**Configure PostgreSQL**

    $ sudo vim /etc/postgresql/9.5/main/pg_hba.conf

Configure PostgreSQL to allow the timesketch user to authenticate and use the database:

    local   all             timesketch                              md5

Then you need to restart PostgreSQL:

    $ sudo /etc/init.d/postgresql restart

#### Install Timesketch

Now it is time to install Timesketch. First we need to install some dependencies:

    $ sudo apt-get install python-pip python-dev libffi-dev

Then install Timesketch itself:

    $ sudo pip install timesketch

**Configure Timesketch**

Copy the configuration file to /etc and configure it. The file is well commented and it should be pretty straight forward.

    $ sudo cp /usr/local/share/timesketch/timesketch.conf /etc/
    $ sudo chmod 600 /etc/timesketch.conf

Generate a secret key and configure SECRET_KEY in /etc/timesketch.conf

    $ openssl rand -base64 32

Create SQL database user and database:

    $ sudo -u postgres createuser -d -P -R -S timesketch
    $ sudo -u postgres createdb -O timesketch timesketch

In the timesketch.conf file, edit the follwing using the username and password you used in the previous step:

    SQLALCHEMY_DATABASE_URI = u'postgresql://<USERNAME>:<PASSWORD>@localhost/timesketch'

Add the first user

    $ tsctl add_user -u <username>

Start the HTTP server (**NOTE: This is unencrypted. Use SSL for production deployments**):

    $ tsctl runserver -h 0.0.0.0 -p 5000

Go to http://<SERVER IP>:5000/
