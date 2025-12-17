# SCRIPT 1: SYNC PI STATUS

# 1. Find Subscriptions linked to this Invoice
# We search the Child Table for the invoice name
linked_subscriptions = frappe.get_all("Payment Method", 
    filters={"purchase_invoice": doc.name}, 
    fields=["parent"]
)

for link in linked_subscriptions:
    if link.parent:
        # 2. Fetch the Subscription Document
        sub_doc = frappe.get_doc("Internal Subscription", link.parent)
        
        # 3. Update the specific row in the subscription
        # We iterate to find the matching row
        for row in sub_doc.payment_method:
            if row.purchase_invoice == doc.name:
                row.status = doc.status
                row.posting_date = doc.posting_date
                
        # 4. Save the Subscription
        # This acts as the trigger for Cycle logic  Script  to recalculate the dates
        sub_doc.save(ignore_permissions=True)