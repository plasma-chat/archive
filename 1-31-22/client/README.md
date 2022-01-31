# Plasma Client

The default Plasma client. Follow up of [this README](https://github.com/plasma-chat/plasma).  
This guide assumes you already have a `plasma-client` folder and are in it.

### Configuration

The Plasma client comes with various configuration options.  
By default, these are prompted during runtime, unless explicitly specified in the config.

Some of the options include:
- `username` - The username you want to connect with
- `autoconnect` - An IP/domain to automatically connect to
- `timeformat` - `12h`/`24h`/`utc12h`/`utc24h`, the time format used internally
- `colors` - a map of colors to use (more in depth below)

An example config would look like so:
```json
{
    "username": "Benjamin",
    "autoconnect": ":",
    "timeformat": "12h",
    "colors": {
        "user": "red",
        "prompt": "green",
        "time": "yellow"
    }
}
```
In this case, `:` refers to `localhost` (useful for development).  
Currently, the only changable colors are `user`, `prompt`, and `time`.

If a `config.json` file is not present, the following will be asked:
- Server IP (required)
- Username (required)

`timeformat` and `colors` are only present in `config.json`.

### Launching

The simplest way to launch the client is simply running `client.py`.
Unlike the server, the client has a `--debug` option useful for development.

To launch it in debug mode, run `client.py --debug`.
This mode provides you info about your SSL connection, plugin status,
and prevents the screen from clearing (for reading tracebacks).
