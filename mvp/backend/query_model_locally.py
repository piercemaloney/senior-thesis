# Import necessary libraries
from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList
import torch

# Check if MPS (Apple Silicon GPU) device is available and set it as the device
if torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")  # Fallback to CPU if MPS is not available

print(f"Using device: {device}")

# Define paths for the model and tokenizer
model_save_path = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/models/llemma_7b_model'
tokenizer_save_path = '/Users/piercemaloney/Desktop/Thesis/senior-thesis/mvp/backend/models/llemma_7b_tokenizer'

# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(tokenizer_save_path)
tokenizer.pad_token = "</s>"
for t in [4920, 441, 2178, 29889]:
    print(t, tokenizer.decode([t]))

# print(tokenizer.decode([10456]))
model = AutoModelForCausalLM.from_pretrained(model_save_path, torch_dtype="auto",).to(device)  # Move model to the specified device

# model.eval()  # Ensure the model is in evaluation mode


print("Model loaded successfully!")
print(model)

class StopAtPeriodCriteria(StoppingCriteria):
    def __call__(self, input_ids, scores, **kwargs):
        # Decode the last generated token to text
        last_token_text = tokenizer.decode(input_ids[:, -1], skip_special_tokens=True)
        # Check if the decoded text ends with a period
        return '.' in last_token_text

stopping_criteria = StoppingCriteriaList([StopAtPeriodCriteria()])


# Example usage


prompt = "I want to go to the"

result = model.generate(input_ids=tokenizer(prompt, return_tensors="pt").input_ids.to(device), 
                               max_length=50, 
                               stopping_criteria=stopping_criteria, 
                                 do_sample=True,
                                    temperature=0.7,
                                    top_k=10,
                                    top_p=0.95,
                               )

# Decode generated ids to text
generated_text = tokenizer.decode(result[0], skip_special_tokens=True)

print(generated_text)