### Huggingface Training (training script for single GPU)

from datasets import load_dataset

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig, get_peft_model
from datasets import Dataset

# Environment Setup
# !export TOKENIZERS_PARALLELISM=false
# !export CUDA_VISIBLE_DEVICES=0
torch.utils.checkpoint.use_reentrant = True

# Dataset helper functions
system_message = """You are a helpful AI assistant. Users will ask you questions and you will answer the questions."""

def create_conversation(sample):
  messages = [{"role": "system", "content": system_message.format(schema=sample["source"])}]
  conversation = sample["conversations"]
  for i, message in enumerate(conversation):
    if i % 2 == 0:
      messages.append({"role": "user", "content": message})
    else:
      messages.append({"role": "assistant", "content": message})
  return { "messages": messages }

# Customized chat template to pass to the tokenizer 
# However, We use the llama 3 instruct chat template
def format_messages(sample):
    text = ""
    for message in sample["messages"]:
        if message["role"] == "system":
            text += f"<|system|>{message['content']}\n"
        elif message["role"] == "user":
            text += f"<|user|>{message['content']}\n"
        elif message["role"] == "assistant":
            text += f"<|assistant|>{message['content']}\n"
    return {"text": text}

# Load training datasets
train_dataset = load_dataset("GAIR/lima", cache_dir="~/storage/hf-datasets", split="train")
train_dataset = train_dataset.map(create_conversation, batched=False)
train_dataset = train_dataset.remove_columns(["conversations", "source"])
# Dataset Sample
print("Sample Multi-turn Dataset Item:")
print("----------------------")
messages = train_dataset[-1]['messages']
print('\n\n'.join([f"{message['role']}:\n------\n{message['content']}" for message in messages]))

# Tokenizer configs and initialization
model_name = "meta-llama/Llama-3.1-8B"

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
tokenizer.padding_side = "right"
tokenizer.pad_token = tokenizer.eos_token

messages = train_dataset['messages']

# chat_temmplate is of LlaMa
formatted_text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    bos_token="<|begin_of_text|>",
    chat_template="{{- bos_token }}\n{%- if custom_tools is defined %}\n    {%- set tools = custom_tools %}\n{%- endif %}\n{%- if not tools_in_user_message is defined %}\n    {%- set tools_in_user_message = true %}\n{%- endif %}\n{%- if not date_string is defined %}\n    {%- set date_string = \"26 Jul 2024\" %}\n{%- endif %}\n{%- if not tools is defined %}\n    {%- set tools = none %}\n{%- endif %}\n\n{#- This block extracts the system message, so we can slot it into the right place. #}\n{%- if messages[0]['role'] == 'system' %}\n    {%- set system_message = messages[0]['content']|trim %}\n    {%- set messages = messages[1:] %}\n{%- else %}\n    {%- set system_message = \"\" %}\n{%- endif %}\n\n{#- System message + builtin tools #}\n{{- \"<|start_header_id|>system<|end_header_id|>\\n\\n\" }}\n{%- if builtin_tools is defined or tools is not none %}\n    {{- \"Environment: ipython\\n\" }}\n{%- endif %}\n{%- if builtin_tools is defined %}\n    {{- \"Tools: \" + builtin_tools | reject('equalto', 'code_interpreter') | join(\", \") + \"\\n\\n\"}}\n{%- endif %}\n{{- \"Cutting Knowledge Date: December 2023\\n\" }}\n{{- \"Today Date: \" + date_string + \"\\n\\n\" }}\n{%- if tools is not none and not tools_in_user_message %}\n    {{- \"You have access to the following functions. To call a function, please respond with JSON for a function call.\" }}\n    {{- 'Respond in the format {\"name\": function name, \"parameters\": dictionary of argument name and its value}.' }}\n    {{- \"Do not use variables.\\n\\n\" }}\n    {%- for t in tools %}\n        {{- t | tojson(indent=4) }}\n        {{- \"\\n\\n\" }}\n    {%- endfor %}\n{%- endif %}\n{{- system_message }}\n{{- \"<|eot_id|>\" }}\n\n{#- Custom tools are passed in a user message with some extra guidance #}\n{%- if tools_in_user_message and not tools is none %}\n    {#- Extract the first user message so we can plug it in here #}\n    {%- if messages | length != 0 %}\n        {%- set first_user_message = messages[0]['content']|trim %}\n        {%- set messages = messages[1:] %}\n    {%- else %}\n        {{- raise_exception(\"Cannot put tools in the first user message when there's no first user message!\") }}\n{%- endif %}\n    {{- '<|start_header_id|>user<|end_header_id|>\\n\\n' -}}\n    {{- \"Given the following functions, please respond with a JSON for a function call \" }}\n    {{- \"with its proper arguments that best answers the given prompt.\\n\\n\" }}\n    {{- 'Respond in the format {\"name\": function name, \"parameters\": dictionary of argument name and its value}.' }}\n    {{- \"Do not use variables.\\n\\n\" }}\n    {%- for t in tools %}\n        {{- t | tojson(indent=4) }}\n        {{- \"\\n\\n\" }}\n    {%- endfor %}\n    {{- first_user_message + \"<|eot_id|>\"}}\n{%- endif %}\n\n{%- for message in messages %}\n    {%- if not (message.role == 'ipython' or message.role == 'tool' or 'tool_calls' in message) %}\n        {{- '<|start_header_id|>' + message['role'] + '<|end_header_id|>\\n\\n'+ message['content'] | trim + '<|eot_id|>' }}\n    {%- elif 'tool_calls' in message %}\n        {%- if not message.tool_calls|length == 1 %}\n            {{- raise_exception(\"This model only supports single tool-calls at once!\") }}\n        {%- endif %}\n        {%- set tool_call = message.tool_calls[0].function %}\n        {%- if builtin_tools is defined and tool_call.name in builtin_tools %}\n            {{- '<|start_header_id|>assistant<|end_header_id|>\\n\\n' -}}\n            {{- \"<|python_tag|>\" + tool_call.name + \".call(\" }}\n            {%- for arg_name, arg_val in tool_call.arguments | items %}\n                {{- arg_name + '=\"' + arg_val + '\"' }}\n                {%- if not loop.last %}\n                    {{- \", \" }}\n                {%- endif %}\n                {%- endfor %}\n            {{- \")\" }}\n        {%- else  %}\n            {{- '<|start_header_id|>assistant<|end_header_id|>\\n\\n' -}}\n            {{- '{\"name\": \"' + tool_call.name + '\", ' }}\n            {{- '\"parameters\": ' }}\n            {{- tool_call.arguments | tojson }}\n            {{- \"}\" }}\n        {%- endif %}\n        {%- if builtin_tools is defined %}\n            {#- This means we're in ipython mode #}\n            {{- \"<|eom_id|>\" }}\n        {%- else %}\n            {{- \"<|eot_id|>\" }}\n        {%- endif %}\n    {%- elif message.role == \"tool\" or message.role == \"ipython\" %}\n        {{- \"<|start_header_id|>ipython<|end_header_id|>\\n\\n\" }}\n        {%- if message.content is mapping or message.content is iterable %}\n            {{- message.content | tojson }}\n        {%- else %}\n            {{- message.content }}\n        {%- endif %}\n        {{- \"<|eot_id|>\" }}\n    {%- endif %}\n{%- endfor %}\n{%- if add_generation_prompt %}\n    {{- '<|start_header_id|>assistant<|end_header_id|>\\n\\n' }}\n{%- endif %}\n",
    clean_up_tokenization_spaces=True,
    eos_token="<|eot_id|>",
)

train_dataset_tokenized = tokenizer(
    formatted_text,
    padding=True,
    truncation=True,
    return_attention_mask=True,
    return_tensors="pt",
)

# Alternatively, the paddings and attention masks can be created using the collator 
# data_collator = DataCollatorWithPadding(
#     tokenizer=tokenizer
# )

# Create proper datasets from the tokenized data
dataset = Dataset.from_dict({
	"input_ids": train_dataset_tokenized['input_ids'].tolist(),
	"attention_mask": train_dataset_tokenized['attention_mask'].tolist(),
})

split_dataset = dataset.train_test_split(test_size=0.2, seed=42)
train_dataset = split_dataset["train"]
test_dataset = split_dataset["test"]

print("Tokenized Dataset Sample:\n----------------------")
print(tokenizer.decode(train_dataset[-1]["input_ids"]))
print(f"\n----------------------\n\nTraining set size: {len(train_dataset)}")
print(f"Test set size: {len(test_dataset)}")
max_input_seq_len = len(train_dataset[-1]["input_ids"])
print(f"\n----------------------\nFinalized max sequence length: {max_input_seq_len}\n")


# Quantization Configs
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True, 
    bnb_4bit_use_double_quant=True, 
    bnb_4bit_quant_type="nf4", 
    bnb_4bit_compute_dtype=torch.float16
)

# PEFT
output_directory="./output/"
peft_model_id=output_directory+"model"
# Lora Configs
lora_config = LoraConfig(
    r = 8,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)

# Model Configs
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    quantization_config=bnb_config
)
model = get_peft_model(model, lora_config)
# Load the model with the quantization config
# model.resize_token_embeddings(len(tokenizer))
# model.config.use_cache = False
model.to("cuda:0")

# Training Configs
sft_configs = SFTConfig(
    output_dir=output_directory+"checkpoints",
    logging_dir=output_directory+"logs",
    optim="paged_adamw_8bit",
    per_device_train_batch_size=1,
    lr_scheduler_type="cosine",
    logging_strategy="steps",
    logging_steps=250,
    max_seq_length=max_input_seq_len,
    packing=False,
    dataset_kwargs={
        "add_special_tokens": False,
        "append_concat_token": False
    },
    dataset_text_field='text',
    num_train_epochs=1,         # 1-3 is recommended
    gradient_accumulation_steps=4,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
    save_strategy="epoch",
    learning_rate=2e-4,
    fp16=True,
    max_grad_norm=0.3,
    warmup_ratio=0.03,
    report_to="none",
    push_to_hub=False,
    save_steps=5000,
    eval_strategy="steps",
    eval_steps=5000,
    eval_packing=False,
)

print("Started Training...\n")
# Start Training
trainer = SFTTrainer(
    model=model,
    args=sft_configs,
    train_dataset=train_dataset,
    peft_config=lora_config,
    processing_class=tokenizer,
    eval_dataset=test_dataset
)

trainer.train()

trainer.model.save_pretrained(peft_model_id)
tokenizer.save_pretrained(peft_model_id)
print(f"Model and tokenizer saved to {peft_model_id}")