# TDD Evidence

This file preserves representative terminal output from the test-first development cycles. Each RED run failed for the expected missing behavior. The matching GREEN run passed after the smallest implementation for that slice.

## Slice 1: extraction and classification

RED command:

```bash
python3 -m unittest tests.test_core -v
```

RED output:

```text
ImportError: Failed to import test module: test_core
ModuleNotFoundError: No module named 'document_workflow'
Ran 1 test in 0.000s
FAILED (errors=1)
```

GREEN command:

```bash
PYTHONPATH=src python3 -m unittest tests.test_core -v
```

GREEN output:

```text
test_extracts_supported_formats_as_normalized_text ... ok
test_loads_rules_and_classifies_by_priority_then_fallback ... ok
Ran 2 tests in 0.002s
OK
```

## Slice 2: recursive copying and manifests

RED command:

```bash
PYTHONPATH=src python3 -m unittest tests.test_workflow.WorkflowTests.test_recursively_copies_with_duplicate_safe_names_and_manifests -v
```

RED output:

```text
ImportError: Failed to import test module: test_workflow
ModuleNotFoundError: No module named 'document_workflow.workflow'
Ran 1 test in 0.000s
FAILED (errors=1)
```

GREEN output:

```text
test_recursively_copies_with_duplicate_safe_names_and_manifests ... ok
Ran 1 test in 0.002s
OK
```

## Slice 3: invalid and unsupported documents

RED output:

```text
test_records_invalid_json_and_unsupported_files_without_stopping ... ERROR
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
Ran 1 test in 0.003s
FAILED (errors=1)
```

GREEN output:

```text
test_records_invalid_json_and_unsupported_files_without_stopping ... ok
Ran 1 test in 0.001s
OK
```

## Slice 4: dry run

RED output:

```text
test_dry_run_plans_without_creating_output ... ERROR
TypeError: process_documents() got an unexpected keyword argument 'dry_run'
Ran 1 test in 0.001s
FAILED (errors=1)
```

GREEN output:

```text
test_dry_run_plans_without_creating_output ... ok
Ran 1 test in 0.001s
OK
```

## Slice 5: path-safe categories

RED output:

```text
test_rejects_category_names_that_can_escape_output ... FAIL
AssertionError: ValueError not raised
Ran 1 test in 0.001s
FAILED (failures=1)
```

GREEN output:

```text
test_rejects_category_names_that_can_escape_output ... ok
Ran 1 test in 0.001s
OK
```

## Slice 6: CLI dry run

RED output:

```text
test_dry_run_prints_json_plan_and_returns_success ... FAIL
AssertionError: 0 != 1 : /usr/bin/python3: No module named document_workflow.cli
Ran 1 test in 0.033s
FAILED (failures=1)
```

GREEN output:

```text
test_dry_run_prints_json_plan_and_returns_success ... ok
Ran 1 test in 0.051s
OK
```

## Slice 7: normalized rule keywords

RED output:

```text
test_trims_keyword_whitespace_from_rules ... FAIL
AssertionError: 'finance' != 'other'
Ran 1 test in 0.001s
FAILED (failures=1)
```

GREEN output:

```text
test_trims_keyword_whitespace_from_rules ... ok
Ran 1 test in 0.001s
OK
```
