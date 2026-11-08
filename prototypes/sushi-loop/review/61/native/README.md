# Issue #61 · native Godot evidence

Captured from the real game in an isolated test project:

```sh
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/capture_tips.gd --visible --resolution 780x1688 --output prototypes/sushi-loop/review/61/native/phone
```

| Screen | Shows |
| --- | --- |
| `01-floor-cash-jar-tea` | Floor piles at each tier (the $15 pile hidden behind the guest at the lower belt), the placed jar with its balance label, a tea request with its timer, the cash HUD icon |
| `02-tea-served` | The guest's thanks after tea is served |
| `03-tip-toss` | A tip tossed onto the floor, mid-arc |
| `04-jar-flight`, `05-jar-gain` | A tip flying into the jar and its `+$15` popup |
| `06-collect-flight`, `07-counter-after` | Collecting the bundle and its neighbour: cash flies to the counter, which rolls to the new total on landing |
| `08-jar-full` | The full jar and its FULL label |
| `09-edit-layout` | Edit: cash stays on the floor; the jar is an ordinary Layout good |

The FPS banner is the dev performance overlay. Rules are covered by `godot/tests/tips_tests.gd`.
