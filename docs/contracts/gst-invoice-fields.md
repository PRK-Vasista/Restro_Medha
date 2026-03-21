# GST Invoice Fields (Day-1 Mandatory)

## Seller
- legal_name
- gstin
- address_line_1
- address_line_2
- state_code

## Buyer (optional for B2C thresholds)
- customer_name
- customer_gstin

## Item-level
- item_name
- hsn_code
- quantity
- unit_price
- discount_amount
- taxable_value
- gst_rate
- cgst_amount
- sgst_amount
- igst_amount
- line_total

## Invoice-level
- invoice_number
- invoice_date_time
- place_of_supply_state
- subtotal
- total_discount
- total_taxable_value
- total_cgst
- total_sgst
- total_igst
- round_off
- grand_total
- payment_mode
- irn_ack_fields (reserved, optional)
