import { lazy, Suspense, createContext, useContext, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bell, Bot, ChevronLeft, CircleDollarSign, LayoutDashboard, LogOut,
  Menu, PieChart, ReceiptText, Search, Settings2, Sparkles, Target,
  UserRound, WalletCards, X,
} from "lucide-react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { api } from "./api";

const Auth = lazy(() => import("./pages/Auth"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Transactions = lazy(() => import("./pages/Transactions"));
const Budget = lazy(() => import("./pages/Budget"));
const Reports = lazy(() => import("./pages/Reports"));
const Advisor = lazy(() => import("./pages/Advisor"));
const Profile = lazy(() => import("./pages/Profile"));

const SessionContext = createContext(null);
export const useSession = () => useContext(SessionContext);

function Loader() {
  return <div className="grid min-h-screen place-items-center bg-void"><div className="relative h-16 w-16"><div className="absolute inset-0 rounded-2xl border border-primary/30 animate-ping"/><div className="absolute inset-2 grid place-items-center rounded-xl bg-primary/15 text-cyan"><Sparkles/></div></div></div>;
}

function CursorGlow() {
  const [point, setPoint] = useState({ x: -200, y: -200 });
  useEffect(() => {
    if (matchMedia("(pointer: coarse)").matches) return;
    const move = (event) => setPoint({ x: event.clientX, y: event.clientY });
    window.addEventListener("pointermove", move, { passive: true });
    return () => window.removeEventListener("pointermove", move);
  }, []);
  return <motion.div aria-hidden className="pointer-events-none fixed z-[100] h-72 w-72 rounded-full bg-primary/5 blur-3xl" animate={{ x: point.x - 144, y: point.y - 144 }} transition={{ type: "spring", stiffness: 90, damping: 25, mass: .2 }}/>
}

const nav = [
  ["/app/dashboard", "Dashboard", LayoutDashboard],
  ["/app/transactions", "Transactions", ReceiptText],
  ["/app/budget", "Budget", WalletCards],
  ["/app/reports", "Analytics", PieChart],
  ["/app/advisor", "AI Advisor", Bot],
  ["/app/profile", "Profile", UserRound],
];

function Sidebar({ collapsed, setCollapsed, mobile, setMobile }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useSession();
  return <>
    <AnimatePresence>{mobile && <motion.button aria-label="Close navigation" className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden" onClick={() => setMobile(false)} initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}/>}</AnimatePresence>
    <motion.aside className={`glass fixed bottom-4 left-4 top-4 z-50 flex flex-col overflow-hidden rounded-[28px] ${mobile ? "translate-x-0" : "-translate-x-[120%] lg:translate-x-0"}`} animate={{ width: collapsed ? 88 : 248 }} transition={{type:"spring",stiffness:260,damping:28}}>
      <div className="flex h-20 items-center gap-3 border-b border-white/[.06] px-5">
        <img src="/static/images/finsight-ai-logo.png" alt="" className="h-11 w-11 rounded-xl object-cover shadow-glow"/>
        {!collapsed && <motion.span initial={{opacity:0}} animate={{opacity:1}} className="whitespace-nowrap text-lg font-bold tracking-tight">FinSight <span className="text-cyan">AI</span></motion.span>}
      </div>
      <nav className="flex-1 space-y-2 overflow-y-auto p-3 pt-6" aria-label="Primary">
        {nav.map(([href,label,Icon]) => {
          const active=location.pathname===href;
          return <motion.button key={href} onClick={()=>{navigate(href);setMobile(false)}} whileHover={{x:3}} whileTap={{scale:.97}} aria-current={active?"page":undefined} className={`group relative flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${active?"bg-primary/15 text-white shadow-[inset_0_0_24px_rgba(59,130,246,.12),0_0_24px_rgba(59,130,246,.08)]":"text-muted hover:bg-white/[.04] hover:text-white"}`}>
            {active && <motion.span layoutId="active-nav" className="absolute left-0 h-7 w-1 rounded-r-full bg-cyan shadow-[0_0_14px_#22d3ee]"/>}
            <Icon size={20} className="shrink-0 transition-transform duration-300 group-hover:rotate-6"/>{!collapsed&&<span>{label}</span>}
          </motion.button>;
        })}
      </nav>
      <div className="space-y-2 border-t border-white/[.06] p-3">
        <button onClick={logout} className="group flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-muted transition hover:bg-danger/10 hover:text-red-300"><LogOut size={20} className="shrink-0 transition-transform group-hover:-rotate-6"/>{!collapsed&&"Log out"}</button>
        <button onClick={()=>setCollapsed(!collapsed)} className="hidden w-full items-center justify-center rounded-2xl py-3 text-muted transition hover:bg-white/[.04] hover:text-white lg:flex" aria-label={collapsed?"Expand sidebar":"Collapse sidebar"}><ChevronLeft className={`transition-transform ${collapsed?"rotate-180":""}`} size={19}/></button>
      </div>
    </motion.aside>
  </>;
}

function Topbar({ collapsed, setMobile }) {
  const { session } = useSession();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  return <header className={`fixed right-4 top-4 z-30 transition-all duration-300 ${collapsed?"lg:left-[112px]":"lg:left-[272px]"} left-4`}>
    <div className="glass flex h-16 items-center justify-between rounded-2xl px-3 sm:px-5">
      <div className="flex items-center gap-3"><button className="rounded-xl p-2 text-muted hover:bg-white/5 hover:text-white lg:hidden" onClick={()=>setMobile(true)} aria-label="Open navigation"><Menu/></button><div><p className="hidden text-xs text-muted sm:block">{new Intl.DateTimeFormat("en-IN",{weekday:"long",month:"short",day:"numeric"}).format(new Date())}</p><h1 className="text-sm font-semibold sm:text-base">{greeting}, {session.user.name.split(" ")[0]} <span aria-hidden>👋</span></h1></div></div>
      <div className="flex items-center gap-2 sm:gap-3"><label className="hidden h-10 items-center gap-2 rounded-xl border border-white/[.07] bg-white/[.03] px-3 md:flex"><Search size={17} className="text-muted"/><input aria-label="Search" placeholder="Search finances..." className="w-40 bg-transparent text-sm text-white outline-none placeholder:text-slate-600 xl:w-56"/></label><button aria-label="Notifications" className="relative rounded-xl p-2.5 text-muted transition hover:bg-white/5 hover:text-white"><Bell size={19}/><span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-cyan shadow-[0_0_8px_#22d3ee]"/></button><button className="flex items-center gap-2 rounded-xl border border-white/[.07] bg-white/[.03] p-1.5 pr-3 transition hover:border-primary/30"><span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-primary to-cyan text-xs font-bold">{session.user.name.slice(0,2).toUpperCase()}</span><span className="hidden text-left text-xs sm:block"><b className="block max-w-24 truncate">{session.user.name}</b><span className="text-muted">Free plan</span></span></button></div>
    </div>
  </header>;
}

function Assistant() {
  const [open,setOpen]=useState(false); const [message,setMessage]=useState("");
  return <div className="fixed bottom-5 right-5 z-40">
    <AnimatePresence>{open&&<motion.div initial={{opacity:0,y:20,scale:.95}} animate={{opacity:1,y:0,scale:1}} exit={{opacity:0,y:20,scale:.95}} className="glass mb-4 w-[min(23rem,calc(100vw-2.5rem))] overflow-hidden rounded-3xl shadow-cyan"><div className="flex items-center justify-between border-b border-white/[.07] p-4"><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/15 text-cyan"><Bot/></span><div><b className="text-sm">FinSight Copilot</b><p className="text-xs text-success">● Online</p></div></div><button onClick={()=>setOpen(false)} aria-label="Close assistant" className="rounded-lg p-2 text-muted hover:bg-white/5"><X size={18}/></button></div><div className="h-56 space-y-3 overflow-y-auto p-4 text-sm"><div className="max-w-[88%] rounded-2xl rounded-tl-md bg-white/[.05] p-3 text-slate-300">Hi! I can help explain your spending, budget, and savings trends.</div>{message&&<div className="ml-auto max-w-[88%] rounded-2xl rounded-tr-md bg-primary/20 p-3">{message}</div>}</div><form onSubmit={e=>{e.preventDefault();setMessage(e.currentTarget.message.value);e.currentTarget.reset()}} className="flex gap-2 border-t border-white/[.07] p-3"><input name="message" className="min-w-0 flex-1 rounded-xl border border-white/[.08] bg-white/[.04] px-3 text-sm outline-none focus:border-primary/50" placeholder="Ask about your finances..."/><button className="rounded-xl bg-primary px-4 text-sm font-semibold hover:bg-blue-500">Send</button></form></motion.div>}</AnimatePresence>
    <motion.button onClick={()=>setOpen(!open)} aria-label="Open AI assistant" className="relative grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-primary to-cyan text-white shadow-[0_0_35px_rgba(34,211,238,.35)]" animate={{y:[0,-7,0]}} transition={{duration:3,repeat:Infinity,ease:"easeInOut"}} whileHover={{scale:1.08,rotate:3}} whileTap={{scale:.92}}><span className="absolute inset-0 animate-ping rounded-2xl border border-cyan/30"/><Bot className="relative"/></motion.button>
  </div>;
}

function ProtectedLayout() {
  const { session } = useSession(); const [collapsed,setCollapsed]=useState(false); const [mobile,setMobile]=useState(false);
  if(!session?.authenticated) return <Navigate to="/app/login" replace/>;
  return <div className="min-h-screen"><CursorGlow/><Sidebar {...{collapsed,setCollapsed,mobile,setMobile}}/><Topbar {...{collapsed,setMobile}}/><main className={`min-h-screen px-4 pb-10 pt-24 transition-[padding] duration-300 ${collapsed?"lg:pl-[112px]":"lg:pl-[272px]"}`}><Suspense fallback={<Loader/>}><AnimatePresence mode="wait"><Routes><Route path="dashboard" element={<Dashboard/>}/><Route path="transactions" element={<Transactions/>}/><Route path="budget" element={<Budget/>}/><Route path="reports" element={<Reports/>}/><Route path="advisor" element={<Advisor/>}/><Route path="profile" element={<Profile/>}/><Route path="*" element={<Navigate to="dashboard" replace/>}/></Routes></AnimatePresence></Suspense></main><Assistant/></div>;
}

export default function App() {
  const [session,setSession]=useState(null); const navigate=useNavigate();
  const refresh=async()=>setSession(await api("/session"));
  useEffect(()=>{refresh().catch(()=>setSession({authenticated:false}))},[]);
  const logout=async()=>{await api("/auth/logout",{method:"POST"});setSession({authenticated:false});navigate("/app/login")};
  const context=useMemo(()=>({session,refresh,logout}),[session]);
  if(!session) return <Loader/>;
  return <SessionContext.Provider value={context}><Routes><Route path="/app/login" element={session.authenticated?<Navigate to="/app/dashboard" replace/>:<Suspense fallback={<Loader/>}><Auth mode="login"/></Suspense>}/><Route path="/app/register" element={session.authenticated?<Navigate to="/app/dashboard" replace/>:<Suspense fallback={<Loader/>}><Auth mode="register"/></Suspense>}/><Route path="/app/*" element={<ProtectedLayout/>}/><Route path="*" element={<Navigate to={session.authenticated?"/app/dashboard":"/app/login"} replace/>}/></Routes></SessionContext.Provider>;
}
