import sdl2, sdl2.sdlttf, sdl2.sdlmixer

event_handlers = {}


class EventLoop:
    def __init__(self):
        self.keepRunning = False

    def start(self):
        self.keepRunning = True

    def stop(self):
        self.keepRunning = False

    def pump(self, world):
        # TODO: optimize eventloop to use more efficient functions like PeepEvents?
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(event):
            for event_handler in event_handlers.get(event.type, ()):
                event_handler(event, world)
                if not self.keepRunning:
                    break
            if not self.keepRunning:
                break

    def runloop(self, world, loopFunction):
        try:
            while self.keepRunning:
                self.pump(world)
                loopFunction()
        finally:
            # TODO: make these go in a more appropriate place?
            sdl2.sdlmixer.Mix_Quit()
            sdl2.sdlttf.TTF_Quit()
            sdl2.SDL_Quit()


# so that we can use @decorators.
# remember that, since append returns None, all of the functions won't really be defined
def handler(event_type, new_handler=None):
    if event_type not in event_handlers:
        event_handlers[event_type] = []
    if new_handler is None:
        return event_handlers[event_type].append
    else:
        event_handlers[event_type].append(new_handler)
