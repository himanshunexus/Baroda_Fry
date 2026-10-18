import ReactDOM from 'react-dom/client';
import {CartProvider} from './CartContext';
import MenuScreen from './MenuScreen';
import KitchenDashboard from './KitchenDashboard';
import OrderTracking from './OrderTracking';
import './styles.css';
const path=location.pathname;
ReactDOM.createRoot(document.getElementById('root')!).render(<CartProvider>{path.startsWith('/kitchen')?<KitchenDashboard/>:path.startsWith('/track/')?<OrderTracking id={path.split('/')[2]}/>:<MenuScreen onOrder={o=>{location.href=`/track/${o.id}`;}}/>}</CartProvider>);
