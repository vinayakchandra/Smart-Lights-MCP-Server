import asyncio

from mcp.server.fastmcp import FastMCP
from pywizlight import wizlight, PilotBuilder, discovery

mcp = FastMCP("Smart-Lights")

home = {
    'bedroom': '192.168.1.3',
    'office': '192.168.1.4',
    'living': '192.168.1.6',
}


async def discover():
    # returns list of wizlight objects.
    bulbs = await discovery.discover_lights(broadcast_space="192.168.1.255")
    print(f"Bulb IP address: {bulbs[0].ip}")

    # Iterate over all returned bulbs
    for bulb in bulbs:
        print(bulb.__dict__)


def get_ip(place):
    return home[place]


@mcp.tool()
async def turn_off(place: str) -> str:
    """Turning off light
    options:
        bedroom, office, living
    """
    ip = get_ip(place)
    bulb = wizlight(ip)
    await bulb.turn_off()
    await bulb.async_close()

    return "Light off"


@mcp.tool()
async def turn_on(place: str) -> str:
    """Turning on light
    options:
        bedroom, office, living
    """
    ip = get_ip(place)
    bulb = wizlight(ip)
    await bulb.turn_on()
    await bulb.async_close()

    return "Light on"


@mcp.tool()
async def change_color(place: str, r: int, g: int, b: int, brightness: int = 128) -> str:
    """
    Change color into r,g,b
    Example:
        Red = (255, 0, 0)

    brightness should be between 0 and 255 and should always end with 0. max brightness is 255.
    """

    bulb = wizlight(home[place])
    await bulb.turn_on(PilotBuilder(rgb=(r, g, b)))
    await bulb.turn_on(PilotBuilder(brightness=brightness))

    await bulb.async_close()

    return "Color changed"


@mcp.tool()
async def scene(place: str, scene_id: int, brightness: int = 128) -> str:
    """
    options:
        1: "Ocean",
        2: "Romance",
        3: "Sunset",
        4: "Party",
        5: "Fireplace",
        6: "Cozy",
        7: "Forest",
        8: "Pastel colors",
        9: "Wake-up",
        10: "Bedtime",
        11: "Warm white",
        12: "Daylight",
        13: "Cool white",
        14: "Night light",
        15: "Focus",
        16: "Relax",
        17: "True colors",
        18: "TV time",
        19: "Plantgrowth",
        20: "Spring",
        21: "Summer",
        22: "Fall",
        23: "Deep dive",
        24: "Jungle",
        25: "Mojito",
        27: "Christmas",
        28: "Halloween",
        29: "Candlelight",
        30: "Golden white",
        31: "Pulse",
        32: "Steampunk",
        33: "Diwali",
        34: "White",
        35: "Alarm",
        1000: "Rhythm",
    """
    ip = get_ip(place)
    bulb = wizlight(ip)
    await bulb.turn_on(PilotBuilder(scene=scene_id))
    await bulb.turn_on(PilotBuilder(brightness=brightness))

    return f"scene changed to {scene_id}"


if __name__ == '__main__':
    asyncio.run(discover())
