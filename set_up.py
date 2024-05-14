from openai import OpenAI, AssistantEventHandler
from typing_extensions import override
import os
import json
import time

client = OpenAI(api_key="")

def show_json(obj):
    print(json.loads(obj.model_dump_json()))

#Files
file_paths = ["resources/warhammer_core_rules.pdf","resources/astra_militarum_rules.pdf","resources/adeptas_sororitas_rules.pdf"]
file_streams = [open(path, "rb") for path in file_paths]

vector_store = client.beta.vector_stores.create(name="Warhammer Books")

file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)

# Step 1: Create an Assistant
assistant = client.beta.assistants.create(
    name="Warhammer Master",
    instructions="You are a warhammer 40k specialist. You help people by answering their questions about the game's rules and each army's rules.",
    tools=[{"type": "file_search"}],
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    # model="gpt-3.5-turbo",
    model="gpt-4-1106-preview",
)

# Step 2: Create a Thread
thread = client.beta.threads.create()

# Step 3: Add a Message to a Thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="What are the combat phases in Warhammer 40k?"
)

# Step 4: Run the Assistant
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Please provide the requested information"
)

# Waits for the run to be completed. 
while True:
    run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, 
                                                   run_id=run.id)
    if run_status.status == "completed":
        break
    elif run_status.status == "failed":
        print("Run failed:", run_status.last_error)
        break
    time.sleep(2)  # wait for 2 seconds before checking again


# Step 5: Parse the Assistant's Response and print the Results
messages = client.beta.threads.messages.list(
    thread_id=thread.id
)

# Prints the messages the latest message the bottom
# number_of_messages = len(messages.data)
# print( f'Number of messages: {number_of_messages}')

# for message in reversed(messages.data):
#     role = message.role
    
#     for content in message.content:
#         if content.type == 'text':
#             response = content.text.value
#             print(f'\n{role}: {response}')

message_content = message.content[0].text
annotations = message_content.annotations
citations = []
# Iterate over the annotations and add footnotes
for index, annotation in enumerate(annotations):
    # Replace the text with a footnote
    message_content.value = message_content.value.replace(annotation.text, f' [{index}]')
    # Gather citations based on annotation attributes
    print(client.files.retrieve(file_citation.file_id))
    if (file_citation := getattr(annotation, 'file_citation', None)):
        cited_file = client.files.retrieve(file_citation.file_id)
        citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
    elif (file_path := getattr(annotation, 'file_path', None)):
        cited_file = client.files.retrieve(file_path.file_id)
        citations.append(f'[{index}] Click <here> to download {cited_file.filename}')

message_content.value += '\n' + '\n'.join(citations)



