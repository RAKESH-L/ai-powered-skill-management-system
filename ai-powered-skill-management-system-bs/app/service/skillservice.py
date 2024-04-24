import pymysql
from transformers import pipeline

# Define MySQL database connection parameters
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'skilldataset'

# Define a list of stop words
stop_words = ["Business", "logic", "https", "data", "management", "Computer", "Science", "Server", "Web", 
              "development", "software"]

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

# Function to process large input text and save to database
def process_large_text_and_save_to_database(input_text, employee_id, chunk_size=1000):
        # Initialize database connection
    connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

    try:
        with connection.cursor() as cursor:
            # Check if employeeId already exists in skillModel table
            sql_check_employee_id = "SELECT id FROM skillModel WHERE employeeId = %s"
            cursor.execute(sql_check_employee_id, (employee_id,))
            existing_skill_model = cursor.fetchone()

            if not existing_skill_model:
                # Insert data into skillModel table
                sql_insert_skill_model = "INSERT INTO skillModel (employeeId) VALUES (%s)"
                cursor.execute(sql_insert_skill_model, (employee_id,))
                skill_model_id = cursor.lastrowid
            else:
                skill_model_id = existing_skill_model[0]

            # Delete existing records associated with the employeeId
            sql_delete_skillword = "DELETE FROM skillword WHERE skillgroupId IN (SELECT id FROM skillgroup WHERE skillModelId = %s)"
            cursor.execute(sql_delete_skillword, (skill_model_id,))

            sql_delete_skillgroup = "DELETE FROM skillgroup WHERE skillModelId = %s"
            cursor.execute(sql_delete_skillgroup, (skill_model_id,))

            # Process large text
            word_counts, entity_group_counts = process_large_text(input_text, chunk_size)

            # Insert data into skillgroup table and retrieve skillgroup IDs
            skill_group_ids = {}
            for entity_group, count in entity_group_counts.items():
                total_entities = sum(entity_group_counts.values())
                percentage = (count / total_entities) * 100
                sql = "INSERT INTO skillgroup (Type, percentage, total_count, skillModelId) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (entity_group, percentage, count, skill_model_id))
                skill_group_ids[entity_group] = cursor.lastrowid

            # Insert data into skillword table
            for (word, entity_group), count in word_counts.items():
                if entity_group in skill_group_ids:
                    total_count_in_entity_group = entity_group_counts.get(entity_group, 1)
                    percentage = (count / total_count_in_entity_group) * 100
                    sql = "INSERT INTO skillword (word, percentage, entity_group, total_count_in_entity_group, skillgroupId) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (word, percentage, entity_group, count, skill_group_ids[entity_group]))

        # Commit changes to the database
        connection.commit()

    finally:
        # Close the database connection
        connection.close()
        
        
# Function to create database and tables
def create_database_and_tables():
    # Initialize database connection
    connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)

    try:
        with connection.cursor() as cursor:
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")

            # Use the database
            cursor.execute(f"USE {DB_NAME}")

            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skillModel (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    employeeId INT,
                    FOREIGN KEY (employeeId) REFERENCES employee(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skillgroup (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    Type VARCHAR(255),
                    percentage FLOAT,
                    total_count INT,
                    skillModelId INT,
                    FOREIGN KEY (skillModelId) REFERENCES skillModel(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skillword (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    word VARCHAR(255),
                    percentage FLOAT,
                    entity_group VARCHAR(255),
                    total_count_in_entity_group INT,
                    skillgroupId INT,
                    FOREIGN KEY (skillgroupId) REFERENCES skillgroup(id)
                )
            """)
            
            # Commit changes
            connection.commit()

    finally:
        # Close the database connection
        connection.close()