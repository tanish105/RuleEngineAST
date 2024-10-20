# Filename: mongo_db_storage.py
from urllib.parse import quote_plus
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

# Retrieve MongoDB connection details from .env
db_user = quote_plus(os.getenv('DB_USER'))
db_password = quote_plus(os.getenv('DB_PASSWORD'))
db_cluster = os.getenv('DB_CLUSTER')
db_name = os.getenv('DB_NAME')
db_appname = os.getenv('DB_APPNAME')

# Construct MongoDB connection string
mongo_url = f"mongodb+srv://{db_user}:{db_password}@{db_cluster}/?retryWrites=true&w=majority&appName={db_appname}"

# Connect to your MongoDB cluster
client = MongoClient(mongo_url)
db = client[db_name]  # Select the database
rules_collection = db.rules  # Select the collection

# Function to store a rule (AST) in MongoDB
def store_rule(rule_tree, rule_id):
    rule_document = {
        "_id": rule_id,
        "rule_tree": rule_tree,
        "metadata": {
            "created_at": datetime.utcnow(),
            "modified_at": datetime.utcnow()
        }
    }
    rules_collection.insert_one(rule_document)
    print(f"Rule with ID {rule_id} inserted.")

# Function to fetch a rule by ID from MongoDB
def fetch_rule_by_id(rule_id):
    rule_document = rules_collection.find_one({"_id": rule_id})
    if rule_document:
        print(f"Rule found: {json.dumps(rule_document, indent=4)}")
        return rule_document
    else:
        print(f"No rule found with ID {rule_id}.")
        return None
