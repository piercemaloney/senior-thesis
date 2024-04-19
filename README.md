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



# Use the CoqGym Docker image

Pull the image:

```bash
docker pull yangky11/coq-gym
```

This may take a while.

# Run the image, mounting the backend folder to /app and the custom eval environment.

```bash
docker run -it -p 6006:6006 -p 8888:8888 \
-v <path-to-my-eval-env.py>:/workspace/CoqGym/my_eval_env.py \
-v <path-to-backend-folder>:/app \
yangky11/coq-gym
```



