from backend.models import DocStore

# ponytail: plain in-memory dict (D-14); swap to FS/DB when a second user exists
doc_store: dict[str, DocStore] = {}
