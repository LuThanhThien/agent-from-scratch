# Tool-calling demo ideas

The current [FunctionCall demo](FunctionCall/__main__.py) can read files and list directories. The proposed demos below explore what happens when the next tool call depends on an earlier result.

| Proposed demo | Example request | Local implementation and inspiration |
| --- | --- | --- |
| Test-bench device operator | “Turn off the lights on idle benches. Leave active benches alone.” | Simulate three benches, expose their state, and show which lights change. [Home Assistant agent demo](https://www.home-assistant.io/blog/2024/06/07/ai-agents-for-the-smart-home) |
| Edge deployment investigator | “Camera 02 stopped producing detections after the update. Which component failed, and which log line shows it?” | Use the existing file tools on camera, deployment, and inference logs from a known fault. Check the diagnosis and the cited evidence. [AIOpsLab paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2024/10/AIOpsLab-1.pdf) |
| Vending-machine operator | “You have $20 to restock before Friday. Check recent sales and place an order.” | Simulate one day of sales, inventory, and purchases. Inspect the order, remaining cash, and stock. [Vending-Bench paper](https://arxiv.org/abs/2502.15840) |
| Returns-desk assistant | “I’d like the same headphones in blue. What are my options?” | Look up an order and available variants. After the user chooses and confirms an exchange, check which order item changed. [τ-bench retail policy](https://github.com/sierra-research/tau-bench/blob/main/tau_bench/envs/retail/wiki.md) |
| Engineering handoff assistant | “Find the latest camera-test report and draft a handoff for the engineer on duty.” | Combine report files, a shift roster, and a local draft. Check the recipient and whether each finding appears in the latest report. [WorkBench paper](https://arxiv.org/abs/2405.00823) |

## First demo to try: test-bench device operator

Give the model two tools. `list_benches()` returns each bench’s ID, activity, and light state. `set_light(bench_id, on)` sets one light and returns the resulting state. Show the initial state, tool calls, and final state together so the user can see what changed.

| Bench | Activity | Initial light |
| --- | --- | --- |
| A | Idle | On |
| B | Running a test | On |
| C | Idle | Off |

Start each case with this state and a fresh conversation. Only the tool can reveal the current state to the model.

| Request | Expected behavior |
| --- | --- |
| “Which benches are idle?” | Inspect the benches and answer A and C. Make zero writes. |
| “Turn off the lights on idle benches.” | Inspect the benches, then call `set_light("A", false)` once. B stays lit and C is already off. |
| “Turn off its light.” | Ask which bench the user means. Make zero writes. |

Score the tool calls and the final state separately. Setting C’s light to off again produces the expected final state but adds an unnecessary call. Also check the reply against the observed result so the agent gets credit for reporting what actually changed.

## Reading connections

- Use BFCL’s evaluation of function names and arguments to check the calls in each case. [BFCL paper](https://proceedings.mlr.press/v267/patil25a.html)
- Use the observation from `list_benches()` to drive the next decision in the loop. [ReAct paper](https://arxiv.org/abs/2210.03629)
- Vary the information passed to the model while keeping the request and initial state fixed. For example, compare a list of bench IDs with records that also include activity and light state. [Effective context engineering for AI agents](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
