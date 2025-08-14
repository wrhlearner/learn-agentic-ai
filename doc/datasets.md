# About Datasets

## pre-training/massive

large scale pre-training datasets with unlabeled code: e.g. **The Stack, The Stack v2, GitHub Code**

### [GitHub Code Dataset](https://huggingface.co/datasets/codeparrot/github-code)

The GitHub Code dataset consists of **115M code files** from GitHub in **32 programming languages** with **60 extensions** totaling in **1TB of data**. The dataset was created from the public GitHub dataset on Google BiqQuery.

- data instances
```json
{
 'code': "import mod189 from './mod189';\nvar value=mod189+1;\nexport default value;\n",
 'repo_name': 'MirekSz/webpack-es6-ts',
 'path': 'app/mods/mod190.js',
 'language': 'JavaScript',
 'license': 'isc',
 'size': 73
}
```
- data fields
  - code: string, content of source file
  - repo_name: string, name of the GitHub repository
  - path: string, path of file in GitHub repository
  - language: string, programming language as inferred by extension
  - license: string, license of GitHub repository
  - size: int, size of source file in bytes
- programming languages
  ```json
    {
    "Assembly": [".asm"],
    "Batchfile": [".bat", ".cmd"],
    "C": [".c", ".h"],
    "C#": [".cs"],
    "C++": [".cpp", ".hpp", ".c++", ".h++", ".cc", ".hh", ".C", ".H"],
    "CMake": [".cmake"],
    "CSS": [".css"],
    "Dockerfile": [".dockerfile", "Dockerfile"],
    "FORTRAN": ['.f90', '.f', '.f03', '.f08', '.f77', '.f95', '.for', '.fpp'],
    "GO": [".go"],
    "Haskell": [".hs"],
    "HTML":[".html"],
    "Java": [".java"],
    "JavaScript": [".js"],
    "Julia": [".jl"],
    "Lua": [".lua"],
    "Makefile": ["Makefile"],
    "Markdown": [".md", ".markdown"],
    "PHP": [".php", ".php3", ".php4", ".php5", ".phps", ".phpt"],
    "Perl": [".pl", ".pm", ".pod", ".perl"],
    "PowerShell": ['.ps1', '.psd1', '.psm1'],
    "Python": [".py"],
    "Ruby": [".rb"],
    "Rust": [".rs"],
    "SQL": [".sql"],
    "Scala": [".scala"],
    "Shell": [".sh", ".bash", ".command", ".zsh"],
    "TypeScript": [".ts", ".tsx"],
    "TeX": [".tex"],
    "Visual Basic": [".vb"]
    }
  ```

## Instruction/Finetuning datasets/benchmarks 

useful for fine-tuning models, especially when aligning to task formats similar to your DSL: e.g. **APPS(automated programming progress standard), CodeXGLUE, CodeContests, TACO**

### [APPS](https://huggingface.co/datasets/codeparrot/apps)

- category: code generation
- dataset size: 
  - 10K coding problems
  - ~131K test cases
- dataset function: evaluate the ability of language models to generate code from natural language specifications
- all problems have a least one test case except 195 samples in the train split
- for tests split, the average number of test cases is 21.2
- average length of a problem is 293.2 words
- all files have ground-truth solutions except 1235 samples in the test split
- dataset structure
    ```python
    DatasetDict({
        train: Dataset({
            features: ['problem_id', 'question', 'solutions', 'input_output', 'difficulty', 'url', 'starter_code'],
            num_rows: 5000
        })
        test: Dataset({
            features: ['problem_id', 'question', 'solutions', 'input_output', 'difficulty', 'url', 'starter_code'],
            num_rows: 5000
        })
    })
    ```
    ```json
    {
    'problem_id': 0,
    'question': 'Polycarp has $n$ different binary words. A word called binary if it contains only characters \'0\' and \'1\'. For example...',
    'solutions': ["for _ in range(int(input())):\n    n = int(input())\n    mass = []\n    zo = 0\n    oz = 0\n    zz = 0\n    oo = 0\n...",...],
    'input_output': {'inputs': ['4\n4\n0001\n1000\n0011\n0111\n3\n010\n101\n0\n2\n00000\n00001\n4\n01\n001\n0001\n00001\n'], 
                    'outputs': ['1\n3 \n-1\n0\n\n2\n1 2 \n']},
    'difficulty': 'interview',
    'url': 'https://codeforces.com/problemset/problem/1259/D',
    'starter_code': ''}
    }
    ```
    - problem_id: problem id
    - question: a programming problem formulation in English
    - solutions: some ground truth Python solutions
    - input_output: json test cases that are defined by their inputs and outputs and function name if provided
    - metadata
      - difficulty: difficulty level. introductory, interview, and competition
      - url: code source
      - starter_code: starter code to include in prompts

## Complex logic benchmarks

explore complex generation and practical behaviors, particularly useful when needing more than simple one-shot examples: e.g. **BigCodeBench, ClassEval, NaturalCodeBench**

### [BigCodeBench](https://huggingface.co/datasets/bigcode/bigcodebench)

- dataset function: 
  - BigCodeBench-Complete: **Code Completion** based on the structured docstrings.
  - BigCodeBench-Instruct: **Code Generation** based on the NL-oriented instructions.
- data fields
  - task_id (string): The unique identifier for the task.
  - complete_prompt (string): The PEP257-structured docstring prompt.
  - instruct_prompt (string): The natural-language-oriented instruction prompt.
  - canonical_solution (string): The canonical solution w/o comments.
  - code_prompt (string): The code-only prompt.
  - test (string): The code snippet for testing, wrapped in a unittest.TestCase class.
  - entry_point (string): The entry point for the code snippet, which is task_func.
  - doc_struct (string[dictionary]): The structured docstring.
    - description (string): The main task description in natural language.
    - note (string): The additional notes for the task in natural language.
    - reqs (string, optional): The modules can be used in the task solution.
    - params (string, optional): The parameters used in the task solution.
    - returns (string, optional): The values to be returned in the task solution.
    - raises (string, optional): The exceptions should be raised in the task solution.
    - examples (string, optional): The interactive Python examples as hints for the task solution.
  - libs (string): The libraries can be used in the task solution.
```json
{
    'task_id': 'BigCodeBench/0',
    'complete_prompt': 'import itertools\nfrom random import shuffle\n\ndef task_func(numbers=list(range(1, 3))):\n"""\nCalculates the average of the sums of absolute differences between each pair of consecutive numbers\nfor all permutations of a given list. Each permutation is shuffled before calculating the differences.\n\nArgs:\n- numbers (list): A list of numbers. Default is numbers from 1 to 10.\n\nReturns:\nfloat: The average of the sums of absolute differences for each shuffled permutation of the list.\n\nRequirements:\n- itertools\n- random.shuffle\n\nExample:\n>>> result = task_func([1, 2, 3])\n>>> isinstance(result, float)\nTrue\n"""',
    'instruct_prompt': 'Calculates the average of the sums of absolute differences between each pair of consecutive numbers for all permutations of a given list. Each permutation is shuffled before calculating the differences. Args: - numbers (list): A list of numbers. Default is numbers from 1 to 10.\nThe function should output with:\nfloat: The average of the sums of absolute differences for each shuffled permutation of the list.\nYou should write self-contained code starting with:\n```\nimport itertools\nfrom random import shuffle\ndef task_func(numbers=list(range(1, 3))):\n```',
    'canonical_solution': 'permutations = list(itertools.permutations(numbers))\nsum_diffs = 0\n\nfor perm in permutations:\nperm = list(perm)\nshuffle(perm)\ndiffs = [abs(perm[i] - perm[i+1]) for i in range(len(perm)-1)]\nsum_diffs += sum(diffs)\n\navg_sum_diffs = sum_diffs / len(permutations)\n\nreturn avg_sum_diffs',
    'code_prompt': 'import itertools\nfrom random import shuffle\ndef task_func(numbers=list(range(1, 3))):',
    'test':'import unittest\nfrom unittest.mock import patch\nfrom random import seed, shuffle\nimport itertools\nclass TestCases(unittest.TestCase):\ndef test_default_numbers(self):\n# Test with default number range (1 to 10) to check that the result is a positive float.\nresult = task_func()\nself.assertIsInstance(result, float)\nself.assertGreater(result, 0)\ndef test_custom_list(self):\n# Test with a custom list of small positive integers to ensure proper handling and positive result.\nresult = task_func([1, 2, 3])\nself.assertIsInstance(result, float)\nself.assertGreater(result, 0)\ndef test_negative_numbers(self):\n# Test with negative numbers to verify the function handles and returns a positive result.\nresult = task_func([-3, -2, -1])\nself.assertIsInstance(result, float)\nself.assertGreater(result, 0)\ndef test_single_element(self):\n# Test with a single element list to confirm the return is zero since no pairs exist.\nresult = task_func([5])\nself.assertIsInstance(result, float)\nself.assertEqual(result, 0)\ndef test_empty_list(self):\n# Test with an empty list to ensure the function handles it gracefully and returns zero.\nresult = task_func([])\nself.assertIsInstance(result, float)\nself.assertEqual(result, 0)\ndef test_identical_elements(self):\n# Test with a list of identical elements to confirm that differences are zero and the average is zero.\nresult = task_func([2, 2, 2])\nself.assertIsInstance(result, float)\nself.assertEqual(result, 0)\ndef test_mixed_numbers(self):\n# Test with a list of mixed positive and negative numbers to check correct average of differences.\nresult = task_func([-10, 10, -5])\nself.assertIsInstance(result, float)\nself.assertGreater(result, 0)\ndef test_specific_value_with_seed(self):\n# Set seed for reproducibility and check the computed value\nwith patch('random.shuffle', side_effect=lambda x: seed(42) or shuffle(x)):\nresult = task_func([1, 2, 3])\nself.assertAlmostEqual(result, 2.5, delta=0.5) # This expected value should be calculated beforehand\ndef test_large_list_with_seed(self):\n# Set seed and test with a larger list for specific computed value\nwith patch('random.shuffle', side_effect=lambda x: seed(99) or shuffle(x)):\nresult = task_func(list(range(1, 11)))\nself.assertAlmostEqual(result, 33.0, delta=0.5) # This expected value should be calculated beforehand\ndef test_random_behavior(self):\n# Test to ensure different seeds produce different outputs, demonstrating randomness\nwith patch('random.shuffle', side_effect=lambda x: seed(1) or shuffle(x)):\nresult1 = task_func([1, 2, 3])\nwith patch('random.shuffle', side_effect=lambda x: seed(1) or shuffle(x)):\nresult2 = task_func([1, 2, 4])\nself.assertNotEqual(result1, result2)',
    'entry_point': 'task_func',
    'doc_struct': {
        "description": ["Calculates the average of the sums of absolute differences between each pair of consecutive numbers", "for all permutations of a given list. Each permutation is shuffled before calculating the differences.", "Args:", "- numbers (list): A list of numbers. Default is numbers from 1 to 10."], 
        "notes": [], 
        "params": [], 
        "returns": ["float: The average of the sums of absolute differences for each shuffled permutation of the list."], 
        "reqs": ["itertools", "random.shuffle"], "raises": [], 
        "examples": [">>> result = task_func([1, 2, 3])", ">>> isinstance(result, float)", "True"]
    },
    'libs': ['random', 'itertools']
}
```

## Multilingual datasets

are good for evaluating or enhancing model robustness across multiple programming languages: e.g. **MBPP/MBXP, HumanEval-X, Multilingual HumanEval, MultiPL-E**

### [HumanEval-X](https://huggingface.co/datasets/zai-org/humaneval-x)

- dataset function: a benchmark for **evaluating** the multilingual ability of code generative models
- language: Python, C++, Java, JavaScript, and Go
- tasks: can be used for various tasks, such as code generation and translation
- dataset size: 820 data samples each with test cases
- dataset structure
    ```python
    from datasets import load_dataset
    load_dataset("THUDM/humaneval-x", "js")

    DatasetDict({
        test: Dataset({
            features: ['task_id', 'prompt', 'declaration', 'canonical_solution', 'test', 'example_test'],
            num_rows: 164
        })
    })
    ```
- data fields
    ```json
    {'task_id': 'JavaScript/0',
    'prompt': '/* Check if in given list of numbers, are any two numbers closer to each other than\n  given threshold.\n  >>> hasCloseElements([1.0, 2.0, 3.0], 0.5)\n  false\n  >>> hasCloseElements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n  true\n  */\nconst hasCloseElements = (numbers, threshold) => {\n',
    'declaration': '\nconst hasCloseElements = (numbers, threshold) => {\n',
    'canonical_solution': '  for (let i = 0; i < numbers.length; i++) {\n    for (let j = 0; j < numbers.length; j++) {\n      if (i != j) {\n        let distance = Math.abs(numbers[i] - numbers[j]);\n        if (distance < threshold) {\n          return true;\n        }\n      }\n    }\n  }\n  return false;\n}\n\n',
    'test': 'const testHasCloseElements = () => {\n  console.assert(hasCloseElements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) === true)\n  console.assert(\n    hasCloseElements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) === false\n  )\n  console.assert(hasCloseElements([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) === true)\n  console.assert(hasCloseElements([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) === false)\n  console.assert(hasCloseElements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) === true)\n  console.assert(hasCloseElements([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) === true)\n  console.assert(hasCloseElements([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) === false)\n}\n\ntestHasCloseElements()\n',
    'example_test': 'const testHasCloseElements = () => {\n  console.assert(hasCloseElements([1.0, 2.0, 3.0], 0.5) === false)\n  console.assert(\n    hasCloseElements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) === true\n  )\n}\ntestHasCloseElements()\n'}

    ```
    - task_id: indicates the target language and ID of the problem. Language is one of ["Python", "Java", "JavaScript", "CPP", "Go"]
    - prompt: the function declaration and docstring, used for code generation.
    - declaration: only the function declaration, used for code translation.
    - canonical_solution: human-crafted example solutions.
    - test: hidden test samples, used for evaluation.
    - example_test: public test samples (appeared in prompt), used for evaluation.



