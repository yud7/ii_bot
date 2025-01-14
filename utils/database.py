import csv

FILE_PATH = "data/users.csv"

def save_user_data(user_data: dict):
    with open(FILE_PATH, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([user_data["name"], user_data["age"], user_data["email"]])
