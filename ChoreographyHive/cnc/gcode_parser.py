from cnc.cnc_instructions import BotCnc
from util.vec import Vec3


class GCodeParser:
    """
    This parses a file format called "G-code" which is an industry standard for computer-aided manufacturing:
    https://en.wikipedia.org/wiki/G-code

    Since we can move bots around very precisely with state setting and draw things with boost trails,
    we can pretend a car is like a cutting tool in a big milling machine.

    This allows us to use a wide variety of open source CNC (computer numerical control) software to
    define a path that a bot should take. Example: http://ncplot.com/stickfont/stickfont.htm
    """
    def parse_file(self, file_name, origin: Vec3, normal: Vec3, scale: float, speed: float) -> BotCnc:
        bot_cnc = BotCnc(origin, normal, scale, speed)
        with open(file_name, 'r') as file:
            for line in file:
                if line[0] == 'G':
                    if 'F' in line:
                        bot_cnc.activate_nozzle()
                    else:
                        bot_cnc.deactivate_nozzle()
                elif line[0] == 'X':
                    coords = line[1:].split('Y')
                    bot_cnc.move_to_position(float(coords[0]), float(coords[1]))
        return bot_cnc
