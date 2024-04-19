## Data Generation

To generate query data, use the `yangky11/coq-gym` docker image with this project mounted at `/app`. Inside the docker container, run the scripts in this order:

```bash
python generate_coq_projects_as_txt.py
```
```bash
python generate_query_data.py
```

It will create and populate the `query_data/` directory.


