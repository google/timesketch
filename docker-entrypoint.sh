#!/bin/bash

# Run the container in default way
if [ "$1" = 'timesketch' ]; then
	# Set SECRET_KEY in /etc/timesketch.conf if it isn't already set
	if grep -q "SECRET_KEY = u''" /etc/timesketch.conf; then
		OPENSSL_RAND=$( openssl rand -base64 32 )
		# Using the pound sign as a delimiter to avoid problems with / being output from openssl
		sed -i 's#SECRET_KEY = u\x27\x27#SECRET_KEY = u\x27'$OPENSSL_RAND'\x27#' /etc/timesketch.conf 
	fi

	if [ $USER_NAME ] && [ $USER_PASSWORD ]; then
		sed -i 's/postgresql:\/\/<USERNAME>:<PASSWORD>/postgresql:\/\/'$USER_NAME':'$USER_PASSWORD'/' /etc/timesketch.conf
		tsctl add_user -u "$USER_NAME" 
	else
		sed -i 's/postgresql:\/\/<USERNAME>:<PASSWORD>/postgresql:\/\/demo:demo/' /etc/timesketch.conf
		tsctl add_user -u demo
	fi

	# Run the Timesketch server (without SSL)
	exec `tsctl runserver -h 0.0.0.0 -p 5000`
fi

# Run a custom command on container start
exec "$@"
