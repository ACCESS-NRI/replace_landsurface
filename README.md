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

#### Integration tests
To manually run the integration tests, from the `replace_landsurface` directory, you can:
1. Activate your [micromamba/conda testing environment](#create-a-micromamba-conda-testing-environment)
2. Run the following command:
   ```
   bash integration/integration_tests.sh
   ```