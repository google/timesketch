#!/bin/bash

# Run the container in default way
if [ "$1" = 'timesketch' ]; then
	# Set SECRET_KEY in /etc/timesketch.conf if it isn't already set
	if grep -q "SECRET_KEY = u''" /etc/timesketch.conf; then
		OPENSSL_RAND=$( openssl rand -base64 32 )
		# Using the pound sign as a delimiter to avoid problems with / being output from openssl
		sed -i 's#SECRET_KEY = u\x27\x27#SECRET_KEY = u\x27'$OPENSSL_RAND'\x27#' /etc/timesketch.conf
	fi

	if [ $POSTGRES_USER ] && [ $POSTGRES_PASSWORD ] && [ $POSTGRES_ADDRESS ] && [ $POSTGRES_PORT ]; then
		sed -i 's#postgresql://<USERNAME>:<PASSWORD>#postgresql://'$POSTGRES_USER':'$POSTGRES_PASSWORD'@'$POSTGRES_ADDRESS':'$POSTGRES_PORT'#' /etc/timesketch.conf
		tsctl add_user -u "$POSTGRES_USER"
	else
		# Log an error since we need the above-listed environment variables
		echo "Please pass values for the POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_ADDRESS, and POSTGRES_PORT environment variables"
		exit 1
	fi

	# Run the Timesketch server (without SSL)
	exec `tsctl runserver -h 0.0.0.0 -p 5000`
fi

# Run a custom command on container start
exec "$@"
