def route_command(command_name: str) -> str:
    """Route a command to the appropriate agent"""
    routes = {
        "ping": "system",
        "status": "system",
        "say": "discord-interface",
        "tasks": "system",
        "research": "research-agent",
    }
    return routes.get(command_name, "system")