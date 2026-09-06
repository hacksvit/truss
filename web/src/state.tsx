import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import type {Snapshot} from './contracts';
import {connect,type Connection} from './stream';
const Context=createContext<{snapshot:Snapshot|null;connection:Connection}>({snapshot:null,connection:'connecting'});
export function SnapshotProvider({children}:{children:ReactNode}){
 const [snapshot,setSnapshot]=useState<Snapshot|null>(null),[connection,setConnection]=useState<Connection>('connecting');
 useEffect(()=>connect('mock',setSnapshot,setConnection),[]);
 return <Context.Provider value={{snapshot,connection}}>{children}</Context.Provider>;
}
export const useSnapshot=()=>useContext(Context);
