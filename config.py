import os

#USE_MONGO = os.getenv("USE_MONGO", "False") == "True"
USE_MONGO = True  # False कर दो तो फिर JSON काम करेगा

# 🛠 MongoDB Configuration
MONGO_URI = "mongodb+srv://pankajsainikishanpura02:SHivxQzJdLrvbA9M@cluster0.tftxnvm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "botdb"
