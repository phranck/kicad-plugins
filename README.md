<div align="center">

[![license](https://img.shields.io/github/license/phranck/kicad-plugins?style=flat&color=e53935&label=license)](https://layered.mit-license.org)
[![last commit](https://img.shields.io/github/last-commit/phranck/kicad-plugins?style=flat&color=fb8c00&label=last%20commit)](https://github.com/phranck/kicad-plugins/commits/main)
[![code size](https://img.shields.io/github/languages/code-size/phranck/kicad-plugins?style=flat&color=f9a825&label=code%20size)](https://github.com/phranck/kicad-plugins)
[![language](https://img.shields.io/github/languages/top/phranck/kicad-plugins?style=flat&color=43a047)](https://github.com/phranck/kicad-plugins)
[![issues](https://img.shields.io/github/issues/phranck/kicad-plugins?style=flat&color=1e88e5&label=issues)](https://github.com/phranck/kicad-plugins/issues)
[![stars](https://img.shields.io/github/stars/phranck/kicad-plugins?style=flat&color=8e24aa&label=stars)](https://github.com/phranck/kicad-plugins)

<img src="media/hero.png" alt="KiCad Plugins, action plugins for the KiCad PCB editor" width="860">

</div>

# KiCad Plugins

Action plugins for the KiCad PCB editor. Each one lives in its own folder with its own README, and installs on its own, so you can take the one you want and ignore the rest.

## Plugins

| Plugin | What it does |
|---|---|
| [GridRef](gridref) | Draws a lettered and numbered grid around the board, so a position has a name instead of a millimetre coordinate |

## Installation

Clone the repository, then link the plugin folder you want into KiCad's plugin directory. A link rather than a copy means `git pull` updates the installed plugin.

```bash
git clone https://github.com/phranck/kicad-plugins.git
ln -s "$PWD/kicad-plugins/gridref" ~/Documents/KiCad/10.0/3rdparty/plugins/gridref
```

On Linux the plugin directory is `~/.local/share/kicad/10.0/3rdparty/plugins`, and on Windows it is `%USERPROFILE%\Documents\KiCad\10.0\3rdparty\plugins`.

In the PCB editor, choose **Tools → External Plugins → Refresh Plugins**. The button appears in the toolbar.

## Requirements

KiCad 9 or 10. The plugins use the `pcbnew` Python API and wxPython, both of which ship with KiCad, so nothing else needs installing.

## License

This repository has been published under the [MIT](https://layered.mit-license.org) license.
