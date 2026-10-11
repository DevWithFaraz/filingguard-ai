import { B, C, F, tween, windowed } from "../brand";
import { Caption } from "../components/chrome";
export const IntakeScene = ({ frame }: { frame: number }) => {
  const [start,end] = B.intake;
  if (frame >= end) return null;
  const opacity = windowed(frame,12,end,12,8);
  const landing = tween(frame,[24,50],[0,1]);
  const lift = tween(frame,[12,42],[60,0]);
  return <>
    <Caption frame={frame} start={start} end={end} eyebrow="01 / PREFLIGHT INTAKE" title="Upload brief" sub="A document enters. The evidence pipeline begins." />
    <div style={{ position:"absolute",left:976,top:515+lift,width:760,height:320,opacity,
      transform:"perspective(1100px) rotateX(56deg) rotateZ(-12deg)",borderRadius:28,background:"linear-gradient(135deg,#9564DD55,#170A33 45%,#3E0F8D88)",border:"2px solid #C9B3F277",
      boxShadow:"0 8px 0 #3E0F8D,0 11px 0 #9564DD88,0 30px 0 #150A29,0 60px 70px #06020F88",display:"grid",placeItems:"center" }}>
      <div style={{position:"absolute",inset:16,borderRadius:19,border:"1px solid #C9B3F233"}} />
      <div style={{ width:590,height:215,borderRadius:24,border:"3px solid "+C.yellow,boxShadow:"0 0 "+(12+landing*15)+"px "+C.yellow+"66,inset 0 0 30px "+C.yellow+"22",
        background:"linear-gradient(135deg,#E4DA7215,#9564DD11)",opacity:.4+landing*.6 }} />
      <div style={{position:"absolute",bottom:20,left:46,right:46,display:"flex",justifyContent:"space-between"}}>{[0,1,2,3].map(i=><span key={i} style={{height:4,width:i===0?65:24,background:i===0?C.yellow:C.lilac,opacity:i===0?.8:.4}} />)}</div>
    </div>
    {[0,1].map(i=><div key={i} style={{position:"absolute",left:1042+i*15,top:300+i*20,width:640,height:500,opacity:opacity*landing*.7,borderRadius:14,
      background:i===0?"#9564DD33":"#170A3399",border:"1px solid #C9B3F266",transform:"perspective(1400px) rotateX(15deg) rotateZ(-12deg)",boxShadow:"0 15px 30px #06020F33"}} />)}
    <div style={{position:"absolute",left:1600,top:217,opacity:opacity*tween(frame,[36,48],[0,1]),transform:"translateY("+tween(frame,[36,48],[18,0])+"px)",border:"1px solid #C9B3F255",borderRadius:12,padding:"16px 20px",background:"linear-gradient(135deg,#3E0F8DEE,#170A33EE)",boxShadow:"0 16px 30px #06020F55",fontFamily:F.mono,fontSize:24,color:C.paper}}><span style={{color:C.yellow}}>↳</span> BRIEF</div>
    <div style={{ position:"absolute",left:1140,top:890,opacity,fontFamily:F.mono,fontSize:22,letterSpacing:".1em",color:C.lilacSoft }}>TEXT / PDF → PREFLIGHT</div>
  </>;
};
