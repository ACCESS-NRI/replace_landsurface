# Integration tests for replace_landsurface

`integration_tests.sh` is a basic binary compatibility test script for the replace_landsurface package.

The script executes various tests in parallel, for all the entry points of the package, using different options to test multiple cases.

All multiple tests are executed to completion, even if any of them fails.
When all the tests are completed, the script fails if any of the tested returned a non-zero exit code, and a message is printed with information about the failed test.

The tests are designed to be run on Gadi within a Python environment where `replace_landsurface` is installed as a development package (for instructions refer to the Installation paragraph in the README).

Usage:
    regression_tests.sh [-h] [--keep]

Options:
    -h, --help          Print this usage information and exit.
    -k, --keep          Force output data to be kept upon test completion.
                        The default behaviour is to keep the output data only for failed test sessions and delete it if all tests pass.

All test data is located in `/g/data/vk83/testing/data/replace_landsurface/integration_tests`.

### Tests performed

- Test 1: hres_ic with `--type era5land`
- Test 2: hres_ic with `--type barra`
- Test 3: hres_ic with `--type astart`
- Test 4: hres_eccb with `--type era5land` (CURRENTLY NOT AVAILABLE)
- Test 5: hres_eccb with `--type barra` (CURRENTLY NOT AVAILABLE)