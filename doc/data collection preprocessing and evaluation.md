# About data

## Goal

a guidance and quantitative evaluation on whole pipeline about data, including and not limited to problem definition, data identification and collection, data preprocessing, evaluation and benchmarking

inputs:
- problem description
- painpoints
- expected outcome agent system use cases
- evaluation metrics

outputs:
- problem validity checker: 
  - whether this is a valid problem. A template form to fill to understand your problem, including and not limited to: problem description, painpoints, accessible dataset size, evaluation metrics, etc.
- dataset specs: 
  - functionalities: what task? (e.g. code generation, code completion, etc.) how to use? (pretraining, finetuning, RAG?)
  - dataset structure: training/test set split
  - data fields: column names, data type, description, example
  - data curation guidelines: 
    - rationale about the whole dataset. [Reference rationale for BigCodeBench](https://huggingface.co/datasets/bigcode/bigcodebench)
    - data record quality guidelines. [Reference quality guideline for BigCodeBench](https://docs.google.com/document/d/1zgMSoZKL6Z3gWw7n0pvrvhCbTOsPhWb7AD3hORQrs8g/edit?pli=1&tab=t.0#heading=h.nsqdtn3mz8cp)
- A data platform supporting various tools need to develop
  - Tools for data collection
  - Tools for dataset statistics analysis
  - Prompt design quality evaluation
  - Model finetuning/RAG/evaluation APIs
  - Model/RAG quality evaluation tools

## Problem Definition

## Data Collection

## Data Cleaning and Labeling

## Prompt Design

## Evaluation and Benchmark

