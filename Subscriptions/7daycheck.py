from frappe.utils import add_months, getdate, nowdate, add_days

# 1. Get all Active subscriptions
subs = frappe.get_all("Internal Subscription", 
    filters={"status": ["in", ["Active", "Draft"]]}, 
    fields=["name", "subscription_start_date"]
)

for sub in subs:
    doc = frappe.get_doc("Internal Subscription", sub.name)
    
    # --- A. RE-RUN LOGIC ---
    # We simply save the document. 
    # This triggers "Script 2" above, which recalculates "Past Due" vs "Active"
    doc.save(ignore_permissions=True)
    
    # --- B. 7-DAY WARNING CHECKER ---
    if doc.subscription_end_date:
        days_remaining = (getdate(doc.subscription_end_date) - getdate(nowdate())).days
        
        if days_remaining == 7:
            # Create a ToDo or Email Alert
            frappe.get_doc({
                "doctype": "ToDo",
                "owner": doc.owner,
                "description": f"Reminder: Internal Subscription {doc.name} expires in 7 days.",
                "reference_type": "Internal Subscription",
                "reference_name": doc.name,
                "assigned_by": "Administrator"
            }).insert(ignore_permissions=True)
            
            # Optional: Log to console if debugging
            print(f"7 Day Warning triggered for {doc.name}")