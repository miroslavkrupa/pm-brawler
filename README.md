# PM Brawler — Projekťák: Termín byl včera

A funny 2D beat 'em up platformer made in Unity. You play a project manager fighting your way
up the org chart: developers → testers → stakeholders → the Steering Committee → the C-suite.
Czech and English text (Tab switches the language), built for WebGL.

## Getting started

1. Install **Unity Hub** (https://unity.com/download) and a **Unity 6 LTS** editor (6000.0.x)
   with the **WebGL Build Support** module.
2. Unity Hub → **Add → Add project from disk** → select this folder (`~/code/PM-Brawler`).
   If Hub says the editor version differs, choose your installed Unity 6 version.
3. On first open the project creates `Assets/Scenes/Main.unity` by itself.
   Press **Play**. (If the scene isn't there, use the menu **PM Brawler → Create Main Scene**.)

There is nothing to set up in the scene: `GameManager` bootstraps itself and builds the levels,
characters and HUD from code, with generated placeholder graphics.

## Controls

| Action | Keys |
|---|---|
| Move | A / D or ← / → |
| Jump (hold for higher) | Space / W / ↑ |
| Drop through a desk | S + Space |
| Attack (3-hit combo, air attack) | J or X |
| Gantt slam (heavy, breaks shields) | K or C |
| "Let's take this offline" (stuns everyone nearby, costs 50 caffeine) | L or V |
| Pause | Esc or P |
| Language CZ/EN | Tab |

## The cast

| Enemy | Gimmick |
|---|---|
| Developer | Raises a "works on my machine" shield that blocks light hits from the front. Slam it or hit them from behind. |
| Tester | Keeps their distance, throws BUG reports that slow you down. |
| Stakeholder | Shouts "Scope creep!" and charges. Dodge, then punish while they catch their breath. |
| CFO | Throws budget cuts that drain your caffeine. |
| **Steering Committee** (boss) | Meeting invites, escalations that summon stakeholders, status-report table slam. |
| **CEO** (final boss) | Synergy dash, memos; under 50 % HP pivots (reverses your controls), launches strategic initiatives (summons developers) and shockwave slams. |

Pickups: **coffee** (health + caffeine), **Gantt chart** (2× damage for 12 s), **scope freeze** (freezes enemies).
The exit stays locked until every blocker in the level is defeated ("awaiting sign-off").

## Code map

- `Assets/Scripts/Core` — `GameManager` (state machine, HUD, level loading), `Loc` (CZ/EN texts),
  `GameInput` (works with both input systems), `Art` (placeholder sprites), `Fx`, `CameraFollow`
- `Assets/Scripts/Combat` — `Fighter` (shared physics/hit logic), `Health`, `Projectile`
- `Assets/Scripts/Player/PlayerController.cs`
- `Assets/Scripts/Enemies` — `Enemy` base class plus one file per enemy type
- `Assets/Scripts/Level` — `Levels.cs` (text maps), `LevelBuilder`, `Pickup`, `ExitDoor`
- `Assets/Editor/ProjectSetup.cs` — scene setup and the **PM Brawler → Build WebGL** menu

### Adding content

- **Edit a level:** change the text map in `Levels.cs` (legend at the top of the file).
- **New text / translation:** add a key to the table in `Loc.cs` with both Czech and English.
- **New enemy:** subclass `Enemy` (or `Thrower` for ranged), set stats and look in `Configure()`,
  override `Think()` / `Attack()`, and give it a letter in `LevelBuilder.Build`.
- **Real art:** replace `Art.BuildCharacter` with sprites/animations; gameplay code doesn't depend on it.

## Publishing on the web

**PM Brawler → Build WebGL** writes an uncompressed build to `Builds/WebGL`. Upload the contents of that
folder to GitHub Pages (or any static host), the same way as the hybrid project game.
