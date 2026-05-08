# Aletheia - OSDI'26 Artifact Evaluation

This repository contains the artifacts for the paper "Aletheia: Automated Detection of Data Integrity Violations in Microservices", accepted in OSDI'26.

See [Getting Started](#getting-started) for a quick demonstration of how to analyze a simple application.

See [Detailed Instructions](#detailed-instructions) for instructions on running the experiments and obtaining the results in the paper.

## Requirements

To run experiments:

- [Golang](https://go.dev/doc/install) >= 1.24.5
- `time` command with memory reporting support (e.g., GNU `time -v` commonly available on Linux or BSD `/usr/bin/time -l` on macOS)

To later gather results from experiments, either install dependencies manually (Python and Cloc) or use our provided Docker image:

- [Python](https://www.python.org/downloads/) >= 3.10 and [Cloc](https://github.com/aldanial/cloc#install-via-package-manager) >= 2.06
- [Docker](https://docs.docker.com/get-docker/) >= 28.0.0

## Overview

If you obtained this artifact directly through [Zenodo](https://doi.org/10.5281/zenodo.20087594), you can skip the repository setup below.

### Repository Setup

Clone the repository:

```zsh
git clone --recurse-submodules https://github.com/aletheia-microservices/aletheia-artifact-osdi26.git
```

If you already cloned the repository without `--recurse-submodules`, make sure to initialize the submodules:

```zsh
git submodule update --init --recursive
```

### Project Structure

For Aletheia's full documentation, see [aletheia/README.md](https://github.com/aletheia-microservices/aletheia/blob/osdi26/README.md).

The repository is organized as follows:

```
├── aletheia/                         # Aletheia static analysis framework
│   └── blueprint/                    # Blueprint compiler
│       └── examples/                 # Blueprint applications analyzed by Aletheia
├── registry/                         # locations and Blueprint specs for each application
├── generator-synthetic-apps/         # generator for synthetic applications based on Alibaba traces
├── expected/
│   └── {app}/                        # expected results for validation of warnings
└── paper/                            # generated tables and plots from the paper
```

The generation of synthetic applications is based on call graph characteristics observed in [Alibaba traces](<(https://github.com/alibaba/clusterdata/tree/master/cluster-trace-microservices-v2021)>) specified in `generator-synthetic-apps/configs/alibaba2021.yaml`.

The expected results in `expected/{app}` include a README for each application, summarizing the detected warnings and true positives, false positives, and false negatives.

## Getting Started

We now demonstrate how to analyze a simple application, `simpleshop`, provided in `blueprint/examples/simpleshop/`. The application is composed of two microservices, Product Service and Inventory Service and allows clients to register new products and their respective inventory, as well as delete products.

To begin, add a new entry for the `simpleshop` application in the `aletheia/registry/apps.yaml`. This will tell Aletheia how to properly import and analyze the application:

```yaml
- name: simpleshop
  app_root: github.com/blueprint-uservices/blueprint/examples/simpleshop
  package_path: simpleshop/workflow/simpleshop
  spec_name: simpleshop_docker
  spec_path: github.com/blueprint-uservices/blueprint/examples/simpleshop/wiring/specs
```

Go to `aletheia` directory:

```zsh
cd aletheia
```

Now, you will need to generate the application registry according to the new entry added to `aletheia/registry/apps.yaml`. The following script will (i) generate a Go file under `pkg/frameworks/blueprint/` defining how Aletheia locates applications and imports their corresponding Blueprint specs, and (ii) update `go.mod` with new entries so that Go can locate applications relative to Aletheia's path.

```zsh
go run scripts/gen_app_registry/main.go
```

Now, you can run the analysis:

```zsh
go run main.go simpleshop
```

This command prints the analysis results and saves them in `aletheia/output/simpleshop/`. The warnings related to integrity violations are saved in `aletheia/output/simpleshop/analysis/`. Information about the application dependencies (microservices and datastores used) and the schema are saved in `aletheia/output/simpleshop/app.json` and `aletheia/output/simpleshop/schema.json`, respectively.

The output should contain a referential integrity warning indicating a missing cascading delete. In this case, when a product is deleted, the effect is not propagated to the Inventory Service, leaving a dangling inventory record.

```txt
[NUM_WARNINGS = 1]
delete: ProductService.DeleteProduct() ... product_db.product.DeleteOne()
	missing cascade #1: database={inventory_db}, entity={inventory}, pending_fields={ID}
```

If you want to suppress warnings related to missing cascade deletes on the inventory (e.g., when inventory records are intentionally retained), create a YAML file at `aletheia/config/simpleshop.yaml` with the following content:

```yaml
app: simpleshop
ignore_cascade:
  - database: inventory_db
    entity: inventory
    # optional fields for more fine-grained control
    trigger_database: product_db
    trigger_entity: product
```

Then, you can run the analysis again and pass the `--detection_config` flag followed by the file path:

```zsh
go run main.go --detection_config config/simpleshop.yaml simpleshop
```

## Detailed Instructions

Next, we present the instructions to run the experiments in the paper.

We recommend using a machine with at least **16 GB of RAM** available to analyze the large synthetic applications.

The actual experiments should take approximately **4 hours**. However, most of the time is spent analyzing the synthetic applications, since analyzing the realistic applications takes less than **2 minutes**.

In the end, the `paper/` directory will contain the following files corresponding to the results reported in the paper:
- Table 2: `paper/table2-realistic.apps.txt`
- Table 3: `paper/table3-synthetic.apps.txt`
- Figure 5: `paper/figure5-realistic-synthetic.txt`

> [!NOTE]
> If you only wish to reproduce the results for the **realistic applications**, you can remove the three files in `registry/` that start with `apps_synthetic_` and proceed directly to [Registering Applications in Aletheia](#registering-applications-in-aletheia). This will **skip the experiments for synthetic applications** while still allowing you to reproduce the results for realistic applications reported in Table 2 and Figure 5.

### Generating Synthetic Applications

Generate the synthetic applications based on graph characteristics (call depth, fan-out, and request volume) defined in `generator-synthetic-apps/configs/alibaba2021.yaml` whose values were derived from [Alibaba's 2021 production microservice traces](https://github.com/Antipode-SOSP23/alibaba-spike). The script takes the templates for Go applications targeting Blueprint in `generator-synthetic-apps/templates/`, reads the configuration in `generator-synthetic-apps/configs/alibaba2021.yaml` containing the call graph characteristics, and generates and saves the synthetic applications under `aletheia/blueprint/examples/`:

```zsh
cd generator-synthetic-apps && go run main.go --config config/alibaba2021.yaml --output ../aletheia/blueprint/examples && cd ..
```

### Registering Applications in Aletheia

Copy the files in `registry` to `aletheia/registry`. These files provide the application locations and the corresponding Blueprint specifications required by Aletheia:

```zsh
cp -r registry/* aletheia/registry/
```

Then, generate the application registry. This script uses the information copied to `aletheia/registry/` to create a Go file under `aletheia/pkg/frameworks/blueprint/` and update `aletheia/go.mod`, allowing Aletheia to import the applications to be analyzed:

```zsh
cd aletheia && go run scripts/gen_app_registry/main.go && cd ..
```

### Running the Experiments

The experiments include the analysis of **realistic applications** (digota, sockshop, eshopmicroservices, postnotification, dsb_socialnetwork, dsb_mediamicroservices, trainticket) and **synthetic applications** (app1, app2, app3, app4, app5), all located under `blueprint/examples/` folder.

Run the experiments for all applications. If you are running the experiments only for realistic or synthetic applications, you can add the `--realistic` or `--synthetic` flag, respectively. You can use the `--help` flag to see all available options.

```zsh
./run.sh
```

The script will run the experiments 5 times for each application. Peak memory usage is collected using the `time` command with memory reporting support (e.g., GNU `time -v` commonly available on Linux or BSD `/usr/bin/time -l` on macOS).

The results for each analysis iteration will be saved under `aletheia/eval/metrics/{date}/` and `aletheia/eval/memory/{date}/`.

The output containing the detected warnings will be saved under `aletheia/output/{app}/analysis/`.

### Gathering Paper Results

To gather the results, you can either manually install the dependencies or use Docker.

#### Option 1: Installing Dependencies

Install Python requirements:

```zsh
pip3 install -r requirements.txt
```

Install [Cloc](https://github.com/aldanial/cloc#install-via-package-manager) to count the number of lines of code for each realistic application:

```zsh
# Example for Debian, Ubuntu
sudo apt install cloc
# Example for macOS
brew install cloc
```

#### Option 2: Setting up Docker

For simplicity, we provide a Docker image to easily gather the results.

Build the Docker image from the repository root:

```zsh
docker build -t aletheia-eval .
```

Run the Docker container mounting the current repository:

```zsh
docker run --rm -it -v "$PWD":/aletheia-eval aletheia-eval
```

#### Collecting Results from Experiments

Run the following script to collect all results from the experiments:

```zsh
./collect.sh
```

Internally, `collect.sh` executes the following scripts in order to collect the results:

| Script                | Purpose                                                                                          | Inputs                                        | Outputs                                                                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `collect_warnings.py` | collect warnings per pattern, compare actual vs expected, compute TP/FP/FN, precision and recall | `aletheia/output/{app}/`<br>`expected/{app}/` | `paper/tmp/table2_real_detection.txt`                                                                                                               |
| `collect_metrics.py`  | collect app characteristics (microservices, datastores, LOC, call graphs) and analysis time      | `aletheia/eval/metrics/{date}/`       | `results/metrics-realistic.yaml`<br>`results/metrics-synthetic.yaml`<br>`paper/tmp/table2_real_metrics.txt`<br>`paper/tmp/table3_synth_metrics.txt` |
| `collect_memory.py`   | collect average peak memory usage                                                                | `aletheia/eval/memory/{date}/`        | `results/memory-realistic.txt`<br>`results/memory-synthetic.txt`<br>`paper/tmp/table2_real_memory.txt`<br>`paper/tmp/table3_synth_memory.txt`       |

> [!WARNING]
> The scripts gather all results for the **current date** under `aletheia/eval/{memory,metrics}/{date}/`. If you want to rerun the experiments, make sure to clean up these directories beforehand.

The files saved to `paper/tmp/` contain the results that are later aggregated when creating the tables seen in the paper.

The files saved to `results/` contain the averaged results across all five runs used to generate the results in `paper/tmp/`. The files are also used by the `create_plot.py` script to generate the plot for the analysis time.

Now, you can finally generate the paper's results for Table 2, Table 3, and Figure 5.

First, generate results for Table 2 and Table 3. The script aggregates the results in `paper/tmp/`:

```zsh
python3 create_tables.py
```

The tables will be saved in `paper/table2-realistic-apps.txt` and `paper/table3-synthetic-apps.txt`.

Finally, generate results for Figure 5. The script reads the analysis time results in `results/metrics-realistic.yaml` and `results/metrics-synthetic.yaml` and creates a plot:

```zsh
python3 create_plot.py
```

The plot will be saved in `paper/figure5-realistic-synthetic.png`.

#### Extra: Detailed Analysis Results

Optionally, you can also see detailed analysis results for each application.

You can check the colored diff between the actual warnings in `aletheia/output/{app}/analysis/` and the expected warnings in `expected/{app}/analysis`. The red lines show missing warnings (false negatives), and green lines show extra warnings (false positives) produced by Aletheia. The script works iteratively:

```zsh
python3 collect_warnings.py {app} analysis

# Example:
python3 collect_warnings.py trainticket analysis
```

You can also check the quantitative metrics (number of TP/FP/FN, precision, recall) for each constraint violation pattern using the following command:

```zsh
python3 collect_warnings.py {app} metrics

# Example:
python3 collect_warnings.py trainticket metrics
```
