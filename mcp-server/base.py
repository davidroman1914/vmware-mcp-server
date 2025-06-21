class BaseServer:
    def __init__(self):
        self.commands = {}

    def command(self, name):
        def wrapper(func):
            self.commands[name] = func
            return func
        return wrapper

    def run(self):
        import sys
        import json

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                cmd = data.get("command")
                if cmd in self.commands:
                    result = self.commands[cmd](data.get("args", {}))
                    print(json.dumps({"result": result}))
                else:
                    print(json.dumps({"error": f"Unknown command: {cmd}"}))
            except Exception as e:
                print(json.dumps({"error": str(e)}))
