def debug(self):
    """prints debug info"""
    self.renderer.begin_rendering("debug")
    self.renderer.draw_string_2d(self.RLwindow[2]*0.75, 10, 2, 2, str(self.state), self.renderer.red())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 40, 1, 1, "car pos: " + str(self.info.my_car.pos), self.renderer.black())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 55, 1, 1, "timer: " + str(self.timer), self.renderer.black())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 70, 1, 1, "action: " + str(self.action), self.renderer.black())
    self.renderer.end_rendering()