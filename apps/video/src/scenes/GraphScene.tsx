import { B, C, F, tween, windowed } from "../brand";
import { Caption } from "../components/chrome";
const nodes = [
  {x:1260,y:260,label:"Claim",detail:"¶4 · Reversed",color:C.review},
  {x:1570,y:290,label:"Brown",detail:"347 U.S. 483",color:C.lilac},
  {x:1600,y:648,label:"Quote",detail:"Word differs",color:C.review},
  {x:1320,y:758,label:"Privacy",detail:"¶6 · Detected",color:C.partial},
  {x:940,y:742,label:"Disclosure",detail:"Heading missing",color:C.partial},
];
export const GraphScene = ({ frame }: { frame:number }) => {
  const [start,end]=B.graph;
  if(frame < start || frame >= end+6)return null;
  const opacity=windowed(frame,start,end+6,12,12);
  const expand=tween(frame,[start+5,start+29],[0,1]);
  const edge=tween(frame,[start+10,start+42],[0,1]);
  const center={x:1075,y:545};
  return <>
    <Caption frame={frame} start={start} end={end} eyebrow="07 / EVIDENCE LINEAGE" title="Risk mapping" sub="Follow a finding through the filing, the claim and the source." />
    <svg width="1920" height="1080" style={{position:"absolute",inset:0,opacity}}>
      <defs><linearGradient id="graphPath"><stop stopColor={C.yellow}/><stop offset="1" stopColor={C.lilac}/></linearGradient><radialGradient id="graphNode"><stop stopColor={C.lilac} stopOpacity=".38"/><stop offset="1" stopColor={C.lilac} stopOpacity="0"/></radialGradient></defs>
      {nodes.map((node,i)=>{
        const x=center.x+(node.x-center.x)*expand,y=center.y+(node.y-center.y)*expand;
        const travel=tween(frame,[start+24+i*4,start+54+i*4],[0,1]);
        const packetX=(1-travel)**2*center.x+2*(1-travel)*travel*(center.x+130)+travel**2*x;
        const packetY=(1-travel)**2*center.y+2*(1-travel)*travel*(center.y-30)+travel**2*y;
        return <g key={node.label}>
          <path d={"M"+center.x+" "+center.y+" Q"+(center.x+130)+" "+(center.y-30)+" "+x+" "+y} fill="none" stroke={i===0||i===1?"url(#graphPath)":C.lilac+"55"} strokeWidth={i===0||i===1?3:2}
            pathLength={1} strokeDasharray={1} strokeDashoffset={1-edge}/>
          <circle cx={x} cy={y} r={49} fill="url(#graphNode)"/>
          <circle cx={x} cy={y} r={37} fill="none" stroke={node.color} strokeOpacity=".28" strokeWidth="1"/>
          <circle cx={x} cy={y} r={27} fill="#170A33" stroke={node.color} strokeWidth={2.5}/>
          <circle cx={x} cy={y} r={12} fill={node.color+"22"} stroke={node.color} strokeWidth="1"/>
          <circle cx={x} cy={y} r={4} fill={node.color}/>
          {travel>0&&travel<1&&<g><circle cx={packetX} cy={packetY} r="10" fill={C.yellow} fillOpacity=".12"/><circle cx={packetX} cy={packetY} r="3" fill={C.yellow}/></g>}
        </g>;
      })}
      <path d={"M1260 260 Q1440 150 1570 290"} fill="none" stroke={C.yellow} strokeWidth={3} pathLength={1} strokeDasharray={1} strokeDashoffset={1-tween(frame,[start+35,start+55],[0,1])}/>
    </svg>
    {nodes.map((node,i)=><div key={node.label} style={{position:"absolute",left:node.x-112,top:node.y+39,width:224,padding:"11px 9px",boxSizing:"border-box",borderRadius:12,border:"1px solid "+node.color+"55",background:"linear-gradient(135deg,#3E0F8DBB,#170A33F2)",boxShadow:"0 6px 0 #0E0620AA,0 14px 26px #06020F33",textAlign:"center",opacity:opacity*tween(frame,[start+16+i*4,start+27+i*4],[0,1]),fontFamily:F.sans}}>
      <div style={{fontSize:27,fontWeight:600,color:C.paper}}>{node.label}</div><div style={{fontFamily:F.mono,fontSize:22,marginTop:5,color:C.lilacSoft}}>{node.detail}</div>
    </div>)}
    <div style={{position:"absolute",left:1290,top:439,width:435,padding:"18px 24px",boxSizing:"border-box",borderRadius:12,background:"linear-gradient(130deg,#3E0F8DF2,#170A33F2)",border:"1px solid "+C.lilac+"88",boxShadow:"0 7px 0 #170A33,0 16px 30px #06020F55",
      opacity:opacity*tween(frame,[start+46,start+58],[0,1]),color:C.paper}}>
      <div style={{fontFamily:F.mono,fontSize:22,color:C.lilacSoft,display:"flex",alignItems:"center",gap:10}}><span style={{width:5,height:20,background:C.yellow}}/>BROWN / SOURCE PASSAGE</div>
      <div style={{fontFamily:F.sans,fontSize:25,lineHeight:1.3,marginTop:10}}>Separate educational facilities are inherently <span style={{color:C.yellow}}>unequal.</span></div>
    </div>
  </>;
};
