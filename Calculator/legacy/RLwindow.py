def get_window_size(s):
    """finds the size of the Rocket League window"""
    import sys
    try:
        import win32gui
    except ImportError:
        print('Importing win32gui failed, window size cannot be found. Defaulting to 1080p')

    s.RLwindow = [0] * 4

    if 'win32gui' in sys.modules:
        def callback(hwnd, win_rect):
            if 'Rocket League' in win32gui.GetWindowText(hwnd):
                rect = win32gui.GetWindowRect(hwnd)
                win_rect[0] = rect[0]
                win_rect[1] = rect[1]
                win_rect[2] = rect[2] - rect[0]
                win_rect[3] = rect[3] - rect[1]
        win32gui.EnumWindows(callback, s.RLwindow)
    else:
        s.RLwindow = [0,0,1920,1080] 