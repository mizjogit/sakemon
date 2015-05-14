class MItem:
    def __init__(self, text, state, url, port):
        self.text = text
        self.state = state
        self.url = url
        self.port = port

menu_states = {'stirrer': MItem("Stirrer", False, '/iotoggle/stirrer', 10),
               'fan': MItem("Fan", False, '/iotoggle/fan', 20) }
