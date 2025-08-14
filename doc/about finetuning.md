# About Finetuning

## Goal

- learn to build LLM for specific task

## Tasks

- [ ] Which domain?
  - From gpt-5, if I want the LLM to output a custom language scripts, this task belongs to text generation/code generation/domain-specific-language (DSL) generation
  - More detailed task specification
    - volume and corpus scope: mostly finetuning on structured DSL examples instead of large-scale pretraining from raw code
    - task format: both generation from DSL-like prompts and require evaluation (e.g. test-case checking, parsing)
    - languge diversity: the DSL is purely synthetic and is not integrated with other languages
    - quality vs quantity: prioritize strict compliance with fewer high-quality samples instead of larger but noisier dataset
  - There are several different types of datasets:
    - pre-training/massive: large scale pre-training datasets with unlabeled code: e.g. **The Stack, The Stack v2, GitHub Code**
    - Instruction/Finetuning datasets/benchmarks useful for fine-tuning models, especially when aligning to task formats similar to your DSL: e.g. **APPS(automated programming progress standard), CodeXGLUE, CodeContests, TACO**
    - Complex logic benchmarks explore complex generation and practical behaviors, particularly useful when needing more than simple one-shot examples: e.g. **BigCodeBench, ClassEval, NaturalCodeBench**
    - Multilingual datasets are good for evaluating or enhancing model robustness across multiple programming languages: e.g. **MBPP/MBXP, HumanEval-X, Multilingual HumanEval, MultiPL-E**
  - types of training/finetuning workflows
    - for mixed tcl + DSL code generation
      - inventory and canonicalize your code base
        - collect sources
          - real tcl scripts (gold corpus)
          - all proc/variable definitions (APIs) including versions
          - DSL manuals/specs + any examples/snippets from internal docs
        - normalize
          - deduplicate near-duplicates
          - remove secrets; mask sensitive constants
          - format consistently (one style; run a formatter/linter if you have one)
      - build strict validators if syntax correctness is a hard requirement
        - tcl validator
          - batch `tclsh -n` (syntax check) or your preferred static checker.
          - Optional: run minimal smoke tests if your procs are side-effect-free with mocks.
        - DSL validator
          - Implement a parser per the manual (ANTLR/PEG/hand-rolled).
          - Provide a tiny interpreter/simulator if semantics allow (even partial is helpful).
        - mixed tcl + DSL validator
          - Define the embedding contract (e.g., dsl { ... }, @dsl(...), heredoc, etc.).
          - Ensure the validator checks both host Tcl and every embedded DSL block.
        - Output: a CLI like validate mixed.tcl → {valid_syntax, valid_DSL_blocks, details}. You’ll also want a “repair hints” mode to harvest negative examples.
      - extract a symbol catalog for grounding: Create a machine-readable manifest of everything the model is allowed to call.
        - Procs: name, args (with defaults), types/constraints, side effects, return, examples.
        - Variables (config/consts): names, allowed values, scope.
        - DSL blocks: grammar fragments, valid attributes/options, examples.
        - Constraints/policies: forbidden procs, deprecations, required headers.
        ```json
        {
        "procs": [
            {
            "name": "my::route",
            "args": [{"name":"net","type":"string"}, {"name":"layer","type":"enum","values":["M1","M2","M3"]}],
            "returns": "int",
            "examples": ["my::route -net CLK -layer M3"],
            "notes": "Fails if layer is blocked in techfile"
            }
        ],
        "variables": [{"name":"::tech::corner","values":["tt","ss","ff"]}],
        "dsl": {
            "embedding": {"open":"dsl {", "close":"}"},
            "grammar_summary": "... short EBNF here ..."
        }
        }
        ```
      - build context packs for prompts (for training + inference): Each pack = the minimal slice of the catalog needed for a task.
        - Pack contents: the relevant proc signatures + examples, variable options, DSL grammar excerpt(s), and 2–3 tiny good examples of Tcl+DSL usage.
        - Why: keeps prompts short, enforces “only-these-APIs” behavior, and scales with retrieval.
      - create the training dataset (instruction -> solution): You already have real scripts — convert them to training items:
        - Extract tasks from existing scripts
          - Write a short natural-language requirement that the script fulfills.
          - Keep the final Tcl+DSL as the target.
          - Optionally add a brief rationale (hidden from training target, but useful for analysis).
          - Build/attach a context pack that includes only APIs actually used.
          - Validate with your validators; discard anything that fails.
        - Synthesize additional tasks
          - From the symbol catalog: programmatically generate small tasks (parameter sweeps, common variants).
          - From the DSL manual: generate micro-exercises that focus on one grammar rule at a time.
          - Create hard negatives: wrong arg names, bad enum values, malformed DSL blocks.
          - Label as invalid and keep for a separate “refusal/correction” head or for contrastive learning.
        - Data format (JSONL)
            ```json
            {
            "instruction": "Route net CLK on metal layer M3 and enforce spacing rule SR2 using a DSL block.",
            "context": { /* context pack subset here */ },
            "output": "#!/usr/bin/env tclsh\nset ::tech::corner tt\nmy::route -net CLK -layer M3\n# DSL block for spacing\ndsl {\n  rule \"SR2\" apply_to: CLK spacing: 0.12um\n}\n",
            "metadata": {"validators_passed": true, "topic": "routing+rules"}
            }
            ```
      - constrained generation (grammar & trie decoding) You require full compliance. Combine two layers:
        - Token constraints: Build a trie/finite automaton over tokens to forbid illegal keywords outside DSL blocks, enforce required keywords after dsl {, etc.
        - Grammar constraints: Provide a CFG/PEG for the DSL and a pattern grammar for the Tcl host including the embedding delimiters. Use constrained decoding to only allow next tokens permitted by the active grammar state.
        - Segmented decoding: Decode Tcl normally (with token constraints), switch to DSL-grammar-constrained decoding inside dsl { ... }, then switch back to Tcl constraints after closing brace.
        - During fine-tuning, you can simulate constraints with rejection-sampling + validator, but at inference you should enforce via constrained decoding for reliability.
      - training strategy (offline, local)
        - Model choice: pick a capable local base model trained on code (size 7B–14B+ depending on budget/latency).
        - Supervised Fine-Tuning (SFT) on (instruction + context pack → Tcl+DSL).
          - Shuffle examples by difficulty.
          - Mix in a small % of edit/repair tasks: “Fix this script to satisfy validator error XYZ”
        - Curriculum:
          - micro-DSL blocks in tiny Tcl stubs
          - multi-block scripts,
          - end-to-end flows with several procs and one or more DSL sections.
        - Regularization:
          - De-duplicate near-identical tasks.
          - Cap very long scripts (or train with chunked continuation).
        - Online filtering loop (optional):During training, periodically generate on a dev set → run validators → prioritize failures in the next epoch with targeted examples.
      - RAG offline
        - Build a local embeddings index over proc docs, examples, and DSL snippets.
        - At request time:
          - Embed the user instruction.
          - Retrieve top-k relevant symbols + examples
          - Build a context pack (bounded length)
          - Generate with constraints.
        - This keeps outputs aligned with your current codebase without retraining every time.
      - prompt & output templates
        - System (fixed): “You generate Tcl scripts that may embed DSL within dsl { ... }. Use only the APIs shown in the context. Outputs must pass the Tcl and DSL validators.”
        - User (example)
        ```json
        Goal: Insert keepout around net CLK and route it on M3.
        Constraints: Use spacing rule SR2 from DSL; do not modify other nets.

        Context:
        - procs:
        - my::route -net <string> -layer {M1|M2|M3}
        - my::keepout -net <string> -width <float_um>
        - DSL excerpt:
        dsl {
            rule "<ID>" apply_to: <NET> spacing: <FLOAT>um
        }
        - variables:
        ::tech::corner in {tt, ss, ff}

        Produce a single Tcl file.

        ```
        - Assistant output (skeleton): Tcl header + calls + one DSL block (must validate).
      - evaluation
        - Create three held-out test suites:
          - Syntax suite: no semantics — just varied forms to ensure parser compliance.
          - Unit tasks: single feature per script (routing, spacing, keepout, etc.).
          - Scenario tasks: multi-step flows (several procs + DSL rules).
        - Metrics
          - Tcl parse rate (% scripts passing Tcl syntax).
          - DSL parse rate.
          - Mixed compliance (both pass).
          - Policy compliance (no forbidden procs, args in allowed sets).
          - Pass@k (try k samples with different temps).
          - Latency & token count (for offline sizing).
      - packing for offline use
        - Bundle:
          - The fine-tuned model weights
          - The validator CLI.
          - The retriever (embeddings + index).
          - A context-builder (turns a request into a context pack).
          - A constrained decoder wrapper (Tcl/DSL grammars).
        - Expose a single local CLI: The CLI internally: retrieve → build context → constrained decode → validate → save
            ```json
                        generate \
            --instruction task.txt \
            --max_tokens 2000 \
            --k 8 --temperature 0.3 \
            --out script.tcl
            ```
      - ongoing maintenance
        - When APIs/DSL evolve, update the catalog and examples, then just re-index.
        - Periodically mine production prompts + human fixes → append to training set for the next SFT refresh.
        - Track validator error taxonomy to drive targeted data synthesis.
    - for DSL integrated with other languages
      - select benchmark datasets as semantic seeds
      - write an X->DSL converter using your DSL manual to convert solution from X language to DSL
      - Add domain-specific prompts
      - integrate testbenches so every example can be run for pass/fail checking
      - mix negative examples to enforce strict syntax(include invalid DSL snippets with common mistakes like missing semicolons, undeclared signals, etc. and label them `valid: false` so the LLM learns to avoid these)
    - for purely synthetic DSL
      - defining the DSL dataset structure. Include invalid examples with `valid: false` to train syntax robustness
        ```json
        {
        "description": "Design a 2-input AND gate module named G1.",
        "dsl_code": "MODULE G1(INPUT A, INPUT B, OUTPUT Y) { Y = A & B; }",
        "tests": [
            {"input": {"A":0, "B":0}, "expected": {"Y":0}},
            {"input": {"A":0, "B":1}, "expected": {"Y":0}},
            {"input": {"A":1, "B":0}, "expected": {"Y":0}},
            {"input": {"A":1, "B":1}, "expected": {"Y":1}}
        ],
        "valid": true
        }
        ```
      - generating the synthetic corpus by
        - manual authoring small and high-quality datasets: hand write 200-1000 examples that cover all aspects in your DSL. Ensures absolute syntax compliance from the start
        - rule-based generator: write a DSL program generator that can scale to thousands of examples while keeping correctness
      - application workflow: generation + evaluation:
        - prompt design: write natural-language specs that simulate real production requests
        - DSL generation: output code using your strict syntax rules
        - test vector execution: run in a reference sandbox to verify correctness
        - filtering: remove invalid or non-compilable examples automatically
        - negative data: intentionally produce invalid DSL for error detection learning
      - dataset size recommendation
        - initial fine-tune: ~1K-5K high-quality hand verified examples
        - extended(with generator): up to 50K+ synthetic examples
        - evaluation set: 200-500 unseen tasks with varied complexity
      - finetuning flow
        - build DSL execution environment to verify model outputs
          - parser: checks syntax against the grammar
          - simulator: execute DSL code with given test input cases to get output results
          - validator: compares simulation output to expected results, returning pass/fail
        - create the dataset
          - write a rule-based DSL generator
            - Randomly generate valid DSL programs from the grammar
            - Include natural-language problem descriptions for each program
            - Auto-generate test cases from truth tables, FSMs, or random input patterns
          - create negative examples
            - Mutate valid DSL code to introduce common error types including and not limited to:
              - Missing semicolons
              - Wrong stage names
              - Extra/missing brackets
            - Label them as valid: false
          - format the dataset, e.g. into a common JSONL schema
            ```json
            {
            "description": "Design a 2-input AND gate named G1.",
            "dsl_code": "MODULE G1(INPUT A, INPUT B, OUTPUT Y) { Y = A & B; }",
            "tests": [
                {"input": {"A":0, "B":0}, "expected": {"Y":0}},
                {"input": {"A":1, "B":1}, "expected": {"Y":1}}
            ],
            "valid": true
            }
            ```
        - train/finetune the LLM
          - choose teh model
            - for offline, small-scale training: use small models
            - for cloud-based large models: use GPT-style APIs or hugging face hosted models
          - training approach
            - supervised fine-tuning (SFT) to train the model to map problem to DSL code exactly
            - few-shot prompting(optional pre-step) to give the model several DSL examples before your task during training
          - syntax enforcement during finetuning
            - use a syntax validator in the training loop to discard outputs that fail parsing
            - optionally implement constrained decoding to let the decoder only emits tokens allowed by the DSL grammar
        - evaluation and feedback loop
          - maintain a held-out set of unseen DSL problems
          - For each generated solution:
            - Parse with the DSL parser
            - Run in the simulator with provided test vectors
            - Compare outputs for correctness
          - Metrics:
            - Pass@1 / Pass@k: percentage of tasks passed on first (or top-k) attempts
            - Syntax validity rate
            - Functional correctness rate
        - iterative improvement
          - Analyze model errors (syntax vs. logic failures)
          - Generate more targeted training examples for weak spots
          - Optionally add Reinforcement Learning with Human Feedback (RLHF) or Reinforcement Learning with Simulation Feedback:
            - Reward = test pass rate + syntax correctness
            - This helps the model learn correctness beyond what SFT provides
- [ ] Typical datasets and metrics in this domain
- [ ] Typical ways and stages of finetuning
- [ ] Typical finetuning pipeline
- [ ] How to evaluate model quality? How to design metrics?
- [ ] Example dataset
- [ ] Example finetuning process
- [ ] Example evaluation pipeline

## Reference

