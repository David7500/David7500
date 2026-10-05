(()=>{var xu=0,Dl=1,_u=2;var _s=1,yu=2,or=3,ns=0,rn=1,fn=2,vi=0,cr=1,is=2,Ul=3,Nl=4,Mu=5;var ys=100,Su=101,bu=102,Eu=103,wu=104,Tu=200,Au=201,Ru=202,Cu=203,Fl=204,zl=205,Pu=206,Iu=207,Lu=208,Du=209,Uu=210,Nu=211,Fu=212,zu=213,Ou=214,ro=0,ao=1,oo=2,Ys=3,co=4,lo=5,ho=6,uo=7,Ol=0,Bu=1,ku=2,zn=0,Bl=1,kl=2,Hl=3,Vl=4,Gl=5,Wl=6,pa=7;var Xl=300,ss=301,Ms=302,Go=303,Wo=304,ma=306,js=1e3,Hn=1001,fo=1002,en=1003,Hu=1004;var ga=1005;var $e=1006,Xo=1007;var rs=1008;var Cn=1009,ql=1010,Yl=1011,lr=1012,qo=1013,ai=1014,Gn=1015,On=1016,Yo=1017,jo=1018,hr=1020,jl=35902,Zl=35899,$l=1021,Jl=1022,Wn=1023,di=1026,as=1027,Zo=1028,$o=1029,xi=1030,Jo=1031;var Ko=1033,va=33776,xa=33777,_a=33778,ya=33779,Qo=35840,tc=35841,ec=35842,nc=35843,ic=36196,sc=37492,rc=37496,ac=37488,oc=37489,Ma=37490,cc=37491,lc=37808,hc=37809,uc=37810,dc=37811,fc=37812,pc=37813,mc=37814,gc=37815,vc=37816,xc=37817,_c=37818,yc=37819,Mc=37820,Sc=37821,bc=36492,Ec=36494,wc=36495,Tc=36283,Ac=36284,Sa=36285,Rc=36286;var Ur=2300,po=2301,io=2302,yl=2303,Ml=2400,Sl=2401,bl=2402;var Vu=3200;var Cc=0,Gu=1,Fi="",yn="srgb",Nr="srgb-linear",Fr="linear",Ae="srgb";var so=7680;var Wu=519,Xu=512,qu=513,Yu=514,Pc=515,ju=516,Zu=517,Ic=518,$u=519,Kl=35044;var Ql="300 es",ei=2e3,Zs=2001;function Sf(i){for(let t=i.length-1;t>=0;--t)if(i[t]>=65535)return!0;return!1}function bf(i){return ArrayBuffer.isView(i)&&!(i instanceof DataView)}function zr(i){return document.createElementNS("http://www.w3.org/1999/xhtml",i)}function Ju(){let i=zr("canvas");return i.style.display="block",i}var Oh={},$s=null;function Or(...i){let t="THREE."+i.shift();$s?$s("log",t,...i):console.log(t,...i)}function Ku(i){let t=i[0];if(typeof t=="string"&&t.startsWith("TSL:")){let e=i[1];e&&e.isStackTrace?i[0]+=" "+e.getLocation():i[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return i}function ee(...i){i=Ku(i);let t="THREE."+i.shift();if($s)$s("warn",t,...i);else{let e=i[0];e&&e.isStackTrace?console.warn(e.getError(t)):console.warn(t,...i)}}function se(...i){i=Ku(i);let t="THREE."+i.shift();if($s)$s("error",t,...i);else{let e=i[0];e&&e.isStackTrace?console.error(e.getError(t)):console.error(t,...i)}}function gs(...i){let t=i.join(" ");t in Oh||(Oh[t]=!0,ee(...i))}function Qu(i,t,e){return new Promise(function(n,s){function r(){switch(i.clientWaitSync(t,i.SYNC_FLUSH_COMMANDS_BIT,0)){case i.WAIT_FAILED:s();break;case i.TIMEOUT_EXPIRED:setTimeout(r,e);break;default:n()}}setTimeout(r,e)})}var td={[ro]:ao,[oo]:ho,[co]:uo,[Ys]:lo,[ao]:ro,[ho]:oo,[uo]:co,[lo]:Ys},fi=class{addEventListener(t,e){this._listeners===void 0&&(this._listeners={});let n=this._listeners;n[t]===void 0&&(n[t]=[]),n[t].indexOf(e)===-1&&n[t].push(e)}hasEventListener(t,e){let n=this._listeners;return n===void 0?!1:n[t]!==void 0&&n[t].indexOf(e)!==-1}removeEventListener(t,e){let n=this._listeners;if(n===void 0)return;let s=n[t];if(s!==void 0){let r=s.indexOf(e);r!==-1&&s.splice(r,1)}}dispatchEvent(t){let e=this._listeners;if(e===void 0)return;let n=e[t.type];if(n!==void 0){t.target=this;let s=n.slice(0);for(let r=0,a=s.length;r<a;r++)s[r].call(this,t);t.target=null}}},un=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Bh=1234567,Pr=Math.PI/180,Js=180/Math.PI;function ui(){let i=Math.random()*4294967295|0,t=Math.random()*4294967295|0,e=Math.random()*4294967295|0,n=Math.random()*4294967295|0;return(un[i&255]+un[i>>8&255]+un[i>>16&255]+un[i>>24&255]+"-"+un[t&255]+un[t>>8&255]+"-"+un[t>>16&15|64]+un[t>>24&255]+"-"+un[e&63|128]+un[e>>8&255]+"-"+un[e>>16&255]+un[e>>24&255]+un[n&255]+un[n>>8&255]+un[n>>16&255]+un[n>>24&255]).toLowerCase()}function ae(i,t,e){return Math.max(t,Math.min(e,i))}function th(i,t){return(i%t+t)%t}function Ef(i,t,e,n,s){return n+(i-t)*(s-n)/(e-t)}function wf(i,t,e){return i!==t?(e-i)/(t-i):0}function Ir(i,t,e){return(1-e)*i+e*t}function Tf(i,t,e,n){return Ir(i,t,1-Math.exp(-e*n))}function Af(i,t=1){return t-Math.abs(th(i,t*2)-t)}function Rf(i,t,e){return i<=t?0:i>=e?1:(i=(i-t)/(e-t),i*i*(3-2*i))}function Cf(i,t,e){return i<=t?0:i>=e?1:(i=(i-t)/(e-t),i*i*i*(i*(i*6-15)+10))}function Pf(i,t){return i+Math.floor(Math.random()*(t-i+1))}function If(i,t){return i+Math.random()*(t-i)}function Lf(i){return i*(.5-Math.random())}function Df(i){i!==void 0&&(Bh=i);let t=Bh+=1831565813;return t=Math.imul(t^t>>>15,t|1),t^=t+Math.imul(t^t>>>7,t|61),((t^t>>>14)>>>0)/4294967296}function Uf(i){return i*Pr}function Nf(i){return i*Js}function Ff(i){return i>0&&Number.isInteger(i)&&2**Math.round(Math.log2(i))===i}function zf(i){return Math.pow(2,Math.ceil(Math.log(i)/Math.LN2))}function Of(i){return Math.pow(2,Math.floor(Math.log(i)/Math.LN2))}function Bf(i,t,e,n,s){let r=Math.cos,a=Math.sin,o=r(e/2),c=a(e/2),l=r((t+n)/2),h=a((t+n)/2),d=r((t-n)/2),u=a((t-n)/2),f=r((n-t)/2),g=a((n-t)/2);switch(s){case"XYX":i.set(o*h,c*d,c*u,o*l);break;case"YZY":i.set(c*u,o*h,c*d,o*l);break;case"ZXZ":i.set(c*d,c*u,o*h,o*l);break;case"XZX":i.set(o*h,c*g,c*f,o*l);break;case"YXY":i.set(c*f,o*h,c*g,o*l);break;case"ZYZ":i.set(c*g,c*f,o*h,o*l);break;default:ee("MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+s)}}function ti(i,t){switch(t.constructor){case Float32Array:return i;case Uint32Array:return i/4294967295;case Uint16Array:return i/65535;case Uint8Array:case Uint8ClampedArray:return i/255;case Int32Array:return Math.max(i/2147483647,-1);case Int16Array:return Math.max(i/32767,-1);case Int8Array:return Math.max(i/127,-1);default:throw new Error("THREE.MathUtils: Invalid component type.")}}function Ce(i,t){switch(t.constructor){case Float32Array:return i;case Uint32Array:return Math.round(i*4294967295);case Uint16Array:return Math.round(i*65535);case Uint8Array:case Uint8ClampedArray:return Math.round(i*255);case Int32Array:return Math.round(i*2147483647);case Int16Array:return Math.round(i*32767);case Int8Array:return Math.round(i*127);default:throw new Error("THREE.MathUtils: Invalid component type.")}}var _i={DEG2RAD:Pr,RAD2DEG:Js,generateUUID:ui,clamp:ae,euclideanModulo:th,mapLinear:Ef,inverseLerp:wf,lerp:Ir,damp:Tf,pingpong:Af,smoothstep:Rf,smootherstep:Cf,randInt:Pf,randFloat:If,randFloatSpread:Lf,seededRandom:Df,degToRad:Uf,radToDeg:Nf,isPowerOfTwo:Ff,ceilPowerOfTwo:zf,floorPowerOfTwo:Of,setQuaternionFromProperEuler:Bf,normalize:Ce,denormalize:ti},ah=class ah{constructor(t=0,e=0){this.x=t,this.y=e}get width(){return this.x}set width(t){this.x=t}get height(){return this.y}set height(t){this.y=t}set(t,e){return this.x=t,this.y=e,this}setScalar(t){return this.x=t,this.y=t,this}setX(t){return this.x=t,this}setY(t){return this.y=t,this}setComponent(t,e){switch(t){case 0:this.x=e;break;case 1:this.y=e;break;default:throw new Error("THREE.Vector2: index is out of range: "+t)}return this}getComponent(t){switch(t){case 0:return this.x;case 1:return this.y;default:throw new Error("THREE.Vector2: index is out of range: "+t)}}clone(){return new this.constructor(this.x,this.y)}copy(t){return this.x=t.x,this.y=t.y,this}add(t){return this.x+=t.x,this.y+=t.y,this}addScalar(t){return this.x+=t,this.y+=t,this}addVectors(t,e){return this.x=t.x+e.x,this.y=t.y+e.y,this}addScaledVector(t,e){return this.x+=t.x*e,this.y+=t.y*e,this}sub(t){return this.x-=t.x,this.y-=t.y,this}subScalar(t){return this.x-=t,this.y-=t,this}subVectors(t,e){return this.x=t.x-e.x,this.y=t.y-e.y,this}multiply(t){return this.x*=t.x,this.y*=t.y,this}multiplyScalar(t){return this.x*=t,this.y*=t,this}divide(t){return this.x/=t.x,this.y/=t.y,this}divideScalar(t){return this.multiplyScalar(1/t)}applyMatrix3(t){let e=this.x,n=this.y,s=t.elements;return this.x=s[0]*e+s[3]*n+s[6],this.y=s[1]*e+s[4]*n+s[7],this}min(t){return this.x=Math.min(this.x,t.x),this.y=Math.min(this.y,t.y),this}max(t){return this.x=Math.max(this.x,t.x),this.y=Math.max(this.y,t.y),this}clamp(t,e){return this.x=ae(this.x,t.x,e.x),this.y=ae(this.y,t.y,e.y),this}clampScalar(t,e){return this.x=ae(this.x,t,e),this.y=ae(this.y,t,e),this}clampLength(t,e){let n=this.length();return this.divideScalar(n||1).multiplyScalar(ae(n,t,e))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(t){return this.x*t.x+this.y*t.y}cross(t){return this.x*t.y-this.y*t.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(t){let e=Math.sqrt(this.lengthSq()*t.lengthSq());if(e===0)return Math.PI/2;let n=this.dot(t)/e;return Math.acos(ae(n,-1,1))}distanceTo(t){return Math.sqrt(this.distanceToSquared(t))}distanceToSquared(t){let e=this.x-t.x,n=this.y-t.y;return e*e+n*n}manhattanDistanceTo(t){return Math.abs(this.x-t.x)+Math.abs(this.y-t.y)}setLength(t){return this.normalize().multiplyScalar(t)}lerp(t,e){return this.x+=(t.x-this.x)*e,this.y+=(t.y-this.y)*e,this}lerpVectors(t,e,n){return this.x=t.x+(e.x-t.x)*n,this.y=t.y+(e.y-t.y)*n,this}equals(t){return t.x===this.x&&t.y===this.y}fromArray(t,e=0){return this.x=t[e],this.y=t[e+1],this}toArray(t=[],e=0){return t[e]=this.x,t[e+1]=this.y,t}fromBufferAttribute(t,e){return this.x=t.getX(e),this.y=t.getY(e),this}rotateAround(t,e){let n=Math.cos(e),s=Math.sin(e),r=this.x-t.x,a=this.y-t.y;return this.x=r*n-a*s+t.x,this.y=r*s+a*n+t.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};ah.prototype.isVector2=!0;var mt=ah,nn=class{constructor(t=0,e=0,n=0,s=1){this.isQuaternion=!0,this._x=t,this._y=e,this._z=n,this._w=s}static slerpFlat(t,e,n,s,r,a,o){let c=n[s+0],l=n[s+1],h=n[s+2],d=n[s+3],u=r[a+0],f=r[a+1],g=r[a+2],x=r[a+3];if(d!==x||c!==u||l!==f||h!==g){let p=c*u+l*f+h*g+d*x;p<0&&(u=-u,f=-f,g=-g,x=-x,p=-p);let m=1-o;if(p<.9995){let S=Math.acos(p),E=Math.sin(S);m=Math.sin(m*S)/E,o=Math.sin(o*S)/E,c=c*m+u*o,l=l*m+f*o,h=h*m+g*o,d=d*m+x*o}else{c=c*m+u*o,l=l*m+f*o,h=h*m+g*o,d=d*m+x*o;let S=1/Math.sqrt(c*c+l*l+h*h+d*d);c*=S,l*=S,h*=S,d*=S}}t[e]=c,t[e+1]=l,t[e+2]=h,t[e+3]=d}static multiplyQuaternionsFlat(t,e,n,s,r,a){let o=n[s],c=n[s+1],l=n[s+2],h=n[s+3],d=r[a],u=r[a+1],f=r[a+2],g=r[a+3];return t[e]=o*g+h*d+c*f-l*u,t[e+1]=c*g+h*u+l*d-o*f,t[e+2]=l*g+h*f+o*u-c*d,t[e+3]=h*g-o*d-c*u-l*f,t}get x(){return this._x}set x(t){this._x=t,this._onChangeCallback()}get y(){return this._y}set y(t){this._y=t,this._onChangeCallback()}get z(){return this._z}set z(t){this._z=t,this._onChangeCallback()}get w(){return this._w}set w(t){this._w=t,this._onChangeCallback()}set(t,e,n,s){return this._x=t,this._y=e,this._z=n,this._w=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(t){return this._x=t.x,this._y=t.y,this._z=t.z,this._w=t.w,this._onChangeCallback(),this}setFromEuler(t,e=!0){let n=t._x,s=t._y,r=t._z,a=t._order,o=Math.cos,c=Math.sin,l=o(n/2),h=o(s/2),d=o(r/2),u=c(n/2),f=c(s/2),g=c(r/2);switch(a){case"XYZ":this._x=u*h*d+l*f*g,this._y=l*f*d-u*h*g,this._z=l*h*g+u*f*d,this._w=l*h*d-u*f*g;break;case"YXZ":this._x=u*h*d+l*f*g,this._y=l*f*d-u*h*g,this._z=l*h*g-u*f*d,this._w=l*h*d+u*f*g;break;case"ZXY":this._x=u*h*d-l*f*g,this._y=l*f*d+u*h*g,this._z=l*h*g+u*f*d,this._w=l*h*d-u*f*g;break;case"ZYX":this._x=u*h*d-l*f*g,this._y=l*f*d+u*h*g,this._z=l*h*g-u*f*d,this._w=l*h*d+u*f*g;break;case"YZX":this._x=u*h*d+l*f*g,this._y=l*f*d+u*h*g,this._z=l*h*g-u*f*d,this._w=l*h*d-u*f*g;break;case"XZY":this._x=u*h*d-l*f*g,this._y=l*f*d-u*h*g,this._z=l*h*g+u*f*d,this._w=l*h*d+u*f*g;break;default:ee("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return e===!0&&this._onChangeCallback(),this}setFromAxisAngle(t,e){let n=e/2,s=Math.sin(n);return this._x=t.x*s,this._y=t.y*s,this._z=t.z*s,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(t){let e=t.elements,n=e[0],s=e[4],r=e[8],a=e[1],o=e[5],c=e[9],l=e[2],h=e[6],d=e[10],u=n+o+d;if(u>0){let f=.5/Math.sqrt(u+1);this._w=.25/f,this._x=(h-c)*f,this._y=(r-l)*f,this._z=(a-s)*f}else if(n>o&&n>d){let f=2*Math.sqrt(1+n-o-d);this._w=(h-c)/f,this._x=.25*f,this._y=(s+a)/f,this._z=(r+l)/f}else if(o>d){let f=2*Math.sqrt(1+o-n-d);this._w=(r-l)/f,this._x=(s+a)/f,this._y=.25*f,this._z=(c+h)/f}else{let f=2*Math.sqrt(1+d-n-o);this._w=(a-s)/f,this._x=(r+l)/f,this._y=(c+h)/f,this._z=.25*f}return this._onChangeCallback(),this}setFromUnitVectors(t,e){let n=t.dot(e)+1;return n<1e-8?(n=0,Math.abs(t.x)>Math.abs(t.z)?(this._x=-t.y,this._y=t.x,this._z=0,this._w=n):(this._x=0,this._y=-t.z,this._z=t.y,this._w=n)):(this._x=t.y*e.z-t.z*e.y,this._y=t.z*e.x-t.x*e.z,this._z=t.x*e.y-t.y*e.x,this._w=n),this.normalize()}angleTo(t){return 2*Math.acos(Math.abs(ae(this.dot(t),-1,1)))}rotateTowards(t,e){let n=this.angleTo(t);if(n===0)return this;let s=Math.min(1,e/n);return this.slerp(t,s),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(t){return this._x*t._x+this._y*t._y+this._z*t._z+this._w*t._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let t=this.length();return t===0?(this._x=0,this._y=0,this._z=0,this._w=1):(t=1/t,this._x=this._x*t,this._y=this._y*t,this._z=this._z*t,this._w=this._w*t),this._onChangeCallback(),this}multiply(t){return this.multiplyQuaternions(this,t)}premultiply(t){return this.multiplyQuaternions(t,this)}multiplyQuaternions(t,e){let n=t._x,s=t._y,r=t._z,a=t._w,o=e._x,c=e._y,l=e._z,h=e._w;return this._x=n*h+a*o+s*l-r*c,this._y=s*h+a*c+r*o-n*l,this._z=r*h+a*l+n*c-s*o,this._w=a*h-n*o-s*c-r*l,this._onChangeCallback(),this}slerp(t,e){let n=t._x,s=t._y,r=t._z,a=t._w,o=this.dot(t);o<0&&(n=-n,s=-s,r=-r,a=-a,o=-o);let c=1-e;if(o<.9995){let l=Math.acos(o),h=Math.sin(l);c=Math.sin(c*l)/h,e=Math.sin(e*l)/h,this._x=this._x*c+n*e,this._y=this._y*c+s*e,this._z=this._z*c+r*e,this._w=this._w*c+a*e,this._onChangeCallback()}else this._x=this._x*c+n*e,this._y=this._y*c+s*e,this._z=this._z*c+r*e,this._w=this._w*c+a*e,this.normalize();return this}slerpQuaternions(t,e,n){return this.copy(t).slerp(e,n)}random(){let t=2*Math.PI*Math.random(),e=2*Math.PI*Math.random(),n=Math.random(),s=Math.sqrt(1-n),r=Math.sqrt(n);return this.set(s*Math.sin(t),s*Math.cos(t),r*Math.sin(e),r*Math.cos(e))}equals(t){return t._x===this._x&&t._y===this._y&&t._z===this._z&&t._w===this._w}fromArray(t,e=0){return this._x=t[e],this._y=t[e+1],this._z=t[e+2],this._w=t[e+3],this._onChangeCallback(),this}toArray(t=[],e=0){return t[e]=this._x,t[e+1]=this._y,t[e+2]=this._z,t[e+3]=this._w,t}fromBufferAttribute(t,e){return this._x=t.getX(e),this._y=t.getY(e),this._z=t.getZ(e),this._w=t.getW(e),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(t){return this._onChangeCallback=t,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}},oh=class oh{constructor(t=0,e=0,n=0){this.x=t,this.y=e,this.z=n}set(t,e,n){return n===void 0&&(n=this.z),this.x=t,this.y=e,this.z=n,this}setScalar(t){return this.x=t,this.y=t,this.z=t,this}setX(t){return this.x=t,this}setY(t){return this.y=t,this}setZ(t){return this.z=t,this}setComponent(t,e){switch(t){case 0:this.x=e;break;case 1:this.y=e;break;case 2:this.z=e;break;default:throw new Error("THREE.Vector3: index is out of range: "+t)}return this}getComponent(t){switch(t){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("THREE.Vector3: index is out of range: "+t)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(t){return this.x=t.x,this.y=t.y,this.z=t.z,this}add(t){return this.x+=t.x,this.y+=t.y,this.z+=t.z,this}addScalar(t){return this.x+=t,this.y+=t,this.z+=t,this}addVectors(t,e){return this.x=t.x+e.x,this.y=t.y+e.y,this.z=t.z+e.z,this}addScaledVector(t,e){return this.x+=t.x*e,this.y+=t.y*e,this.z+=t.z*e,this}sub(t){return this.x-=t.x,this.y-=t.y,this.z-=t.z,this}subScalar(t){return this.x-=t,this.y-=t,this.z-=t,this}subVectors(t,e){return this.x=t.x-e.x,this.y=t.y-e.y,this.z=t.z-e.z,this}multiply(t){return this.x*=t.x,this.y*=t.y,this.z*=t.z,this}multiplyScalar(t){return this.x*=t,this.y*=t,this.z*=t,this}multiplyVectors(t,e){return this.x=t.x*e.x,this.y=t.y*e.y,this.z=t.z*e.z,this}applyEuler(t){return this.applyQuaternion(kh.setFromEuler(t))}applyAxisAngle(t,e){return this.applyQuaternion(kh.setFromAxisAngle(t,e))}applyMatrix3(t){let e=this.x,n=this.y,s=this.z,r=t.elements;return this.x=r[0]*e+r[3]*n+r[6]*s,this.y=r[1]*e+r[4]*n+r[7]*s,this.z=r[2]*e+r[5]*n+r[8]*s,this}applyNormalMatrix(t){return this.applyMatrix3(t).normalize()}applyMatrix4(t){let e=this.x,n=this.y,s=this.z,r=t.elements,a=1/(r[3]*e+r[7]*n+r[11]*s+r[15]);return this.x=(r[0]*e+r[4]*n+r[8]*s+r[12])*a,this.y=(r[1]*e+r[5]*n+r[9]*s+r[13])*a,this.z=(r[2]*e+r[6]*n+r[10]*s+r[14])*a,this}applyQuaternion(t){let e=this.x,n=this.y,s=this.z,r=t.x,a=t.y,o=t.z,c=t.w,l=2*(a*s-o*n),h=2*(o*e-r*s),d=2*(r*n-a*e);return this.x=e+c*l+a*d-o*h,this.y=n+c*h+o*l-r*d,this.z=s+c*d+r*h-a*l,this}project(t){return this.applyMatrix4(t.matrixWorldInverse).applyMatrix4(t.projectionMatrix)}unproject(t){return this.applyMatrix4(t.projectionMatrixInverse).applyMatrix4(t.matrixWorld)}transformDirection(t){let e=this.x,n=this.y,s=this.z,r=t.elements;return this.x=r[0]*e+r[4]*n+r[8]*s,this.y=r[1]*e+r[5]*n+r[9]*s,this.z=r[2]*e+r[6]*n+r[10]*s,this.normalize()}divide(t){return this.x/=t.x,this.y/=t.y,this.z/=t.z,this}divideScalar(t){return this.multiplyScalar(1/t)}min(t){return this.x=Math.min(this.x,t.x),this.y=Math.min(this.y,t.y),this.z=Math.min(this.z,t.z),this}max(t){return this.x=Math.max(this.x,t.x),this.y=Math.max(this.y,t.y),this.z=Math.max(this.z,t.z),this}clamp(t,e){return this.x=ae(this.x,t.x,e.x),this.y=ae(this.y,t.y,e.y),this.z=ae(this.z,t.z,e.z),this}clampScalar(t,e){return this.x=ae(this.x,t,e),this.y=ae(this.y,t,e),this.z=ae(this.z,t,e),this}clampLength(t,e){let n=this.length();return this.divideScalar(n||1).multiplyScalar(ae(n,t,e))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(t){return this.x*t.x+this.y*t.y+this.z*t.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(t){return this.normalize().multiplyScalar(t)}lerp(t,e){return this.x+=(t.x-this.x)*e,this.y+=(t.y-this.y)*e,this.z+=(t.z-this.z)*e,this}lerpVectors(t,e,n){return this.x=t.x+(e.x-t.x)*n,this.y=t.y+(e.y-t.y)*n,this.z=t.z+(e.z-t.z)*n,this}cross(t){return this.crossVectors(this,t)}crossVectors(t,e){let n=t.x,s=t.y,r=t.z,a=e.x,o=e.y,c=e.z;return this.x=s*c-r*o,this.y=r*a-n*c,this.z=n*o-s*a,this}projectOnVector(t){let e=t.lengthSq();if(e===0)return this.set(0,0,0);let n=t.dot(this)/e;return this.copy(t).multiplyScalar(n)}projectOnPlane(t){return Zc.copy(this).projectOnVector(t),this.sub(Zc)}reflect(t){return this.sub(Zc.copy(t).multiplyScalar(2*this.dot(t)))}angleTo(t){let e=Math.sqrt(this.lengthSq()*t.lengthSq());if(e===0)return Math.PI/2;let n=this.dot(t)/e;return Math.acos(ae(n,-1,1))}distanceTo(t){return Math.sqrt(this.distanceToSquared(t))}distanceToSquared(t){let e=this.x-t.x,n=this.y-t.y,s=this.z-t.z;return e*e+n*n+s*s}manhattanDistanceTo(t){return Math.abs(this.x-t.x)+Math.abs(this.y-t.y)+Math.abs(this.z-t.z)}setFromSpherical(t){return this.setFromSphericalCoords(t.radius,t.phi,t.theta)}setFromSphericalCoords(t,e,n){let s=Math.sin(e)*t;return this.x=s*Math.sin(n),this.y=Math.cos(e)*t,this.z=s*Math.cos(n),this}setFromCylindrical(t){return this.setFromCylindricalCoords(t.radius,t.theta,t.y)}setFromCylindricalCoords(t,e,n){return this.x=t*Math.sin(e),this.y=n,this.z=t*Math.cos(e),this}setFromMatrixPosition(t){let e=t.elements;return this.x=e[12],this.y=e[13],this.z=e[14],this}setFromMatrixScale(t){let e=this.setFromMatrixColumn(t,0).length(),n=this.setFromMatrixColumn(t,1).length(),s=this.setFromMatrixColumn(t,2).length();return this.x=e,this.y=n,this.z=s,this}setFromMatrixColumn(t,e){return this.fromArray(t.elements,e*4)}setFromMatrix3Column(t,e){return this.fromArray(t.elements,e*3)}setFromEuler(t){return this.x=t._x,this.y=t._y,this.z=t._z,this}setFromColor(t){return this.x=t.r,this.y=t.g,this.z=t.b,this}equals(t){return t.x===this.x&&t.y===this.y&&t.z===this.z}fromArray(t,e=0){return this.x=t[e],this.y=t[e+1],this.z=t[e+2],this}toArray(t=[],e=0){return t[e]=this.x,t[e+1]=this.y,t[e+2]=this.z,t}fromBufferAttribute(t,e){return this.x=t.getX(e),this.y=t.getY(e),this.z=t.getZ(e),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){let t=Math.random()*Math.PI*2,e=Math.random()*2-1,n=Math.sqrt(1-e*e);return this.x=n*Math.cos(t),this.y=e,this.z=n*Math.sin(t),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};oh.prototype.isVector3=!0;var P=oh,Zc=new P,kh=new nn,ch=class ch{constructor(t,e,n,s,r,a,o,c,l){this.elements=[1,0,0,0,1,0,0,0,1],t!==void 0&&this.set(t,e,n,s,r,a,o,c,l)}set(t,e,n,s,r,a,o,c,l){let h=this.elements;return h[0]=t,h[1]=s,h[2]=o,h[3]=e,h[4]=r,h[5]=c,h[6]=n,h[7]=a,h[8]=l,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(t){let e=this.elements,n=t.elements;return e[0]=n[0],e[1]=n[1],e[2]=n[2],e[3]=n[3],e[4]=n[4],e[5]=n[5],e[6]=n[6],e[7]=n[7],e[8]=n[8],this}extractBasis(t,e,n){return t.setFromMatrix3Column(this,0),e.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(t){let e=t.elements;return this.set(e[0],e[4],e[8],e[1],e[5],e[9],e[2],e[6],e[10]),this}multiply(t){return this.multiplyMatrices(this,t)}premultiply(t){return this.multiplyMatrices(t,this)}multiplyMatrices(t,e){let n=t.elements,s=e.elements,r=this.elements,a=n[0],o=n[3],c=n[6],l=n[1],h=n[4],d=n[7],u=n[2],f=n[5],g=n[8],x=s[0],p=s[3],m=s[6],S=s[1],E=s[4],v=s[7],b=s[2],M=s[5],A=s[8];return r[0]=a*x+o*S+c*b,r[3]=a*p+o*E+c*M,r[6]=a*m+o*v+c*A,r[1]=l*x+h*S+d*b,r[4]=l*p+h*E+d*M,r[7]=l*m+h*v+d*A,r[2]=u*x+f*S+g*b,r[5]=u*p+f*E+g*M,r[8]=u*m+f*v+g*A,this}multiplyScalar(t){let e=this.elements;return e[0]*=t,e[3]*=t,e[6]*=t,e[1]*=t,e[4]*=t,e[7]*=t,e[2]*=t,e[5]*=t,e[8]*=t,this}determinant(){let t=this.elements,e=t[0],n=t[1],s=t[2],r=t[3],a=t[4],o=t[5],c=t[6],l=t[7],h=t[8];return e*a*h-e*o*l-n*r*h+n*o*c+s*r*l-s*a*c}invert(){let t=this.elements,e=t[0],n=t[1],s=t[2],r=t[3],a=t[4],o=t[5],c=t[6],l=t[7],h=t[8],d=h*a-o*l,u=o*c-h*r,f=l*r-a*c,g=e*d+n*u+s*f;if(g===0)return this.set(0,0,0,0,0,0,0,0,0);let x=1/g;return t[0]=d*x,t[1]=(s*l-h*n)*x,t[2]=(o*n-s*a)*x,t[3]=u*x,t[4]=(h*e-s*c)*x,t[5]=(s*r-o*e)*x,t[6]=f*x,t[7]=(n*c-l*e)*x,t[8]=(a*e-n*r)*x,this}transpose(){let t,e=this.elements;return t=e[1],e[1]=e[3],e[3]=t,t=e[2],e[2]=e[6],e[6]=t,t=e[5],e[5]=e[7],e[7]=t,this}getNormalMatrix(t){return this.setFromMatrix4(t).invert().transpose()}transposeIntoArray(t){let e=this.elements;return t[0]=e[0],t[1]=e[3],t[2]=e[6],t[3]=e[1],t[4]=e[4],t[5]=e[7],t[6]=e[2],t[7]=e[5],t[8]=e[8],this}setUvTransform(t,e,n,s,r,a,o){let c=Math.cos(r),l=Math.sin(r);return this.set(n*c,n*l,-n*(c*a+l*o)+a+t,-s*l,s*c,-s*(-l*a+c*o)+o+e,0,0,1),this}scale(t,e){return gs("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply($c.makeScale(t,e)),this}rotate(t){return gs("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply($c.makeRotation(-t)),this}translate(t,e){return gs("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply($c.makeTranslation(t,e)),this}makeTranslation(t,e){return t.isVector2?this.set(1,0,t.x,0,1,t.y,0,0,1):this.set(1,0,t,0,1,e,0,0,1),this}makeRotation(t){let e=Math.cos(t),n=Math.sin(t);return this.set(e,-n,0,n,e,0,0,0,1),this}makeScale(t,e){return this.set(t,0,0,0,e,0,0,0,1),this}equals(t){let e=this.elements,n=t.elements;for(let s=0;s<9;s++)if(e[s]!==n[s])return!1;return!0}fromArray(t,e=0){for(let n=0;n<9;n++)this.elements[n]=t[n+e];return this}toArray(t=[],e=0){let n=this.elements;return t[e]=n[0],t[e+1]=n[1],t[e+2]=n[2],t[e+3]=n[3],t[e+4]=n[4],t[e+5]=n[5],t[e+6]=n[6],t[e+7]=n[7],t[e+8]=n[8],t}clone(){return new this.constructor().fromArray(this.elements)}};ch.prototype.isMatrix3=!0;var ce=ch,$c=new ce,Hh=new ce().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Vh=new ce().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function kf(){let i={enabled:!0,workingColorSpace:Nr,spaces:{},convert:function(s,r,a){return this.enabled===!1||r===a||!r||!a||(this.spaces[r].transfer===Ae&&(s.r=Li(s.r),s.g=Li(s.g),s.b=Li(s.b)),this.spaces[r].primaries!==this.spaces[a].primaries&&(s.applyMatrix3(this.spaces[r].toXYZ),s.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===Ae&&(s.r=qs(s.r),s.g=qs(s.g),s.b=qs(s.b))),s},workingToColorSpace:function(s,r){return this.convert(s,this.workingColorSpace,r)},colorSpaceToWorking:function(s,r){return this.convert(s,r,this.workingColorSpace)},getPrimaries:function(s){return this.spaces[s].primaries},getTransfer:function(s){return s===Fi?Fr:this.spaces[s].transfer},getToneMappingMode:function(s){return this.spaces[s].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(s,r=this.workingColorSpace){return s.fromArray(this.spaces[r].luminanceCoefficients)},define:function(s){Object.assign(this.spaces,s)},_getMatrix:function(s,r,a){return s.copy(this.spaces[r].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(s){return this.spaces[s].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(s=this.workingColorSpace){return this.spaces[s].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(s,r){return gs("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),i.workingToColorSpace(s,r)},toWorkingColorSpace:function(s,r){return gs("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),i.colorSpaceToWorking(s,r)}},t=[.64,.33,.3,.6,.15,.06],e=[.2126,.7152,.0722],n=[.3127,.329];return i.define({[Nr]:{primaries:t,whitePoint:n,transfer:Fr,toXYZ:Hh,fromXYZ:Vh,luminanceCoefficients:e,workingColorSpaceConfig:{unpackColorSpace:yn},outputColorSpaceConfig:{drawingBufferColorSpace:yn}},[yn]:{primaries:t,whitePoint:n,transfer:Ae,toXYZ:Hh,fromXYZ:Vh,luminanceCoefficients:e,outputColorSpaceConfig:{drawingBufferColorSpace:yn}}}),i}var Se=kf();function Li(i){return i<.04045?i*.0773993808:Math.pow(i*.9478672986+.0521327014,2.4)}function qs(i){return i<.0031308?i*12.92:1.055*Math.pow(i,.41666)-.055}var Ps,mo=class{static getDataURL(t,e="image/png"){if(/^data:/i.test(t.src)||typeof HTMLCanvasElement>"u")return t.src;let n;if(t instanceof HTMLCanvasElement)n=t;else{Ps===void 0&&(Ps=zr("canvas")),Ps.width=t.width,Ps.height=t.height;let s=Ps.getContext("2d");t instanceof ImageData?s.putImageData(t,0,0):s.drawImage(t,0,0,t.width,t.height),n=Ps}return n.toDataURL(e)}static sRGBToLinear(t){if(typeof HTMLImageElement<"u"&&t instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&t instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&t instanceof ImageBitmap){let e=zr("canvas");e.width=t.width,e.height=t.height;let n=e.getContext("2d");n.drawImage(t,0,0,t.width,t.height);let s=n.getImageData(0,0,t.width,t.height),r=s.data;for(let a=0;a<r.length;a++)r[a]=Li(r[a]/255)*255;return n.putImageData(s,0,0),e}else if(t.data){let e=t.data.slice(0);for(let n=0;n<e.length;n++)e instanceof Uint8Array||e instanceof Uint8ClampedArray?e[n]=Math.floor(Li(e[n]/255)*255):e[n]=Li(e[n]);return{data:e,width:t.width,height:t.height}}else return ee("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),t}},Hf=0,Ks=class{constructor(t=null){this.isTextureSource=!0,Object.defineProperty(this,"id",{value:Hf++}),this.uuid=ui(),this.data=t,this.dataReady=!0,this.version=0}getSize(t){let e=this.data;return typeof HTMLVideoElement<"u"&&e instanceof HTMLVideoElement?t.set(e.videoWidth,e.videoHeight,0):typeof VideoFrame<"u"&&e instanceof VideoFrame?t.set(e.displayWidth,e.displayHeight,0):e!==null?t.set(e.width,e.height,e.depth||0):t.set(0,0,0),t}set needsUpdate(t){t===!0&&this.version++}toJSON(t){let e=t===void 0||typeof t=="string";if(!e&&t.images[this.uuid]!==void 0)return t.images[this.uuid];let n={uuid:this.uuid,url:""},s=this.data;if(s!==null){let r;if(Array.isArray(s)){r=[];for(let a=0,o=s.length;a<o;a++)s[a].isDataTexture?r.push(Jc(s[a].image)):r.push(Jc(s[a]))}else r=Jc(s);n.url=r}return e||(t.images[this.uuid]=n),n}};function Jc(i){return typeof HTMLImageElement<"u"&&i instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&i instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&i instanceof ImageBitmap?mo.getDataURL(i):i.data?{data:Array.from(i.data),width:i.width,height:i.height,type:i.data.constructor.name}:(ee("Texture: Unable to serialize Texture."),{})}var Vf=0,Kc=new P,Mn=class i extends fi{constructor(t=i.DEFAULT_IMAGE,e=i.DEFAULT_MAPPING,n=Hn,s=Hn,r=$e,a=rs,o=Wn,c=Cn,l=i.DEFAULT_ANISOTROPY,h=Fi){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Vf++}),this.uuid=ui(),this.name="",this.source=new Ks(t),this.mipmaps=[],this.mapping=e,this.channel=0,this.wrapS=n,this.wrapT=s,this.magFilter=r,this.minFilter=a,this.anisotropy=l,this.format=o,this.internalFormat=null,this.type=c,this.offset=new mt(0,0),this.repeat=new mt(1,1),this.center=new mt(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new ce,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=h,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(t&&t.depth&&t.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(Kc).x}get height(){return this.source.getSize(Kc).y}get depth(){return this.source.getSize(Kc).z}get image(){return this.source.data}set image(t){this.source.data=t}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(t,e){this.updateRanges.push({start:t,count:e})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(t){return this.name=t.name,this.source=t.source,this.mipmaps=t.mipmaps.slice(0),this.mapping=t.mapping,this.channel=t.channel,this.wrapS=t.wrapS,this.wrapT=t.wrapT,this.magFilter=t.magFilter,this.minFilter=t.minFilter,this.anisotropy=t.anisotropy,this.format=t.format,this.internalFormat=t.internalFormat,this.type=t.type,this.normalized=t.normalized,this.offset.copy(t.offset),this.repeat.copy(t.repeat),this.center.copy(t.center),this.rotation=t.rotation,this.matrixAutoUpdate=t.matrixAutoUpdate,this.matrix.copy(t.matrix),this.generateMipmaps=t.generateMipmaps,this.premultiplyAlpha=t.premultiplyAlpha,this.flipY=t.flipY,this.unpackAlignment=t.unpackAlignment,this.colorSpace=t.colorSpace,this.renderTarget=t.renderTarget,this.isRenderTargetTexture=t.isRenderTargetTexture,this.isArrayTexture=t.isArrayTexture,this.userData=JSON.parse(JSON.stringify(t.userData)),this.needsUpdate=!0,this}setValues(t){for(let e in t){let n=t[e];if(n===void 0){ee(`Texture.setValues(): parameter '${e}' has value of undefined.`);continue}let s=this[e];if(s===void 0){ee(`Texture.setValues(): property '${e}' does not exist.`);continue}s&&n&&s.isVector2&&n.isVector2||s&&n&&s.isVector3&&n.isVector3||s&&n&&s.isMatrix3&&n.isMatrix3?s.copy(n):this[e]=n}}toJSON(t){let e=t===void 0||typeof t=="string";if(!e&&t.textures[this.uuid]!==void 0)return t.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(t).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),e||(t.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(t){if(this.mapping!==Xl)return t;if(t.applyMatrix3(this.matrix),t.x<0||t.x>1)switch(this.wrapS){case js:t.x=t.x-Math.floor(t.x);break;case Hn:t.x=t.x<0?0:1;break;case fo:Math.abs(Math.floor(t.x)%2)===1?t.x=Math.ceil(t.x)-t.x:t.x=t.x-Math.floor(t.x);break}if(t.y<0||t.y>1)switch(this.wrapT){case js:t.y=t.y-Math.floor(t.y);break;case Hn:t.y=t.y<0?0:1;break;case fo:Math.abs(Math.floor(t.y)%2)===1?t.y=Math.ceil(t.y)-t.y:t.y=t.y-Math.floor(t.y);break}return this.flipY&&(t.y=1-t.y),t}set needsUpdate(t){t===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(t){t===!0&&this.pmremVersion++}};Mn.DEFAULT_IMAGE=null;Mn.DEFAULT_MAPPING=Xl;Mn.DEFAULT_ANISOTROPY=1;var lh=class lh{constructor(t=0,e=0,n=0,s=1){this.x=t,this.y=e,this.z=n,this.w=s}get width(){return this.z}set width(t){this.z=t}get height(){return this.w}set height(t){this.w=t}set(t,e,n,s){return this.x=t,this.y=e,this.z=n,this.w=s,this}setScalar(t){return this.x=t,this.y=t,this.z=t,this.w=t,this}setX(t){return this.x=t,this}setY(t){return this.y=t,this}setZ(t){return this.z=t,this}setW(t){return this.w=t,this}setComponent(t,e){switch(t){case 0:this.x=e;break;case 1:this.y=e;break;case 2:this.z=e;break;case 3:this.w=e;break;default:throw new Error("THREE.Vector4: index is out of range: "+t)}return this}getComponent(t){switch(t){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("THREE.Vector4: index is out of range: "+t)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(t){return this.x=t.x,this.y=t.y,this.z=t.z,this.w=t.w!==void 0?t.w:1,this}add(t){return this.x+=t.x,this.y+=t.y,this.z+=t.z,this.w+=t.w,this}addScalar(t){return this.x+=t,this.y+=t,this.z+=t,this.w+=t,this}addVectors(t,e){return this.x=t.x+e.x,this.y=t.y+e.y,this.z=t.z+e.z,this.w=t.w+e.w,this}addScaledVector(t,e){return this.x+=t.x*e,this.y+=t.y*e,this.z+=t.z*e,this.w+=t.w*e,this}sub(t){return this.x-=t.x,this.y-=t.y,this.z-=t.z,this.w-=t.w,this}subScalar(t){return this.x-=t,this.y-=t,this.z-=t,this.w-=t,this}subVectors(t,e){return this.x=t.x-e.x,this.y=t.y-e.y,this.z=t.z-e.z,this.w=t.w-e.w,this}multiply(t){return this.x*=t.x,this.y*=t.y,this.z*=t.z,this.w*=t.w,this}multiplyScalar(t){return this.x*=t,this.y*=t,this.z*=t,this.w*=t,this}applyMatrix4(t){let e=this.x,n=this.y,s=this.z,r=this.w,a=t.elements;return this.x=a[0]*e+a[4]*n+a[8]*s+a[12]*r,this.y=a[1]*e+a[5]*n+a[9]*s+a[13]*r,this.z=a[2]*e+a[6]*n+a[10]*s+a[14]*r,this.w=a[3]*e+a[7]*n+a[11]*s+a[15]*r,this}divide(t){return this.x/=t.x,this.y/=t.y,this.z/=t.z,this.w/=t.w,this}divideScalar(t){return this.multiplyScalar(1/t)}setAxisAngleFromQuaternion(t){this.w=2*Math.acos(t.w);let e=Math.sqrt(1-t.w*t.w);return e<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=t.x/e,this.y=t.y/e,this.z=t.z/e),this}setAxisAngleFromRotationMatrix(t){let e,n,s,r,c=t.elements,l=c[0],h=c[4],d=c[8],u=c[1],f=c[5],g=c[9],x=c[2],p=c[6],m=c[10];if(Math.abs(h-u)<.01&&Math.abs(d-x)<.01&&Math.abs(g-p)<.01){if(Math.abs(h+u)<.1&&Math.abs(d+x)<.1&&Math.abs(g+p)<.1&&Math.abs(l+f+m-3)<.1)return this.set(1,0,0,0),this;e=Math.PI;let E=(l+1)/2,v=(f+1)/2,b=(m+1)/2,M=(h+u)/4,A=(d+x)/4,_=(g+p)/4;return E>v&&E>b?E<.01?(n=0,s=.707106781,r=.707106781):(n=Math.sqrt(E),s=M/n,r=A/n):v>b?v<.01?(n=.707106781,s=0,r=.707106781):(s=Math.sqrt(v),n=M/s,r=_/s):b<.01?(n=.707106781,s=.707106781,r=0):(r=Math.sqrt(b),n=A/r,s=_/r),this.set(n,s,r,e),this}let S=Math.sqrt((p-g)*(p-g)+(d-x)*(d-x)+(u-h)*(u-h));return Math.abs(S)<.001&&(S=1),this.x=(p-g)/S,this.y=(d-x)/S,this.z=(u-h)/S,this.w=Math.acos((l+f+m-1)/2),this}setFromMatrixPosition(t){let e=t.elements;return this.x=e[12],this.y=e[13],this.z=e[14],this.w=e[15],this}min(t){return this.x=Math.min(this.x,t.x),this.y=Math.min(this.y,t.y),this.z=Math.min(this.z,t.z),this.w=Math.min(this.w,t.w),this}max(t){return this.x=Math.max(this.x,t.x),this.y=Math.max(this.y,t.y),this.z=Math.max(this.z,t.z),this.w=Math.max(this.w,t.w),this}clamp(t,e){return this.x=ae(this.x,t.x,e.x),this.y=ae(this.y,t.y,e.y),this.z=ae(this.z,t.z,e.z),this.w=ae(this.w,t.w,e.w),this}clampScalar(t,e){return this.x=ae(this.x,t,e),this.y=ae(this.y,t,e),this.z=ae(this.z,t,e),this.w=ae(this.w,t,e),this}clampLength(t,e){let n=this.length();return this.divideScalar(n||1).multiplyScalar(ae(n,t,e))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(t){return this.x*t.x+this.y*t.y+this.z*t.z+this.w*t.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(t){return this.normalize().multiplyScalar(t)}lerp(t,e){return this.x+=(t.x-this.x)*e,this.y+=(t.y-this.y)*e,this.z+=(t.z-this.z)*e,this.w+=(t.w-this.w)*e,this}lerpVectors(t,e,n){return this.x=t.x+(e.x-t.x)*n,this.y=t.y+(e.y-t.y)*n,this.z=t.z+(e.z-t.z)*n,this.w=t.w+(e.w-t.w)*n,this}equals(t){return t.x===this.x&&t.y===this.y&&t.z===this.z&&t.w===this.w}fromArray(t,e=0){return this.x=t[e],this.y=t[e+1],this.z=t[e+2],this.w=t[e+3],this}toArray(t=[],e=0){return t[e]=this.x,t[e+1]=this.y,t[e+2]=this.z,t[e+3]=this.w,t}fromBufferAttribute(t,e){return this.x=t.getX(e),this.y=t.getY(e),this.z=t.getZ(e),this.w=t.getW(e),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};lh.prototype.isVector4=!0;var xe=lh,go=class extends fi{constructor(t=1,e=1,n={}){super(),n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:$e,depthBuffer:!0,stencilBuffer:!1,resolveColorBuffer:!0,resolveDepthBuffer:!0,resolveStencilBuffer:!0,storeMultisampledColorBuffer:!0,storeMultisampledDepthBuffer:!0,storeMultisampledStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1,useArrayDepthTexture:!1},n),this.isRenderTarget=!0,this.width=t,this.height=e,this.depth=n.depth,this.scissor=new xe(0,0,t,e),this.scissorTest=!1,this.viewport=new xe(0,0,t,e),this.textures=[];let s={width:t,height:e,depth:n.depth},r=new Mn(s),a=n.count;for(let o=0;o<a;o++)this.textures[o]=r.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveColorBuffer=n.resolveColorBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this.storeMultisampledColorBuffer=n.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=n.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=n.storeMultisampledStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview,this.useArrayDepthTexture=n.useArrayDepthTexture}_setTextureOptions(t={}){let e={minFilter:$e,generateMipmaps:!1,flipY:!1,internalFormat:null};t.mapping!==void 0&&(e.mapping=t.mapping),t.wrapS!==void 0&&(e.wrapS=t.wrapS),t.wrapT!==void 0&&(e.wrapT=t.wrapT),t.wrapR!==void 0&&(e.wrapR=t.wrapR),t.magFilter!==void 0&&(e.magFilter=t.magFilter),t.minFilter!==void 0&&(e.minFilter=t.minFilter),t.format!==void 0&&(e.format=t.format),t.type!==void 0&&(e.type=t.type),t.anisotropy!==void 0&&(e.anisotropy=t.anisotropy),t.colorSpace!==void 0&&(e.colorSpace=t.colorSpace),t.flipY!==void 0&&(e.flipY=t.flipY),t.generateMipmaps!==void 0&&(e.generateMipmaps=t.generateMipmaps),t.internalFormat!==void 0&&(e.internalFormat=t.internalFormat);for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(e)}get texture(){return this.textures[0]}set texture(t){this.textures[0]=t}set depthTexture(t){this._depthTexture!==null&&this._depthTexture.renderTarget===this&&(this._depthTexture.renderTarget=null),t!==null&&t.renderTarget===null&&(t.renderTarget=this),this._depthTexture=t}get depthTexture(){return this._depthTexture}setSize(t,e,n=1){if(this.width!==t||this.height!==e||this.depth!==n){this.width=t,this.height=e,this.depth=n;for(let s=0,r=this.textures.length;s<r;s++)this.textures[s].image.width=t,this.textures[s].image.height=e,this.textures[s].image.depth=n,this.textures[s].isData3DTexture!==!0&&(this.textures[s].isArrayTexture=this.textures[s].image.depth>1);this.dispose()}this.viewport.set(0,0,t,e),this.scissor.set(0,0,t,e)}clone(){return new this.constructor().copy(this)}copy(t){this.width=t.width,this.height=t.height,this.depth=t.depth,this.scissor.copy(t.scissor),this.scissorTest=t.scissorTest,this.viewport.copy(t.viewport),this.textures.length=0;for(let e=0,n=t.textures.length;e<n;e++){this.textures[e]=t.textures[e].clone(),this.textures[e].isRenderTargetTexture=!0,this.textures[e].renderTarget=this;let s=Object.assign({},t.textures[e].image);this.textures[e].source=new Ks(s)}if(this.depthBuffer=t.depthBuffer,this.stencilBuffer=t.stencilBuffer,this.resolveColorBuffer=t.resolveColorBuffer,this.resolveDepthBuffer=t.resolveDepthBuffer,this.resolveStencilBuffer=t.resolveStencilBuffer,this.storeMultisampledColorBuffer=t.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=t.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=t.storeMultisampledStencilBuffer,t.depthTexture!==null)if(t.depthTexture.renderTarget===t){let e=t.depthTexture.clone();e.renderTarget=null,this.depthTexture=e}else this.depthTexture=t.depthTexture;return this.samples=t.samples,this.multiview=t.multiview,this.useArrayDepthTexture=t.useArrayDepthTexture,this}dispose(){this.dispatchEvent({type:"dispose"})}},An=class extends go{constructor(t=1,e=1,n={}){super(t,e,n),this.isWebGLRenderTarget=!0}},Br=class extends Mn{constructor(t=null,e=1,n=1,s=1){super(null),this.isDataArrayTexture=!0,this.image={data:t,width:e,height:n,depth:s},this.magFilter=en,this.minFilter=en,this.wrapR=Hn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}copy(t){return super.copy(t),this.wrapR=t.wrapR,this}addLayerUpdate(t){this.layerUpdates.add(t)}clearLayerUpdates(){this.layerUpdates.clear()}};var vo=class extends Mn{constructor(t=null,e=1,n=1,s=1){super(null),this.isData3DTexture=!0,this.image={data:t,width:e,height:n,depth:s},this.magFilter=en,this.minFilter=en,this.wrapR=Hn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}copy(t){return super.copy(t),this.wrapR=t.wrapR,this}};var Vo=class Vo{constructor(t,e,n,s,r,a,o,c,l,h,d,u,f,g,x,p){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],t!==void 0&&this.set(t,e,n,s,r,a,o,c,l,h,d,u,f,g,x,p)}set(t,e,n,s,r,a,o,c,l,h,d,u,f,g,x,p){let m=this.elements;return m[0]=t,m[4]=e,m[8]=n,m[12]=s,m[1]=r,m[5]=a,m[9]=o,m[13]=c,m[2]=l,m[6]=h,m[10]=d,m[14]=u,m[3]=f,m[7]=g,m[11]=x,m[15]=p,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new Vo().fromArray(this.elements)}copy(t){let e=this.elements,n=t.elements;return e[0]=n[0],e[1]=n[1],e[2]=n[2],e[3]=n[3],e[4]=n[4],e[5]=n[5],e[6]=n[6],e[7]=n[7],e[8]=n[8],e[9]=n[9],e[10]=n[10],e[11]=n[11],e[12]=n[12],e[13]=n[13],e[14]=n[14],e[15]=n[15],this}copyPosition(t){let e=this.elements,n=t.elements;return e[12]=n[12],e[13]=n[13],e[14]=n[14],this}setFromMatrix3(t){let e=t.elements;return this.set(e[0],e[3],e[6],0,e[1],e[4],e[7],0,e[2],e[5],e[8],0,0,0,0,1),this}extractBasis(t,e,n){return this.determinantAffine()===0?(t.set(1,0,0),e.set(0,1,0),n.set(0,0,1),this):(t.setFromMatrixColumn(this,0),e.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this)}makeBasis(t,e,n){return this.set(t.x,e.x,n.x,0,t.y,e.y,n.y,0,t.z,e.z,n.z,0,0,0,0,1),this}extractRotation(t){if(t.determinantAffine()===0)return this.identity();let e=this.elements,n=t.elements,s=1/Is.setFromMatrixColumn(t,0).length(),r=1/Is.setFromMatrixColumn(t,1).length(),a=1/Is.setFromMatrixColumn(t,2).length();return e[0]=n[0]*s,e[1]=n[1]*s,e[2]=n[2]*s,e[3]=0,e[4]=n[4]*r,e[5]=n[5]*r,e[6]=n[6]*r,e[7]=0,e[8]=n[8]*a,e[9]=n[9]*a,e[10]=n[10]*a,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,this}makeRotationFromEuler(t){let e=this.elements,n=t.x,s=t.y,r=t.z,a=Math.cos(n),o=Math.sin(n),c=Math.cos(s),l=Math.sin(s),h=Math.cos(r),d=Math.sin(r);if(t.order==="XYZ"){let u=a*h,f=a*d,g=o*h,x=o*d;e[0]=c*h,e[4]=-c*d,e[8]=l,e[1]=f+g*l,e[5]=u-x*l,e[9]=-o*c,e[2]=x-u*l,e[6]=g+f*l,e[10]=a*c}else if(t.order==="YXZ"){let u=c*h,f=c*d,g=l*h,x=l*d;e[0]=u+x*o,e[4]=g*o-f,e[8]=a*l,e[1]=a*d,e[5]=a*h,e[9]=-o,e[2]=f*o-g,e[6]=x+u*o,e[10]=a*c}else if(t.order==="ZXY"){let u=c*h,f=c*d,g=l*h,x=l*d;e[0]=u-x*o,e[4]=-a*d,e[8]=g+f*o,e[1]=f+g*o,e[5]=a*h,e[9]=x-u*o,e[2]=-a*l,e[6]=o,e[10]=a*c}else if(t.order==="ZYX"){let u=a*h,f=a*d,g=o*h,x=o*d;e[0]=c*h,e[4]=g*l-f,e[8]=u*l+x,e[1]=c*d,e[5]=x*l+u,e[9]=f*l-g,e[2]=-l,e[6]=o*c,e[10]=a*c}else if(t.order==="YZX"){let u=a*c,f=a*l,g=o*c,x=o*l;e[0]=c*h,e[4]=x-u*d,e[8]=g*d+f,e[1]=d,e[5]=a*h,e[9]=-o*h,e[2]=-l*h,e[6]=f*d+g,e[10]=u-x*d}else if(t.order==="XZY"){let u=a*c,f=a*l,g=o*c,x=o*l;e[0]=c*h,e[4]=-d,e[8]=l*h,e[1]=u*d+x,e[5]=a*h,e[9]=f*d-g,e[2]=g*d-f,e[6]=o*h,e[10]=x*d+u}return e[3]=0,e[7]=0,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,this}makeRotationFromQuaternion(t){return this.compose(Gf,t,Wf)}lookAt(t,e,n){let s=this.elements;return Ln.subVectors(t,e),Ln.lengthSq()===0&&(Ln.z=1),Ln.normalize(),Vi.crossVectors(n,Ln),Vi.lengthSq()===0&&(Math.abs(n.z)===1?Ln.x+=1e-4:Ln.z+=1e-4,Ln.normalize(),Vi.crossVectors(n,Ln)),Vi.normalize(),La.crossVectors(Ln,Vi),s[0]=Vi.x,s[4]=La.x,s[8]=Ln.x,s[1]=Vi.y,s[5]=La.y,s[9]=Ln.y,s[2]=Vi.z,s[6]=La.z,s[10]=Ln.z,this}multiply(t){return this.multiplyMatrices(this,t)}premultiply(t){return this.multiplyMatrices(t,this)}multiplyMatrices(t,e){let n=t.elements,s=e.elements,r=this.elements,a=n[0],o=n[4],c=n[8],l=n[12],h=n[1],d=n[5],u=n[9],f=n[13],g=n[2],x=n[6],p=n[10],m=n[14],S=n[3],E=n[7],v=n[11],b=n[15],M=s[0],A=s[4],_=s[8],T=s[12],I=s[1],L=s[5],N=s[9],B=s[13],D=s[2],O=s[6],$=s[10],J=s[14],W=s[3],G=s[7],K=s[11],nt=s[15];return r[0]=a*M+o*I+c*D+l*W,r[4]=a*A+o*L+c*O+l*G,r[8]=a*_+o*N+c*$+l*K,r[12]=a*T+o*B+c*J+l*nt,r[1]=h*M+d*I+u*D+f*W,r[5]=h*A+d*L+u*O+f*G,r[9]=h*_+d*N+u*$+f*K,r[13]=h*T+d*B+u*J+f*nt,r[2]=g*M+x*I+p*D+m*W,r[6]=g*A+x*L+p*O+m*G,r[10]=g*_+x*N+p*$+m*K,r[14]=g*T+x*B+p*J+m*nt,r[3]=S*M+E*I+v*D+b*W,r[7]=S*A+E*L+v*O+b*G,r[11]=S*_+E*N+v*$+b*K,r[15]=S*T+E*B+v*J+b*nt,this}multiplyScalar(t){let e=this.elements;return e[0]*=t,e[4]*=t,e[8]*=t,e[12]*=t,e[1]*=t,e[5]*=t,e[9]*=t,e[13]*=t,e[2]*=t,e[6]*=t,e[10]*=t,e[14]*=t,e[3]*=t,e[7]*=t,e[11]*=t,e[15]*=t,this}determinant(){let t=this.elements,e=t[0],n=t[4],s=t[8],r=t[12],a=t[1],o=t[5],c=t[9],l=t[13],h=t[2],d=t[6],u=t[10],f=t[14],g=t[3],x=t[7],p=t[11],m=t[15],S=c*f-l*u,E=o*f-l*d,v=o*u-c*d,b=a*f-l*h,M=a*u-c*h,A=a*d-o*h;return e*(x*S-p*E+m*v)-n*(g*S-p*b+m*M)+s*(g*E-x*b+m*A)-r*(g*v-x*M+p*A)}determinantAffine(){let t=this.elements,e=t[0],n=t[4],s=t[8],r=t[1],a=t[5],o=t[9],c=t[2],l=t[6],h=t[10];return e*(a*h-o*l)-n*(r*h-o*c)+s*(r*l-a*c)}transpose(){let t=this.elements,e;return e=t[1],t[1]=t[4],t[4]=e,e=t[2],t[2]=t[8],t[8]=e,e=t[6],t[6]=t[9],t[9]=e,e=t[3],t[3]=t[12],t[12]=e,e=t[7],t[7]=t[13],t[13]=e,e=t[11],t[11]=t[14],t[14]=e,this}setPosition(t,e,n){let s=this.elements;return t.isVector3?(s[12]=t.x,s[13]=t.y,s[14]=t.z):(s[12]=t,s[13]=e,s[14]=n),this}invert(){let t=this.elements,e=t[0],n=t[1],s=t[2],r=t[3],a=t[4],o=t[5],c=t[6],l=t[7],h=t[8],d=t[9],u=t[10],f=t[11],g=t[12],x=t[13],p=t[14],m=t[15],S=e*o-n*a,E=e*c-s*a,v=e*l-r*a,b=n*c-s*o,M=n*l-r*o,A=s*l-r*c,_=h*x-d*g,T=h*p-u*g,I=h*m-f*g,L=d*p-u*x,N=d*m-f*x,B=u*m-f*p,D=S*B-E*N+v*L+b*I-M*T+A*_;if(D===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let O=1/D;return t[0]=(o*B-c*N+l*L)*O,t[1]=(s*N-n*B-r*L)*O,t[2]=(x*A-p*M+m*b)*O,t[3]=(u*M-d*A-f*b)*O,t[4]=(c*I-a*B-l*T)*O,t[5]=(e*B-s*I+r*T)*O,t[6]=(p*v-g*A-m*E)*O,t[7]=(h*A-u*v+f*E)*O,t[8]=(a*N-o*I+l*_)*O,t[9]=(n*I-e*N-r*_)*O,t[10]=(g*M-x*v+m*S)*O,t[11]=(d*v-h*M-f*S)*O,t[12]=(o*T-a*L-c*_)*O,t[13]=(e*L-n*T+s*_)*O,t[14]=(x*E-g*b-p*S)*O,t[15]=(h*b-d*E+u*S)*O,this}scale(t){let e=this.elements,n=t.x,s=t.y,r=t.z;return e[0]*=n,e[4]*=s,e[8]*=r,e[1]*=n,e[5]*=s,e[9]*=r,e[2]*=n,e[6]*=s,e[10]*=r,e[3]*=n,e[7]*=s,e[11]*=r,this}getMaxScaleOnAxis(){let t=this.elements,e=t[0]*t[0]+t[1]*t[1]+t[2]*t[2],n=t[4]*t[4]+t[5]*t[5]+t[6]*t[6],s=t[8]*t[8]+t[9]*t[9]+t[10]*t[10];return Math.sqrt(Math.max(e,n,s))}makeTranslation(t,e,n){return t.isVector3?this.set(1,0,0,t.x,0,1,0,t.y,0,0,1,t.z,0,0,0,1):this.set(1,0,0,t,0,1,0,e,0,0,1,n,0,0,0,1),this}makeRotationX(t){let e=Math.cos(t),n=Math.sin(t);return this.set(1,0,0,0,0,e,-n,0,0,n,e,0,0,0,0,1),this}makeRotationY(t){let e=Math.cos(t),n=Math.sin(t);return this.set(e,0,n,0,0,1,0,0,-n,0,e,0,0,0,0,1),this}makeRotationZ(t){let e=Math.cos(t),n=Math.sin(t);return this.set(e,-n,0,0,n,e,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(t,e){let n=Math.cos(e),s=Math.sin(e),r=1-n,a=t.x,o=t.y,c=t.z,l=r*a,h=r*o;return this.set(l*a+n,l*o-s*c,l*c+s*o,0,l*o+s*c,h*o+n,h*c-s*a,0,l*c-s*o,h*c+s*a,r*c*c+n,0,0,0,0,1),this}makeScale(t,e,n){return this.set(t,0,0,0,0,e,0,0,0,0,n,0,0,0,0,1),this}makeShear(t,e,n,s,r,a){return this.set(1,n,r,0,t,1,a,0,e,s,1,0,0,0,0,1),this}compose(t,e,n){let s=this.elements,r=e._x,a=e._y,o=e._z,c=e._w,l=r+r,h=a+a,d=o+o,u=r*l,f=r*h,g=r*d,x=a*h,p=a*d,m=o*d,S=c*l,E=c*h,v=c*d,b=n.x,M=n.y,A=n.z;return s[0]=(1-(x+m))*b,s[1]=(f+v)*b,s[2]=(g-E)*b,s[3]=0,s[4]=(f-v)*M,s[5]=(1-(u+m))*M,s[6]=(p+S)*M,s[7]=0,s[8]=(g+E)*A,s[9]=(p-S)*A,s[10]=(1-(u+x))*A,s[11]=0,s[12]=t.x,s[13]=t.y,s[14]=t.z,s[15]=1,this}decompose(t,e,n){let s=this.elements;t.x=s[12],t.y=s[13],t.z=s[14];let r=this.determinantAffine();if(r===0)return n.set(1,1,1),e.identity(),this;let a=Is.set(s[0],s[1],s[2]).length(),o=Is.set(s[4],s[5],s[6]).length(),c=Is.set(s[8],s[9],s[10]).length();r<0&&(a=-a),$n.copy(this);let l=1/a,h=1/o,d=1/c;return $n.elements[0]*=l,$n.elements[1]*=l,$n.elements[2]*=l,$n.elements[4]*=h,$n.elements[5]*=h,$n.elements[6]*=h,$n.elements[8]*=d,$n.elements[9]*=d,$n.elements[10]*=d,e.setFromRotationMatrix($n),n.x=a,n.y=o,n.z=c,this}makePerspective(t,e,n,s,r,a,o=ei,c=!1){let l=this.elements,h=2*r/(e-t),d=2*r/(n-s),u=(e+t)/(e-t),f=(n+s)/(n-s),g,x;if(c)g=r/(a-r),x=a*r/(a-r);else if(o===ei)g=-(a+r)/(a-r),x=-2*a*r/(a-r);else if(o===Zs)g=-a/(a-r),x=-a*r/(a-r);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return l[0]=h,l[4]=0,l[8]=u,l[12]=0,l[1]=0,l[5]=d,l[9]=f,l[13]=0,l[2]=0,l[6]=0,l[10]=g,l[14]=x,l[3]=0,l[7]=0,l[11]=-1,l[15]=0,this}makeOrthographic(t,e,n,s,r,a,o=ei,c=!1){let l=this.elements,h=2/(e-t),d=2/(n-s),u=-(e+t)/(e-t),f=-(n+s)/(n-s),g,x;if(c)g=1/(a-r),x=a/(a-r);else if(o===ei)g=-2/(a-r),x=-(a+r)/(a-r);else if(o===Zs)g=-1/(a-r),x=-r/(a-r);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return l[0]=h,l[4]=0,l[8]=0,l[12]=u,l[1]=0,l[5]=d,l[9]=0,l[13]=f,l[2]=0,l[6]=0,l[10]=g,l[14]=x,l[3]=0,l[7]=0,l[11]=0,l[15]=1,this}equals(t){let e=this.elements,n=t.elements;for(let s=0;s<16;s++)if(e[s]!==n[s])return!1;return!0}fromArray(t,e=0){for(let n=0;n<16;n++)this.elements[n]=t[n+e];return this}toArray(t=[],e=0){let n=this.elements;return t[e]=n[0],t[e+1]=n[1],t[e+2]=n[2],t[e+3]=n[3],t[e+4]=n[4],t[e+5]=n[5],t[e+6]=n[6],t[e+7]=n[7],t[e+8]=n[8],t[e+9]=n[9],t[e+10]=n[10],t[e+11]=n[11],t[e+12]=n[12],t[e+13]=n[13],t[e+14]=n[14],t[e+15]=n[15],t}};Vo.prototype.isMatrix4=!0;var ue=Vo,Is=new P,$n=new ue,Gf=new P(0,0,0),Wf=new P(1,1,1),Vi=new P,La=new P,Ln=new P,Gh=new ue,Wh=new nn,ni=class i{constructor(t=0,e=0,n=0,s=i.DEFAULT_ORDER){this.isEuler=!0,this._x=t,this._y=e,this._z=n,this._order=s}get x(){return this._x}set x(t){this._x=t,this._onChangeCallback()}get y(){return this._y}set y(t){this._y=t,this._onChangeCallback()}get z(){return this._z}set z(t){this._z=t,this._onChangeCallback()}get order(){return this._order}set order(t){this._order=t,this._onChangeCallback()}set(t,e,n,s=this._order){return this._x=t,this._y=e,this._z=n,this._order=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(t){return this._x=t._x,this._y=t._y,this._z=t._z,this._order=t._order,this._onChangeCallback(),this}setFromRotationMatrix(t,e=this._order,n=!0){let s=t.elements,r=s[0],a=s[4],o=s[8],c=s[1],l=s[5],h=s[9],d=s[2],u=s[6],f=s[10];switch(e){case"XYZ":this._y=Math.asin(ae(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-h,f),this._z=Math.atan2(-a,r)):(this._x=Math.atan2(u,l),this._z=0);break;case"YXZ":this._x=Math.asin(-ae(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(o,f),this._z=Math.atan2(c,l)):(this._y=Math.atan2(-d,r),this._z=0);break;case"ZXY":this._x=Math.asin(ae(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(-d,f),this._z=Math.atan2(-a,l)):(this._y=0,this._z=Math.atan2(c,r));break;case"ZYX":this._y=Math.asin(-ae(d,-1,1)),Math.abs(d)<.9999999?(this._x=Math.atan2(u,f),this._z=Math.atan2(c,r)):(this._x=0,this._z=Math.atan2(-a,l));break;case"YZX":this._z=Math.asin(ae(c,-1,1)),Math.abs(c)<.9999999?(this._x=Math.atan2(-h,l),this._y=Math.atan2(-d,r)):(this._x=0,this._y=Math.atan2(o,f));break;case"XZY":this._z=Math.asin(-ae(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(u,l),this._y=Math.atan2(o,r)):(this._x=Math.atan2(-h,f),this._y=0);break;default:ee("Euler: .setFromRotationMatrix() encountered an unknown order: "+e)}return this._order=e,n===!0&&this._onChangeCallback(),this}setFromQuaternion(t,e,n){return Gh.makeRotationFromQuaternion(t),this.setFromRotationMatrix(Gh,e,n)}setFromVector3(t,e=this._order){return this.set(t.x,t.y,t.z,e)}reorder(t){return Wh.setFromEuler(this),this.setFromQuaternion(Wh,t)}equals(t){return t._x===this._x&&t._y===this._y&&t._z===this._z&&t._order===this._order}fromArray(t){return this._x=t[0],this._y=t[1],this._z=t[2],t[3]!==void 0&&(this._order=t[3]),this._onChangeCallback(),this}toArray(t=[],e=0){return t[e]=this._x,t[e+1]=this._y,t[e+2]=this._z,t[e+3]=this._order,t}_onChange(t){return this._onChangeCallback=t,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}};ni.DEFAULT_ORDER="XYZ";var kr=class{constructor(){this.mask=1}set(t){this.mask=(1<<t|0)>>>0}enable(t){this.mask|=1<<t|0}enableAll(){this.mask=-1}toggle(t){this.mask^=1<<t|0}disable(t){this.mask&=~(1<<t|0)}disableAll(){this.mask=0}test(t){return(this.mask&t.mask)!==0}isEnabled(t){return(this.mask&(1<<t|0))!==0}},Xf=0,Xh=new P,Ls=new nn,Ti=new ue,Da=new P,br=new P,qf=new P,Yf=new nn,qh=new P(1,0,0),Yh=new P(0,1,0),jh=new P(0,0,1),Zh={type:"added"},jf={type:"removed"},Ds={type:"childadded",child:null},Qc={type:"childremoved",child:null},sn=class i extends fi{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Xf++}),this.uuid=ui(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=i.DEFAULT_UP.clone();let t=new P,e=new ni,n=new nn,s=new P(1,1,1);function r(){n.setFromEuler(e,!1)}function a(){e.setFromQuaternion(n,void 0,!1)}e._onChange(r),n._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:t},rotation:{configurable:!0,enumerable:!0,value:e},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:s},modelViewMatrix:{value:new ue},normalMatrix:{value:new ce}}),this.matrix=new ue,this.matrixWorld=new ue,this.matrixAutoUpdate=i.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=i.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new kr,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(t){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(t),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(t){return this.quaternion.premultiply(t),this}setRotationFromAxisAngle(t,e){this.quaternion.setFromAxisAngle(t,e)}setRotationFromEuler(t){this.quaternion.setFromEuler(t,!0)}setRotationFromMatrix(t){this.quaternion.setFromRotationMatrix(t)}setRotationFromQuaternion(t){this.quaternion.copy(t)}rotateOnAxis(t,e){return Ls.setFromAxisAngle(t,e),this.quaternion.multiply(Ls),this}rotateOnWorldAxis(t,e){return Ls.setFromAxisAngle(t,e),this.quaternion.premultiply(Ls),this}rotateX(t){return this.rotateOnAxis(qh,t)}rotateY(t){return this.rotateOnAxis(Yh,t)}rotateZ(t){return this.rotateOnAxis(jh,t)}translateOnAxis(t,e){return Xh.copy(t).applyQuaternion(this.quaternion),this.position.add(Xh.multiplyScalar(e)),this}translateX(t){return this.translateOnAxis(qh,t)}translateY(t){return this.translateOnAxis(Yh,t)}translateZ(t){return this.translateOnAxis(jh,t)}localToWorld(t){return this.updateWorldMatrix(!0,!1),t.applyMatrix4(this.matrixWorld)}worldToLocal(t){return this.updateWorldMatrix(!0,!1),t.applyMatrix4(Ti.copy(this.matrixWorld).invert())}lookAt(t,e,n){t.isVector3?Da.copy(t):Da.set(t,e,n);let s=this.parent;this.updateWorldMatrix(!0,!1),br.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?Ti.lookAt(br,Da,this.up):Ti.lookAt(Da,br,this.up),this.quaternion.setFromRotationMatrix(Ti),s&&(Ti.extractRotation(s.matrixWorld),Ls.setFromRotationMatrix(Ti),this.quaternion.premultiply(Ls.invert()))}add(t){if(arguments.length>1){for(let e=0;e<arguments.length;e++)this.add(arguments[e]);return this}return t===this?(se("Object3D.add: object can't be added as a child of itself.",t),this):(t&&t.isObject3D?(t.removeFromParent(),t.parent=this,this.children.push(t),t.dispatchEvent(Zh),Ds.child=t,this.dispatchEvent(Ds),Ds.child=null):se("Object3D.add: object not an instance of THREE.Object3D.",t),this)}remove(t){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let e=this.children.indexOf(t);return e!==-1&&(t.parent=null,this.children.splice(e,1),t.dispatchEvent(jf),Qc.child=t,this.dispatchEvent(Qc),Qc.child=null),this}removeFromParent(){let t=this.parent;return t!==null&&t.remove(this),this}clear(){return this.remove(...this.children)}attach(t){return this.updateWorldMatrix(!0,!1),Ti.copy(this.matrixWorld).invert(),t.parent!==null&&(t.parent.updateWorldMatrix(!0,!1),Ti.multiply(t.parent.matrixWorld)),t.applyMatrix4(Ti),t.removeFromParent(),t.parent=this,this.children.push(t),t.updateWorldMatrix(!1,!0),t.dispatchEvent(Zh),Ds.child=t,this.dispatchEvent(Ds),Ds.child=null,this}getObjectById(t){return this.getObjectByProperty("id",t)}getObjectByName(t){return this.getObjectByProperty("name",t)}getObjectByProperty(t,e){if(this[t]===e)return this;for(let n=0,s=this.children.length;n<s;n++){let a=this.children[n].getObjectByProperty(t,e);if(a!==void 0)return a}}getObjectsByProperty(t,e,n=[]){this[t]===e&&n.push(this);let s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].getObjectsByProperty(t,e,n);return n}getWorldPosition(t){return this.updateWorldMatrix(!0,!1),t.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(t){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(br,t,qf),t}getWorldScale(t){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(br,Yf,t),t}getWorldDirection(t){this.updateWorldMatrix(!0,!1);let e=this.matrixWorld.elements;return t.set(e[8],e[9],e[10]).normalize()}raycast(){}intersectsFrustum(){}traverse(t){t(this);let e=this.children;for(let n=0,s=e.length;n<s;n++)e[n].traverse(t)}traverseVisible(t){if(this.visible===!1)return;t(this);let e=this.children;for(let n=0,s=e.length;n<s;n++)e[n].traverseVisible(t)}traverseAncestors(t){let e=this.parent;e!==null&&(t(e),e.traverseAncestors(t))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);let t=this.pivot;if(t!==null){let e=t.x,n=t.y,s=t.z,r=this.matrix.elements;r[12]+=e-r[0]*e-r[4]*n-r[8]*s,r[13]+=n-r[1]*e-r[5]*n-r[9]*s,r[14]+=s-r[2]*e-r[6]*n-r[10]*s}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(t){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||t)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,t=!0);let e=this.children;for(let n=0,s=e.length;n<s;n++)e[n].updateMatrixWorld(t)}updateWorldMatrix(t,e,n=!1){let s=this.parent;if(t===!0&&s!==null&&s.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||n)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,n=!0),e===!0){let r=this.children;for(let a=0,o=r.length;a<o;a++)r[a].updateWorldMatrix(!1,!0,n)}}toJSON(t){let e=t===void 0||typeof t=="string",n={};e&&(t={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});let s={};s.uuid=this.uuid,s.type=this.type,s.name=this.name,s.castShadow=this.castShadow,s.receiveShadow=this.receiveShadow,s.visible=this.visible,s.frustumCulled=this.frustumCulled,s.renderOrder=this.renderOrder,s.static=this.static,s.matrixAutoUpdate=this.matrixAutoUpdate,Object.keys(this.userData).length>0&&(s.userData=this.userData),s.layers=this.layers.mask,s.matrix=this.matrix.toArray(),s.up=this.up.toArray(),this.pivot!==null&&(s.pivot=this.pivot.toArray()),this.morphTargetDictionary!==void 0&&(s.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(s.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(s.type="InstancedMesh",s.count=this.count,s.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(s.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(s.type="BatchedMesh",s.perObjectFrustumCulled=this.perObjectFrustumCulled,s.sortObjects=this.sortObjects,s.drawRanges=this._drawRanges,s.reservedRanges=this._reservedRanges,s.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),s.instanceInfo=this._instanceInfo.map(o=>({...o})),s.availableInstanceIds=this._availableInstanceIds.slice(),s.availableGeometryIds=this._availableGeometryIds.slice(),s.nextIndexStart=this._nextIndexStart,s.nextVertexStart=this._nextVertexStart,s.geometryCount=this._geometryCount,s.maxInstanceCount=this._maxInstanceCount,s.maxVertexCount=this._maxVertexCount,s.maxIndexCount=this._maxIndexCount,s.geometryInitialized=this._geometryInitialized,s.matricesTexture=this._matricesTexture.toJSON(t),s.indirectTexture=this._indirectTexture.toJSON(t),this._colorsTexture!==null&&(s.colorsTexture=this._colorsTexture.toJSON(t)),this.boundingSphere!==null&&(s.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(s.boundingBox=this.boundingBox.toJSON()));function r(o,c){return o[c.uuid]===void 0&&(o[c.uuid]=c.toJSON(t)),c.uuid}if(this.isScene)this.background&&(this.background.isColor?s.background=this.background.toJSON():this.background.isTexture&&(s.background=this.background.toJSON(t).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(s.environment=this.environment.toJSON(t).uuid);else if(this.isMesh||this.isLine||this.isPoints){s.geometry=r(t.geometries,this.geometry);let o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){let c=o.shapes;if(Array.isArray(c))for(let l=0,h=c.length;l<h;l++){let d=c[l];r(t.shapes,d)}else r(t.shapes,c)}}if(this.isSkinnedMesh&&(s.bindMode=this.bindMode,s.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(r(t.skeletons,this.skeleton),s.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){let o=[];for(let c=0,l=this.material.length;c<l;c++)o.push(r(t.materials,this.material[c]));s.material=o}else s.material=r(t.materials,this.material);if(this.children.length>0){s.children=[];for(let o=0;o<this.children.length;o++)s.children.push(this.children[o].toJSON(t).object)}if(this.animations.length>0){s.animations=[];for(let o=0;o<this.animations.length;o++){let c=this.animations[o];s.animations.push(r(t.animations,c))}}if(e){let o=a(t.geometries),c=a(t.materials),l=a(t.textures),h=a(t.images),d=a(t.shapes),u=a(t.skeletons),f=a(t.animations),g=a(t.nodes);o.length>0&&(n.geometries=o),c.length>0&&(n.materials=c),l.length>0&&(n.textures=l),h.length>0&&(n.images=h),d.length>0&&(n.shapes=d),u.length>0&&(n.skeletons=u),f.length>0&&(n.animations=f),g.length>0&&(n.nodes=g)}return n.object=s,n;function a(o){let c=[];for(let l in o){let h=o[l];delete h.metadata,c.push(h)}return c}}clone(t){return new this.constructor().copy(this,t)}copy(t,e=!0){if(this.name=t.name,this.up.copy(t.up),this.position.copy(t.position),this.rotation.order=t.rotation.order,this.quaternion.copy(t.quaternion),this.scale.copy(t.scale),this.pivot=t.pivot!==null?t.pivot.clone():null,this.matrix.copy(t.matrix),this.matrixWorld.copy(t.matrixWorld),this.matrixAutoUpdate=t.matrixAutoUpdate,this.matrixWorldAutoUpdate=t.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=t.matrixWorldNeedsUpdate,this.layers.mask=t.layers.mask,this.visible=t.visible,this.castShadow=t.castShadow,this.receiveShadow=t.receiveShadow,this.frustumCulled=t.frustumCulled,this.renderOrder=t.renderOrder,this.static=t.static,this.animations=t.animations.slice(),this.userData=JSON.parse(JSON.stringify(t.userData)),e===!0)for(let n=0;n<t.children.length;n++){let s=t.children[n];this.add(s.clone())}return this}dispose(){this.dispatchEvent({type:"dispose"})}};sn.DEFAULT_UP=new P(0,1,0);sn.DEFAULT_MATRIX_AUTO_UPDATE=!0;sn.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var oe=class extends sn{constructor(){super(),this.isGroup=!0,this.type="Group"}},Zf={type:"move"},Qs=class{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new oe,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new oe,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new P,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new P),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new oe,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new P,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new P,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(t){return this._targetRay!==null&&this._targetRay.dispatchEvent(t),this._grip!==null&&this._grip.dispatchEvent(t),this._hand!==null&&this._hand.dispatchEvent(t),this}connect(t){if(t&&t.hand){let e=this._hand;if(e)for(let n of t.hand.values())this._getHandJoint(e,n)}return this.dispatchEvent({type:"connected",data:t}),this}disconnect(t){return this.dispatchEvent({type:"disconnected",data:t}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(t,e,n){let s=null,r=null,a=null,o=this._targetRay,c=this._grip,l=this._hand;if(t&&e.session.visibilityState!=="visible-blurred"){if(l&&t.hand){a=!0;for(let x of t.hand.values()){let p=e.getJointPose(x,n),m=this._getHandJoint(l,x);p!==null&&(m.matrix.fromArray(p.transform.matrix),m.matrix.decompose(m.position,m.rotation,m.scale),m.matrixWorldNeedsUpdate=!0,m.jointRadius=p.radius),m.visible=p!==null}let h=l.joints["index-finger-tip"],d=l.joints["thumb-tip"],u=h.position.distanceTo(d.position),f=.02,g=.005;l.inputState.pinching&&u>f+g?(l.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:t.handedness,target:this})):!l.inputState.pinching&&u<=f-g&&(l.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:t.handedness,target:this}))}else c!==null&&t.gripSpace&&(r=e.getPose(t.gripSpace,n),r!==null&&(c.matrix.fromArray(r.transform.matrix),c.matrix.decompose(c.position,c.rotation,c.scale),c.matrixWorldNeedsUpdate=!0,r.linearVelocity?(c.hasLinearVelocity=!0,c.linearVelocity.copy(r.linearVelocity)):c.hasLinearVelocity=!1,r.angularVelocity?(c.hasAngularVelocity=!0,c.angularVelocity.copy(r.angularVelocity)):c.hasAngularVelocity=!1,c.eventsEnabled&&c.dispatchEvent({type:"gripUpdated",data:t,target:this})));o!==null&&(s=e.getPose(t.targetRaySpace,n),s===null&&r!==null&&(s=r),s!==null&&(o.matrix.fromArray(s.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,s.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(s.linearVelocity)):o.hasLinearVelocity=!1,s.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(s.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(Zf)))}return o!==null&&(o.visible=s!==null),c!==null&&(c.visible=r!==null),l!==null&&(l.visible=a!==null),this}_getHandJoint(t,e){if(t.joints[e.jointName]===void 0){let n=new oe;n.matrixAutoUpdate=!1,n.visible=!1,t.joints[e.jointName]=n,t.add(n)}return t.joints[e.jointName]}},ed={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},Gi={h:0,s:0,l:0},Ua={h:0,s:0,l:0};function tl(i,t,e){return e<0&&(e+=1),e>1&&(e-=1),e<1/6?i+(t-i)*6*e:e<1/2?t:e<2/3?i+(t-i)*6*(2/3-e):i}var Ot=class{constructor(t,e,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(t,e,n)}set(t,e,n){if(e===void 0&&n===void 0){let s=t;s&&s.isColor?this.copy(s):typeof s=="number"?this.setHex(s):typeof s=="string"&&this.setStyle(s)}else this.setRGB(t,e,n);return this}setScalar(t){return this.r=t,this.g=t,this.b=t,this}setHex(t,e=yn){return t=Math.floor(t),this.r=(t>>16&255)/255,this.g=(t>>8&255)/255,this.b=(t&255)/255,Se.colorSpaceToWorking(this,e),this}setRGB(t,e,n,s=Se.workingColorSpace){return this.r=t,this.g=e,this.b=n,Se.colorSpaceToWorking(this,s),this}setHSL(t,e,n,s=Se.workingColorSpace){if(t=th(t,1),e=ae(e,0,1),n=ae(n,0,1),e===0)this.r=this.g=this.b=n;else{let r=n<=.5?n*(1+e):n+e-n*e,a=2*n-r;this.r=tl(a,r,t+1/3),this.g=tl(a,r,t),this.b=tl(a,r,t-1/3)}return Se.colorSpaceToWorking(this,s),this}setStyle(t,e=yn){function n(r){r!==void 0&&parseFloat(r)<1&&ee("Color: Alpha component of "+t+" will be ignored.")}let s;if(s=/^(\w+)\(([^\)]*)\)/.exec(t)){let r,a=s[1],o=s[2];switch(a){case"rgb":case"rgba":if(r=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(255,parseInt(r[1],10))/255,Math.min(255,parseInt(r[2],10))/255,Math.min(255,parseInt(r[3],10))/255,e);if(r=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(100,parseInt(r[1],10))/100,Math.min(100,parseInt(r[2],10))/100,Math.min(100,parseInt(r[3],10))/100,e);break;case"hsl":case"hsla":if(r=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setHSL(parseFloat(r[1])/360,parseFloat(r[2])/100,parseFloat(r[3])/100,e);break;default:ee("Color: Unknown color model "+t)}}else if(s=/^\#([A-Fa-f\d]+)$/.exec(t)){let r=s[1],a=r.length;if(a===3)return this.setRGB(parseInt(r.charAt(0),16)/15,parseInt(r.charAt(1),16)/15,parseInt(r.charAt(2),16)/15,e);if(a===6)return this.setHex(parseInt(r,16),e);ee("Color: Invalid hex color "+t)}else if(t&&t.length>0)return this.setColorName(t,e);return this}setColorName(t,e=yn){let n=ed[t.toLowerCase()];return n!==void 0?this.setHex(n,e):ee("Color: Unknown color "+t),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(t){return this.r=t.r,this.g=t.g,this.b=t.b,this}copySRGBToLinear(t){return this.r=Li(t.r),this.g=Li(t.g),this.b=Li(t.b),this}copyLinearToSRGB(t){return this.r=qs(t.r),this.g=qs(t.g),this.b=qs(t.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(t=yn){return Se.workingToColorSpace(dn.copy(this),t),Math.round(ae(dn.r*255,0,255))*65536+Math.round(ae(dn.g*255,0,255))*256+Math.round(ae(dn.b*255,0,255))}getHexString(t=yn){return("000000"+this.getHex(t).toString(16)).slice(-6)}getHSL(t,e=Se.workingColorSpace){Se.workingToColorSpace(dn.copy(this),e);let n=dn.r,s=dn.g,r=dn.b,a=Math.max(n,s,r),o=Math.min(n,s,r),c,l,h=(o+a)/2;if(o===a)c=0,l=0;else{let d=a-o;switch(l=h<=.5?d/(a+o):d/(2-a-o),a){case n:c=(s-r)/d+(s<r?6:0);break;case s:c=(r-n)/d+2;break;case r:c=(n-s)/d+4;break}c/=6}return t.h=c,t.s=l,t.l=h,t}getRGB(t,e=Se.workingColorSpace){return Se.workingToColorSpace(dn.copy(this),e),t.r=dn.r,t.g=dn.g,t.b=dn.b,t}getStyle(t=yn){Se.workingToColorSpace(dn.copy(this),t);let e=dn.r,n=dn.g,s=dn.b;return t!==yn?`color(${t} ${e.toFixed(3)} ${n.toFixed(3)} ${s.toFixed(3)})`:`rgb(${Math.round(e*255)},${Math.round(n*255)},${Math.round(s*255)})`}offsetHSL(t,e,n){return this.getHSL(Gi),this.setHSL(Gi.h+t,Gi.s+e,Gi.l+n)}add(t){return this.r+=t.r,this.g+=t.g,this.b+=t.b,this}addColors(t,e){return this.r=t.r+e.r,this.g=t.g+e.g,this.b=t.b+e.b,this}addScalar(t){return this.r+=t,this.g+=t,this.b+=t,this}sub(t){return this.r=Math.max(0,this.r-t.r),this.g=Math.max(0,this.g-t.g),this.b=Math.max(0,this.b-t.b),this}multiply(t){return this.r*=t.r,this.g*=t.g,this.b*=t.b,this}multiplyScalar(t){return this.r*=t,this.g*=t,this.b*=t,this}lerp(t,e){return this.r+=(t.r-this.r)*e,this.g+=(t.g-this.g)*e,this.b+=(t.b-this.b)*e,this}lerpColors(t,e,n){return this.r=t.r+(e.r-t.r)*n,this.g=t.g+(e.g-t.g)*n,this.b=t.b+(e.b-t.b)*n,this}lerpHSL(t,e){this.getHSL(Gi),t.getHSL(Ua);let n=Ir(Gi.h,Ua.h,e),s=Ir(Gi.s,Ua.s,e),r=Ir(Gi.l,Ua.l,e);return this.setHSL(n,s,r),this}setFromVector3(t){return this.r=t.x,this.g=t.y,this.b=t.z,this}applyMatrix3(t){let e=this.r,n=this.g,s=this.b,r=t.elements;return this.r=r[0]*e+r[3]*n+r[6]*s,this.g=r[1]*e+r[4]*n+r[7]*s,this.b=r[2]*e+r[5]*n+r[8]*s,this}equals(t){return t.r===this.r&&t.g===this.g&&t.b===this.b}fromArray(t,e=0){return this.r=t[e],this.g=t[e+1],this.b=t[e+2],this}toArray(t=[],e=0){return t[e]=this.r,t[e+1]=this.g,t[e+2]=this.b,t}fromBufferAttribute(t,e){return this.r=t.getX(e),this.g=t.getY(e),this.b=t.getZ(e),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}},dn=new Ot;Ot.NAMES=ed;var Hr=class i{constructor(t,e=1,n=1e3){this.isFog=!0,this.name="",this.color=new Ot(t),this.near=e,this.far=n}clone(){return new i(this.color,this.near,this.far)}toJSON(){return{type:"Fog",name:this.name,color:this.color.getHex(),near:this.near,far:this.far}}},Di=class extends sn{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new ni,this.environmentIntensity=1,this.environmentRotation=new ni,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(t,e){return super.copy(t,e),t.background!==null&&(this.background=t.background.clone()),t.environment!==null&&(this.environment=t.environment.clone()),t.fog!==null&&(this.fog=t.fog.clone()),this.backgroundBlurriness=t.backgroundBlurriness,this.backgroundIntensity=t.backgroundIntensity,this.backgroundRotation.copy(t.backgroundRotation),this.environmentIntensity=t.environmentIntensity,this.environmentRotation.copy(t.environmentRotation),t.overrideMaterial!==null&&(this.overrideMaterial=t.overrideMaterial.clone()),this.matrixAutoUpdate=t.matrixAutoUpdate,this}toJSON(t){let e=super.toJSON(t);return this.fog!==null&&(e.object.fog=this.fog.toJSON()),e.object.backgroundBlurriness=this.backgroundBlurriness,e.object.backgroundIntensity=this.backgroundIntensity,e.object.backgroundRotation=this.backgroundRotation.toArray(),e.object.environmentIntensity=this.environmentIntensity,e.object.environmentRotation=this.environmentRotation.toArray(),e}},Jn=new P,Ai=new P,el=new P,Ri=new P,Us=new P,Ns=new P,$h=new P,nl=new P,il=new P,sl=new P,rl=new xe,al=new xe,ol=new xe,Yi=class i{constructor(t=new P,e=new P,n=new P){this.a=t,this.b=e,this.c=n}static getNormal(t,e,n,s){s.subVectors(n,e),Jn.subVectors(t,e),s.cross(Jn);let r=s.lengthSq();return r>0?s.multiplyScalar(1/Math.sqrt(r)):s.set(0,0,0)}static getBarycoord(t,e,n,s,r){Jn.subVectors(s,e),Ai.subVectors(n,e),el.subVectors(t,e);let a=Jn.dot(Jn),o=Jn.dot(Ai),c=Jn.dot(el),l=Ai.dot(Ai),h=Ai.dot(el),d=a*l-o*o;if(d===0)return r.set(0,0,0),null;let u=1/d,f=(l*c-o*h)*u,g=(a*h-o*c)*u;return r.set(1-f-g,g,f)}static containsPoint(t,e,n,s){return this.getBarycoord(t,e,n,s,Ri)===null?!1:Ri.x>=0&&Ri.y>=0&&Ri.x+Ri.y<=1}static getInterpolation(t,e,n,s,r,a,o,c){return this.getBarycoord(t,e,n,s,Ri)===null?(c.x=0,c.y=0,"z"in c&&(c.z=0),"w"in c&&(c.w=0),null):(c.setScalar(0),c.addScaledVector(r,Ri.x),c.addScaledVector(a,Ri.y),c.addScaledVector(o,Ri.z),c)}static getInterpolatedAttribute(t,e,n,s,r,a){return rl.setScalar(0),al.setScalar(0),ol.setScalar(0),rl.fromBufferAttribute(t,e),al.fromBufferAttribute(t,n),ol.fromBufferAttribute(t,s),a.setScalar(0),a.addScaledVector(rl,r.x),a.addScaledVector(al,r.y),a.addScaledVector(ol,r.z),a}static isFrontFacing(t,e,n,s){return Jn.subVectors(n,e),Ai.subVectors(t,e),Jn.cross(Ai).dot(s)<0}set(t,e,n){return this.a.copy(t),this.b.copy(e),this.c.copy(n),this}setFromPointsAndIndices(t,e,n,s){return this.a.copy(t[e]),this.b.copy(t[n]),this.c.copy(t[s]),this}setFromAttributeAndIndices(t,e,n,s){return this.a.fromBufferAttribute(t,e),this.b.fromBufferAttribute(t,n),this.c.fromBufferAttribute(t,s),this}clone(){return new this.constructor().copy(this)}copy(t){return this.a.copy(t.a),this.b.copy(t.b),this.c.copy(t.c),this}getArea(){return Jn.subVectors(this.c,this.b),Ai.subVectors(this.a,this.b),Jn.cross(Ai).length()*.5}getMidpoint(t){return t.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(t){return i.getNormal(this.a,this.b,this.c,t)}getPlane(t){return t.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(t,e){return i.getBarycoord(t,this.a,this.b,this.c,e)}getInterpolation(t,e,n,s,r){return i.getInterpolation(t,this.a,this.b,this.c,e,n,s,r)}containsPoint(t){return i.containsPoint(t,this.a,this.b,this.c)}isFrontFacing(t){return i.isFrontFacing(this.a,this.b,this.c,t)}intersectsBox(t){return t.intersectsTriangle(this)}closestPointToPoint(t,e){let n=this.a,s=this.b,r=this.c,a,o;Us.subVectors(s,n),Ns.subVectors(r,n),nl.subVectors(t,n);let c=Us.dot(nl),l=Ns.dot(nl);if(c<=0&&l<=0)return e.copy(n);il.subVectors(t,s);let h=Us.dot(il),d=Ns.dot(il);if(h>=0&&d<=h)return e.copy(s);let u=c*d-h*l;if(u<=0&&c>=0&&h<=0)return a=c/(c-h),e.copy(n).addScaledVector(Us,a);sl.subVectors(t,r);let f=Us.dot(sl),g=Ns.dot(sl);if(g>=0&&f<=g)return e.copy(r);let x=f*l-c*g;if(x<=0&&l>=0&&g<=0)return o=l/(l-g),e.copy(n).addScaledVector(Ns,o);let p=h*g-f*d;if(p<=0&&d-h>=0&&f-g>=0)return $h.subVectors(r,s),o=(d-h)/(d-h+(f-g)),e.copy(s).addScaledVector($h,o);let m=1/(p+x+u);return a=x*m,o=u*m,e.copy(n).addScaledVector(Us,a).addScaledVector(Ns,o)}equals(t){return t.a.equals(this.a)&&t.b.equals(this.b)&&t.c.equals(this.c)}},Sn=class{constructor(t=new P(1/0,1/0,1/0),e=new P(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=t,this.max=e}set(t,e){return this.min.copy(t),this.max.copy(e),this}setFromArray(t){this.makeEmpty();for(let e=0,n=t.length;e<n;e+=3)this.expandByPoint(Kn.fromArray(t,e));return this}setFromBufferAttribute(t){this.makeEmpty();for(let e=0,n=t.count;e<n;e++)this.expandByPoint(Kn.fromBufferAttribute(t,e));return this}setFromPoints(t){this.makeEmpty();for(let e=0,n=t.length;e<n;e++)this.expandByPoint(t[e]);return this}setFromCenterAndSize(t,e){let n=Kn.copy(e).multiplyScalar(.5);return this.min.copy(t).sub(n),this.max.copy(t).add(n),this}setFromObject(t,e=!1){return this.makeEmpty(),this.expandByObject(t,e)}clone(){return new this.constructor().copy(this)}copy(t){return this.min.copy(t.min),this.max.copy(t.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(t){return this.isEmpty()?t.set(0,0,0):t.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(t){return this.isEmpty()?t.set(0,0,0):t.subVectors(this.max,this.min)}expandByPoint(t){return this.min.min(t),this.max.max(t),this}expandByVector(t){return this.min.sub(t),this.max.add(t),this}expandByScalar(t){return this.min.addScalar(-t),this.max.addScalar(t),this}expandByObject(t,e=!1){t.updateWorldMatrix(!1,!1);let n=t.geometry;if(n!==void 0){let r=n.getAttribute("position");if(e===!0&&r!==void 0&&t.isInstancedMesh!==!0)for(let a=0,o=r.count;a<o;a++)t.isMesh===!0?t.getVertexPosition(a,Kn):Kn.fromBufferAttribute(r,a),Kn.applyMatrix4(t.matrixWorld),this.expandByPoint(Kn);else t.boundingBox!==void 0?(t.boundingBox===null&&t.computeBoundingBox(),Na.copy(t.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),Na.copy(n.boundingBox)),Na.applyMatrix4(t.matrixWorld),this.union(Na)}let s=t.children;for(let r=0,a=s.length;r<a;r++)this.expandByObject(s[r],e);return this}containsPoint(t){return t.x>=this.min.x&&t.x<=this.max.x&&t.y>=this.min.y&&t.y<=this.max.y&&t.z>=this.min.z&&t.z<=this.max.z}containsBox(t){return this.min.x<=t.min.x&&t.max.x<=this.max.x&&this.min.y<=t.min.y&&t.max.y<=this.max.y&&this.min.z<=t.min.z&&t.max.z<=this.max.z}getParameter(t,e){return e.set((t.x-this.min.x)/(this.max.x-this.min.x),(t.y-this.min.y)/(this.max.y-this.min.y),(t.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(t){return t.max.x>=this.min.x&&t.min.x<=this.max.x&&t.max.y>=this.min.y&&t.min.y<=this.max.y&&t.max.z>=this.min.z&&t.min.z<=this.max.z}intersectsSphere(t){return this.clampPoint(t.center,Kn),Kn.distanceToSquared(t.center)<=t.radius*t.radius}intersectsPlane(t){let e,n;return t.normal.x>0?(e=t.normal.x*this.min.x,n=t.normal.x*this.max.x):(e=t.normal.x*this.max.x,n=t.normal.x*this.min.x),t.normal.y>0?(e+=t.normal.y*this.min.y,n+=t.normal.y*this.max.y):(e+=t.normal.y*this.max.y,n+=t.normal.y*this.min.y),t.normal.z>0?(e+=t.normal.z*this.min.z,n+=t.normal.z*this.max.z):(e+=t.normal.z*this.max.z,n+=t.normal.z*this.min.z),e<=-t.constant&&n>=-t.constant}intersectsTriangle(t){if(this.isEmpty())return!1;this.getCenter(Er),Fa.subVectors(this.max,Er),Fs.subVectors(t.a,Er),zs.subVectors(t.b,Er),Os.subVectors(t.c,Er),Wi.subVectors(zs,Fs),Xi.subVectors(Os,zs),us.subVectors(Fs,Os);let e=[0,-Wi.z,Wi.y,0,-Xi.z,Xi.y,0,-us.z,us.y,Wi.z,0,-Wi.x,Xi.z,0,-Xi.x,us.z,0,-us.x,-Wi.y,Wi.x,0,-Xi.y,Xi.x,0,-us.y,us.x,0];return!cl(e,Fs,zs,Os,Fa)||(e=[1,0,0,0,1,0,0,0,1],!cl(e,Fs,zs,Os,Fa))?!1:(za.crossVectors(Wi,Xi),e=[za.x,za.y,za.z],cl(e,Fs,zs,Os,Fa))}clampPoint(t,e){return e.copy(t).clamp(this.min,this.max)}distanceToPoint(t){return this.clampPoint(t,Kn).distanceTo(t)}getBoundingSphere(t){return this.isEmpty()?t.makeEmpty():(this.getCenter(t.center),t.radius=this.getSize(Kn).length()*.5),t}intersect(t){return this.min.max(t.min),this.max.min(t.max),this.isEmpty()&&this.makeEmpty(),this}union(t){return this.min.min(t.min),this.max.max(t.max),this}applyMatrix4(t){return this.isEmpty()?this:(Ci[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(t),Ci[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(t),Ci[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(t),Ci[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(t),Ci[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(t),Ci[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(t),Ci[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(t),Ci[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(t),this.setFromPoints(Ci),this)}translate(t){return this.min.add(t),this.max.add(t),this}equals(t){return t.min.equals(this.min)&&t.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(t){return this.min.fromArray(t.min),this.max.fromArray(t.max),this}},Ci=[new P,new P,new P,new P,new P,new P,new P,new P],Kn=new P,Na=new Sn,Fs=new P,zs=new P,Os=new P,Wi=new P,Xi=new P,us=new P,Er=new P,Fa=new P,za=new P,ds=new P;function cl(i,t,e,n,s){for(let r=0,a=i.length-3;r<=a;r+=3){ds.fromArray(i,r);let o=s.x*Math.abs(ds.x)+s.y*Math.abs(ds.y)+s.z*Math.abs(ds.z),c=t.dot(ds),l=e.dot(ds),h=n.dot(ds);if(Math.max(-Math.max(c,l,h),Math.min(c,l,h))>o)return!1}return!0}var Ii=$f();function $f(){let i=new ArrayBuffer(4),t=new Float32Array(i),e=new Uint32Array(i),n=new Uint32Array(512),s=new Uint32Array(512);for(let c=0;c<256;++c){let l=c-127;l<-27?(n[c]=0,n[c|256]=32768,s[c]=24,s[c|256]=24):l<-14?(n[c]=1024>>-l-14,n[c|256]=1024>>-l-14|32768,s[c]=-l-1,s[c|256]=-l-1):l<=15?(n[c]=l+15<<10,n[c|256]=l+15<<10|32768,s[c]=13,s[c|256]=13):l<128?(n[c]=31744,n[c|256]=64512,s[c]=24,s[c|256]=24):(n[c]=31744,n[c|256]=64512,s[c]=13,s[c|256]=13)}let r=new Uint32Array(2048),a=new Uint32Array(64),o=new Uint32Array(64);for(let c=1;c<1024;++c){let l=c<<13,h=0;for(;(l&8388608)===0;)l<<=1,h-=8388608;l&=-8388609,h+=947912704,r[c]=l|h}for(let c=1024;c<2048;++c)r[c]=939524096+(c-1024<<13);for(let c=1;c<31;++c)a[c]=c<<23;a[31]=1199570944,a[32]=2147483648;for(let c=33;c<63;++c)a[c]=2147483648+(c-32<<23);a[63]=3347054592;for(let c=1;c<64;++c)c!==32&&(o[c]=1024);return{floatView:t,uint32View:e,baseTable:n,shiftTable:s,mantissaTable:r,exponentTable:a,offsetTable:o}}function Jf(i){Math.abs(i)>65504&&ee("DataUtils.toHalfFloat(): Value out of range."),i=ae(i,-65504,65504),Ii.floatView[0]=i;let t=Ii.uint32View[0],e=t>>23&511;return Ii.baseTable[e]+((t&8388607)>>Ii.shiftTable[e])}function Kf(i){let t=i>>10;return Ii.uint32View[0]=Ii.mantissaTable[Ii.offsetTable[t]+(i&1023)]+Ii.exponentTable[t],Ii.floatView[0]}var tr=class{static toHalfFloat(t){return Jf(t)}static fromHalfFloat(t){return Kf(t)}},je=new P,Oa=new mt,Qf=0,Pe=class extends fi{constructor(t,e,n=!1){if(super(),Array.isArray(t))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Qf++}),this.name="",this.array=t,this.itemSize=e,this.count=t!==void 0?t.length/e:0,this.normalized=n,this.usage=Kl,this.updateRanges=[],this.gpuType=Gn,this.version=0}onUploadCallback(){}set needsUpdate(t){t===!0&&this.version++}setUsage(t){return this.usage=t,this}addUpdateRange(t,e){this.updateRanges.push({start:t,count:e})}clearUpdateRanges(){this.updateRanges.length=0}copy(t){return this.name=t.name,this.array=new t.array.constructor(t.array),this.itemSize=t.itemSize,this.count=t.count,this.normalized=t.normalized,this.usage=t.usage,this.gpuType=t.gpuType,this}copyAt(t,e,n){t*=this.itemSize,n*=e.itemSize;for(let s=0,r=this.itemSize;s<r;s++)this.array[t+s]=e.array[n+s];return this}copyArray(t){return this.array.set(t),this}applyMatrix3(t){if(this.itemSize===2)for(let e=0,n=this.count;e<n;e++)Oa.fromBufferAttribute(this,e),Oa.applyMatrix3(t),this.setXY(e,Oa.x,Oa.y);else if(this.itemSize===3)for(let e=0,n=this.count;e<n;e++)je.fromBufferAttribute(this,e),je.applyMatrix3(t),this.setXYZ(e,je.x,je.y,je.z);return this}applyMatrix4(t){for(let e=0,n=this.count;e<n;e++)je.fromBufferAttribute(this,e),je.applyMatrix4(t),this.setXYZ(e,je.x,je.y,je.z);return this}applyNormalMatrix(t){for(let e=0,n=this.count;e<n;e++)je.fromBufferAttribute(this,e),je.applyNormalMatrix(t),this.setXYZ(e,je.x,je.y,je.z);return this}transformDirection(t){for(let e=0,n=this.count;e<n;e++)je.fromBufferAttribute(this,e),je.transformDirection(t),this.setXYZ(e,je.x,je.y,je.z);return this}set(t,e=0){return this.array.set(t,e),this}getComponent(t,e){let n=this.array[t*this.itemSize+e];return this.normalized&&(n=ti(n,this.array)),n}setComponent(t,e,n){return this.normalized&&(n=Ce(n,this.array)),this.array[t*this.itemSize+e]=n,this}getX(t){let e=this.array[t*this.itemSize];return this.normalized&&(e=ti(e,this.array)),e}setX(t,e){return this.normalized&&(e=Ce(e,this.array)),this.array[t*this.itemSize]=e,this}getY(t){let e=this.array[t*this.itemSize+1];return this.normalized&&(e=ti(e,this.array)),e}setY(t,e){return this.normalized&&(e=Ce(e,this.array)),this.array[t*this.itemSize+1]=e,this}getZ(t){let e=this.array[t*this.itemSize+2];return this.normalized&&(e=ti(e,this.array)),e}setZ(t,e){return this.normalized&&(e=Ce(e,this.array)),this.array[t*this.itemSize+2]=e,this}getW(t){let e=this.array[t*this.itemSize+3];return this.normalized&&(e=ti(e,this.array)),e}setW(t,e){return this.normalized&&(e=Ce(e,this.array)),this.array[t*this.itemSize+3]=e,this}setXY(t,e,n){return t*=this.itemSize,this.normalized&&(e=Ce(e,this.array),n=Ce(n,this.array)),this.array[t+0]=e,this.array[t+1]=n,this}setXYZ(t,e,n,s){return t*=this.itemSize,this.normalized&&(e=Ce(e,this.array),n=Ce(n,this.array),s=Ce(s,this.array)),this.array[t+0]=e,this.array[t+1]=n,this.array[t+2]=s,this}setXYZW(t,e,n,s,r){return t*=this.itemSize,this.normalized&&(e=Ce(e,this.array),n=Ce(n,this.array),s=Ce(s,this.array),r=Ce(r,this.array)),this.array[t+0]=e,this.array[t+1]=n,this.array[t+2]=s,this.array[t+3]=r,this}onUpload(t){return this.onUploadCallback=t,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let t={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return t.name=this.name,t.usage=this.usage,t.gpuType=this.gpuType,t}dispose(){this.dispatchEvent({type:"dispose"})}};var Vr=class extends Pe{constructor(t,e,n){super(new Uint16Array(t),e,n)}};var Gr=class extends Pe{constructor(t,e,n){super(new Uint32Array(t),e,n)}};var Jt=class extends Pe{constructor(t,e,n){super(new Float32Array(t),e,n)}},tp=new Sn,wr=new P,ll=new P,Un=class{constructor(t=new P,e=-1){this.isSphere=!0,this.center=t,this.radius=e}set(t,e){return this.center.copy(t),this.radius=e,this}setFromPoints(t,e){let n=this.center;e!==void 0?n.copy(e):tp.setFromPoints(t).getCenter(n);let s=0;for(let r=0,a=t.length;r<a;r++)s=Math.max(s,n.distanceToSquared(t[r]));return this.radius=Math.sqrt(s),this}copy(t){return this.center.copy(t.center),this.radius=t.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(t){return t.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(t){return t.distanceTo(this.center)-this.radius}intersectsSphere(t){let e=this.radius+t.radius;return t.center.distanceToSquared(this.center)<=e*e}intersectsBox(t){return t.intersectsSphere(this)}intersectsPlane(t){return Math.abs(t.distanceToPoint(this.center))<=this.radius}clampPoint(t,e){let n=this.center.distanceToSquared(t);return e.copy(t),n>this.radius*this.radius&&(e.sub(this.center).normalize(),e.multiplyScalar(this.radius).add(this.center)),e}getBoundingBox(t){return this.isEmpty()?(t.makeEmpty(),t):(t.set(this.center,this.center),t.expandByScalar(this.radius),t)}applyMatrix4(t){return this.center.applyMatrix4(t),this.radius=this.radius*t.getMaxScaleOnAxis(),this}translate(t){return this.center.add(t),this}expandByPoint(t){if(this.isEmpty())return this.center.copy(t),this.radius=0,this;wr.subVectors(t,this.center);let e=wr.lengthSq();if(e>this.radius*this.radius){let n=Math.sqrt(e),s=(n-this.radius)*.5;this.center.addScaledVector(wr,s/n),this.radius+=s}return this}union(t){return t.isEmpty()?this:this.isEmpty()?(this.copy(t),this):(this.center.equals(t.center)===!0?this.radius=Math.max(this.radius,t.radius):(ll.subVectors(t.center,this.center).setLength(t.radius),this.expandByPoint(wr.copy(t.center).add(ll)),this.expandByPoint(wr.copy(t.center).sub(ll))),this)}equals(t){return t.center.equals(this.center)&&t.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(t){return this.radius=t.radius,this.center.fromArray(t.center),this}},ep=0,kn=new ue,hl=new sn,Bs=new P,Dn=new Sn,Tr=new Sn,tn=new P,_e=class i extends fi{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:ep++}),this.uuid=ui(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(t){return Array.isArray(t)?this.index=new(Sf(t)?Gr:Vr)(t,1):this.index=t,this}setIndirect(t,e=0){return this.indirect=t,this.indirectOffset=e,this}getIndirect(){return this.indirect}getAttribute(t){return this.attributes[t]}setAttribute(t,e){return this.attributes[t]=e,this}deleteAttribute(t){return delete this.attributes[t],this}hasAttribute(t){return this.attributes[t]!==void 0}addGroup(t,e,n=0){this.groups.push({start:t,count:e,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(t,e){this.drawRange.start=t,this.drawRange.count=e}applyMatrix4(t){let e=this.attributes.position;e!==void 0&&(e.applyMatrix4(t),e.needsUpdate=!0);let n=this.attributes.normal;if(n!==void 0){let r=new ce().getNormalMatrix(t);n.applyNormalMatrix(r),n.needsUpdate=!0}let s=this.attributes.tangent;return s!==void 0&&(s.transformDirection(t),s.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this._transformed=!0,this}applyQuaternion(t){return kn.makeRotationFromQuaternion(t),this.applyMatrix4(kn),this}rotateX(t){return kn.makeRotationX(t),this.applyMatrix4(kn),this}rotateY(t){return kn.makeRotationY(t),this.applyMatrix4(kn),this}rotateZ(t){return kn.makeRotationZ(t),this.applyMatrix4(kn),this}translate(t,e,n){return kn.makeTranslation(t,e,n),this.applyMatrix4(kn),this}scale(t,e,n){return kn.makeScale(t,e,n),this.applyMatrix4(kn),this}lookAt(t){return hl.lookAt(t),hl.updateMatrix(),this.applyMatrix4(hl.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(Bs).negate(),this.translate(Bs.x,Bs.y,Bs.z),this}setFromPoints(t){let e=this.getAttribute("position");if(e===void 0){let n=[];for(let s=0,r=t.length;s<r;s++){let a=t[s];n.push(a.x,a.y,a.z||0)}this.setAttribute("position",new Jt(n,3))}else{let n=Math.min(t.length,e.count);for(let s=0;s<n;s++){let r=t[s];e.setXYZ(s,r.x,r.y,r.z||0)}t.length>e.count&&ee("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),e.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new Sn);let t=this.attributes.position,e=this.morphAttributes.position;if(t&&t.isGLBufferAttribute){se("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new P(-1/0,-1/0,-1/0),new P(1/0,1/0,1/0));return}if(t!==void 0){if(this.boundingBox.setFromBufferAttribute(t),e)for(let n=0,s=e.length;n<s;n++){let r=e[n];Dn.setFromBufferAttribute(r),this.morphTargetsRelative?(tn.addVectors(this.boundingBox.min,Dn.min),this.boundingBox.expandByPoint(tn),tn.addVectors(this.boundingBox.max,Dn.max),this.boundingBox.expandByPoint(tn)):(this.boundingBox.expandByPoint(Dn.min),this.boundingBox.expandByPoint(Dn.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&se('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Un);let t=this.attributes.position,e=this.morphAttributes.position;if(t&&t.isGLBufferAttribute){se("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new P,1/0);return}if(t){let n=this.boundingSphere.center;if(Dn.setFromBufferAttribute(t),e)for(let r=0,a=e.length;r<a;r++){let o=e[r];Tr.setFromBufferAttribute(o),this.morphTargetsRelative?(tn.addVectors(Dn.min,Tr.min),Dn.expandByPoint(tn),tn.addVectors(Dn.max,Tr.max),Dn.expandByPoint(tn)):(Dn.expandByPoint(Tr.min),Dn.expandByPoint(Tr.max))}Dn.getCenter(n);let s=0;for(let r=0,a=t.count;r<a;r++)tn.fromBufferAttribute(t,r),s=Math.max(s,n.distanceToSquared(tn));if(e)for(let r=0,a=e.length;r<a;r++){let o=e[r],c=this.morphTargetsRelative;for(let l=0,h=o.count;l<h;l++)tn.fromBufferAttribute(o,l),c&&(Bs.fromBufferAttribute(t,l),tn.add(Bs)),s=Math.max(s,n.distanceToSquared(tn))}this.boundingSphere.radius=Math.sqrt(s),isNaN(this.boundingSphere.radius)&&se('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let t=this.index,e=this.attributes;if(t===null||e.position===void 0||e.normal===void 0||e.uv===void 0){se("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let n=e.position,s=e.normal,r=e.uv,a=this.getAttribute("tangent");(a===void 0||a.count!==n.count)&&(a=new Pe(new Float32Array(4*n.count),4),this.setAttribute("tangent",a));let o=[],c=[];for(let _=0;_<n.count;_++)o[_]=new P,c[_]=new P;let l=new P,h=new P,d=new P,u=new mt,f=new mt,g=new mt,x=new P,p=new P;function m(_,T,I){l.fromBufferAttribute(n,_),h.fromBufferAttribute(n,T),d.fromBufferAttribute(n,I),u.fromBufferAttribute(r,_),f.fromBufferAttribute(r,T),g.fromBufferAttribute(r,I),h.sub(l),d.sub(l),f.sub(u),g.sub(u);let L=1/(f.x*g.y-g.x*f.y);isFinite(L)&&(x.copy(h).multiplyScalar(g.y).addScaledVector(d,-f.y).multiplyScalar(L),p.copy(d).multiplyScalar(f.x).addScaledVector(h,-g.x).multiplyScalar(L),o[_].add(x),o[T].add(x),o[I].add(x),c[_].add(p),c[T].add(p),c[I].add(p))}let S=this.groups;S.length===0&&(S=[{start:0,count:t.count}]);for(let _=0,T=S.length;_<T;++_){let I=S[_],L=I.start,N=I.count;for(let B=L,D=L+N;B<D;B+=3)m(t.getX(B+0),t.getX(B+1),t.getX(B+2))}let E=new P,v=new P,b=new P,M=new P;function A(_){b.fromBufferAttribute(s,_),M.copy(b);let T=o[_];E.copy(T),E.sub(b.multiplyScalar(b.dot(T))).normalize(),v.crossVectors(M,T);let L=v.dot(c[_])<0?-1:1;a.setXYZW(_,E.x,E.y,E.z,L)}for(let _=0,T=S.length;_<T;++_){let I=S[_],L=I.start,N=I.count;for(let B=L,D=L+N;B<D;B+=3)A(t.getX(B+0)),A(t.getX(B+1)),A(t.getX(B+2))}this._transformed=!0}computeVertexNormals(){let t=this.index,e=this.getAttribute("position");if(e!==void 0){let n=this.getAttribute("normal");if(n===void 0||n.count!==e.count)n=new Pe(new Float32Array(e.count*3),3),this.setAttribute("normal",n);else for(let u=0,f=n.count;u<f;u++)n.setXYZ(u,0,0,0);let s=new P,r=new P,a=new P,o=new P,c=new P,l=new P,h=new P,d=new P;if(t)for(let u=0,f=t.count;u<f;u+=3){let g=t.getX(u+0),x=t.getX(u+1),p=t.getX(u+2);s.fromBufferAttribute(e,g),r.fromBufferAttribute(e,x),a.fromBufferAttribute(e,p),h.subVectors(a,r),d.subVectors(s,r),h.cross(d),o.fromBufferAttribute(n,g),c.fromBufferAttribute(n,x),l.fromBufferAttribute(n,p),o.add(h),c.add(h),l.add(h),n.setXYZ(g,o.x,o.y,o.z),n.setXYZ(x,c.x,c.y,c.z),n.setXYZ(p,l.x,l.y,l.z)}else for(let u=0,f=e.count;u<f;u+=3)s.fromBufferAttribute(e,u+0),r.fromBufferAttribute(e,u+1),a.fromBufferAttribute(e,u+2),h.subVectors(a,r),d.subVectors(s,r),h.cross(d),n.setXYZ(u+0,h.x,h.y,h.z),n.setXYZ(u+1,h.x,h.y,h.z),n.setXYZ(u+2,h.x,h.y,h.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let t=this.attributes.normal;for(let e=0,n=t.count;e<n;e++)tn.fromBufferAttribute(t,e),tn.normalize(),t.setXYZ(e,tn.x,tn.y,tn.z)}toNonIndexed(){function t(o,c){let l=o.array,h=o.itemSize,d=o.normalized,u=new l.constructor(c.length*h),f=0,g=0;for(let x=0,p=c.length;x<p;x++){o.isInterleavedBufferAttribute?f=c[x]*o.data.stride+o.offset:f=c[x]*h;for(let m=0;m<h;m++)u[g++]=l[f++]}return new Pe(u,h,d)}if(this.index===null)return ee("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let e=new i,n=this.index.array,s=this.attributes;for(let o in s){let c=s[o],l=t(c,n);e.setAttribute(o,l)}let r=this.morphAttributes;for(let o in r){let c=[],l=r[o];for(let h=0,d=l.length;h<d;h++){let u=l[h],f=t(u,n);c.push(f)}e.morphAttributes[o]=c}e.morphTargetsRelative=this.morphTargetsRelative;let a=this.groups;for(let o=0,c=a.length;o<c;o++){let l=a[o];e.addGroup(l.start,l.count,l.materialIndex)}return e}toJSON(){let t={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(t.uuid=this.uuid,t.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,t.name=this.name,Object.keys(this.userData).length>0&&(t.userData=this.userData),this.parameters!==void 0&&this._transformed!==!0){let c=this.parameters;for(let l in c)c[l]!==void 0&&(t[l]=c[l]);return t}t.data={attributes:{}};let e=this.index;e!==null&&(t.data.index={type:e.array.constructor.name,array:Array.prototype.slice.call(e.array)});let n=this.attributes;for(let c in n){let l=n[c];t.data.attributes[c]=l.toJSON(t.data)}let s={},r=!1;for(let c in this.morphAttributes){let l=this.morphAttributes[c],h=[];for(let d=0,u=l.length;d<u;d++){let f=l[d];h.push(f.toJSON(t.data))}h.length>0&&(s[c]=h,r=!0)}r&&(t.data.morphAttributes=s,t.data.morphTargetsRelative=this.morphTargetsRelative);let a=this.groups;a.length>0&&(t.data.groups=JSON.parse(JSON.stringify(a)));let o=this.boundingSphere;return o!==null&&(t.data.boundingSphere=o.toJSON()),t}clone(){return new this.constructor().copy(this)}copy(t){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let e={};this.name=t.name;let n=t.index;n!==null&&this.setIndex(n.clone());let s=t.attributes;for(let l in s){let h=s[l];this.setAttribute(l,h.clone(e))}let r=t.morphAttributes;for(let l in r){let h=[],d=r[l];for(let u=0,f=d.length;u<f;u++)h.push(d[u].clone(e));this.morphAttributes[l]=h}this.morphTargetsRelative=t.morphTargetsRelative;let a=t.groups;for(let l=0,h=a.length;l<h;l++){let d=a[l];this.addGroup(d.start,d.count,d.materialIndex)}let o=t.boundingBox;o!==null&&(this.boundingBox=o.clone());let c=t.boundingSphere;return c!==null&&(this.boundingSphere=c.clone()),this.drawRange.start=t.drawRange.start,this.drawRange.count=t.drawRange.count,this.userData=t.userData,this._transformed=t._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}},xo=class{constructor(t,e){this.isInterleavedBuffer=!0,this.array=t,this.stride=e,this.count=t!==void 0?t.length/e:0,this.usage=Kl,this.updateRanges=[],this.version=0,this.uuid=ui()}onUploadCallback(){}set needsUpdate(t){t===!0&&this.version++}setUsage(t){return this.usage=t,this}addUpdateRange(t,e){this.updateRanges.push({start:t,count:e})}clearUpdateRanges(){this.updateRanges.length=0}copy(t){return this.array=new t.array.constructor(t.array),this.count=t.count,this.stride=t.stride,this.usage=t.usage,this}copyAt(t,e,n){t*=this.stride,n*=e.stride;for(let s=0,r=this.stride;s<r;s++)this.array[t+s]=e.array[n+s];return this}set(t,e=0){return this.array.set(t,e),this}clone(t){t.arrayBuffers===void 0&&(t.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=ui()),t.arrayBuffers[this.array.buffer._uuid]===void 0&&(t.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer);let e=new this.array.constructor(t.arrayBuffers[this.array.buffer._uuid]),n=new this.constructor(e,this.stride);return n.setUsage(this.usage),n}onUpload(t){return this.onUploadCallback=t,this}toJSON(t){t.arrayBuffers===void 0&&(t.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=ui()),t.arrayBuffers[this.array.buffer._uuid]===void 0&&(t.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer)));let e={uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride};return e.usage=this.usage,e}},_n=new P,ii=class i{constructor(t,e,n,s=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=t,this.itemSize=e,this.offset=n,this.normalized=s}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(t){this.data.needsUpdate=t}applyMatrix4(t){for(let e=0,n=this.data.count;e<n;e++)_n.fromBufferAttribute(this,e),_n.applyMatrix4(t),this.setXYZ(e,_n.x,_n.y,_n.z);return this}applyNormalMatrix(t){for(let e=0,n=this.count;e<n;e++)_n.fromBufferAttribute(this,e),_n.applyNormalMatrix(t),this.setXYZ(e,_n.x,_n.y,_n.z);return this}transformDirection(t){for(let e=0,n=this.count;e<n;e++)_n.fromBufferAttribute(this,e),_n.transformDirection(t),this.setXYZ(e,_n.x,_n.y,_n.z);return this}getComponent(t,e){let n=this.array[t*this.data.stride+this.offset+e];return this.normalized&&(n=ti(n,this.array)),n}setComponent(t,e,n){return this.normalized&&(n=Ce(n,this.array)),this.data.array[t*this.data.stride+this.offset+e]=n,this}setX(t,e){return this.normalized&&(e=Ce(e,this.array)),this.data.array[t*this.data.stride+this.offset]=e,this}setY(t,e){return this.normalized&&(e=Ce(e,this.array)),this.data.array[t*this.data.stride+this.offset+1]=e,this}setZ(t,e){return this.normalized&&(e=Ce(e,this.array)),this.data.array[t*this.data.stride+this.offset+2]=e,this}setW(t,e){return this.normalized&&(e=Ce(e,this.array)),this.data.array[t*this.data.stride+this.offset+3]=e,this}getX(t){let e=this.data.array[t*this.data.stride+this.offset];return this.normalized&&(e=ti(e,this.array)),e}getY(t){let e=this.data.array[t*this.data.stride+this.offset+1];return this.normalized&&(e=ti(e,this.array)),e}getZ(t){let e=this.data.array[t*this.data.stride+this.offset+2];return this.normalized&&(e=ti(e,this.array)),e}getW(t){let e=this.data.array[t*this.data.stride+this.offset+3];return this.normalized&&(e=ti(e,this.array)),e}setXY(t,e,n){return t=t*this.data.stride+this.offset,this.normalized&&(e=Ce(e,this.array),n=Ce(n,this.array)),this.data.array[t+0]=e,this.data.array[t+1]=n,this}setXYZ(t,e,n,s){return t=t*this.data.stride+this.offset,this.normalized&&(e=Ce(e,this.array),n=Ce(n,this.array),s=Ce(s,this.array)),this.data.array[t+0]=e,this.data.array[t+1]=n,this.data.array[t+2]=s,this}setXYZW(t,e,n,s,r){return t=t*this.data.stride+this.offset,this.normalized&&(e=Ce(e,this.array),n=Ce(n,this.array),s=Ce(s,this.array),r=Ce(r,this.array)),this.data.array[t+0]=e,this.data.array[t+1]=n,this.data.array[t+2]=s,this.data.array[t+3]=r,this}clone(t){if(t===void 0){Or("InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");let e=[];for(let n=0;n<this.count;n++){let s=n*this.data.stride+this.offset;for(let r=0;r<this.itemSize;r++)e.push(this.data.array[s+r])}return new Pe(new this.array.constructor(e),this.itemSize,this.normalized)}else return t.interleavedBuffers===void 0&&(t.interleavedBuffers={}),t.interleavedBuffers[this.data.uuid]===void 0&&(t.interleavedBuffers[this.data.uuid]=this.data.clone(t)),new i(t.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}toJSON(t){if(t===void 0){Or("InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");let e=[];for(let n=0;n<this.count;n++){let s=n*this.data.stride+this.offset;for(let r=0;r<this.itemSize;r++)e.push(this.data.array[s+r])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:e,normalized:this.normalized}}else return t.interleavedBuffers===void 0&&(t.interleavedBuffers={}),t.interleavedBuffers[this.data.uuid]===void 0&&(t.interleavedBuffers[this.data.uuid]=this.data.toJSON(t)),{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}},ul=new P,np=new P,ip=new ce,Qn=class{constructor(t=new P(1,0,0),e=0){this.isPlane=!0,this.normal=t,this.constant=e}set(t,e){return this.normal.copy(t),this.constant=e,this}setComponents(t,e,n,s){return this.normal.set(t,e,n),this.constant=s,this}setFromNormalAndCoplanarPoint(t,e){return this.normal.copy(t),this.constant=-e.dot(this.normal),this}setFromCoplanarPoints(t,e,n){let s=ul.subVectors(n,e).cross(np.subVectors(t,e)).normalize();return this.setFromNormalAndCoplanarPoint(s,t),this}copy(t){return this.normal.copy(t.normal),this.constant=t.constant,this}normalize(){let t=1/this.normal.length();return this.normal.multiplyScalar(t),this.constant*=t,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(t){return this.normal.dot(t)+this.constant}distanceToSphere(t){return this.distanceToPoint(t.center)-t.radius}projectPoint(t,e){return e.copy(t).addScaledVector(this.normal,-this.distanceToPoint(t))}intersectLine(t,e,n=!0){let s=t.delta(ul),r=this.normal.dot(s);if(r===0)return this.distanceToPoint(t.start)===0?e.copy(t.start):null;let a=-(t.start.dot(this.normal)+this.constant)/r;return n===!0&&(a<0||a>1)?null:e.copy(t.start).addScaledVector(s,a)}intersectsLine(t){let e=this.distanceToPoint(t.start),n=this.distanceToPoint(t.end);return e<0&&n>0||n<0&&e>0}intersectsBox(t){return t.intersectsPlane(this)}intersectsSphere(t){return t.intersectsPlane(this)}coplanarPoint(t){return t.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(t,e){let n=e||ip.getNormalMatrix(t),s=this.coplanarPoint(ul).applyMatrix4(t),r=this.normal.applyMatrix3(n).normalize();return this.constant=-s.dot(r),this}translate(t){return this.constant-=t.dot(this.normal),this}equals(t){return t.normal.equals(this.normal)&&t.constant===this.constant}clone(){return new this.constructor().copy(this)}toJSON(){return{normal:this.normal.toArray(),constant:this.constant}}fromJSON(t){return this.normal.fromArray(t.normal),this.constant=t.constant,this}},sp=0,Ui=class extends fi{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:sp++}),this.uuid=ui(),this.name="",this.type="Material",this.blending=cr,this.side=ns,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Fl,this.blendDst=zl,this.blendEquation=ys,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new Ot(0,0,0),this.blendAlpha=0,this.depthFunc=Ys,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=Wu,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=so,this.stencilZFail=so,this.stencilZPass=so,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(t){this._alphaTest>0!=t>0&&this.version++,this._alphaTest=t}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(t){if(t!==void 0)for(let e in t){let n=t[e];if(n===void 0){ee(`Material: parameter '${e}' has value of undefined.`);continue}let s=this[e];if(s===void 0){ee(`Material: '${e}' is not a property of THREE.${this.type}.`);continue}s&&s.isColor?s.set(n):s&&s.isVector2&&n&&n.isVector2||s&&s.isEuler&&n&&n.isEuler||s&&s.isVector3&&n&&n.isVector3?s.copy(n):this[e]=n}}toJSON(t){let e=t===void 0||typeof t=="string";e&&(t={textures:{},images:{}});let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,n.blending=this.blending,n.side=this.side,n.shadowSide=this.shadowSide,n.vertexColors=this.vertexColors,n.opacity=this.opacity,n.transparent=this.transparent,n.blendSrc=this.blendSrc,n.blendDst=this.blendDst,n.blendEquation=this.blendEquation,n.blendSrcAlpha=this.blendSrcAlpha,n.blendDstAlpha=this.blendDstAlpha,n.blendEquationAlpha=this.blendEquationAlpha,n.blendColor=this.blendColor.getHex(),n.blendAlpha=this.blendAlpha,n.depthFunc=this.depthFunc,n.depthTest=this.depthTest,n.depthWrite=this.depthWrite,n.colorWrite=this.colorWrite,n.clipIntersection=this.clipIntersection,n.clipShadows=this.clipShadows,n.stencilWriteMask=this.stencilWriteMask,n.stencilFunc=this.stencilFunc,n.stencilRef=this.stencilRef,n.stencilFuncMask=this.stencilFuncMask,n.stencilFail=this.stencilFail,n.stencilZFail=this.stencilZFail,n.stencilZPass=this.stencilZPass,n.stencilWrite=this.stencilWrite,n.polygonOffset=this.polygonOffset,n.polygonOffsetFactor=this.polygonOffsetFactor,n.polygonOffsetUnits=this.polygonOffsetUnits,n.dithering=this.dithering,n.alphaTest=this.alphaTest,n.alphaHash=this.alphaHash,n.alphaToCoverage=this.alphaToCoverage,n.premultipliedAlpha=this.premultipliedAlpha,n.forceSinglePass=this.forceSinglePass,n.allowOverride=this.allowOverride,n.visible=this.visible,n.toneMapped=this.toneMapped,n.name=this.name,this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(t).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(t).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(t).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(t).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(t).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.retroreflectivity!==void 0&&(n.retroreflectivity=this.retroreflectivity),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(t).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(t).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(t).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(t).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(t).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(t).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(t).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(t).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(t).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(t).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(t).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(t).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(t).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(t).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(t).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(t).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(t).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(t).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(t).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(t).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(t).uuid),this.attenuationDistance!==void 0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),Array.isArray(this.clippingPlanes)&&this.clippingPlanes.length>0&&(n.clippingPlanes=this.clippingPlanes.map(r=>r.toJSON())),this.rotation!==void 0&&(n.rotation=this.rotation),this.depthPacking!==void 0&&(n.depthPacking=this.depthPacking),this.linewidth!==void 0&&(n.linewidth=this.linewidth),this.linecap!==void 0&&(n.linecap=this.linecap),this.linejoin!==void 0&&(n.linejoin=this.linejoin),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.wireframe!==void 0&&(n.wireframe=this.wireframe),this.wireframeLinewidth!==void 0&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!==void 0&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!==void 0&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading!==void 0&&(n.flatShading=this.flatShading),this.fog!==void 0&&(n.fog=this.fog),Object.keys(this.userData).length>0&&(n.userData=this.userData);function s(r){let a=[];for(let o in r){let c=r[o];delete c.metadata,a.push(c)}return a}if(e){let r=s(t.textures),a=s(t.images);r.length>0&&(n.textures=r),a.length>0&&(n.images=a)}return n}fromJSON(t,e){if(t.uuid!==void 0&&(this.uuid=t.uuid),t.name!==void 0&&(this.name=t.name),t.color!==void 0&&this.color!==void 0&&this.color.setHex(t.color),t.roughness!==void 0&&(this.roughness=t.roughness),t.metalness!==void 0&&(this.metalness=t.metalness),t.sheen!==void 0&&(this.sheen=t.sheen),t.sheenColor!==void 0&&(this.sheenColor=new Ot().setHex(t.sheenColor)),t.sheenRoughness!==void 0&&(this.sheenRoughness=t.sheenRoughness),t.emissive!==void 0&&this.emissive!==void 0&&this.emissive.setHex(t.emissive),t.specular!==void 0&&this.specular!==void 0&&this.specular.setHex(t.specular),t.specularIntensity!==void 0&&(this.specularIntensity=t.specularIntensity),t.specularColor!==void 0&&this.specularColor!==void 0&&this.specularColor.setHex(t.specularColor),t.shininess!==void 0&&(this.shininess=t.shininess),t.clearcoat!==void 0&&(this.clearcoat=t.clearcoat),t.clearcoatRoughness!==void 0&&(this.clearcoatRoughness=t.clearcoatRoughness),t.dispersion!==void 0&&(this.dispersion=t.dispersion),t.retroreflectivity!==void 0&&(this.retroreflectivity=t.retroreflectivity),t.iridescence!==void 0&&(this.iridescence=t.iridescence),t.iridescenceIOR!==void 0&&(this.iridescenceIOR=t.iridescenceIOR),t.iridescenceThicknessRange!==void 0&&(this.iridescenceThicknessRange=t.iridescenceThicknessRange),t.transmission!==void 0&&(this.transmission=t.transmission),t.thickness!==void 0&&(this.thickness=t.thickness),t.attenuationDistance!==void 0&&(this.attenuationDistance=t.attenuationDistance),t.attenuationColor!==void 0&&this.attenuationColor!==void 0&&this.attenuationColor.setHex(t.attenuationColor),t.anisotropy!==void 0&&(this.anisotropy=t.anisotropy),t.anisotropyRotation!==void 0&&(this.anisotropyRotation=t.anisotropyRotation),t.fog!==void 0&&(this.fog=t.fog),t.flatShading!==void 0&&(this.flatShading=t.flatShading),t.blending!==void 0&&(this.blending=t.blending),t.combine!==void 0&&(this.combine=t.combine),t.side!==void 0&&(this.side=t.side),t.shadowSide!==void 0&&(this.shadowSide=t.shadowSide),t.opacity!==void 0&&(this.opacity=t.opacity),t.transparent!==void 0&&(this.transparent=t.transparent),t.alphaTest!==void 0&&(this.alphaTest=t.alphaTest),t.alphaHash!==void 0&&(this.alphaHash=t.alphaHash),t.depthFunc!==void 0&&(this.depthFunc=t.depthFunc),t.depthTest!==void 0&&(this.depthTest=t.depthTest),t.depthWrite!==void 0&&(this.depthWrite=t.depthWrite),t.colorWrite!==void 0&&(this.colorWrite=t.colorWrite),t.clippingPlanes!==void 0&&(this.clippingPlanes=t.clippingPlanes.map(n=>new Qn().fromJSON(n))),t.clipIntersection!==void 0&&(this.clipIntersection=t.clipIntersection),t.clipShadows!==void 0&&(this.clipShadows=t.clipShadows),t.depthPacking!==void 0&&(this.depthPacking=t.depthPacking),t.blendSrc!==void 0&&(this.blendSrc=t.blendSrc),t.blendDst!==void 0&&(this.blendDst=t.blendDst),t.blendEquation!==void 0&&(this.blendEquation=t.blendEquation),t.blendSrcAlpha!==void 0&&(this.blendSrcAlpha=t.blendSrcAlpha),t.blendDstAlpha!==void 0&&(this.blendDstAlpha=t.blendDstAlpha),t.blendEquationAlpha!==void 0&&(this.blendEquationAlpha=t.blendEquationAlpha),t.blendColor!==void 0&&this.blendColor!==void 0&&this.blendColor.setHex(t.blendColor),t.blendAlpha!==void 0&&(this.blendAlpha=t.blendAlpha),t.stencilWriteMask!==void 0&&(this.stencilWriteMask=t.stencilWriteMask),t.stencilFunc!==void 0&&(this.stencilFunc=t.stencilFunc),t.stencilRef!==void 0&&(this.stencilRef=t.stencilRef),t.stencilFuncMask!==void 0&&(this.stencilFuncMask=t.stencilFuncMask),t.stencilFail!==void 0&&(this.stencilFail=t.stencilFail),t.stencilZFail!==void 0&&(this.stencilZFail=t.stencilZFail),t.stencilZPass!==void 0&&(this.stencilZPass=t.stencilZPass),t.stencilWrite!==void 0&&(this.stencilWrite=t.stencilWrite),t.wireframe!==void 0&&(this.wireframe=t.wireframe),t.wireframeLinewidth!==void 0&&(this.wireframeLinewidth=t.wireframeLinewidth),t.wireframeLinecap!==void 0&&(this.wireframeLinecap=t.wireframeLinecap),t.wireframeLinejoin!==void 0&&(this.wireframeLinejoin=t.wireframeLinejoin),t.rotation!==void 0&&(this.rotation=t.rotation),t.linewidth!==void 0&&(this.linewidth=t.linewidth),t.linecap!==void 0&&(this.linecap=t.linecap),t.linejoin!==void 0&&(this.linejoin=t.linejoin),t.dashSize!==void 0&&(this.dashSize=t.dashSize),t.gapSize!==void 0&&(this.gapSize=t.gapSize),t.scale!==void 0&&(this.scale=t.scale),t.polygonOffset!==void 0&&(this.polygonOffset=t.polygonOffset),t.polygonOffsetFactor!==void 0&&(this.polygonOffsetFactor=t.polygonOffsetFactor),t.polygonOffsetUnits!==void 0&&(this.polygonOffsetUnits=t.polygonOffsetUnits),t.dithering!==void 0&&(this.dithering=t.dithering),t.alphaToCoverage!==void 0&&(this.alphaToCoverage=t.alphaToCoverage),t.premultipliedAlpha!==void 0&&(this.premultipliedAlpha=t.premultipliedAlpha),t.forceSinglePass!==void 0&&(this.forceSinglePass=t.forceSinglePass),t.allowOverride!==void 0&&(this.allowOverride=t.allowOverride),t.visible!==void 0&&(this.visible=t.visible),t.toneMapped!==void 0&&(this.toneMapped=t.toneMapped),t.userData!==void 0&&(this.userData=t.userData),t.vertexColors!==void 0&&(typeof t.vertexColors=="number"?this.vertexColors=t.vertexColors>0:this.vertexColors=t.vertexColors),t.size!==void 0&&(this.size=t.size),t.sizeAttenuation!==void 0&&(this.sizeAttenuation=t.sizeAttenuation),t.map!==void 0&&(this.map=e[t.map]||null),t.matcap!==void 0&&(this.matcap=e[t.matcap]||null),t.alphaMap!==void 0&&(this.alphaMap=e[t.alphaMap]||null),t.bumpMap!==void 0&&(this.bumpMap=e[t.bumpMap]||null),t.bumpScale!==void 0&&(this.bumpScale=t.bumpScale),t.normalMap!==void 0&&(this.normalMap=e[t.normalMap]||null),t.normalMapType!==void 0&&(this.normalMapType=t.normalMapType),t.normalScale!==void 0){let n=t.normalScale;Array.isArray(n)===!1&&(n=[n,n]),this.normalScale=new mt().fromArray(n)}return t.displacementMap!==void 0&&(this.displacementMap=e[t.displacementMap]||null),t.displacementScale!==void 0&&(this.displacementScale=t.displacementScale),t.displacementBias!==void 0&&(this.displacementBias=t.displacementBias),t.roughnessMap!==void 0&&(this.roughnessMap=e[t.roughnessMap]||null),t.metalnessMap!==void 0&&(this.metalnessMap=e[t.metalnessMap]||null),t.emissiveMap!==void 0&&(this.emissiveMap=e[t.emissiveMap]||null),t.emissiveIntensity!==void 0&&(this.emissiveIntensity=t.emissiveIntensity),t.specularMap!==void 0&&(this.specularMap=e[t.specularMap]||null),t.specularIntensityMap!==void 0&&(this.specularIntensityMap=e[t.specularIntensityMap]||null),t.specularColorMap!==void 0&&(this.specularColorMap=e[t.specularColorMap]||null),t.envMap!==void 0&&(this.envMap=e[t.envMap]||null),t.envMapRotation!==void 0&&this.envMapRotation.fromArray(t.envMapRotation),t.envMapIntensity!==void 0&&(this.envMapIntensity=t.envMapIntensity),t.reflectivity!==void 0&&(this.reflectivity=t.reflectivity),t.refractionRatio!==void 0&&(this.refractionRatio=t.refractionRatio),t.lightMap!==void 0&&(this.lightMap=e[t.lightMap]||null),t.lightMapIntensity!==void 0&&(this.lightMapIntensity=t.lightMapIntensity),t.aoMap!==void 0&&(this.aoMap=e[t.aoMap]||null),t.aoMapIntensity!==void 0&&(this.aoMapIntensity=t.aoMapIntensity),t.gradientMap!==void 0&&(this.gradientMap=e[t.gradientMap]||null),t.clearcoatMap!==void 0&&(this.clearcoatMap=e[t.clearcoatMap]||null),t.clearcoatRoughnessMap!==void 0&&(this.clearcoatRoughnessMap=e[t.clearcoatRoughnessMap]||null),t.clearcoatNormalMap!==void 0&&(this.clearcoatNormalMap=e[t.clearcoatNormalMap]||null),t.clearcoatNormalScale!==void 0&&(this.clearcoatNormalScale=new mt().fromArray(t.clearcoatNormalScale)),t.iridescenceMap!==void 0&&(this.iridescenceMap=e[t.iridescenceMap]||null),t.iridescenceThicknessMap!==void 0&&(this.iridescenceThicknessMap=e[t.iridescenceThicknessMap]||null),t.transmissionMap!==void 0&&(this.transmissionMap=e[t.transmissionMap]||null),t.thicknessMap!==void 0&&(this.thicknessMap=e[t.thicknessMap]||null),t.anisotropyMap!==void 0&&(this.anisotropyMap=e[t.anisotropyMap]||null),t.sheenColorMap!==void 0&&(this.sheenColorMap=e[t.sheenColorMap]||null),t.sheenRoughnessMap!==void 0&&(this.sheenRoughnessMap=e[t.sheenRoughnessMap]||null),this}clone(){return new this.constructor().copy(this)}copy(t){this.name=t.name,this.blending=t.blending,this.side=t.side,this.vertexColors=t.vertexColors,this.opacity=t.opacity,this.transparent=t.transparent,this.blendSrc=t.blendSrc,this.blendDst=t.blendDst,this.blendEquation=t.blendEquation,this.blendSrcAlpha=t.blendSrcAlpha,this.blendDstAlpha=t.blendDstAlpha,this.blendEquationAlpha=t.blendEquationAlpha,this.blendColor.copy(t.blendColor),this.blendAlpha=t.blendAlpha,this.depthFunc=t.depthFunc,this.depthTest=t.depthTest,this.depthWrite=t.depthWrite,this.stencilWriteMask=t.stencilWriteMask,this.stencilFunc=t.stencilFunc,this.stencilRef=t.stencilRef,this.stencilFuncMask=t.stencilFuncMask,this.stencilFail=t.stencilFail,this.stencilZFail=t.stencilZFail,this.stencilZPass=t.stencilZPass,this.stencilWrite=t.stencilWrite;let e=t.clippingPlanes,n=null;if(e!==null){let s=e.length;n=new Array(s);for(let r=0;r!==s;++r)n[r]=e[r].clone()}return this.clippingPlanes=n,this.clipIntersection=t.clipIntersection,this.clipShadows=t.clipShadows,this.shadowSide=t.shadowSide,this.colorWrite=t.colorWrite,this.precision=t.precision,this.polygonOffset=t.polygonOffset,this.polygonOffsetFactor=t.polygonOffsetFactor,this.polygonOffsetUnits=t.polygonOffsetUnits,this.dithering=t.dithering,this.alphaTest=t.alphaTest,this.alphaHash=t.alphaHash,this.alphaToCoverage=t.alphaToCoverage,this.premultipliedAlpha=t.premultipliedAlpha,this.forceSinglePass=t.forceSinglePass,this.allowOverride=t.allowOverride,this.visible=t.visible,this.toneMapped=t.toneMapped,this.userData=JSON.parse(JSON.stringify(t.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(t){t===!0&&this.version++}};var Pi=new P,dl=new P,Ba=new P,ka=new P,Wr=class{constructor(t=new P,e=new P(0,0,-1)){this.origin=t,this.direction=e}set(t,e){return this.origin.copy(t),this.direction.copy(e),this}copy(t){return this.origin.copy(t.origin),this.direction.copy(t.direction),this}at(t,e){return e.copy(this.origin).addScaledVector(this.direction,t)}lookAt(t){return this.direction.copy(t).sub(this.origin).normalize(),this}recast(t){return this.origin.copy(this.at(t,Pi)),this}closestPointToPoint(t,e){e.subVectors(t,this.origin);let n=e.dot(this.direction);return n<0?e.copy(this.origin):e.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(t){return Math.sqrt(this.distanceSqToPoint(t))}distanceSqToPoint(t){let e=Pi.subVectors(t,this.origin).dot(this.direction);return e<0?this.origin.distanceToSquared(t):(Pi.copy(this.origin).addScaledVector(this.direction,e),Pi.distanceToSquared(t))}distanceSqToSegment(t,e,n,s){dl.copy(t).add(e).multiplyScalar(.5),Ba.copy(e).sub(t).normalize(),ka.copy(this.origin).sub(dl);let r=t.distanceTo(e)*.5,a=-this.direction.dot(Ba),o=ka.dot(this.direction),c=-ka.dot(Ba),l=ka.lengthSq(),h=Math.abs(1-a*a),d,u,f,g;if(h>0)if(d=a*c-o,u=a*o-c,g=r*h,d>=0)if(u>=-g)if(u<=g){let x=1/h;d*=x,u*=x,f=d*(d+a*u+2*o)+u*(a*d+u+2*c)+l}else u=r,d=Math.max(0,-(a*u+o)),f=-d*d+u*(u+2*c)+l;else u=-r,d=Math.max(0,-(a*u+o)),f=-d*d+u*(u+2*c)+l;else u<=-g?(d=Math.max(0,-(-a*r+o)),u=d>0?-r:Math.min(Math.max(-r,-c),r),f=-d*d+u*(u+2*c)+l):u<=g?(d=0,u=Math.min(Math.max(-r,-c),r),f=u*(u+2*c)+l):(d=Math.max(0,-(a*r+o)),u=d>0?r:Math.min(Math.max(-r,-c),r),f=-d*d+u*(u+2*c)+l);else u=a>0?-r:r,d=Math.max(0,-(a*u+o)),f=-d*d+u*(u+2*c)+l;return n&&n.copy(this.origin).addScaledVector(this.direction,d),s&&s.copy(dl).addScaledVector(Ba,u),f}intersectSphere(t,e){if(t.radius<0)return null;Pi.subVectors(t.center,this.origin);let n=Pi.dot(this.direction),s=Pi.dot(Pi)-n*n,r=t.radius*t.radius;if(s>r)return null;let a=Math.sqrt(r-s),o=n-a,c=n+a;return c<0?null:o<0?this.at(c,e):this.at(o,e)}intersectsSphere(t){return t.radius<0?!1:this.distanceSqToPoint(t.center)<=t.radius*t.radius}distanceToPlane(t){let e=t.normal.dot(this.direction);if(e===0)return t.distanceToPoint(this.origin)===0?0:null;let n=-(this.origin.dot(t.normal)+t.constant)/e;return n>=0?n:null}intersectPlane(t,e){let n=this.distanceToPlane(t);return n===null?null:this.at(n,e)}intersectsPlane(t){let e=t.distanceToPoint(this.origin);return e===0||t.normal.dot(this.direction)*e<0}intersectBox(t,e){let n,s,r,a,o,c,l=1/this.direction.x,h=1/this.direction.y,d=1/this.direction.z,u=this.origin;return l>=0?(n=(t.min.x-u.x)*l,s=(t.max.x-u.x)*l):(n=(t.max.x-u.x)*l,s=(t.min.x-u.x)*l),h>=0?(r=(t.min.y-u.y)*h,a=(t.max.y-u.y)*h):(r=(t.max.y-u.y)*h,a=(t.min.y-u.y)*h),n>a||r>s||((r>n||isNaN(n))&&(n=r),(a<s||isNaN(s))&&(s=a),d>=0?(o=(t.min.z-u.z)*d,c=(t.max.z-u.z)*d):(o=(t.max.z-u.z)*d,c=(t.min.z-u.z)*d),n>c||o>s)||((o>n||n!==n)&&(n=o),(c<s||s!==s)&&(s=c),s<0)?null:this.at(n>=0?n:s,e)}intersectsBox(t){return this.intersectBox(t,Pi)!==null}intersectTriangle(t,e,n,s,r){let a=this.origin,o=this.direction,c=o.x,l=o.y,h=o.z,d=t.x-a.x,u=t.y-a.y,f=t.z-a.z,g=e.x-a.x,x=e.y-a.y,p=e.z-a.z,m=n.x-a.x,S=n.y-a.y,E=n.z-a.z,v=Math.abs(c),b=Math.abs(l),M=Math.abs(h),A,_,T,I,L,N,B,D,O,$,J,W;if(v>=b&&v>=M?(T=c,N=d,O=g,W=m,c>=0?(A=l,_=h,I=u,L=f,B=x,D=p,$=S,J=E):(A=h,_=l,I=f,L=u,B=p,D=x,$=E,J=S)):b>=M?(T=l,N=u,O=x,W=S,l>=0?(A=h,_=c,I=f,L=d,B=p,D=g,$=E,J=m):(A=c,_=h,I=d,L=f,B=g,D=p,$=m,J=E)):(T=h,N=f,O=p,W=E,h>=0?(A=c,_=l,I=d,L=u,B=g,D=x,$=m,J=S):(A=l,_=c,I=u,L=d,B=x,D=g,$=S,J=m)),T===0)return null;let G=A/T,K=_/T,nt=1/T,Et=I-G*N,pt=L-K*N,Ft=B-G*O,Dt=D-K*O,ft=$-G*W,U=J-K*W,V=ft*Dt-U*Ft,dt=Et*U-pt*ft,Mt=Ft*pt-Dt*Et;if(s){if(V<0||dt<0||Mt<0)return null}else if((V<0||dt<0||Mt<0)&&(V>0||dt>0||Mt>0))return null;let yt=V+dt+Mt;if(yt===0)return null;let It=nt*(V*N+dt*O+Mt*W);return(yt>0?It<0:It>0)?null:this.at(It/yt,r)}applyMatrix4(t){return this.origin.applyMatrix4(t),this.direction.transformDirection(t),this}equals(t){return t.origin.equals(this.origin)&&t.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}},si=class extends Ui{constructor(t){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new Ot(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new ni,this.combine=Ol,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(t)}copy(t){return super.copy(t),this.color.copy(t.color),this.map=t.map,this.lightMap=t.lightMap,this.lightMapIntensity=t.lightMapIntensity,this.aoMap=t.aoMap,this.aoMapIntensity=t.aoMapIntensity,this.specularMap=t.specularMap,this.alphaMap=t.alphaMap,this.envMap=t.envMap,this.envMapRotation.copy(t.envMapRotation),this.combine=t.combine,this.reflectivity=t.reflectivity,this.refractionRatio=t.refractionRatio,this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this.wireframeLinecap=t.wireframeLinecap,this.wireframeLinejoin=t.wireframeLinejoin,this.fog=t.fog,this}},Jh=new ue,fs=new Wr,Ha=new Un,Kh=new P,Va=new P,Ga=new P,Wa=new P,fl=new P,Xa=new P,Qh=new P,qa=new P,ot=class extends sn{constructor(t=new _e,e=new si){super(),this.isMesh=!0,this.type="Mesh",this.geometry=t,this.material=e,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(t,e){return super.copy(t,e),t.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=t.morphTargetInfluences.slice()),t.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},t.morphTargetDictionary)),this.material=Array.isArray(t.material)?t.material.slice():t.material,this.geometry=t.geometry,this}updateMorphTargets(){let e=this.geometry.morphAttributes,n=Object.keys(e);if(n.length>0){let s=e[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}getVertexPosition(t,e){let n=this.geometry,s=n.attributes.position,r=n.morphAttributes.position,a=n.morphTargetsRelative;e.fromBufferAttribute(s,t);let o=this.morphTargetInfluences;if(r&&o){Xa.set(0,0,0);for(let c=0,l=r.length;c<l;c++){let h=o[c],d=r[c];h!==0&&(fl.fromBufferAttribute(d,t),a?Xa.addScaledVector(fl,h):Xa.addScaledVector(fl.sub(e),h))}e.add(Xa)}return e}intersectsFrustum(t){return t.intersectsObject(this)}raycast(t,e){let n=this.geometry,s=this.material,r=this.matrixWorld;s!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),Ha.copy(n.boundingSphere),Ha.applyMatrix4(r),fs.copy(t.ray).recast(t.near),!(Ha.containsPoint(fs.origin)===!1&&(fs.intersectSphere(Ha,Kh)===null||fs.origin.distanceToSquared(Kh)>(t.far-t.near)**2))&&(Jh.copy(r).invert(),fs.copy(t.ray).applyMatrix4(Jh),!(n.boundingBox!==null&&fs.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(t,e,fs)))}_computeIntersections(t,e,n){let s,r=this.geometry,a=this.material,o=r.index,c=r.attributes.position,l=r.attributes.uv,h=r.attributes.uv1,d=r.attributes.normal,u=r.groups,f=r.drawRange;if(o!==null)if(Array.isArray(a))for(let g=0,x=u.length;g<x;g++){let p=u[g],m=a[p.materialIndex],S=Math.max(p.start,f.start),E=Math.min(o.count,Math.min(p.start+p.count,f.start+f.count));for(let v=S,b=E;v<b;v+=3){let M=o.getX(v),A=o.getX(v+1),_=o.getX(v+2);s=Ya(this,m,t,n,l,h,d,M,A,_),s&&(s.faceIndex=Math.floor(v/3),s.face.materialIndex=p.materialIndex,e.push(s))}}else{let g=Math.max(0,f.start),x=Math.min(o.count,f.start+f.count);for(let p=g,m=x;p<m;p+=3){let S=o.getX(p),E=o.getX(p+1),v=o.getX(p+2);s=Ya(this,a,t,n,l,h,d,S,E,v),s&&(s.faceIndex=Math.floor(p/3),e.push(s))}}else if(c!==void 0)if(Array.isArray(a))for(let g=0,x=u.length;g<x;g++){let p=u[g],m=a[p.materialIndex],S=Math.max(p.start,f.start),E=Math.min(c.count,Math.min(p.start+p.count,f.start+f.count));for(let v=S,b=E;v<b;v+=3){let M=v,A=v+1,_=v+2;s=Ya(this,m,t,n,l,h,d,M,A,_),s&&(s.faceIndex=Math.floor(v/3),s.face.materialIndex=p.materialIndex,e.push(s))}}else{let g=Math.max(0,f.start),x=Math.min(c.count,f.start+f.count);for(let p=g,m=x;p<m;p+=3){let S=p,E=p+1,v=p+2;s=Ya(this,a,t,n,l,h,d,S,E,v),s&&(s.faceIndex=Math.floor(p/3),e.push(s))}}}};function rp(i,t,e,n,s,r,a,o){let c;if(t.side===rn?c=n.intersectTriangle(a,r,s,!0,o):c=n.intersectTriangle(s,r,a,t.side===ns,o),c===null)return null;qa.copy(o),qa.applyMatrix4(i.matrixWorld);let l=e.ray.origin.distanceTo(qa);return l<e.near||l>e.far?null:{distance:l,point:qa.clone(),object:i}}function Ya(i,t,e,n,s,r,a,o,c,l){i.getVertexPosition(o,Va),i.getVertexPosition(c,Ga),i.getVertexPosition(l,Wa);let h=rp(i,t,e,n,Va,Ga,Wa,Qh);if(h){let d=new P;Yi.getBarycoord(Qh,Va,Ga,Wa,d),s&&(h.uv=Yi.getInterpolatedAttribute(s,o,c,l,d,new mt)),r&&(h.uv1=Yi.getInterpolatedAttribute(r,o,c,l,d,new mt)),a&&(h.normal=Yi.getInterpolatedAttribute(a,o,c,l,d,new P),h.normal.dot(n.direction)>0&&h.normal.multiplyScalar(-1));let u={a:o,b:c,c:l,normal:new P,materialIndex:0};Yi.getNormal(Va,Ga,Wa,u.normal),h.face=u,h.barycoord=d}return h}var vs=class extends Mn{constructor(t=null,e=1,n=1,s,r,a,o,c,l=en,h=en,d,u){super(null,a,o,c,l,h,s,r,d,u),this.isDataTexture=!0,this.image={data:t,width:e,height:n},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var Xr=class extends Pe{constructor(t,e,n,s=1){super(t,e,n),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=s}copy(t){return super.copy(t),this.meshPerAttribute=t.meshPerAttribute,this}toJSON(){let t=super.toJSON();return t.meshPerAttribute=this.meshPerAttribute,t.isInstancedBufferAttribute=!0,t}},ks=new ue,tu=new ue,ja=[],eu=new Sn,ap=new ue,Ar=new ot,Rr=new Un,Rn=class extends ot{constructor(t,e,n){super(t,e),this.isInstancedMesh=!0,this.instanceMatrix=new Xr(new Float32Array(n*16),16),this.instanceColor=null,this.morphTexture=null,this.count=n,this.boundingBox=null,this.boundingSphere=null;for(let s=0;s<n;s++)this.setMatrixAt(s,ap)}computeBoundingBox(){let t=this.geometry,e=this.count;this.boundingBox===null&&(this.boundingBox=new Sn),t.boundingBox===null&&t.computeBoundingBox(),this.boundingBox.makeEmpty();for(let n=0;n<e;n++)this.getMatrixAt(n,ks),eu.copy(t.boundingBox).applyMatrix4(ks),this.boundingBox.union(eu)}computeBoundingSphere(){let t=this.geometry,e=this.count;this.boundingSphere===null&&(this.boundingSphere=new Un),t.boundingSphere===null&&t.computeBoundingSphere(),this.boundingSphere.makeEmpty();for(let n=0;n<e;n++)this.getMatrixAt(n,ks),Rr.copy(t.boundingSphere).applyMatrix4(ks),this.boundingSphere.union(Rr)}copy(t,e){return super.copy(t,e),this.instanceMatrix.copy(t.instanceMatrix),t.morphTexture!==null&&(this.morphTexture=t.morphTexture.clone()),t.instanceColor!==null&&(this.instanceColor=t.instanceColor.clone()),this.count=t.count,t.boundingBox!==null&&(this.boundingBox=t.boundingBox.clone()),t.boundingSphere!==null&&(this.boundingSphere=t.boundingSphere.clone()),this}getColorAt(t,e){return this.instanceColor===null?e.setRGB(1,1,1):e.fromArray(this.instanceColor.array,t*3)}getMatrixAt(t,e){return e.fromArray(this.instanceMatrix.array,t*16)}getMorphAt(t,e){let n=e.morphTargetInfluences,s=this.morphTexture.source.data.data,r=n.length+1,a=t*r+1;for(let o=0;o<n.length;o++)n[o]=s[a+o]}raycast(t,e){let n=this.matrixWorld,s=this.count;if(Ar.geometry=this.geometry,Ar.material=this.material,Ar.material!==void 0&&(this.boundingSphere===null&&this.computeBoundingSphere(),Rr.copy(this.boundingSphere),Rr.applyMatrix4(n),t.ray.intersectsSphere(Rr)!==!1))for(let r=0;r<s;r++){this.getMatrixAt(r,ks),tu.multiplyMatrices(n,ks),Ar.matrixWorld=tu,Ar.raycast(t,ja);for(let a=0,o=ja.length;a<o;a++){let c=ja[a];c.instanceId=r,c.object=this,e.push(c)}ja.length=0}}setColorAt(t,e){return this.instanceColor===null&&(this.instanceColor=new Xr(new Float32Array(this.instanceMatrix.count*3).fill(1),3)),e.toArray(this.instanceColor.array,t*3),this}setMatrixAt(t,e){return e.toArray(this.instanceMatrix.array,t*16),this}setMorphAt(t,e){let n=e.morphTargetInfluences,s=n.length+1;this.morphTexture===null&&(this.morphTexture=new vs(new Float32Array(s*this.count),s,this.count,Zo,Gn));let r=this.morphTexture.source.data.data,a=0;for(let l=0;l<n.length;l++)a+=n[l];let o=this.geometry.morphTargetsRelative?1:1-a,c=s*t;return r[c]=o,r.set(n,c+1),this}updateMorphTargets(){}dispose(){super.dispose(),this.morphTexture!==null&&(this.morphTexture.dispose(),this.morphTexture=null)}},ps=new Un,op=new mt(.5,.5),Za=new P,er=class{constructor(t=new Qn,e=new Qn,n=new Qn,s=new Qn,r=new Qn,a=new Qn){this.planes=[t,e,n,s,r,a]}set(t,e,n,s,r,a){let o=this.planes;return o[0].copy(t),o[1].copy(e),o[2].copy(n),o[3].copy(s),o[4].copy(r),o[5].copy(a),this}copy(t){let e=this.planes;for(let n=0;n<6;n++)e[n].copy(t.planes[n]);return this}setFromProjectionMatrix(t,e=ei,n=!1){let s=this.planes,r=t.elements,a=r[0],o=r[1],c=r[2],l=r[3],h=r[4],d=r[5],u=r[6],f=r[7],g=r[8],x=r[9],p=r[10],m=r[11],S=r[12],E=r[13],v=r[14],b=r[15];if(s[0].setComponents(l-a,f-h,m-g,b-S).normalize(),s[1].setComponents(l+a,f+h,m+g,b+S).normalize(),s[2].setComponents(l+o,f+d,m+x,b+E).normalize(),s[3].setComponents(l-o,f-d,m-x,b-E).normalize(),n)s[4].setComponents(c,u,p,v).normalize(),s[5].setComponents(l-c,f-u,m-p,b-v).normalize();else if(s[4].setComponents(l-c,f-u,m-p,b-v).normalize(),e===ei)s[5].setComponents(l+c,f+u,m+p,b+v).normalize();else if(e===Zs)s[5].setComponents(c,u,p,v).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+e);return this}intersectsObject(t){if(t.boundingSphere!==void 0)t.boundingSphere===null&&t.computeBoundingSphere(),ps.copy(t.boundingSphere).applyMatrix4(t.matrixWorld);else{let e=t.geometry;e.boundingSphere===null&&e.computeBoundingSphere(),ps.copy(e.boundingSphere).applyMatrix4(t.matrixWorld)}return this.intersectsSphere(ps)}intersectsSprite(t){ps.center.set(0,0,0);let e=op.distanceTo(t.center);return ps.radius=.7071067811865476+e,ps.applyMatrix4(t.matrixWorld),this.intersectsSphere(ps)}intersectsSphere(t){let e=this.planes,n=t.center,s=-t.radius;for(let r=0;r<6;r++)if(e[r].distanceToPoint(n)<s)return!1;return!0}intersectsBox(t){let e=this.planes;for(let n=0;n<6;n++){let s=e[n];if(Za.x=s.normal.x>0?t.max.x:t.min.x,Za.y=s.normal.y>0?t.max.y:t.min.y,Za.z=s.normal.z>0?t.max.z:t.min.z,s.distanceToPoint(Za)<0)return!1}return!0}containsPoint(t){let e=this.planes;for(let n=0;n<6;n++)if(e[n].distanceToPoint(t)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}};var _o=class extends Ui{constructor(t){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new Ot(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(t)}copy(t){return super.copy(t),this.color.copy(t.color),this.map=t.map,this.alphaMap=t.alphaMap,this.size=t.size,this.sizeAttenuation=t.sizeAttenuation,this.fog=t.fog,this}},nu=new ue,El=new Wr,$a=new Un,Ja=new P,qr=class extends sn{constructor(t=new _e,e=new _o){super(),this.isPoints=!0,this.type="Points",this.geometry=t,this.material=e,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(t,e){return super.copy(t,e),this.material=Array.isArray(t.material)?t.material.slice():t.material,this.geometry=t.geometry,this}intersectsFrustum(t){return t.intersectsObject(this)}raycast(t,e){let n=this.geometry,s=this.matrixWorld,r=t.params.Points.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),$a.copy(n.boundingSphere),$a.applyMatrix4(s),$a.radius+=r,t.ray.intersectsSphere($a)===!1)return;nu.copy(s).invert(),El.copy(t.ray).applyMatrix4(nu);let o=r/((this.scale.x+this.scale.y+this.scale.z)/3),c=o*o,l=n.index,d=n.attributes.position;if(l!==null){let u=Math.max(0,a.start),f=Math.min(l.count,a.start+a.count);for(let g=u,x=f;g<x;g++){let p=l.getX(g);Ja.fromBufferAttribute(d,p),iu(Ja,p,c,s,t,e,this)}}else{let u=Math.max(0,a.start),f=Math.min(d.count,a.start+a.count);for(let g=u,x=f;g<x;g++)Ja.fromBufferAttribute(d,g),iu(Ja,g,c,s,t,e,this)}}updateMorphTargets(){let e=this.geometry.morphAttributes,n=Object.keys(e);if(n.length>0){let s=e[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}};function iu(i,t,e,n,s,r,a){let o=El.distanceSqToPoint(i);if(o<e){let c=new P;El.closestPointToPoint(i,c),c.applyMatrix4(n);let l=s.ray.origin.distanceTo(c);if(l<s.near||l>s.far)return;r.push({distance:l,distanceToRay:Math.sqrt(o),point:c,index:t,face:null,faceIndex:null,barycoord:null,object:a})}}var Yr=class extends Mn{constructor(t=[],e=ss,n,s,r,a,o,c,l,h){super(t,e,n,s,r,a,o,c,l,h),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(t){this.image=t}},jr=class extends Mn{constructor(t,e,n,s,r,a,o,c,l){super(t,e,n,s,r,a,o,c,l),this.isCanvasTexture=!0,this.needsUpdate=!0}};var ji=class extends Mn{constructor(t,e,n=ai,s,r,a,o=en,c=en,l,h=di,d=1){if(h!==di&&h!==as)throw new Error("THREE.DepthTexture: format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let u={width:t,height:e,depth:d};super(u,s,r,a,o,c,h,n,l),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(t){return super.copy(t),this.source=new Ks(Object.assign({},t.image)),this.compareFunction=t.compareFunction,this}toJSON(t){let e=super.toJSON(t);return e.compareFunction=this.compareFunction,e}},yo=class extends ji{constructor(t,e=ai,n=ss,s,r,a=en,o=en,c,l=di){let h={width:t,height:t,depth:1},d=[h,h,h,h,h,h];super(t,t,e,n,s,r,a,o,c,l),this.image=d,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(t){this.image=t}},Zr=class extends Mn{constructor(t=null){super(),this.sourceTexture=t,this.isExternalTexture=!0}copy(t){return super.copy(t),this.sourceTexture=t.sourceTexture,this}},Re=class i extends _e{constructor(t=1,e=1,n=1,s=1,r=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:t,height:e,depth:n,widthSegments:s,heightSegments:r,depthSegments:a};let o=this;s=Math.floor(s),r=Math.floor(r),a=Math.floor(a);let c=[],l=[],h=[],d=[],u=0,f=0;g("z","y","x",-1,-1,n,e,t,a,r,0),g("z","y","x",1,-1,n,e,-t,a,r,1),g("x","z","y",1,1,t,n,e,s,a,2),g("x","z","y",1,-1,t,n,-e,s,a,3),g("x","y","z",1,-1,t,e,n,s,r,4),g("x","y","z",-1,-1,t,e,-n,s,r,5),this.setIndex(c),this.setAttribute("position",new Jt(l,3)),this.setAttribute("normal",new Jt(h,3)),this.setAttribute("uv",new Jt(d,2));function g(x,p,m,S,E,v,b,M,A,_,T){let I=v/A,L=b/_,N=v/2,B=b/2,D=M/2,O=A+1,$=_+1,J=0,W=0,G=new P;for(let K=0;K<$;K++){let nt=K*L-B;for(let Et=0;Et<O;Et++){let pt=Et*I-N;G[x]=pt*S,G[p]=nt*E,G[m]=D,l.push(G.x,G.y,G.z),G[x]=0,G[p]=0,G[m]=M>0?1:-1,h.push(G.x,G.y,G.z),d.push(Et/A),d.push(1-K/_),J+=1}}for(let K=0;K<_;K++)for(let nt=0;nt<A;nt++){let Et=u+nt+O*K,pt=u+nt+O*(K+1),Ft=u+(nt+1)+O*(K+1),Dt=u+(nt+1)+O*K;c.push(Et,pt,Dt),c.push(pt,Ft,Dt),W+=6}o.addGroup(f,W,T),f+=W,u+=J}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.width,t.height,t.depth,t.widthSegments,t.heightSegments,t.depthSegments)}};var pi=class i extends _e{constructor(t=1,e=32,n=0,s=Math.PI*2){super(),this.type="CircleGeometry",this.parameters={radius:t,segments:e,thetaStart:n,thetaLength:s},e=Math.max(3,e);let r=[],a=[],o=[],c=[],l=new P,h=new mt;a.push(0,0,0),o.push(0,0,1),c.push(.5,.5);for(let d=0,u=3;d<=e;d++,u+=3){let f=n+d/e*s;l.x=t*Math.cos(f),l.y=t*Math.sin(f),a.push(l.x,l.y,l.z),o.push(0,0,1),h.x=(a[u]/t+1)/2,h.y=(a[u+1]/t+1)/2,c.push(h.x,h.y)}for(let d=1;d<=e;d++)r.push(d,d+1,0);this.setIndex(r),this.setAttribute("position",new Jt(a,3)),this.setAttribute("normal",new Jt(o,3)),this.setAttribute("uv",new Jt(c,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.radius,t.segments,t.thetaStart,t.thetaLength)}},ge=class i extends _e{constructor(t=1,e=1,n=1,s=32,r=1,a=!1,o=0,c=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:t,radiusBottom:e,height:n,radialSegments:s,heightSegments:r,openEnded:a,thetaStart:o,thetaLength:c};let l=this;s=Math.floor(s),r=Math.floor(r);let h=[],d=[],u=[],f=[],g=0,x=[],p=n/2,m=0;S(),a===!1&&(t>0&&E(!0),e>0&&E(!1)),this.setIndex(h),this.setAttribute("position",new Jt(d,3)),this.setAttribute("normal",new Jt(u,3)),this.setAttribute("uv",new Jt(f,2));function S(){let v=new P,b=new P,M=0,A=(e-t)/n;for(let _=0;_<=r;_++){let T=[],I=_/r,L=I*(e-t)+t;for(let N=0;N<=s;N++){let B=N/s,D=B*c+o,O=Math.sin(D),$=Math.cos(D);b.x=L*O,b.y=-I*n+p,b.z=L*$,d.push(b.x,b.y,b.z),v.set(O,A,$).normalize(),u.push(v.x,v.y,v.z),f.push(B,1-I),T.push(g++)}x.push(T)}for(let _=0;_<s;_++)for(let T=0;T<r;T++){let I=x[T][_],L=x[T+1][_],N=x[T+1][_+1],B=x[T][_+1];(t>0||T!==0)&&(h.push(I,L,B),M+=3),(e>0||T!==r-1)&&(h.push(L,N,B),M+=3)}l.addGroup(m,M,0),m+=M}function E(v){let b=g,M=new mt,A=new P,_=0,T=v===!0?t:e,I=v===!0?1:-1;for(let N=1;N<=s;N++)d.push(0,p*I,0),u.push(0,I,0),f.push(.5,.5),g++;let L=g;for(let N=0;N<=s;N++){let D=N/s*c+o,O=Math.cos(D),$=Math.sin(D);A.x=T*$,A.y=p*I,A.z=T*O,d.push(A.x,A.y,A.z),u.push(0,I,0),M.x=O*.5+.5,M.y=$*.5*I+.5,f.push(M.x,M.y),g++}for(let N=0;N<s;N++){let B=b+N,D=L+N;v===!0?h.push(D,D+1,B):h.push(D+1,D,B),_+=3}l.addGroup(m,_,v===!0?1:2),m+=_}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.radiusTop,t.radiusBottom,t.height,t.radialSegments,t.heightSegments,t.openEnded,t.thetaStart,t.thetaLength)}},Zi=class i extends ge{constructor(t=1,e=1,n=32,s=1,r=!1,a=0,o=Math.PI*2){super(0,t,e,n,s,r,a,o),this.type="ConeGeometry",this.parameters={radius:t,height:e,radialSegments:n,heightSegments:s,openEnded:r,thetaStart:a,thetaLength:o}}static fromJSON(t){return new i(t.radius,t.height,t.radialSegments,t.heightSegments,t.openEnded,t.thetaStart,t.thetaLength)}},Mo=class i extends _e{constructor(t=[],e=[],n=1,s=0){super(),this.type="PolyhedronGeometry",this.parameters={vertices:t,indices:e,radius:n,detail:s};let r=[],a=[];o(s),l(n),h(),this.setAttribute("position",new Jt(r,3)),this.setAttribute("normal",new Jt(r.slice(),3)),this.setAttribute("uv",new Jt(a,2)),s===0?this.computeVertexNormals():this.normalizeNormals();function o(S){let E=new P,v=new P,b=new P;for(let M=0;M<e.length;M+=3)f(e[M+0],E),f(e[M+1],v),f(e[M+2],b),c(E,v,b,S)}function c(S,E,v,b){let M=b+1,A=[];for(let _=0;_<=M;_++){A[_]=[];let T=S.clone().lerp(v,_/M),I=E.clone().lerp(v,_/M),L=M-_;for(let N=0;N<=L;N++)N===0&&_===M?A[_][N]=T:A[_][N]=T.clone().lerp(I,N/L)}for(let _=0;_<M;_++)for(let T=0;T<2*(M-_)-1;T++){let I=Math.floor(T/2);T%2===0?(u(A[_][I+1]),u(A[_+1][I]),u(A[_][I])):(u(A[_][I+1]),u(A[_+1][I+1]),u(A[_+1][I]))}}function l(S){let E=new P;for(let v=0;v<r.length;v+=3)E.x=r[v+0],E.y=r[v+1],E.z=r[v+2],E.normalize().multiplyScalar(S),r[v+0]=E.x,r[v+1]=E.y,r[v+2]=E.z}function h(){let S=new P;for(let E=0;E<r.length;E+=3){S.x=r[E+0],S.y=r[E+1],S.z=r[E+2];let v=p(S)/2/Math.PI+.5,b=m(S)/Math.PI+.5;a.push(v,1-b)}g(),d()}function d(){for(let S=0;S<a.length;S+=6){let E=a[S+0],v=a[S+2],b=a[S+4],M=Math.max(E,v,b),A=Math.min(E,v,b);M>.9&&A<.1&&(E<.2&&(a[S+0]+=1),v<.2&&(a[S+2]+=1),b<.2&&(a[S+4]+=1))}}function u(S){r.push(S.x,S.y,S.z)}function f(S,E){let v=S*3;E.x=t[v+0],E.y=t[v+1],E.z=t[v+2]}function g(){let S=new P,E=new P,v=new P,b=new P,M=new mt,A=new mt,_=new mt;for(let T=0,I=0;T<r.length;T+=9,I+=6){S.set(r[T+0],r[T+1],r[T+2]),E.set(r[T+3],r[T+4],r[T+5]),v.set(r[T+6],r[T+7],r[T+8]),M.set(a[I+0],a[I+1]),A.set(a[I+2],a[I+3]),_.set(a[I+4],a[I+5]),b.copy(S).add(E).add(v).divideScalar(3);let L=p(b);x(M,I+0,S,L),x(A,I+2,E,L),x(_,I+4,v,L)}}function x(S,E,v,b){b<0&&S.x===1&&(a[E]=S.x-1),v.x===0&&v.z===0&&(a[E]=b/2/Math.PI+.5)}function p(S){return Math.atan2(S.z,-S.x)}function m(S){return Math.atan2(-S.y,Math.sqrt(S.x*S.x+S.z*S.z))}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.vertices,t.indices,t.radius,t.detail)}};var Nn=class{constructor(){this.type="Curve",this.arcLengthDivisions=200,this.needsUpdate=!1,this.cacheArcLengths=null}getPoint(){ee("Curve: .getPoint() not implemented.")}getPointAt(t,e){let n=this.getUtoTmapping(t);return this.getPoint(n,e)}getPoints(t=5){let e=[];for(let n=0;n<=t;n++)e.push(this.getPoint(n/t));return e}getSpacedPoints(t=5){let e=[];for(let n=0;n<=t;n++)e.push(this.getPointAt(n/t));return e}getLength(){let t=this.getLengths();return t[t.length-1]}getLengths(t=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===t+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;let e=[],n,s=this.getPoint(0),r=0;e.push(0);for(let a=1;a<=t;a++)n=this.getPoint(a/t),r+=n.distanceTo(s),e.push(r),s=n;return this.cacheArcLengths=e,e}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(t,e=null){let n=this.getLengths(),s=0,r=n.length,a;e?a=e:a=t*n[r-1];let o=0,c=r-1,l;for(;o<=c;)if(s=Math.floor(o+(c-o)/2),l=n[s]-a,l<0)o=s+1;else if(l>0)c=s-1;else{c=s;break}if(s=c,n[s]===a)return s/(r-1);let h=n[s],u=n[s+1]-h,f=(a-h)/u;return(s+f)/(r-1)}getTangent(t,e){let s=t-1e-4,r=t+1e-4;s<0&&(s=0),r>1&&(r=1);let a=this.getPoint(s),o=this.getPoint(r),c=e||(a.isVector2?new mt:new P);return c.copy(o).sub(a).normalize(),c}getTangentAt(t,e){let n=this.getUtoTmapping(t);return this.getTangent(n,e)}computeFrenetFrames(t,e=!1){let n=new P,s=[],r=[],a=[],o=new P,c=new ue;for(let f=0;f<=t;f++){let g=f/t;s[f]=this.getTangentAt(g,new P)}r[0]=new P,a[0]=new P;let l=Number.MAX_VALUE,h=Math.abs(s[0].x),d=Math.abs(s[0].y),u=Math.abs(s[0].z);h<=l&&(l=h,n.set(1,0,0)),d<=l&&(l=d,n.set(0,1,0)),u<=l&&n.set(0,0,1),o.crossVectors(s[0],n).normalize(),r[0].crossVectors(s[0],o),a[0].crossVectors(s[0],r[0]);for(let f=1;f<=t;f++){if(r[f]=r[f-1].clone(),a[f]=a[f-1].clone(),o.crossVectors(s[f-1],s[f]),o.length()>Number.EPSILON){o.normalize();let g=Math.acos(ae(s[f-1].dot(s[f]),-1,1));r[f].applyMatrix4(c.makeRotationAxis(o,g))}a[f].crossVectors(s[f],r[f])}if(e===!0){let f=Math.acos(ae(r[0].dot(r[t]),-1,1));f/=t,s[0].dot(o.crossVectors(r[0],r[t]))>0&&(f=-f);for(let g=1;g<=t;g++)r[g].applyMatrix4(c.makeRotationAxis(s[g],f*g)),a[g].crossVectors(s[g],r[g])}return{tangents:s,normals:r,binormals:a}}clone(){return new this.constructor().copy(this)}copy(t){return this.arcLengthDivisions=t.arcLengthDivisions,this}toJSON(){let t={metadata:{version:4.7,type:"Curve",generator:"Curve.toJSON"}};return t.arcLengthDivisions=this.arcLengthDivisions,t.type=this.type,t}fromJSON(t){return this.arcLengthDivisions=t.arcLengthDivisions,this}},nr=class extends Nn{constructor(t=0,e=0,n=1,s=1,r=0,a=Math.PI*2,o=!1,c=0){super(),this.isEllipseCurve=!0,this.type="EllipseCurve",this.aX=t,this.aY=e,this.xRadius=n,this.yRadius=s,this.aStartAngle=r,this.aEndAngle=a,this.aClockwise=o,this.aRotation=c}getPoint(t,e=new mt){let n=e,s=Math.PI*2,r=this.aEndAngle-this.aStartAngle,a=Math.abs(r)<Number.EPSILON;for(;r<0;)r+=s;for(;r>s;)r-=s;r<Number.EPSILON&&(a?r=0:r=s),this.aClockwise===!0&&!a&&(r===s?r=-s:r=r-s);let o=this.aStartAngle+t*r,c=this.aX+this.xRadius*Math.cos(o),l=this.aY+this.yRadius*Math.sin(o);if(this.aRotation!==0){let h=Math.cos(this.aRotation),d=Math.sin(this.aRotation),u=c-this.aX,f=l-this.aY;c=u*h-f*d+this.aX,l=u*d+f*h+this.aY}return n.set(c,l)}copy(t){return super.copy(t),this.aX=t.aX,this.aY=t.aY,this.xRadius=t.xRadius,this.yRadius=t.yRadius,this.aStartAngle=t.aStartAngle,this.aEndAngle=t.aEndAngle,this.aClockwise=t.aClockwise,this.aRotation=t.aRotation,this}toJSON(){let t=super.toJSON();return t.aX=this.aX,t.aY=this.aY,t.xRadius=this.xRadius,t.yRadius=this.yRadius,t.aStartAngle=this.aStartAngle,t.aEndAngle=this.aEndAngle,t.aClockwise=this.aClockwise,t.aRotation=this.aRotation,t}fromJSON(t){return super.fromJSON(t),this.aX=t.aX,this.aY=t.aY,this.xRadius=t.xRadius,this.yRadius=t.yRadius,this.aStartAngle=t.aStartAngle,this.aEndAngle=t.aEndAngle,this.aClockwise=t.aClockwise,this.aRotation=t.aRotation,this}},So=class extends nr{constructor(t,e,n,s,r,a){super(t,e,n,n,s,r,a),this.isArcCurve=!0,this.type="ArcCurve"}};function eh(){let i=0,t=0,e=0,n=0;function s(r,a,o,c){i=r,t=o,e=-3*r+3*a-2*o-c,n=2*r-2*a+o+c}return{initCatmullRom:function(r,a,o,c,l){s(a,o,l*(o-r),l*(c-a))},initNonuniformCatmullRom:function(r,a,o,c,l,h,d){let u=(a-r)/l-(o-r)/(l+h)+(o-a)/h,f=(o-a)/h-(c-a)/(h+d)+(c-o)/d;u*=h,f*=h,s(a,o,u,f)},calc:function(r){let a=r*r,o=a*r;return i+t*r+e*a+n*o}}}var su=new P,ru=new P,pl=new eh,ml=new eh,gl=new eh,$i=class extends Nn{constructor(t=[],e=!1,n="centripetal",s=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=t,this.closed=e,this.curveType=n,this.tension=s}getPoint(t,e=new P){let n=e,s=this.points,r=s.length,a=(r-(this.closed?0:1))*t,o=Math.floor(a),c=a-o;this.closed?o+=o>0?0:(Math.floor(Math.abs(o)/r)+1)*r:c===0&&o===r-1&&(o=r-2,c=1);let l,h;this.closed||o>0?l=s[(o-1)%r]:(ru.subVectors(s[0],s[1]).add(s[0]),l=ru);let d=s[o%r],u=s[(o+1)%r];if(this.closed||o+2<r?h=s[(o+2)%r]:(su.subVectors(s[r-1],s[r-2]).add(s[r-1]),h=su),this.curveType==="centripetal"||this.curveType==="chordal"){let f=this.curveType==="chordal"?.5:.25,g=Math.pow(l.distanceToSquared(d),f),x=Math.pow(d.distanceToSquared(u),f),p=Math.pow(u.distanceToSquared(h),f);x<1e-4&&(x=1),g<1e-4&&(g=x),p<1e-4&&(p=x),pl.initNonuniformCatmullRom(l.x,d.x,u.x,h.x,g,x,p),ml.initNonuniformCatmullRom(l.y,d.y,u.y,h.y,g,x,p),gl.initNonuniformCatmullRom(l.z,d.z,u.z,h.z,g,x,p)}else this.curveType==="catmullrom"&&(pl.initCatmullRom(l.x,d.x,u.x,h.x,this.tension),ml.initCatmullRom(l.y,d.y,u.y,h.y,this.tension),gl.initCatmullRom(l.z,d.z,u.z,h.z,this.tension));return n.set(pl.calc(c),ml.calc(c),gl.calc(c)),n}copy(t){super.copy(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let s=t.points[e];this.points.push(s.clone())}return this.closed=t.closed,this.curveType=t.curveType,this.tension=t.tension,this}toJSON(){let t=super.toJSON();t.points=[];for(let e=0,n=this.points.length;e<n;e++){let s=this.points[e];t.points.push(s.toArray())}return t.closed=this.closed,t.curveType=this.curveType,t.tension=this.tension,t}fromJSON(t){super.fromJSON(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let s=t.points[e];this.points.push(new P().fromArray(s))}return this.closed=t.closed,this.curveType=t.curveType,this.tension=t.tension,this}};function au(i,t,e,n,s){let r=(n-t)*.5,a=(s-e)*.5,o=i*i,c=i*o;return(2*e-2*n+r+a)*c+(-3*e+3*n-2*r-a)*o+r*i+e}function cp(i,t){let e=1-i;return e*e*t}function lp(i,t){return 2*(1-i)*i*t}function hp(i,t){return i*i*t}function Lr(i,t,e,n){return cp(i,t)+lp(i,e)+hp(i,n)}function up(i,t){let e=1-i;return e*e*e*t}function dp(i,t){let e=1-i;return 3*e*e*i*t}function fp(i,t){return 3*(1-i)*i*i*t}function pp(i,t){return i*i*i*t}function Dr(i,t,e,n,s){return up(i,t)+dp(i,e)+fp(i,n)+pp(i,s)}var $r=class extends Nn{constructor(t=new mt,e=new mt,n=new mt,s=new mt){super(),this.isCubicBezierCurve=!0,this.type="CubicBezierCurve",this.v0=t,this.v1=e,this.v2=n,this.v3=s}getPoint(t,e=new mt){let n=e,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(Dr(t,s.x,r.x,a.x,o.x),Dr(t,s.y,r.y,a.y,o.y)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this.v3.copy(t.v3),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t.v3=this.v3.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this.v3.fromArray(t.v3),this}},bo=class extends Nn{constructor(t=new P,e=new P,n=new P,s=new P){super(),this.isCubicBezierCurve3=!0,this.type="CubicBezierCurve3",this.v0=t,this.v1=e,this.v2=n,this.v3=s}getPoint(t,e=new P){let n=e,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(Dr(t,s.x,r.x,a.x,o.x),Dr(t,s.y,r.y,a.y,o.y),Dr(t,s.z,r.z,a.z,o.z)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this.v3.copy(t.v3),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t.v3=this.v3.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this.v3.fromArray(t.v3),this}},Jr=class extends Nn{constructor(t=new mt,e=new mt){super(),this.isLineCurve=!0,this.type="LineCurve",this.v1=t,this.v2=e}getPoint(t,e=new mt){let n=e;return t===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(t).add(this.v1)),n}getPointAt(t,e){return this.getPoint(t,e)}getTangent(t,e=new mt){return e.subVectors(this.v2,this.v1).normalize()}getTangentAt(t,e){return this.getTangent(t,e)}copy(t){return super.copy(t),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},Eo=class extends Nn{constructor(t=new P,e=new P){super(),this.isLineCurve3=!0,this.type="LineCurve3",this.v1=t,this.v2=e}getPoint(t,e=new P){let n=e;return t===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(t).add(this.v1)),n}getPointAt(t,e){return this.getPoint(t,e)}getTangent(t,e=new P){return e.subVectors(this.v2,this.v1).normalize()}getTangentAt(t,e){return this.getTangent(t,e)}copy(t){return super.copy(t),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},Kr=class extends Nn{constructor(t=new mt,e=new mt,n=new mt){super(),this.isQuadraticBezierCurve=!0,this.type="QuadraticBezierCurve",this.v0=t,this.v1=e,this.v2=n}getPoint(t,e=new mt){let n=e,s=this.v0,r=this.v1,a=this.v2;return n.set(Lr(t,s.x,r.x,a.x),Lr(t,s.y,r.y,a.y)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},wo=class extends Nn{constructor(t=new P,e=new P,n=new P){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=t,this.v1=e,this.v2=n}getPoint(t,e=new P){let n=e,s=this.v0,r=this.v1,a=this.v2;return n.set(Lr(t,s.x,r.x,a.x),Lr(t,s.y,r.y,a.y),Lr(t,s.z,r.z,a.z)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},Qr=class extends Nn{constructor(t=[]){super(),this.isSplineCurve=!0,this.type="SplineCurve",this.points=t}getPoint(t,e=new mt){let n=e,s=this.points,r=(s.length-1)*t,a=Math.floor(r),o=r-a,c=s[a===0?a:a-1],l=s[a],h=s[a>s.length-2?s.length-1:a+1],d=s[a>s.length-3?s.length-1:a+2];return n.set(au(o,c.x,l.x,h.x,d.x),au(o,c.y,l.y,h.y,d.y)),n}copy(t){super.copy(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let s=t.points[e];this.points.push(s.clone())}return this}toJSON(){let t=super.toJSON();t.points=[];for(let e=0,n=this.points.length;e<n;e++){let s=this.points[e];t.points.push(s.toArray())}return t}fromJSON(t){super.fromJSON(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let s=t.points[e];this.points.push(new mt().fromArray(s))}return this}},wl=Object.freeze({__proto__:null,ArcCurve:So,CatmullRomCurve3:$i,CubicBezierCurve:$r,CubicBezierCurve3:bo,EllipseCurve:nr,LineCurve:Jr,LineCurve3:Eo,QuadraticBezierCurve:Kr,QuadraticBezierCurve3:wo,SplineCurve:Qr}),To=class extends Nn{constructor(){super(),this.type="CurvePath",this.curves=[],this.autoClose=!1}add(t){this.curves.push(t)}closePath(){let t=this.curves[0].getPoint(0),e=this.curves[this.curves.length-1].getPoint(1);if(!t.equals(e)){let n=t.isVector2===!0?"LineCurve":"LineCurve3";this.curves.push(new wl[n](e,t))}return this}getPoint(t,e){let n=t*this.getLength(),s=this.getCurveLengths(),r=0;for(;r<s.length;){if(s[r]>=n){let a=s[r]-n,o=this.curves[r],c=o.getLength(),l=c===0?0:1-a/c;return o.getPointAt(l,e)}r++}return null}getLength(){let t=this.getCurveLengths();return t[t.length-1]}updateArcLengths(){this.needsUpdate=!0,this.cacheLengths=null,this.getCurveLengths()}getCurveLengths(){if(this.cacheLengths&&this.cacheLengths.length===this.curves.length)return this.cacheLengths;let t=[],e=0;for(let n=0,s=this.curves.length;n<s;n++)e+=this.curves[n].getLength(),t.push(e);return this.cacheLengths=t,t}getSpacedPoints(t=40){let e=[];for(let n=0;n<=t;n++)e.push(this.getPoint(n/t));return this.autoClose&&e.push(e[0]),e}getPoints(t=12){let e=[],n;for(let s=0,r=this.curves;s<r.length;s++){let a=r[s],o=a.isEllipseCurve?t*2:a.isLineCurve||a.isLineCurve3?1:a.isSplineCurve?t*a.points.length:t,c=a.getPoints(o);for(let l=0;l<c.length;l++){let h=c[l];n&&n.equals(h)||(e.push(h),n=h)}}return this.autoClose&&e.length>1&&!e[e.length-1].equals(e[0])&&e.push(e[0]),e}copy(t){super.copy(t),this.curves=[];for(let e=0,n=t.curves.length;e<n;e++){let s=t.curves[e];this.curves.push(s.clone())}return this.autoClose=t.autoClose,this}toJSON(){let t=super.toJSON();t.autoClose=this.autoClose,t.curves=[];for(let e=0,n=this.curves.length;e<n;e++){let s=this.curves[e];t.curves.push(s.toJSON())}return t}fromJSON(t){super.fromJSON(t),this.autoClose=t.autoClose,this.curves=[];for(let e=0,n=t.curves.length;e<n;e++){let s=t.curves[e];this.curves.push(new wl[s.type]().fromJSON(s))}return this}},ta=class extends To{constructor(t){super(),this.type="Path",this.currentPoint=new mt,t&&this.setFromPoints(t)}setFromPoints(t){this.moveTo(t[0].x,t[0].y);for(let e=1,n=t.length;e<n;e++)this.lineTo(t[e].x,t[e].y);return this}moveTo(t,e){return this.currentPoint.set(t,e),this}lineTo(t,e){let n=new Jr(this.currentPoint.clone(),new mt(t,e));return this.curves.push(n),this.currentPoint.set(t,e),this}quadraticCurveTo(t,e,n,s){let r=new Kr(this.currentPoint.clone(),new mt(t,e),new mt(n,s));return this.curves.push(r),this.currentPoint.set(n,s),this}bezierCurveTo(t,e,n,s,r,a){let o=new $r(this.currentPoint.clone(),new mt(t,e),new mt(n,s),new mt(r,a));return this.curves.push(o),this.currentPoint.set(r,a),this}splineThru(t){let e=[this.currentPoint.clone()].concat(t),n=new Qr(e);return this.curves.push(n),this.currentPoint.copy(t[t.length-1]),this}arc(t,e,n,s,r,a){let o=this.currentPoint.x,c=this.currentPoint.y;return this.absarc(t+o,e+c,n,s,r,a),this}absarc(t,e,n,s,r,a){return this.absellipse(t,e,n,n,s,r,a),this}ellipse(t,e,n,s,r,a,o,c){let l=this.currentPoint.x,h=this.currentPoint.y;return this.absellipse(t+l,e+h,n,s,r,a,o,c),this}absellipse(t,e,n,s,r,a,o,c){let l=new nr(t,e,n,s,r,a,o,c);if(this.curves.length>0){let d=l.getPoint(0);d.equals(this.currentPoint)||this.lineTo(d.x,d.y)}this.curves.push(l);let h=l.getPoint(1);return this.currentPoint.copy(h),this}copy(t){return super.copy(t),this.currentPoint.copy(t.currentPoint),this}toJSON(){let t=super.toJSON();return t.currentPoint=this.currentPoint.toArray(),t}fromJSON(t){return super.fromJSON(t),this.currentPoint.fromArray(t.currentPoint),this}},mi=class extends ta{constructor(t){super(t),this.uuid=ui(),this.type="Shape",this.holes=[]}getPointsHoles(t){let e=[];for(let n=0,s=this.holes.length;n<s;n++)e[n]=this.holes[n].getPoints(t);return e}extractPoints(t){return{shape:this.getPoints(t),holes:this.getPointsHoles(t)}}copy(t){super.copy(t),this.holes=[];for(let e=0,n=t.holes.length;e<n;e++){let s=t.holes[e];this.holes.push(s.clone())}return this}toJSON(){let t=super.toJSON();t.uuid=this.uuid,t.holes=[];for(let e=0,n=this.holes.length;e<n;e++){let s=this.holes[e];t.holes.push(s.toJSON())}return t}fromJSON(t){super.fromJSON(t),this.uuid=t.uuid,this.holes=[];for(let e=0,n=t.holes.length;e<n;e++){let s=t.holes[e];this.holes.push(new ta().fromJSON(s))}return this}};function mp(i,t,e=2){let n=t&&t.length,s=n?t[0]*e:i.length,r=nd(i,0,s,e,!0),a=[];if(!r||r.next===r.prev)return a;let o,c,l;if(n&&(r=yp(i,t,r,e)),i.length>80*e){o=i[0],c=i[1];let h=o,d=c;for(let u=e;u<s;u+=e){let f=i[u],g=i[u+1];f<o&&(o=f),g<c&&(c=g),f>h&&(h=f),g>d&&(d=g)}l=Math.max(h-o,d-c),l=l!==0?32767/l:0}return ea(r,a,e,o,c,l,0),a}function nd(i,t,e,n,s){let r;if(s===Ip(i,t,e,n)>0)for(let a=t;a<e;a+=n)r=ou(a/n|0,i[a],i[a+1],r);else for(let a=e-n;a>=t;a-=n)r=ou(a/n|0,i[a],i[a+1],r);return r&&ir(r,r.next)&&(ia(r),r=r.next),r}function xs(i,t){if(!i)return i;t||(t=i);let e=i,n;do if(n=!1,!e.steiner&&(ir(e,e.next)||He(e.prev,e,e.next)===0)){if(ia(e),e=t=e.prev,e===e.next)break;n=!0}else e=e.next;while(n||e!==t);return t}function ea(i,t,e,n,s,r,a){if(!i)return;!a&&r&&wp(i,n,s,r);let o=i;for(;i.prev!==i.next;){let c=i.prev,l=i.next;if(r?vp(i,n,s,r):gp(i)){t.push(c.i,i.i,l.i),ia(i),i=l.next,o=l.next;continue}if(i=l,i===o){a?a===1?(i=xp(xs(i),t),ea(i,t,e,n,s,r,2)):a===2&&_p(i,t,e,n,s,r):ea(xs(i),t,e,n,s,r,1);break}}}function gp(i){let t=i.prev,e=i,n=i.next;if(He(t,e,n)>=0)return!1;let s=t.x,r=e.x,a=n.x,o=t.y,c=e.y,l=n.y,h=Math.min(s,r,a),d=Math.min(o,c,l),u=Math.max(s,r,a),f=Math.max(o,c,l),g=n.next;for(;g!==t;){if(g.x>=h&&g.x<=u&&g.y>=d&&g.y<=f&&Cr(s,o,r,c,a,l,g.x,g.y)&&He(g.prev,g,g.next)>=0)return!1;g=g.next}return!0}function vp(i,t,e,n){let s=i.prev,r=i,a=i.next;if(He(s,r,a)>=0)return!1;let o=s.x,c=r.x,l=a.x,h=s.y,d=r.y,u=a.y,f=Math.min(o,c,l),g=Math.min(h,d,u),x=Math.max(o,c,l),p=Math.max(h,d,u),m=Tl(f,g,t,e,n),S=Tl(x,p,t,e,n),E=i.prevZ,v=i.nextZ;for(;E&&E.z>=m&&v&&v.z<=S;){if(E.x>=f&&E.x<=x&&E.y>=g&&E.y<=p&&E!==s&&E!==a&&Cr(o,h,c,d,l,u,E.x,E.y)&&He(E.prev,E,E.next)>=0||(E=E.prevZ,v.x>=f&&v.x<=x&&v.y>=g&&v.y<=p&&v!==s&&v!==a&&Cr(o,h,c,d,l,u,v.x,v.y)&&He(v.prev,v,v.next)>=0))return!1;v=v.nextZ}for(;E&&E.z>=m;){if(E.x>=f&&E.x<=x&&E.y>=g&&E.y<=p&&E!==s&&E!==a&&Cr(o,h,c,d,l,u,E.x,E.y)&&He(E.prev,E,E.next)>=0)return!1;E=E.prevZ}for(;v&&v.z<=S;){if(v.x>=f&&v.x<=x&&v.y>=g&&v.y<=p&&v!==s&&v!==a&&Cr(o,h,c,d,l,u,v.x,v.y)&&He(v.prev,v,v.next)>=0)return!1;v=v.nextZ}return!0}function xp(i,t){let e=i;do{let n=e.prev,s=e.next.next;!ir(n,s)&&sd(n,e,e.next,s)&&na(n,s)&&na(s,n)&&(t.push(n.i,e.i,s.i),ia(e),ia(e.next),e=i=s),e=e.next}while(e!==i);return xs(e)}function _p(i,t,e,n,s,r){let a=i;do{let o=a.next.next;for(;o!==a.prev;){if(a.i!==o.i&&Rp(a,o)){let c=rd(a,o);a=xs(a,a.next),c=xs(c,c.next),ea(a,t,e,n,s,r,0),ea(c,t,e,n,s,r,0);return}o=o.next}a=a.next}while(a!==i)}function yp(i,t,e,n){let s=[];for(let r=0,a=t.length;r<a;r++){let o=t[r]*n,c=r<a-1?t[r+1]*n:i.length,l=nd(i,o,c,n,!1);l===l.next&&(l.steiner=!0),s.push(Ap(l))}s.sort(Mp);for(let r=0;r<s.length;r++)e=Sp(s[r],e);return e}function Mp(i,t){let e=i.x-t.x;if(e===0&&(e=i.y-t.y,e===0)){let n=(i.next.y-i.y)/(i.next.x-i.x),s=(t.next.y-t.y)/(t.next.x-t.x);e=n-s}return e}function Sp(i,t){let e=bp(i,t);if(!e)return t;let n=rd(e,i);return xs(n,n.next),xs(e,e.next)}function bp(i,t){let e=t,n=i.x,s=i.y,r=-1/0,a;if(ir(i,e))return e;do{if(ir(i,e.next))return e.next;if(s<=e.y&&s>=e.next.y&&e.next.y!==e.y){let d=e.x+(s-e.y)*(e.next.x-e.x)/(e.next.y-e.y);if(d<=n&&d>r&&(r=d,a=e.x<e.next.x?e:e.next,d===n))return a}e=e.next}while(e!==t);if(!a)return null;let o=a,c=a.x,l=a.y,h=1/0;e=a;do{if(n>=e.x&&e.x>=c&&n!==e.x&&id(s<l?n:r,s,c,l,s<l?r:n,s,e.x,e.y)){let d=Math.abs(s-e.y)/(n-e.x);na(e,i)&&(d<h||d===h&&(e.x>a.x||e.x===a.x&&Ep(a,e)))&&(a=e,h=d)}e=e.next}while(e!==o);return a}function Ep(i,t){return He(i.prev,i,t.prev)<0&&He(t.next,i,i.next)<0}function wp(i,t,e,n){let s=i;do s.z===0&&(s.z=Tl(s.x,s.y,t,e,n)),s.prevZ=s.prev,s.nextZ=s.next,s=s.next;while(s!==i);s.prevZ.nextZ=null,s.prevZ=null,Tp(s)}function Tp(i){let t,e=1;do{let n=i,s;i=null;let r=null;for(t=0;n;){t++;let a=n,o=0;for(let l=0;l<e&&(o++,a=a.nextZ,!!a);l++);let c=e;for(;o>0||c>0&&a;)o!==0&&(c===0||!a||n.z<=a.z)?(s=n,n=n.nextZ,o--):(s=a,a=a.nextZ,c--),r?r.nextZ=s:i=s,s.prevZ=r,r=s;n=a}r.nextZ=null,e*=2}while(t>1);return i}function Tl(i,t,e,n,s){return i=(i-e)*s|0,t=(t-n)*s|0,i=(i|i<<8)&16711935,i=(i|i<<4)&252645135,i=(i|i<<2)&858993459,i=(i|i<<1)&1431655765,t=(t|t<<8)&16711935,t=(t|t<<4)&252645135,t=(t|t<<2)&858993459,t=(t|t<<1)&1431655765,i|t<<1}function Ap(i){let t=i,e=i;do(t.x<e.x||t.x===e.x&&t.y<e.y)&&(e=t),t=t.next;while(t!==i);return e}function id(i,t,e,n,s,r,a,o){return(s-a)*(t-o)>=(i-a)*(r-o)&&(i-a)*(n-o)>=(e-a)*(t-o)&&(e-a)*(r-o)>=(s-a)*(n-o)}function Cr(i,t,e,n,s,r,a,o){return!(i===a&&t===o)&&id(i,t,e,n,s,r,a,o)}function Rp(i,t){return i.next.i!==t.i&&i.prev.i!==t.i&&!Cp(i,t)&&(na(i,t)&&na(t,i)&&Pp(i,t)&&(He(i.prev,i,t.prev)||He(i,t.prev,t))||ir(i,t)&&He(i.prev,i,i.next)>0&&He(t.prev,t,t.next)>0)}function He(i,t,e){return(t.y-i.y)*(e.x-t.x)-(t.x-i.x)*(e.y-t.y)}function ir(i,t){return i.x===t.x&&i.y===t.y}function sd(i,t,e,n){let s=Qa(He(i,t,e)),r=Qa(He(i,t,n)),a=Qa(He(e,n,i)),o=Qa(He(e,n,t));return!!(s!==r&&a!==o||s===0&&Ka(i,e,t)||r===0&&Ka(i,n,t)||a===0&&Ka(e,i,n)||o===0&&Ka(e,t,n))}function Ka(i,t,e){return t.x<=Math.max(i.x,e.x)&&t.x>=Math.min(i.x,e.x)&&t.y<=Math.max(i.y,e.y)&&t.y>=Math.min(i.y,e.y)}function Qa(i){return i>0?1:i<0?-1:0}function Cp(i,t){let e=i;do{if(e.i!==i.i&&e.next.i!==i.i&&e.i!==t.i&&e.next.i!==t.i&&sd(e,e.next,i,t))return!0;e=e.next}while(e!==i);return!1}function na(i,t){return He(i.prev,i,i.next)<0?He(i,t,i.next)>=0&&He(i,i.prev,t)>=0:He(i,t,i.prev)<0||He(i,i.next,t)<0}function Pp(i,t){let e=i,n=!1,s=(i.x+t.x)/2,r=(i.y+t.y)/2;do e.y>r!=e.next.y>r&&e.next.y!==e.y&&s<(e.next.x-e.x)*(r-e.y)/(e.next.y-e.y)+e.x&&(n=!n),e=e.next;while(e!==i);return n}function rd(i,t){let e=Al(i.i,i.x,i.y),n=Al(t.i,t.x,t.y),s=i.next,r=t.prev;return i.next=t,t.prev=i,e.next=s,s.prev=e,n.next=e,e.prev=n,r.next=n,n.prev=r,n}function ou(i,t,e,n){let s=Al(i,t,e);return n?(s.next=n.next,s.prev=n,n.next.prev=s,n.next=s):(s.prev=s,s.next=s),s}function ia(i){i.next.prev=i.prev,i.prev.next=i.next,i.prevZ&&(i.prevZ.nextZ=i.nextZ),i.nextZ&&(i.nextZ.prevZ=i.prevZ)}function Al(i,t,e){return{i,x:t,y:e,prev:null,next:null,z:0,prevZ:null,nextZ:null,steiner:!1}}function Ip(i,t,e,n){let s=0;for(let r=t,a=e-n;r<e;r+=n)s+=(i[a]-i[r])*(i[r+1]+i[a+1]),a=r;return s}var Rl=class{static triangulate(t,e,n=2){return mp(t,e,n)}},ms=class i{static area(t){let e=t.length,n=0;for(let s=e-1,r=0;r<e;s=r++)n+=t[s].x*t[r].y-t[r].x*t[s].y;return n*.5}static isClockWise(t){return i.area(t)<0}static triangulateShape(t,e){let n=[],s=[],r=[];cu(t),lu(n,t);let a=t.length;e.forEach(cu);for(let c=0;c<e.length;c++)s.push(a),a+=e[c].length,lu(n,e[c]);let o=Rl.triangulate(n,s);for(let c=0;c<o.length;c+=3)r.push(o.slice(c,c+3));return r}};function cu(i){let t=i.length;t>2&&i[t-1].equals(i[0])&&i.pop()}function lu(i,t){for(let e=0;e<t.length;e++)i.push(t[e].x),i.push(t[e].y)}var Ni=class i extends _e{constructor(t=new mi([new mt(.5,.5),new mt(-.5,.5),new mt(-.5,-.5),new mt(.5,-.5)]),e={}){super(),this.type="ExtrudeGeometry",this.parameters={shapes:t,options:e},t=Array.isArray(t)?t:[t];let n=this,s=[],r=[];for(let o=0,c=t.length;o<c;o++){let l=t[o];a(l)}this.setAttribute("position",new Jt(s,3)),this.setAttribute("uv",new Jt(r,2)),this.computeVertexNormals();function a(o){let c=[],l=e.curveSegments!==void 0?e.curveSegments:12,h=e.steps!==void 0?e.steps:1,d=e.depth!==void 0?e.depth:1,u=e.bevelEnabled!==void 0?e.bevelEnabled:!0,f=e.bevelThickness!==void 0?e.bevelThickness:.2,g=e.bevelSize!==void 0?e.bevelSize:f-.1,x=e.bevelOffset!==void 0?e.bevelOffset:0,p=e.bevelSegments!==void 0?e.bevelSegments:3,m=e.extrudePath,S=e.UVGenerator!==void 0?e.UVGenerator:Lp,E,v=!1,b,M,A,_;if(m){E=m.getSpacedPoints(h),v=!0,u=!1;let it=m.isCatmullRomCurve3?m.closed:!1;b=m.computeFrenetFrames(h,it),M=new P,A=new P,_=new P}u||(p=0,f=0,g=0,x=0);let T=o.extractPoints(l),I=T.shape,L=T.holes;if(!ms.isClockWise(I)){I=I.reverse();for(let it=0,ut=L.length;it<ut;it++){let Y=L[it];ms.isClockWise(Y)&&(L[it]=Y.reverse())}}function B(it){let Y=10000000000000001e-36,st=it[0];for(let vt=1;vt<=it.length;vt++){let Vt=vt%it.length,St=it[Vt],Xt=St.x-st.x,Qt=St.y-st.y,F=Xt*Xt+Qt*Qt,ye=Math.max(Math.abs(St.x),Math.abs(St.y),Math.abs(st.x),Math.abs(st.y)),ne=Y*ye*ye;if(F<=ne){it.splice(Vt,1),vt--;continue}st=St}}B(I),L.forEach(B);let D=L.length,O=I;for(let it=0;it<D;it++){let ut=L[it];I=I.concat(ut)}function $(it,ut,Y){return ut||se("ExtrudeGeometry: vec does not exist"),it.clone().addScaledVector(ut,Y)}let J=I.length;function W(it,ut,Y){let st,vt,Vt,St=it.x-ut.x,Xt=it.y-ut.y,Qt=Y.x-it.x,F=Y.y-it.y,ye=St*St+Xt*Xt,ne=St*F-Xt*Qt;if(Math.abs(ne)>Number.EPSILON){let C=Math.sqrt(ye),y=Math.sqrt(Qt*Qt+F*F),H=ut.x-Xt/C,X=ut.y+St/C,tt=Y.x-F/y,ct=Y.y+Qt/y,_t=((tt-H)*F-(ct-X)*Qt)/(St*F-Xt*Qt);st=H+St*_t-it.x,vt=X+Xt*_t-it.y;let rt=st*st+vt*vt;if(rt<=2)return new mt(st,vt);Vt=Math.sqrt(rt/2)}else{let C=!1;St>Number.EPSILON?Qt>Number.EPSILON&&(C=!0):St<-Number.EPSILON?Qt<-Number.EPSILON&&(C=!0):Math.sign(Xt)===Math.sign(F)&&(C=!0),C?(st=-Xt,vt=St,Vt=Math.sqrt(ye)):(st=St,vt=Xt,Vt=Math.sqrt(ye/2))}return new mt(st/Vt,vt/Vt)}let G=[];for(let it=0,ut=O.length,Y=ut-1,st=it+1;it<ut;it++,Y++,st++)Y===ut&&(Y=0),st===ut&&(st=0),G[it]=W(O[it],O[Y],O[st]);let K=[],nt,Et=G.concat();for(let it=0,ut=D;it<ut;it++){let Y=L[it];nt=[];for(let st=0,vt=Y.length,Vt=vt-1,St=st+1;st<vt;st++,Vt++,St++)Vt===vt&&(Vt=0),St===vt&&(St=0),nt[st]=W(Y[st],Y[Vt],Y[St]);K.push(nt),Et=Et.concat(nt)}let pt;if(p===0)pt=ms.triangulateShape(O,L);else{let it=[],ut=[];for(let Y=0;Y<p;Y++){let st=Y/p,vt=f*Math.cos(st*Math.PI/2),Vt=g*Math.sin(st*Math.PI/2)+x;for(let St=0,Xt=O.length;St<Xt;St++){let Qt=$(O[St],G[St],Vt);dt(Qt.x,Qt.y,-vt),st===0&&it.push(Qt)}for(let St=0,Xt=D;St<Xt;St++){let Qt=L[St];nt=K[St];let F=[];for(let ye=0,ne=Qt.length;ye<ne;ye++){let C=$(Qt[ye],nt[ye],Vt);dt(C.x,C.y,-vt),st===0&&F.push(C)}st===0&&ut.push(F)}}pt=ms.triangulateShape(it,ut)}let Ft=pt.length,Dt=g+x;for(let it=0;it<J;it++){let ut=u?$(I[it],Et[it],Dt):I[it];v?(A.copy(b.normals[0]).multiplyScalar(ut.x),M.copy(b.binormals[0]).multiplyScalar(ut.y),_.copy(E[0]).add(A).add(M),dt(_.x,_.y,_.z)):dt(ut.x,ut.y,0)}for(let it=1;it<=h;it++)for(let ut=0;ut<J;ut++){let Y=u?$(I[ut],Et[ut],Dt):I[ut];v?(A.copy(b.normals[it]).multiplyScalar(Y.x),M.copy(b.binormals[it]).multiplyScalar(Y.y),_.copy(E[it]).add(A).add(M),dt(_.x,_.y,_.z)):dt(Y.x,Y.y,d/h*it)}for(let it=p-1;it>=0;it--){let ut=it/p,Y=f*Math.cos(ut*Math.PI/2),st=g*Math.sin(ut*Math.PI/2)+x;for(let vt=0,Vt=O.length;vt<Vt;vt++){let St=$(O[vt],G[vt],st);dt(St.x,St.y,d+Y)}for(let vt=0,Vt=L.length;vt<Vt;vt++){let St=L[vt];nt=K[vt];for(let Xt=0,Qt=St.length;Xt<Qt;Xt++){let F=$(St[Xt],nt[Xt],st);v?dt(F.x,F.y+E[h-1].y,E[h-1].x+Y):dt(F.x,F.y,d+Y)}}}ft(),U();function ft(){let it=s.length/3;if(u){let ut=0,Y=J*ut;for(let st=0;st<Ft;st++){let vt=pt[st];Mt(vt[2]+Y,vt[1]+Y,vt[0]+Y)}ut=h+p*2,Y=J*ut;for(let st=0;st<Ft;st++){let vt=pt[st];Mt(vt[0]+Y,vt[1]+Y,vt[2]+Y)}}else{for(let ut=0;ut<Ft;ut++){let Y=pt[ut];Mt(Y[2],Y[1],Y[0])}for(let ut=0;ut<Ft;ut++){let Y=pt[ut];Mt(Y[0]+J*h,Y[1]+J*h,Y[2]+J*h)}}n.addGroup(it,s.length/3-it,0)}function U(){let it=s.length/3,ut=0;V(O,ut),ut+=O.length;for(let Y=0,st=L.length;Y<st;Y++){let vt=L[Y];V(vt,ut),ut+=vt.length}n.addGroup(it,s.length/3-it,1)}function V(it,ut){let Y=it.length;for(;--Y>=0;){let st=Y,vt=Y-1;vt<0&&(vt=it.length-1);for(let Vt=0,St=h+p*2;Vt<St;Vt++){let Xt=J*Vt,Qt=J*(Vt+1),F=ut+st+Xt,ye=ut+vt+Xt,ne=ut+vt+Qt,C=ut+st+Qt;yt(F,ye,ne,C)}}}function dt(it,ut,Y){c.push(it),c.push(ut),c.push(Y)}function Mt(it,ut,Y){It(it),It(ut),It(Y);let st=s.length/3,vt=S.generateTopUV(n,s,st-3,st-2,st-1);Kt(vt[0]),Kt(vt[1]),Kt(vt[2])}function yt(it,ut,Y,st){It(it),It(ut),It(st),It(ut),It(Y),It(st);let vt=s.length/3,Vt=S.generateSideWallUV(n,s,vt-6,vt-3,vt-2,vt-1);Kt(Vt[0]),Kt(Vt[1]),Kt(Vt[3]),Kt(Vt[1]),Kt(Vt[2]),Kt(Vt[3])}function It(it){s.push(c[it*3+0]),s.push(c[it*3+1]),s.push(c[it*3+2])}function Kt(it){r.push(it.x),r.push(it.y)}}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}toJSON(){let t=super.toJSON(),e=this.parameters.shapes,n=this.parameters.options;return Dp(e,n,t)}static fromJSON(t,e){let n=[];for(let r=0,a=t.shapes.length;r<a;r++){let o=e[t.shapes[r]];n.push(o)}let s=t.options.extrudePath;return s!==void 0&&(t.options.extrudePath=new wl[s.type]().fromJSON(s)),new i(n,t.options)}},Lp={generateTopUV:function(i,t,e,n,s){let r=t[e*3],a=t[e*3+1],o=t[n*3],c=t[n*3+1],l=t[s*3],h=t[s*3+1];return[new mt(r,a),new mt(o,c),new mt(l,h)]},generateSideWallUV:function(i,t,e,n,s,r){let a=t[e*3],o=t[e*3+1],c=t[e*3+2],l=t[n*3],h=t[n*3+1],d=t[n*3+2],u=t[s*3],f=t[s*3+1],g=t[s*3+2],x=t[r*3],p=t[r*3+1],m=t[r*3+2];return Math.abs(o-h)<Math.abs(a-l)?[new mt(a,1-c),new mt(l,1-d),new mt(u,1-g),new mt(x,1-m)]:[new mt(o,1-c),new mt(h,1-d),new mt(f,1-g),new mt(p,1-m)]}};function Dp(i,t,e){if(e.shapes=[],Array.isArray(i))for(let n=0,s=i.length;n<s;n++){let r=i[n];e.shapes.push(r.uuid)}else e.shapes.push(i.uuid);return e.options=Object.assign({},t),t.extrudePath!==void 0&&(e.options.extrudePath=t.extrudePath.toJSON()),e}var sr=class i extends Mo{constructor(t=1,e=0){let n=(1+Math.sqrt(5))/2,s=[-1,n,0,1,n,0,-1,-n,0,1,-n,0,0,-1,n,0,1,n,0,-1,-n,0,1,-n,n,0,-1,n,0,1,-n,0,-1,-n,0,1],r=[0,11,5,0,5,1,0,1,7,0,7,10,0,10,11,1,5,9,5,11,4,11,10,2,10,7,6,7,1,8,3,9,4,3,4,2,3,2,6,3,6,8,3,8,9,4,9,5,2,4,11,6,2,10,8,6,7,9,8,1];super(s,r,t,e),this.type="IcosahedronGeometry",this.parameters={radius:t,detail:e}}static fromJSON(t){return new i(t.radius,t.detail)}},gi=class i extends _e{constructor(t=[new mt(0,-.5),new mt(.5,0),new mt(0,.5)],e=12,n=0,s=Math.PI*2){super(),this.type="LatheGeometry",this.parameters={points:t,segments:e,phiStart:n,phiLength:s},e=Math.floor(e),s=ae(s,0,Math.PI*2);let r=[],a=[],o=[],c=[],l=[],h=1/e,d=new P,u=new mt,f=new P,g=new P,x=new P,p=0,m=0;for(let S=0;S<=t.length-1;S++)switch(S){case 0:p=t[S+1].x-t[S].x,m=t[S+1].y-t[S].y,f.x=m*1,f.y=-p,f.z=m*0,x.copy(f),f.normalize(),c.push(f.x,f.y,f.z);break;case t.length-1:c.push(x.x,x.y,x.z);break;default:p=t[S+1].x-t[S].x,m=t[S+1].y-t[S].y,f.x=m*1,f.y=-p,f.z=m*0,g.copy(f),f.x+=x.x,f.y+=x.y,f.z+=x.z,f.normalize(),c.push(f.x,f.y,f.z),x.copy(g)}for(let S=0;S<=e;S++){let E=n+S*h*s,v=Math.sin(E),b=Math.cos(E);for(let M=0;M<=t.length-1;M++){d.x=t[M].x*v,d.y=t[M].y,d.z=t[M].x*b,a.push(d.x,d.y,d.z),u.x=S/e,u.y=M/(t.length-1),o.push(u.x,u.y);let A=c[3*M+0]*v,_=c[3*M+1],T=c[3*M+0]*b;l.push(A,_,T)}}for(let S=0;S<e;S++)for(let E=0;E<t.length-1;E++){let v=E+S*t.length,b=v,M=v+t.length,A=v+t.length+1,_=v+1;r.push(b,M,_),r.push(A,_,M)}this.setIndex(r),this.setAttribute("position",new Jt(a,3)),this.setAttribute("uv",new Jt(o,2)),this.setAttribute("normal",new Jt(l,3))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.points,t.segments,t.phiStart,t.phiLength)}};var Xe=class i extends _e{constructor(t=1,e=1,n=1,s=1){super(),this.type="PlaneGeometry",this.parameters={width:t,height:e,widthSegments:n,heightSegments:s};let r=t/2,a=e/2,o=Math.floor(n),c=Math.floor(s),l=o+1,h=c+1,d=t/o,u=e/c,f=[],g=[],x=[],p=[];for(let m=0;m<h;m++){let S=m*u-a;for(let E=0;E<l;E++){let v=E*d-r;g.push(v,-S,0),x.push(0,0,1),p.push(E/o),p.push(1-m/c)}}for(let m=0;m<c;m++)for(let S=0;S<o;S++){let E=S+l*m,v=S+l*(m+1),b=S+1+l*(m+1),M=S+1+l*m;f.push(E,v,M),f.push(v,b,M)}this.setIndex(f),this.setAttribute("position",new Jt(g,3)),this.setAttribute("normal",new Jt(x,3)),this.setAttribute("uv",new Jt(p,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.width,t.height,t.widthSegments,t.heightSegments)}},sa=class i extends _e{constructor(t=.5,e=1,n=32,s=1,r=0,a=Math.PI*2){super(),this.type="RingGeometry",this.parameters={innerRadius:t,outerRadius:e,thetaSegments:n,phiSegments:s,thetaStart:r,thetaLength:a},n=Math.max(3,n),s=Math.max(1,s);let o=[],c=[],l=[],h=[],d=t,u=(e-t)/s,f=new P,g=new mt;for(let x=0;x<=s;x++){for(let p=0;p<=n;p++){let m=r+p/n*a;f.x=d*Math.cos(m),f.y=d*Math.sin(m),c.push(f.x,f.y,f.z),l.push(0,0,1),g.x=(f.x/e+1)/2,g.y=(f.y/e+1)/2,h.push(g.x,g.y)}d+=u}for(let x=0;x<s;x++){let p=x*(n+1);for(let m=0;m<n;m++){let S=m+p,E=S,v=S+n+1,b=S+n+2,M=S+1;o.push(E,v,M),o.push(v,b,M)}}this.setIndex(o),this.setAttribute("position",new Jt(c,3)),this.setAttribute("normal",new Jt(l,3)),this.setAttribute("uv",new Jt(h,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.innerRadius,t.outerRadius,t.thetaSegments,t.phiSegments,t.thetaStart,t.thetaLength)}};var Vn=class i extends _e{constructor(t=1,e=32,n=16,s=0,r=Math.PI*2,a=0,o=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:t,widthSegments:e,heightSegments:n,phiStart:s,phiLength:r,thetaStart:a,thetaLength:o},e=Math.max(3,Math.floor(e)),n=Math.max(2,Math.floor(n));let c=Math.min(a+o,Math.PI),l=0,h=[],d=new P,u=new P,f=[],g=[],x=[],p=[];for(let m=0;m<=n;m++){let S=[],E=m/n,v=a+E*o,b=t*Math.cos(v),M=Math.sqrt(t*t-b*b),A=0;m===0&&a===0?A=.5/e:m===n&&c===Math.PI&&(A=-.5/e);for(let _=0;_<=e;_++){let T=_/e,I=s+T*r;d.x=-M*Math.cos(I),d.y=b,d.z=M*Math.sin(I),g.push(d.x,d.y,d.z),u.copy(d).normalize(),x.push(u.x,u.y,u.z),p.push(T+A,1-E),S.push(l++)}h.push(S)}for(let m=0;m<n;m++)for(let S=0;S<e;S++){let E=h[m][S+1],v=h[m][S],b=h[m+1][S],M=h[m+1][S+1];(m!==0||a>0)&&f.push(E,v,M),(m!==n-1||c<Math.PI)&&f.push(v,b,M)}this.setIndex(f),this.setAttribute("position",new Jt(g,3)),this.setAttribute("normal",new Jt(x,3)),this.setAttribute("uv",new Jt(p,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.radius,t.widthSegments,t.heightSegments,t.phiStart,t.phiLength,t.thetaStart,t.thetaLength)}};var ri=class i extends _e{constructor(t=1,e=.4,n=12,s=48,r=Math.PI*2,a=0,o=Math.PI*2){super(),this.type="TorusGeometry",this.parameters={radius:t,tube:e,radialSegments:n,tubularSegments:s,arc:r,thetaStart:a,thetaLength:o},n=Math.floor(n),s=Math.floor(s);let c=[],l=[],h=[],d=[],u=new P,f=new P,g=new P;for(let x=0;x<=n;x++){let p=a+x/n*o;for(let m=0;m<=s;m++){let S=m/s*r;f.x=(t+e*Math.cos(p))*Math.cos(S),f.y=(t+e*Math.cos(p))*Math.sin(S),f.z=e*Math.sin(p),l.push(f.x,f.y,f.z),u.x=t*Math.cos(S),u.y=t*Math.sin(S),g.subVectors(f,u).normalize(),h.push(g.x,g.y,g.z),d.push(m/s),d.push(x/n)}}for(let x=1;x<=n;x++)for(let p=1;p<=s;p++){let m=(s+1)*x+p-1,S=(s+1)*(x-1)+p-1,E=(s+1)*(x-1)+p,v=(s+1)*x+p;c.push(m,S,v),c.push(S,E,v)}this.setIndex(c),this.setAttribute("position",new Jt(l,3)),this.setAttribute("normal",new Jt(h,3)),this.setAttribute("uv",new Jt(d,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.radius,t.tube,t.radialSegments,t.tubularSegments,t.arc,t.thetaStart,t.thetaLength)}};var ra=class extends _e{constructor(t=null){if(super(),this.type="WireframeGeometry",this.parameters={geometry:t},t!==null){let e=[],n=new Set,s=new P,r=new P;if(t.index!==null){let a=t.attributes.position,o=t.index,c=t.groups;c.length===0&&(c=[{start:0,count:o.count,materialIndex:0}]);for(let l=0,h=c.length;l<h;++l){let d=c[l],u=d.start,f=d.count;for(let g=u,x=u+f;g<x;g+=3)for(let p=0;p<3;p++){let m=o.getX(g+p),S=o.getX(g+(p+1)%3);s.fromBufferAttribute(a,m),r.fromBufferAttribute(a,S),hu(s,r,n)===!0&&(e.push(s.x,s.y,s.z),e.push(r.x,r.y,r.z))}}}else{let a=t.attributes.position;for(let o=0,c=a.count/3;o<c;o++)for(let l=0;l<3;l++){let h=3*o+l,d=3*o+(l+1)%3;s.fromBufferAttribute(a,h),r.fromBufferAttribute(a,d),hu(s,r,n)===!0&&(e.push(s.x,s.y,s.z),e.push(r.x,r.y,r.z))}}this.setAttribute("position",new Jt(e,3))}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}};function hu(i,t,e){let n=`${i.x},${i.y},${i.z}-${t.x},${t.y},${t.z}`,s=`${t.x},${t.y},${t.z}-${i.x},${i.y},${i.z}`;return e.has(n)===!0||e.has(s)===!0?!1:(e.add(n),e.add(s),!0)}function Ss(i){let t={};for(let e in i){t[e]={};for(let n in i[e]){let s=i[e][n];if(uu(s))s.isRenderTargetTexture?(ee("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),t[e][n]=null):t[e][n]=s.clone();else if(Array.isArray(s))if(uu(s[0])){let r=[];for(let a=0,o=s.length;a<o;a++)r[a]=s[a].clone();t[e][n]=r}else t[e][n]=s.slice();else t[e][n]=s}}return t}function pn(i){let t={};for(let e=0;e<i.length;e++){let n=Ss(i[e]);for(let s in n)t[s]=n[s]}return t}function uu(i){return i&&(i.isColor||i.isMatrix3||i.isMatrix4||i.isVector2||i.isVector3||i.isVector4||i.isTexture||i.isQuaternion)}function Up(i){let t=[];for(let e=0;e<i.length;e++)t.push(i[e].clone());return t}function nh(i){let t=i.getRenderTarget();return t===null?i.outputColorSpace:t.isXRRenderTarget===!0?t.texture.colorSpace:Se.workingColorSpace}var ba={clone:Ss,merge:pn},Np=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Fp=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`,Ue=class extends Ui{constructor(t){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=Np,this.fragmentShader=Fp,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,t!==void 0&&this.setValues(t)}copy(t){return super.copy(t),this.fragmentShader=t.fragmentShader,this.vertexShader=t.vertexShader,this.uniforms=Ss(t.uniforms),this.uniformsGroups=Up(t.uniformsGroups),this.defines=Object.assign({},t.defines),this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this.fog=t.fog,this.lights=t.lights,this.clipping=t.clipping,this.extensions=Object.assign({},t.extensions),this.glslVersion=t.glslVersion,this.defaultAttributeValues=Object.assign({},t.defaultAttributeValues),this.index0AttributeName=t.index0AttributeName,this.uniformsNeedUpdate=t.uniformsNeedUpdate,this}toJSON(t){let e=super.toJSON(t);e.glslVersion=this.glslVersion,e.uniforms={};for(let s in this.uniforms){let a=this.uniforms[s].value;a&&a.isTexture?e.uniforms[s]={type:"t",value:a.toJSON(t).uuid}:a&&a.isColor?e.uniforms[s]={type:"c",value:a.getHex()}:a&&a.isVector2?e.uniforms[s]={type:"v2",value:a.toArray()}:a&&a.isVector3?e.uniforms[s]={type:"v3",value:a.toArray()}:a&&a.isVector4?e.uniforms[s]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?e.uniforms[s]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?e.uniforms[s]={type:"m4",value:a.toArray()}:e.uniforms[s]={value:a}}Object.keys(this.defines).length>0&&(e.defines=this.defines),e.vertexShader=this.vertexShader,e.fragmentShader=this.fragmentShader,e.lights=this.lights,e.clipping=this.clipping;let n={};for(let s in this.extensions)this.extensions[s]===!0&&(n[s]=!0);return Object.keys(n).length>0&&(e.extensions=n),e}fromJSON(t,e){if(super.fromJSON(t,e),t.uniforms!==void 0)for(let n in t.uniforms){let s=t.uniforms[n];switch(this.uniforms[n]={},s.type){case"t":this.uniforms[n].value=e[s.value]||null;break;case"c":this.uniforms[n].value=new Ot().setHex(s.value);break;case"v2":this.uniforms[n].value=new mt().fromArray(s.value);break;case"v3":this.uniforms[n].value=new P().fromArray(s.value);break;case"v4":this.uniforms[n].value=new xe().fromArray(s.value);break;case"m3":this.uniforms[n].value=new ce().fromArray(s.value);break;case"m4":this.uniforms[n].value=new ue().fromArray(s.value);break;default:this.uniforms[n].value=s.value}}if(t.defines!==void 0&&(this.defines=t.defines),t.vertexShader!==void 0&&(this.vertexShader=t.vertexShader),t.fragmentShader!==void 0&&(this.fragmentShader=t.fragmentShader),t.glslVersion!==void 0&&(this.glslVersion=t.glslVersion),t.extensions!==void 0)for(let n in t.extensions)this.extensions[n]=t.extensions[n];return t.lights!==void 0&&(this.lights=t.lights),t.clipping!==void 0&&(this.clipping=t.clipping),this}},Ao=class extends Ue{constructor(t){super(t),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}},Nt=class extends Ui{constructor(t){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new Ot(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new Ot(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Cc,this.normalScale=new mt(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new ni,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(t)}copy(t){return super.copy(t),this.defines={STANDARD:""},this.color.copy(t.color),this.roughness=t.roughness,this.metalness=t.metalness,this.map=t.map,this.lightMap=t.lightMap,this.lightMapIntensity=t.lightMapIntensity,this.aoMap=t.aoMap,this.aoMapIntensity=t.aoMapIntensity,this.emissive.copy(t.emissive),this.emissiveMap=t.emissiveMap,this.emissiveIntensity=t.emissiveIntensity,this.bumpMap=t.bumpMap,this.bumpScale=t.bumpScale,this.normalMap=t.normalMap,this.normalMapType=t.normalMapType,this.normalScale.copy(t.normalScale),this.displacementMap=t.displacementMap,this.displacementScale=t.displacementScale,this.displacementBias=t.displacementBias,this.roughnessMap=t.roughnessMap,this.metalnessMap=t.metalnessMap,this.alphaMap=t.alphaMap,this.envMap=t.envMap,this.envMapRotation.copy(t.envMapRotation),this.envMapIntensity=t.envMapIntensity,this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this.wireframeLinecap=t.wireframeLinecap,this.wireframeLinejoin=t.wireframeLinejoin,this.flatShading=t.flatShading,this.fog=t.fog,this}},Ji=class extends Nt{constructor(t){super(),this.isMeshPhysicalMaterial=!0,this.defines={STANDARD:"",PHYSICAL:""},this.type="MeshPhysicalMaterial",this.anisotropyRotation=0,this.anisotropyMap=null,this.clearcoatMap=null,this.clearcoatRoughness=0,this.clearcoatRoughnessMap=null,this.clearcoatNormalScale=new mt(1,1),this.clearcoatNormalMap=null,this.ior=1.5,Object.defineProperty(this,"reflectivity",{get:function(){return ae(2.5*(this.ior-1)/(this.ior+1),0,1)},set:function(e){this.ior=(1+.4*e)/(1-.4*e)}}),this.iridescenceMap=null,this.iridescenceIOR=1.3,this.iridescenceThicknessRange=[100,400],this.iridescenceThicknessMap=null,this.sheenColor=new Ot(0),this.sheenColorMap=null,this.sheenRoughness=1,this.sheenRoughnessMap=null,this.transmissionMap=null,this.thickness=0,this.thicknessMap=null,this.attenuationDistance=1/0,this.attenuationColor=new Ot(1,1,1),this.specularIntensity=1,this.specularIntensityMap=null,this.specularColor=new Ot(1,1,1),this.specularColorMap=null,this._anisotropy=0,this._clearcoat=0,this._dispersion=0,this._iridescence=0,this._retroreflectivity=0,this._sheen=0,this._transmission=0,this.setValues(t)}get anisotropy(){return this._anisotropy}set anisotropy(t){this._anisotropy>0!=t>0&&this.version++,this._anisotropy=t}get clearcoat(){return this._clearcoat}set clearcoat(t){this._clearcoat>0!=t>0&&this.version++,this._clearcoat=t}get iridescence(){return this._iridescence}set iridescence(t){this._iridescence>0!=t>0&&this.version++,this._iridescence=t}get dispersion(){return this._dispersion}set dispersion(t){this._dispersion>0!=t>0&&this.version++,this._dispersion=t}get retroreflectivity(){return this._retroreflectivity}set retroreflectivity(t){this._retroreflectivity>0!=t>0&&this.version++,this._retroreflectivity=t}get sheen(){return this._sheen}set sheen(t){this._sheen>0!=t>0&&this.version++,this._sheen=t}get transmission(){return this._transmission}set transmission(t){this._transmission>0!=t>0&&this.version++,this._transmission=t}copy(t){return super.copy(t),this.defines={STANDARD:"",PHYSICAL:""},this.anisotropy=t.anisotropy,this.anisotropyRotation=t.anisotropyRotation,this.anisotropyMap=t.anisotropyMap,this.clearcoat=t.clearcoat,this.clearcoatMap=t.clearcoatMap,this.clearcoatRoughness=t.clearcoatRoughness,this.clearcoatRoughnessMap=t.clearcoatRoughnessMap,this.clearcoatNormalMap=t.clearcoatNormalMap,this.clearcoatNormalScale.copy(t.clearcoatNormalScale),this.dispersion=t.dispersion,this.ior=t.ior,this.iridescence=t.iridescence,this.iridescenceMap=t.iridescenceMap,this.iridescenceIOR=t.iridescenceIOR,this.iridescenceThicknessRange=[...t.iridescenceThicknessRange],this.iridescenceThicknessMap=t.iridescenceThicknessMap,this.retroreflectivity=t.retroreflectivity,this.sheen=t.sheen,this.sheenColor.copy(t.sheenColor),this.sheenColorMap=t.sheenColorMap,this.sheenRoughness=t.sheenRoughness,this.sheenRoughnessMap=t.sheenRoughnessMap,this.transmission=t.transmission,this.transmissionMap=t.transmissionMap,this.thickness=t.thickness,this.thicknessMap=t.thicknessMap,this.attenuationDistance=t.attenuationDistance,this.attenuationColor.copy(t.attenuationColor),this.specularIntensity=t.specularIntensity,this.specularIntensityMap=t.specularIntensityMap,this.specularColor.copy(t.specularColor),this.specularColorMap=t.specularColorMap,this}};var Ro=class extends Ui{constructor(t){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=Vu,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(t)}copy(t){return super.copy(t),this.depthPacking=t.depthPacking,this.map=t.map,this.alphaMap=t.alphaMap,this.displacementMap=t.displacementMap,this.displacementScale=t.displacementScale,this.displacementBias=t.displacementBias,this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this}},Co=class extends Ui{constructor(t){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(t)}copy(t){return super.copy(t),this.map=t.map,this.alphaMap=t.alphaMap,this.displacementMap=t.displacementMap,this.displacementScale=t.displacementScale,this.displacementBias=t.displacementBias,this}};function Hs(i,t){return!i||i.constructor===t?i:typeof t.BYTES_PER_ELEMENT=="number"?new t(i):Array.prototype.slice.call(i)}function vl(i){return i!==void 0&&i.inTangents!==void 0&&i.outTangents!==void 0}var Ki=class{constructor(t,e,n,s){this.parameterPositions=t,this._cachedIndex=0,this.resultBuffer=s!==void 0?s:new e.constructor(n),this.sampleValues=e,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(t){let e=this.parameterPositions,n=this._cachedIndex,s=e[n],r=e[n-1];n:{t:{let a;e:{i:if(!(t<s)){for(let o=n+2;;){if(s===void 0){if(t<r)break i;return n=e.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===o)break;if(r=s,s=e[++n],t<s)break t}a=e.length;break e}if(!(t>=r)){let o=e[1];t<o&&(n=2,r=o);for(let c=n-2;;){if(r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===c)break;if(s=r,r=e[--n-1],t>=r)break t}a=n,n=0;break e}break n}for(;n<a;){let o=n+a>>>1;t<e[o]?a=o:n=o+1}if(s=e[n],r=e[n-1],r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(s===void 0)return n=e.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,r,s)}return this.interpolate_(n,r,t,s)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(t){let e=this.resultBuffer,n=this.sampleValues,s=this.valueSize,r=t*s;for(let a=0;a!==s;++a)e[a]=n[r+a];return e}interpolate_(){throw new Error("THREE.Interpolant: Call to abstract method.")}intervalChanged_(){}},Po=class extends Ki{constructor(t,e,n,s){super(t,e,n,s),this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:Ml,endingEnd:Ml}}intervalChanged_(t,e,n){let s=this.parameterPositions,r=t-2,a=t+1,o=s[r],c=s[a];if(o===void 0)switch(this.getSettings_().endingStart){case Sl:r=t,o=2*e-n;break;case bl:r=s.length-2,o=e+s[r]-s[r+1];break;default:r=t,o=n}if(c===void 0)switch(this.getSettings_().endingEnd){case Sl:a=t,c=2*n-e;break;case bl:a=1,c=n+s[1]-s[0];break;default:a=t-1,c=e}let l=(n-e)*.5,h=this.valueSize;this._weightPrev=l/(e-o),this._weightNext=l/(c-n),this._offsetPrev=r*h,this._offsetNext=a*h}interpolate_(t,e,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=t*o,l=c-o,h=this._offsetPrev,d=this._offsetNext,u=this._weightPrev,f=this._weightNext,g=(n-e)/(s-e),x=g*g,p=x*g,m=-u*p+2*u*x-u*g,S=(1+u)*p+(-1.5-2*u)*x+(-.5+u)*g+1,E=(-1-f)*p+(1.5+f)*x+.5*g,v=f*p-f*x;for(let b=0;b!==o;++b)r[b]=m*a[h+b]+S*a[l+b]+E*a[c+b]+v*a[d+b];return r}},Io=class extends Ki{constructor(t,e,n,s){super(t,e,n,s)}interpolate_(t,e,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=t*o,l=c-o,h=(n-e)/(s-e),d=1-h;for(let u=0;u!==o;++u)r[u]=a[l+u]*d+a[c+u]*h;return r}},Lo=class extends Ki{constructor(t,e,n,s){super(t,e,n,s)}interpolate_(t){return this.copySampleValue_(t-1)}},Do=class extends Ki{interpolate_(t,e,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=t*o,l=c-o,h=this.inTangents,d=this.outTangents;if(!h||!d){let g=(n-e)/(s-e),x=1-g;for(let p=0;p!==o;++p)r[p]=a[l+p]*x+a[c+p]*g;return r}let u=o*2,f=t-1;for(let g=0;g!==o;++g){let x=a[l+g],p=a[c+g],m=f*u+g*2,S=d[m],E=d[m+1],v=t*u+g*2,b=h[v],M=h[v+1],A=Op(n,e,S,b,s);r[g]=ad(A,x,E,M,p)}return r}};function ad(i,t,e,n,s){let r=1-i;return r*r*r*t+3*r*r*i*e+3*r*i*i*n+i*i*i*s}function zp(i,t,e,n,s){let r=1-i;return 3*r*r*(e-t)+6*r*i*(n-e)+3*i*i*(s-n)}function Op(i,t,e,n,s){let r=(i-t)/(s-t);for(let a=0;a<8;a++){let o=ad(r,t,e,n,s)-i;if(Math.abs(o)<1e-10)break;let c=zp(r,t,e,n,s);if(Math.abs(c)<1e-10)break;r=Math.max(0,Math.min(1,r-o/c))}return r}var Fn=class{constructor(t,e,n,s){if(t===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(e===void 0||e.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+t);this.name=t,this.times=Hs(e,this.TimeBufferType),this.values=Hs(n,this.ValueBufferType),this.setInterpolation(s||this.DefaultInterpolation)}static toJSON(t){let e=t.constructor,n;if(e.toJSON!==this.toJSON)n=e.toJSON(t);else{n={name:t.name,times:Hs(t.times,Array),values:Hs(t.values,Array)};let s=t.getInterpolation();s!==t.DefaultInterpolation&&(n.interpolation=s),vl(t.settings)&&(n.settings={inTangents:Hs(t.settings.inTangents,Array),outTangents:Hs(t.settings.outTangents,Array)})}return n.type=t.ValueTypeName,n}InterpolantFactoryMethodDiscrete(t){return new Lo(this.times,this.values,this.getValueSize(),t)}InterpolantFactoryMethodLinear(t){return new Io(this.times,this.values,this.getValueSize(),t)}InterpolantFactoryMethodSmooth(t){return new Po(this.times,this.values,this.getValueSize(),t)}InterpolantFactoryMethodBezier(t){let e=new Do(this.times,this.values,this.getValueSize(),t);return this.settings&&(e.inTangents=this.settings.inTangents,e.outTangents=this.settings.outTangents),e}setInterpolation(t){let e;switch(t){case Ur:e=this.InterpolantFactoryMethodDiscrete;break;case po:e=this.InterpolantFactoryMethodLinear;break;case io:e=this.InterpolantFactoryMethodSmooth;break;case yl:e=this.InterpolantFactoryMethodBezier;break}if(e===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(t!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error(n);return ee("KeyframeTrack:",n),this}return this.createInterpolant=e,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return Ur;case this.InterpolantFactoryMethodLinear:return po;case this.InterpolantFactoryMethodSmooth:return io;case this.InterpolantFactoryMethodBezier:return yl}}getValueSize(){return this.values.length/this.times.length}shift(t){if(t!==0){let e=this.times;for(let n=0,s=e.length;n!==s;++n)e[n]+=t}return this}scale(t){if(t!==1){let e=this.times;for(let n=0,s=e.length;n!==s;++n)e[n]*=t;vl(this.settings)&&(du(this.settings.inTangents,t),du(this.settings.outTangents,t))}return this}trim(t,e){let n=this.times,s=n.length,r=0,a=s-1;for(;r!==s&&n[r]<t;)++r;for(;a!==-1&&n[a]>e;)--a;if(++a,r!==0||a!==s){r>=a&&(a=Math.max(a,1),r=a-1);let o=this.getValueSize();this.times=n.slice(r,a),this.values=this.values.slice(r*o,a*o)}return this}validate(){let t=!0,e=this.getValueSize();e-Math.floor(e)!==0&&(se("KeyframeTrack: Invalid value size in track.",this),t=!1);let n=this.times,s=this.values,r=n.length;r===0&&(se("KeyframeTrack: Track is empty.",this),t=!1);let a=null;for(let o=0;o!==r;o++){let c=n[o];if(typeof c=="number"&&isNaN(c)){se("KeyframeTrack: Time is not a valid number.",this,o,c),t=!1;break}if(a!==null&&a>c){se("KeyframeTrack: Out of order keys.",this,o,c,a),t=!1;break}a=c}if(s!==void 0&&bf(s))for(let o=0,c=s.length;o!==c;++o){let l=s[o];if(isNaN(l)){se("KeyframeTrack: Value is not a valid number.",this,o,l),t=!1;break}}return t}optimize(){let t=this.times.slice(),e=this.values.slice(),n=this.getValueSize(),s=this.getInterpolation()===io,r=t.length-1,a=1;for(let o=1;o<r;++o){let c=!1,l=t[o],h=t[o+1];if(l!==h&&(o!==1||l!==t[0]))if(s)c=!0;else{let d=o*n,u=d-n,f=d+n;for(let g=0;g!==n;++g){let x=e[d+g];if(x!==e[u+g]||x!==e[f+g]){c=!0;break}}}if(c){if(o!==a){t[a]=t[o];let d=o*n,u=a*n;for(let f=0;f!==n;++f)e[u+f]=e[d+f]}++a}}if(r>0){t[a]=t[r];for(let o=r*n,c=a*n,l=0;l!==n;++l)e[c+l]=e[o+l];++a}return a!==t.length?(this.times=t.slice(0,a),this.values=e.slice(0,a*n)):(this.times=t,this.values=e),this}clone(){let t=this.times.slice(),e=this.values.slice(),n=this.constructor,s=new n(this.name,t,e);return s.createInterpolant=this.createInterpolant,vl(this.settings)&&(s.settings={inTangents:this.settings.inTangents.slice(),outTangents:this.settings.outTangents.slice()}),s}};function du(i,t){for(let e=0,n=i.length;e!==n;e+=2)i[e]*=t}Fn.prototype.ValueTypeName="";Fn.prototype.TimeBufferType=Float32Array;Fn.prototype.ValueBufferType=Float32Array;Fn.prototype.DefaultInterpolation=po;var Qi=class extends Fn{constructor(t,e,n){super(t,e,n)}};Qi.prototype.ValueTypeName="bool";Qi.prototype.ValueBufferType=Array;Qi.prototype.DefaultInterpolation=Ur;Qi.prototype.InterpolantFactoryMethodLinear=void 0;Qi.prototype.InterpolantFactoryMethodSmooth=void 0;var Uo=class extends Fn{constructor(t,e,n,s){super(t,e,n,s)}};Uo.prototype.ValueTypeName="color";var No=class extends Fn{constructor(t,e,n,s){super(t,e,n,s)}};No.prototype.ValueTypeName="number";var Fo=class extends Ki{constructor(t,e,n,s){super(t,e,n,s)}interpolate_(t,e,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=(n-e)/(s-e),l=t*o;for(let h=l+o;l!==h;l+=4)nn.slerpFlat(r,0,a,l-o,a,l,c);return r}},aa=class extends Fn{constructor(t,e,n,s){super(t,e,n,s)}InterpolantFactoryMethodLinear(t){return new Fo(this.times,this.values,this.getValueSize(),t)}};aa.prototype.ValueTypeName="quaternion";aa.prototype.InterpolantFactoryMethodSmooth=void 0;var ts=class extends Fn{constructor(t,e,n){super(t,e,n)}};ts.prototype.ValueTypeName="string";ts.prototype.ValueBufferType=Array;ts.prototype.DefaultInterpolation=Ur;ts.prototype.InterpolantFactoryMethodLinear=void 0;ts.prototype.InterpolantFactoryMethodSmooth=void 0;var zo=class extends Fn{constructor(t,e,n,s){super(t,e,n,s)}};zo.prototype.ValueTypeName="vector";var Oo=class{constructor(t,e,n){let s=this,r=!1,a=0,o=0,c,l=[];this.onStart=void 0,this.onLoad=t,this.onProgress=e,this.onError=n,this._abortController=null,this.itemStart=function(h){o++,r===!1&&s.onStart!==void 0&&s.onStart(h,a,o),r=!0},this.itemEnd=function(h){a++,s.onProgress!==void 0&&s.onProgress(h,a,o),a===o&&(r=!1,s.onLoad!==void 0&&s.onLoad())},this.itemError=function(h){s.onError!==void 0&&s.onError(h)},this.resolveURL=function(h){return h=h.normalize("NFC"),c?c(h):h},this.setURLModifier=function(h){return c=h,this},this.addHandler=function(h,d){return l.push(h,d),this},this.removeHandler=function(h){let d=l.indexOf(h);return d!==-1&&l.splice(d,2),this},this.getHandler=function(h){for(let d=0,u=l.length;d<u;d+=2){let f=l[d],g=l[d+1];if(f.global&&(f.lastIndex=0),f.test(h))return g}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){return this._abortController||(this._abortController=new AbortController),this._abortController}},od=new Oo,Bo=class{constructor(t){this.manager=t!==void 0?t:od,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}load(){}loadAsync(t,e){let n=this;return new Promise(function(s,r){n.load(t,s,e,r)})}parse(){}setCrossOrigin(t){return this.crossOrigin=t,this}setWithCredentials(t){return this.withCredentials=t,this}setPath(t){return this.path=t,this}setResourcePath(t){return this.resourcePath=t,this}setRequestHeader(t){return this.requestHeader=t,this}abort(){return this}};Bo.DEFAULT_MATERIAL_NAME="__DEFAULT";var rr=class extends sn{constructor(t,e=1){super(),this.isLight=!0,this.type="Light",this.color=new Ot(t),this.intensity=e}copy(t,e){return super.copy(t,e),this.color.copy(t.color),this.intensity=t.intensity,this}toJSON(t){let e=super.toJSON(t);return e.object.color=this.color.getHex(),e.object.intensity=this.intensity,e}},oa=class extends rr{constructor(t,e,n){super(t,n),this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(sn.DEFAULT_UP),this.updateMatrix(),this.groundColor=new Ot(e)}copy(t,e){return super.copy(t,e),this.groundColor.copy(t.groundColor),this}toJSON(t){let e=super.toJSON(t);return e.object.groundColor=this.groundColor.getHex(),e}},xl=new ue,fu=new P,pu=new P,ca=class{constructor(t){this.camera=t,this.intensity=1,this.bias=0,this.biasNode=null,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new mt(512,512),this.mapType=Cn,this.map=null,this.mapPass=null,this.matrix=new ue,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new er,this._frameExtents=new mt(1,1),this._viewportCount=1,this._viewports=[new xe(0,0,1,1)]}getViewportCount(){return this._viewportCount}getCamera(){return this.camera}getFrustum(){return this._frustum}updateMatrices(t){let e=this.camera;fu.setFromMatrixPosition(t.matrixWorld),e.position.copy(fu),pu.setFromMatrixPosition(t.target.matrixWorld),e.lookAt(pu),e.updateMatrixWorld(),this._updateMatrix(e,this.matrix,this._frustum)}_updateMatrix(t,e,n,s){xl.multiplyMatrices(t.projectionMatrix,t.matrixWorldInverse),n.setFromProjectionMatrix(xl,t.coordinateSystem,t.reversedDepth);let r=this._frameExtents,a=s?s.z/r.x:1,o=s?s.w/r.y:1,c=s?s.x/r.x:0,l=s?s.y/r.y:0;t.coordinateSystem===Zs||t.reversedDepth?e.set(.5*a,0,0,.5*a+c,0,.5*o,0,.5*o+l,0,0,1,0,0,0,0,1):e.set(.5*a,0,0,.5*a+c,0,.5*o,0,.5*o+l,0,0,.5,.5,0,0,0,1),e.multiply(xl)}getViewport(t){return this._viewports[t]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(t){return this.camera=t.camera.clone(),this.intensity=t.intensity,this.bias=t.bias,this.radius=t.radius,this.autoUpdate=t.autoUpdate,this.needsUpdate=t.needsUpdate,this.normalBias=t.normalBias,this.blurSamples=t.blurSamples,this.mapSize.copy(t.mapSize),this.biasNode=t.biasNode,this}clone(){return new this.constructor().copy(this)}toJSON(){let t={};return t.intensity=this.intensity,t.bias=this.bias,t.normalBias=this.normalBias,t.radius=this.radius,t.blurSamples=this.blurSamples,t.mapSize=this.mapSize.toArray(),t.camera=this.camera.toJSON(!1).object,delete t.camera.matrix,t}},to=new P,eo=new nn,hi=new P,la=class extends sn{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new ue,this.projectionMatrix=new ue,this.projectionMatrixInverse=new ue,this.coordinateSystem=ei,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(t,e){return super.copy(t,e),this.matrixWorldInverse.copy(t.matrixWorldInverse),this.projectionMatrix.copy(t.projectionMatrix),this.projectionMatrixInverse.copy(t.projectionMatrixInverse),this.coordinateSystem=t.coordinateSystem,this}getWorldDirection(t){return super.getWorldDirection(t).negate()}updateMatrixWorld(t){super.updateMatrixWorld(t),this.matrixWorld.decompose(to,eo,hi),hi.x===1&&hi.y===1&&hi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(to,eo,hi.set(1,1,1)).invert()}updateWorldMatrix(t,e,n=!1){super.updateWorldMatrix(t,e,n),this.matrixWorld.decompose(to,eo,hi),hi.x===1&&hi.y===1&&hi.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(to,eo,hi.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}},qi=new P,mu=new mt,gu=new mt,Ze=class extends la{constructor(t=50,e=1,n=.1,s=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=t,this.zoom=1,this.near=n,this.far=s,this.focus=10,this.aspect=e,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(t,e){return super.copy(t,e),this.fov=t.fov,this.zoom=t.zoom,this.near=t.near,this.far=t.far,this.focus=t.focus,this.aspect=t.aspect,this.view=t.view===null?null:Object.assign({},t.view),this.filmGauge=t.filmGauge,this.filmOffset=t.filmOffset,this}setFocalLength(t){let e=.5*this.getFilmHeight()/t;this.fov=Js*2*Math.atan(e),this.updateProjectionMatrix()}getFocalLength(){let t=Math.tan(Pr*.5*this.fov);return .5*this.getFilmHeight()/t}getEffectiveFOV(){return Js*2*Math.atan(Math.tan(Pr*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(t,e,n){qi.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),e.set(qi.x,qi.y).multiplyScalar(-t/qi.z),qi.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(qi.x,qi.y).multiplyScalar(-t/qi.z)}getViewSize(t,e){return this.getViewBounds(t,mu,gu),e.subVectors(gu,mu)}setViewOffset(t,e,n,s,r,a){this.aspect=t/e,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=t,this.view.fullHeight=e,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let t=this.near,e=t*Math.tan(Pr*.5*this.fov)/this.zoom,n=2*e,s=this.aspect*n,r=-.5*s,a=this.view;if(this.view!==null&&this.view.enabled){let c=a.fullWidth,l=a.fullHeight;r+=a.offsetX*s/c,e-=a.offsetY*n/l,s*=a.width/c,n*=a.height/l}let o=this.filmOffset;o!==0&&(r+=t*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(r,r+s,e,e-n,t,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(t){let e=super.toJSON(t);return e.object.fov=this.fov,e.object.zoom=this.zoom,e.object.near=this.near,e.object.far=this.far,e.object.focus=this.focus,e.object.aspect=this.aspect,this.view!==null&&(e.object.view=Object.assign({},this.view)),e.object.filmGauge=this.filmGauge,e.object.filmOffset=this.filmOffset,e}};var Cl=class extends ca{constructor(){super(new Ze(90,1,.5,500)),this.isPointLightShadow=!0}},ha=class extends rr{constructor(t,e,n=0,s=2){super(t,e),this.isPointLight=!0,this.type="PointLight",this.distance=n,this.decay=s,this.shadow=new Cl}get power(){return this.intensity*4*Math.PI}set power(t){this.intensity=t/(4*Math.PI)}dispose(){super.dispose(),this.shadow.dispose()}copy(t,e){return super.copy(t,e),this.distance=t.distance,this.decay=t.decay,this.shadow=t.shadow.clone(),this}toJSON(t){let e=super.toJSON(t);return e.object.distance=this.distance,e.object.decay=this.decay,e.object.shadow=this.shadow.toJSON(),e}},ar=class extends la{constructor(t=-1,e=1,n=1,s=-1,r=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=t,this.right=e,this.top=n,this.bottom=s,this.near=r,this.far=a,this.updateProjectionMatrix()}copy(t,e){return super.copy(t,e),this.left=t.left,this.right=t.right,this.top=t.top,this.bottom=t.bottom,this.near=t.near,this.far=t.far,this.zoom=t.zoom,this.view=t.view===null?null:Object.assign({},t.view),this}setViewOffset(t,e,n,s,r,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=t,this.view.fullHeight=e,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let t=(this.right-this.left)/(2*this.zoom),e=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,s=(this.top+this.bottom)/2,r=n-t,a=n+t,o=s+e,c=s-e;if(this.view!==null&&this.view.enabled){let l=(this.right-this.left)/this.view.fullWidth/this.zoom,h=(this.top-this.bottom)/this.view.fullHeight/this.zoom;r+=l*this.view.offsetX,a=r+l*this.view.width,o-=h*this.view.offsetY,c=o-h*this.view.height}this.projectionMatrix.makeOrthographic(r,a,o,c,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(t){let e=super.toJSON(t);return e.object.zoom=this.zoom,e.object.left=this.left,e.object.right=this.right,e.object.top=this.top,e.object.bottom=this.bottom,e.object.near=this.near,e.object.far=this.far,this.view!==null&&(e.object.view=Object.assign({},this.view)),e}},Pl=class extends ca{constructor(){super(new ar(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}},ua=class extends rr{constructor(t,e){super(t,e),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(sn.DEFAULT_UP),this.updateMatrix(),this.target=new sn,this.shadow=new Pl}dispose(){super.dispose(),this.shadow.dispose()}copy(t){return super.copy(t),this.target=t.target.clone(),this.shadow=t.shadow.clone(),this}toJSON(t){let e=super.toJSON(t);return e.object.shadow=this.shadow.toJSON(),e.object.target=this.target.uuid,e}};var da=class extends _e{constructor(){super(),this.isInstancedBufferGeometry=!0,this.type="InstancedBufferGeometry",this.instanceCount=1/0}copy(t){return super.copy(t),this.instanceCount=t.instanceCount,this}toJSON(){let t=super.toJSON();return t.instanceCount=this.instanceCount,t.isInstancedBufferGeometry=!0,t}};var Vs=-90,Gs=1,ko=class extends sn{constructor(t,e,n){super(),this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;let s=new Ze(Vs,Gs,t,e);s.layers=this.layers,this.add(s);let r=new Ze(Vs,Gs,t,e);r.layers=this.layers,this.add(r);let a=new Ze(Vs,Gs,t,e);a.layers=this.layers,this.add(a);let o=new Ze(Vs,Gs,t,e);o.layers=this.layers,this.add(o);let c=new Ze(Vs,Gs,t,e);c.layers=this.layers,this.add(c);let l=new Ze(Vs,Gs,t,e);l.layers=this.layers,this.add(l)}updateCoordinateSystem(){let t=this.coordinateSystem,e=this.children.concat(),[n,s,r,a,o,c]=e;for(let l of e)this.remove(l);if(t===ei)n.up.set(0,1,0),n.lookAt(1,0,0),s.up.set(0,1,0),s.lookAt(-1,0,0),r.up.set(0,0,-1),r.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),c.up.set(0,1,0),c.lookAt(0,0,-1);else if(t===Zs)n.up.set(0,-1,0),n.lookAt(-1,0,0),s.up.set(0,-1,0),s.lookAt(1,0,0),r.up.set(0,0,1),r.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),c.up.set(0,-1,0),c.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+t);for(let l of e)this.add(l),l.updateMatrixWorld()}update(t,e){this.parent===null&&this.updateMatrixWorld();let{renderTarget:n,activeMipmapLevel:s}=this;this.coordinateSystem!==t.coordinateSystem&&(this.coordinateSystem=t.coordinateSystem,this.updateCoordinateSystem());let[r,a,o,c,l,h]=this.children,d=t.getRenderTarget(),u=t.getActiveCubeFace(),f=t.getActiveMipmapLevel(),g=t.xr.enabled;t.xr.enabled=!1;let x=n.texture.generateMipmaps;n.texture.generateMipmaps=!1;let p=!1;t.isWebGLRenderer===!0?p=t.state.buffers.depth.getReversed():p=t.reversedDepthBuffer,t.setRenderTarget(n,0,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,r),t.setRenderTarget(n,1,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,a),t.setRenderTarget(n,2,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,o),t.setRenderTarget(n,3,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,c),t.setRenderTarget(n,4,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,l),n.texture.generateMipmaps=x,t.setRenderTarget(n,5,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,h),t.setRenderTarget(d,u,f),t.xr.enabled=g,n.texture.needsPMREMUpdate=!0}},Ho=class extends Ze{constructor(t=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=t}};var ih="\\[\\]\\.:\\/",Bp=new RegExp("["+ih+"]","g"),sh="[^"+ih+"]",kp="[^"+ih.replace("\\.","")+"]",Hp=/((?:WC+[\/:])*)/.source.replace("WC",sh),Vp=/(WCOD+)?/.source.replace("WCOD",kp),Gp=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",sh),Wp=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",sh),Xp=new RegExp("^"+Hp+Vp+Gp+Wp+"$"),qp=["material","materials","bones","map"],Il=class{constructor(t,e,n){let s=n||Oe.parseTrackName(e);this._targetGroup=t,this._bindings=t.subscribe_(e,s)}getValue(t,e){this.bind();let n=this._targetGroup.nCachedObjects_,s=this._bindings[n];s!==void 0&&s.getValue(t,e)}setValue(t,e){let n=this._bindings;for(let s=this._targetGroup.nCachedObjects_,r=n.length;s!==r;++s)n[s].setValue(t,e)}bind(){let t=this._bindings;for(let e=this._targetGroup.nCachedObjects_,n=t.length;e!==n;++e)t[e].bind()}unbind(){let t=this._bindings;for(let e=this._targetGroup.nCachedObjects_,n=t.length;e!==n;++e)t[e].unbind()}},Oe=class i{constructor(t,e,n){this.path=e,this.parsedPath=n||i.parseTrackName(e),this.node=i.findNode(t,this.parsedPath.nodeName),this.rootNode=t,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(t,e,n){return t&&t.isAnimationObjectGroup?new i.Composite(t,e,n):new i(t,e,n)}static sanitizeNodeName(t){return t.replace(/\s/g,"_").replace(Bp,"")}static parseTrackName(t){let e=Xp.exec(t);if(e===null)throw new Error("THREE.PropertyBinding: Cannot parse trackName: "+t);let n={nodeName:e[2],objectName:e[3],objectIndex:e[4],propertyName:e[5],propertyIndex:e[6]},s=n.nodeName&&n.nodeName.lastIndexOf(".");if(s!==void 0&&s!==-1){let r=n.nodeName.substring(s+1);qp.indexOf(r)!==-1&&(n.nodeName=n.nodeName.substring(0,s),n.objectName=r)}if(n.propertyName===null||n.propertyName.length===0)throw new Error("THREE.PropertyBinding: can not parse propertyName from trackName: "+t);return n}static findNode(t,e){if(e===void 0||e===""||e==="."||e===-1||e===t.name||e===t.uuid)return t;if(t.skeleton){let n=t.skeleton.getBoneByName(e);if(n!==void 0)return n}if(t.children){let n=function(r){for(let a=0;a<r.length;a++){let o=r[a];if(o.name===e||o.uuid===e)return o;let c=n(o.children);if(c)return c}return null},s=n(t.children);if(s)return s}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(t,e){t[e]=this.targetObject[this.propertyName]}_getValue_array(t,e){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)t[e++]=n[s]}_getValue_arrayElement(t,e){t[e]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(t,e){this.resolvedProperty.toArray(t,e)}_setValue_direct(t,e){this.targetObject[this.propertyName]=t[e]}_setValue_direct_setNeedsUpdate(t,e){this.targetObject[this.propertyName]=t[e],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(t,e){this.targetObject[this.propertyName]=t[e],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(t,e){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=t[e++]}_setValue_array_setNeedsUpdate(t,e){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=t[e++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(t,e){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=t[e++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(t,e){this.resolvedProperty[this.propertyIndex]=t[e]}_setValue_arrayElement_setNeedsUpdate(t,e){this.resolvedProperty[this.propertyIndex]=t[e],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(t,e){this.resolvedProperty[this.propertyIndex]=t[e],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(t,e){this.resolvedProperty.fromArray(t,e)}_setValue_fromArray_setNeedsUpdate(t,e){this.resolvedProperty.fromArray(t,e),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(t,e){this.resolvedProperty.fromArray(t,e),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(t,e){this.bind(),this.getValue(t,e)}_setValue_unbound(t,e){this.bind(),this.setValue(t,e)}bind(){let t=this.node,e=this.parsedPath,n=e.objectName,s=e.propertyName,r=e.propertyIndex;if(t||(t=i.findNode(this.rootNode,e.nodeName),this.node=t),this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!t){ee("PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let l=e.objectIndex;switch(n){case"materials":if(!t.material){se("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!t.material.materials){se("PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}t=t.material.materials;break;case"bones":if(!t.skeleton){se("PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}t=t.skeleton.bones;for(let h=0;h<t.length;h++)if(t[h].name===l){l=h;break}break;case"map":if("map"in t){t=t.map;break}if(!t.material){se("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!t.material.map){se("PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}t=t.material.map;break;default:if(t[n]===void 0){se("PropertyBinding: Can not bind to objectName of node undefined.",this);return}t=t[n]}if(l!==void 0){if(t[l]===void 0){se("PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,t);return}t=t[l]}}let a=t[s];if(a===void 0){let l=e.nodeName;se("PropertyBinding: Trying to update property for track: "+l+"."+s+" but it wasn't found.",t);return}let o=this.Versioning.None;this.targetObject=t,t.isMaterial===!0?o=this.Versioning.NeedsUpdate:t.isObject3D===!0&&(o=this.Versioning.MatrixWorldNeedsUpdate);let c=this.BindingType.Direct;if(r!==void 0){if(s==="morphTargetInfluences"){if(!t.geometry){se("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!t.geometry.morphAttributes){se("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}t.morphTargetDictionary[r]!==void 0&&(r=t.morphTargetDictionary[r])}c=this.BindingType.ArrayElement,this.resolvedProperty=a,this.propertyIndex=r}else a.fromArray!==void 0&&a.toArray!==void 0?(c=this.BindingType.HasFromToArray,this.resolvedProperty=a):Array.isArray(a)?(c=this.BindingType.EntireArray,this.resolvedProperty=a):this.propertyName=s;this.getValue=this.GetterByBindingType[c],this.setValue=this.SetterByBindingTypeAndVersioning[c][o]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}};Oe.Composite=Il;Oe.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};Oe.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};Oe.prototype.GetterByBindingType=[Oe.prototype._getValue_direct,Oe.prototype._getValue_array,Oe.prototype._getValue_arrayElement,Oe.prototype._getValue_toArray];Oe.prototype.SetterByBindingTypeAndVersioning=[[Oe.prototype._setValue_direct,Oe.prototype._setValue_direct_setNeedsUpdate,Oe.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[Oe.prototype._setValue_array,Oe.prototype._setValue_array_setNeedsUpdate,Oe.prototype._setValue_array_setMatrixWorldNeedsUpdate],[Oe.prototype._setValue_arrayElement,Oe.prototype._setValue_arrayElement_setNeedsUpdate,Oe.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[Oe.prototype._setValue_fromArray,Oe.prototype._setValue_fromArray_setNeedsUpdate,Oe.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var P_=new Float32Array(1);var es=class extends xo{constructor(t,e,n=1){super(t,e),this.isInstancedInterleavedBuffer=!0,this.meshPerAttribute=n}copy(t){return super.copy(t),this.meshPerAttribute=t.meshPerAttribute,this}clone(t){let e=super.clone(t);return e.meshPerAttribute=this.meshPerAttribute,e}toJSON(t){let e=super.toJSON(t);return e.isInstancedInterleavedBuffer=!0,e.meshPerAttribute=this.meshPerAttribute,e}};var hh=class hh{constructor(t,e,n,s){this.elements=[1,0,0,1],t!==void 0&&this.set(t,e,n,s)}identity(){return this.set(1,0,0,1),this}fromArray(t,e=0){for(let n=0;n<4;n++)this.elements[n]=t[n+e];return this}set(t,e,n,s){let r=this.elements;return r[0]=t,r[2]=e,r[1]=n,r[3]=s,this}};hh.prototype.isMatrix2=!0;var Ll=hh;var vu=new P,no=new P,Ws=new P,Xs=new P,_l=new P,Yp=new P,jp=new P,fa=class{constructor(t=new P,e=new P){this.start=t,this.end=e}set(t,e){return this.start.copy(t),this.end.copy(e),this}copy(t){return this.start.copy(t.start),this.end.copy(t.end),this}getCenter(t){return t.addVectors(this.start,this.end).multiplyScalar(.5)}delta(t){return t.subVectors(this.end,this.start)}distanceSq(){return this.start.distanceToSquared(this.end)}distance(){return this.start.distanceTo(this.end)}at(t,e){return this.delta(e).multiplyScalar(t).add(this.start)}closestPointToPointParameter(t,e){vu.subVectors(t,this.start),no.subVectors(this.end,this.start);let n=no.dot(no);if(n===0)return 0;let r=no.dot(vu)/n;return e&&(r=ae(r,0,1)),r}closestPointToPoint(t,e,n){let s=this.closestPointToPointParameter(t,e);return this.delta(n).multiplyScalar(s).add(this.start)}distanceSqToLine3(t,e=Yp,n=jp){let s=10000000000000001e-32,r,a,o=this.start,c=t.start,l=this.end,h=t.end;Ws.subVectors(l,o),Xs.subVectors(h,c),_l.subVectors(o,c);let d=Ws.dot(Ws),u=Xs.dot(Xs),f=Xs.dot(_l);if(d<=s&&u<=s)return e.copy(o),n.copy(c),e.sub(n),e.dot(e);if(d<=s)r=0,a=f/u,a=ae(a,0,1);else{let g=Ws.dot(_l);if(u<=s)a=0,r=ae(-g/d,0,1);else{let x=Ws.dot(Xs),p=d*u-x*x;p!==0?r=ae((x*f-g*u)/p,0,1):r=0,a=(x*r+f)/u,a<0?(a=0,r=ae(-g/d,0,1)):a>1&&(a=1,r=ae((x-g)/d,0,1))}}return e.copy(o).addScaledVector(Ws,r),n.copy(c).addScaledVector(Xs,a),e.distanceToSquared(n)}applyMatrix4(t){return this.start.applyMatrix4(t),this.end.applyMatrix4(t),this}equals(t){return t.start.equals(this.start)&&t.end.equals(this.end)}clone(){return new this.constructor().copy(this)}};function rh(i,t,e,n){let s=Zp(n);switch(e){case $l:return i*t;case Zo:return i*t/s.components*s.byteLength;case $o:return i*t/s.components*s.byteLength;case xi:return i*t*2/s.components*s.byteLength;case Jo:return i*t*2/s.components*s.byteLength;case Jl:return i*t*3/s.components*s.byteLength;case Wn:return i*t*4/s.components*s.byteLength;case Ko:return i*t*4/s.components*s.byteLength;case va:case xa:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*8;case _a:case ya:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*16;case tc:case nc:return Math.max(i,16)*Math.max(t,8)/4;case Qo:case ec:return Math.max(i,8)*Math.max(t,8)/2;case ic:case sc:case ac:case oc:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*8;case rc:case Ma:case cc:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*16;case lc:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*16;case hc:return Math.floor((i+4)/5)*Math.floor((t+3)/4)*16;case uc:return Math.floor((i+4)/5)*Math.floor((t+4)/5)*16;case dc:return Math.floor((i+5)/6)*Math.floor((t+4)/5)*16;case fc:return Math.floor((i+5)/6)*Math.floor((t+5)/6)*16;case pc:return Math.floor((i+7)/8)*Math.floor((t+4)/5)*16;case mc:return Math.floor((i+7)/8)*Math.floor((t+5)/6)*16;case gc:return Math.floor((i+7)/8)*Math.floor((t+7)/8)*16;case vc:return Math.floor((i+9)/10)*Math.floor((t+4)/5)*16;case xc:return Math.floor((i+9)/10)*Math.floor((t+5)/6)*16;case _c:return Math.floor((i+9)/10)*Math.floor((t+7)/8)*16;case yc:return Math.floor((i+9)/10)*Math.floor((t+9)/10)*16;case Mc:return Math.floor((i+11)/12)*Math.floor((t+9)/10)*16;case Sc:return Math.floor((i+11)/12)*Math.floor((t+11)/12)*16;case bc:case Ec:case wc:return Math.ceil(i/4)*Math.ceil(t/4)*16;case Tc:case Ac:return Math.ceil(i/4)*Math.ceil(t/4)*8;case Sa:case Rc:return Math.ceil(i/4)*Math.ceil(t/4)*16}throw new Error(`Unable to determine texture byte length for ${e} format.`)}function Zp(i){switch(i){case Cn:case ql:return{byteLength:1,components:1};case lr:case Yl:case On:return{byteLength:2,components:1};case Yo:case jo:return{byteLength:2,components:4};case ai:case qo:case Gn:return{byteLength:4,components:1};case jl:case Zl:return{byteLength:4,components:3}}throw new Error(`THREE.TextureUtils: Unknown texture type ${i}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"186"}}));typeof window<"u"&&(window.__THREE__?ee("WARNING: Multiple instances of Three.js being imported."):window.__THREE__="186");function Cd(){let i=null,t=!1,e=null,n=null;function s(r,a){n=i.requestAnimationFrame(s),e(r,a)}return{start:function(){t!==!0&&e!==null&&i!==null&&(n=i.requestAnimationFrame(s),t=!0)},stop:function(){i!==null&&i.cancelAnimationFrame(n),t=!1},setAnimationLoop:function(r){e=r},setContext:function(r){i=r}}}function Jp(i){let t=new WeakMap;function e(o,c){let l=o.array,h=o.usage,d=l.byteLength,u=i.createBuffer();i.bindBuffer(c,u),i.bufferData(c,l,h),o.onUploadCallback();let f;if(l instanceof Float32Array)f=i.FLOAT;else if(typeof Float16Array<"u"&&l instanceof Float16Array)f=i.HALF_FLOAT;else if(l instanceof Uint16Array)o.isFloat16BufferAttribute?f=i.HALF_FLOAT:f=i.UNSIGNED_SHORT;else if(l instanceof Int16Array)f=i.SHORT;else if(l instanceof Uint32Array)f=i.UNSIGNED_INT;else if(l instanceof Int32Array)f=i.INT;else if(l instanceof Int8Array)f=i.BYTE;else if(l instanceof Uint8Array)f=i.UNSIGNED_BYTE;else if(l instanceof Uint8ClampedArray)f=i.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+l);return{buffer:u,type:f,bytesPerElement:l.BYTES_PER_ELEMENT,version:o.version,size:d}}function n(o,c,l){let h=c.array,d=c.updateRanges;if(i.bindBuffer(l,o),d.length===0)i.bufferSubData(l,0,h);else{d.sort((f,g)=>f.start-g.start);let u=0;for(let f=1;f<d.length;f++){let g=d[u],x=d[f];x.start<=g.start+g.count+1?g.count=Math.max(g.count,x.start+x.count-g.start):(++u,d[u]=x)}d.length=u+1;for(let f=0,g=d.length;f<g;f++){let x=d[f];i.bufferSubData(l,x.start*h.BYTES_PER_ELEMENT,h,x.start,x.count)}c.clearUpdateRanges()}c.onUploadCallback()}function s(o){return o.isInterleavedBufferAttribute&&(o=o.data),t.get(o)}function r(o){o.isInterleavedBufferAttribute&&(o=o.data);let c=t.get(o);c&&(i.deleteBuffer(c.buffer),t.delete(o))}function a(o,c){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){let h=t.get(o);(!h||h.version<o.version)&&t.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}let l=t.get(o);if(l===void 0)t.set(o,e(o,c));else if(l.version<o.version){if(l.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");n(l.buffer,o,c),l.version=o.version}}return{get:s,remove:r,update:a}}var Kp=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,Qp=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,t0=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,e0=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,n0=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,i0=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,s0=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,r0=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,a0=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec4 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 );
	}
#endif`,o0=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,c0=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,l0=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,h0=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,u0=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,d0=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,f0=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,p0=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,m0=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,g0=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,v0=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,x0=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,_0=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,y0=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec4( 1.0 );
#endif
#ifdef USE_COLOR_ALPHA
	vColor *= color;
#elif defined( USE_COLOR )
	vColor.rgb *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.rgb *= instanceColor.rgb;
#endif
#ifdef USE_BATCHING_COLOR
	vColor *= getBatchingColor( getIndirectIndex( gl_DrawID ) );
#endif`,M0=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
#define inverseTransformDirection transformDirectionByInverseViewMatrix
vec3 transformNormalByInverseViewMatrix( in vec3 normal, in mat4 viewMatrix ) {
	return normalize( ( vec4( normal, 0.0 ) * viewMatrix ).xyz );
}
vec3 transformDirectionByInverseViewMatrix( in vec3 dir, in mat4 viewMatrix ) {
	return normalize( ( vec4( dir, 0.0 ) * viewMatrix ).xyz );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,S0=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,b0=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
#endif`,E0=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,w0=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,T0=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,A0=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,R0="gl_FragColor = linearToOutputTexel( gl_FragColor );",C0=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,P0=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * reflectVec );
		#ifdef ENVMAP_BLENDING_MULTIPLY
			outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_MIX )
			outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_ADD )
			outgoingLight += envColor.xyz * specularStrength * reflectivity;
		#endif
	#endif
#endif`,I0=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,L0=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,D0=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,U0=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,N0=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,F0=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,z0=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,O0=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,B0=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,k0=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,H0=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,V0=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,G0=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_SUN_LIGHTS > 0
	struct SunLight {
		vec3 direction;
		vec3 color;
	};
	uniform SunLight sunLights[ NUM_SUN_LIGHTS ];
	void getSunLightInfo( const in SunLight sunLight, out IncidentLight light ) {
		light.color = sunLight.color;
		light.direction = sunLight.direction;
		light.visible = true;
	}
#endif
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif
#include <lightprobes_pars_fragment>`,W0=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, pow4( roughness ) ) );
			reflectVec = transformDirectionByInverseViewMatrix( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_RETROREFLECTION
		vec3 getIBLRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 retroVec = normalize( mix( viewDir, normal, pow4( roughness ) ) );
				retroVec = transformDirectionByInverseViewMatrix( retroVec, viewMatrix );
				vec4 envMapColor = textureCubeUV( envMap, envMapRotation * retroVec, roughness );
				return envMapColor.rgb * envMapIntensity;
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
		#ifdef USE_RETROREFLECTION
			vec3 getIBLAnisotropyRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
				#ifdef ENVMAP_TYPE_CUBE_UV
					vec3 bentNormal = cross( bitangent, viewDir );
					bentNormal = normalize( cross( bentNormal, bitangent ) );
					bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
					return getIBLRetroRadiance( viewDir, bentNormal, roughness );
				#else
					return vec3( 0.0 );
				#endif
			}
		#endif
	#endif
#endif`,X0=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,q0=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,Y0=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,j0=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,Z0=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.diffuseContribution = diffuseColor.rgb * ( 1.0 - metalnessFactor );
material.metalness = metalnessFactor;
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor;
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = vec3( 0.04 );
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_RETROREFLECTION
	material.retroreflectivity = retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.0001, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,$0=`uniform sampler2D dfgLUT;
struct PhysicalMaterial {
	vec3 diffuseColor;
	vec3 diffuseContribution;
	vec3 specularColor;
	vec3 specularColorBlended;
	float roughness;
	float metalness;
	float specularF90;
	float dispersion;
	vec2 dfg;
	vec3 multiScatteringCompensation;
	#ifdef USE_RETROREFLECTION
		float retroreflectivity;
	#endif
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0Dielectric;
		vec3 iridescenceF0Metallic;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		return 0.5 / max( gv + gl, EPSILON );
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColorBlended;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transpose( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float rInv = 1.0 / ( roughness + 0.1 );
	float a = -1.9362 + 1.0678 * roughness + 0.4573 * r2 - 0.8469 * rInv;
	float b = -0.6014 + 0.5538 * roughness - 0.4670 * r2 - 0.1255 * rInv;
	float DG = exp( a * dotNV + b );
	return saturate( DG );
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec2 fab, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec2 fab, const in vec3 specularColor, const in float specularF90, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColorBlended * t2.x + ( material.specularF90 - material.specularColorBlended ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseContribution * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
		#ifdef USE_CLEARCOAT
			vec3 Ncc = geometryClearcoatNormal;
			vec2 uvClearcoat = LTC_Uv( Ncc, viewDir, material.clearcoatRoughness );
			vec4 t1Clearcoat = texture2D( ltc_1, uvClearcoat );
			vec4 t2Clearcoat = texture2D( ltc_2, uvClearcoat );
			mat3 mInvClearcoat = mat3(
				vec3( t1Clearcoat.x, 0, t1Clearcoat.y ),
				vec3(             0, 1,             0 ),
				vec3( t1Clearcoat.z, 0, t1Clearcoat.w )
			);
			vec3 fresnelClearcoat = material.clearcoatF0 * t2Clearcoat.x + ( material.clearcoatF90 - material.clearcoatF0 ) * t2Clearcoat.y;
			clearcoatSpecularDirect += lightColor * fresnelClearcoat * LTC_Evaluate( Ncc, viewDir, position, mInvClearcoat, rectCoords );
		#endif
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
 
 		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
 
 		float sheenAlbedoV = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
 		float sheenAlbedoL = IBLSheenBRDF( geometryNormal, directLight.direction, material.sheenRoughness );
 
 		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * max( sheenAlbedoV, sheenAlbedoL );
 
 		irradiance *= sheenEnergyComp;
 
 	#endif
	vec3 specularBRDF = BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	#ifdef USE_RETROREFLECTION
		vec3 retroViewDir = reflect( - geometryViewDir, geometryNormal );
		vec3 retroSpecularBRDF = BRDF_GGX( directLight.direction, retroViewDir, geometryNormal, material );
		specularBRDF = mix( specularBRDF, retroSpecularBRDF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directSpecular += irradiance * specularBRDF * material.multiScatteringCompensation;
	vec3 halfDir = normalize( directLight.direction + geometryViewDir );
	float dotVH = saturate( dot( geometryViewDir, halfDir ) );
	vec3 F = F_Schlick( material.specularColor, material.specularF90, dotVH );
	#ifdef USE_RETROREFLECTION
		vec3 retroHalfDir = normalize( directLight.direction + retroViewDir );
		float dotRetroVH = saturate( dot( retroViewDir, retroHalfDir ) );
		vec3 retroF = F_Schlick( material.specularColor, material.specularF90, dotRetroVH );
		F = mix( F, retroF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - F );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScattering, multiScattering );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScattering, multiScattering );
	#endif
	vec3 diffuse = irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - singleScattering - multiScattering );
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		sheenSpecularIndirect += irradiance * material.sheenColor * sheenAlbedo * RECIPROCAL_PI;
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		diffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectDiffuse += diffuse;
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness ) * RECIPROCAL_PI;
 	#endif
	vec3 singleScatteringDielectric = vec3( 0.0 );
	vec3 multiScatteringDielectric = vec3( 0.0 );
	vec3 singleScatteringMetallic = vec3( 0.0 );
	vec3 multiScatteringMetallic = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscatteringIridescence( material.dfg, material.diffuseColor, material.specularF90, material.iridescence, material.iridescenceF0Metallic, singleScatteringMetallic, multiScatteringMetallic );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscattering( material.dfg, material.diffuseColor, material.specularF90, singleScatteringMetallic, multiScatteringMetallic );
	#endif
	vec3 singleScattering = mix( singleScatteringDielectric, singleScatteringMetallic, material.metalness );
	vec3 multiScattering = mix( multiScatteringDielectric, multiScatteringMetallic, material.metalness );
	vec3 totalScatteringDielectric = singleScatteringDielectric + multiScatteringDielectric;
	vec3 diffuse = material.diffuseContribution * ( 1.0 - totalScatteringDielectric );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	vec3 indirectSpecular = radiance * singleScattering;
	indirectSpecular += multiScattering * cosineWeightedIrradiance;
	vec3 indirectDiffuse = diffuse * cosineWeightedIrradiance;
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		indirectSpecular *= sheenEnergyComp;
		indirectDiffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectSpecular += indirectSpecular;
	reflectedLight.indirectDiffuse += indirectDiffuse;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,J0=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		vec3 iridescenceFresnelDielectric = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		vec3 iridescenceFresnelMetallic = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.diffuseColor );
		material.iridescenceFresnel = mix( iridescenceFresnelDielectric, iridescenceFresnelMetallic, material.metalness );
		material.iridescenceF0Dielectric = Schlick_to_F0( iridescenceFresnelDielectric, 1.0, dotNVi );
		material.iridescenceF0Metallic = Schlick_to_F0( iridescenceFresnelMetallic, 1.0, dotNVi );
	}
#endif
#ifdef STANDARD
	float dotNVms = saturate( dot( geometryNormal, geometryViewDir ) );
	material.dfg = texture2D( dfgLUT, vec2( material.roughness, dotNVms ) ).rg;
	#if ( NUM_SUN_LIGHTS > 0 || NUM_DIR_LIGHTS > 0 || NUM_POINT_LIGHTS > 0 || NUM_SPOT_LIGHTS > 0 )
		float EssMs = material.dfg.x + material.dfg.y;
		material.multiScatteringCompensation = 1.0 + material.specularColorBlended * ( 1.0 / EssMs - 1.0 );
	#endif
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS ) && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SUN_LIGHTS > 0 ) && defined( RE_Direct )
	SunLight sunLight;
	#if defined( USE_SHADOWMAP ) && NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHTS; i ++ ) {
		sunLight = sunLights[ i ];
		getSunLightInfo( sunLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SUN_LIGHT_SHADOWS )
		sunLightShadow = sunLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getSunShadow( sunShadowMap[ i ], sunLightShadow, UNROLLED_LOOP_INDEX ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
	#ifdef USE_LIGHT_PROBES_GRID
		vec3 probeWorldPos = ( ( vec4( geometryPosition, 1.0 ) - viewMatrix[ 3 ] ) * viewMatrix ).xyz;
		vec3 probeWorldNormal = transformNormalByInverseViewMatrix( geometryNormal, viewMatrix );
		irradiance += getLightProbeGridIrradiance( probeWorldPos, probeWorldNormal );
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,K0=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( ENVMAP_TYPE_CUBE_UV )
		#if defined( STANDARD ) || defined( LAMBERT ) || defined( PHONG )
			iblIrradiance += getIBLIrradiance( geometryNormal );
		#endif
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		vec3 iblRadiance = getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		vec3 iblRadiance = getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_RETROREFLECTION
		#ifdef USE_ANISOTROPY
			vec3 retroIBLRadiance = getIBLAnisotropyRetroRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
		#else
			vec3 retroIBLRadiance = getIBLRetroRadiance( geometryViewDir, geometryNormal, material.roughness );
		#endif
		iblRadiance = mix( iblRadiance, retroIBLRadiance, saturate( material.retroreflectivity ) );
	#endif
	radiance += iblRadiance;
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,Q0=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,tm=`#ifdef USE_LIGHT_PROBES_GRID
uniform highp sampler3D probesSH;
uniform vec3 probesMin;
uniform vec3 probesMax;
uniform vec3 probesResolution;
vec3 getLightProbeGridIrradiance( vec3 worldPos, vec3 worldNormal ) {
	vec3 res = probesResolution;
	vec3 gridRange = probesMax - probesMin;
	vec3 resMinusOne = res - 1.0;
	vec3 probeSpacing = gridRange / resMinusOne;
	vec3 samplePos = worldPos + worldNormal * probeSpacing * 0.5;
	vec3 uvw = clamp( ( samplePos - probesMin ) / gridRange, 0.0, 1.0 );
	uvw = uvw * resMinusOne / res + 0.5 / res;
	float nz          = res.z;
	float paddedSlices = nz + 2.0;
	float atlasDepth  = 7.0 * paddedSlices;
	float uvZBase     = uvw.z * nz + 1.0;
	vec4 s0 = texture( probesSH, vec3( uvw.xy, ( uvZBase                       ) / atlasDepth ) );
	vec4 s1 = texture( probesSH, vec3( uvw.xy, ( uvZBase +       paddedSlices   ) / atlasDepth ) );
	vec4 s2 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 2.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s3 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 3.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s4 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 4.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s5 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 5.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s6 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 6.0 * paddedSlices   ) / atlasDepth ) );
	vec3 c0 = s0.xyz;
	vec3 c1 = vec3( s0.w, s1.xy );
	vec3 c2 = vec3( s1.zw, s2.x );
	vec3 c3 = s2.yzw;
	vec3 c4 = s3.xyz;
	vec3 c5 = vec3( s3.w, s4.xy );
	vec3 c6 = vec3( s4.zw, s5.x );
	vec3 c7 = s5.yzw;
	vec3 c8 = s6.xyz;
	float x = worldNormal.x, y = worldNormal.y, z = worldNormal.z;
	vec3 result = c0 * 0.886227;
	result += c1 * 2.0 * 0.511664 * y;
	result += c2 * 2.0 * 0.511664 * z;
	result += c3 * 2.0 * 0.511664 * x;
	result += c4 * 2.0 * 0.429043 * x * y;
	result += c5 * 2.0 * 0.429043 * y * z;
	result += c6 * ( 0.743125 * z * z - 0.247708 );
	result += c7 * 2.0 * 0.429043 * x * z;
	result += c8 * 0.429043 * ( x * x - y * y );
	return max( result, vec3( 0.0 ) );
}
#endif`,em=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,nm=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,im=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,sm=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,rm=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,am=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,om=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,cm=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,lm=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,hm=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,um=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,dm=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,fm=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,pm=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,mm=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,gm=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#ifdef DOUBLE_SIDED
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#ifdef DOUBLE_SIDED
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,vm=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#if defined( USE_PACKED_NORMALMAP )
		mapN = vec3( mapN.xy, sqrt( saturate( 1.0 - dot( mapN.xy, mapN.xy ) ) ) );
	#endif
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,xm=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,_m=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,ym=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
		#ifdef FLIP_SIDED
			vBitangent = - vBitangent;
		#endif
	#endif
#endif`,Mm=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,Sm=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,bm=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,Em=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,wm=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,Tm=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,Am=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	#ifdef USE_REVERSED_DEPTH_BUFFER
	
		return depth * ( far - near ) - far;
	#else
		return depth * ( near - far ) - near;
	#endif
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	
	#ifdef USE_REVERSED_DEPTH_BUFFER
		return ( near * far ) / ( ( near - far ) * depth - near );
	#else
		return ( near * far ) / ( ( far - near ) * depth - far );
	#endif
}`,Rm=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,Cm=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,Pm=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,Im=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,Lm=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,Dm=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,Um=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		#define SUN_LIGHT_CASCADES 2
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#else
			uniform sampler2D sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#endif
		uniform mat4 sunShadowMatrix[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		uniform vec4 sunShadowCascade[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
		struct SunLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SunLightShadow sunLightShadows[ NUM_SUN_LIGHT_SHADOWS ];
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#else
			uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#endif
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#else
			uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#endif
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform samplerCubeShadow pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#elif defined( SHADOWMAP_TYPE_BASIC )
			uniform samplerCube pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#endif
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float interleavedGradientNoise( vec2 position ) {
			return fract( 52.9829189 * fract( dot( position, vec2( 0.06711056, 0.00583715 ) ) ) );
		}
		vec2 vogelDiskSample( int sampleIndex, int samplesCount, float phi ) {
			const float goldenAngle = 2.399963229728653;
			float r = sqrt( ( float( sampleIndex ) + 0.5 ) / float( samplesCount ) );
			float theta = float( sampleIndex ) * goldenAngle + phi;
			return vec2( cos( theta ), sin( theta ) ) * r;
		}
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float getShadow( sampler2DShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
				float radius = shadowRadius * texelSize.x;
				float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
				shadow = (
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 0, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 1, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 2, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 3, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 4, 5, phi ) * radius, shadowCoord.z ) )
				) * 0.2;
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#elif defined( SHADOWMAP_TYPE_VSM )
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 distribution = texture2D( shadowMap, shadowCoord.xy ).rg;
				float mean = distribution.x;
				float variance = distribution.y * distribution.y;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					float hard_shadow = step( mean, shadowCoord.z );
				#else
					float hard_shadow = step( shadowCoord.z, mean );
				#endif
				
				if ( hard_shadow == 1.0 ) {
					shadow = 1.0;
				} else {
					variance = max( variance, 0.0000001 );
					float d = shadowCoord.z - mean;
					float p_max = variance / ( variance + d * d );
					p_max = clamp( ( p_max - 0.3 ) / 0.65, 0.0, 1.0 );
					shadow = max( hard_shadow, p_max );
				}
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#else
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				float depth = texture2D( shadowMap, shadowCoord.xy ).r;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					shadow = step( depth, shadowCoord.z );
				#else
					shadow = step( shadowCoord.z, depth );
				#endif
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#endif
	#if NUM_SUN_LIGHT_SHADOWS > 0
		float getSunShadow(
			#if defined( SHADOWMAP_TYPE_PCF )
				sampler2DShadow shadowMap,
			#else
				sampler2D shadowMap,
			#endif
			SunLightShadow sunLightShadow,
			int shadowIndex
		) {
			vec4 shadowWorldPosition = vec4( vSunShadowWorldPosition.xyz + vSunShadowWorldNormal * sunLightShadow.shadowNormalBias, 1.0 );
			float viewDepth = vSunShadowWorldPosition.w;
			int cascadeOffset = shadowIndex * SUN_LIGHT_CASCADES;
			float shadow = 1.0;
			for ( int i = SUN_LIGHT_CASCADES - 1; i >= 0; i -- ) {
				vec4 cascade = sunShadowCascade[ cascadeOffset + i ];
				if ( viewDepth >= cascade.x && viewDepth < cascade.y ) {
					float cascadeShadow = getShadow(
						shadowMap,
						sunLightShadow.shadowMapSize,
						sunLightShadow.shadowIntensity,
						sunLightShadow.shadowBias,
						sunLightShadow.shadowRadius,
						sunShadowMatrix[ cascadeOffset + i ] * shadowWorldPosition
					);
					shadow = mix( cascadeShadow, shadow, smoothstep( cascade.z, cascade.y, viewDepth ) );
				}
			}
			return shadow;
		}
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#if defined( SHADOWMAP_TYPE_PCF )
	float getPointShadow( samplerCubeShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			#ifdef USE_REVERSED_DEPTH_BUFFER
				float dp = ( shadowCameraNear * ( shadowCameraFar - viewSpaceZ ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp -= shadowBias;
			#else
				float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp += shadowBias;
			#endif
			float texelSize = shadowRadius / shadowMapSize.x;
			vec3 absDir = abs( bd3D );
			vec3 tangent = absDir.x > absDir.z ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 );
			tangent = normalize( cross( bd3D, tangent ) );
			vec3 bitangent = cross( bd3D, tangent );
			float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
			vec2 sample0 = vogelDiskSample( 0, 5, phi );
			vec2 sample1 = vogelDiskSample( 1, 5, phi );
			vec2 sample2 = vogelDiskSample( 2, 5, phi );
			vec2 sample3 = vogelDiskSample( 3, 5, phi );
			vec2 sample4 = vogelDiskSample( 4, 5, phi );
			shadow = (
				texture( shadowMap, vec4( bd3D + ( tangent * sample0.x + bitangent * sample0.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample1.x + bitangent * sample1.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample2.x + bitangent * sample2.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample3.x + bitangent * sample3.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample4.x + bitangent * sample4.y ) * texelSize, dp ) )
			) * 0.2;
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#elif defined( SHADOWMAP_TYPE_BASIC )
	float getPointShadow( samplerCube shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			float depth = textureCube( shadowMap, bd3D ).r;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				depth = 1.0 - depth;
			#endif
			shadow = step( dp, depth );
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#endif
	#endif
#endif`,Nm=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,Fm=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_SUN_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	#ifdef HAS_NORMAL
		vec3 shadowWorldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
	#else
		vec3 shadowWorldNormal = vec3( 0.0 );
	#endif
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_SUN_LIGHT_SHADOWS > 0
		vSunShadowWorldPosition = vec4( worldPosition.xyz, - mvPosition.z );
		vSunShadowWorldNormal = shadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,zm=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHT_SHADOWS; i ++ ) {
		sunLight = sunLightShadows[ i ];
		shadow *= receiveShadow ? getSunShadow( sunShadowMap[ i ], sunLight, UNROLLED_LOOP_INDEX ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0 && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,Om=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,Bm=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,km=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,Hm=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,Vm=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,Gm=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,Wm=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,Xm=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,qm=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseContribution, material.specularColorBlended, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,Ym=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,jm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,Zm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,$m=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,Jm=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,Km=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,Qm=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,tg=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,eg=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vWorldDirection );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,ng=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,ig=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,sg=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,rg=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,ag=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,og=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = vec4( dist, 0.0, 0.0, 1.0 );
}`,cg=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,lg=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,hg=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,ug=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,dg=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,fg=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,pg=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,mg=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,gg=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,vg=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,xg=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,_g=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( normalize( normal ) * 0.5 + 0.5, diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,yg=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Mg=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Sg=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,bg=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_RETROREFLECTION
	uniform float retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
 
		outgoingLight = outgoingLight + sheenSpecularDirect + sheenSpecularIndirect;
 
 	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Eg=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,wg=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Tg=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,Ag=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Rg=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Cg=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Pg=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,Ig=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,me={alphahash_fragment:Kp,alphahash_pars_fragment:Qp,alphamap_fragment:t0,alphamap_pars_fragment:e0,alphatest_fragment:n0,alphatest_pars_fragment:i0,aomap_fragment:s0,aomap_pars_fragment:r0,batching_pars_vertex:a0,batching_vertex:o0,begin_vertex:c0,beginnormal_vertex:l0,bsdfs:h0,iridescence_fragment:u0,bumpmap_pars_fragment:d0,clipping_planes_fragment:f0,clipping_planes_pars_fragment:p0,clipping_planes_pars_vertex:m0,clipping_planes_vertex:g0,color_fragment:v0,color_pars_fragment:x0,color_pars_vertex:_0,color_vertex:y0,common:M0,cube_uv_reflection_fragment:S0,defaultnormal_vertex:b0,displacementmap_pars_vertex:E0,displacementmap_vertex:w0,emissivemap_fragment:T0,emissivemap_pars_fragment:A0,colorspace_fragment:R0,colorspace_pars_fragment:C0,envmap_fragment:P0,envmap_common_pars_fragment:I0,envmap_pars_fragment:L0,envmap_pars_vertex:D0,envmap_physical_pars_fragment:W0,envmap_vertex:U0,fog_vertex:N0,fog_pars_vertex:F0,fog_fragment:z0,fog_pars_fragment:O0,gradientmap_pars_fragment:B0,lightmap_pars_fragment:k0,lights_lambert_fragment:H0,lights_lambert_pars_fragment:V0,lights_pars_begin:G0,lights_toon_fragment:X0,lights_toon_pars_fragment:q0,lights_phong_fragment:Y0,lights_phong_pars_fragment:j0,lights_physical_fragment:Z0,lights_physical_pars_fragment:$0,lights_fragment_begin:J0,lights_fragment_maps:K0,lights_fragment_end:Q0,lightprobes_pars_fragment:tm,logdepthbuf_fragment:em,logdepthbuf_pars_fragment:nm,logdepthbuf_pars_vertex:im,logdepthbuf_vertex:sm,map_fragment:rm,map_pars_fragment:am,map_particle_fragment:om,map_particle_pars_fragment:cm,metalnessmap_fragment:lm,metalnessmap_pars_fragment:hm,morphinstance_vertex:um,morphcolor_vertex:dm,morphnormal_vertex:fm,morphtarget_pars_vertex:pm,morphtarget_vertex:mm,normal_fragment_begin:gm,normal_fragment_maps:vm,normal_pars_fragment:xm,normal_pars_vertex:_m,normal_vertex:ym,normalmap_pars_fragment:Mm,clearcoat_normal_fragment_begin:Sm,clearcoat_normal_fragment_maps:bm,clearcoat_pars_fragment:Em,iridescence_pars_fragment:wm,opaque_fragment:Tm,packing:Am,premultiplied_alpha_fragment:Rm,project_vertex:Cm,dithering_fragment:Pm,dithering_pars_fragment:Im,roughnessmap_fragment:Lm,roughnessmap_pars_fragment:Dm,shadowmap_pars_fragment:Um,shadowmap_pars_vertex:Nm,shadowmap_vertex:Fm,shadowmask_pars_fragment:zm,skinbase_vertex:Om,skinning_pars_vertex:Bm,skinning_vertex:km,skinnormal_vertex:Hm,specularmap_fragment:Vm,specularmap_pars_fragment:Gm,tonemapping_fragment:Wm,tonemapping_pars_fragment:Xm,transmission_fragment:qm,transmission_pars_fragment:Ym,uv_pars_fragment:jm,uv_pars_vertex:Zm,uv_vertex:$m,worldpos_vertex:Jm,background_vert:Km,background_frag:Qm,backgroundCube_vert:tg,backgroundCube_frag:eg,cube_vert:ng,cube_frag:ig,depth_vert:sg,depth_frag:rg,distance_vert:ag,distance_frag:og,equirect_vert:cg,equirect_frag:lg,linedashed_vert:hg,linedashed_frag:ug,meshbasic_vert:dg,meshbasic_frag:fg,meshlambert_vert:pg,meshlambert_frag:mg,meshmatcap_vert:gg,meshmatcap_frag:vg,meshnormal_vert:xg,meshnormal_frag:_g,meshphong_vert:yg,meshphong_frag:Mg,meshphysical_vert:Sg,meshphysical_frag:bg,meshtoon_vert:Eg,meshtoon_frag:wg,points_vert:Tg,points_frag:Ag,shadow_vert:Rg,shadow_frag:Cg,sprite_vert:Pg,sprite_frag:Ig},Ct={common:{diffuse:{value:new Ot(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new ce},alphaMap:{value:null},alphaMapTransform:{value:new ce},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new ce}},envmap:{envMap:{value:null},envMapRotation:{value:new ce},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new ce}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new ce}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new ce},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new ce},normalScale:{value:new mt(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new ce},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new ce}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new ce}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new ce}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new Ot(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},sunLights:{value:[],properties:{direction:{},color:{}}},sunLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},sunShadowMatrix:{value:[]},sunShadowCascade:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new P},probesMax:{value:new P},probesResolution:{value:new P}},points:{diffuse:{value:new Ot(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new ce},alphaTest:{value:0},uvTransform:{value:new ce}},sprite:{diffuse:{value:new Ot(16777215)},opacity:{value:1},center:{value:new mt(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new ce},alphaMap:{value:null},alphaMapTransform:{value:new ce},alphaTest:{value:0}}},bn={basic:{uniforms:pn([Ct.common,Ct.specularmap,Ct.envmap,Ct.aomap,Ct.lightmap,Ct.fog]),vertexShader:me.meshbasic_vert,fragmentShader:me.meshbasic_frag},lambert:{uniforms:pn([Ct.common,Ct.specularmap,Ct.envmap,Ct.aomap,Ct.lightmap,Ct.emissivemap,Ct.bumpmap,Ct.normalmap,Ct.displacementmap,Ct.fog,Ct.lights,{emissive:{value:new Ot(0)},envMapIntensity:{value:1}}]),vertexShader:me.meshlambert_vert,fragmentShader:me.meshlambert_frag},phong:{uniforms:pn([Ct.common,Ct.specularmap,Ct.envmap,Ct.aomap,Ct.lightmap,Ct.emissivemap,Ct.bumpmap,Ct.normalmap,Ct.displacementmap,Ct.fog,Ct.lights,{emissive:{value:new Ot(0)},specular:{value:new Ot(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:me.meshphong_vert,fragmentShader:me.meshphong_frag},standard:{uniforms:pn([Ct.common,Ct.envmap,Ct.aomap,Ct.lightmap,Ct.emissivemap,Ct.bumpmap,Ct.normalmap,Ct.displacementmap,Ct.roughnessmap,Ct.metalnessmap,Ct.fog,Ct.lights,{emissive:{value:new Ot(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:me.meshphysical_vert,fragmentShader:me.meshphysical_frag},toon:{uniforms:pn([Ct.common,Ct.aomap,Ct.lightmap,Ct.emissivemap,Ct.bumpmap,Ct.normalmap,Ct.displacementmap,Ct.gradientmap,Ct.fog,Ct.lights,{emissive:{value:new Ot(0)}}]),vertexShader:me.meshtoon_vert,fragmentShader:me.meshtoon_frag},matcap:{uniforms:pn([Ct.common,Ct.bumpmap,Ct.normalmap,Ct.displacementmap,Ct.fog,{matcap:{value:null}}]),vertexShader:me.meshmatcap_vert,fragmentShader:me.meshmatcap_frag},points:{uniforms:pn([Ct.points,Ct.fog]),vertexShader:me.points_vert,fragmentShader:me.points_frag},dashed:{uniforms:pn([Ct.common,Ct.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:me.linedashed_vert,fragmentShader:me.linedashed_frag},depth:{uniforms:pn([Ct.common,Ct.displacementmap]),vertexShader:me.depth_vert,fragmentShader:me.depth_frag},normal:{uniforms:pn([Ct.common,Ct.bumpmap,Ct.normalmap,Ct.displacementmap,{opacity:{value:1}}]),vertexShader:me.meshnormal_vert,fragmentShader:me.meshnormal_frag},sprite:{uniforms:pn([Ct.sprite,Ct.fog]),vertexShader:me.sprite_vert,fragmentShader:me.sprite_frag},background:{uniforms:{uvTransform:{value:new ce},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:me.background_vert,fragmentShader:me.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new ce}},vertexShader:me.backgroundCube_vert,fragmentShader:me.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:me.cube_vert,fragmentShader:me.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:me.equirect_vert,fragmentShader:me.equirect_frag},distance:{uniforms:pn([Ct.common,Ct.displacementmap,{referencePosition:{value:new P},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:me.distance_vert,fragmentShader:me.distance_frag},shadow:{uniforms:pn([Ct.lights,Ct.fog,{color:{value:new Ot(0)},opacity:{value:1}}]),vertexShader:me.shadow_vert,fragmentShader:me.shadow_frag}};bn.physical={uniforms:pn([bn.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new ce},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new ce},clearcoatNormalScale:{value:new mt(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new ce},dispersion:{value:0},retroreflectivity:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new ce},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new ce},sheen:{value:0},sheenColor:{value:new Ot(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new ce},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new ce},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new ce},transmissionSamplerSize:{value:new mt},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new ce},attenuationDistance:{value:0},attenuationColor:{value:new Ot(0)},specularColor:{value:new Ot(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new ce},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new ce},anisotropyVector:{value:new mt},anisotropyMap:{value:null},anisotropyMapTransform:{value:new ce}}]),vertexShader:me.meshphysical_vert,fragmentShader:me.meshphysical_frag};var Lc={r:0,b:0,g:0},Lg=new ue,Pd=new ce;Pd.set(-1,0,0,0,1,0,0,0,1);function Dg(i,t,e,n,s,r){let a=new Ot(0),o=s===!0?0:1,c,l,h=null,d=0,u=null;function f(S){let E=S.isScene===!0?S.background:null;if(E&&E.isTexture){let v=S.backgroundBlurriness>0;E=t.get(E,v)}return E}function g(S){let E=!1,v=f(S);v===null?p(a,o):v&&v.isColor&&(p(v,1),E=!0);let b=i.xr.getEnvironmentBlendMode();b==="additive"?e.buffers.color.setClear(0,0,0,1,r):b==="alpha-blend"&&e.buffers.color.setClear(0,0,0,0,r),(i.autoClear||E)&&(e.buffers.depth.setTest(!0),e.buffers.depth.setMask(!0),e.buffers.color.setMask(!0),i.clear(i.autoClearColor,i.autoClearDepth,i.autoClearStencil))}function x(S,E){let v=f(E);v&&(v.isCubeTexture||v.mapping===ma)?(l===void 0&&(l=new ot(new Re(1,1,1),new Ue({name:"BackgroundCubeMaterial",uniforms:Ss(bn.backgroundCube.uniforms),vertexShader:bn.backgroundCube.vertexShader,fragmentShader:bn.backgroundCube.fragmentShader,side:rn,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),l.geometry.deleteAttribute("uv"),l.onBeforeRender=function(b,M,A){this.matrixWorld.copyPosition(A.matrixWorld)},Object.defineProperty(l.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),n.update(l)),l.material.uniforms.envMap.value=v,l.material.uniforms.backgroundBlurriness.value=E.backgroundBlurriness,l.material.uniforms.backgroundIntensity.value=E.backgroundIntensity,l.material.uniforms.backgroundRotation.value.setFromMatrix4(Lg.makeRotationFromEuler(E.backgroundRotation)).transpose(),v.isCubeTexture&&v.isRenderTargetTexture===!1&&l.material.uniforms.backgroundRotation.value.premultiply(Pd),l.material.toneMapped=Se.getTransfer(v.colorSpace)!==Ae,(h!==v||d!==v.version||u!==i.toneMapping)&&(l.material.needsUpdate=!0,h=v,d=v.version,u=i.toneMapping),l.layers.enableAll(),S.unshift(l,l.geometry,l.material,0,0,null)):v&&v.isTexture&&(c===void 0&&(c=new ot(new Xe(2,2),new Ue({name:"BackgroundMaterial",uniforms:Ss(bn.background.uniforms),vertexShader:bn.background.vertexShader,fragmentShader:bn.background.fragmentShader,side:ns,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),Object.defineProperty(c.material,"map",{get:function(){return this.uniforms.t2D.value}}),n.update(c)),c.material.uniforms.t2D.value=v,c.material.uniforms.backgroundIntensity.value=E.backgroundIntensity,c.material.toneMapped=Se.getTransfer(v.colorSpace)!==Ae,v.matrixAutoUpdate===!0&&v.updateMatrix(),c.material.uniforms.uvTransform.value.copy(v.matrix),(h!==v||d!==v.version||u!==i.toneMapping)&&(c.material.needsUpdate=!0,h=v,d=v.version,u=i.toneMapping),c.layers.enableAll(),S.unshift(c,c.geometry,c.material,0,0,null))}function p(S,E){S.getRGB(Lc,nh(i)),e.buffers.color.setClear(Lc.r,Lc.g,Lc.b,E,r)}function m(){l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0),c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0)}return{getClearColor:function(){return a},setClearColor:function(S,E=1){a.set(S),o=E,p(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(S){o=S,p(a,o)},render:g,addToRenderList:x,dispose:m}}function Ug(i,t){let e=i.getParameter(i.MAX_VERTEX_ATTRIBS),n={},s=u(null),r=s,a=!1;function o(L,N,B,D,O){let $=!1,J=d(L,D,B,N);r!==J&&(r=J,l(r.object)),$=f(L,D,B,O),$&&g(L,D,B,O),O!==null&&t.update(O,i.ELEMENT_ARRAY_BUFFER),($||a)&&(a=!1,v(L,N,B,D),O!==null&&i.bindBuffer(i.ELEMENT_ARRAY_BUFFER,t.get(O).buffer))}function c(){return i.createVertexArray()}function l(L){return i.bindVertexArray(L)}function h(L){return i.deleteVertexArray(L)}function d(L,N,B,D){let O=D.wireframe===!0,$=n[N.id];$===void 0&&($={},n[N.id]=$);let J=L.isInstancedMesh===!0?L.id:0,W=$[J];W===void 0&&(W={},$[J]=W);let G=W[B.id];G===void 0&&(G={},W[B.id]=G);let K=G[O];return K===void 0&&(K=u(c()),G[O]=K),K}function u(L){let N=[],B=[],D=[];for(let O=0;O<e;O++)N[O]=0,B[O]=0,D[O]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:N,enabledAttributes:B,attributeDivisors:D,object:L,attributes:{},index:null}}function f(L,N,B,D){let O=r.attributes,$=N.attributes,J=0,W=B.getAttributes();for(let G in W)if(W[G].location>=0){let nt=O[G],Et=$[G];if(Et===void 0&&(G==="instanceMatrix"&&L.instanceMatrix&&(Et=L.instanceMatrix),G==="instanceColor"&&L.instanceColor&&(Et=L.instanceColor)),nt===void 0||nt.attribute!==Et||Et&&nt.data!==Et.data)return!0;J++}return r.attributesNum!==J||r.index!==D}function g(L,N,B,D){let O={},$=N.attributes,J=0,W=B.getAttributes();for(let G in W)if(W[G].location>=0){let nt=$[G];nt===void 0&&(G==="instanceMatrix"&&L.instanceMatrix&&(nt=L.instanceMatrix),G==="instanceColor"&&L.instanceColor&&(nt=L.instanceColor));let Et={};Et.attribute=nt,nt&&nt.data&&(Et.data=nt.data),O[G]=Et,J++}r.attributes=O,r.attributesNum=J,r.index=D}function x(){let L=r.newAttributes;for(let N=0,B=L.length;N<B;N++)L[N]=0}function p(L){m(L,0)}function m(L,N){let B=r.newAttributes,D=r.enabledAttributes,O=r.attributeDivisors;B[L]=1,D[L]===0&&(i.enableVertexAttribArray(L),D[L]=1),O[L]!==N&&(i.vertexAttribDivisor(L,N),O[L]=N)}function S(){let L=r.newAttributes,N=r.enabledAttributes;for(let B=0,D=N.length;B<D;B++)N[B]!==L[B]&&(i.disableVertexAttribArray(B),N[B]=0)}function E(L,N,B,D,O,$,J){J===!0?i.vertexAttribIPointer(L,N,B,O,$):i.vertexAttribPointer(L,N,B,D,O,$)}function v(L,N,B,D){x();let O=D.attributes,$=B.getAttributes(),J=N.defaultAttributeValues;for(let W in $){let G=$[W];if(G.location>=0){let K=O[W];if(K===void 0&&(W==="instanceMatrix"&&L.instanceMatrix&&(K=L.instanceMatrix),W==="instanceColor"&&L.instanceColor&&(K=L.instanceColor)),K!==void 0){let nt=K.normalized,Et=K.itemSize,pt=t.get(K);if(pt===void 0)continue;let Ft=pt.buffer,Dt=pt.type,ft=pt.bytesPerElement,U=Dt===i.INT||Dt===i.UNSIGNED_INT||K.gpuType===qo;if(K.isInterleavedBufferAttribute){let V=K.data,dt=V.stride,Mt=K.offset;if(V.isInstancedInterleavedBuffer){for(let yt=0;yt<G.locationSize;yt++)m(G.location+yt,V.meshPerAttribute);L.isInstancedMesh!==!0&&D._maxInstanceCount===void 0&&(D._maxInstanceCount=V.meshPerAttribute*V.count)}else for(let yt=0;yt<G.locationSize;yt++)p(G.location+yt);i.bindBuffer(i.ARRAY_BUFFER,Ft);for(let yt=0;yt<G.locationSize;yt++)E(G.location+yt,Et/G.locationSize,Dt,nt,dt*ft,(Mt+Et/G.locationSize*yt)*ft,U)}else{if(K.isInstancedBufferAttribute){for(let V=0;V<G.locationSize;V++)m(G.location+V,K.meshPerAttribute);L.isInstancedMesh!==!0&&D._maxInstanceCount===void 0&&(D._maxInstanceCount=K.meshPerAttribute*K.count)}else for(let V=0;V<G.locationSize;V++)p(G.location+V);i.bindBuffer(i.ARRAY_BUFFER,Ft);for(let V=0;V<G.locationSize;V++)E(G.location+V,Et/G.locationSize,Dt,nt,Et*ft,Et/G.locationSize*V*ft,U)}}else if(J!==void 0){let nt=J[W];if(nt!==void 0)switch(nt.length){case 2:i.vertexAttrib2fv(G.location,nt);break;case 3:i.vertexAttrib3fv(G.location,nt);break;case 4:i.vertexAttrib4fv(G.location,nt);break;default:i.vertexAttrib1fv(G.location,nt)}}}}S()}function b(){T();for(let L in n){let N=n[L];for(let B in N){let D=N[B];for(let O in D){let $=D[O];for(let J in $)h($[J].object),delete $[J];delete D[O]}}delete n[L]}}function M(L){if(n[L.id]===void 0)return;let N=n[L.id];for(let B in N){let D=N[B];for(let O in D){let $=D[O];for(let J in $)h($[J].object),delete $[J];delete D[O]}}delete n[L.id]}function A(L){for(let N in n){let B=n[N];for(let D in B){let O=B[D];if(O[L.id]===void 0)continue;let $=O[L.id];for(let J in $)h($[J].object),delete $[J];delete O[L.id]}}}function _(L){for(let N in n){let B=n[N],D=L.isInstancedMesh===!0?L.id:0,O=B[D];if(O!==void 0){for(let $ in O){let J=O[$];for(let W in J)h(J[W].object),delete J[W];delete O[$]}delete B[D],Object.keys(B).length===0&&delete n[N]}}}function T(){I(),a=!0,r!==s&&(r=s,l(r.object))}function I(){s.geometry=null,s.program=null,s.wireframe=!1}return{setup:o,reset:T,resetDefaultState:I,dispose:b,releaseStatesOfGeometry:M,releaseStatesOfObject:_,releaseStatesOfProgram:A,initAttributes:x,enableAttribute:p,disableUnusedAttributes:S}}function Ng(i,t,e){let n;function s(c){n=c}function r(c,l){i.drawArrays(n,c,l),e.update(l,n,1)}function a(c,l,h){h!==0&&(i.drawArraysInstanced(n,c,l,h),e.update(l,n,h))}function o(c,l,h){if(h===0)return;t.get("WEBGL_multi_draw").multiDrawArraysWEBGL(n,c,0,l,0,h);let u=0;for(let f=0;f<h;f++)u+=l[f];e.update(u,n,1)}this.setMode=s,this.render=r,this.renderInstances=a,this.renderMultiDraw=o}function Fg(i,t,e,n){let s;function r(){if(s!==void 0)return s;if(t.has("EXT_texture_filter_anisotropic")===!0){let A=t.get("EXT_texture_filter_anisotropic");s=i.getParameter(A.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else s=0;return s}function a(A){return!(A!==Wn&&n.convert(A)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(A){let _=A===On&&(t.has("EXT_color_buffer_half_float")||t.has("EXT_color_buffer_float"));return!(A!==Cn&&A!==Gn&&!_&&n.convert(A)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_TYPE))}function c(A){if(A==="highp"){if(i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.HIGH_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.HIGH_FLOAT).precision>0)return"highp";A="mediump"}return A==="mediump"&&i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.MEDIUM_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let l=e.precision!==void 0?e.precision:"highp",h=c(l);h!==l&&(ee("WebGLRenderer:",l,"not supported, using",h,"instead."),l=h);let d=e.logarithmicDepthBuffer===!0,u=e.reversedDepthBuffer===!0&&t.has("EXT_clip_control");e.reversedDepthBuffer===!0&&u===!1&&ee("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");let f=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),g=i.getParameter(i.MAX_VERTEX_TEXTURE_IMAGE_UNITS),x=i.getParameter(i.MAX_TEXTURE_SIZE),p=i.getParameter(i.MAX_CUBE_MAP_TEXTURE_SIZE),m=i.getParameter(i.MAX_VERTEX_ATTRIBS),S=i.getParameter(i.MAX_VERTEX_UNIFORM_VECTORS),E=i.getParameter(i.MAX_VARYING_VECTORS),v=i.getParameter(i.MAX_FRAGMENT_UNIFORM_VECTORS),b=i.getParameter(i.MAX_SAMPLES),M=i.getParameter(i.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:r,getMaxPrecision:c,textureFormatReadable:a,textureTypeReadable:o,precision:l,logarithmicDepthBuffer:d,reversedDepthBuffer:u,maxTextures:f,maxVertexTextures:g,maxTextureSize:x,maxCubemapSize:p,maxAttributes:m,maxVertexUniforms:S,maxVaryings:E,maxFragmentUniforms:v,maxSamples:b,samples:M}}function zg(i){let t=this,e=null,n=0,s=!1,r=!1,a=new Qn,o=new ce,c={value:null,needsUpdate:!1};this.uniform=c,this.numPlanes=0,this.numIntersection=0,this.init=function(d,u){let f=d.length!==0||u||n!==0||s;return s=u,n=d.length,f},this.beginShadows=function(){r=!0,h(null)},this.endShadows=function(){r=!1},this.setGlobalState=function(d,u){e=h(d,u,0)},this.setState=function(d,u,f){let g=d.clippingPlanes,x=d.clipIntersection,p=d.clipShadows,m=i.get(d);if(!s||g===null||g.length===0||r&&!p)r?h(null):l();else{let S=r?0:n,E=S*4,v=m.clippingState||null;c.value=v,v=h(g,u,E,f);for(let b=0;b!==E;++b)v[b]=e[b];m.clippingState=v,this.numIntersection=x?this.numPlanes:0,this.numPlanes+=S}};function l(){c.value!==e&&(c.value=e,c.needsUpdate=n>0),t.numPlanes=n,t.numIntersection=0}function h(d,u,f,g){let x=d!==null?d.length:0,p=null;if(x!==0){if(p=c.value,g!==!0||p===null){let m=f+x*4,S=u.matrixWorldInverse;o.getNormalMatrix(S),(p===null||p.length<m)&&(p=new Float32Array(m));for(let E=0,v=f;E!==x;++E,v+=4)a.copy(d[E]).applyMatrix4(S,o),a.normal.toArray(p,v),p[v+3]=a.constant}c.value=p,c.needsUpdate=!0}return t.numPlanes=x,t.numIntersection=0,p}}var dr=4,Og=6,Bg=20,kg=256,Ea=new ar,cd=new Ot,uh=null,dh=0,fh=0,ph=!1,Hg=new P,bs=new P,pr=class{constructor(t){this._renderer=t,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(t,e=0,n=.1,s=100,r={}){let{size:a=256,position:o=Hg}=r;uh=this._renderer.getRenderTarget(),dh=this._renderer.getActiveCubeFace(),fh=this._renderer.getActiveMipmapLevel(),ph=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);let c=this._allocateTargets();return c.depthBuffer=!0,this._sceneToCubeUV(t,n,s,c,o),e>0&&this._blur(c,0,0,e),this._applyPMREM(c),this._cleanup(c),c}fromEquirectangular(t,e=null){return this._fromTexture(t,e)}fromCubemap(t,e=null){return this._fromTexture(t,e)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=ud(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=hd(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(t){this._lodMax=Math.floor(Math.log2(t)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let t=0;t<this._lodMeshes.length;t++)this._lodMeshes[t].geometry.dispose()}_cleanup(t){this._renderer.setRenderTarget(uh,dh,fh),this._renderer.xr.enabled=ph,t.scissorTest=!1,ur(t,0,0,t.width,t.height)}_fromTexture(t,e){t.mapping===ss||t.mapping===Ms?this._setSize(t.image.length===0?16:t.image[0].width||t.image[0].image.width):this._setSize(t.image.width/4),uh=this._renderer.getRenderTarget(),dh=this._renderer.getActiveCubeFace(),fh=this._renderer.getActiveMipmapLevel(),ph=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let n=e||this._allocateTargets();return this._textureToCubeUV(t,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){let t=3*Math.max(this._cubeSize,112),e=4*this._cubeSize,n={magFilter:$e,minFilter:$e,generateMipmaps:!1,type:On,format:Wn,colorSpace:Nr,depthBuffer:!1},s=ld(t,e,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==t||this._pingPongRenderTarget.height!==e){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=ld(t,e,n);let{_lodMax:r}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods}=Vg(r)),this._blurMaterial=Wg(r,t,e),this._ggxMaterial=Gg(r,t,e)}return s}_compileMaterial(t){let e=new ot(new _e,t);this._renderer.compile(e,Ea)}_sceneToCubeUV(t,e,n,s,r){let c=new Ze(90,1,e,n),l=[1,-1,1,1,1,1],h=[1,1,1,-1,-1,-1],d=this._renderer,u=d.autoClear,f=d.toneMapping;d.getClearColor(cd),d.toneMapping=zn,d.autoClear=!1,d.state.buffers.depth.getReversed()&&(d.setRenderTarget(s),d.clearDepth(),d.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new ot(new Re,new si({name:"PMREM.Background",side:rn,depthWrite:!1,depthTest:!1})));let x=this._backgroundBox,p=x.material,m=!1,S=t.background;S?S.isColor&&(p.color.copy(S),t.background=null,m=!0):(p.color.copy(cd),m=!0);for(let E=0;E<6;E++){let v=E%3;v===0?(c.up.set(0,l[E],0),c.position.set(r.x,r.y,r.z),c.lookAt(r.x+h[E],r.y,r.z)):v===1?(c.up.set(0,0,l[E]),c.position.set(r.x,r.y,r.z),c.lookAt(r.x,r.y+h[E],r.z)):(c.up.set(0,l[E],0),c.position.set(r.x,r.y,r.z),c.lookAt(r.x,r.y,r.z+h[E]));let b=this._cubeSize;ur(s,v*b,E>2?b:0,b,b),d.setRenderTarget(s),m&&d.render(x,c),d.render(t,c)}d.toneMapping=f,d.autoClear=u,t.background=S}_textureToCubeUV(t,e){let n=this._renderer,s=t.mapping===ss||t.mapping===Ms;s?(this._cubemapMaterial===null&&(this._cubemapMaterial=ud()),this._cubemapMaterial.uniforms.flipEnvMap.value=t.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=hd());let r=s?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=r;let o=r.uniforms;o.envMap.value=t;let c=this._cubeSize;ur(e,0,0,3*c,2*c),n.setRenderTarget(e),n.render(a,Ea)}_applyPMREM(t){let e=this._renderer,n=e.autoClear;e.autoClear=!1;let s=this._lodMeshes.length;for(let r=1;r<s;r++)this._applyGGXFilter(t,r-1,r);e.autoClear=n}_applyGGXFilter(t,e,n){let s=this._renderer,r=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[n];o.material=a;let c=a.uniforms,l=n/(this._lodMeshes.length-1),h=e/(this._lodMeshes.length-1),d=Math.sqrt(l*l-h*h),u=l*1.25,f=d*u,{_lodMax:g}=this,x=this._sizeLods[n],p=3*x*(n>g-dr?n-g+dr:0),m=4*(this._cubeSize-x);c.envMap.value=t.texture,c.roughness.value=f,c.mipInt.value=g-e,ur(r,p,m,3*x,2*x),s.setRenderTarget(r),s.render(o,Ea),c.envMap.value=r.texture,c.roughness.value=0,c.mipInt.value=g-n,ur(t,p,m,3*x,2*x),s.setRenderTarget(t),s.render(o,Ea)}_blur(t,e,n,s){let r=this._pingPongRenderTarget,a=Math.min(s,Math.PI)/Math.SQRT2;this._blurPass(t,r,e,n,a),this._blurPass(r,t,n,n,a)}_blurPass(t,e,n,s,r){let a=this._renderer,o=this._blurMaterial,c=this._lodMeshes[s];c.material=o;let l=o.uniforms;l.envMap.value=t.texture,l.sigma.value=r,l.mipInt.value=this._lodMax-n;let h=this._sizeLods[s],d=3*h*(s>this._lodMax-dr?s-this._lodMax+dr:0),u=4*(this._cubeSize-h);ur(e,d,u,3*h,2*h),a.setRenderTarget(e),a.render(c,Ea)}};function Vg(i){let t=[],e=[],n=i,s=i-dr+1+Og;for(let r=0;r<s;r++){let a=Math.pow(2,n);t.push(a);let o=1/(a-2),c=-o,l=1+o,h=[c,c,l,c,l,l,c,c,l,l,c,l],d=6,u=6,f=3,g=new Float32Array(f*u*d),x=new Float32Array(f*u*d);for(let m=0;m<d;m++){let S=m%3*2/3-1,E=m>2?0:-1,v=[S,E,0,S+2/3,E,0,S+2/3,E+1,0,S,E,0,S+2/3,E+1,0,S,E+1,0];g.set(v,f*u*m);for(let b=0;b<u;b++){let M=h[b*2]*2-1,A=h[b*2+1]*2-1;m===0?bs.set(1,A,M):m===1?bs.set(-M,1,-A):m===2?bs.set(-M,A,1):m===3?bs.set(-1,A,-M):m===4?bs.set(-M,-1,A):bs.set(M,A,-1),bs.toArray(x,(m*u+b)*f)}}let p=new _e;p.setAttribute("position",new Pe(g,f)),p.setAttribute("outputDirection",new Pe(x,f)),e.push(new ot(p,null)),n>dr&&n--}return{lodMeshes:e,sizeLods:t}}function ld(i,t,e){let n=new An(i,t,e);return n.texture.mapping=ma,n.texture.name="PMREM.cubeUv",n.scissorTest=!0,n}function ur(i,t,e,n,s){i.viewport.set(t,e,n,s),i.scissor.set(t,e,n,s)}function Gg(i,t,e){return new Ue({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:kg,CUBEUV_TEXEL_WIDTH:1/t,CUBEUV_TEXEL_HEIGHT:1/e,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:Fc(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float roughness;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359

			// Van der Corput radical inverse
			float radicalInverse_VdC(uint bits) {
				bits = (bits << 16u) | (bits >> 16u);
				bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
				bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
				bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
				bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);
				return float(bits) * 2.3283064365386963e-10; // / 0x100000000
			}

			// Hammersley sequence
			vec2 hammersley(uint i, uint N) {
				return vec2(float(i) / float(N), radicalInverse_VdC(i));
			}

			// GGX VNDF importance sampling (Eric Heitz 2018)
			// "Sampling the GGX Distribution of Visible Normals"
			// https://jcgt.org/published/0007/04/01/
			vec3 importanceSampleGGX_VNDF(vec2 Xi, vec3 V, float roughness) {
				float alpha = roughness * roughness;

				// Section 4.1: Orthonormal basis
				vec3 T1 = vec3(1.0, 0.0, 0.0);
				vec3 T2 = cross(V, T1);

				// Section 4.2: Parameterization of projected area
				float r = sqrt(Xi.x);
				float phi = 2.0 * PI * Xi.y;
				float t1 = r * cos(phi);
				float t2 = r * sin(phi);
				float s = 0.5 * (1.0 + V.z);
				t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;

				// Section 4.3: Reprojection onto hemisphere
				vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0.0, 1.0 - t1 * t1 - t2 * t2)) * V;

				// Section 3.4: Transform back to ellipsoid configuration
				return normalize(vec3(alpha * Nh.x, alpha * Nh.y, max(0.0, Nh.z)));
			}

			void main() {
				vec3 N = normalize(vOutputDirection);
				vec3 V = N; // Assume view direction equals normal for pre-filtering

				vec3 prefilteredColor = vec3(0.0);
				float totalWeight = 0.0;

				// For very low roughness, just sample the environment directly
				if (roughness < 0.001) {
					gl_FragColor = vec4(bilinearCubeUV(envMap, N, mipInt), 1.0);
					return;
				}

				// Tangent space basis for VNDF sampling
				vec3 up = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
				vec3 tangent = normalize(cross(up, N));
				vec3 bitangent = cross(N, tangent);

				for(uint i = 0u; i < uint(GGX_SAMPLES); i++) {
					vec2 Xi = hammersley(i, uint(GGX_SAMPLES));

					// For PMREM, V = N, so in tangent space V is always (0, 0, 1)
					vec3 H_tangent = importanceSampleGGX_VNDF(Xi, vec3(0.0, 0.0, 1.0), roughness);

					// Transform H back to world space
					vec3 H = normalize(tangent * H_tangent.x + bitangent * H_tangent.y + N * H_tangent.z);
					vec3 L = normalize(2.0 * dot(V, H) * H - V);

					float NdotL = max(dot(N, L), 0.0);

					if(NdotL > 0.0) {
						// Sample environment at fixed mip level
						// VNDF importance sampling handles the distribution filtering
						vec3 sampleColor = bilinearCubeUV(envMap, L, mipInt);

						// Weight by NdotL for the split-sum approximation
						// VNDF PDF naturally accounts for the visible microfacet distribution
						prefilteredColor += sampleColor * NdotL;
						totalWeight += NdotL;
					}
				}

				if (totalWeight > 0.0) {
					prefilteredColor = prefilteredColor / totalWeight;
				}

				gl_FragColor = vec4(prefilteredColor, 1.0);
			}
		`,blending:vi,depthTest:!1,depthWrite:!1})}function Wg(i,t,e){return new Ue({name:"SphericalGaussianBlur",defines:{SAMPLES:Bg,CUBEUV_TEXEL_WIDTH:1/t,CUBEUV_TEXEL_HEIGHT:1/e,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},sigma:{value:0},mipInt:{value:0}},vertexShader:Fc(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float sigma;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359
			#define GOLDEN_ANGLE 2.39996322973

			void main() {

				if ( sigma == 0.0 ) {

					gl_FragColor = vec4( bilinearCubeUV( envMap, vOutputDirection, mipInt ), 1.0 );
					return;

				}

				vec3 outputDirection = normalize( vOutputDirection );

				vec3 up = abs( outputDirection.z ) < 0.999 ? vec3( 0.0, 0.0, 1.0 ) : vec3( 1.0, 0.0, 0.0 );
				vec3 tangent = normalize( cross( up, outputDirection ) );
				vec3 bitangent = cross( outputDirection, tangent );

				// Truncate the kernel at three standard deviations or at the antipode.
				float thetaMax = min( 3.0 * sigma, PI );
				float truncation = 1.0 - exp( - 0.5 * thetaMax * thetaMax / ( sigma * sigma ) );

				vec3 accumColor = vec3( 0.0 );
				float accumWeight = 0.0;

				for ( int i = 0; i < SAMPLES; i ++ ) {

					// Stratified inverse-CDF sampling of the Gaussian, placed on a golden-angle spiral.
					float stratum = ( float( i ) + 0.5 ) / float( SAMPLES );
					float theta = sigma * sqrt( - 2.0 * log( 1.0 - stratum * truncation ) );
					float phi = float( i ) * GOLDEN_ANGLE;

					vec3 offset = cos( phi ) * tangent + sin( phi ) * bitangent;
					vec3 sampleDirection = cos( theta ) * outputDirection + sin( theta ) * offset;

					// Correct the planar sample density to solid angle.
					float weight = sin( theta ) / theta;

					accumColor += weight * bilinearCubeUV( envMap, sampleDirection, mipInt );
					accumWeight += weight;

				}

				gl_FragColor = vec4( accumColor / accumWeight, 1.0 );

			}
		`,blending:vi,depthTest:!1,depthWrite:!1})}function hd(){return new Ue({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Fc(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:vi,depthTest:!1,depthWrite:!1})}function ud(){return new Ue({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Fc(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:vi,depthTest:!1,depthWrite:!1})}function Fc(){return`

		precision mediump float;
		precision mediump int;

		attribute vec3 outputDirection;

		varying vec3 vOutputDirection;

		void main() {

			vOutputDirection = outputDirection;
			gl_Position = vec4( position, 1.0 );

		}
	`}var Uc=class extends An{constructor(t=1,e={}){super(t,t,e),this.isWebGLCubeRenderTarget=!0;let n={width:t,height:t,depth:1},s=[n,n,n,n,n,n];this.texture=new Yr(s),this._setTextureOptions(e),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(t,e){this.texture.type=e.type,this.texture.colorSpace=e.colorSpace,this.texture.generateMipmaps=e.generateMipmaps,this.texture.minFilter=e.minFilter,this.texture.magFilter=e.magFilter;let n={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},s=new Re(5,5,5),r=new Ue({name:"CubemapFromEquirect",uniforms:Ss(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:rn,blending:vi});r.uniforms.tEquirect.value=e;let a=new ot(s,r),o=e.minFilter;return e.minFilter===rs&&(e.minFilter=$e),new ko(1,10,this).update(t,a),e.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(t,e=!0,n=!0,s=!0){let r=t.getRenderTarget();for(let a=0;a<6;a++)t.setRenderTarget(this,a),t.clear(e,n,s);t.setRenderTarget(r)}};function Xg(i){let t=new WeakMap,e=new WeakMap,n=null;function s(u,f=!1){return u==null?null:f?a(u):r(u)}function r(u){if(u&&u.isTexture){let f=u.mapping;if(f===Go||f===Wo)if(t.has(u)){let g=t.get(u).texture;return o(g,u.mapping)}else{let g=u.image;if(g&&g.height>0){let x=new Uc(g.height);return x.fromEquirectangularTexture(i,u),t.set(u,x),u.addEventListener("dispose",l),o(x.texture,u.mapping)}else return null}}return u}function a(u){if(u&&u.isTexture){let f=u.mapping,g=f===Go||f===Wo,x=f===ss||f===Ms;if(g||x){let p=e.get(u),m=p!==void 0?p.texture.pmremVersion:0;if(u.isRenderTargetTexture&&u.pmremVersion!==m)return n===null&&(n=new pr(i)),p=g?n.fromEquirectangular(u,p):n.fromCubemap(u,p),p.texture.pmremVersion=u.pmremVersion,e.set(u,p),p.texture;if(p!==void 0)return p.texture;{let S=u.image;return g&&S&&S.height>0||x&&S&&c(S)?(n===null&&(n=new pr(i)),p=g?n.fromEquirectangular(u):n.fromCubemap(u),p.texture.pmremVersion=u.pmremVersion,e.set(u,p),u.addEventListener("dispose",h),p.texture):null}}}return u}function o(u,f){return f===Go?u.mapping=ss:f===Wo&&(u.mapping=Ms),u}function c(u){let f=0,g=6;for(let x=0;x<g;x++)u[x]!==void 0&&f++;return f===g}function l(u){let f=u.target;f.removeEventListener("dispose",l);let g=t.get(f);g!==void 0&&(t.delete(f),g.dispose())}function h(u){let f=u.target;f.removeEventListener("dispose",h);let g=e.get(f);g!==void 0&&(e.delete(f),g.dispose())}function d(){t=new WeakMap,e=new WeakMap,n!==null&&(n.dispose(),n=null)}return{get:s,dispose:d}}function qg(i){let t={};function e(n){if(t[n]!==void 0)return t[n];let s=i.getExtension(n);return t[n]=s,s}return{has:function(n){return e(n)!==null},init:function(){e("EXT_color_buffer_float"),e("WEBGL_clip_cull_distance"),e("OES_texture_float_linear"),e("EXT_color_buffer_half_float"),e("WEBGL_multisampled_render_to_texture"),e("WEBGL_render_shared_exponent")},get:function(n){let s=e(n);return s===null&&gs("WebGLRenderer: "+n+" extension not supported."),s}}}function Yg(i,t,e,n){let s={},r=new WeakMap;function a(d){let u=d.target;u.index!==null&&t.remove(u.index);for(let g in u.attributes)t.remove(u.attributes[g]);u.removeEventListener("dispose",a),delete s[u.id];let f=r.get(u);f&&(t.remove(f),r.delete(u)),n.releaseStatesOfGeometry(u),u.isInstancedBufferGeometry===!0&&delete u._maxInstanceCount,e.memory.geometries--}function o(d,u){return s[u.id]===!0||(u.addEventListener("dispose",a),s[u.id]=!0,e.memory.geometries++),u}function c(d){let u=d.attributes;for(let f in u)t.update(u[f],i.ARRAY_BUFFER)}function l(d){let u=[],f=d.index,g=d.attributes.position,x=0;if(g===void 0)return;if(f!==null){let S=f.array;x=f.version;for(let E=0,v=S.length;E<v;E+=3){let b=S[E+0],M=S[E+1],A=S[E+2];u.push(b,M,M,A,A,b)}}else{let S=g.array;x=g.version;for(let E=0,v=S.length/3-1;E<v;E+=3){let b=E+0,M=E+1,A=E+2;u.push(b,M,M,A,A,b)}}let p=new(g.count>=65535?Gr:Vr)(u,1);p.version=x;let m=r.get(d);m&&t.remove(m),r.set(d,p)}function h(d){let u=r.get(d);if(u){let f=d.index;f!==null&&u.version<f.version&&l(d)}else l(d);return r.get(d)}return{get:o,update:c,getWireframeAttribute:h}}function jg(i,t,e){let n;function s(d){n=d}let r,a;function o(d){r=d.type,a=d.bytesPerElement}function c(d,u){i.drawElements(n,u,r,d*a),e.update(u,n,1)}function l(d,u,f){f!==0&&(i.drawElementsInstanced(n,u,r,d*a,f),e.update(u,n,f))}function h(d,u,f){if(f===0)return;t.get("WEBGL_multi_draw").multiDrawElementsWEBGL(n,u,0,r,d,0,f);let x=0;for(let p=0;p<f;p++)x+=u[p];e.update(x,n,1)}this.setMode=s,this.setIndex=o,this.render=c,this.renderInstances=l,this.renderMultiDraw=h}function Zg(i){let t={geometries:0,textures:0},e={frame:0,calls:0,triangles:0,points:0,lines:0};function n(r,a,o){switch(e.calls++,a){case i.TRIANGLES:e.triangles+=o*(r/3);break;case i.LINES:e.lines+=o*(r/2);break;case i.LINE_STRIP:e.lines+=o*(r-1);break;case i.LINE_LOOP:e.lines+=o*r;break;case i.POINTS:e.points+=o*r;break;default:se("WebGLInfo: Unknown draw mode:",a);break}}function s(){e.calls=0,e.triangles=0,e.points=0,e.lines=0}return{memory:t,render:e,programs:null,autoReset:!0,reset:s,update:n}}function $g(i,t,e){let n=new WeakMap,s=new xe;function r(a,o,c){let l=a.morphTargetInfluences,h=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,d=h!==void 0?h.length:0,u=n.get(o);if(u===void 0||u.count!==d){let T=function(){A.dispose(),n.delete(o),o.removeEventListener("dispose",T)};u!==void 0&&u.texture.dispose();let f=o.morphAttributes.position!==void 0,g=o.morphAttributes.normal!==void 0,x=o.morphAttributes.color!==void 0,p=o.morphAttributes.position||[],m=o.morphAttributes.normal||[],S=o.morphAttributes.color||[],E=0;f===!0&&(E=1),g===!0&&(E=2),x===!0&&(E=3);let v=o.attributes.position.count*E,b=1;v>t.maxTextureSize&&(b=Math.ceil(v/t.maxTextureSize),v=t.maxTextureSize);let M=new Float32Array(v*b*4*d),A=new Br(M,v,b,d);A.type=Gn,A.needsUpdate=!0;let _=E*4;for(let I=0;I<d;I++){let L=p[I],N=m[I],B=S[I],D=v*b*4*I;for(let O=0;O<L.count;O++){let $=O*_;f===!0&&(s.fromBufferAttribute(L,O),M[D+$+0]=s.x,M[D+$+1]=s.y,M[D+$+2]=s.z,M[D+$+3]=0),g===!0&&(s.fromBufferAttribute(N,O),M[D+$+4]=s.x,M[D+$+5]=s.y,M[D+$+6]=s.z,M[D+$+7]=0),x===!0&&(s.fromBufferAttribute(B,O),M[D+$+8]=s.x,M[D+$+9]=s.y,M[D+$+10]=s.z,M[D+$+11]=B.itemSize===4?s.w:1)}}u={count:d,texture:A,size:new mt(v,b)},n.set(o,u),o.addEventListener("dispose",T)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)c.getUniforms().setValue(i,"morphTexture",a.morphTexture,e);else{let f=0;for(let x=0;x<l.length;x++)f+=l[x];let g=o.morphTargetsRelative?1:1-f;c.getUniforms().setValue(i,"morphTargetBaseInfluence",g),c.getUniforms().setValue(i,"morphTargetInfluences",l)}c.getUniforms().setValue(i,"morphTargetsTexture",u.texture,e),c.getUniforms().setValue(i,"morphTargetsTextureSize",u.size)}return{update:r}}function Jg(i,t,e,n,s){let r=new WeakMap;function a(l){let h=s.render.frame,d=l.geometry,u=t.get(l,d);if(r.get(u)!==h&&(t.update(u),r.set(u,h)),l.isInstancedMesh&&(l.hasEventListener("dispose",c)===!1&&l.addEventListener("dispose",c),r.get(l)!==h&&(e.update(l.instanceMatrix,i.ARRAY_BUFFER),l.instanceColor!==null&&e.update(l.instanceColor,i.ARRAY_BUFFER),r.set(l,h))),l.isSkinnedMesh){let f=l.skeleton;r.get(f)!==h&&(f.update(),r.set(f,h))}return u}function o(){r=new WeakMap}function c(l){let h=l.target;h.removeEventListener("dispose",c),n.releaseStatesOfObject(h),e.remove(h.instanceMatrix),h.instanceColor!==null&&e.remove(h.instanceColor)}return{update:a,dispose:o}}var Kg={[Bl]:"LINEAR_TONE_MAPPING",[kl]:"REINHARD_TONE_MAPPING",[Hl]:"CINEON_TONE_MAPPING",[Vl]:"ACES_FILMIC_TONE_MAPPING",[Wl]:"AGX_TONE_MAPPING",[pa]:"NEUTRAL_TONE_MAPPING",[Gl]:"CUSTOM_TONE_MAPPING"};function Qg(i,t,e,n,s,r){let a=new An(t,e,{type:i,depthBuffer:s,stencilBuffer:r,samples:n?4:0,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,resolveDepthBuffer:!1,resolveStencilBuffer:!1}),o=null,c=null,l=new _e;l.setAttribute("position",new Jt([-1,3,0,-1,-1,0,3,-1,0],3)),l.setAttribute("uv",new Jt([0,2,0,0,2,0],2));let h=new Ao({uniforms:{tDiffuse:{value:null}},vertexShader:`
			precision highp float;

			uniform mat4 modelViewMatrix;
			uniform mat4 projectionMatrix;

			attribute vec3 position;
			attribute vec2 uv;

			varying vec2 vUv;

			void main() {
				vUv = uv;
				gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
			}`,fragmentShader:`
			precision highp float;

			uniform sampler2D tDiffuse;

			varying vec2 vUv;

			#include <tonemapping_pars_fragment>
			#include <colorspace_pars_fragment>

			void main() {
				gl_FragColor = texture2D( tDiffuse, vUv );

				#ifdef LINEAR_TONE_MAPPING
					gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );
				#elif defined( REINHARD_TONE_MAPPING )
					gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );
				#elif defined( CINEON_TONE_MAPPING )
					gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );
				#elif defined( ACES_FILMIC_TONE_MAPPING )
					gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );
				#elif defined( AGX_TONE_MAPPING )
					gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );
				#elif defined( NEUTRAL_TONE_MAPPING )
					gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );
				#elif defined( CUSTOM_TONE_MAPPING )
					gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );
				#endif

				#ifdef SRGB_TRANSFER
					gl_FragColor = sRGBTransferOETF( gl_FragColor );
				#endif
			}`,depthTest:!1,depthWrite:!1}),d=new ot(l,h),u=new ar(-1,1,1,-1,0,1),f=null,g=null,x=!1,p,m=null,S=[],E=!1;this.setSize=function(v,b){a.setSize(v,b),o!==null&&o.setSize(v,b),c!==null&&c.setSize(v,b);for(let M=0;M<S.length;M++){let A=S[M];A.setSize&&A.setSize(v,b)}},this.setEffects=function(v){S=v,E=S.length>0&&S[0].isRenderPass===!0;let b=a.width,M=a.height;S.length>0&&o===null&&(o=new An(b,M,{type:On,depthBuffer:!1,stencilBuffer:!1}),c=new An(b,M,{type:On,depthBuffer:!1,stencilBuffer:!1}));for(let A=0;A<S.length;A++){let _=S[A];_.setSize&&_.setSize(b,M)}},this.begin=function(v,b){if(x||v.toneMapping===zn&&S.length===0)return!1;if(m=b,b!==null){let M=b.width,A=b.height;(a.width!==M||a.height!==A)&&this.setSize(M,A)}return E===!1&&v.setRenderTarget(a),p=v.toneMapping,v.toneMapping=zn,!0},this.hasRenderPass=function(){return E},this.end=function(v,b){v.toneMapping=p,x=!0;let M=a,A=o;for(let _=0;_<S.length;_++){let T=S[_];T.enabled!==!1&&(T.render(v,A,M,b),T.needsSwap!==!1&&(M=A,A=A===o?c:o))}if(f!==v.outputColorSpace||g!==v.toneMapping){f=v.outputColorSpace,g=v.toneMapping,h.defines={},Se.getTransfer(f)===Ae&&(h.defines.SRGB_TRANSFER="");let _=Kg[g];_&&(h.defines[_]=""),h.needsUpdate=!0}h.uniforms.tDiffuse.value=M.texture,v.setRenderTarget(m),v.render(d,u),m=null,x=!1},this.isCompositing=function(){return x},this.dispose=function(){a.dispose(),o!==null&&o.dispose(),c!==null&&c.dispose(),l.dispose(),h.dispose()}}var Id=new Mn,vh=new ji(1,1),Ld=new Br,Dd=new vo,Ud=new Yr,dd=[],fd=[],pd=new Float32Array(16),md=new Float32Array(9),gd=new Float32Array(4);function mr(i,t,e){let n=i[0];if(n<=0||n>0)return i;let s=t*e,r=dd[s];if(r===void 0&&(r=new Float32Array(s),dd[s]=r),t!==0){n.toArray(r,0);for(let a=1,o=0;a!==t;++a)o+=e,i[a].toArray(r,o)}return r}function Je(i,t){if(i.length!==t.length)return!1;for(let e=0,n=i.length;e<n;e++)if(i[e]!==t[e])return!1;return!0}function Ke(i,t){for(let e=0,n=t.length;e<n;e++)i[e]=t[e]}function zc(i,t){let e=fd[t];e===void 0&&(e=new Int32Array(t),fd[t]=e);for(let n=0;n!==t;++n)e[n]=i.allocateTextureUnit();return e}function tv(i,t){let e=this.cache;e[0]!==t&&(i.uniform1f(this.addr,t),e[0]=t)}function ev(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y)&&(i.uniform2f(this.addr,t.x,t.y),e[0]=t.x,e[1]=t.y);else{if(Je(e,t))return;i.uniform2fv(this.addr,t),Ke(e,t)}}function nv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z)&&(i.uniform3f(this.addr,t.x,t.y,t.z),e[0]=t.x,e[1]=t.y,e[2]=t.z);else if(t.r!==void 0)(e[0]!==t.r||e[1]!==t.g||e[2]!==t.b)&&(i.uniform3f(this.addr,t.r,t.g,t.b),e[0]=t.r,e[1]=t.g,e[2]=t.b);else{if(Je(e,t))return;i.uniform3fv(this.addr,t),Ke(e,t)}}function iv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z||e[3]!==t.w)&&(i.uniform4f(this.addr,t.x,t.y,t.z,t.w),e[0]=t.x,e[1]=t.y,e[2]=t.z,e[3]=t.w);else{if(Je(e,t))return;i.uniform4fv(this.addr,t),Ke(e,t)}}function sv(i,t){let e=this.cache,n=t.elements;if(n===void 0){if(Je(e,t))return;i.uniformMatrix2fv(this.addr,!1,t),Ke(e,t)}else{if(Je(e,n))return;gd.set(n),i.uniformMatrix2fv(this.addr,!1,gd),Ke(e,n)}}function rv(i,t){let e=this.cache,n=t.elements;if(n===void 0){if(Je(e,t))return;i.uniformMatrix3fv(this.addr,!1,t),Ke(e,t)}else{if(Je(e,n))return;md.set(n),i.uniformMatrix3fv(this.addr,!1,md),Ke(e,n)}}function av(i,t){let e=this.cache,n=t.elements;if(n===void 0){if(Je(e,t))return;i.uniformMatrix4fv(this.addr,!1,t),Ke(e,t)}else{if(Je(e,n))return;pd.set(n),i.uniformMatrix4fv(this.addr,!1,pd),Ke(e,n)}}function ov(i,t){let e=this.cache;e[0]!==t&&(i.uniform1i(this.addr,t),e[0]=t)}function cv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y)&&(i.uniform2i(this.addr,t.x,t.y),e[0]=t.x,e[1]=t.y);else{if(Je(e,t))return;i.uniform2iv(this.addr,t),Ke(e,t)}}function lv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z)&&(i.uniform3i(this.addr,t.x,t.y,t.z),e[0]=t.x,e[1]=t.y,e[2]=t.z);else{if(Je(e,t))return;i.uniform3iv(this.addr,t),Ke(e,t)}}function hv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z||e[3]!==t.w)&&(i.uniform4i(this.addr,t.x,t.y,t.z,t.w),e[0]=t.x,e[1]=t.y,e[2]=t.z,e[3]=t.w);else{if(Je(e,t))return;i.uniform4iv(this.addr,t),Ke(e,t)}}function uv(i,t){let e=this.cache;e[0]!==t&&(i.uniform1ui(this.addr,t),e[0]=t)}function dv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y)&&(i.uniform2ui(this.addr,t.x,t.y),e[0]=t.x,e[1]=t.y);else{if(Je(e,t))return;i.uniform2uiv(this.addr,t),Ke(e,t)}}function fv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z)&&(i.uniform3ui(this.addr,t.x,t.y,t.z),e[0]=t.x,e[1]=t.y,e[2]=t.z);else{if(Je(e,t))return;i.uniform3uiv(this.addr,t),Ke(e,t)}}function pv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z||e[3]!==t.w)&&(i.uniform4ui(this.addr,t.x,t.y,t.z,t.w),e[0]=t.x,e[1]=t.y,e[2]=t.z,e[3]=t.w);else{if(Je(e,t))return;i.uniform4uiv(this.addr,t),Ke(e,t)}}function mv(i,t,e){let n=this.cache,s=e.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s);let r;this.type===i.SAMPLER_2D_SHADOW?(vh.compareFunction=e.isReversedDepthBuffer()?Ic:Pc,r=vh):r=Id,e.setTexture2D(t||r,s)}function gv(i,t,e){let n=this.cache,s=e.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),e.setTexture3D(t||Dd,s)}function vv(i,t,e){let n=this.cache,s=e.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),e.setTextureCube(t||Ud,s)}function xv(i,t,e){let n=this.cache,s=e.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),e.setTexture2DArray(t||Ld,s)}function _v(i){switch(i){case 5126:return tv;case 35664:return ev;case 35665:return nv;case 35666:return iv;case 35674:return sv;case 35675:return rv;case 35676:return av;case 5124:case 35670:return ov;case 35667:case 35671:return cv;case 35668:case 35672:return lv;case 35669:case 35673:return hv;case 5125:return uv;case 36294:return dv;case 36295:return fv;case 36296:return pv;case 35678:case 36198:case 36298:case 36306:case 35682:return mv;case 35679:case 36299:case 36307:return gv;case 35680:case 36300:case 36308:case 36293:return vv;case 36289:case 36303:case 36311:case 36292:return xv}}function yv(i,t){i.uniform1fv(this.addr,t)}function Mv(i,t){let e=mr(t,this.size,2);i.uniform2fv(this.addr,e)}function Sv(i,t){let e=mr(t,this.size,3);i.uniform3fv(this.addr,e)}function bv(i,t){let e=mr(t,this.size,4);i.uniform4fv(this.addr,e)}function Ev(i,t){let e=mr(t,this.size,4);i.uniformMatrix2fv(this.addr,!1,e)}function wv(i,t){let e=mr(t,this.size,9);i.uniformMatrix3fv(this.addr,!1,e)}function Tv(i,t){let e=mr(t,this.size,16);i.uniformMatrix4fv(this.addr,!1,e)}function Av(i,t){i.uniform1iv(this.addr,t)}function Rv(i,t){i.uniform2iv(this.addr,t)}function Cv(i,t){i.uniform3iv(this.addr,t)}function Pv(i,t){i.uniform4iv(this.addr,t)}function Iv(i,t){i.uniform1uiv(this.addr,t)}function Lv(i,t){i.uniform2uiv(this.addr,t)}function Dv(i,t){i.uniform3uiv(this.addr,t)}function Uv(i,t){i.uniform4uiv(this.addr,t)}function Nv(i,t,e){let n=this.cache,s=t.length,r=zc(e,s);Je(n,r)||(i.uniform1iv(this.addr,r),Ke(n,r));let a;this.type===i.SAMPLER_2D_SHADOW?a=vh:a=Id;for(let o=0;o!==s;++o)e.setTexture2D(t[o]||a,r[o])}function Fv(i,t,e){let n=this.cache,s=t.length,r=zc(e,s);Je(n,r)||(i.uniform1iv(this.addr,r),Ke(n,r));for(let a=0;a!==s;++a)e.setTexture3D(t[a]||Dd,r[a])}function zv(i,t,e){let n=this.cache,s=t.length,r=zc(e,s);Je(n,r)||(i.uniform1iv(this.addr,r),Ke(n,r));for(let a=0;a!==s;++a)e.setTextureCube(t[a]||Ud,r[a])}function Ov(i,t,e){let n=this.cache,s=t.length,r=zc(e,s);Je(n,r)||(i.uniform1iv(this.addr,r),Ke(n,r));for(let a=0;a!==s;++a)e.setTexture2DArray(t[a]||Ld,r[a])}function Bv(i){switch(i){case 5126:return yv;case 35664:return Mv;case 35665:return Sv;case 35666:return bv;case 35674:return Ev;case 35675:return wv;case 35676:return Tv;case 5124:case 35670:return Av;case 35667:case 35671:return Rv;case 35668:case 35672:return Cv;case 35669:case 35673:return Pv;case 5125:return Iv;case 36294:return Lv;case 36295:return Dv;case 36296:return Uv;case 35678:case 36198:case 36298:case 36306:case 35682:return Nv;case 35679:case 36299:case 36307:return Fv;case 35680:case 36300:case 36308:case 36293:return zv;case 36289:case 36303:case 36311:case 36292:return Ov}}var xh=class{constructor(t,e,n){this.id=t,this.addr=n,this.cache=[],this.type=e.type,this.setValue=_v(e.type)}},_h=class{constructor(t,e,n){this.id=t,this.addr=n,this.cache=[],this.type=e.type,this.size=e.size,this.setValue=Bv(e.type)}},yh=class{constructor(t){this.id=t,this.seq=[],this.map={}}setValue(t,e,n){let s=this.seq;for(let r=0,a=s.length;r!==a;++r){let o=s[r];o.setValue(t,e[o.id],n)}}},mh=/(\w+)(\])?(\[|\.)?/g;function vd(i,t){i.seq.push(t),i.map[t.id]=t}function kv(i,t,e){let n=i.name,s=n.length;for(mh.lastIndex=0;;){let r=mh.exec(n),a=mh.lastIndex,o=r[1],c=r[2]==="]",l=r[3];if(c&&(o=o|0),l===void 0||l==="["&&a+2===s){vd(e,l===void 0?new xh(o,i,t):new _h(o,i,t));break}else{let d=e.map[o];d===void 0&&(d=new yh(o),vd(e,d)),e=d}}}var fr=class{constructor(t,e){this.seq=[],this.map={};let n=t.getProgramParameter(e,t.ACTIVE_UNIFORMS);for(let a=0;a<n;++a){let o=t.getActiveUniform(e,a),c=t.getUniformLocation(e,o.name);kv(o,c,this)}let s=[],r=[];for(let a of this.seq)a.type===t.SAMPLER_2D_SHADOW||a.type===t.SAMPLER_CUBE_SHADOW||a.type===t.SAMPLER_2D_ARRAY_SHADOW?s.push(a):r.push(a);s.length>0&&(this.seq=s.concat(r))}setValue(t,e,n,s){let r=this.map[e];r!==void 0&&r.setValue(t,n,s)}setOptional(t,e,n){let s=e[n];s!==void 0&&this.setValue(t,n,s)}static upload(t,e,n,s){for(let r=0,a=e.length;r!==a;++r){let o=e[r],c=n[o.id];c.needsUpdate!==!1&&o.setValue(t,c.value,s)}}static seqWithValue(t,e){let n=[];for(let s=0,r=t.length;s!==r;++s){let a=t[s];a.id in e&&n.push(a)}return n}};function xd(i,t,e){let n=i.createShader(t);return i.shaderSource(n,e),i.compileShader(n),n}var Hv=37297,Vv=0;function Gv(i,t){let e=i.split(`
`),n=[],s=Math.max(t-6,0),r=Math.min(t+6,e.length);for(let a=s;a<r;a++){let o=a+1;n.push(`${o===t?">":" "} ${o}: ${e[a]}`)}return n.join(`
`)}var _d=new ce;function Wv(i){Se._getMatrix(_d,Se.workingColorSpace,i);let t=`mat3( ${_d.elements.map(e=>e.toFixed(4))} )`;switch(Se.getTransfer(i)){case Fr:return[t,"LinearTransferOETF"];case Ae:return[t,"sRGBTransferOETF"];default:return ee("WebGLProgram: Unsupported color space: ",i),[t,"LinearTransferOETF"]}}function yd(i,t,e){let n=i.getShaderParameter(t,i.COMPILE_STATUS),r=(i.getShaderInfoLog(t)||"").trim();if(n&&r==="")return"";let a=/ERROR: 0:(\d+)/.exec(r);if(a){let o=parseInt(a[1]);return e.toUpperCase()+`

`+r+`

`+Gv(i.getShaderSource(t),o)}else return r}function Xv(i,t){let e=Wv(t);return[`vec4 ${i}( vec4 value ) {`,`	return ${e[1]}( vec4( value.rgb * ${e[0]}, value.a ) );`,"}"].join(`
`)}var qv={[Bl]:"Linear",[kl]:"Reinhard",[Hl]:"Cineon",[Vl]:"ACESFilmic",[Wl]:"AgX",[pa]:"Neutral",[Gl]:"Custom"};function Yv(i,t){let e=qv[t];return e===void 0?(ee("WebGLProgram: Unsupported toneMapping:",t),"vec3 "+i+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+i+"( vec3 color ) { return "+e+"ToneMapping( color ); }"}var Dc=new P;function jv(){Se.getLuminanceCoefficients(Dc);let i=Dc.x.toFixed(4),t=Dc.y.toFixed(4),e=Dc.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${i}, ${t}, ${e} );`,"	return dot( weights, rgb );","}"].join(`
`)}function Zv(i){return[i.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",i.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Ta).join(`
`)}function $v(i){let t=[];for(let e in i){let n=i[e];n!==!1&&t.push("#define "+e+" "+n)}return t.join(`
`)}function Jv(i,t){let e={},n=i.getProgramParameter(t,i.ACTIVE_ATTRIBUTES);for(let s=0;s<n;s++){let r=i.getActiveAttrib(t,s),a=r.name,o=1;r.type===i.FLOAT_MAT2&&(o=2),r.type===i.FLOAT_MAT3&&(o=3),r.type===i.FLOAT_MAT4&&(o=4),e[a]={type:r.type,location:i.getAttribLocation(t,a),locationSize:o}}return e}function Ta(i){return i!==""}function Md(i,t){let e=t.numSpotLightShadows+t.numSpotLightMaps-t.numSpotLightShadowsWithMaps;return i.replace(/NUM_SUN_LIGHTS/g,t.numSunLights).replace(/NUM_DIR_LIGHTS/g,t.numDirLights).replace(/NUM_SPOT_LIGHTS/g,t.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,t.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,e).replace(/NUM_RECT_AREA_LIGHTS/g,t.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,t.numPointLights).replace(/NUM_HEMI_LIGHTS/g,t.numHemiLights).replace(/NUM_SUN_LIGHT_SHADOWS/g,t.numSunLightShadows).replace(/NUM_DIR_LIGHT_SHADOWS/g,t.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,t.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,t.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,t.numPointLightShadows)}function Sd(i,t){return i.replace(/NUM_CLIPPING_PLANES/g,t.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,t.numClippingPlanes-t.numClipIntersection)}var Kv=/^[ \t]*#include +<([\w\d./]+)>/gm;function Mh(i){return i.replace(Kv,tx)}var Qv=new Map;function tx(i,t){let e=me[t];if(e===void 0){let n=Qv.get(t);if(n!==void 0)e=me[n],ee('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',t,n);else throw new Error("THREE.WebGLProgram: Can not resolve #include <"+t+">")}return Mh(e)}var ex=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function bd(i){return i.replace(ex,nx)}function nx(i,t,e,n){let s="";for(let r=parseInt(t);r<parseInt(e);r++)s+=n.replace(/\[\s*i\s*\]/g,"[ "+r+" ]").replace(/UNROLLED_LOOP_INDEX/g,r);return s}function Ed(i){let t=`precision ${i.precision} float;
	precision ${i.precision} int;
	precision ${i.precision} sampler2D;
	precision ${i.precision} samplerCube;
	precision ${i.precision} sampler3D;
	precision ${i.precision} sampler2DArray;
	precision ${i.precision} sampler2DShadow;
	precision ${i.precision} samplerCubeShadow;
	precision ${i.precision} sampler2DArrayShadow;
	precision ${i.precision} isampler2D;
	precision ${i.precision} isampler3D;
	precision ${i.precision} isamplerCube;
	precision ${i.precision} isampler2DArray;
	precision ${i.precision} usampler2D;
	precision ${i.precision} usampler3D;
	precision ${i.precision} usamplerCube;
	precision ${i.precision} usampler2DArray;
	`;return i.precision==="highp"?t+=`
#define HIGH_PRECISION`:i.precision==="mediump"?t+=`
#define MEDIUM_PRECISION`:i.precision==="lowp"&&(t+=`
#define LOW_PRECISION`),t}var ix={[_s]:"SHADOWMAP_TYPE_PCF",[or]:"SHADOWMAP_TYPE_VSM"};function sx(i){return ix[i.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}var rx={[ss]:"ENVMAP_TYPE_CUBE",[Ms]:"ENVMAP_TYPE_CUBE",[ma]:"ENVMAP_TYPE_CUBE_UV"};function ax(i){return i.envMap===!1?"ENVMAP_TYPE_CUBE":rx[i.envMapMode]||"ENVMAP_TYPE_CUBE"}var ox={[Ms]:"ENVMAP_MODE_REFRACTION"};function cx(i){return i.envMap===!1?"ENVMAP_MODE_REFLECTION":ox[i.envMapMode]||"ENVMAP_MODE_REFLECTION"}var lx={[Ol]:"ENVMAP_BLENDING_MULTIPLY",[Bu]:"ENVMAP_BLENDING_MIX",[ku]:"ENVMAP_BLENDING_ADD"};function hx(i){return i.envMap===!1?"ENVMAP_BLENDING_NONE":lx[i.combine]||"ENVMAP_BLENDING_NONE"}function ux(i){let t=i.envMapCubeUVHeight;if(t===null)return null;let e=Math.log2(t)-2,n=1/t;return{texelWidth:1/(3*Math.max(Math.pow(2,e),112)),texelHeight:n,maxMip:e}}function dx(i,t,e,n){let s=i.getContext(),r=e.defines,a=e.vertexShader,o=e.fragmentShader,c=sx(e),l=ax(e),h=cx(e),d=hx(e),u=ux(e),f=Zv(e),g=$v(r),x=s.createProgram(),p,m,S=e.glslVersion?"#version "+e.glslVersion+`
`:"";e.isRawShaderMaterial?(p=["#define SHADER_TYPE "+e.shaderType,"#define SHADER_NAME "+e.shaderName,g].filter(Ta).join(`
`),p.length>0&&(p+=`
`),m=["#define SHADER_TYPE "+e.shaderType,"#define SHADER_NAME "+e.shaderName,g].filter(Ta).join(`
`),m.length>0&&(m+=`
`)):(p=[Ed(e),"#define SHADER_TYPE "+e.shaderType,"#define SHADER_NAME "+e.shaderName,g,e.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",e.batching?"#define USE_BATCHING":"",e.batchingColor?"#define USE_BATCHING_COLOR":"",e.instancing?"#define USE_INSTANCING":"",e.instancingColor?"#define USE_INSTANCING_COLOR":"",e.instancingMorph?"#define USE_INSTANCING_MORPH":"",e.useFog&&e.fog?"#define USE_FOG":"",e.useFog&&e.fogExp2?"#define FOG_EXP2":"",e.map?"#define USE_MAP":"",e.envMap?"#define USE_ENVMAP":"",e.envMap?"#define "+h:"",e.lightMap?"#define USE_LIGHTMAP":"",e.aoMap?"#define USE_AOMAP":"",e.bumpMap?"#define USE_BUMPMAP":"",e.normalMap?"#define USE_NORMALMAP":"",e.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",e.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",e.displacementMap?"#define USE_DISPLACEMENTMAP":"",e.emissiveMap?"#define USE_EMISSIVEMAP":"",e.anisotropy?"#define USE_ANISOTROPY":"",e.anisotropyMap?"#define USE_ANISOTROPYMAP":"",e.clearcoatMap?"#define USE_CLEARCOATMAP":"",e.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",e.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",e.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",e.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",e.specularMap?"#define USE_SPECULARMAP":"",e.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",e.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",e.roughnessMap?"#define USE_ROUGHNESSMAP":"",e.metalnessMap?"#define USE_METALNESSMAP":"",e.alphaMap?"#define USE_ALPHAMAP":"",e.alphaHash?"#define USE_ALPHAHASH":"",e.transmission?"#define USE_TRANSMISSION":"",e.transmissionMap?"#define USE_TRANSMISSIONMAP":"",e.thicknessMap?"#define USE_THICKNESSMAP":"",e.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",e.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",e.mapUv?"#define MAP_UV "+e.mapUv:"",e.alphaMapUv?"#define ALPHAMAP_UV "+e.alphaMapUv:"",e.lightMapUv?"#define LIGHTMAP_UV "+e.lightMapUv:"",e.aoMapUv?"#define AOMAP_UV "+e.aoMapUv:"",e.emissiveMapUv?"#define EMISSIVEMAP_UV "+e.emissiveMapUv:"",e.bumpMapUv?"#define BUMPMAP_UV "+e.bumpMapUv:"",e.normalMapUv?"#define NORMALMAP_UV "+e.normalMapUv:"",e.displacementMapUv?"#define DISPLACEMENTMAP_UV "+e.displacementMapUv:"",e.metalnessMapUv?"#define METALNESSMAP_UV "+e.metalnessMapUv:"",e.roughnessMapUv?"#define ROUGHNESSMAP_UV "+e.roughnessMapUv:"",e.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+e.anisotropyMapUv:"",e.clearcoatMapUv?"#define CLEARCOATMAP_UV "+e.clearcoatMapUv:"",e.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+e.clearcoatNormalMapUv:"",e.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+e.clearcoatRoughnessMapUv:"",e.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+e.iridescenceMapUv:"",e.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+e.iridescenceThicknessMapUv:"",e.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+e.sheenColorMapUv:"",e.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+e.sheenRoughnessMapUv:"",e.specularMapUv?"#define SPECULARMAP_UV "+e.specularMapUv:"",e.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+e.specularColorMapUv:"",e.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+e.specularIntensityMapUv:"",e.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+e.transmissionMapUv:"",e.thicknessMapUv?"#define THICKNESSMAP_UV "+e.thicknessMapUv:"",e.vertexTangents&&e.flatShading===!1?"#define USE_TANGENT":"",e.vertexNormals?"#define HAS_NORMAL":"",e.vertexColors?"#define USE_COLOR":"",e.vertexAlphas?"#define USE_COLOR_ALPHA":"",e.vertexUv1s?"#define USE_UV1":"",e.vertexUv2s?"#define USE_UV2":"",e.vertexUv3s?"#define USE_UV3":"",e.pointsUvs?"#define USE_POINTS_UV":"",e.flatShading?"#define FLAT_SHADED":"",e.skinning?"#define USE_SKINNING":"",e.morphTargets?"#define USE_MORPHTARGETS":"",e.morphNormals&&e.flatShading===!1?"#define USE_MORPHNORMALS":"",e.morphColors?"#define USE_MORPHCOLORS":"",e.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+e.morphTextureStride:"",e.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+e.morphTargetsCount:"",e.doubleSided?"#define DOUBLE_SIDED":"",e.flipSided?"#define FLIP_SIDED":"",e.shadowMapEnabled?"#define USE_SHADOWMAP":"",e.shadowMapEnabled?"#define "+c:"",e.sizeAttenuation?"#define USE_SIZEATTENUATION":"",e.numLightProbes>0?"#define USE_LIGHT_PROBES":"",e.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",e.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Ta).join(`
`),m=[Ed(e),"#define SHADER_TYPE "+e.shaderType,"#define SHADER_NAME "+e.shaderName,g,e.useFog&&e.fog?"#define USE_FOG":"",e.useFog&&e.fogExp2?"#define FOG_EXP2":"",e.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",e.map?"#define USE_MAP":"",e.matcap?"#define USE_MATCAP":"",e.envMap?"#define USE_ENVMAP":"",e.envMap?"#define "+l:"",e.envMap?"#define "+h:"",e.envMap?"#define "+d:"",u?"#define CUBEUV_TEXEL_WIDTH "+u.texelWidth:"",u?"#define CUBEUV_TEXEL_HEIGHT "+u.texelHeight:"",u?"#define CUBEUV_MAX_MIP "+u.maxMip+".0":"",e.lightMap?"#define USE_LIGHTMAP":"",e.aoMap?"#define USE_AOMAP":"",e.bumpMap?"#define USE_BUMPMAP":"",e.normalMap?"#define USE_NORMALMAP":"",e.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",e.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",e.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",e.emissiveMap?"#define USE_EMISSIVEMAP":"",e.anisotropy?"#define USE_ANISOTROPY":"",e.anisotropyMap?"#define USE_ANISOTROPYMAP":"",e.clearcoat?"#define USE_CLEARCOAT":"",e.clearcoatMap?"#define USE_CLEARCOATMAP":"",e.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",e.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",e.dispersion?"#define USE_DISPERSION":"",e.retroreflection?"#define USE_RETROREFLECTION":"",e.iridescence?"#define USE_IRIDESCENCE":"",e.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",e.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",e.specularMap?"#define USE_SPECULARMAP":"",e.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",e.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",e.roughnessMap?"#define USE_ROUGHNESSMAP":"",e.metalnessMap?"#define USE_METALNESSMAP":"",e.alphaMap?"#define USE_ALPHAMAP":"",e.alphaTest?"#define USE_ALPHATEST":"",e.alphaHash?"#define USE_ALPHAHASH":"",e.sheen?"#define USE_SHEEN":"",e.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",e.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",e.transmission?"#define USE_TRANSMISSION":"",e.transmissionMap?"#define USE_TRANSMISSIONMAP":"",e.thicknessMap?"#define USE_THICKNESSMAP":"",e.vertexTangents&&e.flatShading===!1?"#define USE_TANGENT":"",e.vertexColors||e.instancingColor?"#define USE_COLOR":"",e.vertexAlphas||e.batchingColor?"#define USE_COLOR_ALPHA":"",e.vertexUv1s?"#define USE_UV1":"",e.vertexUv2s?"#define USE_UV2":"",e.vertexUv3s?"#define USE_UV3":"",e.pointsUvs?"#define USE_POINTS_UV":"",e.gradientMap?"#define USE_GRADIENTMAP":"",e.flatShading?"#define FLAT_SHADED":"",e.doubleSided?"#define DOUBLE_SIDED":"",e.flipSided?"#define FLIP_SIDED":"",e.shadowMapEnabled?"#define USE_SHADOWMAP":"",e.shadowMapEnabled?"#define "+c:"",e.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",e.numLightProbes>0?"#define USE_LIGHT_PROBES":"",e.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",e.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",e.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",e.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",e.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",e.toneMapping!==zn?"#define TONE_MAPPING":"",e.toneMapping!==zn?me.tonemapping_pars_fragment:"",e.toneMapping!==zn?Yv("toneMapping",e.toneMapping):"",e.dithering?"#define DITHERING":"",e.opaque?"#define OPAQUE":"",me.colorspace_pars_fragment,Xv("linearToOutputTexel",e.outputColorSpace),jv(),e.useDepthPacking?"#define DEPTH_PACKING "+e.depthPacking:"",`
`].filter(Ta).join(`
`)),a=Mh(a),a=Md(a,e),a=Sd(a,e),o=Mh(o),o=Md(o,e),o=Sd(o,e),a=bd(a),o=bd(o),e.isRawShaderMaterial!==!0&&(S=`#version 300 es
`,p=[f,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+p,m=["#define varying in",e.glslVersion===Ql?"":"layout(location = 0) out highp vec4 pc_fragColor;",e.glslVersion===Ql?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+m);let E=S+p+a,v=S+m+o,b=xd(s,s.VERTEX_SHADER,E),M=xd(s,s.FRAGMENT_SHADER,v);s.attachShader(x,b),s.attachShader(x,M),e.index0AttributeName!==void 0?s.bindAttribLocation(x,0,e.index0AttributeName):e.hasPositionAttribute===!0&&s.bindAttribLocation(x,0,"position"),s.linkProgram(x);function A(L){if(i.debug.checkShaderErrors){let N=s.getProgramInfoLog(x)||"",B=s.getShaderInfoLog(b)||"",D=s.getShaderInfoLog(M)||"",O=N.trim(),$=B.trim(),J=D.trim(),W=!0,G=!0;if(s.getProgramParameter(x,s.LINK_STATUS)===!1)if(W=!1,typeof i.debug.onShaderError=="function")i.debug.onShaderError(s,x,b,M);else{let K=yd(s,b,"vertex"),nt=yd(s,M,"fragment");se("WebGLProgram: Shader Error "+s.getError()+" - VALIDATE_STATUS "+s.getProgramParameter(x,s.VALIDATE_STATUS)+`

Material Name: `+L.name+`
Material Type: `+L.type+`

Program Info Log: `+O+`
`+K+`
`+nt)}else O!==""?ee("WebGLProgram: Program Info Log:",O):($===""||J==="")&&(G=!1);G&&(L.diagnostics={runnable:W,programLog:O,vertexShader:{log:$,prefix:p},fragmentShader:{log:J,prefix:m}})}s.deleteShader(b),s.deleteShader(M),_=new fr(s,x),T=Jv(s,x)}let _;this.getUniforms=function(){return _===void 0&&A(this),_};let T;this.getAttributes=function(){return T===void 0&&A(this),T};let I=e.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return I===!1&&(I=s.getProgramParameter(x,Hv)),I},this.destroy=function(){n.releaseStatesOfProgram(this),s.deleteProgram(x),this.program=void 0},this.type=e.shaderType,this.name=e.shaderName,this.id=Vv++,this.cacheKey=t,this.usedTimes=1,this.program=x,this.vertexShader=b,this.fragmentShader=M,this}var fx=0,Sh=class{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(t,e,n){let s=this._getShaderCacheForMaterial(t);return s.has(e)===!1&&(s.add(e),e.usedTimes++),s.has(n)===!1&&(s.add(n),n.usedTimes++),this}remove(t){let e=this.materialCache.get(t);for(let n of e)n.usedTimes--,n.usedTimes===0&&this.shaderCache.delete(n.code);return this.materialCache.delete(t),this}getVertexShaderStage(t){return this._getShaderStage(t.vertexShader)}getFragmentShaderStage(t){return this._getShaderStage(t.fragmentShader)}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(t){let e=this.materialCache,n=e.get(t);return n===void 0&&(n=new Set,e.set(t,n)),n}_getShaderStage(t){let e=this.shaderCache,n=e.get(t);return n===void 0&&(n=new bh(t),e.set(t,n)),n}},bh=class{constructor(t){this.id=fx++,this.code=t,this.usedTimes=0}};function px(i){return i===xi||i===Ma||i===Sa}function mx(i,t,e,n,s,r){let a=new kr,o=new Sh,c=new Set,l=[],h=new Map,d=n.logarithmicDepthBuffer,u=n.precision,f={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function g(_){return c.add(_),_===0?"uv":`uv${_}`}function x(_,T,I,L,N,B){let D=L.fog,O=N.geometry,$=_.isMeshStandardMaterial||_.isMeshLambertMaterial||_.isMeshPhongMaterial?L.environment:null,J=_.isMeshStandardMaterial||_.isMeshLambertMaterial&&!_.envMap||_.isMeshPhongMaterial&&!_.envMap,W=t.get(_.envMap||$,J),G=W&&W.mapping===ma?W.image.height:null,K=f[_.type];_.precision!==null&&(u=n.getMaxPrecision(_.precision),u!==_.precision&&ee("WebGLProgram.getParameters:",_.precision,"not supported, using",u,"instead."));let nt=O.morphAttributes.position||O.morphAttributes.normal||O.morphAttributes.color,Et=nt!==void 0?nt.length:0,pt=0;O.morphAttributes.position!==void 0&&(pt=1),O.morphAttributes.normal!==void 0&&(pt=2),O.morphAttributes.color!==void 0&&(pt=3);let Ft,Dt,ft,U;if(K){let he=bn[K];Ft=he.vertexShader,Dt=he.fragmentShader}else{Ft=_.vertexShader,Dt=_.fragmentShader;let he=o.getVertexShaderStage(_),de=o.getFragmentShaderStage(_);o.update(_,he,de),ft=he.id,U=de.id}let V=i.getRenderTarget(),dt=i.state.buffers.depth.getReversed(),Mt=N.isInstancedMesh===!0,yt=N.isBatchedMesh===!0,It=!!_.map,Kt=!!_.matcap,it=!!W,ut=!!_.aoMap,Y=!!_.lightMap,st=!!_.bumpMap&&_.wireframe===!1,vt=!!_.normalMap,Vt=!!_.displacementMap,St=!!_.emissiveMap,Xt=!!_.metalnessMap,Qt=!!_.roughnessMap,F=_.anisotropy>0,ye=_.clearcoat>0,ne=_.dispersion>0,C=_.retroreflectivity>0,y=_.iridescence>0,H=_.sheen>0,X=_.transmission>0,tt=F&&!!_.anisotropyMap,ct=ye&&!!_.clearcoatMap,_t=ye&&!!_.clearcoatNormalMap,rt=ye&&!!_.clearcoatRoughnessMap,ht=y&&!!_.iridescenceMap,bt=y&&!!_.iridescenceThicknessMap,Wt=H&&!!_.sheenColorMap,At=H&&!!_.sheenRoughnessMap,Tt=!!_.specularMap,Bt=!!_.specularColorMap,jt=!!_.specularIntensityMap,re=X&&!!_.transmissionMap,R=X&&!!_.thicknessMap,j=!!_.gradientMap,k=!!_.alphaMap,at=_.alphaTest>0,xt=!!_.alphaHash,et=!!_.extensions,wt=zn;_.toneMapped&&(V===null||V.isXRRenderTarget===!0)&&(wt=i.toneMapping);let Pt={shaderID:K,shaderType:_.type,shaderName:_.name,vertexShader:Ft,fragmentShader:Dt,defines:_.defines,customVertexShaderID:ft,customFragmentShaderID:U,isRawShaderMaterial:_.isRawShaderMaterial===!0,glslVersion:_.glslVersion,precision:u,batching:yt,batchingColor:yt&&N._colorsTexture!==null,instancing:Mt,instancingColor:Mt&&N.instanceColor!==null,instancingMorph:Mt&&N.morphTexture!==null,outputColorSpace:V===null?i.outputColorSpace:V.isXRRenderTarget===!0?V.texture.colorSpace:Se.workingColorSpace,alphaToCoverage:!!_.alphaToCoverage,map:It,matcap:Kt,envMap:it,envMapMode:it&&W.mapping,envMapCubeUVHeight:G,aoMap:ut,lightMap:Y,bumpMap:st,normalMap:vt,displacementMap:Vt,emissiveMap:St,normalMapObjectSpace:vt&&_.normalMapType===Gu,normalMapTangentSpace:vt&&_.normalMapType===Cc,packedNormalMap:vt&&_.normalMapType===Cc&&px(_.normalMap.format),metalnessMap:Xt,roughnessMap:Qt,anisotropy:F,anisotropyMap:tt,clearcoat:ye,clearcoatMap:ct,clearcoatNormalMap:_t,clearcoatRoughnessMap:rt,dispersion:ne,retroreflection:C,iridescence:y,iridescenceMap:ht,iridescenceThicknessMap:bt,sheen:H,sheenColorMap:Wt,sheenRoughnessMap:At,specularMap:Tt,specularColorMap:Bt,specularIntensityMap:jt,transmission:X,transmissionMap:re,thicknessMap:R,gradientMap:j,opaque:_.transparent===!1&&_.blending===cr&&_.alphaToCoverage===!1,alphaMap:k,alphaTest:at,alphaHash:xt,combine:_.combine,mapUv:It&&g(_.map.channel),aoMapUv:ut&&g(_.aoMap.channel),lightMapUv:Y&&g(_.lightMap.channel),bumpMapUv:st&&g(_.bumpMap.channel),normalMapUv:vt&&g(_.normalMap.channel),displacementMapUv:Vt&&g(_.displacementMap.channel),emissiveMapUv:St&&g(_.emissiveMap.channel),metalnessMapUv:Xt&&g(_.metalnessMap.channel),roughnessMapUv:Qt&&g(_.roughnessMap.channel),anisotropyMapUv:tt&&g(_.anisotropyMap.channel),clearcoatMapUv:ct&&g(_.clearcoatMap.channel),clearcoatNormalMapUv:_t&&g(_.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:rt&&g(_.clearcoatRoughnessMap.channel),iridescenceMapUv:ht&&g(_.iridescenceMap.channel),iridescenceThicknessMapUv:bt&&g(_.iridescenceThicknessMap.channel),sheenColorMapUv:Wt&&g(_.sheenColorMap.channel),sheenRoughnessMapUv:At&&g(_.sheenRoughnessMap.channel),specularMapUv:Tt&&g(_.specularMap.channel),specularColorMapUv:Bt&&g(_.specularColorMap.channel),specularIntensityMapUv:jt&&g(_.specularIntensityMap.channel),transmissionMapUv:re&&g(_.transmissionMap.channel),thicknessMapUv:R&&g(_.thicknessMap.channel),alphaMapUv:k&&g(_.alphaMap.channel),vertexTangents:!!O.attributes.tangent&&(vt||F),vertexNormals:!!O.attributes.normal,vertexColors:_.vertexColors,vertexAlphas:_.vertexColors===!0&&!!O.attributes.color&&O.attributes.color.itemSize===4,pointsUvs:N.isPoints===!0&&!!O.attributes.uv&&(It||k),fog:!!D,useFog:_.fog===!0,fogExp2:!!D&&D.isFogExp2,flatShading:_.wireframe===!1&&(_.flatShading===!0||O.attributes.normal===void 0&&vt===!1&&(_.isMeshLambertMaterial||_.isMeshPhongMaterial||_.isMeshStandardMaterial||_.isMeshPhysicalMaterial)),sizeAttenuation:_.sizeAttenuation===!0,logarithmicDepthBuffer:d,reversedDepthBuffer:dt,skinning:N.isSkinnedMesh===!0,hasPositionAttribute:O.attributes.position!==void 0,morphTargets:O.morphAttributes.position!==void 0,morphNormals:O.morphAttributes.normal!==void 0,morphColors:O.morphAttributes.color!==void 0,morphTargetsCount:Et,morphTextureStride:pt,numSunLights:T.sun.length,numDirLights:T.directional.length,numPointLights:T.point.length,numSpotLights:T.spot.length,numSpotLightMaps:T.spotLightMap.length,numRectAreaLights:T.rectArea.length,numHemiLights:T.hemi.length,numSunLightShadows:T.sunShadowMap.length,numDirLightShadows:T.directionalShadowMap.length,numPointLightShadows:T.pointShadowMap.length,numSpotLightShadows:T.spotShadowMap.length,numSpotLightShadowsWithMaps:T.numSpotLightShadowsWithMaps,numLightProbes:T.numLightProbes,numLightProbeGrids:B.length,numClippingPlanes:r.numPlanes,numClipIntersection:r.numIntersection,dithering:_.dithering,shadowMapEnabled:i.shadowMap.enabled&&I.length>0,shadowMapType:i.shadowMap.type,toneMapping:wt,decodeVideoTexture:It&&_.map.isVideoTexture===!0&&Se.getTransfer(_.map.colorSpace)===Ae,decodeVideoTextureEmissive:St&&_.emissiveMap.isVideoTexture===!0&&Se.getTransfer(_.emissiveMap.colorSpace)===Ae,premultipliedAlpha:_.premultipliedAlpha,doubleSided:_.side===fn,flipSided:_.side===rn,useDepthPacking:_.depthPacking>=0,depthPacking:_.depthPacking||0,index0AttributeName:_.index0AttributeName,extensionClipCullDistance:et&&_.extensions.clipCullDistance===!0&&e.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(et&&_.extensions.multiDraw===!0||yt)&&e.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:e.has("KHR_parallel_shader_compile"),customProgramCacheKey:_.customProgramCacheKey()};return Pt.vertexUv1s=c.has(1),Pt.vertexUv2s=c.has(2),Pt.vertexUv3s=c.has(3),c.clear(),Pt}function p(_){let T=[];if(_.shaderID?T.push(_.shaderID):(T.push(_.customVertexShaderID),T.push(_.customFragmentShaderID)),_.defines!==void 0)for(let I in _.defines)T.push(I),T.push(_.defines[I]);return _.isRawShaderMaterial===!1&&(m(T,_),S(T,_),T.push(i.outputColorSpace)),T.push(_.customProgramCacheKey),T.join()}function m(_,T){_.push(T.precision),_.push(T.outputColorSpace),_.push(T.envMapMode),_.push(T.envMapCubeUVHeight),_.push(T.mapUv),_.push(T.alphaMapUv),_.push(T.lightMapUv),_.push(T.aoMapUv),_.push(T.bumpMapUv),_.push(T.normalMapUv),_.push(T.displacementMapUv),_.push(T.emissiveMapUv),_.push(T.metalnessMapUv),_.push(T.roughnessMapUv),_.push(T.anisotropyMapUv),_.push(T.clearcoatMapUv),_.push(T.clearcoatNormalMapUv),_.push(T.clearcoatRoughnessMapUv),_.push(T.iridescenceMapUv),_.push(T.iridescenceThicknessMapUv),_.push(T.sheenColorMapUv),_.push(T.sheenRoughnessMapUv),_.push(T.specularMapUv),_.push(T.specularColorMapUv),_.push(T.specularIntensityMapUv),_.push(T.transmissionMapUv),_.push(T.thicknessMapUv),_.push(T.combine),_.push(T.fogExp2),_.push(T.sizeAttenuation),_.push(T.morphTargetsCount),_.push(T.morphAttributeCount),_.push(T.numSunLights),_.push(T.numDirLights),_.push(T.numPointLights),_.push(T.numSpotLights),_.push(T.numSpotLightMaps),_.push(T.numHemiLights),_.push(T.numRectAreaLights),_.push(T.numSunLightShadows),_.push(T.numDirLightShadows),_.push(T.numPointLightShadows),_.push(T.numSpotLightShadows),_.push(T.numSpotLightShadowsWithMaps),_.push(T.numLightProbes),_.push(T.shadowMapType),_.push(T.toneMapping),_.push(T.numClippingPlanes),_.push(T.numClipIntersection),_.push(T.depthPacking)}function S(_,T){a.disableAll(),T.instancing&&a.enable(0),T.instancingColor&&a.enable(1),T.instancingMorph&&a.enable(2),T.matcap&&a.enable(3),T.envMap&&a.enable(4),T.normalMapObjectSpace&&a.enable(5),T.normalMapTangentSpace&&a.enable(6),T.clearcoat&&a.enable(7),T.iridescence&&a.enable(8),T.alphaTest&&a.enable(9),T.vertexColors&&a.enable(10),T.vertexAlphas&&a.enable(11),T.vertexUv1s&&a.enable(12),T.vertexUv2s&&a.enable(13),T.vertexUv3s&&a.enable(14),T.vertexTangents&&a.enable(15),T.anisotropy&&a.enable(16),T.alphaHash&&a.enable(17),T.batching&&a.enable(18),T.dispersion&&a.enable(19),T.retroreflection&&a.enable(24),T.batchingColor&&a.enable(20),T.gradientMap&&a.enable(21),T.packedNormalMap&&a.enable(22),T.vertexNormals&&a.enable(23),_.push(a.mask),a.disableAll(),T.fog&&a.enable(0),T.useFog&&a.enable(1),T.flatShading&&a.enable(2),T.logarithmicDepthBuffer&&a.enable(3),T.reversedDepthBuffer&&a.enable(4),T.skinning&&a.enable(5),T.morphTargets&&a.enable(6),T.morphNormals&&a.enable(7),T.morphColors&&a.enable(8),T.premultipliedAlpha&&a.enable(9),T.shadowMapEnabled&&a.enable(10),T.doubleSided&&a.enable(11),T.flipSided&&a.enable(12),T.useDepthPacking&&a.enable(13),T.dithering&&a.enable(14),T.transmission&&a.enable(15),T.sheen&&a.enable(16),T.opaque&&a.enable(17),T.pointsUvs&&a.enable(18),T.decodeVideoTexture&&a.enable(19),T.decodeVideoTextureEmissive&&a.enable(20),T.alphaToCoverage&&a.enable(21),T.numLightProbeGrids>0&&a.enable(22),T.hasPositionAttribute&&a.enable(23),_.push(a.mask)}function E(_){let T=f[_.type],I;if(T){let L=bn[T];I=ba.clone(L.uniforms)}else I=_.uniforms;return I}function v(_,T){let I=h.get(T);return I!==void 0?++I.usedTimes:(I=new dx(i,T,_,s),l.push(I),h.set(T,I)),I}function b(_){if(--_.usedTimes===0){let T=l.indexOf(_);l[T]=l[l.length-1],l.pop(),h.delete(_.cacheKey),_.destroy()}}function M(_){o.remove(_)}function A(){o.dispose()}return{getParameters:x,getProgramCacheKey:p,getUniforms:E,acquireProgram:v,releaseProgram:b,releaseShaderCache:M,programs:l,dispose:A}}function gx(){let i=new WeakMap;function t(a){return i.has(a)}function e(a){let o=i.get(a);return o===void 0&&(o={},i.set(a,o)),o}function n(a){i.delete(a)}function s(a,o,c){i.get(a)[o]=c}function r(){i=new WeakMap}return{has:t,get:e,remove:n,update:s,dispose:r}}function vx(i,t){return i.groupOrder!==t.groupOrder?i.groupOrder-t.groupOrder:i.renderOrder!==t.renderOrder?i.renderOrder-t.renderOrder:i.material.id!==t.material.id?i.material.id-t.material.id:i.materialVariant!==t.materialVariant?i.materialVariant-t.materialVariant:i.z!==t.z?i.z-t.z:i.id-t.id}function wd(i,t){return i.groupOrder!==t.groupOrder?i.groupOrder-t.groupOrder:i.renderOrder!==t.renderOrder?i.renderOrder-t.renderOrder:i.z!==t.z?t.z-i.z:i.id-t.id}function Td(){let i=[],t=0,e=[],n=[],s=[];function r(){t=0,e.length=0,n.length=0,s.length=0}function a(u){let f=0;return u.isInstancedMesh&&(f+=2),u.isSkinnedMesh&&(f+=1),f}function o(u,f,g,x,p,m){let S=i[t];return S===void 0?(S={id:u.id,object:u,geometry:f,material:g,materialVariant:a(u),groupOrder:x,renderOrder:u.renderOrder,z:p,group:m},i[t]=S):(S.id=u.id,S.object=u,S.geometry=f,S.material=g,S.materialVariant=a(u),S.groupOrder=x,S.renderOrder=u.renderOrder,S.z=p,S.group=m),t++,S}function c(u,f,g,x,p,m,S){S.reversedDepth===!0&&(p=-p);let E=o(u,f,g,x,p,m);g.transmission>0?n.push(E):g.transparent===!0?s.push(E):e.push(E)}function l(u,f,g,x,p,m){let S=o(u,f,g,x,p,m);g.transmission>0?n.unshift(S):g.transparent===!0?s.unshift(S):e.unshift(S)}function h(u,f){e.length>1&&e.sort(u||vx),n.length>1&&n.sort(f||wd),s.length>1&&s.sort(f||wd)}function d(){for(let u=t,f=i.length;u<f;u++){let g=i[u];if(g.id===null)break;g.id=null,g.object=null,g.geometry=null,g.material=null,g.group=null}}return{opaque:e,transmissive:n,transparent:s,init:r,push:c,unshift:l,finish:d,sort:h}}function xx(){let i=new WeakMap;function t(n,s){let r=i.get(n),a;return r===void 0?(a=new Td,i.set(n,[a])):s>=r.length?(a=new Td,r.push(a)):a=r[s],a}function e(){i=new WeakMap}return{get:t,dispose:e}}function _x(){let i={};return{get:function(t){if(i[t.id]!==void 0)return i[t.id];let e;switch(t.type){case"SunLight":case"DirectionalLight":e={direction:new P,color:new Ot};break;case"SpotLight":e={position:new P,direction:new P,color:new Ot,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":e={position:new P,color:new Ot,distance:0,decay:0};break;case"HemisphereLight":e={direction:new P,skyColor:new Ot,groundColor:new Ot};break;case"RectAreaLight":e={color:new Ot,position:new P,halfWidth:new P,halfHeight:new P};break}return i[t.id]=e,e}}}function yx(){let i={};return{get:function(t){if(i[t.id]!==void 0)return i[t.id];let e;switch(t.type){case"SunLight":case"DirectionalLight":e={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new mt};break;case"SpotLight":e={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new mt};break;case"PointLight":e={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new mt,shadowCameraNear:1,shadowCameraFar:1e3};break}return i[t.id]=e,e}}}var Mx=0;function Sx(i,t){return(t.castShadow?2:0)-(i.castShadow?2:0)+(t.map?1:0)-(i.map?1:0)}function bx(i){let t=new _x,e=yx(),n={version:0,hash:{sunLength:-1,directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numSunShadows:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],sun:[],sunShadow:[],sunShadowMap:[],sunShadowMatrix:[],sunShadowCascade:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let l=0;l<9;l++)n.probe.push(new P);let s=new P,r=new ue,a=new ue;function o(l){let h=0,d=0,u=0;for(let N=0;N<9;N++)n.probe[N].set(0,0,0);let f=0,g=0,x=0,p=0,m=0,S=0,E=0,v=0,b=0,M=0,A=0,_=0,T=0,I=0;l.sort(Sx);for(let N=0,B=l.length;N<B;N++){let D=l[N],O=D.color,$=D.intensity,J=D.distance,W=null;if(D.shadow&&D.shadow.map&&(D.shadow.map.texture.format===xi?W=D.shadow.map.texture:W=D.shadow.map.depthTexture||D.shadow.map.texture),D.isAmbientLight)h+=O.r*$,d+=O.g*$,u+=O.b*$;else if(D.isLightProbe){for(let G=0;G<9;G++)n.probe[G].addScaledVector(D.sh.coefficients[G],$);I++}else if(D.isSunLight){let G=t.get(D);if(G.color.copy(D.color).multiplyScalar(D.intensity),D.castShadow){let K=D.shadow,nt=e.get(D);nt.shadowIntensity=K.intensity,nt.shadowBias=K.bias,nt.shadowNormalBias=K.normalBias,nt.shadowRadius=K.radius,nt.shadowMapSize.copy(K.mapSize).multiply(K.getFrameExtents()),n.sunShadow[g]=nt,n.sunShadowMap[g]=W;let Et=K.getViewportCount();for(let pt=0;pt<Et;pt++)n.sunShadowMatrix[x+pt]=K.getMatrix(pt),n.sunShadowCascade[x+pt]=K._cascadeData[pt];x+=Et,g++}n.sun[f]=G,f++}else if(D.isDirectionalLight){let G=t.get(D);if(G.color.copy(D.color).multiplyScalar(D.intensity),D.castShadow){let K=D.shadow,nt=e.get(D);nt.shadowIntensity=K.intensity,nt.shadowBias=K.bias,nt.shadowNormalBias=K.normalBias,nt.shadowRadius=K.radius,nt.shadowMapSize=K.mapSize,n.directionalShadow[p]=nt,n.directionalShadowMap[p]=W,n.directionalShadowMatrix[p]=D.shadow.matrix,b++}n.directional[p]=G,p++}else if(D.isSpotLight){let G=t.get(D);G.position.setFromMatrixPosition(D.matrixWorld),G.color.copy(O).multiplyScalar($),G.distance=J,G.coneCos=Math.cos(D.angle),G.penumbraCos=Math.cos(D.angle*(1-D.penumbra)),G.decay=D.decay,n.spot[S]=G;let K=D.shadow;if(D.map&&(n.spotLightMap[_]=D.map,_++,K.updateMatrices(D),D.castShadow&&T++),n.spotLightMatrix[S]=K.matrix,D.castShadow){let nt=e.get(D);nt.shadowIntensity=K.intensity,nt.shadowBias=K.bias,nt.shadowNormalBias=K.normalBias,nt.shadowRadius=K.radius,nt.shadowMapSize=K.mapSize,n.spotShadow[S]=nt,n.spotShadowMap[S]=W,A++}S++}else if(D.isRectAreaLight){let G=t.get(D);G.color.copy(O).multiplyScalar($),G.halfWidth.set(D.width*.5,0,0),G.halfHeight.set(0,D.height*.5,0),n.rectArea[E]=G,E++}else if(D.isPointLight){let G=t.get(D);if(G.color.copy(D.color).multiplyScalar(D.intensity),G.distance=D.distance,G.decay=D.decay,D.castShadow){let K=D.shadow,nt=e.get(D);nt.shadowIntensity=K.intensity,nt.shadowBias=K.bias,nt.shadowNormalBias=K.normalBias,nt.shadowRadius=K.radius,nt.shadowMapSize=K.mapSize,nt.shadowCameraNear=K.camera.near,nt.shadowCameraFar=K.camera.far,n.pointShadow[m]=nt,n.pointShadowMap[m]=W,n.pointShadowMatrix[m]=D.shadow.matrix,M++}n.point[m]=G,m++}else if(D.isHemisphereLight){let G=t.get(D);G.skyColor.copy(D.color).multiplyScalar($),G.groundColor.copy(D.groundColor).multiplyScalar($),n.hemi[v]=G,v++}}E>0&&(i.has("OES_texture_float_linear")===!0?(n.rectAreaLTC1=Ct.LTC_FLOAT_1,n.rectAreaLTC2=Ct.LTC_FLOAT_2):(n.rectAreaLTC1=Ct.LTC_HALF_1,n.rectAreaLTC2=Ct.LTC_HALF_2)),n.ambient[0]=h,n.ambient[1]=d,n.ambient[2]=u;let L=n.hash;(L.sunLength!==f||L.directionalLength!==p||L.pointLength!==m||L.spotLength!==S||L.rectAreaLength!==E||L.hemiLength!==v||L.numSunShadows!==g||L.numDirectionalShadows!==b||L.numPointShadows!==M||L.numSpotShadows!==A||L.numSpotMaps!==_||L.numLightProbes!==I)&&(n.sun.length=f,n.directional.length=p,n.spot.length=S,n.rectArea.length=E,n.point.length=m,n.hemi.length=v,n.sunShadow.length=g,n.sunShadowMap.length=g,n.sunShadowMatrix.length=x,n.sunShadowCascade.length=x,n.directionalShadow.length=b,n.directionalShadowMap.length=b,n.directionalShadowMatrix.length=b,n.pointShadow.length=M,n.pointShadowMap.length=M,n.pointShadowMatrix.length=M,n.spotShadow.length=A,n.spotShadowMap.length=A,n.spotLightMatrix.length=A+_-T,n.spotLightMap.length=_,n.numSpotLightShadowsWithMaps=T,n.numLightProbes=I,L.sunLength=f,L.directionalLength=p,L.pointLength=m,L.spotLength=S,L.rectAreaLength=E,L.hemiLength=v,L.numSunShadows=g,L.numDirectionalShadows=b,L.numPointShadows=M,L.numSpotShadows=A,L.numSpotMaps=_,L.numLightProbes=I,n.version=Mx++)}function c(l,h){let d=0,u=0,f=0,g=0,x=0,p=0,m=h.matrixWorldInverse;for(let S=0,E=l.length;S<E;S++){let v=l[S];if(v.isSunLight){let b=n.sun[d];b.direction.setFromMatrixPosition(v.matrixWorld),b.direction.transformDirection(m),d++}else if(v.isDirectionalLight){let b=n.directional[u];b.direction.setFromMatrixPosition(v.matrixWorld),s.setFromMatrixPosition(v.target.matrixWorld),b.direction.sub(s),b.direction.transformDirection(m),u++}else if(v.isSpotLight){let b=n.spot[g];b.position.setFromMatrixPosition(v.matrixWorld),b.position.applyMatrix4(m),b.direction.setFromMatrixPosition(v.matrixWorld),s.setFromMatrixPosition(v.target.matrixWorld),b.direction.sub(s),b.direction.transformDirection(m),g++}else if(v.isRectAreaLight){let b=n.rectArea[x];b.position.setFromMatrixPosition(v.matrixWorld),b.position.applyMatrix4(m),a.identity(),r.copy(v.matrixWorld),r.premultiply(m),a.extractRotation(r),b.halfWidth.set(v.width*.5,0,0),b.halfHeight.set(0,v.height*.5,0),b.halfWidth.applyMatrix4(a),b.halfHeight.applyMatrix4(a),x++}else if(v.isPointLight){let b=n.point[f];b.position.setFromMatrixPosition(v.matrixWorld),b.position.applyMatrix4(m),f++}else if(v.isHemisphereLight){let b=n.hemi[p];b.direction.setFromMatrixPosition(v.matrixWorld),b.direction.transformDirection(m),p++}}}return{setup:o,setupView:c,state:n}}function Ad(i){let t=new bx(i),e=[],n=[],s=[];function r(u){d.camera=u,e.length=0,n.length=0,s.length=0}function a(u){e.push(u)}function o(u){n.push(u)}function c(u){s.push(u)}function l(){t.setup(e)}function h(u){t.setupView(e,u)}let d={lightsArray:e,shadowsArray:n,lightProbeGridArray:s,camera:null,lights:t,transmissionRenderTarget:{},textureUnits:0};return{init:r,state:d,setupLights:l,setupLightsView:h,pushLight:a,pushShadow:o,pushLightProbeGrid:c}}function Ex(i){let t=new WeakMap;function e(s,r=0){let a=t.get(s),o;return a===void 0?(o=new Ad(i),t.set(s,[o])):r>=a.length?(o=new Ad(i),a.push(o)):o=a[r],o}function n(){t=new WeakMap}return{get:e,dispose:n}}var wx=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,Tx=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ).rg;
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ).r;
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( max( 0.0, squared_mean - mean * mean ) );
	gl_FragColor = vec4( mean, std_dev, 0.0, 1.0 );
}`,Ax=[new P(1,0,0),new P(-1,0,0),new P(0,1,0),new P(0,-1,0),new P(0,0,1),new P(0,0,-1)],Rx=[new P(0,-1,0),new P(0,-1,0),new P(0,0,1),new P(0,0,-1),new P(0,-1,0),new P(0,-1,0)],Rd=new ue,wa=new P,gh=new P;function Cx(i,t,e){let n=new er,s=new mt,r=new mt,a=new xe,o=new Ro,c=new Co,l={},h=e.maxTextureSize,d={[ns]:rn,[rn]:ns,[fn]:fn},u=new Ue({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new mt},radius:{value:4}},vertexShader:wx,fragmentShader:Tx}),f=u.clone();f.defines.HORIZONTAL_PASS=1;let g=new _e;g.setAttribute("position",new Pe(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));let x=new ot(g,u),p=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=_s;let m=this.type;this.render=function(M,A,_){if(p.enabled===!1||p.autoUpdate===!1&&p.needsUpdate===!1||M.length===0)return;this.type===yu&&(ee("WebGLShadowMap: PCFSoftShadowMap has been removed. Using PCFShadowMap instead."),this.type=_s);let T=i.getRenderTarget(),I=i.getActiveCubeFace(),L=i.getActiveMipmapLevel(),N=i.state;N.setBlending(vi),N.buffers.depth.getReversed()===!0?N.buffers.color.setClear(0,0,0,0):N.buffers.color.setClear(1,1,1,1),N.buffers.depth.setTest(!0),N.setScissorTest(!1);let B=m!==this.type;B&&A.traverse(function(D){D.material&&(Array.isArray(D.material)?D.material.forEach(O=>O.needsUpdate=!0):D.material.needsUpdate=!0)});for(let D=0,O=M.length;D<O;D++){let $=M[D],J=$.shadow;if(J===void 0){ee("WebGLShadowMap:",$,"has no shadow.");continue}if(J.autoUpdate===!1&&J.needsUpdate===!1)continue;s.copy(J.mapSize);let W=J.getFrameExtents();s.multiply(W),r.copy(J.mapSize),(s.x>h||s.y>h)&&(s.x>h&&(r.x=Math.floor(h/W.x),s.x=r.x*W.x,J.mapSize.x=r.x),s.y>h&&(r.y=Math.floor(h/W.y),s.y=r.y*W.y,J.mapSize.y=r.y));let G=i.state.buffers.depth.getReversed();if(J.camera._reversedDepth=G,J.map===null||B===!0){if(J.map!==null&&(J.map.depthTexture!==null&&(J.map.depthTexture.dispose(),J.map.depthTexture=null),J.map.dispose()),this.type===or){if($.isPointLight){ee("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}J.map=new An(s.x,s.y,{format:xi,type:On,minFilter:$e,magFilter:$e,generateMipmaps:!1}),J.map.texture.name=$.name+".shadowMap",J.map.depthTexture=new ji(s.x,s.y,Gn),J.map.depthTexture.name=$.name+".shadowMapDepth",J.map.depthTexture.format=di,J.map.depthTexture.compareFunction=null,J.map.depthTexture.minFilter=en,J.map.depthTexture.magFilter=en}else $.isPointLight?(J.map=new Uc(s.x),J.map.depthTexture=new yo(s.x,ai)):(J.map=new An(s.x,s.y),J.map.depthTexture=new ji(s.x,s.y,ai)),J.map.depthTexture.name=$.name+".shadowMap",J.map.depthTexture.format=di,this.type===_s?(J.map.depthTexture.compareFunction=G?Ic:Pc,J.map.depthTexture.minFilter=$e,J.map.depthTexture.magFilter=$e):(J.map.depthTexture.compareFunction=null,J.map.depthTexture.minFilter=en,J.map.depthTexture.magFilter=en);J.camera.updateProjectionMatrix()}J.map.isWebGLCubeRenderTarget!==!0&&(J.map.width!==s.x||J.map.height!==s.y)&&J.map.setSize(s.x,s.y);let K=J.map.isWebGLCubeRenderTarget?6:J.getViewportCount();$.isPointLight!==!0&&J.updateMatrices($,_);for(let nt=0;nt<K;nt++){let Et=J.getCamera(nt);if($.isPointLight){let pt=J.camera,Ft=J.matrix,Dt=$.distance||pt.far;Dt!==pt.far&&(pt.far=Dt,pt.updateProjectionMatrix()),wa.setFromMatrixPosition($.matrixWorld),pt.position.copy(wa),gh.copy(pt.position),gh.add(Ax[nt]),pt.up.copy(Rx[nt]),pt.lookAt(gh),pt.updateMatrixWorld(),Ft.makeTranslation(-wa.x,-wa.y,-wa.z),Rd.multiplyMatrices(pt.projectionMatrix,pt.matrixWorldInverse),J._frustum.setFromProjectionMatrix(Rd,pt.coordinateSystem,pt.reversedDepth)}if(J.map.isWebGLCubeRenderTarget)i.setRenderTarget(J.map,nt),i.clear();else{nt===0&&(i.setRenderTarget(J.map),i.clear());let pt=J.getViewport(nt);a.set(r.x*pt.x,r.y*pt.y,r.x*pt.z,r.y*pt.w),N.viewport(a)}n=J.getFrustum(nt),v(A,_,Et,$,this.type)}J.isPointLightShadow!==!0&&this.type===or&&S(J,_),J.needsUpdate=!1}m=this.type,p.needsUpdate=!1,i.setRenderTarget(T,I,L)};function S(M,A){let _=t.update(x);u.defines.VSM_SAMPLES!==M.blurSamples&&(u.defines.VSM_SAMPLES=M.blurSamples,f.defines.VSM_SAMPLES=M.blurSamples,u.needsUpdate=!0,f.needsUpdate=!0),M.mapPass===null?M.mapPass=new An(s.x,s.y,{format:xi,type:On}):(M.mapPass.width!==M.map.width||M.mapPass.height!==M.map.height)&&M.mapPass.setSize(M.map.width,M.map.height),u.uniforms.shadow_pass.value=M.map.depthTexture,u.uniforms.resolution.value.set(M.map.width,M.map.height),u.uniforms.radius.value=M.radius,i.setRenderTarget(M.mapPass),i.clear(),i.renderBufferDirect(A,null,_,u,x,null),f.uniforms.shadow_pass.value=M.mapPass.texture,f.uniforms.resolution.value.set(M.map.width,M.map.height),f.uniforms.radius.value=M.radius,i.setRenderTarget(M.map),i.clear(),i.renderBufferDirect(A,null,_,f,x,null)}function E(M,A,_,T){let I=null,L=_.isPointLight===!0?M.customDistanceMaterial:M.customDepthMaterial;if(L!==void 0)I=L;else if(I=_.isPointLight===!0?c:o,i.localClippingEnabled&&A.clipShadows===!0&&Array.isArray(A.clippingPlanes)&&A.clippingPlanes.length!==0||A.displacementMap&&A.displacementScale!==0||A.alphaMap&&A.alphaTest>0||A.map&&A.alphaTest>0||A.alphaToCoverage===!0){let N=I.uuid,B=A.uuid,D=l[N];D===void 0&&(D={},l[N]=D);let O=D[B];O===void 0&&(O=I.clone(),D[B]=O,A.addEventListener("dispose",b)),I=O}if(I.visible=A.visible,I.wireframe=A.wireframe,T===or?I.side=A.shadowSide!==null?A.shadowSide:A.side:I.side=A.shadowSide!==null?A.shadowSide:d[A.side],I.alphaMap=A.alphaMap,I.alphaTest=A.alphaToCoverage===!0?.5:A.alphaTest,I.map=A.map,I.clipShadows=A.clipShadows,I.clippingPlanes=A.clippingPlanes,I.clipIntersection=A.clipIntersection,I.displacementMap=A.displacementMap,I.displacementScale=A.displacementScale,I.displacementBias=A.displacementBias,I.wireframeLinewidth=A.wireframeLinewidth,I.linewidth=A.linewidth,_.isPointLight===!0&&I.isMeshDistanceMaterial===!0){let N=i.properties.get(I);N.light=_}return I}function v(M,A,_,T,I){if(M.visible===!1)return;if(M.layers.test(A.layers)&&(M.isMesh||M.isLine||M.isPoints)&&(M.castShadow||M.receiveShadow&&I===or)&&(!M.frustumCulled||M.intersectsFrustum(n))){M.modelViewMatrix.multiplyMatrices(_.matrixWorldInverse,M.matrixWorld);let B=t.update(M),D=M.material;if(Array.isArray(D)){let O=B.groups;for(let $=0,J=O.length;$<J;$++){let W=O[$],G=D[W.materialIndex];if(G&&G.visible){let K=E(M,G,T,I);M.onBeforeShadow(i,M,A,_,B,K,W),i.renderBufferDirect(_,null,B,K,M,W),M.onAfterShadow(i,M,A,_,B,K,W)}}}else if(D.visible){let O=E(M,D,T,I);M.onBeforeShadow(i,M,A,_,B,O,null),i.renderBufferDirect(_,null,B,O,M,null),M.onAfterShadow(i,M,A,_,B,O,null)}}let N=M.children;for(let B=0,D=N.length;B<D;B++)v(N[B],A,_,T,I)}function b(M){M.target.removeEventListener("dispose",b);for(let _ in l){let T=l[_],I=M.target.uuid;I in T&&(T[I].dispose(),delete T[I])}}}function Px(i,t){function e(){let R=!1,j=new xe,k=null,at=new xe(0,0,0,0);return{setMask:function(xt){k!==xt&&!R&&(i.colorMask(xt,xt,xt,xt),k=xt)},setLocked:function(xt){R=xt},setClear:function(xt,et,wt,Pt,he){he===!0&&(xt*=Pt,et*=Pt,wt*=Pt),j.set(xt,et,wt,Pt),at.equals(j)===!1&&(i.clearColor(xt,et,wt,Pt),at.copy(j))},reset:function(){R=!1,k=null,at.set(-1,0,0,0)}}}function n(){let R=!1,j=!1,k=null,at=null,xt=null;return{setReversed:function(et){if(j!==et){let wt=t.get("EXT_clip_control");et?wt.clipControlEXT(wt.LOWER_LEFT_EXT,wt.ZERO_TO_ONE_EXT):wt.clipControlEXT(wt.LOWER_LEFT_EXT,wt.NEGATIVE_ONE_TO_ONE_EXT),j=et;let Pt=xt;xt=null,this.setClear(Pt)}},getReversed:function(){return j},setTest:function(et){et?V(i.DEPTH_TEST):dt(i.DEPTH_TEST)},setMask:function(et){k!==et&&!R&&(i.depthMask(et),k=et)},setFunc:function(et){if(j&&(et=td[et]),at!==et){switch(et){case ro:i.depthFunc(i.NEVER);break;case ao:i.depthFunc(i.ALWAYS);break;case oo:i.depthFunc(i.LESS);break;case Ys:i.depthFunc(i.LEQUAL);break;case co:i.depthFunc(i.EQUAL);break;case lo:i.depthFunc(i.GEQUAL);break;case ho:i.depthFunc(i.GREATER);break;case uo:i.depthFunc(i.NOTEQUAL);break;default:i.depthFunc(i.LEQUAL)}at=et}},setLocked:function(et){R=et},setClear:function(et){xt!==et&&(xt=et,j&&(et=1-et),i.clearDepth(et))},reset:function(){R=!1,k=null,at=null,xt=null,j=!1}}}function s(){let R=!1,j=null,k=null,at=null,xt=null,et=null,wt=null,Pt=null,he=null;return{setTest:function(de){R||(de?V(i.STENCIL_TEST):dt(i.STENCIL_TEST))},setMask:function(de){j!==de&&!R&&(i.stencilMask(de),j=de)},setFunc:function(de,Ge,ln){(k!==de||at!==Ge||xt!==ln)&&(i.stencilFunc(de,Ge,ln),k=de,at=Ge,xt=ln)},setOp:function(de,Ge,ln){(et!==de||wt!==Ge||Pt!==ln)&&(i.stencilOp(de,Ge,ln),et=de,wt=Ge,Pt=ln)},setLocked:function(de){R=de},setClear:function(de){he!==de&&(i.clearStencil(de),he=de)},reset:function(){R=!1,j=null,k=null,at=null,xt=null,et=null,wt=null,Pt=null,he=null}}}let r=new e,a=new n,o=new s,c=new WeakMap,l=new WeakMap,h={},d={},u={},f=new WeakMap,g=[],x=null,p=!1,m=null,S=null,E=null,v=null,b=null,M=null,A=null,_=new Ot(0,0,0),T=0,I=!1,L=null,N=null,B=null,D=null,O=null,$=i.getParameter(i.MAX_COMBINED_TEXTURE_IMAGE_UNITS),J=!1,W=0,G=i.getParameter(i.VERSION);G.indexOf("WebGL")!==-1?(W=parseFloat(/^WebGL (\d)/.exec(G)[1]),J=W>=1):G.indexOf("OpenGL ES")!==-1&&(W=parseFloat(/^OpenGL ES (\d)/.exec(G)[1]),J=W>=2);let K=null,nt={},Et=i.getParameter(i.SCISSOR_BOX),pt=i.getParameter(i.VIEWPORT),Ft=new xe().fromArray(Et),Dt=new xe().fromArray(pt);function ft(R,j,k,at){let xt=new Uint8Array(4),et=i.createTexture();i.bindTexture(R,et),i.texParameteri(R,i.TEXTURE_MIN_FILTER,i.NEAREST),i.texParameteri(R,i.TEXTURE_MAG_FILTER,i.NEAREST);for(let wt=0;wt<k;wt++)R===i.TEXTURE_3D||R===i.TEXTURE_2D_ARRAY?i.texImage3D(j,0,i.RGBA,1,1,at,0,i.RGBA,i.UNSIGNED_BYTE,xt):i.texImage2D(j+wt,0,i.RGBA,1,1,0,i.RGBA,i.UNSIGNED_BYTE,xt);return et}let U={};U[i.TEXTURE_2D]=ft(i.TEXTURE_2D,i.TEXTURE_2D,1),U[i.TEXTURE_CUBE_MAP]=ft(i.TEXTURE_CUBE_MAP,i.TEXTURE_CUBE_MAP_POSITIVE_X,6),U[i.TEXTURE_2D_ARRAY]=ft(i.TEXTURE_2D_ARRAY,i.TEXTURE_2D_ARRAY,1,1),U[i.TEXTURE_3D]=ft(i.TEXTURE_3D,i.TEXTURE_3D,1,1),r.setClear(0,0,0,1),a.setClear(1),o.setClear(0),V(i.DEPTH_TEST),a.setFunc(Ys),st(!1),vt(Dl),V(i.CULL_FACE),ut(vi);function V(R){h[R]!==!0&&(i.enable(R),h[R]=!0)}function dt(R){h[R]!==!1&&(i.disable(R),h[R]=!1)}function Mt(R,j){return u[R]!==j?(i.bindFramebuffer(R,j),u[R]=j,R===i.DRAW_FRAMEBUFFER&&(u[i.FRAMEBUFFER]=j),R===i.FRAMEBUFFER&&(u[i.DRAW_FRAMEBUFFER]=j),!0):!1}function yt(R,j){let k=g,at=!1;if(R){k=f.get(j),k===void 0&&(k=[],f.set(j,k));let xt=R.textures;if(k.length!==xt.length||k[0]!==i.COLOR_ATTACHMENT0){for(let et=0,wt=xt.length;et<wt;et++)k[et]=i.COLOR_ATTACHMENT0+et;k.length=xt.length,at=!0}}else k[0]!==i.BACK&&(k[0]=i.BACK,at=!0);at&&i.drawBuffers(k)}function It(R){return x!==R?(i.useProgram(R),x=R,!0):!1}let Kt={[ys]:i.FUNC_ADD,[Su]:i.FUNC_SUBTRACT,[bu]:i.FUNC_REVERSE_SUBTRACT};Kt[Eu]=i.MIN,Kt[wu]=i.MAX;let it={[Tu]:i.ZERO,[Au]:i.ONE,[Ru]:i.SRC_COLOR,[Fl]:i.SRC_ALPHA,[Uu]:i.SRC_ALPHA_SATURATE,[Lu]:i.DST_COLOR,[Pu]:i.DST_ALPHA,[Cu]:i.ONE_MINUS_SRC_COLOR,[zl]:i.ONE_MINUS_SRC_ALPHA,[Du]:i.ONE_MINUS_DST_COLOR,[Iu]:i.ONE_MINUS_DST_ALPHA,[Nu]:i.CONSTANT_COLOR,[Fu]:i.ONE_MINUS_CONSTANT_COLOR,[zu]:i.CONSTANT_ALPHA,[Ou]:i.ONE_MINUS_CONSTANT_ALPHA};function ut(R,j,k,at,xt,et,wt,Pt,he,de){if(R===vi){p===!0&&(dt(i.BLEND),p=!1);return}if(p===!1&&(V(i.BLEND),p=!0),R!==Mu){if(R!==m||de!==I){if((S!==ys||b!==ys)&&(i.blendEquation(i.FUNC_ADD),S=ys,b=ys),de)switch(R){case cr:i.blendFuncSeparate(i.ONE,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case is:i.blendFunc(i.ONE,i.ONE);break;case Ul:i.blendFuncSeparate(i.ZERO,i.ONE_MINUS_SRC_COLOR,i.ZERO,i.ONE);break;case Nl:i.blendFuncSeparate(i.DST_COLOR,i.ONE_MINUS_SRC_ALPHA,i.ZERO,i.ONE);break;default:se("WebGLState: Invalid blending: ",R);break}else switch(R){case cr:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case is:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE,i.ONE,i.ONE);break;case Ul:se("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case Nl:se("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:se("WebGLState: Invalid blending: ",R);break}E=null,v=null,M=null,A=null,_.set(0,0,0),T=0,m=R,I=de}return}xt=xt||j,et=et||k,wt=wt||at,(j!==S||xt!==b)&&(i.blendEquationSeparate(Kt[j],Kt[xt]),S=j,b=xt),(k!==E||at!==v||et!==M||wt!==A)&&(i.blendFuncSeparate(it[k],it[at],it[et],it[wt]),E=k,v=at,M=et,A=wt),(Pt.equals(_)===!1||he!==T)&&(i.blendColor(Pt.r,Pt.g,Pt.b,he),_.copy(Pt),T=he),m=R,I=!1}function Y(R,j){R.side===fn?dt(i.CULL_FACE):V(i.CULL_FACE);let k=R.side===rn;j&&(k=!k),st(k),R.blending===cr&&R.transparent===!1?ut(vi):ut(R.blending,R.blendEquation,R.blendSrc,R.blendDst,R.blendEquationAlpha,R.blendSrcAlpha,R.blendDstAlpha,R.blendColor,R.blendAlpha,R.premultipliedAlpha),a.setFunc(R.depthFunc),a.setTest(R.depthTest),a.setMask(R.depthWrite),r.setMask(R.colorWrite);let at=R.stencilWrite;o.setTest(at),at&&(o.setMask(R.stencilWriteMask),o.setFunc(R.stencilFunc,R.stencilRef,R.stencilFuncMask),o.setOp(R.stencilFail,R.stencilZFail,R.stencilZPass)),St(R.polygonOffset,R.polygonOffsetFactor,R.polygonOffsetUnits),R.alphaToCoverage===!0?V(i.SAMPLE_ALPHA_TO_COVERAGE):dt(i.SAMPLE_ALPHA_TO_COVERAGE)}function st(R){L!==R&&(R?i.frontFace(i.CW):i.frontFace(i.CCW),L=R)}function vt(R){R!==xu?(V(i.CULL_FACE),R!==N&&(R===Dl?i.cullFace(i.BACK):R===_u?i.cullFace(i.FRONT):i.cullFace(i.FRONT_AND_BACK))):dt(i.CULL_FACE),N=R}function Vt(R){R!==B&&(J&&i.lineWidth(R),B=R)}function St(R,j,k){R?(V(i.POLYGON_OFFSET_FILL),(D!==j||O!==k)&&(D=j,O=k,a.getReversed()&&(j=-j),i.polygonOffset(j,k))):dt(i.POLYGON_OFFSET_FILL)}function Xt(R){R?V(i.SCISSOR_TEST):dt(i.SCISSOR_TEST)}function Qt(R){R===void 0&&(R=i.TEXTURE0+$-1),K!==R&&(i.activeTexture(R),K=R)}function F(R,j,k){k===void 0&&(K===null?k=i.TEXTURE0+$-1:k=K);let at=nt[k];at===void 0&&(at={type:void 0,texture:void 0},nt[k]=at),(at.type!==R||at.texture!==j)&&(K!==k&&(i.activeTexture(k),K=k),i.bindTexture(R,j||U[R]),at.type=R,at.texture=j)}function ye(){let R=nt[K];R!==void 0&&R.type!==void 0&&(i.bindTexture(R.type,null),R.type=void 0,R.texture=void 0)}function ne(){try{i.compressedTexImage2D(...arguments)}catch(R){se("WebGLState:",R)}}function C(){try{i.compressedTexImage3D(...arguments)}catch(R){se("WebGLState:",R)}}function y(){try{i.texSubImage2D(...arguments)}catch(R){se("WebGLState:",R)}}function H(){try{i.texSubImage3D(...arguments)}catch(R){se("WebGLState:",R)}}function X(){try{i.compressedTexSubImage2D(...arguments)}catch(R){se("WebGLState:",R)}}function tt(){try{i.compressedTexSubImage3D(...arguments)}catch(R){se("WebGLState:",R)}}function ct(){try{i.texStorage2D(...arguments)}catch(R){se("WebGLState:",R)}}function _t(){try{i.texStorage3D(...arguments)}catch(R){se("WebGLState:",R)}}function rt(){try{i.texImage2D(...arguments)}catch(R){se("WebGLState:",R)}}function ht(){try{i.texImage3D(...arguments)}catch(R){se("WebGLState:",R)}}function bt(R){return d[R]!==void 0?d[R]:i.getParameter(R)}function Wt(R,j){d[R]!==j&&(i.pixelStorei(R,j),d[R]=j)}function At(R){Ft.equals(R)===!1&&(i.scissor(R.x,R.y,R.z,R.w),Ft.copy(R))}function Tt(R){Dt.equals(R)===!1&&(i.viewport(R.x,R.y,R.z,R.w),Dt.copy(R))}function Bt(R,j){let k=l.get(j);k===void 0&&(k=new WeakMap,l.set(j,k));let at=k.get(R);at===void 0&&(at=i.getUniformBlockIndex(j,R.name),k.set(R,at))}function jt(R,j){let at=l.get(j).get(R);c.get(j)!==at&&(i.uniformBlockBinding(j,at,R.__bindingPointIndex),c.set(j,at))}function re(){i.disable(i.BLEND),i.disable(i.CULL_FACE),i.disable(i.DEPTH_TEST),i.disable(i.POLYGON_OFFSET_FILL),i.disable(i.SCISSOR_TEST),i.disable(i.STENCIL_TEST),i.disable(i.SAMPLE_ALPHA_TO_COVERAGE),i.blendEquation(i.FUNC_ADD),i.blendFunc(i.ONE,i.ZERO),i.blendFuncSeparate(i.ONE,i.ZERO,i.ONE,i.ZERO),i.blendColor(0,0,0,0),i.colorMask(!0,!0,!0,!0),i.clearColor(0,0,0,0),i.depthMask(!0),i.depthFunc(i.LESS),a.setReversed(!1),i.clearDepth(1),i.stencilMask(4294967295),i.stencilFunc(i.ALWAYS,0,4294967295),i.stencilOp(i.KEEP,i.KEEP,i.KEEP),i.clearStencil(0),i.cullFace(i.BACK),i.frontFace(i.CCW),i.polygonOffset(0,0),i.activeTexture(i.TEXTURE0),i.bindFramebuffer(i.FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.useProgram(null),i.lineWidth(1),i.scissor(0,0,i.canvas.width,i.canvas.height),i.viewport(0,0,i.canvas.width,i.canvas.height),i.pixelStorei(i.PACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,!1),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,i.BROWSER_DEFAULT_WEBGL),i.pixelStorei(i.PACK_ROW_LENGTH,0),i.pixelStorei(i.PACK_SKIP_PIXELS,0),i.pixelStorei(i.PACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_ROW_LENGTH,0),i.pixelStorei(i.UNPACK_IMAGE_HEIGHT,0),i.pixelStorei(i.UNPACK_SKIP_PIXELS,0),i.pixelStorei(i.UNPACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_SKIP_IMAGES,0),h={},d={},K=null,nt={},u={},f=new WeakMap,g=[],x=null,p=!1,m=null,S=null,E=null,v=null,b=null,M=null,A=null,_=new Ot(0,0,0),T=0,I=!1,L=null,N=null,B=null,D=null,O=null,Ft.set(0,0,i.canvas.width,i.canvas.height),Dt.set(0,0,i.canvas.width,i.canvas.height),r.reset(),a.reset(),o.reset()}return{buffers:{color:r,depth:a,stencil:o},enable:V,disable:dt,bindFramebuffer:Mt,drawBuffers:yt,useProgram:It,setBlending:ut,setMaterial:Y,setFlipSided:st,setCullFace:vt,setLineWidth:Vt,setPolygonOffset:St,setScissorTest:Xt,activeTexture:Qt,bindTexture:F,unbindTexture:ye,compressedTexImage2D:ne,compressedTexImage3D:C,texImage2D:rt,texImage3D:ht,pixelStorei:Wt,getParameter:bt,updateUBOMapping:Bt,uniformBlockBinding:jt,texStorage2D:ct,texStorage3D:_t,texSubImage2D:y,texSubImage3D:H,compressedTexSubImage2D:X,compressedTexSubImage3D:tt,scissor:At,viewport:Tt,reset:re}}function Ix(i,t,e,n,s,r,a){let o=t.has("WEBGL_multisampled_render_to_texture")?t.get("WEBGL_multisampled_render_to_texture"):null,c=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),l=new mt,h=new WeakMap,d=new Set,u,f=new WeakMap,g=!1;try{g=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function x(C,y){return g?new OffscreenCanvas(C,y):zr("canvas")}function p(C,y,H){let X=1,tt=ne(C);if((tt.width>H||tt.height>H)&&(X=H/Math.max(tt.width,tt.height)),X<1)if(typeof HTMLImageElement<"u"&&C instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&C instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&C instanceof ImageBitmap||typeof VideoFrame<"u"&&C instanceof VideoFrame){let ct=Math.floor(X*tt.width),_t=Math.floor(X*tt.height);u===void 0&&(u=x(ct,_t));let rt=y?x(ct,_t):u;return rt.width=ct,rt.height=_t,rt.getContext("2d").drawImage(C,0,0,ct,_t),ee("WebGLRenderer: Texture has been resized from ("+tt.width+"x"+tt.height+") to ("+ct+"x"+_t+")."),rt}else return"data"in C&&ee("WebGLRenderer: Image in DataTexture is too big ("+tt.width+"x"+tt.height+")."),C;return C}function m(C){return C.generateMipmaps}function S(C){i.generateMipmap(C)}function E(C){return C.isWebGLCubeRenderTarget?i.TEXTURE_CUBE_MAP:C.isWebGL3DRenderTarget?i.TEXTURE_3D:C.isWebGLArrayRenderTarget||C.isCompressedArrayTexture?i.TEXTURE_2D_ARRAY:i.TEXTURE_2D}function v(C,y,H,X,tt,ct=!1){if(C!==null){if(i[C]!==void 0)return i[C];ee("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+C+"'")}let _t;X&&(_t=t.get("EXT_texture_norm16"),_t||ee("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let rt=y;if(y===i.RED&&(H===i.FLOAT&&(rt=i.R32F),H===i.HALF_FLOAT&&(rt=i.R16F),H===i.UNSIGNED_BYTE&&(rt=i.R8),H===i.UNSIGNED_SHORT&&_t&&(rt=_t.R16_EXT),H===i.SHORT&&_t&&(rt=_t.R16_SNORM_EXT)),y===i.RED_INTEGER&&(H===i.UNSIGNED_BYTE&&(rt=i.R8UI),H===i.UNSIGNED_SHORT&&(rt=i.R16UI),H===i.UNSIGNED_INT&&(rt=i.R32UI),H===i.BYTE&&(rt=i.R8I),H===i.SHORT&&(rt=i.R16I),H===i.INT&&(rt=i.R32I)),y===i.RG&&(H===i.FLOAT&&(rt=i.RG32F),H===i.HALF_FLOAT&&(rt=i.RG16F),H===i.UNSIGNED_BYTE&&(rt=i.RG8),H===i.UNSIGNED_SHORT&&_t&&(rt=_t.RG16_EXT),H===i.SHORT&&_t&&(rt=_t.RG16_SNORM_EXT)),y===i.RG_INTEGER&&(H===i.UNSIGNED_BYTE&&(rt=i.RG8UI),H===i.UNSIGNED_SHORT&&(rt=i.RG16UI),H===i.UNSIGNED_INT&&(rt=i.RG32UI),H===i.BYTE&&(rt=i.RG8I),H===i.SHORT&&(rt=i.RG16I),H===i.INT&&(rt=i.RG32I)),y===i.RGB_INTEGER&&(H===i.UNSIGNED_BYTE&&(rt=i.RGB8UI),H===i.UNSIGNED_SHORT&&(rt=i.RGB16UI),H===i.UNSIGNED_INT&&(rt=i.RGB32UI),H===i.BYTE&&(rt=i.RGB8I),H===i.SHORT&&(rt=i.RGB16I),H===i.INT&&(rt=i.RGB32I)),y===i.RGBA_INTEGER&&(H===i.UNSIGNED_BYTE&&(rt=i.RGBA8UI),H===i.UNSIGNED_SHORT&&(rt=i.RGBA16UI),H===i.UNSIGNED_INT&&(rt=i.RGBA32UI),H===i.BYTE&&(rt=i.RGBA8I),H===i.SHORT&&(rt=i.RGBA16I),H===i.INT&&(rt=i.RGBA32I)),y===i.RGB&&(H===i.UNSIGNED_SHORT&&_t&&(rt=_t.RGB16_EXT),H===i.SHORT&&_t&&(rt=_t.RGB16_SNORM_EXT),H===i.UNSIGNED_INT_5_9_9_9_REV&&(rt=i.RGB9_E5),H===i.UNSIGNED_INT_10F_11F_11F_REV&&(rt=i.R11F_G11F_B10F)),y===i.RGBA){let ht=ct?Fr:Se.getTransfer(tt);H===i.FLOAT&&(rt=i.RGBA32F),H===i.HALF_FLOAT&&(rt=i.RGBA16F),H===i.UNSIGNED_BYTE&&(rt=ht===Ae?i.SRGB8_ALPHA8:i.RGBA8),H===i.UNSIGNED_SHORT&&_t&&(rt=_t.RGBA16_EXT),H===i.SHORT&&_t&&(rt=_t.RGBA16_SNORM_EXT),H===i.UNSIGNED_SHORT_4_4_4_4&&(rt=i.RGBA4),H===i.UNSIGNED_SHORT_5_5_5_1&&(rt=i.RGB5_A1)}return(rt===i.R16F||rt===i.R32F||rt===i.RG16F||rt===i.RG32F||rt===i.RGBA16F||rt===i.RGBA32F)&&t.get("EXT_color_buffer_float"),rt}function b(C,y){let H;return C?y===null||y===ai||y===hr?H=i.DEPTH24_STENCIL8:y===Gn?H=i.DEPTH32F_STENCIL8:y===lr&&(H=i.DEPTH24_STENCIL8,ee("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):y===null||y===ai||y===hr?H=i.DEPTH_COMPONENT24:y===Gn?H=i.DEPTH_COMPONENT32F:y===lr&&(H=i.DEPTH_COMPONENT16),H}function M(C,y){return m(C)===!0||C.isFramebufferTexture&&C.minFilter!==en&&C.minFilter!==$e?Math.log2(Math.max(y.width,y.height))+1:C.mipmaps!==void 0&&C.mipmaps.length>0?C.mipmaps.length:C.isCompressedTexture&&Array.isArray(C.image)?y.mipmaps.length:1}function A(C){let y=C.target;y.removeEventListener("dispose",A),T(y),y.isVideoTexture&&h.delete(y),y.isHTMLTexture&&d.delete(y)}function _(C){let y=C.target;y.removeEventListener("dispose",_),L(y)}function T(C){let y=n.get(C);if(y.__webglInit===void 0)return;let H=C.source,X=f.get(H);if(X){let tt=X[y.__cacheKey];tt.usedTimes--,tt.usedTimes===0&&I(C),Object.keys(X).length===0&&f.delete(H)}n.remove(C)}function I(C){let y=n.get(C);i.deleteTexture(y.__webglTexture);let H=C.source,X=f.get(H);delete X[y.__cacheKey],a.memory.textures--}function L(C){let y=n.get(C);if(C.depthTexture&&(C.depthTexture.dispose(),n.remove(C.depthTexture)),C.isWebGLCubeRenderTarget)for(let X=0;X<6;X++){if(Array.isArray(y.__webglFramebuffer[X]))for(let tt=0;tt<y.__webglFramebuffer[X].length;tt++)i.deleteFramebuffer(y.__webglFramebuffer[X][tt]);else i.deleteFramebuffer(y.__webglFramebuffer[X]);y.__webglDepthbuffer&&i.deleteRenderbuffer(y.__webglDepthbuffer[X])}else{if(Array.isArray(y.__webglFramebuffer))for(let X=0;X<y.__webglFramebuffer.length;X++)i.deleteFramebuffer(y.__webglFramebuffer[X]);else i.deleteFramebuffer(y.__webglFramebuffer);if(y.__webglDepthbuffer&&i.deleteRenderbuffer(y.__webglDepthbuffer),y.__webglMultisampledFramebuffer&&i.deleteFramebuffer(y.__webglMultisampledFramebuffer),y.__webglColorRenderbuffer)for(let X=0;X<y.__webglColorRenderbuffer.length;X++)y.__webglColorRenderbuffer[X]&&i.deleteRenderbuffer(y.__webglColorRenderbuffer[X]);y.__webglDepthRenderbuffer&&i.deleteRenderbuffer(y.__webglDepthRenderbuffer)}let H=C.textures;for(let X=0,tt=H.length;X<tt;X++){let ct=n.get(H[X]);ct.__webglTexture&&(i.deleteTexture(ct.__webglTexture),a.memory.textures--),n.remove(H[X])}n.remove(C)}let N=0;function B(){N=0}function D(){return N}function O(C){N=C}function $(){let C=N;return C>=s.maxTextures&&ee("WebGLTextures: Trying to use "+(C+1)+" texture units while this GPU supports only "+s.maxTextures),N+=1,C}function J(C){let y=[];return y.push(C.wrapS),y.push(C.wrapT),y.push(C.wrapR||0),y.push(C.magFilter),y.push(C.minFilter),y.push(C.anisotropy),y.push(C.internalFormat),y.push(C.format),y.push(C.type),y.push(C.generateMipmaps),y.push(C.premultiplyAlpha),y.push(C.flipY),y.push(C.unpackAlignment),y.push(C.colorSpace),y.join()}function W(C,y){let H=n.get(C);if(C.isVideoTexture&&F(C),C.isRenderTargetTexture===!1&&C.isExternalTexture!==!0&&C.version>0&&H.__version!==C.version){let X=C.image;if(X===null)ee("WebGLRenderer: Texture marked for update but no image data found.");else if(X.complete===!1)ee("WebGLRenderer: Texture marked for update but image is incomplete");else{dt(H,C,y);return}}else C.isExternalTexture&&(H.__webglTexture=C.sourceTexture?C.sourceTexture:null);e.bindTexture(i.TEXTURE_2D,H.__webglTexture,i.TEXTURE0+y)}function G(C,y){let H=n.get(C);if(C.isRenderTargetTexture===!1&&C.version>0&&H.__version!==C.version){dt(H,C,y);return}else C.isExternalTexture&&(H.__webglTexture=C.sourceTexture?C.sourceTexture:null);e.bindTexture(i.TEXTURE_2D_ARRAY,H.__webglTexture,i.TEXTURE0+y)}function K(C,y){let H=n.get(C);if(C.isRenderTargetTexture===!1&&C.version>0&&H.__version!==C.version){dt(H,C,y);return}e.bindTexture(i.TEXTURE_3D,H.__webglTexture,i.TEXTURE0+y)}function nt(C,y){let H=n.get(C);if(C.isCubeDepthTexture!==!0&&C.version>0&&H.__version!==C.version){Mt(H,C,y);return}e.bindTexture(i.TEXTURE_CUBE_MAP,H.__webglTexture,i.TEXTURE0+y)}let Et={[js]:i.REPEAT,[Hn]:i.CLAMP_TO_EDGE,[fo]:i.MIRRORED_REPEAT},pt={[en]:i.NEAREST,[Hu]:i.NEAREST_MIPMAP_NEAREST,[ga]:i.NEAREST_MIPMAP_LINEAR,[$e]:i.LINEAR,[Xo]:i.LINEAR_MIPMAP_NEAREST,[rs]:i.LINEAR_MIPMAP_LINEAR},Ft={[Xu]:i.NEVER,[$u]:i.ALWAYS,[qu]:i.LESS,[Pc]:i.LEQUAL,[Yu]:i.EQUAL,[Ic]:i.GEQUAL,[ju]:i.GREATER,[Zu]:i.NOTEQUAL};function Dt(C,y){if(y.type===Gn&&t.has("OES_texture_float_linear")===!1&&(y.magFilter===$e||y.magFilter===Xo||y.magFilter===ga||y.magFilter===rs||y.minFilter===$e||y.minFilter===Xo||y.minFilter===ga||y.minFilter===rs)&&ee("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),i.texParameteri(C,i.TEXTURE_WRAP_S,Et[y.wrapS]),i.texParameteri(C,i.TEXTURE_WRAP_T,Et[y.wrapT]),(C===i.TEXTURE_3D||C===i.TEXTURE_2D_ARRAY)&&i.texParameteri(C,i.TEXTURE_WRAP_R,Et[y.wrapR]),i.texParameteri(C,i.TEXTURE_MAG_FILTER,pt[y.magFilter]),i.texParameteri(C,i.TEXTURE_MIN_FILTER,pt[y.minFilter]),y.compareFunction&&(i.texParameteri(C,i.TEXTURE_COMPARE_MODE,i.COMPARE_REF_TO_TEXTURE),i.texParameteri(C,i.TEXTURE_COMPARE_FUNC,Ft[y.compareFunction])),t.has("EXT_texture_filter_anisotropic")===!0){if(y.magFilter===en||y.minFilter!==ga&&y.minFilter!==rs||y.type===Gn&&t.has("OES_texture_float_linear")===!1)return;if(y.anisotropy>1||n.get(y).__currentAnisotropy){let H=t.get("EXT_texture_filter_anisotropic");i.texParameterf(C,H.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(y.anisotropy,s.getMaxAnisotropy())),n.get(y).__currentAnisotropy=y.anisotropy}}}function ft(C,y){let H=!1;C.__webglInit===void 0&&(C.__webglInit=!0,y.addEventListener("dispose",A));let X=y.source,tt=f.get(X);tt===void 0&&(tt={},f.set(X,tt));let ct=J(y);if(ct!==C.__cacheKey){tt[ct]===void 0&&(tt[ct]={texture:i.createTexture(),usedTimes:0},a.memory.textures++,H=!0),tt[ct].usedTimes++;let _t=tt[C.__cacheKey];_t!==void 0&&(tt[C.__cacheKey].usedTimes--,_t.usedTimes===0&&I(y)),C.__cacheKey=ct,C.__webglTexture=tt[ct].texture}return H}function U(C,y,H){return Math.floor(Math.floor(C/H)/y)}function V(C,y,H,X){let ct=C.updateRanges;if(ct.length===0)e.texSubImage2D(i.TEXTURE_2D,0,0,0,y.width,y.height,H,X,y.data);else{ct.sort((Wt,At)=>Wt.start-At.start);let _t=0;for(let Wt=1;Wt<ct.length;Wt++){let At=ct[_t],Tt=ct[Wt],Bt=At.start+At.count,jt=U(Tt.start,y.width,4),re=U(At.start,y.width,4);Tt.start<=Bt+1&&jt===re&&U(Tt.start+Tt.count-1,y.width,4)===jt?At.count=Math.max(At.count,Tt.start+Tt.count-At.start):(++_t,ct[_t]=Tt)}ct.length=_t+1;let rt=e.getParameter(i.UNPACK_ROW_LENGTH),ht=e.getParameter(i.UNPACK_SKIP_PIXELS),bt=e.getParameter(i.UNPACK_SKIP_ROWS);e.pixelStorei(i.UNPACK_ROW_LENGTH,y.width);for(let Wt=0,At=ct.length;Wt<At;Wt++){let Tt=ct[Wt],Bt=Math.floor(Tt.start/4),jt=Math.ceil(Tt.count/4),re=Bt%y.width,R=Math.floor(Bt/y.width),j=jt,k=1;e.pixelStorei(i.UNPACK_SKIP_PIXELS,re),e.pixelStorei(i.UNPACK_SKIP_ROWS,R),e.texSubImage2D(i.TEXTURE_2D,0,re,R,j,k,H,X,y.data)}C.clearUpdateRanges(),e.pixelStorei(i.UNPACK_ROW_LENGTH,rt),e.pixelStorei(i.UNPACK_SKIP_PIXELS,ht),e.pixelStorei(i.UNPACK_SKIP_ROWS,bt)}}function dt(C,y,H){let X=i.TEXTURE_2D;(y.isDataArrayTexture||y.isCompressedArrayTexture)&&(X=i.TEXTURE_2D_ARRAY),y.isData3DTexture&&(X=i.TEXTURE_3D);let tt=ft(C,y),ct=y.source;e.bindTexture(X,C.__webglTexture,i.TEXTURE0+H);let _t=n.get(ct);if(ct.version!==_t.__version||tt===!0){if(e.activeTexture(i.TEXTURE0+H),(typeof ImageBitmap<"u"&&y.image instanceof ImageBitmap)===!1){let k=Se.getPrimaries(Se.workingColorSpace),at=y.colorSpace===Fi?null:Se.getPrimaries(y.colorSpace),xt=y.colorSpace===Fi||k===at?i.NONE:i.BROWSER_DEFAULT_WEBGL;e.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,y.flipY),e.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,y.premultiplyAlpha),e.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,xt)}e.pixelStorei(i.UNPACK_ALIGNMENT,y.unpackAlignment);let ht=p(y.image,!1,s.maxTextureSize);ht=ye(y,ht);let bt=r.convert(y.format,y.colorSpace),Wt=r.convert(y.type),At=v(y.internalFormat,bt,Wt,y.normalized,y.colorSpace,y.isVideoTexture);Dt(X,y);let Tt,Bt=y.mipmaps,jt=y.isVideoTexture!==!0,re=_t.__version===void 0||tt===!0,R=ct.dataReady,j=M(y,ht);if(y.isDepthTexture)At=b(y.format===as,y.type),re&&(jt?e.texStorage2D(i.TEXTURE_2D,1,At,ht.width,ht.height):e.texImage2D(i.TEXTURE_2D,0,At,ht.width,ht.height,0,bt,Wt,null));else if(y.isDataTexture)if(Bt.length>0){jt&&re&&e.texStorage2D(i.TEXTURE_2D,j,At,Bt[0].width,Bt[0].height);for(let k=0,at=Bt.length;k<at;k++)Tt=Bt[k],jt?R&&e.texSubImage2D(i.TEXTURE_2D,k,0,0,Tt.width,Tt.height,bt,Wt,Tt.data):e.texImage2D(i.TEXTURE_2D,k,At,Tt.width,Tt.height,0,bt,Wt,Tt.data);y.generateMipmaps=!1}else jt?(re&&e.texStorage2D(i.TEXTURE_2D,j,At,ht.width,ht.height),R&&V(y,ht,bt,Wt)):e.texImage2D(i.TEXTURE_2D,0,At,ht.width,ht.height,0,bt,Wt,ht.data);else if(y.isCompressedTexture)if(y.isCompressedArrayTexture){jt&&re&&e.texStorage3D(i.TEXTURE_2D_ARRAY,j,At,Bt[0].width,Bt[0].height,ht.depth);for(let k=0,at=Bt.length;k<at;k++)if(Tt=Bt[k],y.format!==Wn)if(bt!==null)if(jt){if(R)if(y.layerUpdates.size>0){let xt=rh(Tt.width,Tt.height,y.format,y.type);for(let et of y.layerUpdates){let wt=Tt.data.subarray(et*xt/Tt.data.BYTES_PER_ELEMENT,(et+1)*xt/Tt.data.BYTES_PER_ELEMENT);e.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,k,0,0,et,Tt.width,Tt.height,1,bt,wt)}}else e.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,k,0,0,0,Tt.width,Tt.height,ht.depth,bt,Tt.data)}else e.compressedTexImage3D(i.TEXTURE_2D_ARRAY,k,At,Tt.width,Tt.height,ht.depth,0,Tt.data,0,0);else ee("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else jt?R&&e.texSubImage3D(i.TEXTURE_2D_ARRAY,k,0,0,0,Tt.width,Tt.height,ht.depth,bt,Wt,Tt.data):e.texImage3D(i.TEXTURE_2D_ARRAY,k,At,Tt.width,Tt.height,ht.depth,0,bt,Wt,Tt.data);y.layerUpdates.size>0&&y.clearLayerUpdates()}else{jt&&re&&e.texStorage2D(i.TEXTURE_2D,j,At,Bt[0].width,Bt[0].height);for(let k=0,at=Bt.length;k<at;k++)Tt=Bt[k],y.format!==Wn?bt!==null?jt?R&&e.compressedTexSubImage2D(i.TEXTURE_2D,k,0,0,Tt.width,Tt.height,bt,Tt.data):e.compressedTexImage2D(i.TEXTURE_2D,k,At,Tt.width,Tt.height,0,Tt.data):ee("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):jt?R&&e.texSubImage2D(i.TEXTURE_2D,k,0,0,Tt.width,Tt.height,bt,Wt,Tt.data):e.texImage2D(i.TEXTURE_2D,k,At,Tt.width,Tt.height,0,bt,Wt,Tt.data)}else if(y.isDataArrayTexture)if(jt){if(re&&e.texStorage3D(i.TEXTURE_2D_ARRAY,j,At,ht.width,ht.height,ht.depth),R)if(y.layerUpdates.size>0){let k=rh(ht.width,ht.height,y.format,y.type);for(let at of y.layerUpdates){let xt=ht.data.subarray(at*k/ht.data.BYTES_PER_ELEMENT,(at+1)*k/ht.data.BYTES_PER_ELEMENT);e.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,at,ht.width,ht.height,1,bt,Wt,xt)}y.clearLayerUpdates()}else e.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,0,ht.width,ht.height,ht.depth,bt,Wt,ht.data)}else e.texImage3D(i.TEXTURE_2D_ARRAY,0,At,ht.width,ht.height,ht.depth,0,bt,Wt,ht.data);else if(y.isData3DTexture)jt?(re&&e.texStorage3D(i.TEXTURE_3D,j,At,ht.width,ht.height,ht.depth),R&&e.texSubImage3D(i.TEXTURE_3D,0,0,0,0,ht.width,ht.height,ht.depth,bt,Wt,ht.data)):e.texImage3D(i.TEXTURE_3D,0,At,ht.width,ht.height,ht.depth,0,bt,Wt,ht.data);else if(y.isFramebufferTexture){if(re)if(jt)e.texStorage2D(i.TEXTURE_2D,j,At,ht.width,ht.height);else{let k=ht.width,at=ht.height;for(let xt=0;xt<j;xt++)e.texImage2D(i.TEXTURE_2D,xt,At,k,at,0,bt,Wt,null),k>>=1,at>>=1}}else if(y.isHTMLTexture){if("texElementImage2D"in i){let k=i.canvas;if(k.hasAttribute("layoutsubtree")||k.setAttribute("layoutsubtree","true"),ht.parentNode!==k){k.appendChild(ht),d.add(y),k.onpaint=at=>{let xt=at.changedElements;for(let et of d)xt.includes(et.image)&&(et.needsUpdate=!0)},k.requestPaint();return}if(i.texElementImage2D.length===3)i.texElementImage2D(i.TEXTURE_2D,i.RGBA8,ht);else{let xt=i.RGBA,et=i.RGBA,wt=i.UNSIGNED_BYTE;i.texElementImage2D(i.TEXTURE_2D,0,xt,et,wt,ht)}i.texParameteri(i.TEXTURE_2D,i.TEXTURE_MIN_FILTER,i.LINEAR),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_S,i.CLAMP_TO_EDGE),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_T,i.CLAMP_TO_EDGE)}}else if(Bt.length>0){if(jt&&re){let k=ne(Bt[0]);e.texStorage2D(i.TEXTURE_2D,j,At,k.width,k.height)}for(let k=0,at=Bt.length;k<at;k++)Tt=Bt[k],jt?R&&e.texSubImage2D(i.TEXTURE_2D,k,0,0,bt,Wt,Tt):e.texImage2D(i.TEXTURE_2D,k,At,bt,Wt,Tt);y.generateMipmaps=!1}else if(jt){if(re){let k=ne(ht);e.texStorage2D(i.TEXTURE_2D,j,At,k.width,k.height)}R&&e.texSubImage2D(i.TEXTURE_2D,0,0,0,bt,Wt,ht)}else e.texImage2D(i.TEXTURE_2D,0,At,bt,Wt,ht);m(y)&&S(X),_t.__version=ct.version,y.onUpdate&&y.onUpdate(y)}C.__version=y.version}function Mt(C,y,H){if(y.image.length!==6)return;let X=ft(C,y),tt=y.source;e.bindTexture(i.TEXTURE_CUBE_MAP,C.__webglTexture,i.TEXTURE0+H);let ct=n.get(tt);if(tt.version!==ct.__version||X===!0){e.activeTexture(i.TEXTURE0+H);let _t=Se.getPrimaries(Se.workingColorSpace),rt=y.colorSpace===Fi?null:Se.getPrimaries(y.colorSpace),ht=y.colorSpace===Fi||_t===rt?i.NONE:i.BROWSER_DEFAULT_WEBGL;e.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,y.flipY),e.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,y.premultiplyAlpha),e.pixelStorei(i.UNPACK_ALIGNMENT,y.unpackAlignment),e.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,ht);let bt=y.isCompressedTexture||y.image[0].isCompressedTexture,Wt=y.image[0]&&y.image[0].isDataTexture,At=[];for(let et=0;et<6;et++)!bt&&!Wt?At[et]=p(y.image[et],!0,s.maxCubemapSize):At[et]=Wt?y.image[et].image:y.image[et],At[et]=ye(y,At[et]);let Tt=At[0],Bt=r.convert(y.format,y.colorSpace),jt=r.convert(y.type),re=v(y.internalFormat,Bt,jt,y.normalized,y.colorSpace),R=y.isVideoTexture!==!0,j=ct.__version===void 0||X===!0,k=tt.dataReady,at=M(y,Tt);Dt(i.TEXTURE_CUBE_MAP,y);let xt;if(bt){R&&j&&e.texStorage2D(i.TEXTURE_CUBE_MAP,at,re,Tt.width,Tt.height);for(let et=0;et<6;et++){xt=At[et].mipmaps;for(let wt=0;wt<xt.length;wt++){let Pt=xt[wt];y.format!==Wn?Bt!==null?R?k&&e.compressedTexSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,wt,0,0,Pt.width,Pt.height,Bt,Pt.data):e.compressedTexImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,wt,re,Pt.width,Pt.height,0,Pt.data):ee("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):R?k&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,wt,0,0,Pt.width,Pt.height,Bt,jt,Pt.data):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,wt,re,Pt.width,Pt.height,0,Bt,jt,Pt.data)}}}else{if(xt=y.mipmaps,R&&j){xt.length>0&&at++;let et=ne(At[0]);e.texStorage2D(i.TEXTURE_CUBE_MAP,at,re,et.width,et.height)}for(let et=0;et<6;et++)if(Wt){R?k&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,0,0,0,At[et].width,At[et].height,Bt,jt,At[et].data):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,0,re,At[et].width,At[et].height,0,Bt,jt,At[et].data);for(let wt=0;wt<xt.length;wt++){let he=xt[wt].image[et].image;R?k&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,wt+1,0,0,he.width,he.height,Bt,jt,he.data):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,wt+1,re,he.width,he.height,0,Bt,jt,he.data)}}else{R?k&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,0,0,0,Bt,jt,At[et]):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,0,re,Bt,jt,At[et]);for(let wt=0;wt<xt.length;wt++){let Pt=xt[wt];R?k&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,wt+1,0,0,Bt,jt,Pt.image[et]):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+et,wt+1,re,Bt,jt,Pt.image[et])}}}m(y)&&S(i.TEXTURE_CUBE_MAP),ct.__version=tt.version,y.onUpdate&&y.onUpdate(y)}C.__version=y.version}function yt(C,y,H,X,tt,ct){let _t=r.convert(H.format,H.colorSpace),rt=r.convert(H.type),ht=v(H.internalFormat,_t,rt,H.normalized,H.colorSpace),bt=n.get(y),Wt=n.get(H);if(Wt.__renderTarget=y,!bt.__hasExternalTextures){let At=Math.max(1,y.width>>ct),Tt=Math.max(1,y.height>>ct);tt===i.TEXTURE_3D||tt===i.TEXTURE_2D_ARRAY?e.texImage3D(tt,ct,ht,At,Tt,y.depth,0,_t,rt,null):e.texImage2D(tt,ct,ht,At,Tt,0,_t,rt,null)}e.bindFramebuffer(i.FRAMEBUFFER,C),Qt(y)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,X,tt,Wt.__webglTexture,0,Xt(y)):(tt===i.TEXTURE_2D||tt>=i.TEXTURE_CUBE_MAP_POSITIVE_X&&tt<=i.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&i.framebufferTexture2D(i.FRAMEBUFFER,X,tt,Wt.__webglTexture,ct),e.bindFramebuffer(i.FRAMEBUFFER,null)}function It(C,y,H){if(i.bindRenderbuffer(i.RENDERBUFFER,C),y.depthBuffer){let X=y.depthTexture,tt=X&&X.isDepthTexture?X.type:null,ct=b(y.stencilBuffer,tt),_t=y.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;Qt(y)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,Xt(y),ct,y.width,y.height):H?i.renderbufferStorageMultisample(i.RENDERBUFFER,Xt(y),ct,y.width,y.height):i.renderbufferStorage(i.RENDERBUFFER,ct,y.width,y.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,_t,i.RENDERBUFFER,C)}else{let X=y.textures;for(let tt=0;tt<X.length;tt++){let ct=X[tt],_t=r.convert(ct.format,ct.colorSpace),rt=r.convert(ct.type),ht=v(ct.internalFormat,_t,rt,ct.normalized,ct.colorSpace);Qt(y)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,Xt(y),ht,y.width,y.height):H?i.renderbufferStorageMultisample(i.RENDERBUFFER,Xt(y),ht,y.width,y.height):i.renderbufferStorage(i.RENDERBUFFER,ht,y.width,y.height)}}i.bindRenderbuffer(i.RENDERBUFFER,null)}function Kt(C,y,H){let X=y.isWebGLCubeRenderTarget===!0;if(e.bindFramebuffer(i.FRAMEBUFFER,C),!(y.depthTexture&&y.depthTexture.isDepthTexture))throw new Error("THREE.WebGLTextures: renderTarget.depthTexture must be an instance of THREE.DepthTexture.");let tt=n.get(y.depthTexture);if(tt.__renderTarget=y,(!tt.__webglTexture||y.depthTexture.image.width!==y.width||y.depthTexture.image.height!==y.height)&&(y.depthTexture.image.width=y.width,y.depthTexture.image.height=y.height,y.depthTexture.needsUpdate=!0),X){if(tt.__webglInit===void 0&&(tt.__webglInit=!0,y.depthTexture.addEventListener("dispose",A)),tt.__webglTexture===void 0){tt.__webglTexture=i.createTexture(),e.bindTexture(i.TEXTURE_CUBE_MAP,tt.__webglTexture),Dt(i.TEXTURE_CUBE_MAP,y.depthTexture);let bt=r.convert(y.depthTexture.format),Wt=r.convert(y.depthTexture.type),At;y.depthTexture.format===di?At=i.DEPTH_COMPONENT24:y.depthTexture.format===as&&(At=i.DEPTH24_STENCIL8);for(let Tt=0;Tt<6;Tt++)i.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Tt,0,At,y.width,y.height,0,bt,Wt,null)}}else W(y.depthTexture,0);let ct=tt.__webglTexture,_t=Xt(y),rt=X?i.TEXTURE_CUBE_MAP_POSITIVE_X+H:i.TEXTURE_2D,ht=y.depthTexture.format===as?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;if(y.depthTexture.format===di)Qt(y)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,ht,rt,ct,0,_t):i.framebufferTexture2D(i.FRAMEBUFFER,ht,rt,ct,0);else if(y.depthTexture.format===as)Qt(y)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,ht,rt,ct,0,_t):i.framebufferTexture2D(i.FRAMEBUFFER,ht,rt,ct,0);else throw new Error("THREE.WebGLTextures: Unknown depthTexture format.")}function it(C){let y=n.get(C),H=C.isWebGLCubeRenderTarget===!0;if(y.__boundDepthTexture!==C.depthTexture){let X=C.depthTexture;if(y.__depthDisposeCallback&&y.__depthDisposeCallback(),X){let tt=()=>{delete y.__boundDepthTexture,delete y.__depthDisposeCallback,X.removeEventListener("dispose",tt)};X.addEventListener("dispose",tt),y.__depthDisposeCallback=tt}y.__boundDepthTexture=X}if(C.depthTexture&&!y.__autoAllocateDepthBuffer)if(H)for(let X=0;X<6;X++)Kt(y.__webglFramebuffer[X],C,X);else{let X=C.texture.mipmaps;X&&X.length>0?Kt(y.__webglFramebuffer[0],C,0):Kt(y.__webglFramebuffer,C,0)}else if(H){y.__webglDepthbuffer=[];for(let X=0;X<6;X++)if(e.bindFramebuffer(i.FRAMEBUFFER,y.__webglFramebuffer[X]),y.__webglDepthbuffer[X]===void 0)y.__webglDepthbuffer[X]=i.createRenderbuffer(),It(y.__webglDepthbuffer[X],C,!1);else{let tt=C.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,ct=y.__webglDepthbuffer[X];i.bindRenderbuffer(i.RENDERBUFFER,ct),i.framebufferRenderbuffer(i.FRAMEBUFFER,tt,i.RENDERBUFFER,ct)}}else{let X=C.texture.mipmaps;if(X&&X.length>0?e.bindFramebuffer(i.FRAMEBUFFER,y.__webglFramebuffer[0]):e.bindFramebuffer(i.FRAMEBUFFER,y.__webglFramebuffer),y.__webglDepthbuffer===void 0)y.__webglDepthbuffer=i.createRenderbuffer(),It(y.__webglDepthbuffer,C,!1);else{let tt=C.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,ct=y.__webglDepthbuffer;i.bindRenderbuffer(i.RENDERBUFFER,ct),i.framebufferRenderbuffer(i.FRAMEBUFFER,tt,i.RENDERBUFFER,ct)}}e.bindFramebuffer(i.FRAMEBUFFER,null)}function ut(C,y,H){let X=n.get(C);y!==void 0&&yt(X.__webglFramebuffer,C,C.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,0),H!==void 0&&it(C)}function Y(C){let y=C.texture,H=n.get(C),X=n.get(y);C.addEventListener("dispose",_);let tt=C.textures,ct=C.isWebGLCubeRenderTarget===!0,_t=tt.length>1;if(_t||(X.__webglTexture===void 0&&(X.__webglTexture=i.createTexture()),X.__version=y.version,a.memory.textures++),ct){H.__webglFramebuffer=[];for(let rt=0;rt<6;rt++)if(y.mipmaps&&y.mipmaps.length>0){H.__webglFramebuffer[rt]=[];for(let ht=0;ht<y.mipmaps.length;ht++)H.__webglFramebuffer[rt][ht]=i.createFramebuffer()}else H.__webglFramebuffer[rt]=i.createFramebuffer()}else{if(y.mipmaps&&y.mipmaps.length>0){H.__webglFramebuffer=[];for(let rt=0;rt<y.mipmaps.length;rt++)H.__webglFramebuffer[rt]=i.createFramebuffer()}else H.__webglFramebuffer=i.createFramebuffer();if(_t)for(let rt=0,ht=tt.length;rt<ht;rt++){let bt=n.get(tt[rt]);bt.__webglTexture===void 0&&(bt.__webglTexture=i.createTexture(),a.memory.textures++)}if(C.samples>0&&Qt(C)===!1){H.__webglMultisampledFramebuffer=i.createFramebuffer(),H.__webglColorRenderbuffer=[],e.bindFramebuffer(i.FRAMEBUFFER,H.__webglMultisampledFramebuffer);for(let rt=0;rt<tt.length;rt++){let ht=tt[rt];H.__webglColorRenderbuffer[rt]=i.createRenderbuffer(),i.bindRenderbuffer(i.RENDERBUFFER,H.__webglColorRenderbuffer[rt]);let bt=r.convert(ht.format,ht.colorSpace),Wt=r.convert(ht.type),At=v(ht.internalFormat,bt,Wt,ht.normalized,ht.colorSpace,C.isXRRenderTarget===!0),Tt=Xt(C);i.renderbufferStorageMultisample(i.RENDERBUFFER,Tt,At,C.width,C.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+rt,i.RENDERBUFFER,H.__webglColorRenderbuffer[rt])}i.bindRenderbuffer(i.RENDERBUFFER,null),C.depthBuffer&&(H.__webglDepthRenderbuffer=i.createRenderbuffer(),It(H.__webglDepthRenderbuffer,C,!0)),e.bindFramebuffer(i.FRAMEBUFFER,null)}}if(ct){e.bindTexture(i.TEXTURE_CUBE_MAP,X.__webglTexture),Dt(i.TEXTURE_CUBE_MAP,y);for(let rt=0;rt<6;rt++)if(y.mipmaps&&y.mipmaps.length>0)for(let ht=0;ht<y.mipmaps.length;ht++)yt(H.__webglFramebuffer[rt][ht],C,y,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+rt,ht);else yt(H.__webglFramebuffer[rt],C,y,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+rt,0);m(y)&&S(i.TEXTURE_CUBE_MAP),e.unbindTexture()}else if(_t){for(let rt=0,ht=tt.length;rt<ht;rt++){let bt=tt[rt],Wt=n.get(bt),At=i.TEXTURE_2D;(C.isWebGL3DRenderTarget||C.isWebGLArrayRenderTarget)&&(At=C.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),e.bindTexture(At,Wt.__webglTexture),Dt(At,bt),yt(H.__webglFramebuffer,C,bt,i.COLOR_ATTACHMENT0+rt,At,0),m(bt)&&S(At)}e.unbindTexture()}else{let rt=i.TEXTURE_2D;if((C.isWebGL3DRenderTarget||C.isWebGLArrayRenderTarget)&&(rt=C.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),e.bindTexture(rt,X.__webglTexture),Dt(rt,y),y.mipmaps&&y.mipmaps.length>0)for(let ht=0;ht<y.mipmaps.length;ht++)yt(H.__webglFramebuffer[ht],C,y,i.COLOR_ATTACHMENT0,rt,ht);else yt(H.__webglFramebuffer,C,y,i.COLOR_ATTACHMENT0,rt,0);m(y)&&S(rt),e.unbindTexture()}C.depthBuffer&&it(C)}function st(C){let y=C.textures;for(let H=0,X=y.length;H<X;H++){let tt=y[H];if(m(tt)){let ct=E(C),_t=n.get(tt).__webglTexture;e.bindTexture(ct,_t),S(ct),e.unbindTexture()}}}let vt=[],Vt=[];function St(C){if(C.samples>0){if(Qt(C)===!1){let y=C.textures,H=C.width,X=C.height,tt=i.COLOR_BUFFER_BIT,ct=C.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,_t=n.get(C),rt=y.length>1;if(rt)for(let bt=0;bt<y.length;bt++)e.bindFramebuffer(i.FRAMEBUFFER,_t.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+bt,i.RENDERBUFFER,null),e.bindFramebuffer(i.FRAMEBUFFER,_t.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+bt,i.TEXTURE_2D,null,0);e.bindFramebuffer(i.READ_FRAMEBUFFER,_t.__webglMultisampledFramebuffer);let ht=C.texture.mipmaps;ht&&ht.length>0?e.bindFramebuffer(i.DRAW_FRAMEBUFFER,_t.__webglFramebuffer[0]):e.bindFramebuffer(i.DRAW_FRAMEBUFFER,_t.__webglFramebuffer);for(let bt=0;bt<y.length;bt++){if(C.resolveDepthBuffer&&(C.depthBuffer&&(tt|=i.DEPTH_BUFFER_BIT),C.stencilBuffer&&C.resolveStencilBuffer&&(tt|=i.STENCIL_BUFFER_BIT)),rt){i.framebufferRenderbuffer(i.READ_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.RENDERBUFFER,_t.__webglColorRenderbuffer[bt]);let Wt=n.get(y[bt]).__webglTexture;i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,Wt,0)}i.blitFramebuffer(0,0,H,X,0,0,H,X,tt,i.NEAREST),c===!0&&(vt.length=0,Vt.length=0,vt.push(i.COLOR_ATTACHMENT0+bt),C.depthBuffer&&C.storeMultisampledDepthBuffer===!1&&(vt.push(ct),Vt.push(ct),i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,Vt)),i.invalidateFramebuffer(i.READ_FRAMEBUFFER,vt))}if(e.bindFramebuffer(i.READ_FRAMEBUFFER,null),e.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),rt)for(let bt=0;bt<y.length;bt++){e.bindFramebuffer(i.FRAMEBUFFER,_t.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+bt,i.RENDERBUFFER,_t.__webglColorRenderbuffer[bt]);let Wt=n.get(y[bt]).__webglTexture;e.bindFramebuffer(i.FRAMEBUFFER,_t.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+bt,i.TEXTURE_2D,Wt,0)}e.bindFramebuffer(i.DRAW_FRAMEBUFFER,_t.__webglMultisampledFramebuffer)}else if(C.depthBuffer&&C.storeMultisampledDepthBuffer===!1&&c){let y=C.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,[y])}}}function Xt(C){return Math.min(s.maxSamples,C.samples)}function Qt(C){let y=n.get(C);return C.samples>0&&t.has("WEBGL_multisampled_render_to_texture")===!0&&y.__useRenderToTexture!==!1}function F(C){let y=a.render.frame;h.get(C)!==y&&(h.set(C,y),C.update())}function ye(C,y){let H=C.colorSpace,X=C.format,tt=C.type;return C.isCompressedTexture===!0||C.isVideoTexture===!0||H!==Nr&&H!==Fi&&(Se.getTransfer(H)===Ae?(X!==Wn||tt!==Cn)&&ee("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):se("WebGLTextures: Unsupported texture color space:",H)),y}function ne(C){return typeof HTMLImageElement<"u"&&C instanceof HTMLImageElement?(l.width=C.naturalWidth||C.width,l.height=C.naturalHeight||C.height):typeof VideoFrame<"u"&&C instanceof VideoFrame?(l.width=C.displayWidth,l.height=C.displayHeight):(l.width=C.width,l.height=C.height),l}this.allocateTextureUnit=$,this.resetTextureUnits=B,this.getTextureUnits=D,this.setTextureUnits=O,this.setTexture2D=W,this.setTexture2DArray=G,this.setTexture3D=K,this.setTextureCube=nt,this.rebindTextures=ut,this.setupRenderTarget=Y,this.updateRenderTargetMipmap=st,this.updateMultisampleRenderTarget=St,this.setupDepthRenderbuffer=it,this.setupFrameBufferTexture=yt,this.useMultisampledRTT=Qt,this.isReversedDepthBuffer=function(){return e.buffers.depth.getReversed()}}function Lx(i,t){function e(n,s=Fi){let r,a=Se.getTransfer(s);if(n===Cn)return i.UNSIGNED_BYTE;if(n===Yo)return i.UNSIGNED_SHORT_4_4_4_4;if(n===jo)return i.UNSIGNED_SHORT_5_5_5_1;if(n===jl)return i.UNSIGNED_INT_5_9_9_9_REV;if(n===Zl)return i.UNSIGNED_INT_10F_11F_11F_REV;if(n===ql)return i.BYTE;if(n===Yl)return i.SHORT;if(n===lr)return i.UNSIGNED_SHORT;if(n===qo)return i.INT;if(n===ai)return i.UNSIGNED_INT;if(n===Gn)return i.FLOAT;if(n===On)return i.HALF_FLOAT;if(n===$l)return i.ALPHA;if(n===Jl)return i.RGB;if(n===Wn)return i.RGBA;if(n===di)return i.DEPTH_COMPONENT;if(n===as)return i.DEPTH_STENCIL;if(n===Zo)return i.RED;if(n===$o)return i.RED_INTEGER;if(n===xi)return i.RG;if(n===Jo)return i.RG_INTEGER;if(n===Ko)return i.RGBA_INTEGER;if(n===va||n===xa||n===_a||n===ya)if(a===Ae)if(r=t.get("WEBGL_compressed_texture_s3tc_srgb"),r!==null){if(n===va)return r.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(n===xa)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(n===_a)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(n===ya)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(r=t.get("WEBGL_compressed_texture_s3tc"),r!==null){if(n===va)return r.COMPRESSED_RGB_S3TC_DXT1_EXT;if(n===xa)return r.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(n===_a)return r.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(n===ya)return r.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(n===Qo||n===tc||n===ec||n===nc)if(r=t.get("WEBGL_compressed_texture_pvrtc"),r!==null){if(n===Qo)return r.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(n===tc)return r.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(n===ec)return r.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(n===nc)return r.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(n===ic||n===sc||n===rc||n===ac||n===oc||n===Ma||n===cc)if(r=t.get("WEBGL_compressed_texture_etc"),r!==null){if(n===ic||n===sc)return a===Ae?r.COMPRESSED_SRGB8_ETC2:r.COMPRESSED_RGB8_ETC2;if(n===rc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:r.COMPRESSED_RGBA8_ETC2_EAC;if(n===ac)return r.COMPRESSED_R11_EAC;if(n===oc)return r.COMPRESSED_SIGNED_R11_EAC;if(n===Ma)return r.COMPRESSED_RG11_EAC;if(n===cc)return r.COMPRESSED_SIGNED_RG11_EAC}else return null;if(n===lc||n===hc||n===uc||n===dc||n===fc||n===pc||n===mc||n===gc||n===vc||n===xc||n===_c||n===yc||n===Mc||n===Sc)if(r=t.get("WEBGL_compressed_texture_astc"),r!==null){if(n===lc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:r.COMPRESSED_RGBA_ASTC_4x4_KHR;if(n===hc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:r.COMPRESSED_RGBA_ASTC_5x4_KHR;if(n===uc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:r.COMPRESSED_RGBA_ASTC_5x5_KHR;if(n===dc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:r.COMPRESSED_RGBA_ASTC_6x5_KHR;if(n===fc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:r.COMPRESSED_RGBA_ASTC_6x6_KHR;if(n===pc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:r.COMPRESSED_RGBA_ASTC_8x5_KHR;if(n===mc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:r.COMPRESSED_RGBA_ASTC_8x6_KHR;if(n===gc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:r.COMPRESSED_RGBA_ASTC_8x8_KHR;if(n===vc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:r.COMPRESSED_RGBA_ASTC_10x5_KHR;if(n===xc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:r.COMPRESSED_RGBA_ASTC_10x6_KHR;if(n===_c)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:r.COMPRESSED_RGBA_ASTC_10x8_KHR;if(n===yc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:r.COMPRESSED_RGBA_ASTC_10x10_KHR;if(n===Mc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:r.COMPRESSED_RGBA_ASTC_12x10_KHR;if(n===Sc)return a===Ae?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:r.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(n===bc||n===Ec||n===wc)if(r=t.get("EXT_texture_compression_bptc"),r!==null){if(n===bc)return a===Ae?r.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:r.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(n===Ec)return r.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(n===wc)return r.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(n===Tc||n===Ac||n===Sa||n===Rc)if(r=t.get("EXT_texture_compression_rgtc"),r!==null){if(n===Tc)return r.COMPRESSED_RED_RGTC1_EXT;if(n===Ac)return r.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(n===Sa)return r.COMPRESSED_RED_GREEN_RGTC2_EXT;if(n===Rc)return r.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return n===hr?i.UNSIGNED_INT_24_8:i[n]!==void 0?i[n]:null}return{convert:e}}var Dx=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,Ux=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`,Eh=class{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(t,e){if(this.texture===null){let n=new Zr(t.texture);(t.depthNear!==e.depthNear||t.depthFar!==e.depthFar)&&(this.depthNear=t.depthNear,this.depthFar=t.depthFar),this.texture=n}}getMesh(t){if(this.texture!==null&&this.mesh===null){let e=t.cameras[0].viewport,n=new Ue({vertexShader:Dx,fragmentShader:Ux,uniforms:{depthColor:{value:this.texture},depthWidth:{value:e.z},depthHeight:{value:e.w}}});this.mesh=new ot(new Xe(20,20),n)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}},wh=class extends fi{constructor(t,e){super();let n=this,s=null,r=1,a=null,o="local-floor",c=1,l=null,h=null,d=null,u=null,f=null,g=null,x=typeof XRWebGLBinding<"u",p=new Eh,m={},S=e.getContextAttributes(),E=null,v=null,b=[],M=[],A=new mt,_=null,T=null,I=new Ze;I.viewport=new xe;let L=new Ze;L.viewport=new xe;let N=[I,L],B=new Ho,D=null,O=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(U){let V=b[U];return V===void 0&&(V=new Qs,b[U]=V),V.getTargetRaySpace()},this.getControllerGrip=function(U){let V=b[U];return V===void 0&&(V=new Qs,b[U]=V),V.getGripSpace()},this.getHand=function(U){let V=b[U];return V===void 0&&(V=new Qs,b[U]=V),V.getHandSpace()};function $(U){let V=M.indexOf(U.inputSource);if(V===-1)return;let dt=b[V];dt!==void 0&&(dt.update(U.inputSource,U.frame,l||a),dt.dispatchEvent({type:U.type,data:U.inputSource}))}function J(){s.removeEventListener("select",$),s.removeEventListener("selectstart",$),s.removeEventListener("selectend",$),s.removeEventListener("squeeze",$),s.removeEventListener("squeezestart",$),s.removeEventListener("squeezeend",$),s.removeEventListener("end",J),s.removeEventListener("inputsourceschange",W);for(let U=0;U<b.length;U++){let V=M[U];V!==null&&(M[U]=null,b[U].disconnect(V))}D=null,O=null,p.reset();for(let U in m)delete m[U];if(t.setRenderTarget(E),f=null,u=null,d=null,s=null,v=null,ft.stop(),n.isPresenting=!1,t.setPixelRatio(_),t.setSize(A.width,A.height,!1),T!==null){let U=T.camera;U.fov=T.fov,U.zoom=T.zoom,U.updateProjectionMatrix(),T=null}n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(U){r=U,n.isPresenting===!0&&ee("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(U){o=U,n.isPresenting===!0&&ee("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return l||a},this.setReferenceSpace=function(U){l=U},this.getBaseLayer=function(){return u!==null?u:f},this.getBinding=function(){return d===null&&x&&(d=new XRWebGLBinding(s,e)),d},this.getFrame=function(){return g},this.getSession=function(){return s},this.setSession=async function(U){if(s=U,s!==null){if(E=t.getRenderTarget(),s.addEventListener("select",$),s.addEventListener("selectstart",$),s.addEventListener("selectend",$),s.addEventListener("squeeze",$),s.addEventListener("squeezestart",$),s.addEventListener("squeezeend",$),s.addEventListener("end",J),s.addEventListener("inputsourceschange",W),S.xrCompatible!==!0&&await e.makeXRCompatible(),_=t.getPixelRatio(),t.getSize(A),x&&"createProjectionLayer"in XRWebGLBinding.prototype){let dt=null,Mt=null,yt=null;S.depth&&(yt=S.stencil?e.DEPTH24_STENCIL8:e.DEPTH_COMPONENT24,dt=S.stencil?as:di,Mt=S.stencil?hr:ai);let It={colorFormat:e.RGBA8,depthFormat:yt,scaleFactor:r};d=this.getBinding(),u=d.createProjectionLayer(It),s.updateRenderState({layers:[u]}),t.setPixelRatio(1),t.setSize(u.textureWidth,u.textureHeight,!1),v=new An(u.textureWidth,u.textureHeight,{format:Wn,type:Cn,depthTexture:new ji(u.textureWidth,u.textureHeight,Mt,void 0,void 0,void 0,void 0,void 0,void 0,dt),stencilBuffer:S.stencil,colorSpace:t.outputColorSpace,samples:S.antialias?4:0,resolveDepthBuffer:u.ignoreDepthValues===!1,resolveStencilBuffer:u.ignoreDepthValues===!1,storeMultisampledDepthBuffer:u.ignoreDepthValues===!1,storeMultisampledStencilBuffer:u.ignoreDepthValues===!1})}else{let dt={antialias:S.antialias,alpha:!0,depth:S.depth,stencil:S.stencil,framebufferScaleFactor:r};f=new XRWebGLLayer(s,e,dt),s.updateRenderState({baseLayer:f}),t.setPixelRatio(1),t.setSize(f.framebufferWidth,f.framebufferHeight,!1),v=new An(f.framebufferWidth,f.framebufferHeight,{format:Wn,type:Cn,colorSpace:t.outputColorSpace,stencilBuffer:S.stencil,resolveDepthBuffer:f.ignoreDepthValues===!1,resolveStencilBuffer:f.ignoreDepthValues===!1,storeMultisampledDepthBuffer:f.ignoreDepthValues===!1,storeMultisampledStencilBuffer:f.ignoreDepthValues===!1})}v.isXRRenderTarget=!0,this.setFoveation(c),l=null,a=await s.requestReferenceSpace(o),ft.setContext(s),ft.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(s!==null)return s.environmentBlendMode},this.getDepthTexture=function(){return p.getDepthTexture()};function W(U){for(let V=0;V<U.removed.length;V++){let dt=U.removed[V],Mt=M.indexOf(dt);Mt>=0&&(M[Mt]=null,b[Mt].disconnect(dt))}for(let V=0;V<U.added.length;V++){let dt=U.added[V],Mt=M.indexOf(dt);if(Mt===-1){for(let It=0;It<b.length;It++)if(It>=M.length){M.push(dt),Mt=It;break}else if(M[It]===null){M[It]=dt,Mt=It;break}if(Mt===-1)break}let yt=b[Mt];yt&&yt.connect(dt)}}let G=new P,K=new P;function nt(U,V,dt){G.setFromMatrixPosition(V.matrixWorld),K.setFromMatrixPosition(dt.matrixWorld);let Mt=G.distanceTo(K),yt=V.projectionMatrix.elements,It=dt.projectionMatrix.elements,Kt=yt[14]/(yt[10]-1),it=yt[14]/(yt[10]+1),ut=(yt[9]+1)/yt[5],Y=(yt[9]-1)/yt[5],st=(yt[8]-1)/yt[0],vt=(It[8]+1)/It[0],Vt=Kt*st,St=Kt*vt,Xt=Mt/(-st+vt),Qt=Xt*-st;if(V.matrixWorld.decompose(U.position,U.quaternion,U.scale),U.translateX(Qt),U.translateZ(Xt),U.matrixWorld.compose(U.position,U.quaternion,U.scale),U.matrixWorldInverse.copy(U.matrixWorld).invert(),yt[10]===-1)U.projectionMatrix.copy(V.projectionMatrix),U.projectionMatrixInverse.copy(V.projectionMatrixInverse);else{let F=Kt+Xt,ye=it+Xt,ne=Vt-Qt,C=St+(Mt-Qt),y=ut*it/ye*F,H=Y*it/ye*F;U.projectionMatrix.makePerspective(ne,C,y,H,F,ye),U.projectionMatrixInverse.copy(U.projectionMatrix).invert()}}function Et(U,V){V===null?U.matrixWorld.copy(U.matrix):U.matrixWorld.multiplyMatrices(V.matrixWorld,U.matrix),U.matrixWorldInverse.copy(U.matrixWorld).invert()}this.updateCamera=function(U){if(s===null)return;let V=U.near,dt=U.far;p.texture!==null&&(p.depthNear>0&&(V=p.depthNear),p.depthFar>0&&(dt=p.depthFar)),B.near=L.near=I.near=V,B.far=L.far=I.far=dt,(D!==B.near||O!==B.far)&&(s.updateRenderState({depthNear:B.near,depthFar:B.far}),D=B.near,O=B.far),B.layers.mask=U.layers.mask|6,I.layers.mask=B.layers.mask&-5,L.layers.mask=B.layers.mask&-3;let Mt=U.parent,yt=B.cameras;Et(B,Mt);for(let It=0;It<yt.length;It++)Et(yt[It],Mt);yt.length===2?nt(B,I,L):B.projectionMatrix.copy(I.projectionMatrix),T===null&&U.isPerspectiveCamera&&(T={camera:U,fov:U.fov,zoom:U.zoom}),pt(U,B,Mt)};function pt(U,V,dt){dt===null?U.matrix.copy(V.matrixWorld):(U.matrix.copy(dt.matrixWorld),U.matrix.invert(),U.matrix.multiply(V.matrixWorld)),U.matrix.decompose(U.position,U.quaternion,U.scale),U.updateMatrixWorld(!0),U.projectionMatrix.copy(V.projectionMatrix),U.projectionMatrixInverse.copy(V.projectionMatrixInverse),U.isPerspectiveCamera&&(U.fov=Js*2*Math.atan(1/U.projectionMatrix.elements[5]),U.zoom=1)}this.getCamera=function(){return B},this.getFoveation=function(){if(!(u===null&&f===null))return c},this.setFoveation=function(U){c=U,u!==null&&(u.fixedFoveation=U),f!==null&&f.fixedFoveation!==void 0&&(f.fixedFoveation=U)},this.hasDepthSensing=function(){return p.texture!==null},this.getDepthSensingMesh=function(){return p.getMesh(B)},this.getCameraTexture=function(U){return m[U]};let Ft=null;function Dt(U,V){if(h=V.getViewerPose(l||a),g=V,h!==null){let dt=h.views;f!==null&&(t.setRenderTargetFramebuffer(v,f.framebuffer),t.setRenderTarget(v));let Mt=!1;dt.length!==B.cameras.length&&(B.cameras.length=0,Mt=!0);for(let it=0;it<dt.length;it++){let ut=dt[it],Y=null;if(f!==null)Y=f.getViewport(ut);else{let vt=d.getViewSubImage(u,ut);Y=vt.viewport,it===0&&(t.setRenderTargetTextures(v,vt.colorTexture,vt.depthStencilTexture),t.setRenderTarget(v))}let st=N[it];st===void 0&&(st=new Ze,st.layers.enable(it),st.viewport=new xe,N[it]=st),st.matrix.fromArray(ut.transform.matrix),st.matrix.decompose(st.position,st.quaternion,st.scale),st.projectionMatrix.fromArray(ut.projectionMatrix),st.projectionMatrixInverse.copy(st.projectionMatrix).invert(),st.viewport.set(Y.x,Y.y,Y.width,Y.height),it===0&&(B.matrix.copy(st.matrix),B.matrix.decompose(B.position,B.quaternion,B.scale)),Mt===!0&&B.cameras.push(st)}let yt=s.enabledFeatures;if(yt&&yt.includes("depth-sensing")&&s.depthUsage=="gpu-optimized"&&x){d=n.getBinding();let it=d.getDepthInformation(dt[0]);it&&it.isValid&&it.texture&&p.init(it,s.renderState)}if(yt&&yt.includes("camera-access")&&x){t.state.unbindTexture(),d=n.getBinding();for(let it=0;it<dt.length;it++){let ut=dt[it].camera;if(ut){let Y=m[ut];Y||(Y=new Zr,m[ut]=Y);let st=d.getCameraImage(ut);Y.sourceTexture=st}}}}for(let dt=0;dt<b.length;dt++){let Mt=M[dt],yt=b[dt];Mt!==null&&yt!==void 0&&yt.update(Mt,V,l||a)}Ft&&Ft(U,V),V.detectedPlanes&&n.dispatchEvent({type:"planesdetected",data:V}),g=null}let ft=new Cd;ft.setAnimationLoop(Dt),this.setAnimationLoop=function(U){Ft=U},this.dispose=function(){}}},Nx=new ue,Nd=new ce;Nd.set(-1,0,0,0,1,0,0,0,1);function Fx(i,t){function e(p,m){p.matrixAutoUpdate===!0&&p.updateMatrix(),m.value.copy(p.matrix)}function n(p,m){m.color.getRGB(p.fogColor.value,nh(i)),m.isFog?(p.fogNear.value=m.near,p.fogFar.value=m.far):m.isFogExp2&&(p.fogDensity.value=m.density)}function s(p,m,S,E,v){m.isNodeMaterial?m.uniformsNeedUpdate=!1:m.isMeshBasicMaterial?r(p,m):m.isMeshLambertMaterial?(r(p,m),m.envMap&&(p.envMapIntensity.value=m.envMapIntensity)):m.isMeshToonMaterial?(r(p,m),d(p,m)):m.isMeshPhongMaterial?(r(p,m),h(p,m),m.envMap&&(p.envMapIntensity.value=m.envMapIntensity)):m.isMeshStandardMaterial?(r(p,m),u(p,m),m.isMeshPhysicalMaterial&&f(p,m,v)):m.isMeshMatcapMaterial?(r(p,m),g(p,m)):m.isMeshDepthMaterial?r(p,m):m.isMeshDistanceMaterial?(r(p,m),x(p,m)):m.isMeshNormalMaterial?r(p,m):m.isLineBasicMaterial?(a(p,m),m.isLineDashedMaterial&&o(p,m)):m.isPointsMaterial?c(p,m,S,E):m.isSpriteMaterial?l(p,m):m.isShadowMaterial?(p.color.value.copy(m.color),p.opacity.value=m.opacity):m.isShaderMaterial&&(m.uniformsNeedUpdate=!1)}function r(p,m){p.opacity.value=m.opacity,m.color&&p.diffuse.value.copy(m.color),m.emissive&&p.emissive.value.copy(m.emissive).multiplyScalar(m.emissiveIntensity),m.map&&(p.map.value=m.map,e(m.map,p.mapTransform)),m.alphaMap&&(p.alphaMap.value=m.alphaMap,e(m.alphaMap,p.alphaMapTransform)),m.bumpMap&&(p.bumpMap.value=m.bumpMap,e(m.bumpMap,p.bumpMapTransform),p.bumpScale.value=m.bumpScale,m.side===rn&&(p.bumpScale.value*=-1)),m.normalMap&&(p.normalMap.value=m.normalMap,e(m.normalMap,p.normalMapTransform),p.normalScale.value.copy(m.normalScale),m.side===rn&&p.normalScale.value.negate()),m.displacementMap&&(p.displacementMap.value=m.displacementMap,e(m.displacementMap,p.displacementMapTransform),p.displacementScale.value=m.displacementScale,p.displacementBias.value=m.displacementBias),m.emissiveMap&&(p.emissiveMap.value=m.emissiveMap,e(m.emissiveMap,p.emissiveMapTransform)),m.specularMap&&(p.specularMap.value=m.specularMap,e(m.specularMap,p.specularMapTransform)),m.alphaTest>0&&(p.alphaTest.value=m.alphaTest);let S=t.get(m),E=S.envMap,v=S.envMapRotation;E&&(p.envMap.value=E,p.envMapRotation.value.setFromMatrix4(Nx.makeRotationFromEuler(v)).transpose(),E.isCubeTexture&&E.isRenderTargetTexture===!1&&p.envMapRotation.value.premultiply(Nd),p.reflectivity.value=m.reflectivity,p.ior.value=m.ior,p.refractionRatio.value=m.refractionRatio),m.lightMap&&(p.lightMap.value=m.lightMap,p.lightMapIntensity.value=m.lightMapIntensity,e(m.lightMap,p.lightMapTransform)),m.aoMap&&(p.aoMap.value=m.aoMap,p.aoMapIntensity.value=m.aoMapIntensity,e(m.aoMap,p.aoMapTransform))}function a(p,m){p.diffuse.value.copy(m.color),p.opacity.value=m.opacity,m.map&&(p.map.value=m.map,e(m.map,p.mapTransform))}function o(p,m){p.dashSize.value=m.dashSize,p.totalSize.value=m.dashSize+m.gapSize,p.scale.value=m.scale}function c(p,m,S,E){p.diffuse.value.copy(m.color),p.opacity.value=m.opacity,p.size.value=m.size*S,p.scale.value=E*.5,m.map&&(p.map.value=m.map,e(m.map,p.uvTransform)),m.alphaMap&&(p.alphaMap.value=m.alphaMap,e(m.alphaMap,p.alphaMapTransform)),m.alphaTest>0&&(p.alphaTest.value=m.alphaTest)}function l(p,m){p.diffuse.value.copy(m.color),p.opacity.value=m.opacity,p.rotation.value=m.rotation,m.map&&(p.map.value=m.map,e(m.map,p.mapTransform)),m.alphaMap&&(p.alphaMap.value=m.alphaMap,e(m.alphaMap,p.alphaMapTransform)),m.alphaTest>0&&(p.alphaTest.value=m.alphaTest)}function h(p,m){p.specular.value.copy(m.specular),p.shininess.value=Math.max(m.shininess,1e-4)}function d(p,m){m.gradientMap&&(p.gradientMap.value=m.gradientMap)}function u(p,m){p.metalness.value=m.metalness,m.metalnessMap&&(p.metalnessMap.value=m.metalnessMap,e(m.metalnessMap,p.metalnessMapTransform)),p.roughness.value=m.roughness,m.roughnessMap&&(p.roughnessMap.value=m.roughnessMap,e(m.roughnessMap,p.roughnessMapTransform)),m.envMap&&(p.envMapIntensity.value=m.envMapIntensity)}function f(p,m,S){p.ior.value=m.ior,m.sheen>0&&(p.sheenColor.value.copy(m.sheenColor).multiplyScalar(m.sheen),p.sheenRoughness.value=m.sheenRoughness,m.sheenColorMap&&(p.sheenColorMap.value=m.sheenColorMap,e(m.sheenColorMap,p.sheenColorMapTransform)),m.sheenRoughnessMap&&(p.sheenRoughnessMap.value=m.sheenRoughnessMap,e(m.sheenRoughnessMap,p.sheenRoughnessMapTransform))),m.clearcoat>0&&(p.clearcoat.value=m.clearcoat,p.clearcoatRoughness.value=m.clearcoatRoughness,m.clearcoatMap&&(p.clearcoatMap.value=m.clearcoatMap,e(m.clearcoatMap,p.clearcoatMapTransform)),m.clearcoatRoughnessMap&&(p.clearcoatRoughnessMap.value=m.clearcoatRoughnessMap,e(m.clearcoatRoughnessMap,p.clearcoatRoughnessMapTransform)),m.clearcoatNormalMap&&(p.clearcoatNormalMap.value=m.clearcoatNormalMap,e(m.clearcoatNormalMap,p.clearcoatNormalMapTransform),p.clearcoatNormalScale.value.copy(m.clearcoatNormalScale),m.side===rn&&p.clearcoatNormalScale.value.negate())),m.dispersion>0&&(p.dispersion.value=m.dispersion),m.retroreflectivity>0&&(p.retroreflectivity.value=m.retroreflectivity),m.iridescence>0&&(p.iridescence.value=m.iridescence,p.iridescenceIOR.value=m.iridescenceIOR,p.iridescenceThicknessMinimum.value=m.iridescenceThicknessRange[0],p.iridescenceThicknessMaximum.value=m.iridescenceThicknessRange[1],m.iridescenceMap&&(p.iridescenceMap.value=m.iridescenceMap,e(m.iridescenceMap,p.iridescenceMapTransform)),m.iridescenceThicknessMap&&(p.iridescenceThicknessMap.value=m.iridescenceThicknessMap,e(m.iridescenceThicknessMap,p.iridescenceThicknessMapTransform))),m.transmission>0&&(p.transmission.value=m.transmission,p.transmissionSamplerMap.value=S.texture,p.transmissionSamplerSize.value.set(S.width,S.height),m.transmissionMap&&(p.transmissionMap.value=m.transmissionMap,e(m.transmissionMap,p.transmissionMapTransform)),p.thickness.value=m.thickness,m.thicknessMap&&(p.thicknessMap.value=m.thicknessMap,e(m.thicknessMap,p.thicknessMapTransform)),p.attenuationDistance.value=m.attenuationDistance,p.attenuationColor.value.copy(m.attenuationColor)),m.anisotropy>0&&(p.anisotropyVector.value.set(m.anisotropy*Math.cos(m.anisotropyRotation),m.anisotropy*Math.sin(m.anisotropyRotation)),m.anisotropyMap&&(p.anisotropyMap.value=m.anisotropyMap,e(m.anisotropyMap,p.anisotropyMapTransform))),p.specularIntensity.value=m.specularIntensity,p.specularColor.value.copy(m.specularColor),m.specularColorMap&&(p.specularColorMap.value=m.specularColorMap,e(m.specularColorMap,p.specularColorMapTransform)),m.specularIntensityMap&&(p.specularIntensityMap.value=m.specularIntensityMap,e(m.specularIntensityMap,p.specularIntensityMapTransform))}function g(p,m){m.matcap&&(p.matcap.value=m.matcap)}function x(p,m){let S=t.get(m).light;p.referencePosition.value.setFromMatrixPosition(S.matrixWorld),p.nearDistance.value=S.shadow.camera.near,p.farDistance.value=S.shadow.camera.far}return{refreshFogUniforms:n,refreshMaterialUniforms:s}}function zx(i,t,e,n){let s={},r={},a=[],o=i.getParameter(i.MAX_UNIFORM_BUFFER_BINDINGS);function c(v,b){let M=b.program;n.uniformBlockBinding(v,M)}function l(v,b){let M=s[v.id];M===void 0&&(p(v),M=h(v),s[v.id]=M,v.addEventListener("dispose",S));let A=b.program;n.updateUBOMapping(v,A);let _=t.render.frame;r[v.id]!==_&&(u(v),r[v.id]=_)}function h(v){let b=d();v.__bindingPointIndex=b;let M=i.createBuffer(),A=v.__size,_=v.usage;return i.bindBuffer(i.UNIFORM_BUFFER,M),i.bufferData(i.UNIFORM_BUFFER,A,_),i.bindBuffer(i.UNIFORM_BUFFER,null),i.bindBufferBase(i.UNIFORM_BUFFER,b,M),M}function d(){for(let v=0;v<o;v++)if(a.indexOf(v)===-1)return a.push(v),v;return se("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function u(v){let b=s[v.id],M=v.uniforms,A=v.__cache;i.bindBuffer(i.UNIFORM_BUFFER,b);for(let _=0,T=M.length;_<T;_++){let I=M[_];if(Array.isArray(I))for(let L=0,N=I.length;L<N;L++)f(I[L],_,L,A);else f(I,_,0,A)}i.bindBuffer(i.UNIFORM_BUFFER,null)}function f(v,b,M,A){if(x(v,b,M,A)===!0){let _=v.__offset,T=v.value;if(Array.isArray(T)){let I=0;for(let L=0;L<T.length;L++){let N=T[L],B=m(N);g(N,v.__data,I),typeof N!="number"&&typeof N!="boolean"&&!N.isMatrix3&&!ArrayBuffer.isView(N)&&(I+=B.storage/Float32Array.BYTES_PER_ELEMENT)}}else g(T,v.__data,0);i.bufferSubData(i.UNIFORM_BUFFER,_,v.__data)}}function g(v,b,M){typeof v=="number"||typeof v=="boolean"?b[0]=v:v.isMatrix3?(b[0]=v.elements[0],b[1]=v.elements[1],b[2]=v.elements[2],b[3]=0,b[4]=v.elements[3],b[5]=v.elements[4],b[6]=v.elements[5],b[7]=0,b[8]=v.elements[6],b[9]=v.elements[7],b[10]=v.elements[8],b[11]=0):ArrayBuffer.isView(v)?b.set(new v.constructor(v.buffer,v.byteOffset,b.length)):v.toArray(b,M)}function x(v,b,M,A){let _=v.value,T=b+"_"+M;if(A[T]===void 0)return typeof _=="number"||typeof _=="boolean"?A[T]=_:ArrayBuffer.isView(_)?A[T]=_.slice():A[T]=_.clone(),!0;{let I=A[T];if(typeof _=="number"||typeof _=="boolean"){if(I!==_)return A[T]=_,!0}else{if(ArrayBuffer.isView(_))return!0;if(I.equals(_)===!1)return I.copy(_),!0}}return!1}function p(v){let b=v.uniforms,M=0,A=16;for(let T=0,I=b.length;T<I;T++){let L=Array.isArray(b[T])?b[T]:[b[T]];for(let N=0,B=L.length;N<B;N++){let D=L[N],O=Array.isArray(D.value)?D.value:[D.value];for(let $=0,J=O.length;$<J;$++){let W=O[$],G=m(W),K=M%A,nt=K%G.boundary,Et=K+nt;M+=nt,Et!==0&&A-Et<G.storage&&(M+=A-Et),D.__data=new Float32Array(G.storage/Float32Array.BYTES_PER_ELEMENT),D.__offset=M,M+=G.storage}}}let _=M%A;return _>0&&(M+=A-_),v.__size=M,v.__cache={},this}function m(v){let b={boundary:0,storage:0};return typeof v=="number"||typeof v=="boolean"?(b.boundary=4,b.storage=4):v.isVector2?(b.boundary=8,b.storage=8):v.isVector3||v.isColor?(b.boundary=16,b.storage=12):v.isVector4?(b.boundary=16,b.storage=16):v.isMatrix3?(b.boundary=48,b.storage=48):v.isMatrix4?(b.boundary=64,b.storage=64):v.isTexture?ee("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(v)?(b.boundary=16,b.storage=v.byteLength):ee("WebGLRenderer: Unsupported uniform value type.",v),b}function S(v){let b=v.target;b.removeEventListener("dispose",S);let M=a.indexOf(b.__bindingPointIndex);a.splice(M,1),i.deleteBuffer(s[b.id]),delete s[b.id],delete r[b.id]}function E(){for(let v in s)i.deleteBuffer(s[v]);a=[],s={},r={}}return{bind:c,update:l,dispose:E}}var Ox=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]),yi=null;function Bx(){return yi===null&&(yi=new vs(Ox,16,16,xi,On),yi.name="DFG_LUT",yi.minFilter=$e,yi.magFilter=$e,yi.wrapS=Hn,yi.wrapT=Hn,yi.generateMipmaps=!1,yi.needsUpdate=!0),yi}var Nc=class{constructor(t={}){let{canvas:e=Ju(),context:n=null,depth:s=!0,stencil:r=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:c=!0,preserveDrawingBuffer:l=!1,powerPreference:h="default",failIfMajorPerformanceCaveat:d=!1,reversedDepthBuffer:u=!1,outputBufferType:f=Cn}=t;this.isWebGLRenderer=!0;let g;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");g=n.getContextAttributes().alpha}else g=a;let x=f,p=new Set([Ko,Jo,$o]),m=new Set([Cn,ai,lr,hr,Yo,jo]),S=new Uint32Array(4),E=new Int32Array(4),v=new P,b=null,M=null,A=[],_=[],T=null;this.domElement=e,this.debug={checkShaderErrors:!0,diagnostics:{keywords:!1},onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=zn,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let I=this,L=!1,N=null,B=null,D=null,O=null;this._outputColorSpace=yn;let $=0,J=0,W=null,G=-1,K=null,nt=new xe,Et=new xe,pt=null,Ft=new Ot(0),Dt=0,ft=e.width,U=e.height,V=1,dt=null,Mt=null,yt=new xe(0,0,ft,U),It=new xe(0,0,ft,U),Kt=!1,it=new er,ut=!1,Y=!1,st=new ue,vt=new P,Vt=new xe,St={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},Xt=!1;function Qt(){return W===null?V:1}let F=n;function ye(w,z){return e.getContext(w,z)}let ne,C,y,H,X,tt,ct,_t,rt,ht,bt,Wt,At,Tt,Bt,jt,re,R,j,k,at,xt,et;try{let w={alpha:!0,depth:s,stencil:r,antialias:o,premultipliedAlpha:c,preserveDrawingBuffer:l,powerPreference:h,failIfMajorPerformanceCaveat:d};if("setAttribute"in e&&e.setAttribute("data-engine",`three.js r${"186"}`),e.addEventListener("webglcontextlost",he,!1),e.addEventListener("webglcontextrestored",de,!1),e.addEventListener("webglcontextcreationerror",Ge,!1),F===null){let z="webgl2";if(F=ye(z,w),F===null)throw ye(z)?new Error("THREE.WebGLRenderer: Error creating WebGL context with your selected attributes."):new Error("THREE.WebGLRenderer: Error creating WebGL context.")}wt()}catch(w){throw e.removeEventListener("webglcontextlost",he,!1),e.removeEventListener("webglcontextrestored",de,!1),e.removeEventListener("webglcontextcreationerror",Ge,!1),se("WebGLRenderer: "+w.message),w}function wt(){ne=new qg(F),ne.init(),at=new Lx(F,ne),C=new Fg(F,ne,t,at),y=new Px(F,ne),C.reversedDepthBuffer&&u&&y.buffers.depth.setReversed(!0),B=F.createFramebuffer(),D=F.createFramebuffer(),O=F.createFramebuffer(),H=new Zg(F),X=new gx,tt=new Ix(F,ne,y,X,C,at,H),ct=new Xg(I),_t=new Jp(F),xt=new Ug(F,_t),rt=new Yg(F,_t,H,xt),ht=new Jg(F,rt,_t,xt,H),R=new $g(F,C,tt),Bt=new zg(X),bt=new mx(I,ct,ne,C,xt,Bt),Wt=new Fx(I,X),At=new xx,Tt=new Ex(ne),re=new Dg(I,ct,y,ht,g,c),jt=new Cx(I,ht,C),et=new zx(F,H,C,y),j=new Ng(F,ne,H),k=new jg(F,ne,H),H.programs=bt.programs,I.capabilities=C,I.extensions=ne,I.properties=X,I.renderLists=At,I.shadowMap=jt,I.state=y,I.info=H}x!==Cn&&(T=new Qg(x,e.width,e.height,o,s,r));let Pt=new wh(I,F);this.xr=Pt,this.getContext=function(){return F},this.getContextAttributes=function(){return F.getContextAttributes()},this.forceContextLoss=function(){let w=ne.get("WEBGL_lose_context");w&&w.loseContext()},this.forceContextRestore=function(){let w=ne.get("WEBGL_lose_context");w&&w.restoreContext()},this.getPixelRatio=function(){return V},this.setPixelRatio=function(w){w!==void 0&&(V=w,this.setSize(ft,U,!1))},this.getSize=function(w){return w.set(ft,U)},this.setSize=function(w,z,Q=!0){if(Pt.isPresenting){ee("WebGLRenderer: Can't change size while VR device is presenting.");return}ft=w,U=z,e.width=Math.floor(w*V),e.height=Math.floor(z*V),Q===!0&&(e.style.width=w+"px",e.style.height=z+"px"),T!==null&&T.setSize(e.width,e.height),this.setViewport(0,0,w,z)},this.getDrawingBufferSize=function(w){return w.set(ft*V,U*V).floor()},this.setDrawingBufferSize=function(w,z,Q){ft=w,U=z,V=Q,e.width=Math.floor(w*Q),e.height=Math.floor(z*Q),this.setViewport(0,0,w,z)},this.setEffects=function(w){if(x===Cn){se("WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(w){for(let z=0;z<w.length;z++)if(w[z].isOutputPass===!0){ee("WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}T.setEffects(w||[])},this.getCurrentViewport=function(w){return w.copy(nt)},this.getViewport=function(w){return w.copy(yt)},this.setViewport=function(w,z,Q,q){w.isVector4?yt.set(w.x,w.y,w.z,w.w):yt.set(w,z,Q,q),y.viewport(nt.copy(yt).multiplyScalar(V).round())},this.getScissor=function(w){return w.copy(It)},this.setScissor=function(w,z,Q,q){w.isVector4?It.set(w.x,w.y,w.z,w.w):It.set(w,z,Q,q),y.scissor(Et.copy(It).multiplyScalar(V).round())},this.getScissorTest=function(){return Kt},this.setScissorTest=function(w){y.setScissorTest(Kt=w)},this.setOpaqueSort=function(w){dt=w},this.setTransparentSort=function(w){Mt=w},this.getClearColor=function(w){return w.copy(re.getClearColor())},this.setClearColor=function(){re.setClearColor(...arguments)},this.getClearAlpha=function(){return re.getClearAlpha()},this.setClearAlpha=function(){re.setClearAlpha(...arguments)},this.clear=function(w=!0,z=!0,Q=!0){let q=0;if(w){let Z=!1;if(W!==null){let Ut=W.texture.format;Z=p.has(Ut)}if(Z){let Ut=W.texture.type,kt=m.has(Ut),Lt=re.getClearColor(),qt=re.getClearAlpha(),$t=Lt.r,pe=Lt.g,Me=Lt.b;kt?(S[0]=$t,S[1]=pe,S[2]=Me,S[3]=qt,F.clearBufferuiv(F.COLOR,0,S)):(E[0]=$t,E[1]=pe,E[2]=Me,E[3]=qt,F.clearBufferiv(F.COLOR,0,E))}else q|=F.COLOR_BUFFER_BIT}z&&(q|=F.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),Q&&(q|=F.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),q!==0&&F.clear(q)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(w){w.setRenderer(this),N=w},this.dispose=function(){e.removeEventListener("webglcontextlost",he,!1),e.removeEventListener("webglcontextrestored",de,!1),e.removeEventListener("webglcontextcreationerror",Ge,!1),re.dispose(),At.dispose(),Tt.dispose(),X.dispose(),ct.dispose(),ht.dispose(),xt.dispose(),et.dispose(),bt.dispose(),Pt.dispose(),Pt.removeEventListener("sessionstart",hs),Pt.removeEventListener("sessionend",As),jn.stop()};function he(w){w.preventDefault(),Or("WebGLRenderer: Context Lost."),L=!0}function de(){Or("WebGLRenderer: Context Restored."),L=!1;let w=H.autoReset,z=jt.enabled,Q=jt.autoUpdate,q=jt.needsUpdate,Z=jt.type;wt(),H.autoReset=w,jt.enabled=z,jt.autoUpdate=Q,jt.needsUpdate=q,jt.type=Z}function Ge(w){se("WebGLRenderer: A WebGL context could not be created. Reason: ",w.statusMessage)}function ln(w){let z=w.target;z.removeEventListener("dispose",ln),Oi(z)}function Oi(w){yr(w),X.remove(w)}function yr(w){let z=X.get(w).programs;z!==void 0&&(z.forEach(function(Q){bt.releaseProgram(Q)}),w.isShaderMaterial&&bt.releaseShaderCache(w))}this.renderBufferDirect=function(w,z,Q,q,Z,Ut){z===null&&(z=St);let kt=Z.isMesh&&Z.matrixWorld.determinantAffine()<0,Lt=wi(w,z,Q,q,Z);y.setMaterial(q,kt);let qt=Q.index,$t=1;if(q.wireframe===!0){if(qt=rt.getWireframeAttribute(Q),qt===void 0)return;$t=2}let pe=Q.drawRange,Me=Q.attributes.position,Yt=pe.start*$t,Te=(pe.start+pe.count)*$t;Ut!==null&&(Yt=Math.max(Yt,Ut.start*$t),Te=Math.min(Te,(Ut.start+Ut.count)*$t)),qt!==null?(Yt=Math.max(Yt,0),Te=Math.min(Te,qt.count)):Me!=null&&(Yt=Math.max(Yt,0),Te=Math.min(Te,Me.count));let Ye=Te-Yt;if(Ye<0||Ye===1/0)return;xt.setup(Z,q,Lt,Q,qt);let ze,De=j;if(qt!==null&&(ze=_t.get(qt),De=k,De.setIndex(ze)),Z.isMesh)q.wireframe===!0?(y.setLineWidth(q.wireframeLinewidth*Qt()),De.setMode(F.LINES)):De.setMode(F.TRIANGLES);else if(Z.isLine){let hn=q.linewidth;hn===void 0&&(hn=1),y.setLineWidth(hn*Qt()),Z.isLineSegments?De.setMode(F.LINES):Z.isLineLoop?De.setMode(F.LINE_LOOP):De.setMode(F.LINE_STRIP)}else Z.isPoints?De.setMode(F.POINTS):Z.isSprite&&De.setMode(F.TRIANGLES);if(Z.isBatchedMesh)if(ne.get("WEBGL_multi_draw"))De.renderMultiDraw(Z._multiDrawStarts,Z._multiDrawCounts,Z._multiDrawCount);else{let hn=Z._multiDrawStarts,zt=Z._multiDrawCounts,xn=Z._multiDrawCount,Ee=qt?_t.get(qt).bytesPerElement:1,Bn=X.get(q).currentProgram.getUniforms();for(let li=0;li<xn;li++)Bn.setValue(F,"_gl_DrawID",li),De.render(hn[li]/Ee,zt[li])}else if(Z.isInstancedMesh)De.renderInstances(Yt,Ye,Z.count);else if(Q.isInstancedBufferGeometry){let hn=Q._maxInstanceCount!==void 0?Q._maxInstanceCount:1/0,zt=Math.min(Q.instanceCount,hn);De.renderInstances(Yt,Ye,zt)}else De.render(Yt,Ye)};function Mr(w,z,Q,q){N!==null&&w.isNodeMaterial&&N.setObject(q,w),ut===!0&&Bt.setState(w,Q,!1),w.transparent===!0&&w.side===fn&&w.forceSinglePass===!1?(w.side=rn,w.needsUpdate=!0,Gt(w,z,q),w.side=ns,w.needsUpdate=!0,Gt(w,z,q),w.side=fn):Gt(w,z,q)}this.compile=function(w,z,Q=null){Q===null&&(Q=w),N!==null&&N.renderStart(w,z,Q),M=Tt.get(Q),M.init(z),_.push(M),Q.traverseVisible(function(Z){Z.isLight&&Z.layers.test(z.layers)&&(M.pushLight(Z),Z.castShadow&&M.pushShadow(Z))}),w!==Q&&w.traverseVisible(function(Z){Z.isLight&&Z.layers.test(z.layers)&&(M.pushLight(Z),Z.castShadow&&M.pushShadow(Z))}),M.setupLights(),N!==null&&N.updateLights(M.state.lightsArray),Y=this.localClippingEnabled,ut=Bt.init(this.clippingPlanes,Y),ut===!0&&Bt.setGlobalState(this.clippingPlanes,z),N!==null&&jt.render(M.state.shadowsArray,Q,z);let q=new Set;return w.traverse(function(Z){if(!(Z.isMesh||Z.isPoints||Z.isLine||Z.isSprite))return;let Ut=Z.material;if(Ut)if(Array.isArray(Ut))for(let kt=0;kt<Ut.length;kt++){let Lt=Ut[kt];Mr(Lt,Q,z,Z),q.add(Lt)}else Mr(Ut,Q,z,Z),q.add(Ut)}),M=_.pop(),N!==null&&N.renderEnd(),q},this.compileAsync=function(w,z,Q=null){let q=this.compile(w,z,Q);return new Promise(Z=>{function Ut(){if(q.forEach(function(kt){let qt=X.get(kt).currentProgram;(qt===void 0||qt.isReady())&&q.delete(kt)}),q.size===0){Z(w);return}setTimeout(Ut,10)}ne.get("KHR_parallel_shader_compile")!==null?Ut():setTimeout(Ut,10)})};let qe=null;function Tn(w){qe&&qe(w)}function hs(){jn.stop()}function As(){jn.start()}let jn=new Cd;jn.setAnimationLoop(Tn),typeof self<"u"&&jn.setContext(self),this.setAnimationLoop=function(w){qe=w,Pt.setAnimationLoop(w),w===null?jn.stop():jn.start()},Pt.addEventListener("sessionstart",hs),Pt.addEventListener("sessionend",As),this.render=function(w,z){if(z!==void 0&&z.isCamera!==!0){se("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(L===!0)return;N!==null&&N.renderStart(w,z);let Q=Pt.enabled===!0&&Pt.isPresenting===!0,q=T!==null&&(W===null||Q)&&T.begin(I,W);if(w.matrixWorldAutoUpdate===!0&&w.updateMatrixWorld(),z.parent===null&&z.matrixWorldAutoUpdate===!0&&z.updateMatrixWorld(),Pt.enabled===!0&&Pt.isPresenting===!0&&(T===null||T.isCompositing()===!1)&&(Pt.cameraAutoUpdate===!0&&Pt.updateCamera(z),z=Pt.getCamera()),w.isScene===!0&&w.onBeforeRender(I,w,z,W),M=Tt.get(w,_.length),M.init(z),M.state.textureUnits=tt.getTextureUnits(),_.push(M),st.multiplyMatrices(z.projectionMatrix,z.matrixWorldInverse),it.setFromProjectionMatrix(st,ei,z.reversedDepth),Y=this.localClippingEnabled,ut=Bt.init(this.clippingPlanes,Y),b=At.get(w,A.length),b.init(),A.push(b),Pt.enabled===!0&&Pt.isPresenting===!0){let kt=I.xr.getDepthSensingMesh();kt!==null&&Sr(kt,z,-1/0,I.sortObjects)}Sr(w,z,0,I.sortObjects),b.finish(),N!==null&&N.updateLights(M.state.lightsArray),I.sortObjects===!0&&b.sort(dt,Mt),Xt=Pt.enabled===!1||Pt.isPresenting===!1||Pt.hasDepthSensing()===!1,Xt&&re.addToRenderList(b,w),this.info.render.frame++,this.info.autoReset===!0&&this.info.reset(),ut===!0&&Bt.beginShadows();let Z=M.state.shadowsArray;if(jt.render(Z,w,z),ut===!0&&Bt.endShadows(),(q&&T.hasRenderPass())===!1){let kt=b.opaque,Lt=b.transmissive;if(M.setupLights(),z.isArrayCamera){let qt=z.cameras;if(Lt.length>0)for(let $t=0,pe=qt.length;$t<pe;$t++){let Me=qt[$t];Rt(kt,Lt,w,Me)}Xt&&re.render(w);for(let $t=0,pe=qt.length;$t<pe;$t++){let Me=qt[$t];lt(b,w,Me,Me.viewport)}}else Lt.length>0&&Rt(kt,Lt,w,z),Xt&&re.render(w),lt(b,w,z)}W!==null&&J===0&&(tt.updateMultisampleRenderTarget(W),tt.updateRenderTargetMipmap(W)),q&&T.end(I),w.isScene===!0&&w.onAfterRender(I,w,z),xt.resetDefaultState(),G=-1,K=null,_.pop(),_.length>0?(M=_[_.length-1],tt.setTextureUnits(M.state.textureUnits),ut===!0&&Bt.setGlobalState(I.clippingPlanes,M.state.camera)):M=null,A.pop(),A.length>0?b=A[A.length-1]:b=null,N!==null&&N.renderEnd()};function Sr(w,z,Q,q){if(w.visible===!1)return;if(w.layers.test(z.layers)){if(w.isGroup)Q=w.renderOrder;else if(w.isLOD)w.autoUpdate===!0&&w.update(z);else if(w.isLightProbeGrid)M.pushLightProbeGrid(w);else if(w.isLight)M.pushLight(w),w.castShadow&&M.pushShadow(w);else if(w.isSprite){if(!w.frustumCulled||w.intersectsFrustum(it)){q&&Vt.setFromMatrixPosition(w.matrixWorld).applyMatrix4(st);let kt=ht.update(w),Lt=w.material;Lt.visible&&b.push(w,kt,Lt,Q,Vt.z,null,z)}}else if((w.isMesh||w.isLine||w.isPoints)&&(!w.frustumCulled||w.intersectsFrustum(it))){let kt=ht.update(w),Lt=w.material;if(q&&(w.boundingSphere!==void 0?(w.boundingSphere===null&&w.computeBoundingSphere(),Vt.copy(w.boundingSphere.center)):(kt.boundingSphere===null&&kt.computeBoundingSphere(),Vt.copy(kt.boundingSphere.center)),Vt.applyMatrix4(w.matrixWorld).applyMatrix4(st)),Array.isArray(Lt)){let qt=kt.groups;for(let $t=0,pe=qt.length;$t<pe;$t++){let Me=qt[$t],Yt=Lt[Me.materialIndex];Yt&&Yt.visible&&b.push(w,kt,Yt,Q,Vt.z,Me,z)}}else Lt.visible&&b.push(w,kt,Lt,Q,Vt.z,null,z)}}let Ut=w.children;for(let kt=0,Lt=Ut.length;kt<Lt;kt++)Sr(Ut[kt],z,Q,q)}function lt(w,z,Q,q){let{opaque:Z,transmissive:Ut,transparent:kt}=w;M.setupLightsView(Q),ut===!0&&Bt.setGlobalState(I.clippingPlanes,Q),q&&y.viewport(nt.copy(q)),Z.length>0&&gt(Z,z,Q),Ut.length>0&&gt(Ut,z,Q),kt.length>0&&gt(kt,z,Q),y.buffers.depth.setTest(!0),y.buffers.depth.setMask(!0),y.buffers.color.setMask(!0),y.setPolygonOffset(!1)}function Rt(w,z,Q,q){if((Q.isScene===!0?Q.overrideMaterial:null)!==null)return;if(M.state.transmissionRenderTarget[q.id]===void 0){let Yt=ne.has("EXT_color_buffer_half_float")||ne.has("EXT_color_buffer_float");M.state.transmissionRenderTarget[q.id]=new An(1,1,{generateMipmaps:!0,type:Yt?On:Cn,minFilter:rs,samples:Math.max(4,C.samples),stencilBuffer:r,resolveDepthBuffer:!1,resolveStencilBuffer:!1,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,colorSpace:Se.workingColorSpace})}let Ut=M.state.transmissionRenderTarget[q.id],kt=q.viewport||nt;Ut.setSize(kt.z*I.transmissionResolutionScale,kt.w*I.transmissionResolutionScale);let Lt=I.getRenderTarget(),qt=I.getActiveCubeFace(),$t=I.getActiveMipmapLevel();I.setRenderTarget(Ut),I.getClearColor(Ft),Dt=I.getClearAlpha(),Dt<1&&I.setClearColor(16777215,.5),I.clear(),Xt&&re.render(Q);let pe=I.toneMapping;I.toneMapping=zn;let Me=q.viewport;if(q.viewport!==void 0&&(q.viewport=void 0),M.setupLightsView(q),ut===!0&&Bt.setGlobalState(I.clippingPlanes,q),gt(w,Q,q),tt.updateMultisampleRenderTarget(Ut),tt.updateRenderTargetMipmap(Ut),ne.has("WEBGL_multisampled_render_to_texture")===!1){let Yt=!1;for(let Te=0,Ye=z.length;Te<Ye;Te++){let ze=z[Te],{object:De,geometry:hn,material:zt,group:xn}=ze;if(zt.side===fn&&De.layers.test(q.layers)){let Ee=zt.side;zt.side=rn,zt.needsUpdate=!0,Zt(De,Q,q,hn,zt,xn),zt.side=Ee,zt.needsUpdate=!0,Yt=!0}}Yt===!0&&(tt.updateMultisampleRenderTarget(Ut),tt.updateRenderTargetMipmap(Ut))}I.setRenderTarget(Lt,qt,$t),I.setClearColor(Ft,Dt),Me!==void 0&&(q.viewport=Me),I.toneMapping=pe}function gt(w,z,Q){let q=z.isScene===!0?z.overrideMaterial:null;for(let Z=0,Ut=w.length;Z<Ut;Z++){let kt=w[Z],{object:Lt,geometry:qt,group:$t}=kt,pe=kt.material;pe.allowOverride===!0&&q!==null&&(pe=q),Lt.layers.test(Q.layers)&&Zt(Lt,z,Q,qt,pe,$t)}}function Zt(w,z,Q,q,Z,Ut){N!==null&&Z.isNodeMaterial&&N.setObject(w,Z),w.onBeforeRender(I,z,Q,q,Z,Ut),w.modelViewMatrix.multiplyMatrices(Q.matrixWorldInverse,w.matrixWorld),w.normalMatrix.getNormalMatrix(w.modelViewMatrix),Z.onBeforeRender(I,z,Q,q,w,Ut),Z.transparent===!0&&Z.side===fn&&Z.forceSinglePass===!1?(Z.side=rn,Z.needsUpdate=!0,I.renderBufferDirect(Q,z,q,Z,w,Ut),Z.side=ns,Z.needsUpdate=!0,I.renderBufferDirect(Q,z,q,Z,w,Ut),Z.side=fn):I.renderBufferDirect(Q,z,q,Z,w,Ut),w.onAfterRender(I,z,Q,q,Z,Ut)}function Gt(w,z,Q){z.isScene!==!0&&(z=St);let q=X.get(w),Z=M.state.lights,Ut=M.state.shadowsArray,kt=Z.state.version,Lt=bt.getParameters(w,Z.state,Ut,z,Q,M.state.lightProbeGridArray),qt=bt.getProgramCacheKey(Lt),$t=q.programs;q.environment=w.isMeshStandardMaterial||w.isMeshLambertMaterial||w.isMeshPhongMaterial?z.environment:null,q.fog=z.fog;let pe=w.isMeshStandardMaterial||w.isMeshLambertMaterial&&!w.envMap||w.isMeshPhongMaterial&&!w.envMap;q.envMap=ct.get(w.envMap||q.environment,pe),q.envMapRotation=q.environment!==null&&w.envMap===null?z.environmentRotation:w.envMapRotation,$t===void 0&&(w.addEventListener("dispose",ln),$t=new Map,q.programs=$t);let Me=$t.get(qt);if(Me!==void 0){if(q.currentProgram===Me&&q.lightsStateVersion===kt)return ve(w,Lt),Me}else Lt.uniforms=bt.getUniforms(w),N!==null&&w.isNodeMaterial&&N.build(w,Q,Lt),w.onBeforeCompile(Lt,I),Me=bt.acquireProgram(Lt,qt),$t.set(qt,Me),q.uniforms=Lt.uniforms;let Yt=q.uniforms;return(!w.isShaderMaterial&&!w.isRawShaderMaterial||w.clipping===!0)&&(Yt.clippingPlanes=Bt.uniform),ve(w,Lt),q.needsLights=Zn(w),q.lightsStateVersion=kt,q.needsLights&&(Yt.ambientLightColor.value=Z.state.ambient,Yt.lightProbe.value=Z.state.probe,Yt.sunLights.value=Z.state.sun,Yt.sunLightShadows.value=Z.state.sunShadow,Yt.directionalLights.value=Z.state.directional,Yt.directionalLightShadows.value=Z.state.directionalShadow,Yt.spotLights.value=Z.state.spot,Yt.spotLightShadows.value=Z.state.spotShadow,Yt.rectAreaLights.value=Z.state.rectArea,Yt.ltc_1.value=Z.state.rectAreaLTC1,Yt.ltc_2.value=Z.state.rectAreaLTC2,Yt.pointLights.value=Z.state.point,Yt.pointLightShadows.value=Z.state.pointShadow,Yt.hemisphereLights.value=Z.state.hemi,Yt.sunShadowMatrix.value=Z.state.sunShadowMatrix,Yt.sunShadowCascade.value=Z.state.sunShadowCascade,Yt.directionalShadowMatrix.value=Z.state.directionalShadowMatrix,Yt.spotLightMatrix.value=Z.state.spotLightMatrix,Yt.spotLightMap.value=Z.state.spotLightMap,Yt.pointShadowMatrix.value=Z.state.pointShadowMatrix),q.lightProbeGrid=M.state.lightProbeGridArray.length>0,q.currentProgram=Me,q.uniformsList=null,Me}function te(w){if(w.uniformsList===null){let z=w.currentProgram.getUniforms();w.uniformsList=fr.seqWithValue(z.seq,w.uniforms)}return w.uniformsList}function ve(w,z){let Q=X.get(w);Q.outputColorSpace=z.outputColorSpace,Q.batching=z.batching,Q.batchingColor=z.batchingColor,Q.instancing=z.instancing,Q.instancingColor=z.instancingColor,Q.instancingMorph=z.instancingMorph,Q.skinning=z.skinning,Q.morphTargets=z.morphTargets,Q.morphNormals=z.morphNormals,Q.morphColors=z.morphColors,Q.morphTargetsCount=z.morphTargetsCount,Q.numClippingPlanes=z.numClippingPlanes,Q.numIntersection=z.numClipIntersection,Q.vertexAlphas=z.vertexAlphas,Q.vertexTangents=z.vertexTangents,Q.toneMapping=z.toneMapping}function Qe(w,z){if(w.length===0)return null;if(w.length===1)return w[0].texture!==null?w[0]:null;v.setFromMatrixPosition(z.matrixWorld);for(let Q=0,q=w.length;Q<q;Q++){let Z=w[Q];if(Z.texture!==null&&Z.boundingBox.containsPoint(v))return Z}return null}function wi(w,z,Q,q,Z){z.isScene!==!0&&(z=St),tt.resetTextureUnits();let Ut=z.fog,kt=q.isMeshStandardMaterial||q.isMeshLambertMaterial||q.isMeshPhongMaterial?z.environment:null,Lt=W===null?I.outputColorSpace:W.isXRRenderTarget===!0?W.texture.colorSpace:Se.workingColorSpace,qt=q.isMeshStandardMaterial||q.isMeshLambertMaterial&&!q.envMap||q.isMeshPhongMaterial&&!q.envMap,$t=ct.get(q.envMap||kt,qt),pe=q.vertexColors===!0&&!!Q.attributes.color&&Q.attributes.color.itemSize===4,Me=!!Q.attributes.tangent&&(!!q.normalMap||q.anisotropy>0),Yt=!!Q.morphAttributes.position,Te=!!Q.morphAttributes.normal,Ye=!!Q.morphAttributes.color,ze=zn;q.toneMapped&&(W===null||W.isXRRenderTarget===!0)&&(ze=I.toneMapping);let De=Q.morphAttributes.position||Q.morphAttributes.normal||Q.morphAttributes.color,hn=De!==void 0?De.length:0,zt=X.get(q),xn=M.state.lights;if(ut===!0&&(Y===!0||w!==K)){let Ne=w===K&&q.id===G;Bt.setState(q,w,Ne)}let Ee=!1;q.version===zt.__version?(zt.needsLights&&zt.lightsStateVersion!==xn.state.version||zt.outputColorSpace!==Lt||Z.isBatchedMesh&&zt.batching===!1||!Z.isBatchedMesh&&zt.batching===!0||Z.isBatchedMesh&&zt.batchingColor===!0&&Z._colorsTexture===null||Z.isBatchedMesh&&zt.batchingColor===!1&&Z._colorsTexture!==null||Z.isInstancedMesh&&zt.instancing===!1||!Z.isInstancedMesh&&zt.instancing===!0||Z.isSkinnedMesh&&zt.skinning===!1||!Z.isSkinnedMesh&&zt.skinning===!0||Z.isInstancedMesh&&zt.instancingColor===!0&&Z.instanceColor===null||Z.isInstancedMesh&&zt.instancingColor===!1&&Z.instanceColor!==null||Z.isInstancedMesh&&zt.instancingMorph===!0&&Z.morphTexture===null||Z.isInstancedMesh&&zt.instancingMorph===!1&&Z.morphTexture!==null||zt.envMap!==$t||q.fog===!0&&zt.fog!==Ut||zt.numClippingPlanes!==void 0&&(zt.numClippingPlanes!==Bt.numPlanes||zt.numIntersection!==Bt.numIntersection)||zt.vertexAlphas!==pe||zt.vertexTangents!==Me||zt.morphTargets!==Yt||zt.morphNormals!==Te||zt.morphColors!==Ye||zt.toneMapping!==ze||zt.morphTargetsCount!==hn||!!zt.lightProbeGrid!=M.state.lightProbeGridArray.length>0)&&(Ee=!0):(Ee=!0,zt.__version=q.version);let Bn=zt.currentProgram;Ee===!0&&(Bn=Gt(q,z,Z),N&&q.isNodeMaterial&&N.onUpdateProgram(q,Bn,zt));let li=!1,Bi=!1,Rs=!1,Ie=Bn.getUniforms(),We=zt.uniforms;if(y.useProgram(Bn.program)&&(li=!0,Bi=!0,Rs=!0),q.id!==G&&(G=q.id,Bi=!0),zt.needsLights){let Ne=Qe(M.state.lightProbeGridArray,Z);zt.lightProbeGrid!==Ne&&(zt.lightProbeGrid=Ne,Bi=!0)}if(li||K!==w){y.buffers.depth.getReversed()&&w.reversedDepth!==!0&&(w._reversedDepth=!0,w.updateProjectionMatrix()),Ie.setValue(F,"projectionMatrix",w.projectionMatrix),Ie.setValue(F,"viewMatrix",w.matrixWorldInverse);let Hi=Ie.map.cameraPosition;Hi!==void 0&&Hi.setValue(F,vt.setFromMatrixPosition(w.matrixWorld)),C.logarithmicDepthBuffer&&Ie.setValue(F,"logDepthBufFC",2/(Math.log(w.far+1)/Math.LN2)),(q.isMeshPhongMaterial||q.isMeshToonMaterial||q.isMeshLambertMaterial||q.isMeshBasicMaterial||q.isMeshStandardMaterial||q.isShaderMaterial)&&Ie.setValue(F,"isOrthographic",w.isOrthographicCamera===!0),K!==w&&(K=w,Bi=!0,Rs=!0)}if(zt.needsLights&&(xn.state.sunShadowMap.length>0&&Ie.setValue(F,"sunShadowMap",xn.state.sunShadowMap,tt),xn.state.directionalShadowMap.length>0&&Ie.setValue(F,"directionalShadowMap",xn.state.directionalShadowMap,tt),xn.state.spotShadowMap.length>0&&Ie.setValue(F,"spotShadowMap",xn.state.spotShadowMap,tt),xn.state.pointShadowMap.length>0&&Ie.setValue(F,"pointShadowMap",xn.state.pointShadowMap,tt)),Z.isSkinnedMesh){Ie.setOptional(F,Z,"bindMatrix"),Ie.setOptional(F,Z,"bindMatrixInverse");let Ne=Z.skeleton;Ne&&(Ne.boneTexture===null&&Ne.computeBoneTexture(),Ie.setValue(F,"boneTexture",Ne.boneTexture,tt))}Z.isBatchedMesh&&(Ie.setOptional(F,Z,"batchingTexture"),Ie.setValue(F,"batchingTexture",Z._matricesTexture,tt),Ie.setOptional(F,Z,"batchingIdTexture"),Ie.setValue(F,"batchingIdTexture",Z._indirectTexture,tt),Ie.setOptional(F,Z,"batchingColorTexture"),Z._colorsTexture!==null&&Ie.setValue(F,"batchingColorTexture",Z._colorsTexture,tt));let ki=Q.morphAttributes;if((ki.position!==void 0||ki.normal!==void 0||ki.color!==void 0)&&R.update(Z,Q,Bn),(Bi||zt.receiveShadow!==Z.receiveShadow)&&(zt.receiveShadow=Z.receiveShadow,Ie.setValue(F,"receiveShadow",Z.receiveShadow)),(q.isMeshStandardMaterial||q.isMeshLambertMaterial||q.isMeshPhongMaterial)&&q.envMap===null&&z.environment!==null&&(We.envMapIntensity.value=z.environmentIntensity),We.dfgLUT!==void 0&&(We.dfgLUT.value=Bx()),Bi){if(Ie.setValue(F,"toneMappingExposure",I.toneMappingExposure),zt.needsLights&&In(We,Rs),Ut&&q.fog===!0&&Wt.refreshFogUniforms(We,Ut),Wt.refreshMaterialUniforms(We,q,V,U,M.state.transmissionRenderTarget[w.id]),zt.needsLights&&zt.lightProbeGrid){let Ne=zt.lightProbeGrid;We.probesSH.value=Ne.texture,We.probesMin.value.copy(Ne.boundingBox.min),We.probesMax.value.copy(Ne.boundingBox.max),We.probesResolution.value.copy(Ne.resolution)}fr.upload(F,te(zt),We,tt)}if(q.isShaderMaterial&&q.uniformsNeedUpdate===!0&&(fr.upload(F,te(zt),We,tt),q.uniformsNeedUpdate=!1),q.isSpriteMaterial&&Ie.setValue(F,"center",Z.center),Ie.setValue(F,"modelViewMatrix",Z.modelViewMatrix),Ie.setValue(F,"normalMatrix",Z.normalMatrix),Ie.setValue(F,"modelMatrix",Z.matrixWorld),q.uniformsGroups!==void 0){let Ne=q.uniformsGroups;for(let Hi=0,Cs=Ne.length;Hi<Cs;Hi++){let zh=Ne[Hi];et.update(zh,Bn),et.bind(zh,Bn)}}return Bn}function In(w,z){w.ambientLightColor.needsUpdate=z,w.lightProbe.needsUpdate=z,w.sunLights.needsUpdate=z,w.sunLightShadows.needsUpdate=z,w.directionalLights.needsUpdate=z,w.directionalLightShadows.needsUpdate=z,w.pointLights.needsUpdate=z,w.pointLightShadows.needsUpdate=z,w.spotLights.needsUpdate=z,w.spotLightShadows.needsUpdate=z,w.rectAreaLights.needsUpdate=z,w.hemisphereLights.needsUpdate=z}function Zn(w){return w.isMeshLambertMaterial||w.isMeshToonMaterial||w.isMeshPhongMaterial||w.isMeshStandardMaterial||w.isShadowMaterial||w.isShaderMaterial&&w.lights===!0}this.getActiveCubeFace=function(){return $},this.getActiveMipmapLevel=function(){return J},this.getRenderTarget=function(){return W},this.setRenderTargetTextures=function(w,z,Q){let q=X.get(w);q.__autoAllocateDepthBuffer=w.resolveDepthBuffer===!1,q.__autoAllocateDepthBuffer===!1&&(q.__useRenderToTexture=!1),X.get(w.texture).__webglTexture=z,X.get(w.depthTexture).__webglTexture=q.__autoAllocateDepthBuffer?void 0:Q,q.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(w,z){let Q=X.get(w);Q.__webglFramebuffer=z,Q.__useDefaultFramebuffer=z===void 0},this.setRenderTarget=function(w,z=0,Q=0){W=w,$=z,J=Q;let q=null,Z=!1,Ut=!1;if(w){let Lt=X.get(w);if(Lt.__useDefaultFramebuffer!==void 0){y.bindFramebuffer(F.FRAMEBUFFER,Lt.__webglFramebuffer),nt.copy(w.viewport),Et.copy(w.scissor),pt=w.scissorTest,y.viewport(nt),y.scissor(Et),y.setScissorTest(pt),G=-1;return}else if(Lt.__webglFramebuffer===void 0)tt.setupRenderTarget(w);else if(Lt.__hasExternalTextures)tt.rebindTextures(w,X.get(w.texture).__webglTexture,X.get(w.depthTexture).__webglTexture);else if(w.depthBuffer){let pe=w.depthTexture;if(Lt.__boundDepthTexture!==pe){if(pe!==null&&X.has(pe)&&(w.width!==pe.image.width||w.height!==pe.image.height))throw new Error("THREE.WebGLRenderer: Attached DepthTexture is initialized to the incorrect size.");tt.setupDepthRenderbuffer(w)}}let qt=w.texture;(qt.isData3DTexture||qt.isDataArrayTexture||qt.isCompressedArrayTexture)&&(Ut=!0);let $t=X.get(w).__webglFramebuffer;w.isWebGLCubeRenderTarget?(Array.isArray($t[z])?q=$t[z][Q]:q=$t[z],Z=!0):w.samples>0&&tt.useMultisampledRTT(w)===!1?q=X.get(w).__webglMultisampledFramebuffer:Array.isArray($t)?q=$t[Q]:q=$t,nt.copy(w.viewport),Et.copy(w.scissor),pt=w.scissorTest}else nt.copy(yt).multiplyScalar(V).floor(),Et.copy(It).multiplyScalar(V).floor(),pt=Kt;if(Q!==0&&(q=B),y.bindFramebuffer(F.FRAMEBUFFER,q)&&y.drawBuffers(w,q),y.viewport(nt),y.scissor(Et),y.setScissorTest(pt),Z){let Lt=X.get(w.texture);F.framebufferTexture2D(F.FRAMEBUFFER,F.COLOR_ATTACHMENT0,F.TEXTURE_CUBE_MAP_POSITIVE_X+z,Lt.__webglTexture,Q)}else if(Ut){let Lt=z;for(let qt=0;qt<w.textures.length;qt++){let $t=X.get(w.textures[qt]);F.framebufferTextureLayer(F.FRAMEBUFFER,F.COLOR_ATTACHMENT0+qt,$t.__webglTexture,Q,Lt)}}else if(w!==null&&Q!==0){let Lt=X.get(w.texture);F.framebufferTexture2D(F.FRAMEBUFFER,F.COLOR_ATTACHMENT0,F.TEXTURE_2D,Lt.__webglTexture,Q)}G=-1};function ci(w){let z=X.get(w);return(z.__readFormat!==w.format||z.__readType!==w.type)&&(z.__readFormat=w.format,z.__readType=w.type,z.__formatReadable=C.textureFormatReadable(w.format),z.__typeReadable=C.textureTypeReadable(w.type)),z}this.readRenderTargetPixels=function(w,z,Q,q,Z,Ut,kt,Lt=0){if(!(w&&w.isWebGLRenderTarget)){se("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let qt=X.get(w).__webglFramebuffer;if(w.isWebGLCubeRenderTarget&&kt!==void 0&&(qt=qt[kt]),qt){y.bindFramebuffer(F.FRAMEBUFFER,qt);try{let $t=w.textures[Lt],pe=$t.format,Me=$t.type;w.textures.length>1&&F.readBuffer(F.COLOR_ATTACHMENT0+Lt);let Yt=ci($t);if(Yt.__formatReadable===!1){se("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(Yt.__typeReadable===!1){se("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}z>=0&&z<=w.width-q&&Q>=0&&Q<=w.height-Z&&F.readPixels(z,Q,q,Z,at.convert(pe),at.convert(Me),Ut)}finally{let $t=W!==null?X.get(W).__webglFramebuffer:null;y.bindFramebuffer(F.FRAMEBUFFER,$t)}}},this.readRenderTargetPixelsAsync=async function(w,z,Q,q,Z,Ut,kt,Lt=0){if(!(w&&w.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let qt=X.get(w).__webglFramebuffer;if(w.isWebGLCubeRenderTarget&&kt!==void 0&&(qt=qt[kt]),qt)if(z>=0&&z<=w.width-q&&Q>=0&&Q<=w.height-Z){y.bindFramebuffer(F.FRAMEBUFFER,qt);let $t=w.textures[Lt],pe=$t.format,Me=$t.type;w.textures.length>1&&F.readBuffer(F.COLOR_ATTACHMENT0+Lt);let Yt=ci($t);if(Yt.__formatReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(Yt.__typeReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let Te=F.createBuffer();F.bindBuffer(F.PIXEL_PACK_BUFFER,Te),F.bufferData(F.PIXEL_PACK_BUFFER,Ut.byteLength,F.STREAM_READ),F.readPixels(z,Q,q,Z,at.convert(pe),at.convert(Me),0),F.bindBuffer(F.PIXEL_PACK_BUFFER,null);let Ye=W!==null?X.get(W).__webglFramebuffer:null;y.bindFramebuffer(F.FRAMEBUFFER,Ye);let ze=F.fenceSync(F.SYNC_GPU_COMMANDS_COMPLETE,0);return F.flush(),await Qu(F,ze,4),F.bindBuffer(F.PIXEL_PACK_BUFFER,Te),F.getBufferSubData(F.PIXEL_PACK_BUFFER,0,Ut),F.bindBuffer(F.PIXEL_PACK_BUFFER,null),F.deleteBuffer(Te),F.deleteSync(ze),Ut}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(w,z=null,Q=0){let q=Math.pow(2,-Q),Z=Math.floor(w.image.width*q),Ut=Math.floor(w.image.height*q),kt=z!==null?z.x:0,Lt=z!==null?z.y:0;tt.setTexture2D(w,0),F.copyTexSubImage2D(F.TEXTURE_2D,Q,0,0,kt,Lt,Z,Ut),y.unbindTexture()},this.copyTextureToTexture=function(w,z,Q=null,q=null,Z=0,Ut=0){let kt,Lt,qt,$t,pe,Me,Yt,Te,Ye,ze=w.isCompressedTexture?w.mipmaps[Ut]:w.image;if(Q!==null)kt=Q.max.x-Q.min.x,Lt=Q.max.y-Q.min.y,qt=Q.isBox3?Q.max.z-Q.min.z:1,$t=Q.min.x,pe=Q.min.y,Me=Q.isBox3?Q.min.z:0;else{let We=Math.pow(2,-Z);kt=Math.floor(ze.width*We),Lt=Math.floor(ze.height*We),w.isDataArrayTexture?qt=ze.depth:w.isData3DTexture?qt=Math.floor(ze.depth*We):qt=1,$t=0,pe=0,Me=0}q!==null?(Yt=q.x,Te=q.y,Ye=q.z):(Yt=0,Te=0,Ye=0);let De=at.convert(z.format),hn=at.convert(z.type),zt;z.isData3DTexture?(tt.setTexture3D(z,0),zt=F.TEXTURE_3D):z.isDataArrayTexture||z.isCompressedArrayTexture?(tt.setTexture2DArray(z,0),zt=F.TEXTURE_2D_ARRAY):(tt.setTexture2D(z,0),zt=F.TEXTURE_2D),y.activeTexture(F.TEXTURE0),y.pixelStorei(F.UNPACK_FLIP_Y_WEBGL,z.flipY),y.pixelStorei(F.UNPACK_PREMULTIPLY_ALPHA_WEBGL,z.premultiplyAlpha),y.pixelStorei(F.UNPACK_ALIGNMENT,z.unpackAlignment);let xn=y.getParameter(F.UNPACK_ROW_LENGTH),Ee=y.getParameter(F.UNPACK_IMAGE_HEIGHT),Bn=y.getParameter(F.UNPACK_SKIP_PIXELS),li=y.getParameter(F.UNPACK_SKIP_ROWS),Bi=y.getParameter(F.UNPACK_SKIP_IMAGES);y.pixelStorei(F.UNPACK_ROW_LENGTH,ze.width),y.pixelStorei(F.UNPACK_IMAGE_HEIGHT,ze.height),y.pixelStorei(F.UNPACK_SKIP_PIXELS,$t),y.pixelStorei(F.UNPACK_SKIP_ROWS,pe),y.pixelStorei(F.UNPACK_SKIP_IMAGES,Me);let Rs=w.isDataArrayTexture||w.isData3DTexture,Ie=z.isDataArrayTexture||z.isData3DTexture;if(w.isDepthTexture){let We=X.get(w),ki=X.get(z),Ne=X.get(We.__renderTarget),Hi=X.get(ki.__renderTarget);y.bindFramebuffer(F.READ_FRAMEBUFFER,Ne.__webglFramebuffer),y.bindFramebuffer(F.DRAW_FRAMEBUFFER,Hi.__webglFramebuffer);for(let Cs=0;Cs<qt;Cs++)Rs&&(F.framebufferTextureLayer(F.READ_FRAMEBUFFER,F.COLOR_ATTACHMENT0,X.get(w).__webglTexture,Z,Me+Cs),F.framebufferTextureLayer(F.DRAW_FRAMEBUFFER,F.COLOR_ATTACHMENT0,X.get(z).__webglTexture,Ut,Ye+Cs)),F.blitFramebuffer($t,pe,kt,Lt,Yt,Te,kt,Lt,F.DEPTH_BUFFER_BIT,F.NEAREST);y.bindFramebuffer(F.READ_FRAMEBUFFER,null),y.bindFramebuffer(F.DRAW_FRAMEBUFFER,null)}else if(Z!==0||w.isRenderTargetTexture||X.has(w)){let We=X.get(w),ki=X.get(z);y.bindFramebuffer(F.READ_FRAMEBUFFER,D),y.bindFramebuffer(F.DRAW_FRAMEBUFFER,O);for(let Ne=0;Ne<qt;Ne++)Rs?F.framebufferTextureLayer(F.READ_FRAMEBUFFER,F.COLOR_ATTACHMENT0,We.__webglTexture,Z,Me+Ne):F.framebufferTexture2D(F.READ_FRAMEBUFFER,F.COLOR_ATTACHMENT0,F.TEXTURE_2D,We.__webglTexture,Z),Ie?F.framebufferTextureLayer(F.DRAW_FRAMEBUFFER,F.COLOR_ATTACHMENT0,ki.__webglTexture,Ut,Ye+Ne):F.framebufferTexture2D(F.DRAW_FRAMEBUFFER,F.COLOR_ATTACHMENT0,F.TEXTURE_2D,ki.__webglTexture,Ut),Z!==0?F.blitFramebuffer($t,pe,kt,Lt,Yt,Te,kt,Lt,F.COLOR_BUFFER_BIT,F.NEAREST):Ie?F.copyTexSubImage3D(zt,Ut,Yt,Te,Ye+Ne,$t,pe,kt,Lt):F.copyTexSubImage2D(zt,Ut,Yt,Te,$t,pe,kt,Lt);y.bindFramebuffer(F.READ_FRAMEBUFFER,null),y.bindFramebuffer(F.DRAW_FRAMEBUFFER,null)}else Ie?w.isDataTexture||w.isData3DTexture?F.texSubImage3D(zt,Ut,Yt,Te,Ye,kt,Lt,qt,De,hn,ze.data):z.isCompressedArrayTexture?F.compressedTexSubImage3D(zt,Ut,Yt,Te,Ye,kt,Lt,qt,De,ze.data):F.texSubImage3D(zt,Ut,Yt,Te,Ye,kt,Lt,qt,De,hn,ze):w.isDataTexture?F.texSubImage2D(F.TEXTURE_2D,Ut,Yt,Te,kt,Lt,De,hn,ze.data):w.isCompressedTexture?F.compressedTexSubImage2D(F.TEXTURE_2D,Ut,Yt,Te,ze.width,ze.height,De,ze.data):F.texSubImage2D(F.TEXTURE_2D,Ut,Yt,Te,kt,Lt,De,hn,ze);y.pixelStorei(F.UNPACK_ROW_LENGTH,xn),y.pixelStorei(F.UNPACK_IMAGE_HEIGHT,Ee),y.pixelStorei(F.UNPACK_SKIP_PIXELS,Bn),y.pixelStorei(F.UNPACK_SKIP_ROWS,li),y.pixelStorei(F.UNPACK_SKIP_IMAGES,Bi),Ut===0&&z.generateMipmaps&&F.generateMipmap(zt),y.unbindTexture()},this.initRenderTarget=function(w){X.get(w).__webglFramebuffer===void 0&&tt.setupRenderTarget(w)},this.initTexture=function(w){w.isCubeTexture?tt.setTextureCube(w,0):w.isData3DTexture?tt.setTexture3D(w,0):w.isDataArrayTexture||w.isCompressedArrayTexture?tt.setTexture2DArray(w,0):tt.setTexture2D(w,0),y.unbindTexture()},this.resetState=function(){$=0,J=0,W=null,y.reset(),xt.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return ei}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(t){this._outputColorSpace=t;let e=this.getContext();e.drawingBufferColorSpace=Se._getDrawingBufferColorSpace(t),e.unpackColorSpace=Se._getUnpackColorSpace()}};var Fe=(i,t=0,e=1)=>Math.min(e,Math.max(t,i)),fe=(i,t,e)=>i+(t-i)*e,be=(i,t,e)=>{let n=Fe((e-i)/(t-i));return n*n*(3-2*n)},Fd=(i,t,e)=>{let n=Fe((e-i)/(t-i));return n*n*n*(n*(n*6-15)+10)},En=(i,t,e,n,s)=>be(t,e,i)*(1-be(n,s,i));function mn(i=1){let t=i>>>0;return()=>{t=t+1831565813>>>0;let e=t;return e=Math.imul(e^e>>>15,e|1),e^=e+Math.imul(e^e>>>7,e|61),((e^e>>>14)>>>0)/4294967296}}function Xn(i=7){let t=new Uint8Array(512),e=mn(i),n=[...Array(256).keys()];for(let a=255;a>0;a--){let o=Math.floor(e()*(a+1));[n[a],n[o]]=[n[o],n[a]]}for(let a=0;a<512;a++)t[a]=n[a&255];let s=new Float32Array(256).map(()=>e()*2-1),r=a=>a*a*a*(a*(a*6-15)+10);return(a,o)=>{let c=Math.floor(a),l=Math.floor(o),h=a-c,d=o-l,u=c&255,f=l&255,g=s[t[t[u]+f]],x=s[t[t[u+1]+f]],p=s[t[t[u]+f+1]],m=s[t[t[u+1]+f+1]],S=r(h),E=r(d);return fe(fe(g,x,S),fe(p,m,S),E)}}function wn(i,t,e,n=4,s=2,r=.5){let a=0,o=1,c=0;for(let l=0;l<n;l++)a+=i(t,e)*o,c+=o,t*=s,e*=s,o*=r;return a/c}function Be(i,t){let e=document.createElement("canvas");return e.width=i,e.height=t,[e,e.getContext("2d")]}function Ve(i,{srgb:t=!0,ponavljaj:e=!1,aniz:n=8}={}){let s=new jr(i);return t&&(s.colorSpace=yn),e&&(s.wrapS=s.wrapT=js),s.anisotropy=n,s}function Aa(i,t=2){let e=i.width,n=i.height,s=i.getContext("2d").getImageData(0,0,e,n).data,[r,a]=Be(e,n),o=a.createImageData(e,n),c=(l,h)=>s[((h+n)%n*e+(l+e)%e)*4]/255;for(let l=0;l<n;l++)for(let h=0;h<e;h++){let d=c(h+1,l-1)+2*c(h+1,l)+c(h+1,l+1)-(c(h-1,l-1)+2*c(h-1,l)+c(h-1,l+1)),u=c(h-1,l+1)+2*c(h,l+1)+c(h+1,l+1)-(c(h-1,l-1)+2*c(h,l-1)+c(h+1,l-1)),f=new P(-d*t,u*t,1).normalize(),g=(l*e+h)*4;o.data[g]=(f.x*.5+.5)*255,o.data[g+1]=(f.y*.5+.5)*255,o.data[g+2]=(f.z*.5+.5)*255,o.data[g+3]=255}return a.putImageData(o,0,0),r}function ie(i,t,e,n=.02,s=2){let r=new Re(i,t,e,1,1,1);return n<=0?r:kx(i,t,e,n,s)}function kx(i,t,e,n,s){let r=new Re(i,t,e,s*2+1,s*2+1,s*2+1),a=r.attributes.position,o=new P,c=new P,l=i/2-n,h=t/2-n,d=e/2-n;for(let u=0;u<a.count;u++){o.fromBufferAttribute(a,u),c.set(Fe(o.x,-l,l),Fe(o.y,-h,h),Fe(o.z,-d,d));let f=o.clone().sub(c);f.lengthSq()>1e-12&&o.copy(c).add(f.normalize().multiplyScalar(n)),a.setXYZ(u,o.x,o.y,o.z)}return r.computeVertexNormals(),r}function ke(i){let t=[];for(let[s,r,a]of i){let o=s.index?s.toNonIndexed():s.clone();a&&o.applyMatrix4(a);let c=o.attributes.position.count,l=new Float32Array(c*3),h=new Ot(r);for(let d=0;d<c;d++)l.set([h.r,h.g,h.b],d*3);o.setAttribute("color",new Pe(l,3));for(let d of Object.keys(o.attributes))["position","normal","color","uv"].includes(d)||o.deleteAttribute(d);o.attributes.uv||o.setAttribute("uv",new Pe(new Float32Array(c*2),2)),t.push(o)}let e=t.reduce((s,r)=>s+r.attributes.position.count,0),n=new _e;for(let[s,r]of[["position",3],["normal",3],["color",3],["uv",2]]){let a=new Float32Array(e*r),o=0;for(let c of t)a.set(c.attributes[s].array,o),o+=c.attributes[s].array.length;n.setAttribute(s,new Pe(a,r))}return n}var Ht=(i=0,t=0,e=0,n=0,s=0,r=0,a=1)=>{let o=new ue;return o.compose(new P(i,t,e),new nn().setFromEuler(new ni(n,s,r)),new P(a,a,a)),o};function Oc(i){let t=i.length,e=i[0].v.length,n=i.map((s,r)=>{if(s.mir)return new Array(e).fill(0);let a=i[Math.max(0,r-1)],o=i[Math.min(t-1,r+1)],c=o.t-a.t||1;return s.v.map((l,h)=>{let d=(o.v[h]-a.v[h])/c;if(r===0||r===t-1)return d;let u=(s.v[h]-a.v[h])/(s.t-a.t||1),f=(o.v[h]-s.v[h])/(o.t-s.t||1);if(u*f<=0)return 0;let g=3*Math.min(Math.abs(u),Math.abs(f));return Math.sign(d)*Math.min(Math.abs(d),g)})});return(s,r=new Array(e))=>{if(s<=i[0].t){for(let m=0;m<e;m++)r[m]=i[0].v[m];return r}if(s>=i[t-1].t){for(let m=0;m<e;m++)r[m]=i[t-1].v[m];return r}let a=0;for(;i[a+1].t<s;)a++;let o=i[a],c=i[a+1],l=c.t-o.t,h=(s-o.t)/l,d=h*h,u=d*h,f=2*u-3*d+1,g=u-2*d+h,x=-2*u+3*d,p=u-d;for(let m=0;m<e;m++)r[m]=f*o.v[m]+g*l*n[a][m]+x*c.v[m]+p*l*n[a+1][m];return r}}var Th=`
uniform vec3 uSonce;
uniform vec3 uZenit, uObzorje, uSij, uSoncBarva;
uniform float uMeglaGost, uMeglaVis, uMeglaY0, uOblaki, uCasN, uZvezde, uMeglaMax;
float nhash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float nsum(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(nhash(i), nhash(i + vec2(1, 0)), f.x), mix(nhash(i + vec2(0, 1)), nhash(i + vec2(1, 1)), f.x), f.y);
}
float nfbm(vec2 p) {
  float s = 0.0, a = 0.5;
  for (int i = 0; i < 4; i++) { s += a * nsum(p); p = p * 2.03 + vec2(1.7, 9.2); a *= 0.5; }
  return s;
}
vec3 neboBarva(vec3 d, float disk) {
  float y = d.y;
  float t = pow(clamp(y, 0.0, 1.0), 0.5);
  vec3 c = mix(uObzorje, uZenit, t);
  float mu = max(dot(d, uSonce), 0.0);
  float nadObz = smoothstep(-0.06, 0.02, uSonce.y);
  c += uSij * (pow(mu, 6.0) * 0.45 + pow(mu, 48.0) * 0.55) * nadObz;
  c += uSoncBarva * smoothstep(0.99955, 0.99985, mu) * 30.0 * disk * nadObz;
  // pod obzorjem: zemeljska izparina
  c = mix(c, uObzorje * 0.82, smoothstep(0.0, -0.12, y));
  return c;
}
vec3 atmosfera(vec3 col, vec3 cam, vec3 v) {
  float dist = length(v);
  vec3 d = v / max(dist, 1e-4);
  float b = uMeglaVis;
  float h0 = max(cam.y - uMeglaY0, -50.0);
  float ry = d.y;
  float k = abs(ry * dist * b) > 1e-4 ? (1.0 - exp(-ry * dist * b)) / (ry * b) : dist;
  float kol = uMeglaGost * exp(-h0 * b) * k;
  float f = 1.0 - exp(-max(kol, 0.0));
  f = min(f, uMeglaMax);
  vec3 m = neboBarva(normalize(vec3(d.x, max(d.y, 0.0) * 0.6, d.z)), 0.0);
  return mix(col, m, f);
}
`,Ah=Th,Bc={zora:{sonceVis:6.5,sonceAz:104,zenit:"#6f93c4",obzorje:"#e7c9ae",sij:"#ffb36b",soncBarva:"#ffd9a8",sonceI:2.7,sonceC:"#ffc890",nebI:.62,nebZg:"#a9c4e6",nebSp:"#6e6252",meglaGost:.0019,meglaVis:.022,meglaY0:0,meglaMax:.97,oblaki:.42,zvezde:0,izp:1,okolje:.65},jutro:{sonceVis:12,sonceAz:112,zenit:"#5d8cc8",obzorje:"#dcd6cc",sij:"#ffd29a",soncBarva:"#fff0d8",sonceI:2.9,sonceC:"#ffe4bf",nebI:.7,nebZg:"#b5cdea",nebSp:"#6f6a5c",meglaGost:9e-4,meglaVis:.012,meglaY0:0,meglaMax:.95,oblaki:.38,zvezde:0,izp:1,okolje:.75},noc:{sonceVis:28,sonceAz:210,zenit:"#050a16",obzorje:"#17233a",sij:"#30486e",soncBarva:"#9fb4d8",sonceI:.38,sonceC:"#9db6e8",nebI:.24,nebZg:"#2a3c62",nebSp:"#0c0e12",meglaGost:.0014,meglaVis:.016,meglaY0:0,meglaMax:.9,oblaki:.2,zvezde:1,izp:1.15,okolje:.35}},zd=new Ot,Od=new Ot;function Bd(i,t,e){let n={};for(let s of Object.keys(i))typeof i[s]=="string"?(zd.set(i[s]),Od.set(t[s]),n[s]=zd.clone().lerp(Od,e)):n[s]=fe(i[s],t[s],e);return n}var kc=class{constructor(){this.U={uSonce:{value:new P(0,.1,1)},uZenit:{value:new Ot},uObzorje:{value:new Ot},uSij:{value:new Ot},uSoncBarva:{value:new Ot},uMeglaGost:{value:.002},uMeglaVis:{value:.02},uMeglaY0:{value:0},uMeglaMax:{value:1},uOblaki:{value:.4},uCasN:{value:0},uZvezde:{value:0}};let t=new Ue({uniforms:this.U,vertexShader:`
        varying vec3 vSmer;
        void main() {
          vSmer = normalize((modelMatrix * vec4(position, 0.0)).xyz);
          vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          gl_Position = p.xyww;
        }`,fragmentShader:Th+`
        varying vec3 vSmer;
        void main() {
          vec3 d = normalize(vSmer);
          vec3 c = neboBarva(d, 1.0);
          // oblaki na ravnini 2,5 km, osvetljeni s strani sonca
          if (d.y > 0.01) {
            vec2 p = d.xz / d.y * 2.5 + vec2(uCasN * 0.004, uCasN * 0.0015);
            float n = nfbm(p * 0.55);
            float pokr = smoothstep(1.0 - uOblaki, 1.0 - uOblaki + 0.35, n);
            float mu = max(dot(d, uSonce), 0.0);
            vec3 oc = mix(uObzorje * 1.05, uSij * 1.2 + uZenit * 0.3, 0.35 + 0.65 * pow(mu, 4.0));
            oc = mix(oc, uZenit * 0.6 + uObzorje * 0.5, smoothstep(0.55, 0.95, n) * 0.5);
            c = mix(c, oc, pokr * smoothstep(0.01, 0.12, d.y) * 0.85);
          }
          // zvezde pono\u010Di
          if (uZvezde > 0.0 && d.y > 0.0) {
            vec3 q = d * 420.0;
            vec3 iq = floor(q);
            float h = fract(sin(dot(iq, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
            float z = step(0.9965, h) * smoothstep(0.5, 0.0, length(fract(q) - 0.5));
            c += vec3(0.9, 0.95, 1.0) * z * uZvezde * smoothstep(0.02, 0.25, d.y) * (0.5 + 2.0 * fract(h * 91.0));
          }
          gl_FragColor = vec4(c, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,side:rn,depthWrite:!1,depthTest:!0});this.kupola=new ot(new Vn(1,48,24),t),this.kupola.scale.setScalar(9e3),this.kupola.frustumCulled=!1,this.kupola.renderOrder=-1e3,this.sonce=new ua("#fff",2),this.sonce.castShadow=!0,this.sonce.shadow.bias=-3e-4,this.sonce.shadow.normalBias=.03,this.nebesna=new oa("#bcd","#554",.6),this.stanje=null}popravi(t){if(t.userData.atm||!("fog"in t)||t.isShaderMaterial)return;t.userData.atm=!0;let e=t.onBeforeCompile,n=this.U;t.onBeforeCompile=(r,a)=>{e&&e.call(t,r,a),Object.assign(r.uniforms,n),r.vertexShader=r.vertexShader.replace("#include <fog_pars_vertex>",`#include <fog_pars_vertex>
varying vec3 vAtmPog;`).replace("#include <fog_vertex>",`#include <fog_vertex>
vAtmPog = mvPosition.xyz;`),r.fragmentShader=r.fragmentShader.replace("#include <fog_pars_fragment>",`#include <fog_pars_fragment>
varying vec3 vAtmPog;
`+Th).replace("#include <fog_fragment>",`#ifdef USE_FOG
 gl_FragColor.rgb = atmosfera(gl_FragColor.rgb, cameraPosition, (vec4(vAtmPog, 0.0) * viewMatrix).xyz);
#endif`)};let s=t.customProgramCacheKey.bind(t);t.customProgramCacheKey=()=>s()+"|atm",t.needsUpdate=!0}nastavi(t,e=null,n=0){let s=e?Bd(Bc[t],Bc[e],n):Bd(Bc[t],Bc[t],0),r=this.U,a=_i.degToRad(s.sonceVis),o=_i.degToRad(s.sonceAz);return r.uSonce.value.set(Math.sin(o)*Math.cos(a),Math.sin(a),-Math.cos(o)*Math.cos(a)),r.uZenit.value.copy(s.zenit),r.uObzorje.value.copy(s.obzorje),r.uSij.value.copy(s.sij),r.uSoncBarva.value.copy(s.soncBarva),r.uMeglaGost.value=s.meglaGost,r.uMeglaVis.value=s.meglaVis,r.uMeglaY0.value=s.meglaY0,r.uMeglaMax.value=s.meglaMax,r.uOblaki.value=s.oblaki,r.uZvezde.value=s.zvezde,this.sonce.color.copy(s.sonceC),this.sonce.intensity=s.sonceI,this.nebesna.color.copy(s.nebZg),this.nebesna.groundColor.copy(s.nebSp),this.nebesna.intensity=s.nebI,this.stanje=s,s}okolje(t){let e=new Di,n=this.kupola.clone();n.scale.setScalar(100),e.add(n);let s=new ot(new pi(90,32),new si({color:this.U.uObzorje.value.clone().multiplyScalar(.35)}));s.rotation.x=-Math.PI/2,s.position.y=-2,e.add(s);let r=new pr(t),a=t.toneMapping;t.toneMapping=zn;let o=r.fromScene(e,0,.1,400);return t.toneMapping=a,r.dispose(),o.texture}};var kd=.7175,Hx=[[1400,0],[900,0],[500,0],[250,0],[0,0],[-250,0],[-480,0],[-800,-25],[-1150,-120],[-1550,-190],[-1950,-170],[-2350,-80],[-2750,-15],[-3050,0],[-3300,0],[-3600,0],[-4e3,0]];function Vd(){let i=new $i(Hx.map(([f,g])=>new P(f,0,g)),!1,"centripetal");i.arcLengthDivisions=4e3;let t=i.getLength(),e=4e3,n=[],s=[];for(let f=0;f<=e;f++){let g=f/e;n.push(i.getPointAt(g)),s.push(i.getTangentAt(g))}let r=(f,g=new P)=>{let x=Math.min(Math.max(f/t,0),1)*e,p=Math.min(Math.floor(x),e-1),m=x-p;return g.lerpVectors(n[p],n[p+1],m)},a=(f,g=new P)=>{let x=Math.min(Math.max(f/t,0),1)*e,p=Math.min(Math.floor(x),e-1),m=x-p;return g.lerpVectors(s[p],s[p+1],m).normalize()},o=f=>{let g=0,x=t;for(let p=0;p<40;p++){let m=(g+x)/2;r(m).x>f?g=m:x=m}return(g+x)/2},c=-4e3,l=1400,h=2,d=new Float32Array(Math.round((l-c)/h)+1);for(let f=0;f<d.length;f++)d[f]=r(o(c+f*h)).z;return{L:t,tocka:r,smer:a,sPriX:o,zPriX:f=>{let g=(Math.min(Math.max(f,c),l)-c)/h,x=Math.min(Math.floor(g),d.length-2),p=g-x;return d[x]*(1-p)+d[x+1]*p},krivulja:i}}var Rh=new P(0,1,0);function Ch(i,t=new P){return t.crossVectors(i,Rh).normalize()}function Vx(){let i=Xn(11),t=mn(5),e=256,[n,s]=Be(e,e),r=s.createImageData(e,e),a=[...Array(260)].map(()=>[t()*e,t()*e,.55+t()*.45,t()]);for(let c=0;c<e;c++)for(let l=0;l<e;l++){let h=1e9,d=1e9,u=0,f=0;for(let[S,E,v,b]of a)for(let[M,A]of[[0,0],[e,0],[-e,0],[0,e],[0,-e]]){let _=(l-S-M)**2+(c-E-A)**2;_<h?(d=h,h=_,u=v,f=b):_<d&&(d=_)}let g=Math.sqrt(d)-Math.sqrt(h),x=Math.min(1,g/5)*u*(.85+.15*wn(i,l/9,c/9,3)),p=(c*e+l)*4,m=f>.8?1:0;r.data[p]=(118+40*m)*x+18,r.data[p+1]=(114+22*m)*x+17,r.data[p+2]=(108+4*m)*x+16,r.data[p+3]=255}s.putImageData(r,0,0);let o=Aa(n,3);return{barva:Ve(n,{ponavljaj:!0}),normala:Ve(o,{srgb:!1,ponavljaj:!0})}}function Hd(i,t,e,n,s,r=0,a=1){let o=[],c=[],l=[],h=new P,d=new P,u=new P,f=Math.ceil((e-t)/n),g=s.length;for(let p=0;p<=f;p++){let m=t+(e-t)*p/f;i.tocka(m,h),i.smer(m,d),Ch(d,u);for(let[S,E,v]of s)o.push(h.x+u.x*(S+r),E,h.z+u.z*(S+r)),c.push(m/a,v);if(p<f)for(let S=0;S<g-1;S++){let E=p*g+S,v=E+g;l.push(E,v,E+1,E+1,v,v+1)}}let x=new _e;return x.setAttribute("position",new Jt(o,3)),x.setAttribute("uv",new Jt(c,2)),x.setIndex(l),x.computeVertexNormals(),x}function Gd(i,{atmU:t,NEBO:e}={}){let n=new oe,s=i.L,r=Vx();r.barva.repeat.set(1,1);let a=Hd(i,0,s,2,[[-3.4,-.85,0],[-2,-.22,.32],[2,-.22,.68],[3.4,-.85,1]],0,4),o=new Nt({map:r.barva,normalMap:r.normala,normalScale:new mt(1.2,1.2),roughness:.95,color:"#c9c4bc"});o.map.repeat.set(1,3),o.normalMap.repeat.set(1,3);let c=new ot(a,o);c.receiveShadow=!0,n.add(c);let l=[[-.075,-.17,0],[.075,-.17,.1],[.075,-.155,.2],[.012,-.14,.3],[.01,-.04,.4],[.036,-.03,.5],[.036,-.004,.6],[.026,0,.7],[-.026,0,.8],[-.036,-.004,.9],[-.036,-.03,.92],[-.01,-.04,.94],[-.012,-.14,.96],[-.075,-.155,.98],[-.075,-.17,1]],h=new Nt({color:"#7d6a5a",metalness:.75,roughness:.42});h.onBeforeCompile=W=>{W.fragmentShader=W.fragmentShader.replace("#include <color_fragment>",`#include <color_fragment>
        float _vrh = smoothstep(0.86, 0.97, dot(normalize(vNormal), normalize((viewMatrix * vec4(0.0, 1.0, 0.0, 0.0)).xyz)))
                   * (1.0 - smoothstep(35.0, 140.0, length(vViewPosition)));
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.74, 0.75, 0.77), _vrh);`).replace("#include <roughnessmap_fragment>",`#include <roughnessmap_fragment>
float _dal = smoothstep(30.0, 150.0, length(vViewPosition));
roughnessFactor = mix(mix(roughnessFactor, 0.2, _vrh), 0.8, _dal);`).replace("#include <metalnessmap_fragment>",`#include <metalnessmap_fragment>
metalnessFactor = mix(mix(metalnessFactor, 1.0, _vrh), 0.3, _dal);`)},h.customProgramCacheKey=()=>"tirnica",h.polygonOffset=!0,h.polygonOffsetFactor=-2,h.polygonOffsetUnits=-2;for(let W of[-kd,kd]){let G=Hd(i,0,s,2,l.map(([nt,Et,pt])=>[nt+W,Et,pt]),0,1),K=new ot(G,h);K.castShadow=!1,K.receiveShadow=!0,n.add(K)}let d=ie(.26,.19,2.6,.02),u=new Nt({color:"#a7a39b",roughness:.9});u.onBeforeCompile=W=>{W.fragmentShader=W.fragmentShader.replace("#include <color_fragment>",`#include <color_fragment>
diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.45, 0.43, 0.4), smoothstep(25.0, 110.0, length(vViewPosition)));`)},u.customProgramCacheKey=()=>"prag",u.polygonOffset=!0,u.polygonOffsetFactor=-1,u.polygonOffsetUnits=-1;let f=300,g=new ue,x=new nn,p=new P,m=new P,S=mn(3);for(let W=0;W<s;W+=f){let G=Math.floor(Math.min(f,s-W)/.6),K=new Rn(d,u,G);for(let nt=0;nt<G;nt++){let Et=W+nt*.6;i.tocka(Et,p),i.smer(Et,m),x.setFromAxisAngle(Rh,Math.atan2(-m.z,m.x)+(S()-.5)*.01),p.y=-.24,g.compose(p,x,new P(1,1,1)),K.setMatrixAt(nt,g)}K.receiveShadow=!0,K.computeBoundingSphere(),n.add(K)}let E=55,v=Math.atan2(.7,3.4),b=ke([[ie(.22,8.2,.22,.01),"#8e9496",Ht(0,4.1,0)],[ie(.5,.25,.5,.02),"#7f8486",Ht(0,.1,0)],[new ge(.035,.035,3.6,6),"#7c8183",Ht(0,7.8,1.7,Math.PI/2,0,0)],[new ge(.04,.04,Math.hypot(3.4,.7),6),"#7c8183",Ht(0,7.15,1.7,Math.PI/2-v,0,0)],[new ge(.025,.025,.93,6),"#7c8183",Ht(0,6.865,2.6)],[new ge(.018,.018,.95,6),"#7c8183",Ht(0,6.33,3.075,Math.PI/2,0,0)],[new ge(.05,.05,.4,8),"#a5462f",Ht(0,7.8,.35,Math.PI/2,0,0)],[new ge(.05,.05,.35,8),"#a5462f",Ht(0,6.87,.35,Math.PI/2-v,0,0)]]),M=new Nt({vertexColors:!0,roughness:.6,metalness:.5}),A=Math.floor((s-20)/E),_=new Rn(b,M,A),T=new P;for(let W=0;W<A;W++){let G=W*E+10;i.tocka(G,p),i.smer(G,m),Ch(m,T);let K=p.clone().addScaledVector(T,3.3);K.y=-.8,x.setFromAxisAngle(Rh,Math.atan2(-m.z,m.x)+Math.PI),g.compose(K,x,new P(1,1,1)),_.setMatrixAt(W,g)}_.castShadow=!0,_.computeBoundingSphere(),n.add(_);let I=5.5,L=6.62,N=[],B=(W,G,K)=>(i.tocka(W,p),i.smer(W,m),Ch(m,T),p.clone().addScaledVector(T,G).setY(K)),D=W=>{let G=(W-10)/E;return .2*(1-2*Math.abs(G%2-1))},O=W=>{let G=(W-10)/E%1;return L-.5*4*G*(1-G)},$=3;for(let W=10;W<10+(A-1)*E-1e-6;W+=$){let G=Math.min(W+$,10+(A-1)*E);N.push(B(W,D(W),I),B(G,D(G),I));let K=(W-10)/E%1,nt=Math.abs((G-10)/E%1)<1e-6?L:O(G);N.push(B(W,D(W)*.3,K<1e-6?L:O(W)),B(G,D(G)*.3,nt))}for(let W=10+4.5;W<10+(A-1)*E;W+=9)N.push(B(W,D(W),I),B(W,D(W)*.3,O(W)));let J=Gx(N,t,e);return n.add(J),{skupina:n,VOD_Y:I,zice:J}}function Gx(i,t,e){let n=i.length/2,s=new Float32Array(n*4*3),r=new Float32Array(n*4*3),a=new Float32Array(n*4*2),o=new Uint32Array(n*6);for(let d=0;d<n;d++){let u=i[2*d],f=i[2*d+1];for(let g=0;g<4;g++){let x=(d*4+g)*3;s.set([u.x,u.y,u.z],x),r.set([f.x,f.y,f.z],x),a.set([g>>1,g&1?1:-1],(d*4+g)*2)}o.set([d*4,d*4+2,d*4+1,d*4+1,d*4+2,d*4+3],d*6)}let c=new _e;c.setAttribute("position",new Pe(s,3)),c.setAttribute("aB",new Pe(r,3)),c.setAttribute("aK",new Pe(a,2)),c.setIndex(new Pe(o,1));let l=new Ue({uniforms:{...t,uLoc:{value:new mt(1e3,1e3)},uSir:{value:.014},uBarva:{value:new Ot("#2c2824")}},vertexShader:`
      attribute vec3 aB; attribute vec2 aK;
      uniform vec2 uLoc; uniform float uSir;
      varying float vPokr, vPx, vS; varying vec3 vW;
      void main() {
        vec4 a = viewMatrix * vec4(position, 1.0), b = viewMatrix * vec4(aB, 1.0);
        float near = projectionMatrix[3][2] / (projectionMatrix[2][2] - 1.0);
        float zn = -near * 1.01;
        if (a.z > zn && b.z > zn) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); return; }
        if (a.z > zn) a.xyz = mix(a.xyz, b.xyz, (zn - a.z) / (b.z - a.z));
        if (b.z > zn) b.xyz = mix(b.xyz, a.xyz, (zn - b.z) / (a.z - b.z));
        vec4 ca = projectionMatrix * a, cb = projectionMatrix * b;
        vec2 sa = ca.xy / ca.w * uLoc * 0.5, sb = cb.xy / cb.w * uLoc * 0.5;
        vec2 smer = sb - sa;
        smer = length(smer) > 1e-5 ? normalize(smer) : vec2(1.0, 0.0);
        vec2 nor = vec2(-smer.y, smer.x);
        vec4 c = aK.x < 0.5 ? ca : cb;
        vec3 v = aK.x < 0.5 ? a.xyz : b.xyz;
        float px = uSir * projectionMatrix[1][1] * uLoc.y * 0.5 / max(-v.z, 1e-3);
        float w = max(px, 1.25);
        vPokr = px / w; vPx = w; vS = aK.y;
        c.xy += nor * aK.y * w * 0.5 / (uLoc * 0.5) * c.w;
        vW = aK.x < 0.5 ? position : aB;
        gl_Position = c;
      }`,fragmentShader:e+`
      uniform vec3 uBarva;
      varying float vPokr, vPx, vS; varying vec3 vW;
      void main() {
        float rob = clamp((1.0 - abs(vS)) * vPx * 0.5 + 0.5, 0.0, 1.0);
        vec3 col = uBarva + neboBarva(vec3(0.0, 1.0, 0.0), 0.0) * 0.05;
        col = atmosfera(col, cameraPosition, vW - cameraPosition);
        gl_FragColor = vec4(col, vPokr * rob);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,transparent:!0,depthWrite:!1}),h=new ot(c,l);return h.frustumCulled=!1,h.renderOrder=2,h}var Le={sir:1.4,Lc:27,Lv:26,rega:.9,aVozF:5.1,rVoz:2.85,medOsjem:2.4,rKolo:.46};Le.dolzina=Le.Lc*2+Le.Lv+Le.rega*2;var Es={modra:"#1a9be6",bela:"#e8e6df",streha:"#3d4247",crna:"#0b0d10",steklo:"#0b1117",temna:"#23272b"},we={pasSp:[.93,1.11],crn:[1.11,2.5],okSp:[1.13,1.76],pasZg:[2.5,2.68],okZg:[2.86,3.8],vrata:[.45,2.48],okV:[1.14,2.09],okVm:[1.74,2.45],streha:4.34},Ca={z:.64,y0:.45,y1:1.33,glob:.86},Hc=.3,Wx=[.45,.645,.93,1.11,1.125,1.3,1.33,1.42,1.565,1.63,1.7,1.72,1.9,2.07,2.2,2.31,2.38,2.5,2.68,2.75],Xx=[2.86,3.15,3.45,3.53,3.76,3.84,3.88,4.05,4.07];function qx(){let i=Le.sir,t=[],e=.12;for(let a=0;a<=4;a++){let o=-Math.PI/2+a/4*(Math.PI/2);t.push([i-e+e*Math.cos(o),Hc+e+e*Math.sin(o)])}let n=[];for(let a=.5;a<2.75;a+=.1)n.push(+a.toFixed(3));n=[...new Set([...n,...Wx])].filter(a=>a>Hc+e+.01).sort((a,o)=>a-o);for(let a of n)t.push([i,a]);let s=[];for(let a=2.85;a<4.1;a+=.1)s.push(+a.toFixed(3));s=[...new Set([...s,...Xx,4.1])].sort((a,o)=>a-o);for(let a of s)t.push([fe(i,1.24,(a-2.75)/1.35),a]);let r=.3;for(let a=1;a<=7;a++){let o=a/8*(Math.PI/2);t.push([.94+r*Math.cos(o),4.1+r*Math.sin(o)])}return t}var gn=qx(),cs=gn.length,ls=4.4,Pa=.94,vr=(()=>{let i=[];for(let e=0;e<=24;e++)i.push(Math.sin(Math.PI/2*(2*e/24-1)));let t=Ca.z/Le.sir;for(let e of[-t,t,-.1,.1])i.push(e);return[...new Set(i.map(e=>+e.toFixed(5)))].sort((e,n)=>e-n)})(),gr=vr.length-1,Wd=i=>ls+.05*(1-(i/Pa)**2);function Xd(i){let t=gn[Math.max(0,i-1)],e=gn[Math.min(cs-1,i+1)],n=e[0]-t[0],s=e[1]-t[1],r=Math.hypot(n,s)||1;return[s/r,-n/r]}function Ph(i,t){let[e,n]=gn[i];return{w:t>Hc+.05&&n<t+.12?Le.sir:e,y:Math.max(n,t),pod:n<t}}var $d=[[.3,.04],[.45,.02],[.8,0],[1.3,0],[1.33,.13],[1.42,.15],[1.7,.21],[2.07,.38],[2.38,.47],[3.45,1.02],[3.84,1.25],[4.05,1.4]],Ra=(()=>{let n=Math.hypot(.72,1),s=(ls-4.05)/(1-.72/n);return{R:s,cd:1.4+s/n,cy:4.05-.72/n*s,y0:4.05}})(),qd=(()=>{let i=$d,t=[];for(let e=0;e<i.length;e++){if(e===i.length-1){t.push(.72);continue}if(e===0){t.push((i[1][1]-i[0][1])/(i[1][0]-i[0][0]));continue}let n=(i[e][1]-i[e-1][1])/(i[e][0]-i[e-1][0]),s=(i[e+1][1]-i[e][1])/(i[e+1][0]-i[e][0]);t.push(n*s<=0?0:2*n*s/(n+s))}return t})();function Yx(i){if(i>=Ra.y0){let d=Math.max(0,Ra.R*Ra.R-(Math.min(i,ls)-Ra.cy)**2);return Ra.cd-Math.sqrt(d)}let t=$d,e=0;for(;e<t.length-2&&i>t[e+1][0];)e++;let[n,s]=t[e],[r,a]=t[e+1],o=r-n,c=Fe((i-n)/o),l=c*c,h=l*c;return(2*h-3*l+1)*s+(h-2*l+c)*o*qd[e]+(-2*h+3*l)*a+(h-l)*o*qd[e+1]}function jx(i){if(i>=ls)return Pa;if(i<=gn[0][1])return gn[0][0];for(let t=0;t<cs-1;t++)if(i<=gn[t+1][1]){let e=(i-gn[t][1])/(gn[t+1][1]-gn[t][1]||1);return fe(gn[t][0],gn[t+1][0],Fe(e))}return fe(gn[cs-1][0],Pa,Fe((i-gn[cs-1][1])/(ls-gn[cs-1][1])))}function Zx(i,t){let e=i<.45?Le.sir:jx(i),n,s,r;if(i<=1.315)n=.3,s=.17,r=.03;else{let l=Fe((i-1.33)/1.1);n=fe(.46,.66,l),s=fe(.3,.56,l),r=.07}n=Math.min(n,e*.7);let a=Math.min(Math.abs(t),e),o=r*(a/e)**2,c=e-n;return a>c&&(o+=s*(1-Math.sqrt(Math.max(0,1-((a-c)/n)**2)))),o}var Pn=(i,t)=>Yx(i)+Zx(i,t);function Yd(i,t){let e=[],n=[],s=[],r=[],l=t?[[0,1],[4.5,1],[4.65,.32],[i-6.82,.32],[i-6.67,1],[i-3.25,1],[i-3.1,.45],[i-2.9,.45]]:[[0,1],[4.5,1],[4.65,.32],[i-4.65,.32],[i-4.5,1],[i,1]],h=(x,p,m)=>{let S=[],E=(b,M)=>m?i-Pn(b,M):x;for(let b=0;b<cs;b++){let M=Ph(b,p),[A,_]=Xd(b);S.push([E(M.y,-M.w),M.y,-M.w,0,M.pod?0:_,M.pod?-1:-A,-.5])}for(let b=0;b<=gr;b++){let M=vr[b]*Pa;S.push([E(ls,M),Wd(M),M,0,1,0,0])}for(let b=cs-1;b>=0;b--){let M=Ph(b,p),[A,_]=Xd(b);S.push([E(M.y,M.w),M.y,M.w,0,M.pod?0:_,M.pod?1:A,0])}let v=p>Hc+.05?Le.sir:gn[0][0];for(let b=gr;b>=0;b--){let M=vr[b]*v;S.push([E(p,M),p,M,0,-1,0,0])}return S},d=l.map(([x,p])=>h(x,p,!1));t&&d.push(h(0,.45,!0));let u=d[0].length;for(let x of d)for(let[p,m,S,E,v,b,M]of x)e.push(p,m,S),n.push(E,v,b),s.push(p,m,M);for(let x=0;x<d.length-1;x++)for(let p=0;p<u-1;p++){let m=x*u+p,S=m+1,E=m+u,v=E+1;r.push(m,S,E,S,v,E)}let f=(x,p)=>{let m=d[x],S=e.length/3,E=m[0][0];e.push(E,2.3,0),n.push(p?1:-1,0,0),s.push(E,2.3,2);let v=e.length/3;for(let[b,M,A]of m)e.push(b,M,A),n.push(p?1:-1,0,0),s.push(b,M,2);for(let b=0;b<u-1;b++)p?r.push(S,v+b,v+b+1):r.push(S,v+b+1,v+b)};if(f(0,!1),t||f(d.length-1,!0),t){let x=e.length/3,p=[];for(let v=0;v<cs;v++){let b=Ph(v,.45);p.push([b.w,b.y])}p.push([Pa,ls]);let m=p.length,S=.001;for(let v=0;v<m;v++){let[b,M]=p[v];for(let A=0;A<=gr;A++){let _=vr[A]*b,T=v===m-1?Wd(_):M,I=i-Pn(T,_),L=Math.max(T-S,.45),N=Math.min(T+S,ls),B=N>L?(Pn(N,_)-Pn(L,_))/(N-L):0,D=Fe(_,-b+S,b-S),O=(Pn(T,D+S)-Pn(T,D-S))/(2*S),$=new P(1,Math.min(B,60),Math.max(-60,Math.min(60,O))).normalize();e.push(I,T,_),n.push($.x,$.y,$.z),s.push(_,T,1)}}let E=Ca.z/Le.sir+1e-4;for(let v=0;v<m-1;v++){let b=p[v][1],M=p[v+1][1],A=b>=Ca.y0-1e-4&&M<=Ca.y1+1e-4;for(let _=0;_<gr;_++){if(A&&Math.abs(vr[_])<=E&&Math.abs(vr[_+1])<=E)continue;let T=x+v*(gr+1)+_,I=T+1,L=T+gr+1,N=L+1;r.push(T,L,I,I,L,N)}}}let g=new _e;return g.setAttribute("position",new Jt(e,3)),g.setAttribute("normal",new Jt(n,3)),g.setAttribute("aLiv",new Jt(s,3)),g.setIndex(r),g}function $x(i){let t=[],e=[],{z:n,y0:s,y1:r,glob:a}=Ca,o=i-a,c=(d,u,f,g)=>{let x=t.length/3;t.push(...d,...u,...f,...g),e.push(x,x+1,x+2,x,x+2,x+3)},l=8;for(let d=0;d<l;d++){let u=fe(s,r,d/l),f=fe(s,r,(d+1)/l);for(let g of[-1,1]){let x=i-Pn(u,g*n),p=i-Pn(f,g*n);g>0?c([x,u,n],[o,u,n],[o,f,n],[p,f,n]):c([o,u,-n],[x,u,-n],[p,f,-n],[o,f,-n])}}for(let d=0;d<l;d++){let u=fe(-n,n,d/l),f=fe(-n,n,(d+1)/l),g=i-Pn(r,u),x=i-Pn(r,f);c([g,r,u],[x,r,f],[o,r,f],[o,r,u])}c([o,s,-n],[o,r,-n],[o,r,n],[o,s,n]);let h=new _e;return h.setAttribute("position",new Jt(t,3)),h.setIndex(e),h.computeVertexNormals(),h}var Jx=`
varying vec3 vLiv;
varying vec3 vLok;         // lega na vozu (m): x vzdol\u017E, y gor, z \u010Dez
varying vec3 vNorLok;
uniform float uL;
uniform float uCelni;
uniform float uNoc;
uniform float uSvetloba;
uniform float uZarometi;   // 1 = \u010Delo spredaj (beli \u017Earometi)
uniform float uRdece;      // 1 = \u010Delo zadaj (rde\u010Di lu\u010Di)
uniform sampler2D uNapisi;
uniform vec3 cModra, cBela, cStreha, cCrna, cSteklo, cTemna;
uniform vec3 uKam;         // kamera v koordinatah voza
uniform vec4 uVrata;       // odprta vrata na levi: x0, x1, odprtost
uniform mat3 uRot;         // voz -> svet
uniform vec4 uStrop;       // nadstre\u0161ek postaje: x0, x1, z0, z1
uniform float uStropY, uStropLuc;
uniform vec3 uStropBarva;
varying vec3 vSvetPos;
// prepustnost zatemnjenega stekla
const vec3 PREPUSTNOST = vec3(0.50, 0.55, 0.54);

float aa;
// okno v vratih pod to\u010Dko: robova vrat v koordinati, ki jo je dobila vrata(),
// in ali je ta koordinata zrcaljena (uL - x)
float gVrO = 0.0, gVrA = 0.0, gVrB = 0.0, gVrZ = 0.0;
float gP0 = 0.0, gP1 = 0.0, gOkA = 0.0, gOkB = 0.0;
float pasY(float y, float a, float b) { return smoothstep(a - aa, a + aa, y) - smoothstep(b - aa, b + aa, y); }
float sdSkatla(vec2 p, vec2 a, vec2 b, float r) {
  vec2 c = (a + b) * 0.5, h = (b - a) * 0.5;
  vec2 q = abs(p - c) - h + r;
  return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}
float skatla2(vec2 p, vec2 a, vec2 b, float r) { return 1.0 - smoothstep(-aa, aa, sdSkatla(p, a, b, r)); }
float krog(vec2 p, vec2 c, float r) { return 1.0 - smoothstep(-aa, aa, length(p - c) - r); }

struct Liv { vec3 col; float rough; vec3 emis; float coat; float spec; float zun; vec3 dz; };

float vrstaOken(float x, float y, float p0, float p1, float sir, float y0, float y1, float r, float nag, out float id) {
  float dol = p1 - p0;
  float n = max(1.0, floor(dol / 1.95 + 0.3));
  float kor = dol / n;
  float k = clamp(floor((x - p0) / kor), 0.0, n - 1.0);
  id = k + floor(p0 * 7.0);
  float c = p0 + (k + 0.5) * kor + (y - (y0 + y1) * 0.5) * nag;
  return skatla2(vec2(x, y), vec2(c - sir * 0.5, y0), vec2(c + sir * 0.5, y1), r);
}
void vrata(float x, float y, float a, float b, float zrc, inout vec3 col, inout float steklo) {
  float portal = skatla2(vec2(x, y), vec2(a - 0.07, 0.40), vec2(b + 0.07, 2.57), 0.10);
  col = mix(col, cCrna * 1.4, portal);
  float m = skatla2(vec2(x, y), vec2(a, 0.46), vec2(b, 2.48), 0.05);
  col = mix(col, cModra, m);
  float c = (a + b) * 0.5;
  float reza = (1.0 - smoothstep(0.007, 0.007 + aa, abs(x - c))) * m;
  col = mix(col, cCrna, reza);
  float l = (c - a) * 0.5;
  float o1 = skatla2(vec2(x, y), vec2(a + l - 0.11, 1.14), vec2(a + l + 0.11, 2.09), 0.08);
  float o2 = skatla2(vec2(x, y), vec2(c + l - 0.11, 1.14), vec2(c + l + 0.11, 2.09), 0.08);
  float ob = max(o1, o2);
  if (ob > gVrO) { gVrO = ob; gVrA = a; gVrB = b; gVrZ = zrc; }
  steklo = max(steklo, ob);
}

// ---- notranjost za steklom ----
// \u017Darek iz kamere skozi to\u010Dko na steklu v \u0161katlo eta\u017Ee (\xBBinterior mapping\xAB):
// daljna stena z okni, tla, strop z lu\u010Dmi, sede\u017Ei 2 + 2 v predelih po oknih,
// tu in tam potnik. Brez geometrije, a s pravo paralakso.
float hashN(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
float mehko(float d) { return 1.0 - smoothstep(-0.006, 0.006, d); }
float naslon(vec2 q, float yF) {
  return max(mehko(sdSkatla(q, vec2(0.31, yF + 0.40), vec2(0.775, yF + 1.18), 0.08)),
             mehko(sdSkatla(q, vec2(0.795, yF + 0.40), vec2(1.255, yF + 1.18), 0.08)));
}
float potnik(vec2 q, float zc, float yF) {
  float glava = 1.0 - smoothstep(0.9, 1.0, length((q - vec2(zc, yF + 1.25)) / vec2(0.086, 0.11)));
  float trup = mehko(sdSkatla(q, vec2(zc - 0.20, yF + 0.46), vec2(zc + 0.20, yF + 1.10), 0.10));
  return max(glava, trup);
}
vec3 barvaJakne(float h) {
  return h < 0.22 ? vec3(0.05, 0.055, 0.065) : h < 0.4 ? vec3(0.24, 0.07, 0.06) : h < 0.58 ? vec3(0.07, 0.12, 0.2)
       : h < 0.76 ? vec3(0.26, 0.25, 0.23) : h < 0.9 ? vec3(0.1, 0.16, 0.1) : vec3(0.42, 0.3, 0.12);
}
vec3 barvaLas(float h) {
  return h < 0.4 ? vec3(0.06, 0.04, 0.03) : h < 0.7 ? vec3(0.02) : h < 0.9 ? vec3(0.17, 0.1, 0.05) : vec3(0.42, 0.32, 0.17);
}
// okno na daljni steni: isti razpored kot na bli\u017Enji
float oknoDalec(vec3 H, float tip) {
  float id;
  if (tip < 1.5) return vrstaOken(H.x, H.y, gP0 + 0.2, gP1 - 0.2, 1.36, ${we.okSp[0]}, ${we.okSp[1]}, 0.10, 0.0, id);
  if (tip < 2.5) return vrstaOken(H.x, H.y, gP0 - 0.35, gP1 + 0.35, 1.80, ${we.okZg[0]}, ${we.okZg[1]}, 0.16, 0.10, id);
  if (tip < 4.5) return skatla2(H.xy, vec2(gOkA, ${we.okVm[0]}), vec2(gOkB, ${we.okVm[1]}), 0.10);
  float l = (gVrB - gVrA) * 0.25, c = (gVrA + gVrB) * 0.5;
  return max(skatla2(H.xy, vec2(gVrA + l - 0.11, 1.14), vec2(gVrA + l + 0.11, 2.09), 0.08),
             skatla2(H.xy, vec2(c + l - 0.11, 1.14), vec2(c + l + 0.11, 2.09), 0.08));
}
vec3 notranjost(vec3 P, vec3 D, float x0, float x1, float yF, float yC, float W,
                float b0, float kor, float sedezi, float tip, out float zun) {
  zun = 0.0;
  float sz = P.z < 0.0 ? 1.0 : -1.0;          // proti daljni steni
  if (D.z * sz <= 1e-4) return vec3(0.0);
  float tH = (sz * W - P.z) / D.z;
  int kaj = 0;                                // 0 stena, 1 strop, 2 tla, 3 \u010Delna stena, 4 sede\u017E
  if (D.y > 1e-4) { float t = (yC - P.y) / D.y; if (t < tH) { tH = t; kaj = 1; } }
  else if (D.y < -1e-4) { float t = (yF - P.y) / D.y; if (t < tH) { tH = t; kaj = 2; } }
  if (D.x > 1e-4) { float t = (x1 - P.x) / D.x; if (t < tH) { tH = t; kaj = 3; } }
  else if (D.x < -1e-4) { float t = (x0 - P.x) / D.x; if (t < tH) { tH = t; kaj = 3; } }
  vec3 col = vec3(0.0);
  if (sedezi > 0.5 && abs(D.x) > 1e-4) {
    float sx = D.x > 0.0 ? 1.0 : -1.0;
    float k0 = floor((P.x - b0) / kor);
    for (int j = 0; j < 4; j++) {
      float k = k0 + float(j) * sx;
      float a = b0 + k * kor, b = a + kor;
      if (b < x0 || a > x1) break;
      float tb = tH; vec3 cb = vec3(0.0); bool zad = false;
      for (int i = 0; i < 4; i++) {
        float xp = i == 0 ? a + 0.08 : i == 1 ? a + 0.36 : i == 2 ? b - 0.36 : b - 0.08;
        float t = (xp - P.x) / D.x;
        if (t <= 0.0 || t >= tb) continue;
        vec3 Q = P + D * t;
        vec2 q = vec2(abs(Q.z), Q.y);
        if (i == 0 || i == 3) {
          if (naslon(q, yF) > 0.5) {
            tb = t; zad = true;
            float hs = hashN(vec3(k, sign(Q.z), float(i) + uL));
            cb = mix(vec3(0.075, 0.12, 0.24), vec3(0.12, 0.18, 0.33), step(yF + 0.98, Q.y)) * (0.88 + 0.24 * hs);
          }
        } else {
          float zc = q.x < 0.785 ? 0.54 : 1.025;
          float smer = i == 1 ? 1.0 : -1.0;           // A gleda v +x, B v -x
          float h = hashN(vec3(k * 3.1 + zc, sign(Q.z), smer + uL));
          if (h < 0.3 && potnik(q, zc, yF) > 0.5) {
            tb = t; zad = true;
            bool obraz = smer * D.x < 0.0;
            vec3 lasje = barvaLas(fract(h * 37.0));
            if (Q.y > yF + 1.13) cb = obraz && Q.y < yF + 1.28 ? vec3(0.5, 0.35, 0.26) : lasje;
            else cb = barvaJakne(fract(h * 91.0));
          }
        }
      }
      // sedi\u0161\u010Da
      if (D.y < -1e-4) {
        float t = (yF + 0.45 - P.y) / D.y;
        if (t > 0.0 && t < tb) {
          vec3 Q = P + D * t;
          float az = abs(Q.z);
          bool vx = (Q.x > a + 0.08 && Q.x < a + 0.56) || (Q.x > b - 0.56 && Q.x < b - 0.08);
          if (vx && az > 0.31 && az < 1.255) { tb = t; zad = true; cb = vec3(0.085, 0.13, 0.26); }
        }
      }
      if (zad) { tH = tb; col = cb; kaj = 4; break; }
    }
  }
  vec3 H = P + D * tH;
  float vis = clamp((H.y - yF) / max(yC - yF, 0.1), 0.0, 1.0);
  float sv = mix(0.30, 0.62, uNoc) * (0.62 + 0.5 * vis);
  if (kaj == 0) {
    float ok = oknoDalec(H, tip);
    vec3 st = mix(vec3(0.30, 0.31, 0.33), vec3(0.74, 0.72, 0.67), smoothstep(yF + 0.30, yF + 0.36, H.y));
    col = st * sv * (1.0 - ok);
    zun = ok;
  } else if (kaj == 1) {
    float luc = 1.0 - smoothstep(0.04, 0.055, abs(abs(H.z) - 0.46));
    col = vec3(0.82, 0.82, 0.8) * sv + vec3(1.0, 0.94, 0.84) * luc * mix(0.30, 0.62, uNoc) * 3.2;
  } else if (kaj == 2) {
    col = mix(vec3(0.22, 0.23, 0.25), vec3(0.3, 0.31, 0.33), 1.0 - step(0.30, abs(H.z))) * sv;
  } else if (kaj == 3) {
    col = vec3(0.66, 0.65, 0.62) * sv;
  } else {
    col *= sv * 1.1;
  }
  return col;
}

// \u017Darometna skupina na \u010Delu (az = |z|): okrogel \u017Earomet zunaj, LED polje
// znotraj, ohi\u0161je s po\u0161evnim notranjim robom.
void lucCela(float az, float y, inout vec3 col, inout vec3 emis, inout float rough) {
  float notr = 0.49 + (y - 1.42) * 0.70;          // notranji po\u0161evni rob
  float vrh = 1.63 + (az - 0.49) * 0.11;
  float ohis = smoothstep(notr - aa, notr + aa, az) * (1.0 - smoothstep(1.15 - aa, 1.15 + aa, az))
             * smoothstep(1.42 - aa, 1.42 + aa, y) * (1.0 - smoothstep(vrh - aa, vrh + aa, y));
  col = mix(col, cCrna, ohis);
  rough = mix(rough, 0.12, ohis);
  // okrogel \u017Earomet s sedmimi diodami
  vec2 p = vec2(az, y), c = vec2(1.0, 1.555);
  float zar = krog(p, c, 0.083);
  float diode = 0.0;
  diode = max(diode, krog(p, c, 0.017));
  for (int i = 0; i < 6; i++) {
    float t = float(i) * 1.0472 + 0.5236;
    diode = max(diode, krog(p, c + vec2(cos(t), sin(t)) * 0.048, 0.016));
  }
  col = mix(col, vec3(0.28, 0.29, 0.30), zar * ohis);
  col = mix(col, vec3(0.75), diode * zar);
  emis += vec3(1.0, 0.97, 0.9) * (diode * 6.0 + zar * 0.8) * uZarometi * uSvetloba;
  // LED polje: pike v mre\u017Ei
  float polje = smoothstep(notr + 0.05 - aa, notr + 0.05 + aa, az) * (1.0 - smoothstep(0.87 - aa, 0.87 + aa, az))
              * smoothstep(1.47 - aa, 1.47 + aa, y) * (1.0 - smoothstep(1.61 - aa, 1.61 + aa, y));
  vec2 g = fract(vec2(az, y) / 0.018) - 0.5;
  float pika = 1.0 - smoothstep(0.22, 0.36, length(g));
  vec3 rd = vec3(1.0, 0.08, 0.05) * uRdece * 4.0 + vec3(1.0, 0.85, 0.7) * uZarometi * 1.2;
  col = mix(col, vec3(0.16, 0.08, 0.08), polje * 0.6);
  emis += rd * pika * polje * uSvetloba;
}

Liv liv() {
  vec3 p = vLiv;
  aa = max(0.0025, length(fwidth(p.xy)) * 0.8);
  Liv L;
  L.col = cBela; L.rough = 0.33; L.emis = vec3(0.0); L.coat = 0.7; L.spec = 0.04; L.zun = 0.0; L.dz = vec3(0.0, 0.0, 1.0);
  float steklo = 0.0, tipOkna = 0.0, wOkna = 0.0;
  float korSp = 1.95, korZg = 1.95;

  if (p.z > 1.5) {
    L.col = cTemna; L.rough = 0.7; L.coat = 0.0;
    return L;
  }
  if (p.z > 0.5) {
    // ---- \u010Delo: p.x = z, p.y = y ----
    float az = abs(p.x), y = p.y;
    vec3 col = cModra;
    // spodaj belo: odbija\u010Da, polica, kotna pasova ob lu\u010Deh
    float brada = 0.49 + (y - 1.33) * 0.70;
    float belo = 1.0 - smoothstep(1.33 - aa, 1.33 + aa, y);
    belo = max(belo, (1.0 - smoothstep(1.42 - aa, 1.42 + aa, y)) * smoothstep(brada - aa, brada + aa, az));
    belo = max(belo, (1.0 - smoothstep(1.72 - aa, 1.72 + aa, y)) * smoothstep(1.14 - aa, 1.14 + aa, az));
    col = mix(col, cBela, belo);
    // \u010Drna maska: brada stekla (V), steklo, tabla, zgornji del z mre\u017Eo
    float vV = 2.07 + 0.24 * clamp(az / 0.98, 0.0, 1.0);
    float sir = 0.98 - max(0.0, y - 2.38) * 0.05;
    float maska = smoothstep(vV - aa, vV + aa, y) * (1.0 - smoothstep(sir - aa, sir + aa, az)) * (1.0 - smoothstep(3.46 - aa, 3.46 + aa, y));
    float sirZg = y < 3.84 ? 0.84 : 0.62 - (y - 3.84) * 0.25;
    maska = max(maska, smoothstep(3.44 - aa, 3.44 + aa, y) * (1.0 - smoothstep(sirZg - aa, sirZg + aa, az)));
    col = mix(col, cCrna, maska);
    float vs = skatla2(vec2(az, y), vec2(-0.96, 2.40), vec2(0.96 - (y - 2.4) * 0.05, 3.43), 0.10);
    float tabla = skatla2(vec2(az, y), vec2(-0.66, 3.52), vec2(0.66, 3.77), 0.04);
    float zgLuc = skatla2(vec2(az, y), vec2(-0.27, 3.88), vec2(0.27, 4.08), 0.07);
    float mreza = skatla2(vec2(az, y), vec2(-0.30, 4.12), vec2(0.30, 4.40), 0.04);
    col = mix(col, cTemna * (0.6 + 0.9 * step(0.5, fract(y * 34.0))), mreza);
    steklo = max(max(vs, tabla * 0.6), zgLuc * 0.8);
    L.col = col; L.rough = mix(0.30, 0.18, maska);
    lucCela(az, y, L.col, L.emis, L.rough);
    // logotip in \u0161tevilka iz atlasa
    vec2 uvL = vec2(-p.x / 0.84 + 0.5, (y - 1.715) / 0.215);
    if (uvL.x > 0.0 && uvL.x < 1.0 && uvL.y > 0.0 && uvL.y < 1.0) {
      float a = texture2D(uNapisi, vec2(uvL.x * 0.5, 0.5 + uvL.y * 0.5)).a;
      L.col = mix(L.col, cBela, a);
    }
    vec2 uvN = vec2(-p.x / 0.50 + 0.5, (y - 1.445) / 0.10);
    if (uvN.x > 0.0 && uvN.x < 1.0 && uvN.y > 0.0 && uvN.y < 1.0) {
      float a = texture2D(uNapisi, vec2(uvN.x * 0.5, 0.25 + uvN.y * 0.25)).a;
      L.col = mix(L.col, cBela, a);
    }
    vec2 uvT = vec2(-p.x / 1.30 + 0.5, (y - 3.53) / 0.23);
    if (uvT.x > 0.0 && uvT.x < 1.0 && uvT.y > 0.0 && uvT.y < 1.0) {
      vec4 t = texture2D(uNapisi, vec2(0.5 + uvT.x * 0.5, 0.75 + uvT.y * 0.25));
      L.emis += t.rgb * 2.4 * uSvetloba;
    }
    // zgornja signalna lu\u010D: LED pike
    vec2 g = fract(vec2(az, y) / 0.02) - 0.5;
    L.emis += vec3(1.0, 0.95, 0.85) * (1.0 - smoothstep(0.2, 0.35, length(g))) * skatla2(vec2(az, y), vec2(-0.12, 3.92), vec2(0.12, 4.04), 0.0) * uZarometi * 1.5 * uSvetloba;
  } else {
    // ---- bok: p.x = x vzdol\u017E voza, p.y = vi\u0161ina, p.z < 0 = leva stran ----
    float x = p.x, y = p.y;
    float a = uL - x;
    float e = uCelni > 0.5 ? x : min(x, uL - x);
    // vrata, skozi katera vstopa dijak: odprtina v karoseriji, za njo preddverje
    if (uVrata.z > 0.001 && p.z < -0.25 && x > uVrata.x && x < uVrata.y && y > 0.44 && y < 2.50) discard;
    vec3 col = cBela;
    float streha = smoothstep(${we.streha.toFixed(2)} - aa, ${we.streha.toFixed(2)} + aa, y);
    float zac = uCelni > 0.5 ? 3.62 : -1.0;
    col = mix(col, cModra, max(pasY(y, ${we.pasZg[0]}, ${we.pasZg[1]}) * step(zac, a), pasY(y, ${we.pasSp[0]}, ${we.pasSp[1]}) * step(zac + 0.9, a)));
    // dvonadstropni del med vrati
    float p0 = 5.95;
    float p1 = uCelni > 0.5 ? uL - 8.05 : uL - 5.95;
    gP0 = p0; gP1 = p1;
    korSp = (p1 - p0 - 0.4) / max(1.0, floor((p1 - p0 - 0.4) / 1.95 + 0.3));
    korZg = (p1 - p0 + 0.7) / max(1.0, floor((p1 - p0 + 0.7) / 1.95 + 0.3));
    float vPasu = step(p0, x) * step(x, p1);
    col = mix(col, cCrna * 1.5, pasY(y, ${we.crn[0]}, ${we.crn[1]}) * vPasu);
    float id;
    float sp = vrstaOken(x, y, p0 + 0.2, p1 - 0.2, 1.36, ${we.okSp[0]}, ${we.okSp[1]}, 0.10, 0.0, id) * vPasu;
    col = mix(col, cCrna, vrstaOken(x, y, p0 + 0.2, p1 - 0.2, 1.46, ${we.okSp[0]} - 0.04, ${we.okSp[1]} + 0.05, 0.13, 0.0, id) * vPasu);
    steklo = max(steklo, sp);
    if (sp > wOkna) { wOkna = sp; tipOkna = 1.0; }
    // zgornja okna: \u010Drn okvir z zaobljenima koncema, okna z rahlo nagnjenimi stebri\u010Dki
    float q0 = p0 - 0.45, q1 = p1 + 0.45;
    float okvirZg = skatla2(vec2(x, y), vec2(q0, ${we.okZg[0]} - 0.06), vec2(q1, ${we.okZg[1]} + 0.06), 0.34);
    col = mix(col, cCrna, okvirZg);
    float zgo = vrstaOken(x, y, q0 + 0.1, q1 - 0.1, 1.80, ${we.okZg[0]}, ${we.okZg[1]}, 0.16, 0.10, id) * okvirZg;
    steklo = max(steklo, zgo);
    if (zgo > wOkna) { wOkna = zgo; tipOkna = 2.0; }
    // okna vmesne eta\u017Ee nad vozi\u010Dki
    float okv = skatla2(vec2(e, y), vec2(1.55, ${we.okVm[0]}), vec2(3.35, ${we.okVm[1]}), 0.10);
    col = mix(col, cCrna, skatla2(vec2(e, y), vec2(1.49, ${we.okVm[0]} - 0.06), vec2(3.41, ${we.okVm[1]} + 0.06), 0.13));
    steklo = max(steklo, okv);
    if (okv > wOkna) { wOkna = okv; tipOkna = 3.0; }
    if (uCelni > 0.5) {
      vrata(a, y, 6.75, 8.05, 1.0, col, steklo);
      vrata(x, y, 4.65, 5.95, 0.0, col, steklo);
      // modro polje za kabino: sprednji rob nagnjen naprej (vrh bli\u017Ee nosu)
      float rob = 4.75 - (y - ${we.pasSp[0]}) * 0.62;
      float polje = smoothstep(rob - aa, rob + aa, a) * (1.0 - smoothstep(6.68 - aa, 6.68 + aa, a)) * pasY(y, ${we.pasSp[0]}, ${we.pasZg[1]});
      col = mix(col, cModra, polje);
      float okP = skatla2(vec2(a, y), vec2(5.05, ${we.okVm[0]}), vec2(6.30, ${we.okVm[1]}), 0.10);
      col = mix(col, cCrna, skatla2(vec2(a, y), vec2(4.99, ${we.okVm[0]} - 0.06), vec2(6.36, ${we.okVm[1]} + 0.06), 0.13));
      steklo = max(steklo, okP);
      if (okP > wOkna) { wOkna = okP; tipOkna = 4.0; }
      // napis na polju
      vec2 uvS = vec2((p.z < -0.25 ? (a - 4.25) : (6.45 - a)) / 2.2, (y - 1.20) / 0.22);
      if (uvS.x > 0.0 && uvS.x < 1.0 && uvS.y > 0.0 && uvS.y < 1.0) {
        float t = texture2D(uNapisi, vec2(0.5 + uvS.x * 0.5, 0.5 + uvS.y * 0.25)).a;
        col = mix(col, cBela, t * polje);
      }
      // kabina: veliko okno s po\u0161evnim sprednjim robom, ozko okno v vratih
      float rk = 1.15 + (y - 2.2) * 0.55;
      float kok = smoothstep(rk - aa, rk + aa, a) * skatla2(vec2(a, y), vec2(1.0, 2.2), vec2(2.35, 3.15), 0.12);
      float kvo = skatla2(vec2(a, y), vec2(2.52, 2.2), vec2(2.95, 3.15), 0.09);
      float sv = (1.0 - smoothstep(0.006, 0.006 + aa, abs(a - 2.43))) + (1.0 - smoothstep(0.006, 0.006 + aa, abs(a - 3.16)));
      col = mix(col, cCrna * 2.0, sv * step(0.62, y) * (1.0 - step(3.32, y)) * 0.8);
      steklo = max(steklo, max(kok, kvo));
      // modra kapa nosu: krivulja od lu\u010Di navzgor in nazaj, nato vodoravno
      float t = clamp((a - 0.42) / 2.4, 0.0, 1.0);
      float spodaj = a < 0.42 ? 1.72 : 1.72 + 2.06 * sin(t * 1.5708);
      float konec = 6.6 - (y - 3.78) * 2.2;
      float kapa = smoothstep(spodaj - aa, spodaj + aa, y) * (1.0 - smoothstep(konec - aa, konec + aa, a));
      col = mix(col, cModra, kapa);
      // mre\u017Ea prezra\u010Devanja na kapi
      float mz = skatla2(vec2(a, y), vec2(4.5, 3.95), vec2(5.35, 4.28), 0.04);
      col = mix(col, cTemna * (0.6 + 0.8 * step(0.5, fract(a * 22.0))), mz);
      col = mix(col, cCrna * 2.5, skatla2(vec2(a, y), vec2(5.55, 3.98), vec2(6.05, 4.26), 0.03));
      streha *= step(1.9, a);
    } else {
      vrata(x, y, 4.65, 5.95, 0.0, col, steklo);
      vrata(uL - x, y, 4.65, 5.95, 1.0, col, steklo);
    }
    if (gVrO > wOkna) { wOkna = gVrO; tipOkna = 5.0; }
    col = mix(col, cStreha, streha);
    // umazanija spodaj: zavorni prah
    col *= mix(0.84, 1.0, smoothstep(0.35, 0.95, y));
    L.col = col;
    L.rough = mix(0.33, 0.55, streha);
    L.coat = 0.7 * (1.0 - streha);
  }
  if (steklo > 0.0) {
    // zatemnjeno steklo: odsev po Fresnelu, skozenj notranjost eta\u017Ee
    L.col = mix(L.col, cSteklo, steklo);
    L.rough = mix(L.rough, 0.05, steklo);
    L.coat = mix(L.coat, 0.0, steklo);
    L.spec = mix(L.spec, 0.04, steklo);
    if (tipOkna > 0.5) {
      vec3 P = vLok, D = normalize(vLok - uKam);
      float zun = 0.0;
      vec3 n = vec3(0.0);
      if (tipOkna < 1.5) {
        n = notranjost(P, D, gP0 + 0.05, gP1 - 0.05, 0.50, 2.38, 1.30, gP0 + 0.2, korSp, 1.0, 1.0, zun);
      } else if (tipOkna < 2.5) {
        n = notranjost(P, D, gP0 - 0.35, gP1 + 0.35, 2.58, 4.15, 1.22, gP0 - 0.35, korZg, 1.0, 2.0, zun);
      } else {
        // koordinata od konca voza navznoter (pri zadnjem koncu zrcaljena)
        bool zr = tipOkna < 3.5 ? (uCelni < 0.5 && P.x > uL * 0.5) : tipOkna < 4.5 ? true : gVrZ > 0.5;
        vec3 Pe = P, De = D;
        if (zr) { Pe.x = uL - P.x; De.x = -D.x; }
        if (tipOkna < 3.5) {
          gOkA = 1.55; gOkB = 3.35;
          n = notranjost(Pe, De, 0.15, 4.55, 1.22, 3.55, 1.30, 1.45, 2.0, 1.0, 3.0, zun);
        } else if (tipOkna < 4.5) {
          gOkA = 5.05; gOkB = 6.30;
          n = notranjost(Pe, De, 4.75, 6.65, 1.22, 3.55, 1.30, 4.78, 1.84, 1.0, 4.0, zun);
        } else {
          n = notranjost(Pe, De, gVrA - 0.85, gVrB + 0.85, 0.60, 2.50, 1.30, 0.0, 1.0, 0.0, 5.0, zun);
        }
      }
      float cosT = abs(dot(D, normalize(vNorLok)));
      float F = 0.04 + 0.96 * pow(1.0 - cosT, 5.0);
      float prep = (1.0 - F) * steklo;
      L.emis += n * PREPUSTNOST * prep;
      L.zun = zun * prep;
      L.dz = D;
    }
  }
  return L;
}
`,Kx=`
#if defined( RE_IndirectSpecular )
{
  vec3 Rs = inverseTransformDirection(reflect(-geometryViewDir, geometryNormal), viewMatrix);
  if (Rs.y > 0.02) {
    float t = (uStropY - vSvetPos.y) / Rs.y;
    if (t > 0.0) {
      vec2 h = vSvetPos.xz + Rs.xz * t;
      float zak = smoothstep(uStrop.x - 1.0, uStrop.x + 1.0, h.x) * (1.0 - smoothstep(uStrop.y - 1.0, uStrop.y + 1.0, h.x))
                * smoothstep(uStrop.z - 0.25, uStrop.z + 0.25, h.y) * (1.0 - smoothstep(uStrop.w - 0.25, uStrop.w + 0.25, h.y));
      float tr = (1.0 - smoothstep(0.05, 0.09, abs(h.y - 3.1))) + (1.0 - smoothstep(0.05, 0.09, abs(h.y - 6.0)));
      vec3 s = uStropBarva + vec3(1.0, 0.95, 0.86) * tr * uStropLuc;
      radiance = mix(radiance, s, zak);
      #ifdef USE_CLEARCOAT
        clearcoatRadiance = mix(clearcoatRadiance, s, zak);
      #endif
    }
  }
}
#endif
`,Qx=`
#ifdef USE_ENVMAP
  if (LV.zun > 0.001) totalEmissiveRadiance += LV.zun * PREPUSTNOST * PREPUSTNOST * textureCubeUV(envMap, envMapRotation * normalize(uRot * LV.dz), 0.3).rgb * envMapIntensity;
#endif
`;function t_(){let[i,t]=Be(1024,512);t.clearRect(0,0,1024,512),t.fillStyle="#fff";let e=[[90,340],[255,170],[575,170],[715,35],[800,120],[580,340]],n=f=>{t.beginPath(),f.forEach(([g,x],p)=>p?t.lineTo(g,x):t.moveTo(g,x)),t.closePath(),t.fill()},s=512/1425,r=256/515,a=(f,g)=>[f*s,g*r];n(e.map(([f,g])=>a(f,g))),n(e.map(([f,g])=>a(1425-f,515-g))),t.font='500 104px "IBM Plex Sans", Arial, sans-serif',t.textAlign="center",t.textBaseline="middle",t.fillText("313-005",256,322),t.save(),t.translate(512,128);let o=.075;t.translate(8,18);let c=(f,g)=>[f*o*1.2,g*o*1.2];n(e.map(([f,g])=>c(f,g))),n(e.map(([f,g])=>c(1425-f,515-g))),t.restore(),t.font='500 54px "IBM Plex Sans", Arial, sans-serif',t.textAlign="left",t.fillText("Slovenske \u017Eeleznice",650,176);let[l,h]=Be(512,128);h.fillStyle="#000",h.fillRect(0,0,512,128),h.fillStyle="#fff",h.font='600 78px "IBM Plex Mono", monospace',h.textAlign="center",h.textBaseline="middle",h.fillText("V \u0160OLO",256,66);let d=h.getImageData(0,0,512,128).data;t.fillStyle="#000",t.fillRect(512,0,512,128);let u=6;for(let f=0;f<128;f+=u)for(let g=0;g<512;g+=u){let x=d[((f+3)*512+g+3)*4];t.fillStyle=x>90?"#ffa31a":"#1a0d00",t.beginPath(),t.arc(512+g+3,f+3,x>90?2.4:1.4,0,Math.PI*2),t.fill()}return Ve(i,{srgb:!0,aniz:8})}var Vc=null;function Ih(i,t,e,n={zar:0,rdece:0}){let s=new Ji({color:"#ffffff",roughness:.35,metalness:0,clearcoat:.7,clearcoatRoughness:.1}),r={uL:{value:i},uCelni:{value:t?1:0},uNoc:e.uNoc,uSvetloba:e.uSvetloba,uZarometi:{value:n.zar},uRdece:{value:n.rdece},uNapisi:{value:Vc},cModra:{value:new Ot(Es.modra)},cBela:{value:new Ot(Es.bela)},cStreha:{value:new Ot(Es.streha)},cCrna:{value:new Ot(Es.crna)},cSteklo:{value:new Ot(Es.steklo)},cTemna:{value:new Ot(Es.temna)},uKam:{value:new P(0,2,-20)},uRot:{value:new ce},uVrata:{value:new xe(0,0,0,0)},uStrop:e.uStrop,uStropY:e.uStropY,uStropLuc:e.uStropLuc,uStropBarva:e.uStropBarva};return s.userData.u=r,s.onBeforeCompile=a=>{Object.assign(a.uniforms,r),a.vertexShader=a.vertexShader.replace("#include <common>",`#include <common>
attribute vec3 aLiv;
varying vec3 vLiv;
varying vec3 vLok;
varying vec3 vNorLok;
varying vec3 vSvetPos;`).replace("#include <begin_vertex>",`#include <begin_vertex>
vLiv = aLiv;
vLok = position;
vNorLok = normal;
vSvetPos = (modelMatrix * vec4(position, 1.0)).xyz;`),a.fragmentShader=a.fragmentShader.replace("#include <common>",`#include <common>
`+Jx+`
Liv LV;`).replace("#include <color_fragment>",`#include <color_fragment>
LV = liv();
diffuseColor.rgb = LV.col;`).replace("#include <roughnessmap_fragment>",`#include <roughnessmap_fragment>
roughnessFactor = LV.rough;`).replace("#include <emissivemap_fragment>",`#include <emissivemap_fragment>
totalEmissiveRadiance += LV.emis;`).replace("#include <lights_physical_fragment>",`#include <lights_physical_fragment>
material.clearcoat = LV.coat;
material.specularColor = max(material.specularColor, vec3(LV.spec));`).replace("#include <lights_fragment_maps>",`#include <lights_fragment_maps>
`+Kx).replace("#include <lights_fragment_end>",`#include <lights_fragment_end>
`+Qx)},s.customProgramCacheKey=()=>"kiss-liv",s}function e_(){let i=[];i.push([ie(.035,.48,.37,.05),"#25282c",Ht(.0175,0,0)]);let t=new mi;t.moveTo(0,-.028),t.lineTo(.03,-.028),t.lineTo(.055,-.012),t.lineTo(.055,.018),t.lineTo(.035,.028),t.lineTo(0,.028),t.closePath();let e=new Ni(t,{depth:.33,bevelEnabled:!1});e.translate(0,0,-.165);for(let n=0;n<7;n++)i.push([e,"#33373c",Ht(.02,-.2+n*.0665,0)]);return ke(i)}function n_(i){let t=[],e=[[.45,1.3,i-.06],[.12,.98,i-.22]],n=new _e,s=(g,x,p)=>[p,g,x],[[r,a,o],[c,l,h]]=e,d=.07,u=[s(r,-a,o),s(r,a,o),s(c,l,h),s(c,-l,h),s(r,-a,o-d),s(r,a,o-d),s(c,l,h-d),s(c,-l,h-d)],f=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[3,7,6,2],[0,4,7,3],[1,2,6,5]];for(let[g,x,p,m]of f)t.push(...u[g],...u[x],...u[p],...u[g],...u[p],...u[m]);return n.setAttribute("position",new Jt(t,3)),n.computeVertexNormals(),n}function i_(i){let t=[],s="#6c7074",r="#24272a",a="#121416";t.push([new ge(.085,.1,.95,14),r,Ht(i-.42,.92,-.03,0,0,Math.PI/2)]);let o=[];for(let l=0;l<=10;l++)o.push(new mt(.15+l%2*.035,l*.03));let c=new gi(o,18);t.push([c,"#2b2a2c",Ht(i-.78,.92,-.03,0,0,-Math.PI/2)]),t.push([ie(.12,.36,.44,.02),s,Ht(i+.08,.92,-.03)]),t.push([new ge(.105,.105,.03,20),a,Ht(i+.145,.92,-.03+.1,0,0,Math.PI/2)]),t.push([new ri(.105,.018,8,22),"#55595d",Ht(i+.145,.92,-.03+.1,0,Math.PI/2,0)]),t.push([new ge(.09,.09,.05,18),"#5d6165",Ht(i+.16,.92,-.03-.11,0,0,Math.PI/2)]),t.push([ie(.06,.03,.1,.005),"#2a2d30",Ht(i+.2,.92,-.03-.11)]),t.push([ie(.26,.12,.46,.02),"#1d1f22",Ht(i+.02,.92+.25,-.03)]);for(let l of[-1,1])t.push([new pi(.022,3),"#e8b400",Ht(i+.152,.92+.26,-.03+l*.15,0,Math.PI/2,Math.PI/2)]);return t.push([new ri(.14,.022,8,16,Math.PI),a,Ht(i-.05,.92-.3,-.03-.12,0,Math.PI/2,Math.PI)]),t.push([new ri(.12,.02,8,16,Math.PI),a,Ht(i-.1,.92-.28,-.03+.16,0,Math.PI/2,Math.PI)]),t.push([new ge(.014,.014,.42,6),"#7b7f83",Ht(i+.22,.92-.2,-.03+.06,.55,0,.35)]),ke(t)}function s_(){let i=Le.rKolo,t=[[0,-.07],[i-.05,-.07],[i,-.065],[i,.04],[i+.03,.045],[i+.03,.065],[i-.06,.07],[i-.08,.03],[.16,.025],[.13,.08],[0,.08]],e=new gi(t.map(([n,s])=>new mt(n,s)),28);return e.rotateX(Math.PI/2),e}function r_(i){let t=new oe,e=[],n="#2c3035",s="#4a5057",r="#16171a",a="#9c8a45",o=Le.medOsjem/2,c=new mi;c.moveTo(-1.55,.62),c.lineTo(-1.05,.62),c.lineTo(-.7,.44),c.lineTo(.7,.44),c.lineTo(1.05,.62),c.lineTo(1.55,.62),c.lineTo(1.55,.84),c.lineTo(1,.84),c.lineTo(.65,.7),c.lineTo(-.65,.7),c.lineTo(-1,.84),c.lineTo(-1.55,.84),c.closePath();let l=new Ni(c,{depth:.16,bevelEnabled:!0,bevelThickness:.015,bevelSize:.015,bevelSegments:1});for(let p of[-1,1])e.push([l,n,Ht(0,0,p*1-.08)]);e.push([ie(.5,.2,1.9,.03),n,Ht(0,.52,0)]);for(let p of[-o,o])for(let m of[-1,1])e.push([ie(.34,.28,.22,.04),s,Ht(p,Le.rKolo,m*1.04)]),e.push([new ge(.1,.1,.22,10),a,Ht(p+.22*Math.sign(p),.7,m*1.04)]),e.push([new ge(.075,.075,.16,10),s,Ht(p,Le.rKolo,m*1.18,Math.PI/2)]);for(let p of[-1,1])e.push([new ge(.27,.29,.24,18),r,Ht(0,.96,p*.98)]),e.push([new ge(.045,.045,1.3,8),"#5d636a",Ht(0,.78,p*1.27,0,0,Math.PI/2)]);if(i)for(let p of[-o,o])e.push([ie(.62,.5,.95,.05),"#33373c",Ht(p*.42,.45,.15)]);else for(let p of[-o,o])for(let m of[-1,1])e.push([new ge(.31,.31,.05,20),"#5a5f66",Ht(p,Le.rKolo,m*.3,Math.PI/2)]);let h=new ot(ke(e),new Nt({vertexColors:!0,roughness:.62,metalness:.35}));h.castShadow=!0,t.add(h);let d=s_(),u=new ge(.085,.085,1.5,12);u.rotateX(Math.PI/2);let f=ke([[d,"#9aa0a6",Ht(0,0,.75)],[d,"#9aa0a6",Ht(0,0,-.75,0,Math.PI,0)],[u,"#3a3e43"]]),g=new Nt({vertexColors:!0,roughness:.32,metalness:.9}),x=[];for(let p of[-o,o]){let m=new ot(f,g);m.position.set(p,Le.rKolo,0),m.castShadow=!0,t.add(m),x.push(m)}return t.userData.dvojici=x,t}function jd(){let i=new oe,t=new Nt({color:"#8b9198",roughness:.4,metalness:.7}),e=new Nt({color:"#7a2f24",roughness:.55}),n=new Nt({color:"#2a2e33",roughness:.6,metalness:.3});for(let[c,l]of[[-.5,-.45],[-.5,.45],[.5,-.45],[.5,.45]]){let h=new ot(new ge(.06,.07,.26,10),e);h.position.set(c,.13,l),i.add(h)}let s=new ot(ie(1.3,.08,1.05,.02),n);s.position.y=.3,i.add(s);let r=new ot(new ge(.035,.045,1,8),t),a=new ot(new ge(.022,.03,1,8),t),o=new oe;for(let c of[-.11,.11]){let l=new ot(ie(.06,.05,1.5,.01),new Nt({color:"#31343a",roughness:.5}));l.position.x=c,o.add(l)}for(let c of[-1,1]){let l=new ot(new ri(.16,.012,6,12,Math.PI/2),t);l.position.set(0,-.16,c*.75),l.rotation.y=Math.PI/2,l.rotation.z=c>0?0:Math.PI/2,o.add(l)}return i.add(r,a,o),i.userData.dvigni=c=>{let f=Math.max(.12,c-.3),g=-.35,x=Math.hypot(g- -.2,f),p=Math.atan2(f,g- -.2)-Math.acos(Fe((1.2*1.2+x*x-1.3*1.3)/(2*1.2*x),-1,1)),m=-.2+1.2*Math.cos(p),S=.3+1.2*Math.sin(p),E=(v,b,M,A,_)=>{v.position.set((b+A)/2,(M+_)/2,0),v.rotation.z=Math.atan2(_-M,A-b)-Math.PI/2,v.scale.y=Math.hypot(A-b,_-M)};E(r,-.2,.3,m,S),E(a,m,S,g,.3+f),o.position.set(g,.3+f+.03,0)},i.userData.dvigni(1),i.traverse(c=>{c.isMesh&&(c.castShadow=!0)}),i}function a_(i,t,e){let n=new oe,s=(i+t)/2,r=i-.9,a=t+.9,o=(M,A,_,T,I,L,N)=>[new Re(T-M,I-A,L-_),N,Ht((M+T)/2,(A+I)/2,(_+L)/2)],c=[o(r,.5,-1.37,a,.58,1.37,"#41454a"),o(i,.58,-1.37,t,.586,-1.27,"#d8a817"),o(i,.58,1.27,t,.586,1.37,"#d8a817"),o(i-.02,.555,-1.43,t+.02,.587,-1.3,"#8e949a"),o(i,.44,-1.42,t,.555,-1.36,"#16181b"),o(r,2.5,-1.37,a,2.58,1.37,"#d5d6d3"),o(r,.58,1.33,a,2.5,1.37,"#c5c8c9"),o(i,.58,1.31,t,2.48,1.33,"#33475f"),o(s-.006,.58,1.304,s+.006,2.48,1.31,"#121416"),o(i-.07,.44,-1.42,i,2.56,-1.29,"#2b2e33"),o(t,.44,-1.42,t+.07,2.56,-1.29,"#2b2e33"),o(i-.07,2.48,-1.42,t+.07,2.56,-1.29,"#2b2e33"),o(r-.05,.58,-1.37,r,2.5,-.56,"#cfd2d4"),o(r-.05,.58,.56,r,2.5,1.37,"#cfd2d4"),o(r-.05,2.22,-.56,r,2.5,.56,"#cfd2d4"),o(r-.06,.58,-.58,r+.01,2.24,-.55,"#8b9196"),o(r-.06,.58,.55,r+.01,2.24,.58,"#8b9196"),o(r-.06,2.21,-.58,r+.01,2.24,.58,"#8b9196"),o(r+.002,2.27,-.42,r+.014,2.43,.42,"#0c0d0f"),o(r-2.6,.58,-.62,r-.05,4.1,-.56,"#c7cacc"),o(r-2.6,.58,.56,r-.05,4.1,.62,"#c7cacc"),o(r-2.65,2.4,-.62,r-2.6,4.1,.62,"#cfd2d4"),o(r-2.6,4.1,-.62,r-.05,4.16,.62,"#d5d6d3"),o(a,.58,-1.37,a+.05,2.5,1.37,"#cfd2d4")];for(let M=0;M<8;M++){let A=.58+.245*(M+1);c.push(o(r-.27*(M+1),.58,-.55,r-.27*M,A,.55,"#555a60")),c.push(o(r-.27*M-.035,A-.012,-.55,r-.27*M,A+.002,.55,"#d8a817"))}let l=new Nt({vertexColors:!0,roughness:.72});l.onBeforeCompile=M=>{M.uniforms.uNotrSv=e.uNotrSv,M.fragmentShader=M.fragmentShader.replace("#include <common>",`#include <common>
uniform float uNotrSv;`).replace("#include <emissivemap_fragment>",`#include <emissivemap_fragment>
totalEmissiveRadiance += diffuseColor.rgb * uNotrSv;`)},l.customProgramCacheKey=()=>"preddverje";let h=new ot(ke(c),l);h.receiveShadow=!0,n.add(h);let d=new Nt({color:"#000",emissive:"#fff3df",emissiveIntensity:2.2}),u=(t-i)*.25,f=ke([o(s-.55,2.486,-.3,s+.55,2.5,.3,"#fff"),o(r-2,4.085,-.06,r-.6,4.1,.06,"#fff")]);n.add(new ot(f,d));let g=new Nt({color:"#000",emissive:"#c4d1dc",emissiveIntensity:.8}),x=ke([o(i+u-.11,1.14,1.298,i+u+.11,2.09,1.305,"#fff"),o(s+u-.11,1.14,1.298,s+u+.11,2.09,1.305,"#fff")]);n.add(new ot(x,g));let p=new Nt({color:"#c3c8cd",metalness:.8,roughness:.3}),m=[];for(let[M,A]of[[i+.08,-1.2],[t-.08,-1.2],[i+.08,1.2],[t-.08,1.2]])m.push([new ge(.018,.018,1.92,10),"#c3c8cd",Ht(M,1.54,A)]);let S=Math.hypot(2.2,1.9);m.push([new ge(.02,.02,S,8),"#c3c8cd",Ht(r-1.1,2.45,-.5,0,0,Math.atan2(2.2,1.9))]),n.add(new ot(ke(m),p));let E=new Xe(.8,.2),v=E.attributes.uv;for(let M=0;M<v.count;M++)v.setXY(M,.5+v.getX(M)*.5,.75+v.getY(M)*.25);let b=new ot(E,new Nt({color:"#000",emissive:"#ffffff",emissiveMap:Vc,emissiveIntensity:1.6}));return b.rotation.y=Math.PI/2,b.position.set(r+.016,2.35,0),n.add(b),n.visible=!1,n.userData={zunajMat:g,lucMat:d},n}function o_(i,t){let[e,n]=Be(64,200);n.fillStyle=Es.modra,n.fillRect(0,0,64,200),n.fillStyle="#0b0f14",n.beginPath(),n.roundRect(22,66,20,94,8),n.fill();let s=new Ji({map:Ve(e),roughness:.3,clearcoat:.7}),r=(i+t)/2,a=(t-i)/2,o=new oe,c=[-1,1].map(l=>{let h=new ot(new Re(a,2.02,.025),s);return h.position.set(r+l*a/2,.46+1.01,-1.42),h.userData={x:r+l*a/2,st:l},h.castShadow=!0,o.add(h),h});return o.visible=!1,o.userData.krila=c,o}function Jd(){Vc=Vc||t_();let i={uNoc:{value:0},uSvetloba:{value:1},uNotrSv:{value:.24},uStrop:{value:new xe(-31,31,2.35,7.4)},uStropY:{value:4.1},uStropLuc:{value:.6},uStropBarva:{value:new Ot(.15,.145,.14)}},t=Yd(Le.Lc,!0),e=Yd(Le.Lv,!1),n=Ih(Le.Lc,!0,i,{zar:1,rdece:0}),s=Ih(Le.Lc,!0,i,{zar:0,rdece:1}),r=Ih(Le.Lv,!1,i),a=new oe;a.name="vlak";let o=new Nt({vertexColors:!0,roughness:.55,metalness:.25}),c=new Nt({color:"#141618",roughness:.85,side:fn}),l=new Nt({color:"#1b1d20",roughness:.6,metalness:.2,side:fn}),h=e_();function d(ft,U){ft.add(new ot($x(U),c));let V=new ot(n_(U),l);V.castShadow=!0,ft.add(V);for(let Kt of[-1,1]){let it=Kt*.955,ut=.885,Y=new ot(h,o);Y.position.set(U-Pn(ut,it),ut,it),Y.rotation.y=-Math.atan2(Pn(ut,it+.02)-Pn(ut,it-.02),.04),Y.castShadow=!0,ft.add(Y)}let dt=new ot(i_(U),o);dt.castShadow=!0,ft.add(dt);let Mt=new ot(ie(.025,.85,.03,.008),new Nt({color:"#0d0d0e",roughness:.5})),yt=2.75,It=-.42;Mt.position.set(U-Pn(yt,It)+.03,yt,It),Mt.rotation.z=Math.atan2(1,.51)-Math.PI/2,Mt.rotation.x=.45,ft.add(Mt)}function u(ft,U){let V=[],dt="#5b6168";U?(V.push([ie(3.4,.16,1.3,.05),"#3d4248",Ht(2.4,4.44,0)]),V.push([ie(2,.14,1.2,.05),dt,Ht(ft-7.2,4.46,0)])):(V.push([ie(2.6,.2,1.5,.06),dt,Ht(2.3,4.45,0)]),V.push([ie(2.6,.2,1.5,.06),dt,Ht(ft-2.3,4.45,0)]));let yt=new ot(ke(V),o);return yt.castShadow=!0,yt}function f(){let ft=[];for(let V=0;V<7;V++)ft.push([ie(.08,3.3,2.35,.03),V%2?"#1c1e21":"#2a2d31",Ht(-.42+V*.14,2.5,0)]);let U=new ot(ke(ft),o);return U.castShadow=!0,U}let g=[],x=[{L:Le.Lc,celni:!0,obrnjen:!1,mat:n},{L:Le.Lv,celni:!1,obrnjen:!1,mat:r},{L:Le.Lc,celni:!0,obrnjen:!0,mat:s}];for(let ft of x){let U=new oe,V=new oe,dt=new ot(ft.celni?t:e,ft.mat);dt.castShadow=!0,dt.receiveShadow=!0,V.add(dt),V.add(u(ft.L,ft.celni)),ft.celni&&d(V,ft.L),V.position.x=-ft.L/2,U.add(V),ft.obrnjen&&(U.rotation.y=Math.PI);let Mt=new oe;Mt.add(U),a.add(Mt),g.push({...ft,ovoj:Mt,notr:V})}let p=jd();p.position.set(4.2,4.4,0),p.rotation.y=Math.PI,p.userData.dvigni(1.07),g[2].notr.add(p);let m=jd();m.position.set(4.2,4.4,0),m.rotation.y=Math.PI,m.userData.dvigni(.2),g[0].notr.add(m);let S=[f(),f()];S.forEach(ft=>a.add(ft));let E=[],v=ft=>{let U=r_(ft);return a.add(U),E.push(U),U},b=[v(!1),v(!0),v(!1),v(!1),v(!0),v(!1)],M=new P,A=new P,_=new P,T=new P(0,1,0),I=new P,L=new P,N=new ue,B=null,D=0,O=(ft,U)=>{I.crossVectors(U,T).normalize(),L.crossVectors(I,U).normalize(),N.makeBasis(U,L,I),ft.quaternion.setFromRotationMatrix(N)};function $(ft,U){let{Lc:V,Lv:dt,rega:Mt,aVozF:yt,rVoz:It}=Le,Kt=[U,U-V-Mt,U-V-Mt-dt-Mt],it=[[Kt[0]-yt,Kt[0]-V+It],[Kt[1]-It,Kt[1]-dt+It],[Kt[2]-It,Kt[2]-V+yt]];g.forEach((Y,st)=>{let[vt,Vt]=it[st];ft.tocka(vt,M),ft.tocka(Vt,A),_.subVectors(M,A).normalize();let St=st===2?Y.L/2-It:Y.L/2-(st===0?yt:It),Xt=st===2?-(Y.L/2-yt):-(Y.L/2-It),Qt=(0-Xt)/(St-Xt);Y.ovoj.position.lerpVectors(A,M,Qt),O(Y.ovoj,_)});for(let Y=0;Y<2;Y++){let st=Kt[Y+1]+Mt/2;ft.tocka(st,M),ft.smer(st,_),S[Y].position.copy(M),O(S[Y],_)}let ut=it.flat();B!==null&&(D-=(U-B)/Le.rKolo),B=U,ut.forEach((Y,st)=>{ft.tocka(Y,M),ft.smer(Y,_),b[st].position.copy(M),O(b[st],_);for(let vt of b[st].userData.dvojici)vt.rotation.z=D})}let J=Le.Lv-5.95,W=Le.Lv-4.65,G=a_(J,W,i),K=o_(J,W);g[1].notr.add(G,K);function nt(ft){r.userData.u.uVrata.value.set(J,W,ft,0),G.visible=K.visible=ft>.001;let U=Zd(ft/.18);for(let V of K.userData.krila)V.position.x=V.userData.x+V.userData.st*.63*Zd((ft-.12)/.88),V.position.z=-1.42-.045*U}let Et=(ft,U,V,dt=new P)=>(g[1].notr.updateWorldMatrix(!0,!1),g[1].notr.localToWorld(dt.set(ft,U,V)));function pt(ft=!0,U=0){i.uNoc.value=U,i.uNotrSv.value=fe(.24,.55,U),i.uStropLuc.value=fe(.6,2.4,U),i.uStropBarva.value.setRGB(fe(.15,.2,U),fe(.145,.17,U),fe(.14,.13,U)),G.userData.zunajMat.emissiveIntensity=fe(.8,.05,U),n.userData.u.uZarometi.value=ft?1:0}let Ft=new ue;function Dt(ft){for(let U of g){U.notr.updateWorldMatrix(!0,!1);let V=U.mat.userData.u;Ft.copy(U.notr.matrixWorld).invert(),V.uKam.value.copy(ft.position).applyMatrix4(Ft),V.uRot.value.setFromMatrix4(U.notr.matrixWorld)}}return{skupina:a,postavi:$,nastaviLuci:pt,skupni:i,vozovi:g,pant:p,odpriVrata:nt,vrataLok:Et,kamera:Dt,zadnjiS:()=>B,VRATA:{xa:J,xb:W}}}var Zd=i=>{let t=Fe(i);return t*t*(3-2*t)};var le={z0:1.68,z1:8.2,y:.55,x0:-95,x1:95},Gc={x:0,y:3.32,z:3.05,r:.4},Lh={x:5.2,y:3.38,z:4.3};function c_(){let[e,n]=Be(512,1664),[s,r]=Be(512,1664),a=Xn(21),o=mn(9),c=256;n.fillStyle="#9b9890",n.fillRect(0,0,512,1664),r.fillStyle="#808080",r.fillRect(0,0,512,1664);let l=.4*c;for(let f=.32*c;f<1664;f+=l)for(let g=0;g<512;g+=l){let x=140+o()*26-13;n.fillStyle=`rgb(${x},${x-3},${x-9})`,n.fillRect(g+2,f+2,l-4,l-4),r.fillStyle="#9a9a9a",r.fillRect(g+3,f+3,l-6,l-6)}n.fillStyle="#d9d6cd",n.fillRect(0,0,512,.32*c),r.fillStyle="#b0b0b0",r.fillRect(0,0,512,.32*c),n.fillStyle="#e3b419",n.fillRect(0,.82*c,512,.1*c),n.fillStyle="#cfcbc0",n.fillRect(0,1.02*c,512,.4*c);for(let f=0;f<512;f+=18)r.fillStyle="#c8c8c8",r.fillRect(f+3,1.04*c,9,.36*c),n.fillStyle="#e2ded3",n.fillRect(f+3,1.04*c,9,.36*c);let h=n.getImageData(0,0,512,1664);for(let f=0;f<1664;f++)for(let g=0;g<512;g++){let x=(f*512+g)*4,p=.9+.12*wn(a,g/60,f/60,4)+.04*(o()-.5);h.data[x]*=p,h.data[x+1]*=p,h.data[x+2]*=p}n.putImageData(h,0,0);let d=Ve(e,{ponavljaj:!0}),u=Ve(Aa(s,2.2),{srgb:!1,ponavljaj:!0});return{bar:d,nor:u}}function l_(){let[t,e]=Be(1024,1024),n=1024/2,s=e.createRadialGradient(n,n,0,n,n,n);s.addColorStop(0,"#fbfbf8"),s.addColorStop(.85,"#f1f0ea"),s.addColorStop(1,"#d9d7cf"),e.fillStyle=s,e.beginPath(),e.arc(n,n,n,0,Math.PI*2),e.fill(),e.translate(n,n);for(let r=0;r<60;r++)e.save(),e.rotate(r/60*Math.PI*2),e.fillStyle="#121212",r%5===0?e.fillRect(-n*.034,-n*.94,n*.068,n*.24):e.fillRect(-n*.011,-n*.94,n*.022,n*.075),e.restore();return Ve(t,{aniz:16})}function h_(){let[e,n]=Be(1024,300),[s,r]=Be(1024,300),a=Ve(e,{aniz:8}),o=null;function c(l,h="07:42"){let d=l+h;if(d===o)return;o=d,r.fillStyle="#000",r.fillRect(0,0,1024,300),r.fillStyle="#fff",r.textBaseline="middle",r.font='600 46px "IBM Plex Mono", monospace',r.fillText("ODHOD",36,52),r.fillText("SMER",270,52),r.fillText("TIR",880,52),r.font='600 92px "IBM Plex Mono", monospace',r.fillText(h,30,150),r.fillText("V \u0161olo",300,150),r.fillText("1",905,150),r.font='600 62px "IBM Plex Mono", monospace',l>0&&r.fillText(`zamuda ${l} min`,300,245);let u=r.getImageData(0,0,1024,300).data;n.fillStyle="#050403",n.fillRect(0,0,1024,300);let f=6;for(let g=0;g<300;g+=f)for(let x=0;x<1024;x+=f){let p=u[((g+3)*1024+x+3)*4],m=g>200?"#ff7a1a":"#ffb21f";n.fillStyle=p>100?m:"#140b02",n.beginPath(),n.arc(x+3,g+3,p>100?2.5:1.5,0,Math.PI*2),n.fill()}a.needsUpdate=!0}return c(0),{tex:a,narisi:c}}function Kd(i,t,e,n={}){let r=Math.round(i*48),a=Math.round((t*3.6+1)*48),[o,c]=Be(r,a),[l,h]=Be(r,a),d=mn(n.seme||4),u=Xn(n.seme||4);c.fillStyle=n.omet||"#e6d6b4",c.fillRect(0,0,r,a),h.fillStyle="#000",h.fillRect(0,0,r,a),c.fillStyle=n.podstavek||"#b7ab94",c.fillRect(0,a-.7*48,r,.7*48);for(let x=1;x<t;x++){let p=a-(.7+x*3.6)*48;c.fillStyle="#f2ecdf",c.fillRect(0,p-6,r,12)}c.fillStyle="#f4efe4",c.fillRect(0,0,r,.35*48);let f=i/e;for(let x=0;x<t;x++)for(let p=0;p<e;p++){let m=(p+.5)*f*48,S=a-(.7+x*3.6+.9)*48,E=1.15*48,v=(x===0&&n.loki?2.1:1.6)*48,b=x===0&&n.vrata&&n.vrata.includes(p),M=b?2.6*48:v,A=b?a-.7*48-M:S-v;c.fillStyle="#f6f2e8",c.fillRect(m-E/2-7,A-7,E+14,M+14),x===0&&n.loki&&(c.beginPath(),c.arc(m,A,E/2+7,Math.PI,0),c.fill()),c.fillStyle=b?"#3d4a3a":"#283035",c.fillRect(m-E/2,A,E,M),x===0&&n.loki&&(c.beginPath(),c.arc(m,A,E/2,Math.PI,0),c.fill()),b||(c.fillStyle="#e9e4d8",c.fillRect(m-2,A,4,M),c.fillRect(m-E/2,A+M*.38,E,4),d()<(n.svetijo??.35)&&(h.fillStyle=`rgb(${200+d()*55},${150+d()*50},${80+d()*40})`,h.fillRect(m-E/2+3,A+3,E-6,M-6)))}let g=c.getImageData(0,0,r,a);for(let x=0;x<a;x++)for(let p=0;p<r;p++){let m=(x*r+p)*4,S=.93+.09*wn(u,p/40,x/40,3)-.06*Math.max(0,(x-a*.8)/(a*.2))*0;g.data[m]*=S,g.data[m+1]*=S,g.data[m+2]*=S}return c.putImageData(g,0,0),{bar:Ve(o),emis:Ve(l)}}function xr(i=[150,66,44]){let[n,s]=Be(256,256),[r,a]=Be(256,256),o=mn(13),c=32,l=24;for(let h=0;h<256;h+=c){let d=h/c%2?l/2:0;for(let u=-l;u<256+l;u+=l){let f=.82+o()*.3;s.fillStyle=`rgb(${i[0]*f|0},${i[1]*f|0},${i[2]*f|0})`,s.fillRect(u+d,h,l-1,c);let g=a.createLinearGradient(0,h,0,h+c);g.addColorStop(0,"#202020"),g.addColorStop(1,"#d0d0d0"),a.fillStyle=g,a.fillRect(u+d,h,l-1,c),a.fillStyle="#404040",a.fillRect(u+d+l-2,h,2,c)}}return{bar:Ve(n,{ponavljaj:!0}),nor:Ve(Aa(r,2.5),{srgb:!1,ponavljaj:!0})}}function ws(i,t,e,n=.5){let s=i/2+n,r=t/2+n,a=r>s;a&&([s,r]=[r,s]);let o=r,c=Math.hypot(o,e)/o,l=[-s+o,e,0],h=[s-o,e,0],d=[[[s,0,-r],[-s,0,-r],l,h],[[-s,0,r],[s,0,r],h,l],[[-s,0,-r],[-s,0,r],l],[[s,0,r],[s,0,-r],h]],u=[],f=[],g=(p,m)=>m<2?[p[0],(r-Math.abs(p[2]))*c]:[p[2],(s-Math.abs(p[0]))*c];if(d.forEach((p,m)=>{let S=p.length===4?[[0,1,2],[0,2,3]]:[[0,1,2]];for(let E of S)for(let v of E)u.push(...p[v]),f.push(...g(p[v],m))}),a)for(let p=0;p<u.length;p+=3){let m=u[p];u[p]=-u[p+2],u[p+2]=m}let x=new _e;return x.setAttribute("position",new Jt(u,3)),x.setAttribute("uv",new Jt(f,2)),x.computeVertexNormals(),x}function u_(){let i=new oe,t=Gc.r,e=new Nt({color:"#2a2d31",roughness:.38,metalness:.6}),n=new ot(new ge(t+.04,t+.04,.17,64,1,!0),e);n.rotation.z=Math.PI/2;let s=new ot(new ri(t+.025,.02,12,64),e),r=s.clone();s.rotation.y=Math.PI/2,s.position.x=.085,r.rotation.y=Math.PI/2,r.position.x=-.085,i.add(n,s,r);let a=l_(),o=new Nt({map:a,emissiveMap:a,emissive:"#fff8ea",emissiveIntensity:.35,roughness:.6}),c=[],l=new Nt({color:"#0e0e0e",roughness:.5}),h=new Nt({color:"#c81e14",roughness:.45,emissive:"#3a0500"}),d=new si({color:"#000",transparent:!0,opacity:.16,depthWrite:!1}),u=(p,m,S,E=0)=>{let v=new mi;return v.moveTo(-m/2,-E),v.lineTo(m/2,-E),v.lineTo(S/2,p),v.lineTo(-S/2,p),v.closePath(),new Ni(v,{depth:.004,bevelEnabled:!1})},f=()=>{let p=new mi;p.moveTo(-.0035,-.11*t/.4),p.lineTo(.0035,-.11*t/.4),p.lineTo(.002,t*.86),p.lineTo(-.002,t*.86),p.closePath();let m=new Ni(p,{depth:.003,bevelEnabled:!1}),S=new ge(.022,.022,.003,24);return S.rotateX(Math.PI/2),S.translate(0,-.085*t/.4,.0015),ke([[m,"#c81e14"],[S,"#c81e14"]])};for(let p of[1,-1]){let m=new oe,S=new ot(new pi(t,72),o);m.add(S);let E=new ot(u(t*.64,.036,.026,t*.16),l),v=new ot(u(t*.9,.028,.017,t*.18),l),b=new ot(f(),new Nt({vertexColors:!0,roughness:.45,emissive:"#2a0400"}));E.position.z=.006,v.position.z=.011,b.position.z=.016;let M=new ot(E.geometry,d),A=new ot(v.geometry,d),_=new ot(b.geometry,d);for(let L of[M,A,_])L.position.set(.006,-.008,.0015),L.scale.set(1.04,1.02,.2);let T=new ot(new ge(.012,.012,.006,16),l);T.rotation.x=Math.PI/2,T.position.z=.02,m.add(M,A,_,E,v,b,T);let I=new ot(new pi(t+.005,64),new Ji({color:"#ffffff",transparent:!0,opacity:.08,roughness:.05,metalness:0,clearcoat:1,depthWrite:!1}));I.position.z=.03,m.add(I),m.rotation.y=p>0?-Math.PI/2:Math.PI/2,m.position.x=p*-.07,i.add(m),c.push({ure:E,min:v,sek:b,sU:M,sM:A,sS:_})}let g=new ot(ke([[new ge(.025,.025,.55,10),"#2a2d31",Ht(0,t+.32,0)],[ie(.06,.06,.3,.01),"#2a2d31",Ht(0,t+.6,0)]]),new Nt({vertexColors:!0,roughness:.4,metalness:.6}));i.add(g),i.position.set(Gc.x,Gc.y,Gc.z),i.traverse(p=>{p.isMesh&&p.material!==d&&(p.castShadow=!0)});function x(p){let m=Math.floor(p/3600)%12,S=Math.floor(p/60)%60,E=p%60,v=E<58.5?E/58.5*Math.PI*2:0,b=S/60*Math.PI*2,M=(m+S/60)/12*Math.PI*2;for(let A of c)A.ure.rotation.z=-M,A.min.rotation.z=-b,A.sek.rotation.z=-v,A.sU.rotation.z=-M,A.sM.rotation.z=-b,A.sS.rotation.z=-v}return{skupina:i,nastavi:x,obraz:o}}var d_={prsi:.199,pas:.153,globina:.69,nad:.062,pod:.049,vrat:.054,stegno:.079,meca:.058,trap:.014,kolk:.095};function Wc(i,t,e,n=10,s=0,r=.4){let a=[];for(let o=0;o<=6;o++){let c=o/6*Math.PI/2;a.push(new mt(t*Math.sin(c),-e-t*Math.cos(c)))}if(s)for(let[o,c]of[[.8,fe(t,s,.55)],[r+.12,s*.985],[r,s],[r*.45,fe(i,s,.7)]])a.push(new mt(c,-e*o));for(let o=0;o<=6;o++){let c=o/6*Math.PI/2;a.push(new mt(i*Math.cos(c),i*Math.sin(c)))}return new gi(a,n)}function f_(){let[i,t]=Be(512,320);t.fillStyle="#1d2127",t.fillRect(0,0,512,320),t.fillStyle="#252a31",t.fillRect(0,0,512,22),t.fillRect(0,22,34,298),t.fillStyle="#f0934f",t.fillRect(40,4,90,14);let e=[[["#c678dd","def "],["#61afef","zamuda"],["#abb2bf","(vlak, postaja):"]],[["#7f848e","    # koliko vlak res zamuja"]],[["#abb2bf","    red = urnik[vlak][postaja]"]],[["#abb2bf","    res = meritve.zadnja(vlak)"]],[["#c678dd","    return "],["#abb2bf","res - red"]],[],[["#c678dd","for "],["#abb2bf","vlak "],["#c678dd","in "],["#61afef","vlaki_danes"],["#abb2bf","():"]],[["#abb2bf","    z = "],["#61afef","zamuda"],["#abb2bf","(vlak, "],["#98c379",'"\u0161ola"'],["#abb2bf",")"]],[["#61afef","    zapisi"],["#abb2bf","(vlak, z)"]],[],[["#7f848e","# +13 min"]]];return t.font='500 17px "IBM Plex Mono", monospace',t.textBaseline="middle",e.forEach((n,s)=>{let r=40+s*25;t.fillStyle="#5c6370",t.fillText(String(s+1).padStart(2," "),6,r);let a=44;for(let[o,c]of n)t.fillStyle=o,t.fillText(c,a,r),a+=t.measureText(c).width}),t.fillStyle="#abb2bf",t.fillRect(44+11*10.2,281,2,18),Ve(i,{aniz:4})}function Qd(i=d_){let t=new oe,e=(Ft,Dt=.75)=>new Nt({color:Ft,roughness:Dt}),n=e("#2c3850"),s=e("#4a5461",.85),r=e("#dcae92",.62),a=e("#3a2a1e",.8),o=e("#f0934f",.7),c=e("#b9622c",.7),l=e("#e6e4df",.6),h=e("#9c9890",.7),d=new oe;t.add(d);let u=.89,f=Ft=>Ft.map(([Dt,ft])=>new mt(Dt,ft)),g=new ot(new gi(f([[0,.78],[i.pas-.03,.79],[i.pas-.012,.84],[i.pas-.014,.9],[0,.92]]),18),n);g.scale.set(.66,1,1);let x=new ot(new gi(f([[0,.835],[i.pas+.002,.84],[i.pas+.009,.9],[i.pas+.006,.97],[i.pas,1.05],[fe(i.pas,i.prsi,.45),1.15],[i.prsi-.008,1.26],[i.prsi,1.34],[i.prsi-.02+i.trap*.6,1.41],[.11+i.trap,1.455],[.05+i.trap*.5,1.475],[0,1.476]]),22),s);x.scale.set(i.globina,1,1);let p=new ot((()=>{let Ft=new ri(.088+i.trap*.8,.044+i.trap*.3,8,14,Math.PI);return Ft.rotateX(Math.PI/2),Ft.rotateY(-Math.PI/2),Ft.scale(1,1.05,1.05),Ft})(),s);p.position.set(-.02,1.468,0);let m=new ot(new ge(i.vrat,i.vrat*1.12,.1,14),r);m.position.y=1.5;let S=new oe;S.position.y=1.54;let E=new ot(new Vn(.1,24,18),r);E.scale.set(.92,1.1,.84),E.position.set(.012,.085,0);let v=new ot(new Vn(.106,24,16,0,Math.PI*2,0,Math.PI*.56),a);v.scale.set(.95,1.08,.9),v.position.set(0,.1,0),v.rotation.z=.42;let b=new ot(new Vn(.104,20,14,-Math.PI/2,Math.PI,0,Math.PI*.74),a);b.scale.set(.95,1.1,.89),b.position.set(.006,.088,0);for(let Ft of[-1,1]){let Dt=new ot(new Vn(.022,10,8),r);Dt.scale.set(.9,1.5,.55),Dt.position.set(-.004,.075,Ft*.083),S.add(Dt)}let M=new ot(new Vn(.06,14,10,0,Math.PI*2,0,Math.PI*.5),a);M.scale.set(.9,.55,1.3),M.position.set(.055,.15,0),M.rotation.z=-.5,S.add(E,v,b,M);let A=i.prsi*i.globina,_=new oe,T=new ot(ie(.15,.4,.29,.05),o),I=new ot(ie(.05,.16,.22,.03),c);I.position.set(-.085,-.09,0),_.add(T,I);let L=-(A+.07);_.position.set(L,1.17,0),d.add(g,x,p,m,S,_);let N=[];for(let Ft of[-1,1]){let Dt=new ot(ie(.014,.3,.042,.006),c);Dt.position.set(A-.006,1.2,Ft*(.085+i.trap)),Dt.rotation.z=.08;let ft=new ot(ie(A*2+.02,.014,.042,.006),c);ft.position.set(0,1.43+i.trap*.5,Ft*(.09+i.trap)),d.add(Dt,ft),N.push(Dt,ft)}let B=[];for(let Ft of[-1,1]){let Dt=new oe;Dt.position.set(0,u,Ft*i.kolk),Dt.add(new ot(Wc(i.stegno,i.stegno*.72,.43,12,i.stegno*1.03,.3),n));let ft=new oe;ft.position.y=-.43,ft.add(new ot(Wc(i.meca*.9,i.meca*.66,.415,12,i.meca,.3),n));let U=new oe;U.position.y=-.415;let V=new ot(ie(.25,.07,.094,.03),l);V.position.set(.055,-.03,0);let dt=new ot(ie(.255,.022,.098,.01),h);dt.position.set(.055,-.064,0),U.add(V,dt),ft.add(U),Dt.add(ft),d.add(Dt),B.push({kolk:Dt,koleno:ft,gleznjar:U})}let D=[],O=.07+(i.nad-.047)*1.5;for(let Ft of[-1,1]){let Dt=new oe;Dt.position.set(0,1.375,Ft*(i.prsi+i.nad-.024)),Dt.rotation.x=-Ft*O;let ft=new oe;ft.add(new ot(Wc(i.nad*1.14,i.nad*.78,.27,12,i.nad*1.06,.45),s));let U=new oe;U.position.y=-.27,U.add(new ot(Wc(i.pod,i.pod*.76,.23,12,i.pod*1.05,.25),s));let V=new ot(new Vn(.045,12,10),r);V.scale.set(.42,1.75,.88),V.position.set(.004,-.305,0),U.add(V),ft.add(U),Dt.add(ft),d.add(Dt),D.push({rama:Dt,zamah:ft,komolec:U,dlan:V})}let $=new ot(ie(.009,.15,.072,.008),new Nt({color:"#111",roughness:.3,emissive:"#5c7da8",emissiveIntensity:.6}));$.position.set(.035,-.32,0),$.rotation.z=-.2,D[1].komolec.add($);let J=new Nt({color:"#9aa0a6",roughness:.35,metalness:.6}),W=new oe,G=new ot(ie(.24,.018,.33,.006),J),K=new oe,nt=new ot(ie(.012,.21,.33,.005),J);nt.position.set(.006,.105,0);let Et=new ot(new Xe(.31,.19),new Nt({color:"#000",emissive:"#ffffff",emissiveMap:f_(),emissiveIntensity:1.15}));Et.rotation.y=-Math.PI/2,Et.position.set(-.002,.108,0),K.add(nt,Et),K.position.set(.12,.009,0),K.rotation.z=-.3,W.add(G,K),W.visible=!1,d.add(W),t.traverse(Ft=>{Ft.isMesh&&(Ft.castShadow=!0)});function pt(Ft=0,Dt=0,ft=1,U=0){let V=Ft/1.4*Math.PI*2,dt=Ft>0?1-U:0;B.forEach((Mt,yt)=>{let It=V+(yt?Math.PI:0),Kt=.4*Math.sin(It)*dt,it=-(.06+.8*Math.max(0,Math.cos(It))**2)*dt;Mt.kolk.rotation.z=Kt*(1-U)+U*1.48,Mt.koleno.rotation.z=it*(1-U)-U*1.5,Mt.gleznjar.rotation.z=-(Mt.kolk.rotation.z+Mt.koleno.rotation.z)*(dt?.75:1)}),D.forEach((Mt,yt)=>{let It=V+(yt?0:Math.PI),Kt=yt===1?ft:0,it=.32*Math.sin(It)*dt;Mt.zamah.rotation.z=(it*(1-Kt)+Kt*.25)*(1-U)+U*.25,Mt.komolec.rotation.z=((.18+.2*Math.max(0,Math.sin(It))*dt)*(1-Kt)+Kt*1.75)*(1-U)+U*.78,Mt.rama.rotation.x=-(yt?1:-1)*(O-Kt*.1)}),$.visible=U<.5,W.visible=U>.5;for(let Mt of N)Mt.visible=U<.5;U>.5?(_.position.set(-.04,1.035,-.52),_.rotation.set(0,.35,0)):(_.position.set(L,1.17,0),_.rotation.set(0,0,0)),d.position.y=U*-.36+(dt?-.018*Math.abs(Math.sin(V)):0),d.rotation.y=dt*.05*Math.sin(V),W.position.set(.27,u+.009+i.stegno,0),S.rotation.y=Dt,S.rotation.z=-.42*ft*(1-U)-U*.32}return pt(0),{skupina:t,poza:pt,tel:$,zaslon:Et}}function tf(){let i=new oe,t=mn(17),e=c_();e.bar.repeat.set((le.x1-le.x0)/2,1),e.nor.repeat.copy(e.bar.repeat);let n=le.z1-le.z0,s=le.x1-le.x0,r=new Xe(s,n);r.rotateX(-Math.PI/2);let a=r.attributes.uv;for(let Y=0;Y<a.count;Y++)a.setXY(Y,a.getX(Y),1-a.getY(Y));let o=new ot(r,new Nt({map:e.bar,normalMap:e.nor,roughness:.88}));o.material.map.wrapT=Hn,o.position.set((le.x0+le.x1)/2,le.y,(le.z0+le.z1)/2),o.receiveShadow=!0,i.add(o);let c=new Nt({color:"#8f8b83",roughness:.92}),l=new ot(new Re(s,1.45,n),c);l.position.set((le.x0+le.x1)/2,le.y-.75,(le.z0+le.z1)/2),l.receiveShadow=!0,i.add(l);let h=new ot(new Re(s,.12,.34),new Nt({color:"#cfccc4",roughness:.8}));h.position.set((le.x0+le.x1)/2,le.y-.07,le.z0+.13),h.receiveShadow=!0,i.add(h);for(let Y of[-1,1]){let st=new ot(new Re(8,.1,n),c);st.position.set(Y*(s/2+3.6),le.y-.32,(le.z0+le.z1)/2),st.rotation.z=Y*.07,st.receiveShadow=!0,i.add(st)}let d=-31,u=31,f=2.35,g=7.4,x=le.y+3.55,p=new Nt({color:"#3a3f45",roughness:.5,metalness:.55}),m=new ot(ie(u-d,.28,g-f,.03),new Nt({color:"#d4d2cc",roughness:.7}));m.position.set(0,x+.14,(f+g)/2),m.castShadow=!0,m.receiveShadow=!0;let S=new ot(ie(u-d+.1,.34,.08,.02),p);S.position.set(0,x+.15,f),i.add(m,S);let E=new Rn(ie(.2,x-le.y,.2,.02),p,9),v=new ue;for(let Y=0;Y<9;Y++)v.makeTranslation(d+3+Y*7,le.y+(x-le.y)/2,6.3),E.setMatrixAt(Y,v);E.castShadow=!0,i.add(E);let b=new Nt({color:"#fff",emissive:"#fff3dc",emissiveIntensity:.6});for(let Y of[3.1,6]){let st=new ot(new Re(u-d-2,.04,.16),b);st.position.set(0,x-.02,Y),i.add(st)}let M=u_();i.add(M.skupina);let A=h_(),_=new oe,T=new ot(ie(2.3,.72,.16,.03),new Nt({color:"#202327",roughness:.45,metalness:.4})),I=new Nt({color:"#000",emissive:"#ffffff",emissiveMap:A.tex,emissiveIntensity:1.5,roughness:.25,map:A.tex});for(let Y of[1,-1]){let st=new ot(new Xe(2.14,.6),I);st.position.z=Y*.081,Y<0&&(st.rotation.y=Math.PI),_.add(st)}let L=new ot(new ge(.02,.02,.3,8),p);for(let Y of[-.8,.8]){let st=L.clone();st.position.set(Y,.5,0),_.add(st)}_.add(T),_.rotation.y=-Math.PI/2,_.position.set(Lh.x,Lh.y,Lh.z),i.add(_);let N=ke([[new ge(.05,.07,5.6,10),"#3a3f45",Ht(0,2.8,0)],[ie(.7,.1,.22,.03),"#3a3f45",Ht(-.25,5.62,0)]]),B=new Nt({vertexColors:!0,roughness:.5,metalness:.5}),D=[];for(let Y=-88;Y<=88;Y+=16)Math.abs(Y)>33&&D.push(Y);let O=new Rn(N,B,D.length),$=new Re(.6,.03,.16),J=new Rn($,new Nt({color:"#fff",emissive:"#ffe2b0",emissiveIntensity:.4}),D.length);D.forEach((Y,st)=>{v.makeTranslation(Y,le.y,7),O.setMatrixAt(st,v),v.makeTranslation(Y-.25,le.y+5.56,7),J.setMatrixAt(st,v)}),O.castShadow=!0,i.add(O,J);let W=ke([[ie(1.8,.05,.42,.01),"#8b5a35",Ht(0,.45,0)],[ie(1.8,.4,.05,.01),"#8b5a35",Ht(0,.75,.2,-.12,0,0)],[ie(.06,.45,.4,.01),"#2f3338",Ht(-.75,.22,0)],[ie(.06,.45,.4,.01),"#2f3338",Ht(.75,.22,0)]]),G=new Nt({vertexColors:!0,roughness:.7});for(let Y of[-17.5,10.5,24.5]){let st=new ot(W,G);st.position.set(Y,le.y,6.9),st.castShadow=!0,i.add(st)}let[K,nt]=Be(128,128);nt.fillStyle="#f4f4f0",nt.fillRect(0,0,128,128),nt.strokeStyle="#1b3f8b",nt.lineWidth=8,nt.strokeRect(4,4,120,120),nt.fillStyle="#1b3f8b",nt.font='600 92px "IBM Plex Sans", sans-serif',nt.textAlign="center",nt.textBaseline="middle",nt.fillText("1",64,70);let Et=new Nt({map:Ve(K),roughness:.6});for(let Y of[-36,36]){let st=new oe,vt=new ot(new ge(.04,.04,3.2,8),p);vt.position.y=1.6;let Vt=new ot(new Re(.03,.5,.5),[p,p,p,p,Et,Et]);Vt.position.y=2.9;let St=Vt.clone();St.rotation.y=Math.PI/2,St.position.y=2.9,st.add(vt,St),st.position.set(Y,le.y,2.9),st.traverse(Xt=>{Xt.isMesh&&(Xt.castShadow=!0)}),i.add(st)}let pt={x:0,z:17.5,w:30,d:10,h:8.2},Ft=Kd(pt.w,2,9,{loki:!0,vrata:[4],seme:3}),Dt=Kd(pt.d,2,3,{loki:!0,seme:5}),ft=Y=>new Nt({map:Y.bar,emissiveMap:Y.emis,emissive:"#ffffff",emissiveIntensity:0,roughness:.85}),U=ft(Ft),V=ft(Dt),dt=new ot(new Re(pt.w,pt.h,pt.d),[V,V,c,c,U,U]);dt.position.set(pt.x,le.y+pt.h/2-.3,pt.z),dt.castShadow=!0,dt.receiveShadow=!0,i.add(dt);let Mt=xr();Mt.bar.repeat.set(.5,.5),Mt.nor.repeat.set(.5,.5);let yt=new Nt({map:Mt.bar,normalMap:Mt.nor,roughness:.8}),It=new ot(ws(pt.w,pt.d,3.4,.7),yt);It.position.set(pt.x,le.y+pt.h-.3,pt.z),It.castShadow=!0,It.receiveShadow=!0,i.add(It);for(let Y of[-9,7]){let st=new ot(ie(.6,1.6,.6,.02),new Nt({color:"#b9a98f",roughness:.9}));st.position.set(Y,le.y+pt.h+2.2,pt.z+1.5),st.castShadow=!0,i.add(st)}let Kt=new ot(new Re(9,4.6,8),[V,V,c,c,U,U]);Kt.position.set(pt.x+pt.w/2+4.5,le.y+2,pt.z+.6),Kt.castShadow=!0,Kt.receiveShadow=!0;let it=new ot(ws(9,8,2.2,.5),yt);it.position.set(pt.x+pt.w/2+4.5,le.y+4.3,pt.z+.6),it.castShadow=!0,i.add(Kt,it);let ut=new ot(new Xe(70,6),new Nt({color:"#8a8780",roughness:.95}));return ut.rotation.x=-Math.PI/2,ut.position.set(5,le.y-.01,10.6),ut.receiveShadow=!0,i.add(ut),{skupina:i,ura:M,tabla:A,fasade:[U,V],luci:[b,J.material]}}var ef=Xn(101),Dh=Xn(202),p_=Xn(303),qn={x:-1520,z:-430},_r={x:-3290,z:62};function zi(i,t,e){let n=e.zPriX(Math.max(-3990,Math.min(1390,i))),s=n-t,r=-.85+1.4*wn(ef,i/380,t/380,3),a=be(220,1500,s);r+=a*(110+190*(.5+.5*wn(Dh,i/1100,t/1100,4))),r+=a*40*wn(p_,i/260,t/260,3);let o=be(500,1700,-s);r+=o*(40+80*(.5+.5*wn(Dh,i/900+7,t/900,3)));let c=Math.hypot(i-qn.x,t-qn.z);r+=34*Math.exp(-(c*c)/(300*150));let l=be(16,70,Math.abs(s));r=fe(-.85,r,l);let h=(f,g,x,p)=>{let m=Math.max(Math.abs(i-f)/x,Math.abs(t-g)/p);return 1-be(.75,1,m)},d=h(30,120,190,112),u=h(-3260,150,200,140);return r=fe(r,.25+.6*wn(ef,i/200,t/200,2),Math.max(d,u)*be(9,14,t-n)),i>-48&&i<72&&t-n>6&&t-n<30&&(r=Math.min(r,.4)),r}function nf(i,t,e){let n=wn(Dh,i/520+3.1,t/520-1.7,3);return Fe((n+be(8,60,e)*.55-.08)*3)}var m_=`
varying vec3 vSvet;
float th(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float tn(vec2 p) {
  vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(th(i), th(i + vec2(1, 0)), f.x), mix(th(i + vec2(0, 1)), th(i + vec2(1, 1)), f.x), f.y);
}
float tf(vec2 p) { return 0.5 * tn(p) + 0.25 * tn(p * 2.1 + 3.3) + 0.125 * tn(p * 4.3 + 7.1); }
vec3 teren(vec3 w, float gozd, out float hrap) {
  vec2 p = w.xz;
  // njive: zasukana mre\u017Ea, vsaka parcela svoj posevek
  float kot = 0.35 + 0.5 * tn(p / 900.0);
  mat2 R = mat2(cos(kot), -sin(kot), sin(kot), cos(kot));
  vec2 q = R * p;
  vec2 vel = vec2(96.0, 34.0) * (0.8 + 0.5 * tn(p / 700.0 + 4.0));
  vec2 cel = floor(q / vel);
  float id = th(cel);
  vec2 f = fract(q / vel);
  float meja = min(min(f.x, 1.0 - f.x) * vel.x, min(f.y, 1.0 - f.y) * vel.y);
  vec3 trava = vec3(0.29, 0.37, 0.15), temna = vec3(0.21, 0.27, 0.12);
  vec3 orana = vec3(0.30, 0.23, 0.16), strn = vec3(0.52, 0.45, 0.27), koruza = vec3(0.43, 0.36, 0.21);
  trava = mix(trava, vec3(0.36, 0.38, 0.18), th(cel + 7.0) * 0.6);
  vec3 c = id < 0.35 ? trava : id < 0.5 ? temna : id < 0.68 ? orana : id < 0.84 ? strn : koruza;
  // brazde
  float br = sin(q.y * (id < 0.68 && id > 0.5 ? 9.0 : 3.5)) * 0.5 + 0.5;
  c *= 0.94 + 0.07 * br;
  c *= 0.85 + 0.3 * tf(p / 18.0);
  // \u017Eiva meja med parcelami
  c = mix(vec3(0.17, 0.2, 0.09), c, smoothstep(0.6, 2.5, meja));
  // gozd: jesenske kro\u0161nje, iglavci temni
  float pis = tf(p / 9.0);
  vec3 g = mix(vec3(0.13, 0.19, 0.11), vec3(0.55, 0.32, 0.10), smoothstep(0.35, 0.75, tf(p / 40.0 + 9.0)));
  g = mix(g, vec3(0.62, 0.48, 0.14), smoothstep(0.65, 0.9, pis) * 0.5);
  g *= 0.65 + 0.5 * pis;
  c = mix(c, g, gozd);
  hrap = mix(0.95, 0.9, gozd);
  return c;
}
`;function sf(i){let a=Math.round(320),o=Math.round(5e3/20),c=new Xe(6400,5e3,a,o);c.rotateX(-Math.PI/2),c.translate(-2800/2,0,-1400/2);let l=c.attributes.position,h=new Float32Array(l.count);for(let f=0;f<l.count;f++){let g=l.getX(f),x=l.getZ(f),p=zi(g,x,i);l.setY(f,p),h[f]=nf(g,x,p)*be(28,70,Math.abs(i.zPriX(Math.max(-3990,Math.min(1390,g)))-x))}c.setAttribute("aGozd",new Pe(h,1)),c.computeVertexNormals();let d=new Nt({color:"#ffffff",roughness:.95});d.onBeforeCompile=f=>{f.vertexShader=f.vertexShader.replace("#include <common>",`#include <common>
attribute float aGozd;
varying float vGozd;
varying vec3 vSvet;`).replace("#include <begin_vertex>",`#include <begin_vertex>
vGozd = aGozd;
vSvet = (modelMatrix * vec4(position, 1.0)).xyz;`),f.fragmentShader=f.fragmentShader.replace("#include <common>",`#include <common>
varying float vGozd;
`+m_+`
float _hr;`).replace("#include <color_fragment>",`#include <color_fragment>
diffuseColor.rgb = teren(vSvet, vGozd, _hr);`).replace("#include <roughnessmap_fragment>",`#include <roughnessmap_fragment>
roughnessFactor = _hr;`)},d.customProgramCacheKey=()=>"teren";let u=new ot(c,d);return u.receiveShadow=!0,u}function g_(){let i=[];i.push([new ge(.12,.18,2.2,6),"#4a3626",Ht(0,1.1,0)]);let t=[[1.7,3.6,2.4],[1.35,3.4,4.4],[.95,3.2,6.3],[.55,2.6,8]];for(let[e,n,s]of t)i.push([new Zi(e,n,8),"#ffffff",Ht(0,s,0)]);return ke(i)}function v_(){return ke([[new Zi(1.8,8.6,5),"#ffffff",Ht(0,4.6,0)]])}function x_(){let i=new sr(2.8,0);return i.scale(1,1.2,1),ke([[i,"#ffffff",Ht(0,5.2,0)]])}function __(i){let t=mn(i),e=new sr(2.6,1),n=e.attributes.position,s=Xn(i);for(let a=0;a<n.count;a++){let o=new P().fromBufferAttribute(n,a),c=1+.28*s(o.x*.9+3,o.y*.9+o.z*.7);o.multiplyScalar(c),o.y*=1.15,n.setXYZ(a,o.x,o.y,o.z)}e.computeVertexNormals();let r=[[new ge(.16,.24,3.6,6),"#4d3b2b",Ht(0,1.8,0)],[e,"#ffffff",Ht(0,5+t(),0)]];return ke(r)}var y_=["#a8641f","#c48a2c","#8c4a1c","#b5772a","#6f7a2c","#5d6b28","#d0a23a","#7f3f1a"],M_=["#2d4632","#26402c","#33503a","#2a3f2f"];function rf(i,t=[],e=1){let n=(E,v)=>t.some(([b,M,A])=>(E-b)**2+(v-M)**2<A*A),s=new oe,r=mn(77),a=g_(),o=__(5),c=v_(),l=x_(),h=new Nt({vertexColors:!0,roughness:.92}),d=500,u=new Map,f=(E,v,b,M,A,_=A)=>{let T=`${Math.floor(E/d)},${Math.floor(v/d)},${b?1:0},${A?1:0},${_?1:0}`;u.has(T)||u.set(T,[]),u.get(T).push([E,v,M])};for(let E=0;E<3e4*e;E++){let v=-4400+r()*5900,b=i.zPriX(Math.max(-3990,Math.min(1390,v))),M=(r()<.75?-1:1)*(35+Math.pow(r(),1.6)*1400),A=b+M,_=zi(v,A,i),T=nf(v,A,_);if(r()>T*.9||Math.abs(v-30)<220&&A>b&&A<b+240||Math.abs(v+3260)<230&&A>b&&A<b+300||Math.hypot(v-qn.x,A-qn.z)<70||n(v,A))continue;let I=r()<.38+.3*be(40,200,_);f(v,A,I,.75+r()*.75,Math.abs(M)<150,Math.abs(M)<320||Math.hypot(v-qn.x,A-qn.z)<400)}for(let E=0;E<1600;E++){let v=-4300+r()*5600,b=i.zPriX(Math.max(-3990,Math.min(1390,v))),M=b+(r()<.5?-1:1)*(22+r()*600);Math.abs(v-30)<200&&M>b&&M<b+240||Math.abs(v+3260)<230&&M>b&&M<b+300||n(v,M)||f(v,M,r()<.2,.7+r()*.6,Math.abs(M-b)<160)}let g=new ue,x=new nn,p=new Ot,m=new P(0,1,0),S=0;for(let[E,v]of u){let b=E.split(",")[2]==="1",M=E.split(",")[3]==="1",A=E.split(",")[4]==="1",_=new Rn(A?b?a:o:b?c:l,h,v.length);v.forEach(([T,I,L],N)=>{let B=zi(T,I,i);x.setFromAxisAngle(m,r()*Math.PI*2);let D=L*(.85+r()*.3);g.compose(new P(T,B-.2,I),x,new P(D,L*(b?1.15+r()*.5:.9+r()*.35),D)),_.setMatrixAt(N,g),p.set((b?M_:y_)[Math.floor(r()*(b?4:8))]),p.offsetHSL(0,0,(r()-.5)*.06),_.setColorAt(N,p)}),_.castShadow=M,_.receiveShadow=!1,_.computeBoundingSphere(),s.add(_),S+=v.length}return s.userData.stevilo=S,s}function S_(){let[i,t]=Be(256,256),[e,n]=Be(256,256);t.fillStyle="#ffffff",t.fillRect(0,0,256,256),n.fillStyle="#000",n.fillRect(0,0,256,256);let s=mn(31);for(let r of[40,150])for(let a of[30,110,190])t.fillStyle="#d8d2c6",t.fillRect(a-4,r-4,44,56),t.fillStyle="#2b2a28",t.fillRect(a,r,36,48),t.fillStyle="#6b4a2f",t.fillRect(a-12,r,10,48),t.fillRect(a+38,r,10,48),s()<.45&&(n.fillStyle="#ffcf8a",n.fillRect(a+2,r+2,32,44));return{bar:Ve(i),emis:Ve(e)}}function af(i){let t=new oe,e=mn(55),n=[],s=(E,v,b,M,A=0)=>{for(let _=0,T=0;_<b&&T<b*8;T++){let I=e()*Math.PI*2,L=Math.sqrt(e())*M,N=E+Math.cos(I)*L,B=v+Math.sin(I)*L,D=i.zPriX(Math.max(-3990,Math.min(1390,N)));Math.abs(B-D)<26||n.some(O=>Math.hypot(O.x-N,O.z-B)<17)||(n.push({x:N,z:B,w:8+e()*4,d:9+e()*3,h:5.5+e()*1.8,rot:A+(e()<.5?0:Math.PI/2)+(e()-.5)*.25}),_++)}};s(60,120,46,175),s(-60,-70,16,90),s(-1250,170,24,120),s(qn.x+40,qn.z+120,16,90),s(-3200,170,50,200),s(-2400,-260,12,80),s(-600,260,10,70);let r=new Re(1,1,1);r.translate(0,.5,0);let a=S_(),o=new Nt({map:a.bar,emissiveMap:a.emis,emissive:"#ffffff",emissiveIntensity:0,roughness:.9}),c=new _e;{let M=[[-.56,0,-.56],[.56,0,-.56],[.56,.55,0],[-.56,.55,0],[.56,0,.56],[-.56,0,.56]],A=[[0,3,2],[0,2,1],[4,2,3],[4,3,5],[5,3,0],[1,2,4]],_=[],T=[];for(let I of A)for(let L of I)_.push(...M[L]),T.push(M[L][0]*6,(M[L][1]+Math.abs(M[L][2]))*6);c.setAttribute("position",new Jt(_,3)),c.setAttribute("uv",new Jt(T,2)),c.computeVertexNormals()}let l=xr([160,70,46]),h=new Nt({map:l.bar,normalMap:l.nor,roughness:.82}),d=new Rn(r,o,n.length),u=new Rn(c,h,n.length),f=new ue,g=new nn,x=new Ot,p=new P(0,1,0),m=["#ece6d8","#e9dfc4","#f1ede4","#e2d3b1","#dcd6cb","#efe2c6"],S=["#ffffff","#e8d6cf","#c9b8b0","#f0e4dc"];n.forEach((E,v)=>{let b=zi(E.x,E.z,i)-.3;g.setFromAxisAngle(p,E.rot),f.compose(new P(E.x,b,E.z),g,new P(E.w,E.h,E.d)),d.setMatrixAt(v,f),x.set(m[Math.floor(e()*m.length)]),d.setColorAt(v,x),f.compose(new P(E.x,b+E.h,E.z),g,new P(E.w*1.05,E.w*.95,E.d*1.05)),u.setMatrixAt(v,f),x.set(S[Math.floor(e()*S.length)]),u.setColorAt(v,x)});for(let E of[d,u])E.castShadow=!0,E.receiveShadow=!0,E.computeBoundingSphere(),t.add(E);return t.userData.okna=o,t}function of(i){let t=new oe,e=new Nt({color:"#efebe2",roughness:.85}),n=xr([150,64,42]);n.bar.repeat.set(.4,.4),n.nor.repeat.set(.4,.4);let s=new Nt({map:n.bar,normalMap:n.nor,roughness:.8}),r=new Nt({color:"#3b4146",roughness:.55,metalness:.3}),a=new Nt({color:"#1d1f22",roughness:.8}),o=zi(qn.x,qn.z,i)-.5,c=new ot(new Re(20,8.5,9.5),e);c.position.set(0,4.25,0);let l=new ot(ws(20,9.5,5.2,.6),s);l.position.set(0,8.5,0);let h=new ot(new Re(7,7.2,7.5),e);h.position.set(13,3.6,0);let d=new ot(ws(7,7.5,3.6,.5),s);d.position.set(13,7.2,0);let u=new ot(new Re(5,24,5),e);u.position.set(-12,12,0);let f=new ot(new Zi(3.7,13,8),r);f.rotation.y=Math.PI/8,f.position.set(-12,24+6.5,0);let g=new ot(ke([[ie(.12,1.6,.12,0),"#c9a54a"],[ie(.12,.12,.9,0),"#c9a54a",Ht(0,.35,0)]]),new Nt({vertexColors:!0,metalness:.8,roughness:.3}));g.position.set(-12,37.8,0),t.add(c,l,h,d,u,f,g);for(let[x,p,m]of[[2.52,0,Math.PI/2],[-2.52,0,-Math.PI/2],[0,2.52,0],[0,-2.52,Math.PI]]){let S=new ot(new Xe(1.4,2.6),a);S.position.set(-12+x,20.5,p),S.rotation.y=m,t.add(S)}for(let x=0;x<4;x++)for(let p of[-1,1]){let m=new ot(new Xe(1.3,3.2),a);m.position.set(-6+x*4.2,5,p*4.77),m.rotation.y=p>0?0:Math.PI,t.add(m)}return t.position.set(qn.x,o,qn.z),t.rotation.y=.18,t.traverse(x=>{x.isMesh&&(x.castShadow=!0,x.receiveShadow=!0)}),t}function cf(){let i=[],t="#5d4330",e="#4a3626",n="#b8a050";for(let d=0;d<=3;d++){for(let u of[-1,1])i.push([ie(.32,6.6,.32,.03),t,Ht(-13/2+d*(13/3),6.6/2,u*5.2/2)]);i.push([ie(.22,.25,5.2+.6,.02),e,Ht(-13/2+d*(13/3),6.6-.3,0)]),i.push([ie(.2,.22,5.2,.02),e,Ht(-13/2+d*(13/3),2.3,0)])}for(let d of[-1,1]){for(let u=0;u<10;u++)i.push([ie(13+.4,.07,.08,.01),t,Ht(0,.9+u*.52,d*(5.2/2+.18))]);for(let u=0;u<4;u++)i.push([ie(13*.9,.42,.18,.06),n,Ht(.3,1.2+u*1.05,d*(5.2/2+.3))])}i.push([ie(13+.4,.2,5.2-.4,.02),e,Ht(0,3.4,0)]);let o=new oe,c=new ot(ke(i),new Nt({vertexColors:!0,roughness:.92})),l=xr([118,70,50]);l.bar.repeat.set(.5,.5),l.nor.repeat.set(.5,.5);let h=new ot(ws(13+1.2,5.2+1.6,2.6,.2),new Nt({map:l.bar,normalMap:l.nor,roughness:.85}));return h.position.y=6.6,o.add(c,h),o.traverse(d=>{d.isMesh&&(d.castShadow=!0,d.receiveShadow=!0)}),o}function lf(i){let t=new oe,e=32,n=46,s=12.6,[r,a]=Be(n*e,Math.round(s*e)),[o,c]=Be(n*e,Math.round(s*e));a.fillStyle="#e8c87e",a.fillRect(0,0,r.width,r.height),c.fillStyle="#000",c.fillRect(0,0,r.width,r.height),a.fillStyle="#b39a6c",a.fillRect(0,r.height-.9*e,r.width,.9*e),a.fillStyle="#f5ead3";for(let S of[.25,4.1,8])a.fillRect(0,S*e,r.width,.22*e);let l=mn(8);for(let S=0;S<3;S++)for(let E=0;E<14;E++){let v=(1.6+E*3.08)*e,b=r.height-(1.6+S*3.85+2.2)*e;a.fillStyle="#f5ead3",a.fillRect(v-5,b-5,1.3*e+10,2.2*e+10),a.fillStyle="#2b3036",a.fillRect(v,b,1.3*e,2.2*e),a.fillStyle="#e9e2d0",a.fillRect(v+.63*e,b,3,2.2*e),a.fillRect(v,b+.7*e,1.3*e,3),c.fillStyle=l()<.8?"#ffe9c0":"#000",c.fillRect(v+2,b+2,1.3*e-4,2.2*e-4)}a.fillStyle="#5a3d2b",a.fillRect(r.width/2-1.2*e,r.height-3.6*e,2.4*e,2.7*e),a.fillStyle="#3a2f26",a.font=`600 ${.9*e}px "IBM Plex Sans", sans-serif`,a.textAlign="center",a.fillText("\u0160OLA",r.width/2,r.height-4.2*e);let h=new Nt({map:Ve(r),emissiveMap:Ve(o),emissive:"#ffffff",emissiveIntensity:0,roughness:.85}),d=new Nt({color:"#e5c57b",roughness:.85}),u=new ot(new Re(n,s,15),[d,d,d,d,h,h]);u.position.y=s/2;let f=xr([120,58,40]);f.bar.repeat.set(.5,.5),f.nor.repeat.set(.5,.5);let g=new ot(ws(n,15,5.5,.7),new Nt({map:f.bar,normalMap:f.nor,roughness:.8}));g.position.y=s;let x=new ot(new Re(2.4,3.2,2.4),new Nt({color:"#f5ead3",roughness:.8}));x.position.set(0,s+5.2,0);let p=new ot(new Zi(1.9,2.6,4),new Nt({color:"#3d4448",roughness:.5,metalness:.4}));p.rotation.y=Math.PI/4,p.position.set(0,s+8.1,0),t.add(u,g,x,p);let m=zi(_r.x,_r.z,i)-.2;return t.position.set(_r.x,m,_r.z),t.rotation.y=Math.PI,t.traverse(S=>{S.isMesh&&(S.castShadow=!0,S.receiveShadow=!0)}),t.userData.okna=h,t.userData.zvonec=new P(_r.x,m+s+5.2,_r.z),t}function hf(){let e=[],n=[],s=[],r=Xn(909);for(let l=0;l<=26;l++){let h=5200+Math.pow(l/26,1.3)*32e3;for(let d=0;d<=256;d++){let u=d/256*Math.PI*2,f=Math.cos(u)*h-1400,g=Math.sin(u)*h-600,x=be(-.2,.75,-Math.sin(u)),p=1-Math.abs(wn(r,f/5200,g/5200,5)),m=(180+420*wn(r,f/3e3+9,g/3e3,4))*be(5200,9e3,h);m+=x*Math.pow(p,2.2)*2600*be(9e3,2e4,h),m*=1-be(3e4,37e3,h),e.push(f,m-30,g),s.push(m)}}for(let l=0;l<26;l++)for(let h=0;h<256;h++){let d=l*257+h,u=d+1,f=d+256+1,g=f+1;n.push(d,f,u,u,f,g)}let a=new _e;a.setAttribute("position",new Jt(e,3)),a.setAttribute("aVis",new Jt(s,1)),a.setIndex(n),a.computeVertexNormals();let o=new Nt({color:"#ffffff",roughness:.95});o.onBeforeCompile=l=>{l.vertexShader=l.vertexShader.replace("#include <common>",`#include <common>
attribute float aVis;
varying float vVis;
varying float vNY;`).replace("#include <begin_vertex>",`#include <begin_vertex>
vVis = aVis;
vNY = normal.y;`),l.fragmentShader=l.fragmentShader.replace("#include <common>",`#include <common>
varying float vVis;
varying float vNY;`).replace("#include <color_fragment>",`#include <color_fragment>
        vec3 c = mix(vec3(0.16, 0.2, 0.12), vec3(0.32, 0.3, 0.28), smoothstep(900.0, 1500.0, vVis));
        c = mix(c, vec3(0.92, 0.93, 0.95), smoothstep(1750.0, 2000.0, vVis + 160.0 * vNY));
        diffuseColor.rgb = c;`)},o.customProgramCacheKey=()=>"gore";let c=new ot(a,o);return c.frustumCulled=!1,c}function uf(i,t){let e=new oe,[n,s]=Be(256,256),r=Xn(404),a=s.createImageData(256,256);for(let d=0;d<256;d++)for(let u=0;u<256;u++){let f=wn(r,u/48,d/48,4)*.5+.5,g=(u-128)/128,x=(d-128)/128,p=Fe(1-Math.sqrt(g*g+x*x)),m=Fe((f-.32)*1.8)*Math.pow(p,.6),S=(d*256+u)*4;a.data[S]=a.data[S+1]=a.data[S+2]=255,a.data[S+3]=m*255}s.putImageData(a,0,0);let o=Ve(n,{srgb:!1}),c=new Ue({uniforms:{...i,uTex:{value:o},uMoc:{value:1}},vertexShader:`
      varying vec2 vUv; varying vec3 vW;
      void main() { vUv = uv; vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`,fragmentShader:t+`
      uniform sampler2D uTex; uniform float uMoc;
      varying vec2 vUv; varying vec3 vW;
      void main() {
        float a = texture2D(uTex, vUv + vec2(uCasN * 0.0004, 0.0)).a;
        vec3 d = normalize(vW - cameraPosition);
        float bl = smoothstep(8.0, 60.0, length(vW - cameraPosition));
        vec3 col = neboBarva(normalize(vec3(d.x, 0.04, d.z)), 0.0) * 1.05;
        gl_FragColor = vec4(col, a * 0.55 * bl * uMoc);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,transparent:!0,depthWrite:!1}),l=mn(12),h=[[400,-60],[180,60],[-300,40],[-700,-80],[-1100,60],[-1500,-120],[-1900,40],[-2300,-60],[-2700,30],[800,20],[-200,-260],[-1e3,-340]];for(let[d,u]of h){let f=700+l()*600,g=new ot(new Xe(f,f*.7),c);g.rotation.x=-Math.PI/2,g.rotation.z=l()*Math.PI,g.position.set(d,2+l()*7,u),g.renderOrder=5,e.add(g)}return e.userData.mat=c,e}var df=new Sn,Xc=new P,oi=class extends da{constructor(){super(),this.isLineSegmentsGeometry=!0,this.type="LineSegmentsGeometry";let t=[-1,2,0,1,2,0,-1,1,0,1,1,0,-1,0,0,1,0,0,-1,-1,0,1,-1,0],e=[-1,2,1,2,-1,1,1,1,-1,-1,1,-1,-1,-2,1,-2],n=[0,2,1,2,3,1,2,4,3,4,5,3,4,6,5,6,7,5];this.setIndex(n),this.setAttribute("position",new Jt(t,3)),this.setAttribute("uv",new Jt(e,2))}applyMatrix4(t){let e=this.attributes.instanceStart,n=this.attributes.instanceEnd;return e!==void 0&&(e.applyMatrix4(t),n.applyMatrix4(t),e.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}setPositions(t){let e;t instanceof Float32Array?e=t:Array.isArray(t)&&(e=new Float32Array(t));let n=new es(e,6,1);return this.setAttribute("instanceStart",new ii(n,3,0)),this.setAttribute("instanceEnd",new ii(n,3,3)),this.instanceCount=this.attributes.instanceStart.count,this.computeBoundingBox(),this.computeBoundingSphere(),this}setColors(t){let e;t instanceof Float32Array?e=t:Array.isArray(t)&&(e=new Float32Array(t));let n=new es(e,6,1);return this.setAttribute("instanceColorStart",new ii(n,3,0)),this.setAttribute("instanceColorEnd",new ii(n,3,3)),this}fromWireframeGeometry(t){return this.setPositions(t.attributes.position.array),this}fromEdgesGeometry(t){return this.setPositions(t.attributes.position.array),this}fromMesh(t){return this.fromWireframeGeometry(new ra(t.geometry)),this}fromLineSegments(t){let e=t.geometry;return this.setPositions(e.attributes.position.array),this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new Sn);let t=this.attributes.instanceStart,e=this.attributes.instanceEnd;t!==void 0&&e!==void 0&&(this.boundingBox.setFromBufferAttribute(t),df.setFromBufferAttribute(e),this.boundingBox.union(df))}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Un),this.boundingBox===null&&this.computeBoundingBox();let t=this.attributes.instanceStart,e=this.attributes.instanceEnd;if(t!==void 0&&e!==void 0){let n=this.boundingSphere.center;this.boundingBox.getCenter(n);let s=0;for(let r=0,a=t.count;r<a;r++)Xc.fromBufferAttribute(t,r),s=Math.max(s,n.distanceToSquared(Xc)),Xc.fromBufferAttribute(e,r),s=Math.max(s,n.distanceToSquared(Xc));this.boundingSphere.radius=Math.sqrt(s),isNaN(this.boundingSphere.radius)&&console.error("THREE.LineSegmentsGeometry.computeBoundingSphere(): Computed radius is NaN. The instanced position data is likely to have NaN values.",this)}}toJSON(){}};Ct.line={worldUnits:{value:1},linewidth:{value:1},resolution:{value:new mt},dashOffset:{value:0},dashScale:{value:1},dashSize:{value:1},gapSize:{value:1}};bn.line={uniforms:ba.merge([Ct.common,Ct.fog,Ct.line]),vertexShader:`
		#include <common>
		#include <color_pars_vertex>
		#include <fog_pars_vertex>
		#include <logdepthbuf_pars_vertex>
		#include <clipping_planes_pars_vertex>

		uniform float linewidth;
		uniform vec2 resolution;

		attribute vec3 instanceStart;
		attribute vec3 instanceEnd;

		attribute vec3 instanceColorStart;
		attribute vec3 instanceColorEnd;

		#ifdef WORLD_UNITS

			varying vec4 worldPos;
			varying vec3 worldStart;
			varying vec3 worldEnd;

			#ifdef USE_DASH

				varying vec2 vUv;

			#endif

		#else

			varying vec2 vUv;

		#endif

		#ifdef USE_DASH

			uniform float dashScale;
			attribute float instanceDistanceStart;
			attribute float instanceDistanceEnd;
			varying float vLineDistance;

		#endif

		float trimSegmentAlpha( const in vec4 start, const in vec4 end ) {

			// compute the interpolation factor needed to trim the segment so it terminates
			// between the camera plane and the near plane

			// conservative estimate of the near plane
			float a = projectionMatrix[ 2 ][ 2 ]; // 3nd entry in 3th column
			float b = projectionMatrix[ 3 ][ 2 ]; // 3nd entry in 4th column

			// we need different nearEstimate formula for reversed and default depth buffer
			// a is positive with a reversed depth buffer so it can be used for controlling the code flow
			float nearEstimate = ( a > 0.0 ) ? ( - b / ( a + 1.0 ) ) : ( - 0.5 * b / a );

			return ( nearEstimate - start.z ) / ( end.z - start.z );

		}

		void main() {

			#ifdef USE_COLOR

				vColor.xyz = ( position.y < 0.5 ) ? instanceColorStart : instanceColorEnd;

			#endif

			float aspect = resolution.x / resolution.y;

			// camera space
			vec4 start = modelViewMatrix * vec4( instanceStart, 1.0 );
			vec4 end = modelViewMatrix * vec4( instanceEnd, 1.0 );

			#ifdef USE_DASH

				float lineDistanceStart = dashScale * instanceDistanceStart;
				float lineDistanceEnd = dashScale * instanceDistanceEnd;

			#endif

			#ifdef WORLD_UNITS

				worldStart = start.xyz;
				worldEnd = end.xyz;

			#else

				vUv = uv;

			#endif

			// special case for perspective projection, and segments that terminate either in, or behind, the camera plane
			// clearly the gpu firmware has a way of addressing this issue when projecting into ndc space
			// but we need to perform ndc-space calculations in the shader, so we must address this issue directly
			// perhaps there is a more elegant solution -- WestLangley

			bool perspective = ( projectionMatrix[ 2 ][ 3 ] == - 1.0 ); // 4th entry in the 3rd column

			if ( perspective ) {

				if ( start.z < 0.0 && end.z >= 0.0 ) {

					float alpha = trimSegmentAlpha( start, end );
					end.xyz = mix( start.xyz, end.xyz, alpha );

					#ifdef USE_DASH

						lineDistanceEnd = mix( lineDistanceStart, lineDistanceEnd, alpha );

					#endif

				} else if ( end.z < 0.0 && start.z >= 0.0 ) {

					float alpha = trimSegmentAlpha( end, start );
					start.xyz = mix( end.xyz, start.xyz, alpha );

					#ifdef USE_DASH

						lineDistanceStart = mix( lineDistanceEnd, lineDistanceStart, alpha );

					#endif

				}

			}

			#ifdef USE_DASH

				vLineDistance = ( position.y < 0.5 ) ? lineDistanceStart : lineDistanceEnd;
				vUv = uv;

			#endif

			// clip space
			vec4 clipStart = projectionMatrix * start;
			vec4 clipEnd = projectionMatrix * end;

			// ndc space
			vec3 ndcStart = clipStart.xyz / clipStart.w;
			vec3 ndcEnd = clipEnd.xyz / clipEnd.w;

			// direction
			vec2 dir = ndcEnd.xy - ndcStart.xy;

			// account for clip-space aspect ratio
			dir.x *= aspect;
			dir = normalize( dir );

			#ifdef WORLD_UNITS

				vec3 worldDir = normalize( end.xyz - start.xyz );
				vec3 tmpFwd = normalize( mix( start.xyz, end.xyz, 0.5 ) );
				vec3 worldUp = normalize( cross( worldDir, tmpFwd ) );
				vec3 worldFwd = cross( worldDir, worldUp );
				worldPos = position.y < 0.5 ? start: end;

				// height offset
				float hw = linewidth * 0.5;
				worldPos.xyz += position.x < 0.0 ? hw * worldUp : - hw * worldUp;

				// don't extend the line if we're rendering dashes because we
				// won't be rendering the endcaps
				#ifndef USE_DASH

					// cap extension
					worldPos.xyz += position.y < 0.5 ? - hw * worldDir : hw * worldDir;

					// add width to the box
					worldPos.xyz += worldFwd * hw;

					// endcaps
					if ( position.y > 1.0 || position.y < 0.0 ) {

						worldPos.xyz -= worldFwd * 2.0 * hw;

					}

				#endif

				// project the worldpos
				vec4 clip = projectionMatrix * worldPos;

				// shift the depth of the projected points so the line
				// segments overlap neatly
				vec3 clipPose = ( position.y < 0.5 ) ? ndcStart : ndcEnd;
				clip.z = clipPose.z * clip.w;

			#else

				vec2 offset = vec2( dir.y, - dir.x );
				// undo aspect ratio adjustment
				dir.x /= aspect;
				offset.x /= aspect;

				// sign flip
				if ( position.x < 0.0 ) offset *= - 1.0;

				// endcaps
				if ( position.y < 0.0 ) {

					offset += - dir;

				} else if ( position.y > 1.0 ) {

					offset += dir;

				}

				// adjust for linewidth
				offset *= linewidth;

				// adjust for clip-space to screen-space conversion // maybe resolution should be based on viewport ...
				offset /= resolution.y;

				// select end
				vec4 clip = ( position.y < 0.5 ) ? clipStart : clipEnd;

				// back to clip space
				offset *= clip.w;

				clip.xy += offset;

			#endif

			gl_Position = clip;

			vec4 mvPosition = ( position.y < 0.5 ) ? start : end; // this is an approximation

			#include <logdepthbuf_vertex>
			#include <clipping_planes_vertex>
			#include <fog_vertex>

		}
		`,fragmentShader:`
		uniform vec3 diffuse;
		uniform float opacity;
		uniform float linewidth;

		#ifdef USE_DASH

			uniform float dashOffset;
			uniform float dashSize;
			uniform float gapSize;

		#endif

		varying float vLineDistance;

		#ifdef WORLD_UNITS

			varying vec4 worldPos;
			varying vec3 worldStart;
			varying vec3 worldEnd;

			#ifdef USE_DASH

				varying vec2 vUv;

			#endif

		#else

			varying vec2 vUv;

		#endif

		#include <common>
		#include <color_pars_fragment>
		#include <fog_pars_fragment>
		#include <logdepthbuf_pars_fragment>
		#include <clipping_planes_pars_fragment>

		vec2 closestLineToLine(vec3 p1, vec3 p2, vec3 p3, vec3 p4) {

			float mua;
			float mub;

			vec3 p13 = p1 - p3;
			vec3 p43 = p4 - p3;

			vec3 p21 = p2 - p1;

			float d1343 = dot( p13, p43 );
			float d4321 = dot( p43, p21 );
			float d1321 = dot( p13, p21 );
			float d4343 = dot( p43, p43 );
			float d2121 = dot( p21, p21 );

			float denom = d2121 * d4343 - d4321 * d4321;

			float numer = d1343 * d4321 - d1321 * d4343;

			mua = numer / denom;
			mua = clamp( mua, 0.0, 1.0 );
			mub = ( d1343 + d4321 * ( mua ) ) / d4343;
			mub = clamp( mub, 0.0, 1.0 );

			return vec2( mua, mub );

		}

		void main() {

			float alpha = opacity;
			vec4 diffuseColor = vec4( diffuse, alpha );

			#include <clipping_planes_fragment>

			#ifdef USE_DASH

				if ( vUv.y < - 1.0 || vUv.y > 1.0 ) discard; // discard endcaps

				if ( mod( vLineDistance + dashOffset, dashSize + gapSize ) > dashSize ) discard; // todo - FIX

			#endif

			#ifdef WORLD_UNITS

				// Find the closest points on the view ray and the line segment
				vec3 rayEnd = normalize( worldPos.xyz ) * 1e5;
				vec3 lineDir = worldEnd - worldStart;
				vec2 params = closestLineToLine( worldStart, worldEnd, vec3( 0.0, 0.0, 0.0 ), rayEnd );

				vec3 p1 = worldStart + lineDir * params.x;
				vec3 p2 = rayEnd * params.y;
				vec3 delta = p1 - p2;
				float len = length( delta );
				float norm = len / linewidth;

				#ifndef USE_DASH

					#ifdef USE_ALPHA_TO_COVERAGE

						float dnorm = fwidth( norm );
						alpha = 1.0 - smoothstep( 0.5 - dnorm, 0.5 + dnorm, norm );

					#else

						if ( norm > 0.5 ) {

							discard;

						}

					#endif

				#endif

			#else

				#ifdef USE_ALPHA_TO_COVERAGE

					// artifacts appear on some hardware if a derivative is taken within a conditional
					float a = vUv.x;
					float b = ( vUv.y > 0.0 ) ? vUv.y - 1.0 : vUv.y + 1.0;
					float len2 = a * a + b * b;
					float dlen = fwidth( len2 );

					if ( abs( vUv.y ) > 1.0 ) {

						alpha = 1.0 - smoothstep( 1.0 - dlen, 1.0 + dlen, len2 );

					}

				#else

					if ( abs( vUv.y ) > 1.0 ) {

						float a = vUv.x;
						float b = ( vUv.y > 0.0 ) ? vUv.y - 1.0 : vUv.y + 1.0;
						float len2 = a * a + b * b;

						if ( len2 > 1.0 ) discard;

					}

				#endif

			#endif

			#include <logdepthbuf_fragment>
			#include <color_fragment>

			gl_FragColor = vec4( diffuseColor.rgb, alpha );

			#include <tonemapping_fragment>
			#include <colorspace_fragment>
			#include <fog_fragment>
			#include <premultiplied_alpha_fragment>

		}
		`};var Yn=class extends Ue{constructor(t){super({type:"LineMaterial",uniforms:ba.clone(bn.line.uniforms),vertexShader:bn.line.vertexShader,fragmentShader:bn.line.fragmentShader,clipping:!0}),this.isLineMaterial=!0,this.setValues(t)}get color(){return this.uniforms.diffuse.value}set color(t){this.uniforms.diffuse.value=t}get worldUnits(){return"WORLD_UNITS"in this.defines}set worldUnits(t){t===!0!==this.worldUnits&&(this.needsUpdate=!0),t===!0?this.defines.WORLD_UNITS="":delete this.defines.WORLD_UNITS}get linewidth(){return this.uniforms.linewidth.value}set linewidth(t){this.uniforms.linewidth&&(this.uniforms.linewidth.value=t)}get dashed(){return"USE_DASH"in this.defines}set dashed(t){t===!0!==this.dashed&&(this.needsUpdate=!0),t===!0?this.defines.USE_DASH="":delete this.defines.USE_DASH}get dashScale(){return this.uniforms.dashScale.value}set dashScale(t){this.uniforms.dashScale.value=t}get dashSize(){return this.uniforms.dashSize.value}set dashSize(t){this.uniforms.dashSize.value=t}get dashOffset(){return this.uniforms.dashOffset.value}set dashOffset(t){this.uniforms.dashOffset.value=t}get gapSize(){return this.uniforms.gapSize.value}set gapSize(t){this.uniforms.gapSize.value=t}get opacity(){return this.uniforms.opacity.value}set opacity(t){this.uniforms&&(this.uniforms.opacity.value=t)}get resolution(){return this.uniforms.resolution.value}set resolution(t){this.uniforms.resolution.value.copy(t)}get alphaToCoverage(){return"USE_ALPHA_TO_COVERAGE"in this.defines}set alphaToCoverage(t){this.defines&&(t===!0!==this.alphaToCoverage&&(this.needsUpdate=!0),t===!0?this.defines.USE_ALPHA_TO_COVERAGE="":delete this.defines.USE_ALPHA_TO_COVERAGE)}};var Uh=new xe,ff=new P,pf=new P,an=new xe,on=new xe,Mi=new xe,Nh=new P,Fh=new ue,cn=new fa,mf=new P,qc=new Sn,Yc=new Un,Si=new xe,bi,Ts;function gf(i,t,e){return Si.set(0,0,-t,1).applyMatrix4(i.projectionMatrix),Si.multiplyScalar(1/Si.w),Si.x=Ts/e.width,Si.y=Ts/e.height,Si.applyMatrix4(i.projectionMatrixInverse),Si.multiplyScalar(1/Si.w),Math.abs(Math.max(Si.x,Si.y))}function b_(i,t){let e=i.matrixWorld,n=i.geometry,s=n.attributes.instanceStart,r=n.attributes.instanceEnd,a=Math.min(n.instanceCount,s.count);for(let o=0,c=a;o<c;o++){cn.start.fromBufferAttribute(s,o),cn.end.fromBufferAttribute(r,o),cn.applyMatrix4(e);let l=new P,h=new P;bi.distanceSqToSegment(cn.start,cn.end,h,l),h.distanceTo(l)<Ts*.5&&t.push({point:h,pointOnLine:l,distance:bi.origin.distanceTo(h),object:i,face:null,faceIndex:o,uv:null,uv1:null})}}function E_(i,t,e){let n=t.projectionMatrix,r=i.material.resolution,a=i.matrixWorld,o=i.geometry,c=o.attributes.instanceStart,l=o.attributes.instanceEnd,h=Math.min(o.instanceCount,c.count),d=-t.near;bi.at(1,Mi),Mi.w=1,Mi.applyMatrix4(t.matrixWorldInverse),Mi.applyMatrix4(n),Mi.multiplyScalar(1/Mi.w),Mi.x*=r.x/2,Mi.y*=r.y/2,Mi.z=0,Nh.copy(Mi),Fh.multiplyMatrices(t.matrixWorldInverse,a);for(let u=0,f=h;u<f;u++){if(an.fromBufferAttribute(c,u),on.fromBufferAttribute(l,u),an.w=1,on.w=1,an.applyMatrix4(Fh),on.applyMatrix4(Fh),an.z>d&&on.z>d)continue;if(an.z>d){let E=an.z-on.z,v=(an.z-d)/E;an.lerp(on,v)}else if(on.z>d){let E=on.z-an.z,v=(on.z-d)/E;on.lerp(an,v)}an.applyMatrix4(n),on.applyMatrix4(n),an.multiplyScalar(1/an.w),on.multiplyScalar(1/on.w),an.x*=r.x/2,an.y*=r.y/2,on.x*=r.x/2,on.y*=r.y/2,cn.start.copy(an),cn.start.z=0,cn.end.copy(on),cn.end.z=0;let x=cn.closestPointToPointParameter(Nh,!0);cn.at(x,mf);let p=_i.lerp(an.z,on.z,x),m=p>=-1&&p<=1,S=Nh.distanceTo(mf)<Ts*.5;if(m&&S){cn.start.fromBufferAttribute(c,u),cn.end.fromBufferAttribute(l,u),cn.start.applyMatrix4(a),cn.end.applyMatrix4(a);let E=new P,v=new P;bi.distanceSqToSegment(cn.start,cn.end,v,E),e.push({point:v,pointOnLine:E,distance:bi.origin.distanceTo(v),object:i,face:null,faceIndex:u,uv:null,uv1:null})}}}var Ei=class extends ot{constructor(t=new oi,e=new Yn({color:Math.random()*16777215})){super(t,e),this.isLineSegments2=!0,this.type="LineSegments2"}computeLineDistances(){let t=this.geometry,e=t.attributes.instanceStart,n=t.attributes.instanceEnd,s=new Float32Array(2*e.count);for(let a=0,o=0,c=e.count;a<c;a++,o+=2)ff.fromBufferAttribute(e,a),pf.fromBufferAttribute(n,a),s[o]=o===0?0:s[o-1],s[o+1]=s[o]+ff.distanceTo(pf);let r=new es(s,2,1);return t.setAttribute("instanceDistanceStart",new ii(r,1,0)),t.setAttribute("instanceDistanceEnd",new ii(r,1,1)),this}raycast(t,e){let n=this.material.worldUnits,s=t.camera;if(s===null&&!n&&console.error('LineSegments2: "Raycaster.camera" needs to be set in order to raycast against LineSegments2 while worldUnits is set to false.'),n===!1&&(this.material.resolution.x===0||this.material.resolution.y===0))return;let r=t.params.Line2!==void 0&&t.params.Line2.threshold||0;bi=t.ray;let a=this.matrixWorld,o=this.geometry,c=this.material;Ts=c.linewidth+r,o.boundingSphere===null&&o.computeBoundingSphere(),Yc.copy(o.boundingSphere).applyMatrix4(a);let l;if(n)l=Ts*.5;else{let d=Math.max(s.near,Yc.distanceToPoint(bi.origin));l=gf(s,d,c.resolution)}if(Yc.radius+=l,bi.intersectsSphere(Yc)===!1)return;o.boundingBox===null&&o.computeBoundingBox(),qc.copy(o.boundingBox).applyMatrix4(a);let h;if(n)h=Ts*.5;else{let d=Math.max(s.near,qc.distanceToPoint(bi.origin));h=gf(s,d,c.resolution)}qc.expandByScalar(h),bi.intersectsBox(qc)!==!1&&(n?b_(this,e):E_(this,s,e))}onBeforeRender(t){let e=this.material.uniforms;e&&e.resolution&&(t.getViewport(Uh),this.material.uniforms.resolution.value.set(Uh.z,Uh.w))}};var vf=3,w_=(()=>{let i=getComputedStyle(document.documentElement);return[["--d-ontime","#7c8698"],["--d-small","#f2a87e"],["--d-mid","#e07b45"],["--d-big","#b85417"]].map(([t,e])=>i.getPropertyValue(t).trim()||e)})();async function xf(i){let t=await(await fetch(i)).blob(),e=await createImageBitmap(t,{colorSpaceConversion:"none",premultiplyAlpha:"none"}),n=document.createElement("canvas");n.width=e.width,n.height=e.height;let s=n.getContext("2d",{willReadFrequently:!0});return s.drawImage(e,0,0),{w:e.width,h:e.height,px:s.getImageData(0,0,e.width,e.height).data}}function _f(i){let t=Math.floor(i/60+.5);return t<=0?0:t<=5?1:t<=15?2:3}async function yf(i){let[t,e,n]=await Promise.all([fetch(i.karta).then(lt=>lt.json()),xf(i.podatki),xf(i.relief)]),s=new Int16Array(t.n_int16);for(let lt=0;lt<t.n_int16;lt++)s[lt]=e.px[lt*4]*256+e.px[lt*4+1]-32768;let r=t.enota/1e3,a=t.relief,o=n.px,c=new Float32Array(a.nx*a.nz),l=new Float32Array(a.nx*a.nz);for(let lt=0;lt<a.nx*a.nz;lt++)c[lt]=(o[lt*4]*256+o[lt*4+1])*a.skala,l[lt]=o[lt*4+2]/255;let h=a.x0/1e3,d=a.x1/1e3,u=a.z0/1e3,f=a.z1/1e3;function g(lt,Rt){let gt=Fe((lt-h)/(d-h)*a.nx-.5,0,a.nx-1.001),Zt=Fe((Rt-u)/(f-u)*a.nz-.5,0,a.nz-1.001),Gt=Math.floor(gt),te=Math.floor(Zt),ve=gt-Gt,Qe=Zt-te,wi=c[te*a.nx+Gt],In=c[te*a.nx+Gt+1],Zn=c[(te+1)*a.nx+Gt],ci=c[(te+1)*a.nx+Gt+1];return((wi*(1-ve)+In*ve)*(1-Qe)+(Zn*(1-ve)+ci*ve)*Qe)/1e3*vf}let x=new Uint16Array(a.nx*a.nz*2);for(let lt=0;lt<a.nx*a.nz;lt++)x[lt*2]=tr.toHalfFloat(c[lt]),x[lt*2+1]=tr.toHalfFloat(l[lt]);let p=new vs(x,a.nx,a.nz,xi,On);p.magFilter=p.minFilter=$e,p.flipY=!1,p.needsUpdate=!0;let m=new Di,S=new Ot("#05080d");m.background=S;let E=new Ze(42,1,.05,3e3),v=d-h,b=f-u,M=new Xe(v,b,Math.round(a.nx/2),Math.round(a.nz/2));M.rotateX(-Math.PI/2),M.translate((h+d)/2,0,(u+f)/2);let A={uVis:{value:p},uE:{value:vf},uTexel:{value:new mt(1/a.nx,1/a.nz)},uKm:{value:new mt(v/a.nx,b/a.nz)},uOzadje:{value:S},uSvetlost:{value:1},uX0:{value:new xe(h,u,v,b)}},_=new ot(M,new Ue({uniforms:A,vertexShader:`
      uniform sampler2D uVis; uniform float uE; uniform vec4 uX0;
      varying vec2 vUv; varying vec3 vW;
      void main() {
        vec3 p = position;
        vUv = vec2((p.x - uX0.x) / uX0.z, (p.z - uX0.y) / uX0.w);
        p.y = texture2D(uVis, vUv).r / 1000.0 * uE;
        vW = p;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
      }`,fragmentShader:`
      uniform sampler2D uVis; uniform float uE; uniform vec2 uTexel; uniform vec2 uKm; uniform vec3 uOzadje; uniform float uSvetlost;
      varying vec2 vUv; varying vec3 vW;
      void main() {
        vec2 s = texture2D(uVis, vUv).rg;
        float h = s.r, maska = smoothstep(0.15, 0.85, s.g);
        float hl = texture2D(uVis, vUv - vec2(uTexel.x, 0.0)).r, hr = texture2D(uVis, vUv + vec2(uTexel.x, 0.0)).r;
        float hd = texture2D(uVis, vUv - vec2(0.0, uTexel.y)).r, hu = texture2D(uVis, vUv + vec2(0.0, uTexel.y)).r;
        vec3 n = normalize(vec3((hl - hr) / 1000.0 * uE / (2.0 * uKm.x), 1.0, (hd - hu) / 1000.0 * uE / (2.0 * uKm.y)));
        float sv = max(dot(n, normalize(vec3(-0.55, 0.72, -0.42))), 0.0);
        float sv2 = max(dot(n, normalize(vec3(0.5, 0.6, 0.6))), 0.0);
        vec3 nizko = vec3(0.034, 0.046, 0.066), visoko = vec3(0.15, 0.17, 0.205);
        vec3 c = mix(nizko, visoko, smoothstep(150.0, 2400.0, h));
        c *= 0.38 + 0.95 * sv + 0.14 * sv2;
        // plastnice vsakih 100 m, krepkej\u0161e vsakih 500 m
        float k = h / 100.0, w = fwidth(k);
        float pl = 1.0 - smoothstep(0.0, w * 1.3, abs(fract(k - 0.5) - 0.5));
        float k5 = h / 500.0, w5 = fwidth(k5);
        float pl5 = 1.0 - smoothstep(0.0, w5 * 1.6, abs(fract(k5 - 0.5) - 0.5));
        c += vec3(0.30, 0.40, 0.55) * (pl * 0.045 + pl5 * 0.09) * maska * step(60.0, h);
        // zunaj dr\u017Eave skoraj ozadje: Slovenija lebdi
        c = mix(uOzadje * 1.15 + c * 0.16, c, maska);
        // robovi domene v ozadje
        float rob = smoothstep(0.0, 0.1, vUv.x) * smoothstep(1.0, 0.9, vUv.x) * smoothstep(0.0, 0.12, vUv.y) * smoothstep(1.0, 0.88, vUv.y);
        c = mix(uOzadje, c, rob) * uSvetlost;
        gl_FragColor = vec4(c, 1.0);
        #include <colorspace_fragment>
      }`}));m.add(_);let T=t.mesta.find(lt=>lt[0]==="Ljubljana"),I=new mt(T[1]/1e3,T[2]/1e3),L=(lt,Rt)=>{lt.onBeforeCompile=gt=>{gt.uniforms.uRaz=Rt,gt.uniforms.uSr={value:I},gt.vertexShader=gt.vertexShader.replace("#include <common>",`#include <common>
uniform vec2 uSr; varying float vRaz;`).replace("vec4 start = modelViewMatrix * vec4( instanceStart, 1.0 );",`vRaz = mix(distance(instanceStart.xz, uSr), distance(instanceEnd.xz, uSr), position.y < 0.5 ? 0.0 : 1.0);
vec4 start = modelViewMatrix * vec4( instanceStart, 1.0 );`),gt.fragmentShader=gt.fragmentShader.replace("#include <common>",`#include <common>
uniform float uRaz; varying float vRaz;`).replace("vec4 diffuseColor = vec4( diffuse, alpha );",`if (vRaz > uRaz) discard;
vec4 diffuseColor = vec4( diffuse * (1.0 + 2.5 * smoothstep(uRaz - 9.0, uRaz, vRaz)), alpha );`)}},N={value:0},B={value:0},D=[],O=0,$=s.subarray(0,t.dolzina_prog);for(;O<$.length;){let lt=$[O++],Rt=null;for(let gt=0;gt<lt;gt++){let Zt=$[O++]*r,Gt=$[O++]*r,te=g(Zt,Gt)+.06;Rt&&D.push(...Rt,Zt,te,Gt),Rt=[Zt,te,Gt]}}let J=new oi().setPositions(D),W=new Yn({color:"#ffd6ae",linewidth:1.9,transparent:!0,opacity:.95,depthWrite:!1}),G=new Yn({color:"#f0934f",linewidth:7,transparent:!0,opacity:.16,depthWrite:!1,blending:is});L(W,N),L(G,N);let K=new Ei(J,W),nt=new Ei(J,G);K.renderOrder=3,nt.renderOrder=2,m.add(nt,K);let Et=[],pt=s.subarray(t.dolzina_prog,t.dolzina_prog+t.n_bus*4),Ft=.24;for(let lt=0;lt<pt.length;lt+=4){let Rt=pt[lt]*Ft,gt=pt[lt+1]*Ft,Zt=pt[lt+2]*Ft,Gt=pt[lt+3]*Ft;Et.push(Rt,g(Rt,gt)+.04,gt,Zt,g(Zt,Gt)+.04,Gt)}let Dt=new oi().setPositions(Et),ft=new Yn({color:"#6f8fb3",linewidth:.9,transparent:!0,opacity:.32,depthWrite:!1});L(ft,B);let U=new Ei(Dt,ft);U.renderOrder=1,m.add(U);let V=t.obris,dt=[];for(let lt=0;lt<V.length;lt+=2){let Rt=lt,gt=(lt+2)%V.length,Zt=V[Rt]/1e3,Gt=V[Rt+1]/1e3,te=V[gt]/1e3,ve=V[gt+1]/1e3;dt.push(Zt,g(Zt,Gt)+.1,Gt,te,g(te,ve)+.1,ve)}let Mt=new Yn({color:"#c8d3e4",linewidth:1.2,transparent:!0,opacity:.45,depthWrite:!1,dashed:!0,dashSize:1.2,gapSize:.8}),yt=new oi().setPositions(dt),It=new Ei(yt,Mt);It.computeLineDistances(),m.add(It);let Kt=[W,G,ft,Mt],it=s.subarray(t.dolzina_prog+t.n_bus*4,t.dolzina_prog+t.n_bus*4+t.dolzina_vozenj),ut=[];for(O=0;O<it.length;){let lt=it[O++],Rt=it[O++],gt=new Float32Array(Rt),Zt=new Float32Array(Rt),Gt=new Float32Array(Rt),te=new Float32Array(Rt);for(let ve=0;ve<Rt;ve++)gt[ve]=it[O++],Zt[ve]=it[O++]*r,Gt[ve]=it[O++]*r,te[ve]=it[O++]*10;ut.push({vrsta:lt,t:gt,x:Zt,z:Gt,d:te})}let Y=ut.length,st=new Float32Array(Y*3),vt=new Float32Array(Y*3),Vt=new Float32Array(Y),St=new _e;St.setAttribute("position",new Pe(st,3)),St.setAttribute("color",new Pe(vt,3)),St.setAttribute("aVel",new Pe(Vt,1));let Xt={uDpr:{value:1},uVid:{value:0}},Qt=new qr(St,new Ue({uniforms:Xt,vertexShader:`
      attribute float aVel; uniform float uDpr; varying vec3 vC; varying float vV;
      void main() {
        vC = color; vV = aVel;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = aVel * uDpr * clamp(230.0 / -mv.z, 0.9, 2.6);
        gl_Position = projectionMatrix * mv;
      }`,fragmentShader:`
      uniform float uVid; varying vec3 vC; varying float vV;
      void main() {
        if (vV <= 0.0) discard;
        float d = length(gl_PointCoord - 0.5) * 2.0;
        float jedro = 1.0 - smoothstep(0.28, 0.4, d);
        float sij = exp(-d * d * 4.0) * 0.7;
        float a = max(jedro, sij) * uVid;
        if (a < 0.01) discard;
        gl_FragColor = vec4(mix(vC, vec3(1.0), jedro * 0.25), a);
        #include <colorspace_fragment>
      }`,vertexColors:!0,transparent:!0,depthWrite:!1}));Qt.frustumCulled=!1,Qt.renderOrder=5,m.add(Qt);let F=w_.map(lt=>new Ot(lt));function ye(lt){for(let Rt=0;Rt<Y;Rt++){let gt=ut[Rt],Zt=gt.t.length;if(lt<gt.t[0]||lt>gt.t[Zt-1]){Vt[Rt]=0;continue}let Gt=0,te=Zt-1;for(;te-Gt>1;){let ci=Gt+te>>1;gt.t[ci]<=lt?Gt=ci:te=ci}let ve=gt.t[te]>gt.t[Gt]?(lt-gt.t[Gt])/(gt.t[te]-gt.t[Gt]):0,Qe=gt.x[Gt]+(gt.x[te]-gt.x[Gt])*ve,wi=gt.z[Gt]+(gt.z[te]-gt.z[Gt])*ve,In=gt.d[Gt]+(gt.d[te]-gt.d[Gt])*ve;st[Rt*3]=Qe,st[Rt*3+1]=g(Qe,wi)+.18,st[Rt*3+2]=wi;let Zn=F[gt.vrsta===0,_f(In)];vt[Rt*3]=Zn.r,vt[Rt*3+1]=Zn.g,vt[Rt*3+2]=Zn.b,Vt[Rt]=gt.vrsta===0?12:gt.vrsta===2?4.2:5.2}St.attributes.position.needsUpdate=!0,St.attributes.color.needsUpdate=!0,St.attributes.aVel.needsUpdate=!0}let ne=t.vrsta,C=[];for(let lt=0;lt<ne.pot.length;lt+=2)C.push([ne.pot[lt]/1e3,ne.pot[lt+1]/1e3]);let y=[0];for(let lt=1;lt<C.length;lt++)y.push(y[lt-1]+Math.hypot(C[lt][0]-C[lt-1][0],C[lt][1]-C[lt-1][1]));let H=ne.postaje.map(([,lt,Rt])=>{let gt=0,Zt=1e9;return C.forEach(([Gt,te],ve)=>{let Qe=Math.hypot(Gt-lt/1e3,te-Rt/1e3);Qe<Zt&&(Zt=Qe,gt=ve)}),y[gt]}),X=.55,tt=(lt,Rt)=>{let gt=null,Zt=null;for(let te=0;te<H.length;te++)lt[te]!=null&&(H[te]<=Rt&&(gt=te),H[te]>=Rt&&Zt===null&&(Zt=te));if(gt===null&&Zt===null)return null;if(gt===null)return lt[Zt];if(Zt===null||H[Zt]===H[gt])return lt[gt];let Gt=(Rt-H[gt])/(H[Zt]-H[gt]);return lt[gt]+(lt[Zt]-lt[gt])*Gt},ct=new oe,_t=C.map(([lt,Rt])=>g(lt,Rt)+.12),rt=[];for(let[,lt]of ne.dnevi){let Rt=[];for(let gt=0;gt<C.length-1;gt++){let Zt=tt(lt,y[gt]),Gt=tt(lt,y[gt+1]);Zt==null||Gt==null||Rt.push(C[gt][0],_t[gt]+Zt/60*X,C[gt][1],C[gt+1][0],_t[gt+1]+Gt/60*X,C[gt+1][1])}rt.push(...Rt)}let ht=new oi().setPositions(rt),bt=new Yn({color:"#f2a87e",linewidth:1.1,transparent:!0,opacity:.22,depthWrite:!1});ct.add(new Ei(ht,bt));let Wt=C.map((lt,Rt)=>{let gt=ne.dnevi.map(([,Zt])=>tt(Zt,y[Rt])).filter(Zt=>Zt!=null).sort((Zt,Gt)=>Zt-Gt);return gt.length?gt[Math.floor(gt.length/2)]:0}),At=[];for(let lt=0;lt<C.length-1;lt++)At.push(C[lt][0],_t[lt]+Wt[lt]/60*X,C[lt][1],C[lt+1][0],_t[lt+1]+Wt[lt+1]/60*X,C[lt+1][1]);let Tt=new Yn({color:"#f0934f",linewidth:3.2,transparent:!0,depthWrite:!1});ct.add(new Ei(new oi().setPositions(At),Tt));{let lt=[],Rt=[],gt=[];C.forEach(([te,ve],Qe)=>{lt.push(te,_t[Qe],ve,te,_t[Qe]+Wt[Qe]/60*X,ve),gt.push(0,1)});for(let te=0;te<C.length-1;te++){let ve=te*2;Rt.push(ve,ve+2,ve+1,ve+1,ve+2,ve+3)}let Zt=new _e;Zt.setAttribute("position",new Jt(lt,3)),Zt.setAttribute("aA",new Jt(gt,1)),Zt.setIndex(Rt);let Gt=new Ue({uniforms:{uVid:{value:1}},vertexShader:"attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",fragmentShader:"uniform float uVid; varying float vA; void main(){ gl_FragColor = vec4(vec3(0.94,0.58,0.31), (0.05 + 0.32 * vA) * uVid); }",transparent:!0,depthWrite:!1,side:fn,blending:is});ct.add(new ot(Zt,Gt)),ct.userData.zm=Gt}let Bt=[];H.forEach((lt,Rt)=>{let gt=0;y.forEach((Zt,Gt)=>{Math.abs(Zt-lt)<Math.abs(y[gt]-lt)&&(gt=Gt)}),Bt.push(C[gt][0],_t[gt],C[gt][1],C[gt][0],_t[gt]+7.5,C[gt][1])});let jt=new Yn({color:"#c8d3e4",linewidth:.8,transparent:!0,opacity:.35,depthWrite:!1,dashed:!0,dashSize:.3,gapSize:.3}),re=new Ei(new oi().setPositions(Bt),jt);re.computeLineDistances(),ct.add(re),ct.visible=!1,m.add(ct);let R=[bt,Tt,jt],j=new oe,k=T[1]/1e3,at=T[2]/1e3,xt=g(k,at)+.2,et=[];for(let lt=0;lt<3;lt++){let Rt=new ot(new sa(.92,1,64),new si({color:"#f0934f",transparent:!0,depthWrite:!1,side:fn}));Rt.rotation.x=-Math.PI/2,Rt.position.set(k,xt,at),j.add(Rt),et.push(Rt)}m.add(j);let wt=document.createElement("div");wt.className="karta-oznake",document.body.appendChild(wt);let Pt=t.mesta.map(([lt,Rt,gt])=>{let Zt=document.createElement("div");Zt.className="mesto",Zt.textContent=lt,wt.appendChild(Zt);let Gt=Rt/1e3,te=gt/1e3;return{el:Zt,p:new P(Gt,g(Gt,te)+.3,te),ime:lt}}),he=[],de=(lt,Rt,gt,Zt,Gt)=>{let te=document.createElement("div");te.className="oznaka3d "+(Gt||""),te.innerHTML=`<span>${lt}</span>`,wt.appendChild(te);let ve={el:te,p:new P(Rt,g(Rt,gt)+Zt,gt)};return he.push(ve),ve},Ge=ne.stat,ln=ne.postaje[ne.postaje.length-1],Oi=de(`<em>${ne.ime}</em><b>Ljubljana \u2192 Maribor \xB7 ${Ge.dni} dni</b>`,ln[1]/1e3,ln[2]/1e3,8.5,""),yr=de("<em>budilka</em><b>7.15 \u2192 7.22</b>",k,at,2.2,"oranzna"),qe=Oc([{t:128,p:[4,430,270],c:[8,0,-4],f:40},{t:137,p:[-4,215,205],c:[6,0,0],f:40},{t:146,p:[-30,150,175],c:[6,0,2],f:40},{t:157,p:[40,150,175],c:[6,0,2],f:40},{t:168,p:[95,95,95],c:[14,0,-8],f:40},{t:177,p:[62,48,62],c:[22,3,-22],f:40,mir:!0},{t:186,p:[4,26,40],c:[-20,0,4],f:40},{t:193,p:[-14,11,20],c:[-23.5,0,6],f:40},{t:200,p:[-19.5,7,15.5],c:[-23.6,.2,6.6],f:40},{t:206,p:[-23.3,2.4,9.2],c:[-23.7,.2,6.8],f:40}].map(lt=>({t:lt.t,v:[...lt.p,...lt.c,lt.f],mir:lt.mir}))),Tn=new xe,hs=0;function As(lt,Rt,gt,Zt){let Gt=qe(Rt);E.position.set(Gt[0],Gt[1],Gt[2]),E.lookAt(Gt[3],Gt[4],Gt[5]),E.fov=Gt[6],E.near=Math.max(.02,Gt[1]*.02),Zt(E),E.updateProjectionMatrix();let te=innerWidth,ve=innerHeight;for(let z of[...Kt,...R])z.resolution.set(te,ve);let Qe=lt.getPixelRatio();Qe!==hs&&(Xt.uDpr.value=Qe,hs=Qe),N.value=fe(0,260,be(129,141,Rt)),B.value=fe(0,260,be(134,146,Rt));let wi=Rt<146?fe(-300,0,be(138,146,Rt)):Rt<168?fe(0,3600,(Rt-146)/22):3600+(Rt-168)*18;ye(wi),Xt.uVid.value=be(139,145,Rt)*(1-.55*En(Rt,169,173,182,186));let In=En(Rt,168,173,184,188);ct.visible=In>.001,ct.scale.y=1;for(let z of R)z.opacity=z===Tt?In:z===jt?In*.35:In*.22;ct.userData.zm.uniforms.uVid.value=In;let Zn=En(Rt,195,197.5,204,206);j.visible=Zn>.001,et.forEach((z,Q)=>{let q=(gt*.6+Q/3)%1;z.scale.setScalar(.3+q*3.2),z.material.opacity=(1-q)*.8*Zn}),wt.style.opacity=1;let ci=be(140,146,Rt)*(1-be(203,205.5,Rt));for(let z of Pt)jn(z,ci*(z.ime==="Ljubljana"||Rt<184?1:.4));jn(Oi,In),jn(yr,Zn),lt.render(m,E);let w=En(Rt,144,147,168,171);return w>0?{vid:w,oznaka:"\u010Detrtek, 1. 10. 2026",cas:7*3600+Fe(wi,0,3600)}:null}function jn(lt,Rt){if(Rt<=.001){lt.el.style.opacity=0;return}Tn.set(lt.p.x,lt.p.y,lt.p.z,1).applyMatrix4(E.matrixWorldInverse).applyMatrix4(E.projectionMatrix);let gt=(Tn.x/Tn.w*.5+.5)*innerWidth,Zt=(-Tn.y/Tn.w*.5+.5)*innerHeight;lt.el.style.opacity=Tn.w>0?Rt.toFixed(3):0,lt.el.style.transform=`translate3d(${gt.toFixed(1)}px, ${Zt.toFixed(1)}px, 0)`}function Sr(){wt.style.opacity=0}return{risi:As,skrij:Sr,meta:t}}var T_=()=>new Promise(i=>requestAnimationFrame(()=>i())),Ia=matchMedia("(pointer: coarse)").matches||innerWidth<700,jc=matchMedia("(prefers-reduced-motion: reduce)").matches,vn=(i,t,e=0)=>i*3600+t*60+e,A_=[[0,vn(7,41,24)],[10,vn(7,41,59.2)],[11,vn(7,42,0)],[14,vn(7,42,5)],[26,vn(7,50,0)],[43,vn(7,55,0)],[54,vn(7,55,30)],[68,vn(7,56,30)],[103,vn(8,0,0)],[118,vn(8,13,0)],[128,vn(8,14,0)],[206,vn(22,41,0)],[240,vn(22,43,0)]];function Mf(i){let t=A_;if(i<=t[0][0])return t[0][1];for(let e=0;e<t.length-1;e++)if(i<=t[e+1][0]){let n=(i-t[e][0])/(t[e+1][0]-t[e][0]);return t[e+1][1]<t[e][1]?t[e+1][1]:fe(t[e][1],t[e+1][1],n)}return t[t.length-1][1]}var R_=i=>{let t=Math.floor(i/3600)%24,e=Math.floor(i/60)%60;return`${String(t).padStart(2,"0")}.${String(e).padStart(2,"0")}`};async function C_(){let i=document.getElementById("oder"),t;try{t=new Nc({canvas:i,antialias:!0,powerPreference:"high-performance"})}catch{document.documentElement.classList.add("brez-3d");return}let e=+new URLSearchParams(location.search).get("dpr")||0,n=e||Math.min(devicePixelRatio||1,Ia?1.6:2),s=e||Math.min(n,Ia?1.3:2);t.setPixelRatio(s),t.setSize(innerWidth,innerHeight,!1),t.toneMapping=pa,t.toneMappingExposure=1,t.shadowMap.enabled=!0,t.shadowMap.type=_s;let r=document.querySelector(".nalaganje i"),a=null;yf(i.dataset).then(R=>{a=R}).catch(R=>console.warn("kajros: karta se ni nalo\u017Eila",R));let o=async R=>{r&&(r.style.width=`${R*100}%`),await T_()};await Promise.all([document.fonts.load('600 92px "IBM Plex Sans"'),document.fonts.load('600 80px "IBM Plex Mono"')]).catch(()=>{});let c=new Di,l=new kc;l.nastavi("zora"),c.add(l.kupola,l.sonce,l.sonce.target,l.nebesna),c.fog=new Hr("#fff",1,2),l.sonce.shadow.mapSize.set(Ia?1024:2048,Ia?1024:2048),await o(.1);let h=Vd(),d=Gd(h,{atmU:l.U,NEBO:Ah});c.add(d.skupina),await o(.2);let u=Jd();c.add(u.skupina),await o(.3);let f=tf();c.add(f.skupina);let g=Qd();c.add(g.skupina),await o(.4),c.add(sf(h)),await o(.55);let x=[[-2140,-78,.15],[-880,-66,-.1],[-2260,66,.05]],p=rf(h,[...x.map(([R,j])=>[R,j,28]),[-1380,240,50],[-1425,-60,45],[-2105,-45,32],[-2860,175,40],[-2990,160,40],[-3140,105,40],[-3060,330,30]],Ia?.7:1);c.add(p),await o(.7);let m=af(h);c.add(m,of(h));for(let[R,j,k]of x){let at=cf();at.position.set(R,zi(R,j,h)-.2,j),at.rotation.y=k,c.add(at)}let S=lf(h);c.add(S,hf());let E=uf(l.U,Ah);c.add(E);{let R=new ot(new Re(130,1.4,5),new Nt({color:"#9a968e",roughness:.9}));R.position.set(-3265,le.y-.7,1.68+2.5),R.receiveShadow=!0,c.add(R)}await o(.82);let v=new Ue({uniforms:{uMoc:{value:1}},vertexShader:"varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",fragmentShader:"uniform float uMoc; varying vec2 vUv; void main(){ float d = length(vUv - 0.5) * 2.0; float a = exp(-d * d * 5.0) * 0.9 + exp(-d * 18.0) * 0.6; gl_FragColor = vec4(vec3(1.0, 0.95, 0.85) * a * uMoc, 1.0); }",transparent:!0,blending:is,depthWrite:!1}),b=[];for(let R of[-1,1]){let j=new ot(new Xe(3.2,3.2),v);j.renderOrder=10,c.add(j),b.push({m:j,z:R})}let M=[];for(let[R,j,k,at,xt]of[[0,4,4.6,"#ffd7a0",26],[-14,4,4.8,"#ffd7a0",22],[14,4,4.8,"#ffd7a0",22],[-40,5.6,7,"#ffe2b8",14],[-17.25,1.3,6.55,"#a9c4ff",1.6],[-18.9,2.5,8.9,"#ffd9b0",2.4]]){let et=new ha(at,0,26,1.6);et.position.set(R,j,k),c.add(et),M.push([et,xt])}c.traverse(R=>{if(R.material)for(let j of[].concat(R.material))l.popravi(j)}),await o(.88);let A={};l.nastavi("zora"),A.zora=l.okolje(t),l.nastavi("noc"),A.noc=l.okolje(t),l.nastavi("zora"),c.environment=A.zora;let _=new Ze(40,innerWidth/innerHeight,.05,6e4),T=h.sPriX(-40),I=h.sPriX(-3268);function L(R){if(R<206){if(R<28)return T-740-(28-R)*98;if(R<43){let j=(R-28)/15;return T-740*(1-j)*(1-j)}return R<68?T:R<118?T+(I-T)*Fd(0,1,(R-68)/50):I}return T}let N=new P,B=new P,D=new P,O=new P(0,1,0),$=(R,j,k)=>{if(!R.v)return k.set(R[0],R[1],R[2]);let at=L(j);return h.tocka(at,N),h.smer(at,B),D.crossVectors(B,O).normalize(),k.copy(N).addScaledVector(B,R.v[0]).addScaledVector(O,R.v[1]).addScaledVector(D,R.v[2])},J=[{t:0,p:[-2.75,3.12,2.18],c:[0,3.3,3.05],f:34},{t:5,p:[-3.3,3,1.95],c:[0,3.26,3.1],f:35},{t:13,p:[-7.2,2.35,1.3],c:[2,3.25,3.7],f:40},{t:20,p:[-30,2.3,5.4],c:[10,2.9,2.8],f:40},{t:26,p:[-52,2.25,6.2],c:[20,2.6,1],f:38},{t:37,p:[-52,2.2,6.4],c:[-6,2.4,.6],f:38},{t:44,p:[-51.5,2,6.8],c:[-39,2.15,.2],f:40,mir:!0},{t:49,p:[-15,3.3,5.6],c:[1,3.1,3.5],f:42},{t:54,p:[-12,3.25,5.4],c:[2,3.1,3.6],f:42,mir:!0},{t:58,p:[-12.4,1.95,8.3],c:[-6.6,1.5,1.4],f:38},{t:64,p:[-11.8,1.9,8],c:[-6.4,1.55,1.2],f:38},{t:69,p:[-22,2.8,10],c:[-42,2.2,0],f:42},{t:75,p:{v:[-30,5,15]},c:{v:[-4,2,0]},f:42},{t:82,p:{v:[24,3.2,10]},c:{v:[-14,2,0]},f:42},{t:88,p:{v:[60,22,46]},c:{v:[-30,2,-20]},f:44},{t:89.4,p:{v:[86,40,76]},c:{v:[-20,2,-30]},f:44},{t:89.5,p:[-1415,26,-40],c:[-1500,4,-330],f:40,rez:!0},{t:94,p:[-1440,25,-48],c:[-1600,4,-320],f:40},{t:94,p:[-2105,3.2,-45],c:[-2170,4.5,-125],f:42,rez:!0},{t:100,p:[-2110,3.4,-48],c:[-2265,4.5,-110],f:42},{t:100,p:[-2860,48,175],c:[-3260,10,40],f:42,rez:!0},{t:110,p:[-2990,46,160],c:[-3270,8,40],f:42},{t:116,p:[-3140,46,105],c:[-3250,3,4],f:44},{t:122,p:[-3060,120,330],c:[-2600,0,-60],f:46},{t:128,p:[-2700,900,900],c:[-1800,0,-100],f:50},{t:206,p:[-30,34,48],c:[-6,2,2],f:44,rez:!0},{t:213.5,p:[-27.5,6.5,16],c:[-17,1.6,6.2],f:42},{t:222,p:[-20.1,2.05,8.3],c:[-17.3,1.4,6.55],f:40,mir:!0},{t:240,p:[-19.8,1.98,8.05],c:[-17.35,1.38,6.55],f:37}],W=new P,G=[];for(let R of J)(R.rez||!G.length)&&G.push([]),G[G.length-1].push(R);function K(R){let j=G[0];for(let at of G)at[0].t<=R&&(j=at);let k=j.map(at=>({t:at.t,v:$(at.p,R,W).toArray().concat($(at.c,R,W).toArray(),[at.f]),mir:at.mir}));return k.length===1?k[0].v:Oc(k)(R)}let nt=[...document.querySelectorAll(".takt")],Et=[];function pt(){let R=scrollY;Et=nt.map(j=>{let k=j.getBoundingClientRect();return{el:j,top:k.top+R,h:k.height,t0:+j.dataset.t0,t1:+j.dataset.t1,kart:j.querySelector(".kartica")}})}function Ft(R){let j=R+innerHeight*.5;if(!Et.length)return 0;if(j<=Et[0].top)return Et[0].t0;for(let k of Et)if(j<=k.top+k.h)return fe(k.t0,k.t1,Fe((j-k.top)/k.h));return Et[Et.length-1].t1}function Dt(){let R=scrollY+innerHeight*.5;for(let j of Et){if(!j.kart)continue;let k=(R-j.top)/j.h,at=jc?k>-.1&&k<1.1?1:0:En(k,-.02,.14,.84,1);j.kart.style.opacity=at.toFixed(3),j.kart.style.transform=`translate3d(0, ${((1-be(-.02,.14,k))*18).toFixed(1)}px, 0)`}}pt(),addEventListener("resize",()=>{t.setSize(innerWidth,innerHeight,!1),pt()}),new ResizeObserver(pt).observe(document.body);let ft=[...document.querySelectorAll(".oznaka3d[data-p]")].map(R=>({el:R,p:new P(...R.dataset.p.split(",").map(Number)),t0:+R.dataset.t0,t1:+R.dataset.t1})),U=[...document.querySelectorAll(".poglavja a")].map(R=>({a:R,od:+R.dataset.od})),V=-1;function dt(R){let j=0;U.forEach((k,at)=>{R>=k.od-.01&&(j=at)}),j!==V&&(V=j,U.forEach((k,at)=>k.a.setAttribute("aria-current",at===j?"true":"false")))}let Mt=document.querySelector(".hud-ura"),yt=Mt?.querySelector("b"),It=Mt?.querySelector("span"),Kt=document.querySelector(".prehod"),it=document.querySelector(".dodatek"),ut=document.querySelector(".vrh"),Y=new xe,st=new P,vt=new P,Vt=new P,St=null,Xt=0,Qt=!1;function F(R,j){let k=Xt?Fe(j-Xt,0,.25):0;if(Xt=j,St===null||Math.abs(R-St)>1800||jc)return St=R,Qt=!1,St;let at=Math.floor(R/60)*60+60,xt=1-Math.exp(-k*7);return St>=at&&(Qt=!0),Qt&&St>R+.3?St=Math.max(R,St-Math.max(k*2,(St-R)*xt)):St<R-.3?(Qt=!1,St=Math.min(R,St+Math.max(k,(R-St)*xt))):(Qt=!1,St=Math.min(St+k,at-.001)),St}let ye=null;function ne(){if(ye)return ye;let R=u.zadnjiS();u.postavi(h,T);let{xa:j,xb:k}=u.VRATA,at=(j+k)/2,xt=j-.9,et=u.vrataLok(at,0,-2.25),wt=[new P(-8.1,le.y,4.3),new P(fe(-8.1,et.x,.55),le.y,3.1),new P(et.x,le.y,et.z),u.vrataLok(at,.58,-1.3),u.vrataLok(at-.2,.58,-.45),u.vrataLok(xt+.45,.58,-.08),u.vrataLok(xt-.25,.58+.25/.27*.245,0),u.vrataLok(xt-1.5,.58+1.5/.27*.245,0)],Pt=new $i(wt,!1,"centripetal",.5);return ye={krivulja:Pt,dolzina:Pt.getLength()},R!==null&&u.postavi(h,R),ye}let C=-1,y="zora";function H(R,j){let k=R>=206;k?l.nastavi("noc"):l.nastavi("zora","jutro",be(60,118,R));let at=k?"noc":"zora";at!==y&&(c.environment=A[at],y=at),c.environmentIntensity=l.stanje.okolje,l.U.uCasN.value=j,t.toneMappingExposure=l.stanje.izp;let xt=L(R);u.postavi(h,xt),u.nastaviLuci(!0,k?1:be(0,1,0)*.2),h.tocka(xt,N),h.smer(xt,B),D.crossVectors(B,O).normalize();let et=k?0:En(R,24,30,42,48)*.6;v.uniforms.uMoc.value=et;for(let qe of b)qe.m.visible=et>.01,qe.m.position.copy(N).addScaledVector(B,.25).addScaledVector(D,qe.z).setY(1.56),qe.m.lookAt(_.position);let wt=Mf(R);f.ura.nastavi(F(wt,j)),f.ura.obraz.emissiveIntensity=k?1:.38;let Pt=k||wt<vn(7,42,30)?0:wt<vn(7,46)?5:wt<vn(7,49)?10:13;if(Pt!==C&&(f.tabla.narisi(Pt),C=Pt),k)g.skupina.visible=!0,g.skupina.position.set(-17.6,le.y,6.98),g.skupina.rotation.y=Math.PI/2,g.poza(0,Math.sin(j*.4)*.08,0,1);else{let qe=ne(),Tn=be(57.8,63.3,R)*.55+Fe((R-57.8)/5.5)*.45,hs=Tn*qe.dolzina;qe.krivulja.getPointAt(Math.min(Tn,1),W),qe.krivulja.getTangentAt(Math.min(Tn,.999),st),g.skupina.visible=R<63.4,g.skupina.position.copy(W);let As=Math.atan2(-st.z,st.x);g.skupina.rotation.y=fe(.35,As,be(57.2,58.3,R)),g.poza(R>57.8?hs:0,fe(-.3,.5,En(R,3,6,40,46))*(1-be(57,58,R)),1-be(56.8,57.9,R),0)}u.odpriVrata(k?0:be(56.2,57.6,R)*(1-be(63.6,65,R)));for(let qe of f.luci)qe.emissiveIntensity=k?2.6:.5;for(let qe of f.fasade)qe.emissiveIntensity=k?1.1:0;m.userData.okna.emissiveIntensity=k?.9:0,S.userData.okna.emissiveIntensity=k?0:En(R,98,104,120,128)*.25;for(let[qe,Tn]of M)qe.intensity=k?Tn:0;E.userData.mat.uniforms.uMoc.value=k?.25:1-be(70,120,R)*.6;let he=l.U.uSonce.value,de=R>84&&R<128?220:80,Ge=l.sonce.shadow.camera;Ge.left=-de,Ge.right=de,Ge.top=de,Ge.bottom=-de,Ge.near=1,Ge.far=1200,Ge.updateProjectionMatrix();let ln=R>84&&R<128?N:_.position,Oi=2*de/l.sonce.shadow.mapSize.x;vt.crossVectors(O,he).normalize(),Vt.crossVectors(he,vt),W.set(ln.x,0,ln.z);let yr=Math.round(W.dot(vt)/Oi)*Oi,Mr=Math.round(W.dot(Vt)/Oi)*Oi;l.sonce.target.position.set(0,0,0).addScaledVector(vt,yr).addScaledVector(Vt,Mr).addScaledVector(he,W.dot(he)),l.sonce.position.copy(l.sonce.target.position).addScaledVector(he,500),u.kamera(_)}function X(R=_){let j=innerWidth,k=innerHeight;R.aspect=j/k;let at=j/k<.85,xt=be(3,12,ct),et=at?.5:fe(.67,.6,xt),wt=at?fe(.33,.4,xt):.5,Pt=j*2*Math.max(et,1-et),he=k*2*Math.max(wt,1-wt);R.setViewOffset(Pt,he,Pt/2-et*j,he/2-wt*k,j,k)}let tt=0,ct=0,_t=performance.now(),rt=0,ht=null,bt=16,Wt=0,At=!1,Tt=[],Bt=null;function jt(R){let j=Bt?[...Bt.p,...Bt.c,Bt.f]:K(ct),k=ct>=128&&ct<206,at=null;if(k)a?at=a.risi(t,ct,R,X):(t.setClearColor("#0a0d12",1),t.clear());else{a?.skrij();let et=ct>=206?le.y+1.1:ct>70?zi(j[0],j[2],h)+2.2:-1e9;_.position.set(j[0],Math.max(j[1],et),j[2]);let wt=jc?0:1-be(0,3,ct);wt>0&&_.position.add(W.set(Math.sin(R*.33)*.03,Math.sin(R*.27)*.02,Math.cos(R*.21)*.02).multiplyScalar(wt)),_.lookAt(j[3],j[4],j[5]);let Pt=innerWidth/innerHeight,he=_i.degToRad(j[6]),de=2*Math.atan(Math.tan(Math.atan(Math.tan(he/2)*1.6)*.78)/Pt);_.fov=_i.radToDeg(Math.min(Math.max(he,de),_i.degToRad(78))),X(),_.near=Fe(Math.hypot(j[3]-j[0],j[4]-j[1],j[5]-j[2])*.02,.15,.6),_.updateProjectionMatrix(),H(ct,R),d.zice.material.uniforms.uLoc.value.set(i.width,i.height),t.render(c,_)}for(let et of ft){let wt=En(ct,et.t0,et.t0+1.5,et.t1-1.5,et.t1);if(wt<=.001||k){et.el.style.opacity=0;continue}Y.set(et.p.x,et.p.y,et.p.z,1).applyMatrix4(_.matrixWorldInverse).applyMatrix4(_.projectionMatrix);let Pt=(Y.x/Y.w*.5+.5)*innerWidth,he=(-Y.y/Y.w*.5+.5)*innerHeight;et.el.style.opacity=Y.w>0?wt.toFixed(3):0,et.el.style.transform=`translate3d(${Pt.toFixed(1)}px, ${he.toFixed(1)}px, 0)`}let xt=it?it.getBoundingClientRect().top:1/0;if(ut?.classList.toggle("nad-dodatkom",xt<64),Mt){let et=(at?at.vid:En(ct,64,70,124,128)+En(ct,206,212,260,270))*(1-be(innerHeight*.9,innerHeight*.55,xt));Mt.style.opacity=et.toFixed(3),et>0&&(It.textContent=at?at.oznaka:"ura v zgodbi",yt.textContent=R_(at?at.cas:St??Mf(ct)))}if(Kt){let et=En(ct,123,128,128,131.5),wt=En(ct,202,206,206,209);Kt.style.opacity=Math.max(et,wt).toFixed(3),Kt.style.background=et>wt?"#e9e4dc":"#05070b"}}function re(){let R=performance.now(),j=Math.min(.1,(R-_t)/1e3);_t=R,tt=ht??Ft(scrollY);let k=ct;ct=jc?tt:ct+(tt-ct)*(1-Math.exp(-j*6.5)),Math.abs(tt-ct)<.002&&(ct=tt),Dt(),dt(tt);let at=Math.abs(ct-k)>1e-4;if(at&&(rt=R),at||R-rt<400||Wt++%2===0){e||(bt>22&&s>.75?(s=Math.max(.75,s-.15),t.setPixelRatio(s),t.setSize(innerWidth,innerHeight,!1),bt=16):bt<9&&s<n&&(s=Math.min(n,s+.1),t.setPixelRatio(s),t.setSize(innerWidth,innerHeight,!1),bt=14));let xt=performance.now();jt(R/1e3);let et=performance.now()-xt;bt=bt*.95+et*.05}At||(At=!0,document.documentElement.classList.add("pripravljeno"),window.__pripravljen=!0),requestAnimationFrame(re)}try{_.position.set(-1.5,3.2,2.6),_.lookAt(0,3.3,3.05),await t.compileAsync(c,_)}catch{}await o(1),pt(),ct=tt=Ft(scrollY),jt(performance.now()/1e3),requestAnimationFrame(re),window.__film={pojdi(R){ht=R,ct=tt=R,jt(performance.now()/1e3)},pogled(R,j,k=40){Bt=R?{p:R,c:j,f:k}:null,jt(performance.now()/1e3)},skoci(){ht=null,ct=tt=Ft(scrollY),Dt(),jt(performance.now()/1e3)},T:()=>ct,kam:R=>K(R),ura:()=>St,vlakS:R=>L(R),vlakXZ:R=>{let j=h.tocka(L(R),new P);return[Math.round(j.x),Math.round(j.z)]},info:()=>({drevesa:p.userData.stevilo,dpr:s,klici:t.info.render.calls,tri:t.info.render.triangles})}}C_().catch(i=>{console.error(i),document.documentElement.classList.add("brez-3d"),window.__pripravljen=!0});})();
/*! Bundled license information:

three/build/three.core.js:
three/build/three.module.js:
  (**
   * @license
   * Copyright 2010-2026 Three.js Authors
   * SPDX-License-Identifier: MIT
   *)
*/
