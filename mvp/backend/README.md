## Data Generation

To generate data, use the `yangky11/coq-gym` docker image with this project mounted at `/app`. Inside the docker container, run the `txt_file_builder.py` script as follows:

```bash
python txt_file_builder.py
```

It will create a `data/` directory with `.txt` files corresponding to `coq_projects`.

On the HuggingFace hub, data splits may not contain dashes '-'. They are replaced with underscores '_'.

### Where data generation fails:

ruler-compass-geometry
