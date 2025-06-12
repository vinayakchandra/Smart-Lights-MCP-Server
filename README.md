# Smart Lights MCP Server

A `Model Context Protocol (MCP)` server that provides seamless control of `WiZ` smart lights through `FastMCP`. Control multiple rooms, adjust colors, brightness, and apply mood-based lighting scenes across your home network.

## Setup

```bash
pip install fastmcp pywizlight
```

Update IP addresses in `home` dictionary to match your lights.

## Tools

| Function                                   | Parameters                  | Description        |
|--------------------------------------------|-----------------------------|--------------------|
| `turn_on(place)`                           | place                       | Turn on light      |
| `turn_off(place)`                          | place                       | Turn off light     |
| `change_color(place, r, g, b, brightness)` | place, r, g, b, brightness  | Set RGB color      |
| `scene(place, scene_id, brightness)`       | place, scene_id, brightness | Apply preset scene |

**Places**: bedroom, office, living

## Usage

```python
await turn_on("bedroom")
await scene("living", 3)  # Sunset
await change_color("office", 255, 0, 0)  # Red
```

Run `python main.py` to discover lights on network.
