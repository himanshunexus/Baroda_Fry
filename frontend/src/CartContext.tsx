import {createContext,useContext,useState,useEffect,type ReactNode} from 'react';
import type {CartLine,Dish} from './types';
type Cart={lines:CartLine[];add:(dish:Dish,spice:string,notes:string,quantity:number)=>void;change:(key:string,delta:number)=>void;clear:()=>void;count:number;estimate:number};
const Context=createContext<Cart|null>(null);
export function CartProvider({children}:{children:ReactNode}){
 const [lines,setLines]=useState<CartLine[]>(()=>{try{const v=JSON.parse(localStorage.getItem('bfc-cart-v1')||'[]');return Array.isArray(v)?v.filter(x=>x?.dish?.id&&Number.isInteger(x.quantity)&&x.quantity>0&&x.quantity<=20&&typeof x.key==='string'):[];}catch{return[];}});
 useEffect(()=>{try{localStorage.setItem('bfc-cart-v1',JSON.stringify(lines));}catch{/* Storage can be disabled. */}},[lines]);
 const add=(dish:Dish,spice:string,notes:string,quantity:number)=>setLines(old=>{const key=JSON.stringify([dish.id,spice,notes]);const found=old.find(x=>x.key===key);return found?old.map(x=>x.key===key?{...x,quantity:Math.min(20,x.quantity+quantity)}:x):[...old,{key,dish,spice,notes,quantity}];});
 const change=(key:string,delta:number)=>setLines(old=>old.map(x=>x.key===key?{...x,quantity:Math.min(20,x.quantity+delta)}:x).filter(x=>x.quantity>0));
 return <Context.Provider value={{lines,add,change,clear:()=>setLines([]),count:lines.reduce((n,x)=>n+x.quantity,0),estimate:lines.reduce((n,x)=>n+x.quantity*x.dish.price_paise,0)}}>{children}</Context.Provider>;
}
export function useCart(){return useContext(Context)!;}
