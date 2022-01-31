# Plasma Server

The server software for Plasma. Follow up of [this README](https://github.com/plasma-chat/plasma).  
This guide assumes you already have a `plasma-server` folder and are in it.

### Configuration

Before you can launch the server, you first need to make a `config.json` file.  
To ease this process, a `config.example.json` file already exists, rename it to `config.json`.

The average server `config.json` would look like this:
```json
{
    "name": "Server Name",
    "limits": {
        "content": 1000,
        "packet": 5000
    }
}
```

Pretty simple, right? Here's a basic explanation:
- `name` - The name of the server, required
- `limits/content` - The **text** character limit, required
- `limits/packet` - The maximum packet size (JSON) in kb, default is `1mb`

### Launching

The server can simply be launched by calling `server.py`.  
Currently, no server flags are available, although this README will be updated if some are added.
