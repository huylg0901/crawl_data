import json
import transformers
import torch
import re

def clean_text(text):
    # Thay thế tất cả các ký tự đặc biệt bằng khoảng trắng
    text = re.sub(r'[^\w\s]', ' ', text)
    # Loại bỏ khoảng trắng thừa
    return ' '.join(text.split())

# Load source JSON data
with open('input_edit.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Setup the text generation pipeline
model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
pipeline = transformers.pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device_map="auto",
)

# Output file path for new JSON entries
output_file_path = 'output1.json'
new_data = []  

processed_count = 0
json_data = {} 
for item in data:
    group_name = item.get('group_name', '')
    description = item.get('description', '')
    
    group_name = group_name.replace("\n", " ")
    group_name = group_name.replace("\\n", " ")
    group_name = group_name.replace(">", " ")
    group_name = group_name.replace(")", " ")
    group_name = group_name.replace("(", " ")
    group_name = group_name.replace("!", " ")
    group_name = clean_text(group_name)
    group_name = ' '.join(group_name.split())
    
    description = description.replace("\n", " ")
    description = description.replace("\\n", " ")
    description = description.replace(">", " ")
    description = description.replace(")", " ")
    description = description.replace("(", " ")
    description = description.replace("!", " ")
    description = clean_text(description)
    description = ' '.join(description.split())
    

    if group_name:
        messages = [
            {"role": "system", "content": """ 
                You are an assistant who understands Facebook and social networks well.
                Your goal is to analyze and provide the most accurate information possible.
                Respond in the specified format and return JSON format, using Vietnamese with diacritics. 
                Ensure that the data is accurately represented and properly formatted within the JSON structure
                There must be both { } in the output
                
                You are not allowed to show the text "Here is the output in JSON format:" just show the content in JSON, 
                always make sure that there are both { and }, one of the two cannot be missing.
                
                The input data is included:
                - group_name: the name of a Facebook group/ community. ex: "Chia sẻ bí quyết trắng da"
                - description: description of a Facebook group, written by group admins.

                Your output will consist of the following keys and their corresponding values:
                - group_name: Rewrite the group_name of the input ex: "Chia sẻ bí quyết trắng da",
                - categories: Briefly describe the categories of the Facebook group. ex:  ["Làm đẹp", "Phụ nữ", "Sức khỏe"]
                - keywords: Provide keywords with diacritics that users might use to search for the Facebook group. ex: ["Chăm sóc da", "Trắng da", "Spa", "Thẩm mỹ viện", "Sản phẩm làm đẹp", "Trị nám"]
        
            """},
            {"role": "user", "content": f"group_name: {group_name}\ndescription: {description}"}
        ]

        outputs = pipeline(
            messages,
            max_new_tokens=218,
            eos_token_id=pipeline.tokenizer.eos_token_id,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
        )

        # Extract the generated text
        try:
            generated_text = outputs[0]['generated_text'][-1]['content']
            res = json.loads(generated_text)
            with open(output_file_path, 'a', encoding='utf-8') as file:
                json.dump(res, file, ensure_ascii=False, indent=4)
            processed_count += 1
        except:
            data_miss = {
                "group_name" : group_name,
                "description": description
            }
            with open("miss_data.json",'a',encoding='utf-8') as file:
                json.dump(data_miss,file,ensure_ascii=False, indent=4)
            
print(f"Processed and updated {processed_count} group entries successfully.")
