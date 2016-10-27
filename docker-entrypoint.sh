#!/bin/bash

if [ "$1" = 'timesketch' ]; then
	# Set SECRET_KEY in /etc/timesketch.conf if it isn't already set
	if grep -q "SECRET_KEY = u''" /etc/timesketch.conf; then
		OPENSSL_RAND=${openssl rand -base64 32}
		sed -i 's/SECRET_KEY = u''/SECRET_KEY = u\x27$OPENSSL_RAND\x27/' /etc/timesketch.conf
		cat /etc/timesketch.conf
	fi

	if [ $USER_NAME ] && [ $USER_PASSWORD ]; then
		su -c 'tsctl add_user -u "$USER_NAME" -p "$USER_PASSWORD"' timesketch
	else
		su -c 'tsctl add_user -u demo -p demo' timesketch
	fi

	exec `su -c 'tsctl runserver -h 0.0.0.0' timesketch`
fi

# Run normally with all passed parameters
exec "$@"
