# -*- coding: utf-8 -*-
"""SkillModel.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1CzCcrY-3DoliNtkWvIUkI46mi1pzjFjo
"""

import json
from transformers import pipeline

# Define a list of stop words
stop_words = ["Business", "logic", "https", "data", "management", "Computer", "Science"]

# Map entity group names to new names
entity_group_mapping = {
    "B-TECHNOLOGY": "TECHNOLOGY",
    "I-TECHNOLOGY": "TECHNOLOGY",
    "B-TECHNICAL": "TECHNICAL",
    "I-TECHNICAL": "TECHNICAL",
    "B-BUS": "BUSINESS",
    "I-BUS": "BUSINESS",  # Combine "B-BUS" and "I-BUS" into a single entity
    "B-SOFT": "SOFT"
}

# Function to combine subwords and merge multi-word entities into single entities
def combine_subwords(ner_results):
    combined_output = []
    i = 0
    while i < len(ner_results):
        word = ner_results[i]["word"]
        if word.startswith("##"):
            # Combine subwords
            combined_word = word[2:]  # Remove the "##" prefix
            while i + 1 < len(ner_results) and ner_results[i+1]["word"].startswith("##"):
                combined_word += ner_results[i+1]["word"][2:]
                i += 1
            combined_output[-1]["word"] += combined_word
        else:
            # Merge multi-word entities into single entities
            if i + 1 < len(ner_results) and "entity" in ner_results[i+1] and ner_results[i+1]["entity"] == ner_results[i]["entity"]:
                j = i + 1
                while j < len(ner_results) and "entity" in ner_results[j] and ner_results[j]["entity"] == ner_results[i]["entity"]:
                    word += " " + ner_results[j]["word"]
                    j += 1
                i = j - 1
            # Exclude stop words
            if word not in stop_words:
                # Map entity group names to new names
                entity_group = entity_group_mapping.get(ner_results[i]["entity"], ner_results[i]["entity"])
                # Check if the word is "Java" or "C" and update entity_group if necessary
                if word in ["Java", "C"]:
                    entity_group = "TECHNICAL"
                combined_output.append({
                    "entity_group": entity_group,
                    "word": word,
                })
        i += 1
    return combined_output

# Function to combine "MS" and "SQL" into "MS SQL"
def combine_ms_sql(combined_output):
    i = 0
    while i < len(combined_output) - 1:
        if combined_output[i]["word"] == "MS" and combined_output[i+1]["word"] == "SQL":
            combined_output[i]["word"] = "MS SQL"
            del combined_output[i+1]
        else:
            i += 1
    return combined_output

# Function to process large input text
def process_large_text(input_text, chunk_size=1000):
    # Initialize an empty dictionary to store word counts
    word_counts = {}
    entity_group_counts = {}

    # Split the input text into smaller chunks
    chunks = [input_text[i:i+chunk_size] for i in range(0, len(input_text), chunk_size)]

    # Instantiate the pipeline for token classification
    pipe = pipeline("token-classification", model="GalalEwida/lm-ner-skills-extractor_BERT")

    # Process each chunk individually
    for chunk in chunks:
        # Perform named entity recognition
        ner_results = pipe(chunk)

        # Combine subwords into complete words
        combined_output = combine_subwords(ner_results)

        # Combine "MS" and "SQL" into "MS SQL"
        combined_output = combine_ms_sql(combined_output)

        # Update word counts
        for entity in combined_output:
            word = entity["word"]
            entity_group = entity["entity_group"]
            key = (word, entity_group)
            word_counts[key] = word_counts.get(key, 0) + 1
            entity_group_counts[entity_group] = entity_group_counts.get(entity_group, 0) + 1

    return word_counts, entity_group_counts

# Example large input text (replace with your actual text)
# large_input_text = """
#     John is proficient in MS SQL and aws and has experience with MySQL.
# """

large_input_text = input()

# Process the large input text to get word counts
word_counts, entity_group_counts = process_large_text(large_input_text)

# Create a list of unique words with their counts and entity groups
unique_words_with_counts = []

# Calculate the percentage for each word
for (word, entity_group), count in word_counts.items():
    total_count = entity_group_counts[entity_group]
    percentage = (count / total_count) * 100
    unique_words_with_counts.append({
        "word": word,
        "entity_group": entity_group,
        # "count": count,
        "Percentage": f"{percentage:.2f}%"
    })

# Convert the list to JSON format
json_output = json.dumps(unique_words_with_counts, indent=2)

# Print the JSON output
print(json_output)

# Calculate the percentage for each entity_group
entity_group_percentages = {}
total_entities = sum(entity_group_counts.values())
for entity_group, count in entity_group_counts.items():
    percentage = (count / total_entities) * 100
    entity_group_percentages[entity_group] = percentage

# Print the percentage and total count for each entity_group
print("Percentage and total count for each entity group:")
for entity_group, percentage in entity_group_percentages.items():
    count = entity_group_counts[entity_group]
    print(f"{entity_group}: {percentage:.2f}%, Total Count: {count}")