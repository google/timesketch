#!/bin/bash

if [ "$1" = 'timesketch' ]; then
	# Set SECRET_KEY in /etc/timesketch.conf if it isn't already set
	if grep -q "SECRET_KEY = u''" /etc/timesketch.conf; then
		OPENSSL_RAND=$( openssl rand -base64 32 )
		sed -i 's/SECRET_KEY = u\x27\x27/SECRET_KEY = u\x27'$OPENSSL_RAND'\x27/' /etc/timesketch.conf
	fi

	if [ $USER_NAME ] && [ $USER_PASSWORD ]; then
		tsctl add_user -u "$USER_NAME" -p "$USER_PASSWORD"
	else
		tsctl add_user -u demo -p demo
	fi

	# Run the Timesketch server (without SSL)
	exec `tsctl runserver -h 0.0.0.0 -p 5000`
fi

# Run normally with all passed parameters
exec "$@"
