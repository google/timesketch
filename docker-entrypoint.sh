#!/bin/bash

# Run the container the default way
if [ "$1" = 'timesketch' ]; then
	# Set SECRET_KEY in /etc/timesketch.conf if it isn't already set
	if grep -q "SECRET_KEY = u''" /etc/timesketch.conf; then
		OPENSSL_RAND=$( openssl rand -base64 32 )
		# Using the pound sign as a delimiter to avoid problems with / being output from openssl
		sed -i 's#SECRET_KEY = u\x27\x27#SECRET_KEY = u\x27'$OPENSSL_RAND'\x27#' /etc/timesketch.conf
	fi

	# Set up the Postgres connection
	if [ $POSTGRES_USER ] && [ $POSTGRES_PASSWORD ] && [ $POSTGRES_ADDRESS ] && [ $POSTGRES_PORT ]; then
		sed -i 's#postgresql://<USERNAME>:<PASSWORD>#postgresql://'$POSTGRES_USER':'$POSTGRES_PASSWORD'@'$POSTGRES_ADDRESS':'$POSTGRES_PORT'#' /etc/timesketch.conf
	else
		# Log an error since we need the above environment variables
		echo "Please pass values for the POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_ADDRESS, and POSTGRES_PORT environment variables"
		exit 1
	fi

	echo $(grep "postgresql://" /etc/timesketch.conf)

	# Set up the Elastic connection
	if [ $ELASTIC_ADDRESS ] && [ $ELASTIC_PORT ]; then
		sed -i 's#ELASTIC_HOST = u\x27127.0.0.1\x27#ELASTIC_HOST = u\x27'$ELASTIC_ADDRESS'\x27#' /etc/timesketch.conf
		sed -i 's#ELASTIC_PORT = 9200#ELASTIC_PORT = '$ELASTIC_PORT'#' /etc/timesketch.conf
	else
		# Log an error since we need the above environment variables
		echo "Please pass values for the ELASTIC_ADDRESS and ELASTIC_PORT environment variables"
		exit 1
	fi

	# Set up the first Timesketch user
	if [ $TIMESKETCH_USER ] && [ $TIMESKETCH_PASSWORD ]; then
		tsctl add_user -u "$TIMESKETCH_USER" -p "$TIMESKETCH_PASSWORD"
	else
		# Log an error since we need the above environment variables
		echo "Please pass values for the TIMESKETCH_USER and TIMESKETCH_PASSWORD environment variables"
		exit 1
	fi

	# Run the Timesketch server (without SSL)
	exec `tsctl runserver -h 0.0.0.0 -p 5000`
fi

# Run a custom command on container start
exec "$@"
