export type Dish={id:number;name:string;description:string;category:string;price_paise:number;portion_label:string;image_cloudinary_url:string;is_available:boolean;stock_quantity:number;spice_choices_supported:string[];is_bestseller:boolean};
export type CartLine={key:string;dish:Dish;quantity:number;spice:string;notes:string};
export type Totals={subtotal_paise:number;tax_paise:number;delivery_fee_paise:number;total_amount_paise:number};
export type Order=Totals & {id:string;order_number:string;customer_name:string;customer_phone:string;fulfilment_mode:'PICKUP'|'DELIVERY';delivery_address:string;status:string;payment_status:string;created_at:string;accepted_at:string|null;estimated_prep_minutes:number;items:{dish_name:string;quantity:number;portion_label:string;customization_notes:string;unit_price_paise:number}[]};
export const money=(value:number)=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:value%100?2:0}).format(value/100);
