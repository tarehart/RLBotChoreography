from typing import List
from xml.dom.minidom import parse

from svgpathtools import parse_path

from cnc.cnc_instructions import BotCnc, ThicknessKeyframe
from util.vec import Vec3


def dom2dict(element):
    """Converts DOM elements to dictionaries of attributes."""
    keys = list(element.attributes.keys())
    values = [val.value for val in list(element.attributes.values())]
    return dict(list(zip(keys, values)))


def get_nearest_position(target: Vec3, options: List[Vec3]):
    min_distance = None
    nearest = None
    for v in options:
        distance = v.dist(target)
        if min_distance is None or distance < min_distance:
            min_distance = distance
            nearest = v
    return nearest


class SVGParser:

    def handle_to_vector(self, handle) -> Vec3:
        return Vec3(handle.start.imag, handle.start.real)

    def string_pair_to_vector(self, string_pair):
        string_arr = string_pair.split(',')
        return Vec3(float(string_arr[0]), float(string_arr[1]))

    def string_pair_to_thickness_keyframe(self, string_pair):
        string_arr = string_pair.split(',')
        return ThicknessKeyframe(float(string_arr[0]), float(string_arr[1]))

    def parse_file(self, file_name, origin: Vec3, normal: Vec3, scale: float, speed: float) -> BotCnc:
        bot_cnc = BotCnc(origin, normal, scale, speed)
        effect_dict = {}
        paths = None
        attributes = None
        with open(file_name, 'r') as file:
            doc = parse(file)
            path_effects = [dom2dict(el) for el in doc.getElementsByTagName('inkscape:path-effect')]

            for path_effect in path_effects:
                id = path_effect['id']
                offset_points: str = path_effect['offset_points']
                as_string_pairs = offset_points.split(' | ')
                as_thickness_keyframes = [self.string_pair_to_thickness_keyframe(pair) for pair in as_string_pairs]
                effect_dict[id] = as_thickness_keyframes

            attributes = [dom2dict(el) for el in doc.getElementsByTagName('path')]
            d_strings = [p['inkscape:original-d'] if 'inkscape:original-d' in p else p['d'] for p in attributes]
            paths = [parse_path(d) for d in d_strings]

        for index, path in enumerate(paths):
            handles = [self.handle_to_vector(h) for h in path]
            attr = attributes[index]
            path_effect = []
            if 'inkscape:path-effect' in attr:
                path_effect_id = attr['inkscape:path-effect'][1:]  # There's a leading #, so trim it off
                path_effect = effect_dict[path_effect_id]

            first_position = handles[0]
            bot_cnc.move_to_position(first_position.x, first_position.y)
            bot_cnc.activate_nozzle(path_effect)
            for handle in handles:
                bot_cnc.move_to_position(handle.x, handle.y)
            bot_cnc.deactivate_nozzle()

        return bot_cnc
