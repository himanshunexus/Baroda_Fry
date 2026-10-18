let csrf='';
export async function initSession(){const r=await fetch('/api/session',{credentials:'same-origin'});if(!r.ok)throw Error('Unable to connect to the restaurant. Please try again.');const data=await r.json();csrf=data.csrfToken;return data;}
export async function api<T>(path:string,method='GET',body?:unknown):Promise<T>{
 if(method!=='GET'&&!csrf)await initSession();
 const r=await fetch('/api'+path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrf},body:body===undefined?undefined:JSON.stringify(body)});
 const data=await r.json().catch(()=>({detail:'The service is unavailable. Please try again.'}));
 if(!r.ok)throw Error(typeof data.detail==='string'?data.detail:JSON.stringify(data));
 if(data.csrfToken)csrf=data.csrfToken;
 return data;
}
export function subscribe(path:string,refresh:()=>void,onConnection:(online:boolean)=>void=()=>{},pollFallback=true){
 let stopped=false;let socket:WebSocket;let retry:ReturnType<typeof setTimeout>;
 const connect=()=>{socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}${path}`);socket.onopen=()=>{onConnection(true);refresh();};socket.onmessage=()=>refresh();socket.onclose=()=>{onConnection(false);if(!stopped)retry=setTimeout(connect,3000);};socket.onerror=()=>socket.close();};connect();
 const poll=pollFallback?setInterval(refresh,15000):undefined;
 return()=>{stopped=true;clearTimeout(retry);if(poll)clearInterval(poll);socket.close();};
}
