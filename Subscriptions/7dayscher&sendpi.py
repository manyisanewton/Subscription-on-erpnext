# MASTER SCRIPT: CALCULATION + STATUS + INVOICE + TODO
from frappe.utils import add_months, add_days, getdate, nowdate, date_diff

# 1. Get all Subscriptions (Active, Draft, Past Due)
# We only skip Cancelled ones.
subs = frappe.get_all("Internal Subscription", 
    filters={"status": ["!=", "Cancelled"]}, 
    fields=["name"]
)

for s in subs:
    doc = frappe.get_doc("Internal Subscription", s.name)

    # PART 1: AUTO-CALCULATE END DATE (Start + Frequency)
    months_to_add = 1
    if doc.subscription_plan:
        # Fetch billing cycle from the Plan Doctype
        plan_name = doc.subscription_plan[0].plan
        # Using frappe.db.get_value is efficient
        cycle = frappe.db.get_value("Internal Subscription Plan", plan_name, "billing_cycles")
        
        if cycle == "Annually": months_to_add = 12
        elif cycle == "Biannually": months_to_add = 6
        elif cycle == "Quarterly": months_to_add = 3
        else: months_to_add = 1 # Monthly default

    # calculate the End Date
    if doc.subscription_start_date:
        doc.subscription_end_date = add_months(getdate(doc.subscription_start_date), months_to_add)



    # PART 2: UPDATE STATUS (Active vs Past Due)
    is_latest_paid = False
    # Check the latest row in the payment table
    if doc.payment_method and len(doc.payment_method) > 0:
        last_row = doc.payment_method[-1]
        if last_row.status == "Paid":
            is_latest_paid = True

    if is_latest_paid:
        doc.status = "Active"
    else:
        # If not paid, and we are past the Calculated End Date
        if doc.subscription_end_date and getdate(nowdate()) > getdate(doc.subscription_end_date):
            doc.status = "Past Due Date"
        else:
            doc.status = "Active"


    # PART 3: 10-DAY WARNING + AUTO INVOICE 
    if doc.subscription_end_date:
        # Calculate the trigger date (10 days before expiry)
        target_date = add_days(getdate(doc.subscription_end_date), -10)
        
        if getdate(nowdate()) == target_date:
            
            # --- A. CREATE TODO ---
            frappe.get_doc({
                "doctype": "ToDo",
                "owner": doc.owner,
                "description": f"Reminder: Internal Subscription {doc.name} expires in 10 days.",
                "reference_type": "Internal Subscription",
                "reference_name": doc.name,
                "assigned_by": "Administrator"
            }).insert(ignore_permissions=True)
            print(f"10 Day Warning ToDo created for {doc.name}")

            # --- B. AUTO INVOICE ---
            # Check for duplicates in the last 24 hours
            already_created = False
            if doc.payment_method:
                last_row = doc.payment_method[-1]
                if last_row.posting_date == nowdate():
                    already_created = True
            
            if not already_created:
                try:
                    # Create Invoice Object
                    new_pi = frappe.new_doc("Purchase Invoice")
                    
                    # Map Header
                    new_pi.supplier = doc.party 
                    new_pi.company = doc.company
                    new_pi.currency = doc.currency
                    new_pi.set_posting_time = 1
                    new_pi.posting_date = nowdate()
                    new_pi.due_date = doc.subscription_end_date 
                    
                    # Map Items
                    if doc.items:
                        for item in doc.items:
                            new_pi.append("items", {
                                "item_code": item.item,  
                                "qty": item.qty,
                                "rate": item.amount / item.qty if item.qty > 0 else 0,
                                "cost_center": doc.cost_center 
                            })
                    
                    # Insert Invoice (Draft)
                    new_pi.insert(ignore_permissions=True)
                    
                    # Link to Subscription
                    doc.append("payment_method", {
                        "purchase_invoice": new_pi.name,
                        "status": "Draft",
                        "posting_date": nowdate()
                    })
                    
                    print(f"Generated Invoice {new_pi.name} for Subscription {doc.name}")

                except Exception as e:
                    frappe.log_error(f"Failed to auto-create Invoice for {doc.name}: {str(e)}")

    # PART 4: SAVE EVERYTHING
    doc.save(ignore_permissions=True)