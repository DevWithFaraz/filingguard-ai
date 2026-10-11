import { Img, staticFile } from "remotion";
import { B, C, F, tween, windowed } from "../brand";
export const LogoScene = ({ frame }: { frame:number }) => {
  const [start,end]=B.logo;
  if(frame<start||frame>=end-12)return null;
  const opacity=windowed(frame,start,end-12,10,9);
  const settle=tween(frame,[start,start+20],[.9,1]);
  const paths=tween(frame,[start,start+23],[0,1]);
  return <div style={{position:"absolute",inset:0,opacity,fontFamily:F.sans}}>
    <svg width="1920" height="1080" style={{position:"absolute",inset:0}}>
      {[300,540,780].map((y,i)=><g key={y} opacity={1-paths}><path d={"M1740 "+y+" Q1250 540 "+(690+i*35)+" "+(475+i*20)} stroke={C.yellow} strokeWidth={3} fill="none" pathLength={1} strokeDasharray={1} strokeDashoffset={paths}/><circle cx={1740-(1740-690-i*35)*paths} cy={y+(475+i*20-y)*paths} r="6" fill={C.yellow}/></g>)}
      <path d="M367 330 L1342 268 L1538 389 L1538 670 L518 733 L367 628 Z" fill="#9564DD0D" stroke={C.lilac} strokeOpacity=".5" strokeWidth="2"/>
      <path d="M382 345 L1353 285 L1518 389" fill="none" stroke={C.lilacSoft} strokeOpacity=".6"/>
      <path d="M390 650 L540 744 L1540 682" fill="none" stroke={C.lilac} strokeOpacity=".23"/>
    </svg>
    {[0,1].map(i=><div key={i} style={{position:"absolute",left:477+i*13,top:338+i*15,width:990,height:373,borderRadius:25,background:i===0?"#9564DD44":"#3E0F8D55",border:"1px solid #C9B3F255",transform:"scale("+settle+")",boxShadow:"0 18px 45px #06020F44"}}/>)}
    <div style={{position:"absolute",left:465,top:320,width:990,padding:"45px 70px",boxSizing:"border-box",borderRadius:25,background:C.paper,
      transform:"perspective(1400px) rotateX("+tween(frame,[start,start+20],[9,0])+"deg) scale("+settle+")",border:"1px solid #FFFFFFAA",boxShadow:"0 8px 0 #C9B3F244,0 35px 70px #06020F88"}}>
      <Img src={staticFile("filingguard-logo.png")} width={850} height={850/3} style={{display:"block",objectFit:"contain"}} />
      <div style={{position:"absolute",top:0,left:30,right:30,height:2,background:"linear-gradient(90deg,transparent,#FFFFFF,transparent)"}}/>
    </div>
    <div style={{position:"absolute",left:250,right:250,top:760,textAlign:"center",fontFamily:F.mono,fontSize:37,fontWeight:500,color:C.paper,letterSpacing:".12em",
      opacity:tween(frame,[start+17,start+28],[0,1]),transform:"translateY("+tween(frame,[start+15,start+30],[20,0])+"px)"}}>CI/CD FOR COURT FILINGS</div>
  </div>;
};
