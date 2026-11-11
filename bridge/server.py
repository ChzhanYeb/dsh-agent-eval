import json
import sys

# v2：从 mcp.server 导入 MCPServer（不是 mcp.server.fastmcp）
from mcp.server import MCPServer

def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)

mcp = MCPServer("balatro_bridge")

@mcp.tool()
def get_state() -> str:
    """Return the current game state as a JSON string."""
    state = {
        "hand": ["J1", "J2", "J3"],
        "target_score": 300,
        "current_score": 0,
        "round": 1,
        "note": "W1 placeholder state",
    }
    return json.dumps(state, ensure_ascii=False)

if __name__ == "__main__":
    log("balatro_bridge starting on stdio")
    mcp.run(transport="stdio")