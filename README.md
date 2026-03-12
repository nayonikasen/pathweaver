# PathWeaver (Prototype 3/3)

This milestone completes the MAPF core with multiple coordination strategies and scenario presets.

## What is included
- 2D grid editor with obstacles
- Multi-agent independent planning baseline
- Prioritized planning with reservation table (vertex + edge)
- Cooperative A* (prioritized with vertex reservations only)
- Conflict-Based Search (CBS) baseline
- Animated simulation with conflict highlights and metrics
- Scenario presets: warehouse, corridor, dense obstacles

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# single-agent
python3 -m pathweaver.main --size 30 --cell 22

# multi-agent
python3 -m pathweaver.multi_demo --size 30 --cell 22
```

## Multi-agent controls
- Click: toggle obstacle
- N then click: set agent start, click again for goal
- O: obstacle mode
- Space: plan all
- P: play/pause simulation
- R: reset simulation time
- X: clear agents
- C: clear obstacles
- 1: independent
- 2: prioritized
- 3: cooperative A*
- 4: CBS
- W: warehouse scenario
- K: corridor scenario
- D: dense scenario
- Esc: quit

## Notes
CBS here is a baseline implementation suitable for small agent counts (2-5). It may become slow on dense maps.
