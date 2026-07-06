# Minecraft — Actor Guide (MCP) — FundamentalLabs

Provides full Minecraft bot control via the `minecraft` MCP server (`@fundamentallabs/minecraft-mcp`).

## Calling Convention

Every tool call must be wrapped in the dispatcher's `mcp_tool_call` envelope.
**Do NOT prefix tool names — use the bare name.**

```json
{"action": "mcp_tool_call", "tool": "<tool_name>", "arguments": {...}, "history": "<what you did>"}
```

The JSON shown under each tool heading is the `arguments` payload only.

---

## Bot Management (start here)

### joinGame

Spawn a bot. **Call this first before any other tool.**

```json
{"action": "mcp_tool_call", "tool": "joinGame", "arguments": {"username": "Kodo", "host": "localhost", "port": 25565}, "history": "Joined game"}
```

- `username` (required): Bot's username
- `host` (optional, default: `localhost`)
- `port` (optional, default: `25565`)

### leaveGame

Disconnect bot(s).

```json
{"action": "mcp_tool_call", "tool": "leaveGame", "arguments": {"username": "Kodo"}, "history": "Left game"}
```

- `disconnectAll`: `true` to disconnect all bots

---

## Movement & Navigation

### goToKnownLocation

Navigate to specific coordinates.

```json
{"action": "mcp_tool_call", "tool": "goToKnownLocation", "arguments": {"x": 100, "y": 64, "z": 200}, "history": "Went to location"}
```

### goToSomeone

Navigate to another player.

```json
{"action": "mcp_tool_call", "tool": "goToSomeone", "arguments": {"username": "Player1"}, "history": "Went to player"}
```

### runAway

Run away from threats.

```json
{"action": "mcp_tool_call", "tool": "runAway", "arguments": {}, "history": "Ran away"}
```

### swimToLand

Swim to nearest land when in water.

```json
{"action": "mcp_tool_call", "tool": "swimToLand", "arguments": {}, "history": "Swam to land"}
```

---

## Combat & Hunting

### attackSomeone

Attack players, mobs, or animals.

```json
{"action": "mcp_tool_call", "tool": "attackSomeone", "arguments": {"name": "zombie"}, "history": "Attacked zombie"}
```

### hunt

Hunt animals or mobs.

```json
{"action": "mcp_tool_call", "tool": "hunt", "arguments": {"name": "sheep", "count": 3}, "history": "Hunted sheep"}
```

---

## Resource Gathering

### mineResource

Mine specific blocks or resources. **Note: This only targets blocks exposed to air — it cannot mine buried/underground blocks.**

```json
{"action": "mcp_tool_call", "tool": "mineResource", "arguments": {"name": "stone", "count": 10}, "history": "Mined stone"}
```

### harvestMatureCrops

Harvest mature crops from farmland.

```json
{"action": "mcp_tool_call", "tool": "harvestMatureCrops", "arguments": {}, "history": "Harvested crops"}
```

### pickupItem

Pick up items from the ground.

```json
{"action": "mcp_tool_call", "tool": "pickupItem", "arguments": {}, "history": "Picked up items"}
```

---

## Crafting & Smelting

### craftItems

Craft items using a crafting table.

```json
{"action": "mcp_tool_call", "tool": "craftItems", "arguments": {"item": "stone_pickaxe", "count": 1}, "history": "Crafted stone pickaxe"}
```

### cookItem

Cook items in a furnace.

```json
{"action": "mcp_tool_call", "tool": "cookItem", "arguments": {"item": "beef", "count": 3}, "history": "Cooked beef"}
```

### smeltItem

Smelt items in a furnace.

```json
{"action": "mcp_tool_call", "tool": "smeltItem", "arguments": {"item": "iron_ore", "count": 3}, "history": "Smelted iron ore"}
```

### retrieveItemsFromNearbyFurnace

Get smelted items from furnace.

```json
{"action": "mcp_tool_call", "tool": "retrieveItemsFromNearbyFurnace", "arguments": {}, "history": "Retrieved from furnace"}
```

---

## Inventory Management

### openInventory

Open the bot's inventory.

```json
{"action": "mcp_tool_call", "tool": "openInventory", "arguments": {}, "history": "Opened inventory"}
```

### equipItem

Equip armor, tools, or weapons.

```json
{"action": "mcp_tool_call", "tool": "equipItem", "arguments": {"item": "iron_pickaxe", "destination": "hand"}, "history": "Equipped pickaxe"}
```

### dropItem

Drop items from inventory.

```json
{"action": "mcp_tool_call", "tool": "dropItem", "arguments": {"item": "dirt", "count": 5}, "history": "Dropped dirt"}
```

### giveItemToSomeone

Give items to another player.

```json
{"action": "mcp_tool_call", "tool": "giveItemToSomeone", "arguments": {"item": "diamond", "count": 1, "username": "Player1"}, "history": "Gave diamond"}
```

---

## Building & Farming

### placeItemNearYou

Place blocks near the bot.

```json
{"action": "mcp_tool_call", "tool": "placeItemNearYou", "arguments": {"item": "crafting_table", "count": 1}, "history": "Placed crafting table"}
```

### prepareLandForFarming

Prepare land for farming.

```json
{"action": "mcp_tool_call", "tool": "prepareLandForFarming", "arguments": {}, "history": "Prepared farmland"}
```

### useItemOnBlockOrEntity

Use items on blocks or entities.

```json
{"action": "mcp_tool_call", "tool": "useItemOnBlockOrEntity", "arguments": {"item": "bone_meal", "target": "wheat"}, "history": "Used bone meal"}
```

---

## Survival

### eatFood

Eat food to restore hunger.

```json
{"action": "mcp_tool_call", "tool": "eatFood", "arguments": {}, "history": "Ate food"}
```

### rest

Rest to regain health.

```json
{"action": "mcp_tool_call", "tool": "rest", "arguments": {}, "history": "Rested"}
```

### sleepInNearbyBed

Find and sleep in a bed.

```json
{"action": "mcp_tool_call", "tool": "sleepInNearbyBed", "arguments": {}, "history": "Slept in bed"}
```

---

## Storage

### openNearbyChest

Open a nearby chest.

```json
{"action": "mcp_tool_call", "tool": "openNearbyChest", "arguments": {}, "history": "Opened chest"}
```

---

## Vision & Communication

### lookAround

Look around and observe the environment.

```json
{"action": "mcp_tool_call", "tool": "lookAround", "arguments": {}, "history": "Looked around"}
```

### readChat

Read recent chat messages.

```json
{"action": "mcp_tool_call", "tool": "readChat", "arguments": {"count": 10, "timeLimit": 300}, "history": "Read chat"}
```

- `timeLimit`: seconds (default: 300)
- `filterType`: `"chat"` for player messages only

### sendChat

Send chat messages or commands.

```json
{"action": "mcp_tool_call", "tool": "sendChat", "arguments": {"message": "Hello!"}, "history": "Sent chat"}
```

- `delay`: ms to wait before sending

---

## Progression Sequence

### Start: Join game

```json
{"action": "mcp_tool_call", "tool": "joinGame", "arguments": {"username": "Kodo", "host": "localhost", "port": 25565}, "history": "Joined game"}
```

### Check inventory

```json
{"action": "mcp_tool_call", "tool": "openInventory", "arguments": {}, "history": "Opened inventory"}
```

### Punch wood → craft planks → crafting table

```json
{"action": "mcp_tool_call", "tool": "mineResource", "arguments": {"name": "oak_log", "count": 3}, "history": "Mined wood"}
```

```json
{"action": "mcp_tool_call", "tool": "craftItems", "arguments": {"item": "oak_planks", "count": 4}, "history": "Crafted planks"}
```

```json
{"action": "mcp_tool_call", "tool": "craftItems", "arguments": {"item": "crafting_table", "count": 1}, "history": "Crafted table"}
```

### Place crafting table → stone pickaxe

```json
{"action": "mcp_tool_call", "tool": "placeItemNearYou", "arguments": {"item": "crafting_table", "count": 1}, "history": "Placed table"}
```

```json
{"action": "mcp_tool_call", "tool": "mineResource", "arguments": {"name": "stone", "count": 8}, "history": "Mined stone"}
```

```json
{"action": "mcp_tool_call", "tool": "craftItems", "arguments": {"item": "stone_pickaxe", "count": 1}, "history": "Crafted stone pickaxe"}
```

### Iron pickaxe

```json
{"action": "mcp_tool_call", "tool": "mineResource", "arguments": {"name": "iron_ore", "count": 3}, "history": "Mined iron ore"}
```

```json
{"action": "mcp_tool_call", "tool": "placeItemNearYou", "arguments": {"item": "furnace", "count": 1}, "history": "Placed furnace"}
```

```json
{"action": "mcp_tool_call", "tool": "smeltItem", "arguments": {"item": "iron_ore", "count": 3}, "history": "Smelted iron"}
```

```json
{"action": "mcp_tool_call", "tool": "retrieveItemsFromNearbyFurnace", "arguments": {}, "history": "Got iron ingots"}
```

```json
{"action": "mcp_tool_call", "tool": "craftItems", "arguments": {"item": "iron_pickaxe", "count": 1}, "history": "Crafted iron pickaxe"}
```
