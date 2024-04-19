### Enhancing Automated Theorem Proving in Coq with Specialized Large Language Models and Tree of Thoughts

Paper: [Download PDF](./written_final_report.pdf)

## Setup

First, create and activate a conda virtual environment, and run:

```bash
pip install -r backend/requirements.txt
```

to install the required Python packages.

Then, run:

```bash
cd backend
```

Then, run the server

```bash
uvicorn main:app --reload
```

# Use the CoqGym Docker image

In a new terminal, pull the image:

```bash
docker pull yangky11/coq-gym
```

# Run the image

...mounting the backend folder to /app and the custom eval environment, and publish the container's port to the host, so that the theorem-prover can talk to the server.

```bash
docker run -it -p 8888:8888 \
-v <path-to-my-eval-env.py>:/workspace/CoqGym/my_eval_env.py \
-v <path-to-backend-folder>:/app \
yangky11/coq-gym
```

# Generate Query data

Inside the container, run:

```bash
cd /app/backend
```

```bash
python generate_coq_projects_as_txt.py
```

```bash
python generate_query_data.py
```

It will create and populate the `query_data/` directory.
