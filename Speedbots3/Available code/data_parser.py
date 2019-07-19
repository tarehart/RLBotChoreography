# credit to Ard and Hytak

import math
from typing import List


class Packet:
    num_cars: int
    num_boost: int
    num_tiles: int
    num_teams: int
    game_cars: List['Car']
    game_boosts: List['GameBoosts']
    dropshot_tiles: List['TileState']
    teams: List['Team']

    def __init__(self, packet):
        self.num_cars = packet.num_cars
        self.num_boost = packet.num_boost
        self.num_tiles = packet.num_tiles
        self.num_teams = packet.num_teams
        self.game_cars = []
        self.game_boosts = []
        self.game_ball = GameBall(packet.game_ball)
        self.game_info = GameInfo(packet.game_info)
        self.dropshot_tiles = []
        self.teams = []

        for car in range(0, self.num_cars):
            self.game_cars.append(Car(packet.game_cars[car], car))

        for boost in range(0, self.num_boost):
            self.game_boosts.append(GameBoosts(packet.game_boosts[boost]))
            break

        for tile in range(0, self.num_tiles):
            self.dropshot_tiles.append(TileState(packet.tile_state[tile]))
            break

        for team in range(0, self.num_teams):
            self.teams.append(Team(packet.teams[team]))


class Car:
    index: int
    physics: 'Physics'
    score_info: 'ScoreInfo'
    is_demolished: bool
    has_wheel_contact: bool
    is_super_sonic: bool
    is_bot: bool
    jumped: bool
    double_jumped: bool
    name: str
    team: int
    boost: float

    def __init__(self, car, index):
        self.index = index
        self.physics = Physics(car.physics)
        self.score_info = ScoreInfo(car.score_info)
        self.is_demolished = car.is_demolished
        self.has_wheel_contact = car.has_wheel_contact
        self.is_super_sonic = car.is_super_sonic
        self.is_bot = car.is_bot
        self.jumped = car.jumped
        self.double_jumped = car.double_jumped
        self.name = car.name
        self.team = car.team
        self.boost = car.boost


class Physics:
    location: 'Vector3'
    rotation: 'Rotation'
    velocity: 'Vector3'
    angular_velocity: 'Vector3'

    def __init__(self, physics):
        self.location = Vector3.from_struct(physics.location)
        self.rotation = Rotation(physics.rotation)
        self.velocity = Vector3.from_struct(physics.velocity)
        self.angular_velocity = Vector3.from_struct(physics.angular_velocity)


class Vector3:
    x: float
    y: float
    z: float

    def __init__(self, x=0., y=0., z=0.):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, vec: 'Vector3'):
        return Vector3.from_iter(a + b for a, b in zip(self, vec))

    def __sub__(self, vec: 'Vector3'):
        return Vector3.from_iter(a - b for a, b in zip(self, vec))

    def __mul__(self, val: float):
        return Vector3.from_iter(a * val for a in self)

    def __truediv__(self, val):
        return Vector3.from_iter(a / val for a in self)

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __repr__(self):
        return repr((self.x, self.y, self.z))

    def copy(self, x=None, y=None, z=None):
        x = self.x if x is None else x
        y = self.y if y is None else y
        z = self.z if z is None else z
        return Vector3(x, y, z)

    def flatten(self):
        return self.copy(z=0)

    def norm(self):
        return math.sqrt(self.dot(self))

    def normalize(self):
        return self / self.norm()

    def dot(self, vec):
        return sum(a * b for a, b in zip(self, vec))

    @staticmethod
    def from_iter(iterator):
        return Vector3(*list(iterator))

    @staticmethod
    def from_struct(struct):
        return Vector3(struct.x, struct.y, struct.z)


class Rotation:
    pitch: float
    yaw: float
    roll: float

    def __init__(self, rotation):
        self.pitch = rotation.pitch
        self.yaw = rotation.yaw
        self.roll = rotation.roll

    def forward(self):
        c_p = math.cos(self.pitch)
        s_p = math.sin(self.pitch)
        c_y = math.cos(self.yaw)
        s_y = math.sin(self.yaw)

        return Vector3(c_p * c_y, c_p * s_y, s_p)

    def left(self):
        c_r = math.cos(self.roll)
        s_r = math.sin(self.roll)
        c_p = math.cos(self.pitch)
        s_p = math.sin(self.pitch)
        c_y = math.cos(self.yaw)
        s_y = math.sin(self.yaw)

        return Vector3(c_y * s_p * s_r - c_r * s_y, s_y * s_p * s_r + c_r * c_y, -c_p * s_r)

    def up(self):
        c_r = math.cos(self.roll)
        s_r = math.sin(self.roll)
        c_p = math.cos(self.pitch)
        s_p = math.sin(self.pitch)
        c_y = math.cos(self.yaw)
        s_y = math.sin(self.yaw)

        return Vector3(-c_r * c_y * s_p - s_r * s_y, -c_r * s_y * s_p + s_r * c_y, c_p * c_r)


class ScoreInfo:
    score: int
    goals: int
    own_goals: int
    assists: int
    saves: int
    shots: int
    demolitions: int

    def __init__(self, score_info):
        self.score = score_info.score
        self.goals = score_info.goals
        self.own_goals = score_info.own_goals
        self.assists = score_info.assists
        self.saves = score_info.saves
        self.shots = score_info.shots
        self.demolitions = score_info.demolitions


class GameBoosts:
    is_active: bool
    timer: float

    def __init__(self, boost):
        self.is_active = boost.is_active
        self.timer = boost.timer


class GameBall:
    Physics: 'Physics'
    latest_touch: 'LatestTouch'
    drop_shot_info: 'DropShotInfo'

    def __init__(self, ball):
        self.physics = Physics(ball.physics)
        self.latest_touch = LatestTouch(ball.latest_touch)
        self.drop_shot_info = DropShotInfo(ball.drop_shot_info)


class LatestTouch:
    player_name: str
    time_seconds: float
    hit_location: 'Vector3'
    hit_normal: 'Vector3'
    team: int

    def __init__(self, touch):
        self.player_name = touch.player_name
        self.time_seconds = touch.time_seconds
        self.hit_location = Vector3(touch.hit_location.x, touch.hit_location.y, touch.hit_location.z)
        self.hit_normal = Vector3(touch.hit_normal.x, touch.hit_normal.y, touch.hit_normal.z)
        self.team = touch.team


class DropShotInfo:
    damage_index: int
    absorbed_force: int
    force_accum_recent: int

    def __init__(self, info):
        self.damage_index = info.damage_index
        self.absorbed_force = info.absorbed_force
        self.force_accum_recent = info.force_accum_recent


class GameInfo:
    seconds_elapsed: float
    game_time_remaining: float
    is_overtime: bool
    is_unlimited_time: bool
    is_round_active: bool
    is_kickoff_pause: bool
    is_match_ended: bool
    world_gravity_z: float
    game_speed: float

    def __init__(self, game_info):
        self.seconds_elapsed = game_info.seconds_elapsed
        self.game_time_remaining = game_info.game_time_remaining
        self.is_overtime = game_info.is_overtime
        self.is_unlimited_time = game_info.is_unlimited_time
        self.is_round_active = game_info.is_round_active
        self.is_kickoff_pause = game_info.is_kickoff_pause
        self.is_match_ended = game_info.is_match_ended
        self.world_gravity_z = game_info.world_gravity_z
        self.game_speed = game_info.game_speed


class TileState:
    tile_state: int

    def __init__(self, state):
        # 0 == UNKNOWN
        # 1 == FILLED
        # 2 == DAMAGED
        # 3 == OPEN
        self.tile_state = state.tile_state


class Team:
    team_index: int
    score: int

    def __init__(self, team):
        self.team_index = team.team_index
        self.score = team.score


class FieldInfo:
    num_boosts: int
    num_goals: int
    boost_pads: List['BoostPad']
    goals: List['Goal']

    def __init__(self, field):
        self.num_boosts = field.num_boosts
        self.num_goals = field.num_goals
        self.boost_pads = []
        self.goals = []

        for boost in range(0, self.num_boosts):
            self.boost_pads.append(BoostPad(field.boost_pads[boost]))

        for goal in range(0, self.num_goals):
            self.goals.append(Goal(field.goals[goal]))


class BoostPad:
    location: 'Vector3'
    is_full_boost: bool

    def __init__(self, boost):
        self.location = Vector3(boost.location.x, boost.location.y, boost.location.z)
        self.is_full_boost = boost.is_full_boost


class Goal:
    team_num: int
    location: 'Vector3'
    direction: 'Vector3'

    def __init__(self, goal):
        self.team_num = goal.team_num
        self.location = Vector3(goal.location.x, goal.location.y, goal.location.z)
        self.direction = Vector3(goal.direction.x, goal.direction.y, goal.direction.z)
