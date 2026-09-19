import os
import json
from typing import List, Dict, Any
from .models import Invoice, SubscriberInfo

class JsonStorage:
    def __init__(self, base_dir: str, subscriber_code: str):
        self.file_path = os.path.join(base_dir, f"{subscriber_code}_invoices.json")
        os.makedirs(base_dir, exist_ok=True)

    def save(self, subscriber_info: SubscriberInfo, invoices: List[Invoice]):
        data = {
            "subscriber_info": subscriber_info.model_dump(),
            "invoices": [inv.model_dump(by_alias=True) for inv in invoices]
        }
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load(self) -> Tuple[Optional[SubscriberInfo], List[Invoice]]:
        if not os.path.exists(self.file_path):
            return None, []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            sub_info = SubscriberInfo(**data["subscriber_info"])
            invoices = [Invoice(**inv) for inv in data["invoices"]]
            return sub_info, invoices
        except Exception as e:
            print(f"Error loading data: {e}")
            return None, []

    def update_incremental(self, subscriber_info: SubscriberInfo, new_invoices: List[Invoice]):
        old_sub, old_invoices = self.load()
        
        if not old_invoices:
            self.save(subscriber_info, new_invoices)
            return

        # Use Period as key for simplicity, or N.DOC if preferred
        # Let's use N. DOC as it's more unique
        existing_doc_numbers = {inv.doc_number for inv in old_invoices}
        
        added_count = 0
        for inv in new_invoices:
            if inv.doc_number not in existing_doc_numbers:
                old_invoices.append(inv)
                added_count += 1
        
        if added_count > 0:
            # We update subscriber info as well in case it changed
            self.save(subscriber_info, old_invoices)
            print(f"Incremental update: Added {added_count} new invoices.")
        else:
            print("No new invoices to add.")

from typing import Tuple
