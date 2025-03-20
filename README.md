# replace_landsurface

## About

`replace_landsurface` is a `Python` utility to be used within ACCESS-NRI versions of the Regional Nesting Suites to replace specific land surface initial/boundary conditions.


## Development/Testing instructions
For development/testing, it is recommended to install `replace_landsurface` as a development package within a `micromamba`/`conda` testing environment.

### Clone replace_landsurface GitHub repo
```
git clone git@github.com:ACCESS-NRI/replace_landsurface.git
```

### Create a micromamba/conda testing environment
> [!TIP]  
> In the following instructions `micromamba` can be replaced with `conda`.

```
cd replace_landsurface
micromamba env create -n replace_landsurface_dev --file .conda/env_dev.yml
micromamba activate replace_landsurface_dev
```

### Install replace_landsurface as a development package
```
pip install --no-deps --no-build-isolation -e .
```

### Running the tests

The test suite currently includes only integration tests.

To manually run the tests, from the `replace_landsurface` directory, you can:

1. Activate your [micromamba/conda testing environment](#create-a-micromamba-conda-testing-environment)
2. Run the following command:
   ```
   pytest -n 4
   ```

> [!TIP]
> The `-n 4` option is a [pytest-xdist](https://pytest-xdist.readthedocs.io/en/stable/) option to run the tests in parallel across 4 different workers.

> [!IMPORTANT]
> Integration tests are designed to be run on `Gadi`.
> If you run tests on a local machine, the integration tests will be skipped.
> To run the integration tests, membership of the `zz93` and `ob53` NCI projects is required.