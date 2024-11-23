# 3d-blender-plugin
A blender plugin for exporting a IIIF manifest from Blender

## Development

### Requirements

Blender ships with its own version of Python, so you do not actually need anything apart from a code editor to develop this extension.

There are a few tools that can help you with development, if you decide to use them:
- [Pyenv](https://github.com/pyenv/pyenv) - "simple Python version management"
- [Pyright](https://github.com/microsoft/pyright) - "a static type checker for Python"
- [Ruff](https://github.com/astral-sh/ruff) - "an extremely fast Python linter and code formatter"

All of these are **opt-in** and **not required** to develop the plugin.

### Setup

To initialize the development environment, run the following commands:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This should create a virtual environment, install the required dependencies, activate the virtual environment, and allow Pyright to find the Blender specific types.

### Using the plugin

To use the plugin, you need to install it in Blender.
For development, the easiest way is to create a symlink from the Blender `user_default` directory to this directory.

[This is how you can find the relevant directory depending on your operating system.](https://docs.blender.org/manual/en/4.2/advanced/blender_directory_layout.html)

For example, on Linux you can run the following command:

```bash
ln -s /path/to/this/plugin ~/.config/blender/4.2/extensions/user_default/iiif_blender
```
