from llm import generate
from db import db

print(generate("Say hello in one short sentence."))
db.ping.insert_one({"ok": True})
print(db.ping.find_one())
db.ping.drop()