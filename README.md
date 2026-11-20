[![make.fun bounty](https://make.fun/badge/roblox-brainrot-01.svg)](https://make.fun/bounty/roblox-brainrot-01)
[![rank](https://make.fun/badge/roblox-brainrot-01/danikluue-max/makefun-roblox-brainrot-01/rank.svg)](https://make.fun/bounty/roblox-brainrot-01)
[![reward](https://make.fun/badge/roblox-brainrot-01/danikluue-max/makefun-roblox-brainrot-01/reward.svg)](https://make.fun/bounty/roblox-brainrot-01)

# Brainrot Bay — a 3D Roblox brainrot game

[![Roblox](https://img.shields.io/badge/Roblox-Rojo%207.7.1-E2231A)](https://rojo.space)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Brainrot Bay** is our entry for make.fun's ["Make the best AI Roblox brainrot game" bounty](https://make.fun/bounty/roblox-brainrot-01) (roblox-brainrot-01). A full 3D game in Roblox space: stroll the conveyor, buy absurd meme-born characters, dock them on your base, earn money every second, climb the rarity ladder, steal from rivals, lock your base, rebirth — and sprint home when the tsunami rolls in.

Referral code: `0zdpscn2`

## How to play

- **Conveyor lane** — brainrots spawn and walk the central lane. Step up to one and buy it, provided you can afford it and are close enough.
- **Carry it home** — the brainrot floats above your head until you step onto your own base, where it docks and starts earning $/sec.
- **Rarity ladder** — 36 original characters across 7 rarities (Common → Rare → Epic → Legendary → Mythic → Secret → Divine), from Starla Starfish ($3/s) up to the Ocean Oracle ($40,000/s). Mutations (Golden ×2, Neon ×3, Diamond ×4, Rainbow ×8, Cosmic ×10) roll on spawn.
- **Steal** — click a docked brainrot on someone else's base and hold the 3-second channel. If the owner comes within 20 studs, the steal breaks. A base lock ($500, 60 s) keeps thieves out.
- **Rebirth** — $50,000 + a Mythic or better in your collection resets your money and base for a permanent +100% income, stacking with every rebirth.
- **Tsunami** — every 150 s (with a 15 s warning) a wave sweeps the map. Anyone caught outside their own base drops their carried brainrot back onto the conveyor.
- **Quests** — three earnable goals with one-time cash rewards, claimed from the HUD: buy 3 brainrots ($500), steal 1 ($1,500), survive a tsunami ($1,000).
- **Prize book** — a 36-cell collection grid (name + $/s + rarity) that lights up every character you have ever docked; open it from the action bar's PRIZE BOOK button.

## The world

A 320×320 grass baseplate, a central conveyor lane with neon rails and arrows, a 13-sphere rainbow arch, 8 player bases arranged in a ring (each with 8 dock slots, a back wall, a sign and a lock beam), a centre spawn plaza, a shop kiosk, a lock vendor and a rebirth altar, palm trees, clouds, a water pool, flowers and rocks — plus a second densification pass (sand walkways and 8 radial paths, lane fences, 4 market stalls, 8 lamps, 16 trees, 24 bushes, 6 flower clusters, a fountain, 6 hills, 8 clouds, 3 billboards, crates and barrels, 10 coins, 6 benches, 8 torches and a second pool), and a third pass of beach landmarks (a wooden pier with an end hut on the south edge, a striped lighthouse with a warm neon lamp room on the west edge, 4 leaning surfboards, 3 beach umbrellas, 5 beach balls, a big wave sculpture by the pool, 2 sandcastles), so no view is an empty green field. Morning light (ClockTime 9.5), Future lighting, FogEnd 900.

## What's in the repo

- `main.ts` (Node 22, standard library only) hands the game in: it copies `game.rbxl`, `src/`, `screenshots/` and `PLAY.json` to `/output` (skipping every name that starts with a dot) and writes `/output/dossier.json` with `vendor/makefun-roblox.ts`, the kit's copy, unchanged.
- `game.rbxl` is the binary place Rojo builds from `src/` and `default.project.json` (774 instances, well under the 500,000 cap).
- `src/` — 5 Luau scripts (125,020 bytes): `shared/BrainrotData.luau` (cast, rarities, mutations, economy constants), `shared/CharacterFactory.luau` (builds each character model from parts), `shared/FormatUtil.luau` (money formatting), `server/GameServer.server.luau` (game loop, economy, stealing, rebirth, wave, quests, prize book, DataStore saves), `client/GameClient.client.luau` (HUD ScreenGui, shop UI, quests panel, prize book, action bar, notifications, money counter).
- `screenshots/` — four 1280×720 pictures of the game's own world (1-start cover, 2-play, 3-end, 4-book prize-book grid), rendered headlessly in Blender from the game's own world/character data (`render/`), because Roblox Studio does not run on the Linux build machine. They are renders of the game's own models, layout, colors and HUD — not captures from a Studio session. Round 3 renders at 2× resolution (2560×1440, downscaled with LANCZOS), bloom off, 64 Eevee samples and hard shadows, so edges are crisp; a round-3 pipeline fix also made Blender cylinders stand vertical like in the game (before, lamp poles and tree trunks rendered as face-on discs). One of them is also the game's first thumbnail on Roblox, uploaded on the Creator Dashboard with the game's icon.
- `PLAY.json` — names the published place once it exists (currently `place_id`/`universe_id` 0: the place is built and ready, publishing happens on Roblox Studio / the Creator Dashboard).
- `TOUR.json` — the keys that bring the game to each screenshot.

Run it the way the grader does, writing `out/` in place of `/output`:

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

The rules live on the bounty's page (https://make.fun/bounty/roblox-brainrot-01) and in the kit's RULES.txt, which lists every command in order (Before you submit, then Enter).
