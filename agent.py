import ollama
import json
import torch
import pymupdf4llm
from torch._subclasses.functional_tensor import _conversion_method_template
import re
import pdfplumber
import csv

import url_gen_and_parsing

print("GPU available:", torch.cuda.is_available())
print("Device name:", torch.cuda.get_device_name(0))

# Read the documents provided

# dataset = []
# with open('cat-facts.txt', 'r', encoding='utf-8') as f:
#     dataset = f.readlines()
#     print(f'Loaded {len(dataset)} entries.')

# Models used

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'deepseek-r1:8b'

# Each element in the VECTOR_DB will be a tuple (chunk, embedding)
# The embedding is a list of floats, for example: [0.1, 0.04, -0.34, 0.21, ...]

VECTOR_DB = []

def add_chunk_to_database(chunk):
    embedding = ollama.embed(model=EMBEDDING_MODEL, input=chunk)['embeddings'][0]
    VECTOR_DB.append((chunk, embedding))

# we should increase the chunk size here (like 3-4 lines, not just 1 line)
# we should implement overlapping so that we will not lose the 'margin' of a chunk

# CHUNK_SIZE = 5
# k = 0
# for i in range(0, len(dataset), CHUNK_SIZE):
#
#     chunk_elements = dataset[k:i + CHUNK_SIZE]
#     chunk = '\n'.join(chunk_elements)
#
#     k = i + CHUNK_SIZE - 2
#
#     add_chunk_to_database(chunk)
#     print(f'Added chunk {i+1 // CHUNK_SIZE + 1} to the database.')
#     print(chunk)

# Implement the retrieval function

def cosine_similarity(a, b):
    dot_product = sum([x*y for x,y in zip(a, b)])
    norm_a = sum([x ** 2 for x in a]) ** 0.5
    norm_b = sum([x ** 2 for x in b]) ** 0.5
    return dot_product / (norm_a * norm_b)

# Implement the retrieval function

def retrieve(query, top_n = 3):
    query_embedding = ollama.embed(model=EMBEDDING_MODEL, input=query)['embeddings'][0]

    # temporary list to store (chunk, similarity) pairs

    similarities = []

    for chunk, embedding in VECTOR_DB:
        similarity = cosine_similarity(query_embedding, embedding)
        similarities.append((chunk, similarity))

    # sort by similarity in descending order, because higher similarity means more relevant chunks

    similarities.sort(key=lambda x: x[1], reverse=True)

    return similarities[:top_n]

def get_cities_IATA():

    pdf_file = "IATA-Code-List.pdf"
    csv_file = "output.csv"

    rows = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    rows.append([line])

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["content"])
        writer.writerows(rows)

    print("CSV generated:", csv_file)

def read_csv_file_and_populate_embeddings_database():
    with open('output.csv', "r", encoding="utf-8") as f:
        csv_file = csv.reader(f)


    return csv_file


# Generation phase
def generate():
    input_query = input('Ask me a question: ')

        # retrieved_knowledge = retrieve(input_query)
        #
        # print('Retrieve knowledge:')
        # for chunk, similarity in retrieved_knowledge:
        #     if similarity > 0.65:
        #         print(f' - (similarity: {similarity:.2f}) {chunk}')

        #instruction_prompt = f"You are a helpful chatbot." # + "Use only the following pieces of context to answer the question. Don't make up any new information:" + "{'\n'.join([f' - {chunk}' for chunk, similarity in retrieved_knowledge])}"

    instruction_prompt = (f'You are a helpful chatbot that gets the input from user and tokenizes it and returns it in a JSON format like:'
                              "{'dates': {'departureFrom': '','departureTo': '', 'returnFrom': '', 'returnTo': '', 'anytime': True/False, 'stayTime': {'min': '', 'max': ''}}, 'passengers': {'adults': 1, 'children': 0, 'infants': 0,'youth': 0}, 'locations': {'origins': [{'code': 'BUH', 'type': 'CITY'}],'destinations': [{'code': '*', 'type': 'ANYWHERE'}]}, 'deduplicate': False, 'luggageOptions': { 'personalItemCount': 1, 'cabinTrolleyCount': 0, 'checkedBaggageCount': 0}}"
                              "If the user does not provide all the required data, complete the missing data with 0 or '', depending on the field."
                              "Do not generate random data. Use only what the user provides."
        )
        # formatam / continuam discutia pana cand toate datele/datele necesare au fost obtinute

    stream = ollama.chat(
        model=LANGUAGE_MODEL,
        messages=[
        {'role': 'system', 'content': instruction_prompt},
        {'role': 'user', 'content': input_query},
        ],
        stream=True,
    )

    # print the response from the chatbot in real-time
    print('Chatbot response:')

    response_text = ''

    for chunk in stream:

        current_chunk = chunk['message']['content']
        print(current_chunk, end='', flush=True)
        response_text += current_chunk

    # data_dictionary = {}
    #
    # # Extrage continutul JSON daca e in code block
    # match = re.search(r'```json(.*?)```', response_text, re.DOTALL)
    # json_text = match.group(1).strip() if match else response_text.strip()
    #
    # # Incarca sigur JSON
    # data_dictionary = json.loads(json_text)
    #
    # print(data_dictionary)

    formatted_response = response_text.replace('```', '').replace('json', '')

    url_gen_and_parsing.extract_flights(formatted_response)

    #print(type(data_dictionary))


if __name__ == '__main__':
    #get_cities_IATA()

    dataset = read_csv_file_and_populate_embeddings_database()

    for i, chunk in enumerate(dataset):
        add_chunk_to_database(chunk)
        print(f'Added chunk {i + 1}/{len(dataset)} to the database')

    #generate()

