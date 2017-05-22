# akita.py
A simple, lightweight event-driven network device drop-off and reconnection
tool for hacking home network devices.

For example, you can program your network connected lighting to come on if:

* Your phone disconnects from the local network for more than fifteen minutes
* When it reconnects, it's currently dark outside

You can also capture disconnection events. For example, send yourself an email
if your home server is offline for more than one minute.

## Installing

Pre-requisites:

* Python 2.7
* fping

__Ubuntu / Debian / Raspbian__  

```bash
cd ~/
git clone https://github.com/isdampe/akita.git
cd akita
./install.sh
```

## Configuring your network events

The akita jobs configuration is stored in ~/.config/akita/jobs.json.

See "jobs.json manifest format" below.

#### jobs.json manifest format

The jobs.json manifest format is a JSON document, containing an array of
objects, each of which is loaded into akita.py for monitoring.

```json
[
	{
		"name": "My mobile phone",
		"ip": "192.168.0.150",
		"reconnectTimer": 120,
		"disconnectTimer": 60,
		"reconnectAction": "/opt/phone-reconnect.sh",
		"disconnectAction": "/opt/phone-disconnect.sh"
	},
	{
		"name": "My raspberry pi",
		"ip": "192.168.0.160"
	}
]
```

In the example above, if device 192.168.0.150 does not respond to ICMP ping requests
for more than 60 seconds, /opt/phone-disconnect.sh will be executed.

Likewise, once the phone reconnects, if it has been offline for more than 120 seconds,
/opt/phone-reconnect.sh will be triggered.

Object description

```javascript
{
	"name": "Your device name",
	"ip": "Your IP address to ping",
	"reconnectTimer": 120, //If left blank, defaults to 120
	"reconnectAction": "/path/to/reconnect.sh",
	"disconnectTimer": 120, //If left blank, defaults to 120
	"disconnectAction: "/path/to/disconnect.py
}
```

__Some notes about reconnectAction, and disconnectAction__

If no reconnectAction or disconnectAction is supplied, akita.py will
look for and try to execute a script located in ~/.config/akita/proc.d
as per below.

```

Upon reconnection:
~/.config/akita/proc.d/[ip-address]-reconnect.sh

Upon disconnection:
~/.config/akita/proc.d/[ip-address]-disconnect.sh

```

All actions executed will receive one command line argument, which represents the
numbers of seconds the device has been offline for.

The argument is supplied with a ```-t``` prefix. For example.

```
~/.config/akita/proc.d/192.168.0.150-reconnect.sh -t 320
```

Implying 192.168.0.150 was down for 320 seconds.

## Running akita.py
Simply run in user mode with ./akita.py. If you're looking for a headless,
safer way, try creating a sytemd or init service.
