# Minecraft — Actor Guide (@fundamentallabs/minecraft-mcp)

Full Minecraft bot control via the `minecraft` MCP server (`@fundamentallabs/minecraft-mcp`).

## Calling Convention

Every tool call must be wrapped in the dispatcher's `mcp_tool_call` envelope.
**Do NOT prefix tool names — use the bare camelCase name.**

Output either a **single action object** or a **JSON array** of actions to execute multiple in one turn:

```json
{"action": "mcp_tool_call", "tool": "<tool_name>", "arguments": {...}, "history": "<what you did>"}
```

```json
[
  {"action": "mcp_tool_call", "tool": "mineResource", "arguments": {"name": "oak_log", "count": 5}, "history": "Mined 5 logs"},
  {"action": "mcp_tool_call", "tool": "mineResource", "arguments": {"name": "oak_log", "count": 5}, "history": "Mined 5 more logs"}
]
```

The JSON shown under each tool heading is the `arguments` payload only. Refer to the actual MCP tool schemas in your system prompt for exact parameter types and requirements.

**You are the same agent across all turns.** The History shows what *you* already did — read it and continue. Do not reinvent the plan each turn.

**Use batched actions** for predictable sequences (e.g. mining multiple resources). Keep batches under ~8 actions.

---

## First Thing: Join the Game

**The bot does NOT auto-connect.** You must call `joinGame` as your very first action.

```json
{"action": "mcp_tool_call", "tool": "joinGame", "arguments": {"username": "Kodo"}, "history": "Spawned bot Kodo"}
```

Do this once per session. All subsequent tools require the bot to be spawned first.

---

## Movement & Navigation

### goToKnownLocation

Navigate to specific coordinates (uses pathfinding).

```json
{"action": "mcp_tool_call", "tool": "goToKnownLocation", "arguments": {"x": 100, "y": 64, "z": 200}, "history": "Moved to target"}
```

### goToSomeone

Navigate to another player. Optional `distance` (default 3), `keepFollowing` (default false).

```json
{"action": "mcp_tool_call", "tool": "goToSomeone", "arguments": {"userName": "f1ameyy", "distance": 3}, "history": "Went to f1ameyy"}
```

---

## Resource Gathering

### mineResource

Mine a specific block type. Parameter is `name` (block ID) and `count`.

```json
{"action": "mcp_tool_call", "tool": "mineResource", "arguments": {"name": "oak_log", "count": 10}, "history": "Mined 10 oak logs"}
```

### pickupItem

Pick up items from the ground nearby.

---

## Building

### buildSomething (PREFERRED for structures)

**Requires cheats/operator permissions.** Build structures using Minecraft commands (`/fill`, `/setblock`, etc.). Two modes:

**Script mode** — array of command objects:
```json
{"action": "mcp_tool_call", "tool": "buildSomething", "arguments": {"buildScript": [
  {"command": "fill", "x1": 0, "y1": 64, "z1": 0, "x2": 10, "y2": 64, "z2": 10, "block": "stone"},
  {"command": "fill", "x1": 1, "y1": 65, "z1": 1, "x2": 9, "y2": 68, "z2": 9, "block": "oak_planks"},
  {"command": "setblock", "x": 5, "y": 65, "z": 1, "block": "oak_door"}
]}, "history": "Built house via commands"}
```

**Code mode** — JavaScript string for dynamic building:
```json
{"action": "mcp_tool_call", "tool": "buildSomething", "arguments": {"code": "fill(pos.x-5, pos.y, pos.z-5, pos.x+5, pos.y+4, pos.z+5, 'oak_planks'); log('Done!');"}, "history": "Built structure via code"}
```

Supporting commands: `setblock`, `fill`, `clone`, `summon`, `give`, `raw`. All coordinates are relative to the bot's current position.

### placeItemNearYou

Place a specific block or item near the bot. **Unlike the old server, this DOES accept `itemName`.**

```json
{"action": "mcp_tool_call", "tool": "placeItemNearYou", "arguments": {"itemName": "stone", "userName": "f1ameyy"}, "history": "Placed stone near f1ameyy"}
```

---

## Crafting & Smelting

### craftItems

Craft items using a crafting table or inventory.

```json
{"action": "mcp_tool_call", "tool": "craftItems", "arguments": {"item": "oak_planks", "count": 40}, "history": "Crafted 40 oak planks"}
```

### cookItem / smeltItem

Cook food / smelt items in a furnace.

### retrieveItemsFromNearbyFurnace

Get smelted/cooked items from a furnace.

---

## Inventory

### openInventory

Open the bot's inventory.

### equipItem

Equip armor, tools, or weapons.

### dropItem

Drop items from inventory.

### giveItemToSomeone

Give items to another player.

---

## Communication

### sendChat

Send chat messages or commands (starting with `/`).

```json
{"action": "mcp_tool_call", "tool": "sendChat", "arguments": {"message": "Hello everyone!"}, "history": "Sent chat"}
```

Send a command:
```json
{"action": "mcp_tool_call", "tool": "sendChat", "arguments": {"message": "/give @p stone 64"}, "history": "Gave stone"}
```

### readChat

Read recent chat messages. Supports filtering.

```json
{"action": "mcp_tool_call", "tool": "readChat", "arguments": {"count": 30, "filterType": "chat"}, "history": "Read recent chat"}
```

**Chat dedup:** Track which messages you've replied to. Do not respond twice. Respond to new messages and any mentioning "Kodo". **Respond to all chat from players immediately** — drop what you're doing.

---

## Daemons

Always daemonize these on every Minecraft task:
1. `readChat` — monitor incoming chat messages
2. Any other read-only tool useful for the task

Daemon results are fresh each turn — **never re-query daemonized tools.**

---

## Working Memory (Directives)

Store your full game plan as a directive on turn 1. Future turns read it and continue. When done, mark the old plan as DONE.

```json
{"action": "directive", "directive": "PLAN: Build a starter house. 1. joinGame. 2. get position. 3. buildSomething with buildScript for a 10x10 stone house.", "history": "Saved plan"}
```

When done:
```json
{"action": "directive", "directive": "DONE: Built starter house.", "history": "Marked done"}
```

**Follow your own plan.** After storing a directive, do what it says. Don't replan each turn.

---

## Game Knowledge

- **Must call `joinGame({"username": "Kodo"})` first** — bot does not auto-spawn.
- **For building structures, use `buildSomething`** — requires operator/cheat permissions. Uses `/fill` and `/setblock` commands directly. No inventory needed.
- **`placeItemNearYou` accepts `itemName`** — unlike the old server's `place-block`.
- **`mineResource` replaces `dig-block` and `find-blocks`** — specify `name` (block type) and `count`.
- **`craftItems` replaces `craft-item`** — specify `item` name and `count`.
- **`goToKnownLocation` replaces `move-to-position`** — navigate to coordinates.
- **All tool names are camelCase** — NOT kebab-case. E.g. `buildSomething`, not `build-something`.
- **`sendChat` can send commands** — prefix with `/` (e.g. `/give`, `/time`, `/gamemode`).
- **`readChat` supports filtering** — use `filterType: "chat"` for player messages only.
- **Creative mode**: Use `buildSomething` for structures. No need to gather resources.
- **Store your plan as a directive on turn 1** — then execute it. Don't replan each turn.
- **Always daemonize:** `readChat` and any other read-only state you need.
- **Never re-query daemonized tools** — results are fresh every turn.
