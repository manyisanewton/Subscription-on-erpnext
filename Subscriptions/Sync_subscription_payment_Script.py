# 1. Check if this Invoice is linked to any Internal Subscription's child table
# Note: Replace 'Payment Method' with the actual Child Table DocType name if different (e.g., 'Internal Subscription Payment')
linked_subscriptions = frappe.get_all("Payment Method", 
    filters={"purchase_invoice": doc.name}, 
    fields=["parent", "name"]
)

for link in linked_subscriptions:
    # 2. Fetch the Subscription Document
    sub_doc = frappe.get_doc("Internal Subscription", link.parent)
    
    # 3. Find the specific row and update status
    for row in sub_doc.payment_method:
        if row.purchase_invoice == doc.name:
            row.status = doc.status
            row.posting_date = doc.posting_date
            
    # 4. Save the Subscription
    # This automatically triggers Script 2 (below) to recalculate dates/cycles
    sub_doc.save(ignore_permissions=True)