#calculates the boost required to reach a goal speed
def boost_needed(initial_speed, goal_speed):
    p1 = 6.31e-06
    p2 = 0.010383
    p3 = 1.3183
    boost_initial = p1 * initial_speed ** 2 + p2 * initial_speed + p3
    boost_goal = p1 * goal_speed ** 2 + p2 * goal_speed + p3
    return boost_goal - boost_initial
