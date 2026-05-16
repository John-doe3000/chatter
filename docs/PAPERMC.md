# Stats on PaperMC Server

There are several ways to access player stats and server data outside of the Minecraft client. Since PaperMC supports the Bukkit/Spigot API, you can use several existing plugins designed specifically for external integrations and app development.

1. HTTP / REST API Plugins

The most efficient way to get data for an app is through a REST API. These plugins run a small web server alongside your Minecraft server:

- **[PlayerStats API](https://modrinth.com/plugin/playerstats-api)**: Specifically designed for external integrations like web dashboards or custom apps. It exposes vanilla statistics (kills, deaths, distance, etc.) via REST endpoints.
- **[Stater](https://modrinth.com/plugin/stater)**: A lightweight plugin that exposes endpoints for player statistics specifically intended for website or app use. It typically runs on a dedicated port (default is often 25535 or similar).
- Player Analytics (PLAN)

If you want a more robust, ready-made solution, the **[Player Analytics (PLAN)](https://hangar.papermc.io/AuroraLS3/Plan-Player-Analytics)** plugin is a standard in the community.

- **How it works**: It creates a web interface you can access in any browser.
- **Developer use**: It gathers deep data over time (online activity, player growth) and can be configured to use a **MySQL/MariaDB** database. You can then point your app directly at that database to query stats without hitting the Minecraft server itself.
- Direct File Access

If you are comfortable parsing data yourself, you can access the server's raw files directly:

- **Statistics**: Found in the `world/stats/` folder as `.json` files named by player UUID.
- **Player Data**: Found in `world/playerdata/` as `.dat` files. These use the NBT (Named Binary Tag) format, which requires a library (like `prism-nbt` or similar) to read.
- Remote Console (RCON)

For real-time control or simple queries, you can enable **RCON** in your `server.properties` file. This allows you to send console commands (like `/list` or `/stats`) from an external application and receive the text response.

## Send In-Game Messages to Players

1. Using a REST API (Recommended for Apps)

The most modern way to do this is with a plugin that turns your Minecraft server into a web server.

- **[ServerTap](https://github.com/servertap-io/servertap)**: This plugin creates a REST API for your server. You can send a `POST` request to its endpoints to execute commands or send messages directly to players.
- **Example**: Your app can send an HTTP request to `/v1/chat/broadcast` with a JSON body to make a message appear for everyone, or target specific players.

2. Remote Console (RCON)

Minecraft has a built-in remote console protocol called **RCON**. You can enable this in your `server.properties` by setting `enable-rcon=true`.

- **How it works**: Your app connects to the server via the RCON port and sends standard Minecraft commands.
- **Commands to use**:
  - `/say <message>`: Sends a global message that appears as `[Server] Message`.
  - `/msg <player> <message>`: Sends a private whisper to a specific player.
  - `/tellraw @a {"text":"Hello","color":"red"}`: Sends a highly customizable, formatted message (colors, clickable links, etc.) to all players.

3. Database Polling (Indirect)

If you prefer not to have your app talk directly to the server, you can use a "bridge" approach:

- **Plugin + SQL**: Use a plugin that reads from a MySQL database. Your app writes a message into a "queue" table in the database, and the Minecraft plugin checks that table every few seconds to broadcast any new entries in-game.
- Discord Bridges

If your app is integrated with Discord, plugins like **[DiscordSRV](https://www.discordsrv.com/)** allow you to send messages to a Discord channel that then automatically appear in the Minecraft chat.

**Development Tip:** If you want your messages to look professional (with colors or clickable buttons), I recommend using the **[/tellraw](https://minecraft.fandom.com/wiki/Commands/msg)** command via **RCON** or **ServerTap**. It gives you full control over the JSON formatting of the message.

## Stats Available

For a player stats app, [Minecraft](https://www.minecraft.net/en-us) provides a massive amount of data through vanilla files and plugins. This data is generally categorized into **Statistics** (counters for actions) and **PlayerData** (current status and inventory).

1. Vanilla Statistics (Stored in `world/stats/<UUID>.json`)

These are counters that increment automatically. They are perfect for leaderboards:

- **Combat Metrics**: Total player kills (`minecraft:player_kills`), mob-specific kills (e.g., how many Creepers vs. Zombies), and total deaths.
- **Activity & Playtime**: Total time played, time since last death, and number of times the player has jumped or crouched.
- **Movement**: Total distance traveled specifically by walking, sprinting, swimming, flying (Elytra), or riding (Horses/Minecarts).
- **Interaction**: Blocks mined, items crafted, items used (e.g., times a pickaxe was used), and items dropped.
- **Economy/Misc**: Number of villager trades, chests opened, and bells rung.

2. Player Status Data (Stored in `world/playerdata/<UUID>.dat`)

This data represents a player's "live" state. Accessing this usually requires an NBT-capable library or a plugin like [PlayerDataSync](https://hangar.papermc.io/DevVoxel/PlayerDataSync):

- **Vitals**: Current health, hunger level, saturation, and experience points/level.
- **Equipment**: Full inventory list, armor currently worn, and items held in the off-hand.
- **Location**: Exact X, Y, Z coordinates and the dimension (Overworld, Nether, End) the player is currently in.
- **Last Death**: The coordinates and dimension of where the player last died.

3. Advanced & Analytical Data

If you use a plugin like [Player Analytics (PLAN)](https://hangar.papermc.io/AuroraLS3/Plan-Player-Analytics), you can access even deeper insights through its API or database:

- **Session History**: Average session length, peak activity times, and first/last join dates.
- **Engagement**: Player retention (how often they come back) and "growth" metrics for your server.
- **Geography**: Some plugins can estimate player locations (country-level) based on their IP address for a global "Heat Map" of your user base.

4. Custom Data (PersistentDataContainer)

If you are writing your own PaperMC plugin, you can store **Custom Data** directly on a player that persists even after they log out. You could use this to track:

- **RPG Stats**: Custom levels like "Mining Skill" or "Mana".
- **App-Specific Data**: Whether they’ve linked their Discord account, completed an app-exclusive quest, or earned custom badges.

**Development Recommendation:**
For a "Live Leaderboard," use the [PlayerStats API](https://modrinth.com/plugin/playerstats-api) to pull the vanilla JSON stats. For a "Player Profile" page with real-time health/inventory, you'll want to use [ServerTap](https://github.com/servertap-io/servertap) or a custom plugin that reads the `Player` object directly.
