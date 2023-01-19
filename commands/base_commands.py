import json

invalid_command = "INVALID COMMAND HELLO?"

class BaseCommand:
    command: str = invalid_command
    result_class = None

    def __init__(self, **kwargs):
        self.arguments = kwargs

    def serialize(self) -> str:
        if self.command == invalid_command:
            raise Exception("Invalid command")
        serialized_arguments = {}
        for key, value in self.arguments.items():
            serialized_arguments[key] = (
                value.serialize() if hasattr(value, "serialize") else value
            )
        return json.dumps({"command": self.command, "arguments": serialized_arguments})

class StreamingCommand(BaseCommand):
    def serialize(self, stream_session_id: str) -> str:
        if not stream_session_id:
            raise Exception("No stream session id")
        if self.command == invalid_command:
            raise Exception("Invalid command")

        return json.dumps(
            {
                "command": self.command,
                "streamSessionId": stream_session_id,
                **self.arguments,
            }
        )
