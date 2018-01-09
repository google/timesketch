#!/bin/bash

# Run the container the default way
if [ "$1" = 'timesketch' ]; then
	# Set SECRET_KEY in /etc/timesketch.conf if it isn't already set
	if grep -q "SECRET_KEY = u'<KEY_GOES_HERE>'" /etc/timesketch.conf; then
		OPENSSL_RAND=$( openssl rand -base64 32 )
		# Using the pound sign as a delimiter to avoid problems with / being output from openssl
		sed -i 's#SECRET_KEY = u\x27\x3CKEY_GOES_HERE\x3E\x27#SECRET_KEY = u\x27'$OPENSSL_RAND'\x27#' /etc/timesketch.conf
	fi

	# Set up the Postgres connection
	if [ $POSTGRES_USER ] && [ $POSTGRES_PASSWORD ] && [ $POSTGRES_ADDRESS ] && [ $POSTGRES_PORT ]; then
		sed -i 's#postgresql://<USERNAME>:<PASSWORD>@localhost#postgresql://'$POSTGRES_USER':'$POSTGRES_PASSWORD'@'$POSTGRES_ADDRESS':'$POSTGRES_PORT'#' /etc/timesketch.conf
	else
		# Log an error since we need the above-listed environment variables
		echo "Please pass values for the POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_ADDRESS, and POSTGRES_PORT environment variables"
		exit 1
	fi

	# Set up the Elastic connection
	if [ $ELASTIC_ADDRESS ] && [ $ELASTIC_PORT ]; then
		sed -i 's#ELASTIC_HOST = u\x27127.0.0.1\x27#ELASTIC_HOST = u\x27'$ELASTIC_ADDRESS'\x27#' /etc/timesketch.conf
		sed -i 's#ELASTIC_PORT = 9200#ELASTIC_PORT = '$ELASTIC_PORT'#' /etc/timesketch.conf
	else
		# Log an error since we need the above-listed environment variables
		echo "Please pass values for the ELASTIC_ADDRESS and ELASTIC_PORT environment variables"
	fi

	# Replace Redis Hostname
	sed -i "s#^CELERY_BROKER_URL=.*#CELERY_BROKER_URL='redis://redis:6379'#" /etc/timesketch.conf
	sed -i "s#^CELERY_RESULT_BACKEND=.*#CELERY_RESULT_BACKEND='redis://redis:6379'#" /etc/timesketch.conf

	# Set up web credentials
	if [ -z ${TIMESKETCH_USER+x} ]; then
		TIMESKETCH_USER="admin"
		echo "TIMESKETCH_USER set to default: ${TIMESKETCH_USER}";
	fi
	if [ -z ${TIMESKETCH_PASSWORD+x} ]; then
		TIMESKETCH_PASSWORD="$(openssl rand -base64 32)"
		echo "TIMESKETCH_PASSWORD set randomly to: ${TIMESKETCH_PASSWORD}";
	fi
        sleep 5
	tsctl add_user -u "$TIMESKETCH_USER" -p "$TIMESKETCH_PASSWORD"


	# Run the Timesketch server (without SSL)
	exec `tsctl runserver -h 0.0.0.0 -p 5000`
fi

# Run a custom command on container start
exec "$@"
