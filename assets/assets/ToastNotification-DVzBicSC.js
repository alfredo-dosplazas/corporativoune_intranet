import{f as e,s as t}from"./main-izWU1KAm.js";import{n,t as r}from"./jsx-runtime-CeYDa1YS.js";var i=e(t(),1),a=n(),o={data:``},s=e=>{if(typeof window==`object`){let t=(e?e.querySelector(`#_goober`):window._goober)||Object.assign(document.createElement(`style`),{innerHTML:` `,id:`_goober`});return t.nonce=window.__nonce__,t.parentNode||(e||document.head).appendChild(t),t.firstChild}return e||o},c=/(?:([\u0080-\uFFFF\w-%@]+) *:? *([^{;]+?);|([^;}{]*?) *{)|(}\s*)/g,l=/\/\*[^]*?\*\/|  +/g,u=/\n+/g,d=(e,t)=>{let n=``,r=``,i=``;for(let a in e){let o=e[a];a[0]==`@`?a[1]==`i`?n=a+` `+o+`;`:r+=a[1]==`f`?d(o,a):a+`{`+d(o,a[1]==`k`?``:t)+`}`:typeof o==`object`?r+=d(o,t?t.replace(/([^,])+/g,e=>a.replace(/([^,]*:\S+\([^)]*\))|([^,])+/g,t=>/&/.test(t)?t.replace(/&/g,e):e?e+` `+t:t)):a):o!=null&&(a=a[1]==`-`?a:a.replace(/[A-Z]/g,`-$&`).toLowerCase(),i+=d.p?d.p(a,o):a+`:`+o+`;`)}return n+(t&&i?t+`{`+i+`}`:i)+r},f={},p=e=>{if(typeof e==`object`){let t=``;for(let n in e)t+=n+p(e[n]);return t}return e},ee=(e,t,n,r,i)=>{let a=p(e),o=f[a]||(f[a]=(e=>{let t=0,n=11;for(;t<e.length;)n=101*n+e.charCodeAt(t++)>>>0;return`go`+n})(a));if(!f[o]){let t=a===e?(e=>{let t,n,r=[{}];for(;t=c.exec(e.replace(l,``));)t[4]?r.shift():t[3]?(n=t[3].replace(u,` `).trim(),r.unshift(r[0][n]=r[0][n]||{})):r[0][t[1]]=t[2].replace(u,` `).trim();return r[0]})(e):e;f[o]=d(i?{[`@keyframes `+o]:t}:t,n?``:`.`+o)}let s=n&&f.g;return n&&(f.g=f[o]),((e,t,n,r)=>{r?t.data=t.data.replace(r,e):t.data.indexOf(e)===-1&&(t.data=n?e+t.data:t.data+e)})(f[o],t,r,s),o},m=(e,t,n)=>e.reduce((e,r,i)=>{let a=t[i];if(a&&a.call){let e=a(n),t=e&&e.props&&e.props.className||/^go/.test(e)&&e;a=t?`.`+t:e&&typeof e==`object`?e.props?``:d(e,``):!1===e?``:e}return e+r+(a??``)},``);function h(e){let t=this||{},n=e.call?e(t.p):e;return ee(n.unshift?n.raw?m(n,[].slice.call(arguments,1),t.p):n.reduce((e,n)=>Object.assign(e,n&&n.call?n(t.p):n),{}):n,s(t.target),t.g,t.o,t.k)}var g,_,v;h.bind({g:1});var y=h.bind({k:1});function b(e,t,n,r){d.p=t,g=e,_=n,v=r}function x(e,t){let n=this||{};return function(){let r=arguments;function i(a,o){let s=Object.assign({},a),c=s.className||i.className;n.p=Object.assign({theme:_&&_()},s),n.o=/go\d/.test(c),s.className=h.apply(n,r)+(c?` `+c:``),t&&(s.ref=o);let l=e;return e[0]&&(l=s.as||e,delete s.as),v&&l[0]&&v(s),g(l,s)}return t?t(i):i}}var te=e=>typeof e==`function`,S=(e,t)=>te(e)?e(t):e,C=(()=>{let e=0;return()=>(++e).toString()})(),w=(()=>{let e;return()=>{if(e===void 0&&typeof window<`u`){let t=matchMedia(`(prefers-reduced-motion: reduce)`);e=!t||t.matches}return e}})(),T=20,E=`default`,D=(e,t)=>{let{toastLimit:n}=e.settings;switch(t.type){case 0:return{...e,toasts:[t.toast,...e.toasts].slice(0,n)};case 1:return{...e,toasts:e.toasts.map(e=>e.id===t.toast.id?{...e,...t.toast}:e)};case 2:let{toast:r}=t;return D(e,{type:+!!e.toasts.find(e=>e.id===r.id),toast:r});case 3:let{toastId:i}=t;return{...e,toasts:e.toasts.map(e=>e.id===i||i===void 0?{...e,dismissed:!0,visible:!1}:e)};case 4:return t.toastId===void 0?{...e,toasts:[]}:{...e,toasts:e.toasts.filter(e=>e.id!==t.toastId)};case 5:return{...e,pausedAt:t.time};case 6:let a=t.time-(e.pausedAt||0);return{...e,pausedAt:void 0,toasts:e.toasts.map(e=>({...e,pauseDuration:e.pauseDuration+a}))}}},O=[],k={toasts:[],pausedAt:void 0,settings:{toastLimit:T}},A={},j=(e,t=E)=>{A[t]=D(A[t]||k,e),O.forEach(([e,n])=>{e===t&&n(A[t])})},M=e=>Object.keys(A).forEach(t=>j(e,t)),ne=e=>Object.keys(A).find(t=>A[t].toasts.some(t=>t.id===e)),N=(e=E)=>t=>{j(t,e)},P={blank:4e3,error:4e3,success:2e3,loading:1/0,custom:4e3},F=(e={},t=E)=>{let[n,r]=(0,i.useState)(A[t]||k),a=(0,i.useRef)(A[t]);(0,i.useEffect)(()=>(a.current!==A[t]&&r(A[t]),O.push([t,r]),()=>{let e=O.findIndex(([e])=>e===t);e>-1&&O.splice(e,1)}),[t]);let o=n.toasts.map(t=>({...e,...e[t.type],...t,removeDelay:t.removeDelay||e[t.type]?.removeDelay||e?.removeDelay,duration:t.duration||e[t.type]?.duration||e?.duration||P[t.type],style:{...e.style,...e[t.type]?.style,...t.style}}));return{...n,toasts:o}},I=(e,t=`blank`,n)=>({createdAt:Date.now(),visible:!0,dismissed:!1,type:t,ariaProps:{role:`status`,"aria-live":`polite`},message:e,pauseDuration:0,...n,id:n?.id||C()}),L=e=>(t,n)=>{let r=I(t,e,n);return N(r.toasterId||ne(r.id))({type:2,toast:r}),r.id},R=(e,t)=>L(`blank`)(e,t);R.error=L(`error`),R.success=L(`success`),R.loading=L(`loading`),R.custom=L(`custom`),R.dismiss=(e,t)=>{let n={type:3,toastId:e};t?N(t)(n):M(n)},R.dismissAll=e=>R.dismiss(void 0,e),R.remove=(e,t)=>{let n={type:4,toastId:e};t?N(t)(n):M(n)},R.removeAll=e=>R.remove(void 0,e),R.promise=(e,t,n)=>{let r=R.loading(t.loading,{...n,...n?.loading});return typeof e==`function`&&(e=e()),e.then(e=>{let i=t.success?S(t.success,e):void 0;return i?R.success(i,{id:r,...n,...n?.success}):R.dismiss(r),e}).catch(e=>{let i=t.error?S(t.error,e):void 0;i?R.error(i,{id:r,...n,...n?.error}):R.dismiss(r)}),e};var z=1e3,B=(e,t=`default`)=>{let{toasts:n,pausedAt:r}=F(e,t),a=(0,i.useRef)(new Map).current,o=(0,i.useCallback)((e,t=z)=>{if(a.has(e))return;let n=setTimeout(()=>{a.delete(e),s({type:4,toastId:e})},t);a.set(e,n)},[]);(0,i.useEffect)(()=>{if(r)return;let e=Date.now(),i=n.map(n=>{if(n.duration===1/0)return;let r=(n.duration||0)+n.pauseDuration-(e-n.createdAt);if(r<0){n.visible&&R.dismiss(n.id);return}return setTimeout(()=>R.dismiss(n.id,t),r)});return()=>{i.forEach(e=>e&&clearTimeout(e))}},[n,r,t]);let s=(0,i.useCallback)(N(t),[t]),c=(0,i.useCallback)(()=>{s({type:5,time:Date.now()})},[s]),l=(0,i.useCallback)((e,t)=>{s({type:1,toast:{id:e,height:t}})},[s]),u=(0,i.useCallback)(()=>{r&&s({type:6,time:Date.now()})},[r,s]),d=(0,i.useCallback)((e,t)=>{let{reverseOrder:r=!1,gutter:i=8,defaultPosition:a}=t||{},o=n.filter(t=>(t.position||a)===(e.position||a)&&t.height),s=o.findIndex(t=>t.id===e.id),c=o.filter((e,t)=>t<s&&e.visible).length;return o.filter(e=>e.visible).slice(...r?[c+1]:[0,c]).reduce((e,t)=>e+(t.height||0)+i,0)},[n]);return(0,i.useEffect)(()=>{n.forEach(e=>{if(e.dismissed)o(e.id,e.removeDelay);else{let t=a.get(e.id);t&&(clearTimeout(t),a.delete(e.id))}})},[n,o]),{toasts:n,handlers:{updateHeight:l,startPause:c,endPause:u,calculateOffset:d}}},V=y`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
 transform: scale(1) rotate(45deg);
  opacity: 1;
}`,H=y`
from {
  transform: scale(0);
  opacity: 0;
}
to {
  transform: scale(1);
  opacity: 1;
}`,U=y`
from {
  transform: scale(0) rotate(90deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(90deg);
	opacity: 1;
}`,W=x(`div`)`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||`#ff4b4b`};
  position: relative;
  transform: rotate(45deg);

  animation: ${V} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;

  &:after,
  &:before {
    content: '';
    animation: ${H} 0.15s ease-out forwards;
    animation-delay: 150ms;
    position: absolute;
    border-radius: 3px;
    opacity: 0;
    background: ${e=>e.secondary||`#fff`};
    bottom: 9px;
    left: 4px;
    height: 2px;
    width: 12px;
  }

  &:before {
    animation: ${U} 0.15s ease-out forwards;
    animation-delay: 180ms;
    transform: rotate(90deg);
  }
`,G=y`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`,K=x(`div`)`
  width: 12px;
  height: 12px;
  box-sizing: border-box;
  border: 2px solid;
  border-radius: 100%;
  border-color: ${e=>e.secondary||`#e0e0e0`};
  border-right-color: ${e=>e.primary||`#616161`};
  animation: ${G} 1s linear infinite;
`,q=y`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(45deg);
	opacity: 1;
}`,J=y`
0% {
	height: 0;
	width: 0;
	opacity: 0;
}
40% {
  height: 0;
	width: 6px;
	opacity: 1;
}
100% {
  opacity: 1;
  height: 10px;
}`,re=x(`div`)`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${e=>e.primary||`#61d345`};
  position: relative;
  transform: rotate(45deg);

  animation: ${q} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;
  &:after {
    content: '';
    box-sizing: border-box;
    animation: ${J} 0.2s ease-out forwards;
    opacity: 0;
    animation-delay: 200ms;
    position: absolute;
    border-right: 2px solid;
    border-bottom: 2px solid;
    border-color: ${e=>e.secondary||`#fff`};
    bottom: 6px;
    left: 6px;
    height: 10px;
    width: 6px;
  }
`,Y=x(`div`)`
  position: absolute;
`,X=x(`div`)`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 20px;
  min-height: 20px;
`,ie=y`
from {
  transform: scale(0.6);
  opacity: 0.4;
}
to {
  transform: scale(1);
  opacity: 1;
}`,ae=x(`div`)`
  position: relative;
  transform: scale(0.6);
  opacity: 0.4;
  min-width: 20px;
  animation: ${ie} 0.3s 0.12s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
`,oe=({toast:e})=>{let{icon:t,type:n,iconTheme:r}=e;return t===void 0?n===`blank`?null:i.createElement(X,null,i.createElement(K,{...r}),n!==`loading`&&i.createElement(Y,null,n===`error`?i.createElement(W,{...r}):i.createElement(re,{...r}))):typeof t==`string`?i.createElement(ae,null,t):t},se=e=>`
0% {transform: translate3d(0,${e*-200}%,0) scale(.6); opacity:.5;}
100% {transform: translate3d(0,0,0) scale(1); opacity:1;}
`,ce=e=>`
0% {transform: translate3d(0,0,-1px) scale(1); opacity:1;}
100% {transform: translate3d(0,${e*-150}%,-1px) scale(.6); opacity:0;}
`,le=`0%{opacity:0;} 100%{opacity:1;}`,ue=`0%{opacity:1;} 100%{opacity:0;}`,de=x(`div`)`
  display: flex;
  align-items: center;
  background: #fff;
  color: #363636;
  line-height: 1.3;
  will-change: transform;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1), 0 3px 3px rgba(0, 0, 0, 0.05);
  max-width: 350px;
  pointer-events: auto;
  padding: 8px 10px;
  border-radius: 8px;
`,fe=x(`div`)`
  display: flex;
  justify-content: center;
  margin: 4px 10px;
  color: inherit;
  flex: 1 1 auto;
  white-space: pre-line;
`,pe=(e,t)=>{let n=e.includes(`top`)?1:-1,[r,i]=w()?[le,ue]:[se(n),ce(n)];return{animation:t?`${y(r)} 0.35s cubic-bezier(.21,1.02,.73,1) forwards`:`${y(i)} 0.4s forwards cubic-bezier(.06,.71,.55,1)`}},me=i.memo(({toast:e,position:t,style:n,children:r})=>{let a=e.height?pe(e.position||t||`top-center`,e.visible):{opacity:0},o=i.createElement(oe,{toast:e}),s=i.createElement(fe,{...e.ariaProps},S(e.message,e));return i.createElement(de,{className:e.className,style:{...a,...n,...e.style}},typeof r==`function`?r({icon:o,message:s}):i.createElement(i.Fragment,null,o,s))});b(i.createElement);var he=({id:e,className:t,style:n,onHeightUpdate:r,children:a})=>{let o=i.useCallback(t=>{if(t){let n=()=>{let n=t.getBoundingClientRect().height;r(e,n)};n(),new MutationObserver(n).observe(t,{subtree:!0,childList:!0,characterData:!0})}},[e,r]);return i.createElement(`div`,{ref:o,className:t,style:n},a)},ge=(e,t)=>{let n=e.includes(`top`),r=n?{top:0}:{bottom:0},i=e.includes(`center`)?{justifyContent:`center`}:e.includes(`right`)?{justifyContent:`flex-end`}:{};return{left:0,right:0,display:`flex`,position:`absolute`,transition:w()?void 0:`all 230ms cubic-bezier(.21,1.02,.73,1)`,transform:`translateY(${t*(n?1:-1)}px)`,...r,...i}},_e=h`
  z-index: 9999;
  > * {
    pointer-events: auto;
  }
`,Z=16,ve=({reverseOrder:e,position:t=`top-center`,toastOptions:n,gutter:r,children:a,toasterId:o,containerStyle:s,containerClassName:c})=>{let{toasts:l,handlers:u}=B(n,o);return i.createElement(`div`,{"data-rht-toaster":o||``,style:{position:`fixed`,zIndex:9999,top:Z,left:Z,right:Z,bottom:Z,pointerEvents:`none`,...s},className:c,onMouseEnter:u.startPause,onMouseLeave:u.endPause},l.map(n=>{let o=n.position||t,s=ge(o,u.calculateOffset(n,{reverseOrder:e,gutter:r,defaultPosition:t}));return i.createElement(he,{id:n.id,key:n.id,onHeightUpdate:u.updateHeight,className:n.visible?_e:``,style:s},n.type===`custom`?S(n.message,n):a?a(n):i.createElement(me,{toast:n,position:o}))}))},Q=r(),$={success:{alertClass:`alert-success`,icon:`icon-[heroicons--check-circle-20-solid]`},error:{alertClass:`alert-error`,icon:`icon-[heroicons--x-circle-20-solid]`},warning:{alertClass:`alert-warning`,icon:`icon-[heroicons--exclamation-triangle-20-solid]`},info:{alertClass:`alert-info`,icon:`icon-[heroicons--information-circle-20-solid]`},debug:{alertClass:`alert-neutral`,icon:`icon-[heroicons--code-bracket-20-solid]`}},ye=e=>{let t=(0,a.c)(14),{t:n,item:r}=e,i=$[r.level]||$.info,o=`
                alert ${i.alertClass} shadow-lg rounded-xl flex items-center gap-3 max-w-md w-full
                transform transition-all duration-300 ease-in-out pointer-events-auto
                ${n.visible?`opacity-100 translate-y-0 scale-100`:`opacity-0 -translate-y-4 scale-95`}
            `,s=`${i.icon} text-xl flex-none`,c;t[0]===s?c=t[1]:(c=(0,Q.jsx)(`span`,{className:s}),t[0]=s,t[1]=c);let l;t[2]===r.message?l=t[3]:(l=(0,Q.jsx)(`div`,{className:`flex-1 text-sm font-medium leading-tight`,children:r.message}),t[2]=r.message,t[3]=l);let u;t[4]===n.id?u=t[5]:(u=()=>R.dismiss(n.id),t[4]=n.id,t[5]=u);let d;t[6]===Symbol.for(`react.memo_cache_sentinel`)?(d=(0,Q.jsx)(`span`,{className:`icon-[heroicons--x-mark-20-solid] text-base`}),t[6]=d):d=t[6];let f;t[7]===u?f=t[8]:(f=(0,Q.jsx)(`button`,{type:`button`,onClick:u,className:`btn btn-ghost btn-xs btn-circle opacity-70 hover:opacity-100`,children:d}),t[7]=u,t[8]=f);let p;return t[9]!==o||t[10]!==c||t[11]!==l||t[12]!==f?(p=(0,Q.jsxs)(`div`,{className:o,children:[c,l,f]}),t[9]=o,t[10]=c,t[11]=l,t[12]=f,t[13]=p):p=t[13],p},be=e=>{R.custom(t=>(0,Q.jsx)(ye,{t,item:e}),{duration:4e3})};export{ve as n,be as t};