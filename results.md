Scenario: crossing
Description: 4 agents whose straight-line paths intersect at the center
Agents: 4  Grid: 20x20

Algorithm           Success Makespan Total Cost Conflicts Time(ms) Capped 
Independent         Yes     13       52         0         0.6      -      
Prioritized         Yes     13       52         0         1.2      -      
Cooperative A*      Yes     13       52         0         1.3      -      
CBS                 Yes     13       52         0         0.6      -      

------------------------------------------------------------
Scenario: bottleneck
Description: 4 agents must funnel through a narrow 1-cell corridor
Agents: 4  Grid: 20x20

Algorithm           Success Makespan Total Cost Conflicts Time(ms) Capped 
Independent         Yes     25       86         3         1.2      -      
Prioritized         Yes     26       89         1         5.8      -      
Cooperative A*      Yes     26       89         1         5.3      -      
CBS                 Yes     26       87         0         11.6     -      

------------------------------------------------------------
Scenario: warehouse
Description: 6 agents navigate shelf-style obstacles in a warehouse layout
Agents: 4  Grid: 20x20

Algorithm           Success Makespan Total Cost Conflicts Time(ms) Capped 
Independent         Yes     38       114        3         1.4      -      
Prioritized         Yes     38       115        2         3.4      -      
Cooperative A*      Yes     38       115        2         2.6      -      
CBS                 Yes     38       115        0         9.1      -      

------------------------------------------------------------
Scenario: dense
Description: 4 agents in a tighter grid with high obstacle density
Agents: 4  Grid: 15x15

Algorithm           Success Makespan Total Cost Conflicts Time(ms) Capped 
Independent         Yes     28       88         4         0.8      -      
Prioritized         Yes     28       88         1         1.9      -      
Cooperative A*      Yes     28       88         1         1.6      -      
CBS                 Yes     28       88         0         14.5     -      

------------------------------------------------------------
