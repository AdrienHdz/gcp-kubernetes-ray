# Adapted from Ray's template
from ray.job_submission import JobSubmissionClient

client = JobSubmissionClient("http://127.0.0.1:8265")

kick_off_pytorch_benchmark = (
    "python main.py"
)


submission_id = client.submit_job(
    entrypoint=kick_off_pytorch_benchmark,
    runtime_env={
        "working_dir": "./parallelize_torch/"
    }
)

print("Use the following command to follow this Job's logs:")
print(f"ray job logs '{submission_id}' --address http://127.0.0.1:8265 --follow")