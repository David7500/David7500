(()=>{var yu=0,Ul=1,Mu=2;var Ss=1,Su=2,hr=3,rs=0,on=1,vn=2,_i=0,ur=1,as=2,Nl=3,Fl=4,bu=5;var bs=100,Eu=101,wu=102,Tu=103,Au=104,Ru=200,Cu=201,Pu=202,Iu=203,zl=204,Ol=205,Lu=206,Du=207,Uu=208,Nu=209,Fu=210,zu=211,Ou=212,Bu=213,ku=214,ro=0,ao=1,oo=2,$s=3,co=4,lo=5,ho=6,uo=7,Bl=0,Hu=1,Vu=2,On=0,kl=1,Hl=2,Vl=3,Gl=4,Wl=5,Xl=6,pa=7;var ql=300,os=301,Es=302,Go=303,Wo=304,ma=306,Js=1e3,Wn=1001,fo=1002,nn=1003,Gu=1004;var ga=1005;var Ke=1006,Xo=1007;var cs=1008;var Ln=1009,Yl=1010,jl=1011,dr=1012,qo=1013,li=1014,qn=1015,Bn=1016,Yo=1017,jo=1018,fr=1020,Zl=35902,$l=35899,Jl=1021,Kl=1022,Yn=1023,pi=1026,ls=1027,Zo=1028,$o=1029,yi=1030,Jo=1031;var Ko=1033,va=33776,xa=33777,_a=33778,ya=33779,Qo=35840,tc=35841,ec=35842,nc=35843,ic=36196,sc=37492,rc=37496,ac=37488,oc=37489,Ma=37490,cc=37491,lc=37808,hc=37809,uc=37810,dc=37811,fc=37812,pc=37813,mc=37814,gc=37815,vc=37816,xc=37817,_c=37818,yc=37819,Mc=37820,Sc=37821,bc=36492,Ec=36494,wc=36495,Tc=36283,Ac=36284,Sa=36285,Rc=36286;var Ur=2300,po=2301,io=2302,Ml=2303,Sl=2400,bl=2401,El=2402;var Wu=3200;var Cc=0,Xu=1,ki="",bn="srgb",Nr="srgb-linear",Fr="linear",Ie="srgb";var so=7680;var qu=519,Yu=512,ju=513,Zu=514,Pc=515,$u=516,Ju=517,Ic=518,Ku=519,Ql=35044;var th="300 es",si=2e3,Ks=2001;function Ef(i){for(let t=i.length-1;t>=0;--t)if(i[t]>=65535)return!0;return!1}function wf(i){return ArrayBuffer.isView(i)&&!(i instanceof DataView)}function zr(i){return document.createElementNS("http://www.w3.org/1999/xhtml",i)}function Qu(){let i=zr("canvas");return i.style.display="block",i}var kh={},Qs=null;function Or(...i){let t="THREE."+i.shift();Qs?Qs("log",t,...i):console.log(t,...i)}function td(i){let t=i[0];if(typeof t=="string"&&t.startsWith("TSL:")){let e=i[1];e&&e.isStackTrace?i[0]+=" "+e.getLocation():i[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return i}function ie(...i){i=td(i);let t="THREE."+i.shift();if(Qs)Qs("warn",t,...i);else{let e=i[0];e&&e.isStackTrace?console.warn(e.getError(t)):console.warn(t,...i)}}function ae(...i){i=td(i);let t="THREE."+i.shift();if(Qs)Qs("error",t,...i);else{let e=i[0];e&&e.isStackTrace?console.error(e.getError(t)):console.error(t,...i)}}function _s(...i){let t=i.join(" ");t in kh||(kh[t]=!0,ie(...i))}function ed(i,t,e){return new Promise(function(n,s){function r(){switch(i.clientWaitSync(t,i.SYNC_FLUSH_COMMANDS_BIT,0)){case i.WAIT_FAILED:s();break;case i.TIMEOUT_EXPIRED:setTimeout(r,e);break;default:n()}}setTimeout(r,e)})}var nd={[ro]:ao,[oo]:ho,[co]:uo,[$s]:lo,[ao]:ro,[ho]:oo,[uo]:co,[lo]:$s},mi=class{addEventListener(t,e){this._listeners===void 0&&(this._listeners={});let n=this._listeners;n[t]===void 0&&(n[t]=[]),n[t].indexOf(e)===-1&&n[t].push(e)}hasEventListener(t,e){let n=this._listeners;return n===void 0?!1:n[t]!==void 0&&n[t].indexOf(e)!==-1}removeEventListener(t,e){let n=this._listeners;if(n===void 0)return;let s=n[t];if(s!==void 0){let r=s.indexOf(e);r!==-1&&s.splice(r,1)}}dispatchEvent(t){let e=this._listeners;if(e===void 0)return;let n=e[t.type];if(n!==void 0){t.target=this;let s=n.slice(0);for(let r=0,a=s.length;r<a;r++)s[r].call(this,t);t.target=null}}},mn=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Hh=1234567,Pr=Math.PI/180,tr=180/Math.PI;function fi(){let i=Math.random()*4294967295|0,t=Math.random()*4294967295|0,e=Math.random()*4294967295|0,n=Math.random()*4294967295|0;return(mn[i&255]+mn[i>>8&255]+mn[i>>16&255]+mn[i>>24&255]+"-"+mn[t&255]+mn[t>>8&255]+"-"+mn[t>>16&15|64]+mn[t>>24&255]+"-"+mn[e&63|128]+mn[e>>8&255]+"-"+mn[e>>16&255]+mn[e>>24&255]+mn[n&255]+mn[n>>8&255]+mn[n>>16&255]+mn[n>>24&255]).toLowerCase()}function le(i,t,e){return Math.max(t,Math.min(e,i))}function eh(i,t){return(i%t+t)%t}function Tf(i,t,e,n,s){return n+(i-t)*(s-n)/(e-t)}function Af(i,t,e){return i!==t?(e-i)/(t-i):0}function Ir(i,t,e){return(1-e)*i+e*t}function Rf(i,t,e,n){return Ir(i,t,1-Math.exp(-e*n))}function Cf(i,t=1){return t-Math.abs(eh(i,t*2)-t)}function Pf(i,t,e){return i<=t?0:i>=e?1:(i=(i-t)/(e-t),i*i*(3-2*i))}function If(i,t,e){return i<=t?0:i>=e?1:(i=(i-t)/(e-t),i*i*i*(i*(i*6-15)+10))}function Lf(i,t){return i+Math.floor(Math.random()*(t-i+1))}function Df(i,t){return i+Math.random()*(t-i)}function Uf(i){return i*(.5-Math.random())}function Nf(i){i!==void 0&&(Hh=i);let t=Hh+=1831565813;return t=Math.imul(t^t>>>15,t|1),t^=t+Math.imul(t^t>>>7,t|61),((t^t>>>14)>>>0)/4294967296}function Ff(i){return i*Pr}function zf(i){return i*tr}function Of(i){return i>0&&Number.isInteger(i)&&2**Math.round(Math.log2(i))===i}function Bf(i){return Math.pow(2,Math.ceil(Math.log(i)/Math.LN2))}function kf(i){return Math.pow(2,Math.floor(Math.log(i)/Math.LN2))}function Hf(i,t,e,n,s){let r=Math.cos,a=Math.sin,o=r(e/2),c=a(e/2),l=r((t+n)/2),u=a((t+n)/2),d=r((t-n)/2),h=a((t-n)/2),f=r((n-t)/2),g=a((n-t)/2);switch(s){case"XYX":i.set(o*u,c*d,c*h,o*l);break;case"YZY":i.set(c*h,o*u,c*d,o*l);break;case"ZXZ":i.set(c*d,c*h,o*u,o*l);break;case"XZX":i.set(o*u,c*g,c*f,o*l);break;case"YXY":i.set(c*f,o*u,c*g,o*l);break;case"ZYZ":i.set(c*g,c*f,o*u,o*l);break;default:ie("MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+s)}}function ii(i,t){switch(t.constructor){case Float32Array:return i;case Uint32Array:return i/4294967295;case Uint16Array:return i/65535;case Uint8Array:case Uint8ClampedArray:return i/255;case Int32Array:return Math.max(i/2147483647,-1);case Int16Array:return Math.max(i/32767,-1);case Int8Array:return Math.max(i/127,-1);default:throw new Error("THREE.MathUtils: Invalid component type.")}}function De(i,t){switch(t.constructor){case Float32Array:return i;case Uint32Array:return Math.round(i*4294967295);case Uint16Array:return Math.round(i*65535);case Uint8Array:case Uint8ClampedArray:return Math.round(i*255);case Int32Array:return Math.round(i*2147483647);case Int16Array:return Math.round(i*32767);case Int8Array:return Math.round(i*127);default:throw new Error("THREE.MathUtils: Invalid component type.")}}var Mi={DEG2RAD:Pr,RAD2DEG:tr,generateUUID:fi,clamp:le,euclideanModulo:eh,mapLinear:Tf,inverseLerp:Af,lerp:Ir,damp:Rf,pingpong:Cf,smoothstep:Pf,smootherstep:If,randInt:Lf,randFloat:Df,randFloatSpread:Uf,seededRandom:Nf,degToRad:Ff,radToDeg:zf,isPowerOfTwo:Of,ceilPowerOfTwo:Bf,floorPowerOfTwo:kf,setQuaternionFromProperEuler:Hf,normalize:De,denormalize:ii},oh=class oh{constructor(t=0,e=0){this.x=t,this.y=e}get width(){return this.x}set width(t){this.x=t}get height(){return this.y}set height(t){this.y=t}set(t,e){return this.x=t,this.y=e,this}setScalar(t){return this.x=t,this.y=t,this}setX(t){return this.x=t,this}setY(t){return this.y=t,this}setComponent(t,e){switch(t){case 0:this.x=e;break;case 1:this.y=e;break;default:throw new Error("THREE.Vector2: index is out of range: "+t)}return this}getComponent(t){switch(t){case 0:return this.x;case 1:return this.y;default:throw new Error("THREE.Vector2: index is out of range: "+t)}}clone(){return new this.constructor(this.x,this.y)}copy(t){return this.x=t.x,this.y=t.y,this}add(t){return this.x+=t.x,this.y+=t.y,this}addScalar(t){return this.x+=t,this.y+=t,this}addVectors(t,e){return this.x=t.x+e.x,this.y=t.y+e.y,this}addScaledVector(t,e){return this.x+=t.x*e,this.y+=t.y*e,this}sub(t){return this.x-=t.x,this.y-=t.y,this}subScalar(t){return this.x-=t,this.y-=t,this}subVectors(t,e){return this.x=t.x-e.x,this.y=t.y-e.y,this}multiply(t){return this.x*=t.x,this.y*=t.y,this}multiplyScalar(t){return this.x*=t,this.y*=t,this}divide(t){return this.x/=t.x,this.y/=t.y,this}divideScalar(t){return this.multiplyScalar(1/t)}applyMatrix3(t){let e=this.x,n=this.y,s=t.elements;return this.x=s[0]*e+s[3]*n+s[6],this.y=s[1]*e+s[4]*n+s[7],this}min(t){return this.x=Math.min(this.x,t.x),this.y=Math.min(this.y,t.y),this}max(t){return this.x=Math.max(this.x,t.x),this.y=Math.max(this.y,t.y),this}clamp(t,e){return this.x=le(this.x,t.x,e.x),this.y=le(this.y,t.y,e.y),this}clampScalar(t,e){return this.x=le(this.x,t,e),this.y=le(this.y,t,e),this}clampLength(t,e){let n=this.length();return this.divideScalar(n||1).multiplyScalar(le(n,t,e))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(t){return this.x*t.x+this.y*t.y}cross(t){return this.x*t.y-this.y*t.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(t){let e=Math.sqrt(this.lengthSq()*t.lengthSq());if(e===0)return Math.PI/2;let n=this.dot(t)/e;return Math.acos(le(n,-1,1))}distanceTo(t){return Math.sqrt(this.distanceToSquared(t))}distanceToSquared(t){let e=this.x-t.x,n=this.y-t.y;return e*e+n*n}manhattanDistanceTo(t){return Math.abs(this.x-t.x)+Math.abs(this.y-t.y)}setLength(t){return this.normalize().multiplyScalar(t)}lerp(t,e){return this.x+=(t.x-this.x)*e,this.y+=(t.y-this.y)*e,this}lerpVectors(t,e,n){return this.x=t.x+(e.x-t.x)*n,this.y=t.y+(e.y-t.y)*n,this}equals(t){return t.x===this.x&&t.y===this.y}fromArray(t,e=0){return this.x=t[e],this.y=t[e+1],this}toArray(t=[],e=0){return t[e]=this.x,t[e+1]=this.y,t}fromBufferAttribute(t,e){return this.x=t.getX(e),this.y=t.getY(e),this}rotateAround(t,e){let n=Math.cos(e),s=Math.sin(e),r=this.x-t.x,a=this.y-t.y;return this.x=r*n-a*s+t.x,this.y=r*s+a*n+t.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};oh.prototype.isVector2=!0;var vt=oh,sn=class{constructor(t=0,e=0,n=0,s=1){this.isQuaternion=!0,this._x=t,this._y=e,this._z=n,this._w=s}static slerpFlat(t,e,n,s,r,a,o){let c=n[s+0],l=n[s+1],u=n[s+2],d=n[s+3],h=r[a+0],f=r[a+1],g=r[a+2],x=r[a+3];if(d!==x||c!==h||l!==f||u!==g){let p=c*h+l*f+u*g+d*x;p<0&&(h=-h,f=-f,g=-g,x=-x,p=-p);let m=1-o;if(p<.9995){let y=Math.acos(p),E=Math.sin(y);m=Math.sin(m*y)/E,o=Math.sin(o*y)/E,c=c*m+h*o,l=l*m+f*o,u=u*m+g*o,d=d*m+x*o}else{c=c*m+h*o,l=l*m+f*o,u=u*m+g*o,d=d*m+x*o;let y=1/Math.sqrt(c*c+l*l+u*u+d*d);c*=y,l*=y,u*=y,d*=y}}t[e]=c,t[e+1]=l,t[e+2]=u,t[e+3]=d}static multiplyQuaternionsFlat(t,e,n,s,r,a){let o=n[s],c=n[s+1],l=n[s+2],u=n[s+3],d=r[a],h=r[a+1],f=r[a+2],g=r[a+3];return t[e]=o*g+u*d+c*f-l*h,t[e+1]=c*g+u*h+l*d-o*f,t[e+2]=l*g+u*f+o*h-c*d,t[e+3]=u*g-o*d-c*h-l*f,t}get x(){return this._x}set x(t){this._x=t,this._onChangeCallback()}get y(){return this._y}set y(t){this._y=t,this._onChangeCallback()}get z(){return this._z}set z(t){this._z=t,this._onChangeCallback()}get w(){return this._w}set w(t){this._w=t,this._onChangeCallback()}set(t,e,n,s){return this._x=t,this._y=e,this._z=n,this._w=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(t){return this._x=t.x,this._y=t.y,this._z=t.z,this._w=t.w,this._onChangeCallback(),this}setFromEuler(t,e=!0){let n=t._x,s=t._y,r=t._z,a=t._order,o=Math.cos,c=Math.sin,l=o(n/2),u=o(s/2),d=o(r/2),h=c(n/2),f=c(s/2),g=c(r/2);switch(a){case"XYZ":this._x=h*u*d+l*f*g,this._y=l*f*d-h*u*g,this._z=l*u*g+h*f*d,this._w=l*u*d-h*f*g;break;case"YXZ":this._x=h*u*d+l*f*g,this._y=l*f*d-h*u*g,this._z=l*u*g-h*f*d,this._w=l*u*d+h*f*g;break;case"ZXY":this._x=h*u*d-l*f*g,this._y=l*f*d+h*u*g,this._z=l*u*g+h*f*d,this._w=l*u*d-h*f*g;break;case"ZYX":this._x=h*u*d-l*f*g,this._y=l*f*d+h*u*g,this._z=l*u*g-h*f*d,this._w=l*u*d+h*f*g;break;case"YZX":this._x=h*u*d+l*f*g,this._y=l*f*d+h*u*g,this._z=l*u*g-h*f*d,this._w=l*u*d-h*f*g;break;case"XZY":this._x=h*u*d-l*f*g,this._y=l*f*d-h*u*g,this._z=l*u*g+h*f*d,this._w=l*u*d+h*f*g;break;default:ie("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return e===!0&&this._onChangeCallback(),this}setFromAxisAngle(t,e){let n=e/2,s=Math.sin(n);return this._x=t.x*s,this._y=t.y*s,this._z=t.z*s,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(t){let e=t.elements,n=e[0],s=e[4],r=e[8],a=e[1],o=e[5],c=e[9],l=e[2],u=e[6],d=e[10],h=n+o+d;if(h>0){let f=.5/Math.sqrt(h+1);this._w=.25/f,this._x=(u-c)*f,this._y=(r-l)*f,this._z=(a-s)*f}else if(n>o&&n>d){let f=2*Math.sqrt(1+n-o-d);this._w=(u-c)/f,this._x=.25*f,this._y=(s+a)/f,this._z=(r+l)/f}else if(o>d){let f=2*Math.sqrt(1+o-n-d);this._w=(r-l)/f,this._x=(s+a)/f,this._y=.25*f,this._z=(c+u)/f}else{let f=2*Math.sqrt(1+d-n-o);this._w=(a-s)/f,this._x=(r+l)/f,this._y=(c+u)/f,this._z=.25*f}return this._onChangeCallback(),this}setFromUnitVectors(t,e){let n=t.dot(e)+1;return n<1e-8?(n=0,Math.abs(t.x)>Math.abs(t.z)?(this._x=-t.y,this._y=t.x,this._z=0,this._w=n):(this._x=0,this._y=-t.z,this._z=t.y,this._w=n)):(this._x=t.y*e.z-t.z*e.y,this._y=t.z*e.x-t.x*e.z,this._z=t.x*e.y-t.y*e.x,this._w=n),this.normalize()}angleTo(t){return 2*Math.acos(Math.abs(le(this.dot(t),-1,1)))}rotateTowards(t,e){let n=this.angleTo(t);if(n===0)return this;let s=Math.min(1,e/n);return this.slerp(t,s),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(t){return this._x*t._x+this._y*t._y+this._z*t._z+this._w*t._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let t=this.length();return t===0?(this._x=0,this._y=0,this._z=0,this._w=1):(t=1/t,this._x=this._x*t,this._y=this._y*t,this._z=this._z*t,this._w=this._w*t),this._onChangeCallback(),this}multiply(t){return this.multiplyQuaternions(this,t)}premultiply(t){return this.multiplyQuaternions(t,this)}multiplyQuaternions(t,e){let n=t._x,s=t._y,r=t._z,a=t._w,o=e._x,c=e._y,l=e._z,u=e._w;return this._x=n*u+a*o+s*l-r*c,this._y=s*u+a*c+r*o-n*l,this._z=r*u+a*l+n*c-s*o,this._w=a*u-n*o-s*c-r*l,this._onChangeCallback(),this}slerp(t,e){let n=t._x,s=t._y,r=t._z,a=t._w,o=this.dot(t);o<0&&(n=-n,s=-s,r=-r,a=-a,o=-o);let c=1-e;if(o<.9995){let l=Math.acos(o),u=Math.sin(l);c=Math.sin(c*l)/u,e=Math.sin(e*l)/u,this._x=this._x*c+n*e,this._y=this._y*c+s*e,this._z=this._z*c+r*e,this._w=this._w*c+a*e,this._onChangeCallback()}else this._x=this._x*c+n*e,this._y=this._y*c+s*e,this._z=this._z*c+r*e,this._w=this._w*c+a*e,this.normalize();return this}slerpQuaternions(t,e,n){return this.copy(t).slerp(e,n)}random(){let t=2*Math.PI*Math.random(),e=2*Math.PI*Math.random(),n=Math.random(),s=Math.sqrt(1-n),r=Math.sqrt(n);return this.set(s*Math.sin(t),s*Math.cos(t),r*Math.sin(e),r*Math.cos(e))}equals(t){return t._x===this._x&&t._y===this._y&&t._z===this._z&&t._w===this._w}fromArray(t,e=0){return this._x=t[e],this._y=t[e+1],this._z=t[e+2],this._w=t[e+3],this._onChangeCallback(),this}toArray(t=[],e=0){return t[e]=this._x,t[e+1]=this._y,t[e+2]=this._z,t[e+3]=this._w,t}fromBufferAttribute(t,e){return this._x=t.getX(e),this._y=t.getY(e),this._z=t.getZ(e),this._w=t.getW(e),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(t){return this._onChangeCallback=t,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}},ch=class ch{constructor(t=0,e=0,n=0){this.x=t,this.y=e,this.z=n}set(t,e,n){return n===void 0&&(n=this.z),this.x=t,this.y=e,this.z=n,this}setScalar(t){return this.x=t,this.y=t,this.z=t,this}setX(t){return this.x=t,this}setY(t){return this.y=t,this}setZ(t){return this.z=t,this}setComponent(t,e){switch(t){case 0:this.x=e;break;case 1:this.y=e;break;case 2:this.z=e;break;default:throw new Error("THREE.Vector3: index is out of range: "+t)}return this}getComponent(t){switch(t){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("THREE.Vector3: index is out of range: "+t)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(t){return this.x=t.x,this.y=t.y,this.z=t.z,this}add(t){return this.x+=t.x,this.y+=t.y,this.z+=t.z,this}addScalar(t){return this.x+=t,this.y+=t,this.z+=t,this}addVectors(t,e){return this.x=t.x+e.x,this.y=t.y+e.y,this.z=t.z+e.z,this}addScaledVector(t,e){return this.x+=t.x*e,this.y+=t.y*e,this.z+=t.z*e,this}sub(t){return this.x-=t.x,this.y-=t.y,this.z-=t.z,this}subScalar(t){return this.x-=t,this.y-=t,this.z-=t,this}subVectors(t,e){return this.x=t.x-e.x,this.y=t.y-e.y,this.z=t.z-e.z,this}multiply(t){return this.x*=t.x,this.y*=t.y,this.z*=t.z,this}multiplyScalar(t){return this.x*=t,this.y*=t,this.z*=t,this}multiplyVectors(t,e){return this.x=t.x*e.x,this.y=t.y*e.y,this.z=t.z*e.z,this}applyEuler(t){return this.applyQuaternion(Vh.setFromEuler(t))}applyAxisAngle(t,e){return this.applyQuaternion(Vh.setFromAxisAngle(t,e))}applyMatrix3(t){let e=this.x,n=this.y,s=this.z,r=t.elements;return this.x=r[0]*e+r[3]*n+r[6]*s,this.y=r[1]*e+r[4]*n+r[7]*s,this.z=r[2]*e+r[5]*n+r[8]*s,this}applyNormalMatrix(t){return this.applyMatrix3(t).normalize()}applyMatrix4(t){let e=this.x,n=this.y,s=this.z,r=t.elements,a=1/(r[3]*e+r[7]*n+r[11]*s+r[15]);return this.x=(r[0]*e+r[4]*n+r[8]*s+r[12])*a,this.y=(r[1]*e+r[5]*n+r[9]*s+r[13])*a,this.z=(r[2]*e+r[6]*n+r[10]*s+r[14])*a,this}applyQuaternion(t){let e=this.x,n=this.y,s=this.z,r=t.x,a=t.y,o=t.z,c=t.w,l=2*(a*s-o*n),u=2*(o*e-r*s),d=2*(r*n-a*e);return this.x=e+c*l+a*d-o*u,this.y=n+c*u+o*l-r*d,this.z=s+c*d+r*u-a*l,this}project(t){return this.applyMatrix4(t.matrixWorldInverse).applyMatrix4(t.projectionMatrix)}unproject(t){return this.applyMatrix4(t.projectionMatrixInverse).applyMatrix4(t.matrixWorld)}transformDirection(t){let e=this.x,n=this.y,s=this.z,r=t.elements;return this.x=r[0]*e+r[4]*n+r[8]*s,this.y=r[1]*e+r[5]*n+r[9]*s,this.z=r[2]*e+r[6]*n+r[10]*s,this.normalize()}divide(t){return this.x/=t.x,this.y/=t.y,this.z/=t.z,this}divideScalar(t){return this.multiplyScalar(1/t)}min(t){return this.x=Math.min(this.x,t.x),this.y=Math.min(this.y,t.y),this.z=Math.min(this.z,t.z),this}max(t){return this.x=Math.max(this.x,t.x),this.y=Math.max(this.y,t.y),this.z=Math.max(this.z,t.z),this}clamp(t,e){return this.x=le(this.x,t.x,e.x),this.y=le(this.y,t.y,e.y),this.z=le(this.z,t.z,e.z),this}clampScalar(t,e){return this.x=le(this.x,t,e),this.y=le(this.y,t,e),this.z=le(this.z,t,e),this}clampLength(t,e){let n=this.length();return this.divideScalar(n||1).multiplyScalar(le(n,t,e))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(t){return this.x*t.x+this.y*t.y+this.z*t.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(t){return this.normalize().multiplyScalar(t)}lerp(t,e){return this.x+=(t.x-this.x)*e,this.y+=(t.y-this.y)*e,this.z+=(t.z-this.z)*e,this}lerpVectors(t,e,n){return this.x=t.x+(e.x-t.x)*n,this.y=t.y+(e.y-t.y)*n,this.z=t.z+(e.z-t.z)*n,this}cross(t){return this.crossVectors(this,t)}crossVectors(t,e){let n=t.x,s=t.y,r=t.z,a=e.x,o=e.y,c=e.z;return this.x=s*c-r*o,this.y=r*a-n*c,this.z=n*o-s*a,this}projectOnVector(t){let e=t.lengthSq();if(e===0)return this.set(0,0,0);let n=t.dot(this)/e;return this.copy(t).multiplyScalar(n)}projectOnPlane(t){return $c.copy(this).projectOnVector(t),this.sub($c)}reflect(t){return this.sub($c.copy(t).multiplyScalar(2*this.dot(t)))}angleTo(t){let e=Math.sqrt(this.lengthSq()*t.lengthSq());if(e===0)return Math.PI/2;let n=this.dot(t)/e;return Math.acos(le(n,-1,1))}distanceTo(t){return Math.sqrt(this.distanceToSquared(t))}distanceToSquared(t){let e=this.x-t.x,n=this.y-t.y,s=this.z-t.z;return e*e+n*n+s*s}manhattanDistanceTo(t){return Math.abs(this.x-t.x)+Math.abs(this.y-t.y)+Math.abs(this.z-t.z)}setFromSpherical(t){return this.setFromSphericalCoords(t.radius,t.phi,t.theta)}setFromSphericalCoords(t,e,n){let s=Math.sin(e)*t;return this.x=s*Math.sin(n),this.y=Math.cos(e)*t,this.z=s*Math.cos(n),this}setFromCylindrical(t){return this.setFromCylindricalCoords(t.radius,t.theta,t.y)}setFromCylindricalCoords(t,e,n){return this.x=t*Math.sin(e),this.y=n,this.z=t*Math.cos(e),this}setFromMatrixPosition(t){let e=t.elements;return this.x=e[12],this.y=e[13],this.z=e[14],this}setFromMatrixScale(t){let e=this.setFromMatrixColumn(t,0).length(),n=this.setFromMatrixColumn(t,1).length(),s=this.setFromMatrixColumn(t,2).length();return this.x=e,this.y=n,this.z=s,this}setFromMatrixColumn(t,e){return this.fromArray(t.elements,e*4)}setFromMatrix3Column(t,e){return this.fromArray(t.elements,e*3)}setFromEuler(t){return this.x=t._x,this.y=t._y,this.z=t._z,this}setFromColor(t){return this.x=t.r,this.y=t.g,this.z=t.b,this}equals(t){return t.x===this.x&&t.y===this.y&&t.z===this.z}fromArray(t,e=0){return this.x=t[e],this.y=t[e+1],this.z=t[e+2],this}toArray(t=[],e=0){return t[e]=this.x,t[e+1]=this.y,t[e+2]=this.z,t}fromBufferAttribute(t,e){return this.x=t.getX(e),this.y=t.getY(e),this.z=t.getZ(e),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){let t=Math.random()*Math.PI*2,e=Math.random()*2-1,n=Math.sqrt(1-e*e);return this.x=n*Math.cos(t),this.y=e,this.z=n*Math.sin(t),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};ch.prototype.isVector3=!0;var C=ch,$c=new C,Vh=new sn,lh=class lh{constructor(t,e,n,s,r,a,o,c,l){this.elements=[1,0,0,0,1,0,0,0,1],t!==void 0&&this.set(t,e,n,s,r,a,o,c,l)}set(t,e,n,s,r,a,o,c,l){let u=this.elements;return u[0]=t,u[1]=s,u[2]=o,u[3]=e,u[4]=r,u[5]=c,u[6]=n,u[7]=a,u[8]=l,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(t){let e=this.elements,n=t.elements;return e[0]=n[0],e[1]=n[1],e[2]=n[2],e[3]=n[3],e[4]=n[4],e[5]=n[5],e[6]=n[6],e[7]=n[7],e[8]=n[8],this}extractBasis(t,e,n){return t.setFromMatrix3Column(this,0),e.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(t){let e=t.elements;return this.set(e[0],e[4],e[8],e[1],e[5],e[9],e[2],e[6],e[10]),this}multiply(t){return this.multiplyMatrices(this,t)}premultiply(t){return this.multiplyMatrices(t,this)}multiplyMatrices(t,e){let n=t.elements,s=e.elements,r=this.elements,a=n[0],o=n[3],c=n[6],l=n[1],u=n[4],d=n[7],h=n[2],f=n[5],g=n[8],x=s[0],p=s[3],m=s[6],y=s[1],E=s[4],v=s[7],b=s[2],M=s[5],A=s[8];return r[0]=a*x+o*y+c*b,r[3]=a*p+o*E+c*M,r[6]=a*m+o*v+c*A,r[1]=l*x+u*y+d*b,r[4]=l*p+u*E+d*M,r[7]=l*m+u*v+d*A,r[2]=h*x+f*y+g*b,r[5]=h*p+f*E+g*M,r[8]=h*m+f*v+g*A,this}multiplyScalar(t){let e=this.elements;return e[0]*=t,e[3]*=t,e[6]*=t,e[1]*=t,e[4]*=t,e[7]*=t,e[2]*=t,e[5]*=t,e[8]*=t,this}determinant(){let t=this.elements,e=t[0],n=t[1],s=t[2],r=t[3],a=t[4],o=t[5],c=t[6],l=t[7],u=t[8];return e*a*u-e*o*l-n*r*u+n*o*c+s*r*l-s*a*c}invert(){let t=this.elements,e=t[0],n=t[1],s=t[2],r=t[3],a=t[4],o=t[5],c=t[6],l=t[7],u=t[8],d=u*a-o*l,h=o*c-u*r,f=l*r-a*c,g=e*d+n*h+s*f;if(g===0)return this.set(0,0,0,0,0,0,0,0,0);let x=1/g;return t[0]=d*x,t[1]=(s*l-u*n)*x,t[2]=(o*n-s*a)*x,t[3]=h*x,t[4]=(u*e-s*c)*x,t[5]=(s*r-o*e)*x,t[6]=f*x,t[7]=(n*c-l*e)*x,t[8]=(a*e-n*r)*x,this}transpose(){let t,e=this.elements;return t=e[1],e[1]=e[3],e[3]=t,t=e[2],e[2]=e[6],e[6]=t,t=e[5],e[5]=e[7],e[7]=t,this}getNormalMatrix(t){return this.setFromMatrix4(t).invert().transpose()}transposeIntoArray(t){let e=this.elements;return t[0]=e[0],t[1]=e[3],t[2]=e[6],t[3]=e[1],t[4]=e[4],t[5]=e[7],t[6]=e[2],t[7]=e[5],t[8]=e[8],this}setUvTransform(t,e,n,s,r,a,o){let c=Math.cos(r),l=Math.sin(r);return this.set(n*c,n*l,-n*(c*a+l*o)+a+t,-s*l,s*c,-s*(-l*a+c*o)+o+e,0,0,1),this}scale(t,e){return _s("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply(Jc.makeScale(t,e)),this}rotate(t){return _s("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply(Jc.makeRotation(-t)),this}translate(t,e){return _s("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply(Jc.makeTranslation(t,e)),this}makeTranslation(t,e){return t.isVector2?this.set(1,0,t.x,0,1,t.y,0,0,1):this.set(1,0,t,0,1,e,0,0,1),this}makeRotation(t){let e=Math.cos(t),n=Math.sin(t);return this.set(e,-n,0,n,e,0,0,0,1),this}makeScale(t,e){return this.set(t,0,0,0,e,0,0,0,1),this}equals(t){let e=this.elements,n=t.elements;for(let s=0;s<9;s++)if(e[s]!==n[s])return!1;return!0}fromArray(t,e=0){for(let n=0;n<9;n++)this.elements[n]=t[n+e];return this}toArray(t=[],e=0){let n=this.elements;return t[e]=n[0],t[e+1]=n[1],t[e+2]=n[2],t[e+3]=n[3],t[e+4]=n[4],t[e+5]=n[5],t[e+6]=n[6],t[e+7]=n[7],t[e+8]=n[8],t}clone(){return new this.constructor().fromArray(this.elements)}};lh.prototype.isMatrix3=!0;var he=lh,Jc=new he,Gh=new he().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Wh=new he().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function Vf(){let i={enabled:!0,workingColorSpace:Nr,spaces:{},convert:function(s,r,a){return this.enabled===!1||r===a||!r||!a||(this.spaces[r].transfer===Ie&&(s.r=Fi(s.r),s.g=Fi(s.g),s.b=Fi(s.b)),this.spaces[r].primaries!==this.spaces[a].primaries&&(s.applyMatrix3(this.spaces[r].toXYZ),s.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===Ie&&(s.r=Zs(s.r),s.g=Zs(s.g),s.b=Zs(s.b))),s},workingToColorSpace:function(s,r){return this.convert(s,this.workingColorSpace,r)},colorSpaceToWorking:function(s,r){return this.convert(s,r,this.workingColorSpace)},getPrimaries:function(s){return this.spaces[s].primaries},getTransfer:function(s){return s===ki?Fr:this.spaces[s].transfer},getToneMappingMode:function(s){return this.spaces[s].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(s,r=this.workingColorSpace){return s.fromArray(this.spaces[r].luminanceCoefficients)},define:function(s){Object.assign(this.spaces,s)},_getMatrix:function(s,r,a){return s.copy(this.spaces[r].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(s){return this.spaces[s].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(s=this.workingColorSpace){return this.spaces[s].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(s,r){return _s("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),i.workingToColorSpace(s,r)},toWorkingColorSpace:function(s,r){return _s("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),i.colorSpaceToWorking(s,r)}},t=[.64,.33,.3,.6,.15,.06],e=[.2126,.7152,.0722],n=[.3127,.329];return i.define({[Nr]:{primaries:t,whitePoint:n,transfer:Fr,toXYZ:Gh,fromXYZ:Wh,luminanceCoefficients:e,workingColorSpaceConfig:{unpackColorSpace:bn},outputColorSpaceConfig:{drawingBufferColorSpace:bn}},[bn]:{primaries:t,whitePoint:n,transfer:Ie,toXYZ:Gh,fromXYZ:Wh,luminanceCoefficients:e,outputColorSpaceConfig:{drawingBufferColorSpace:bn}}}),i}var Me=Vf();function Fi(i){return i<.04045?i*.0773993808:Math.pow(i*.9478672986+.0521327014,2.4)}function Zs(i){return i<.0031308?i*12.92:1.055*Math.pow(i,.41666)-.055}var Ds,mo=class{static getDataURL(t,e="image/png"){if(/^data:/i.test(t.src)||typeof HTMLCanvasElement>"u")return t.src;let n;if(t instanceof HTMLCanvasElement)n=t;else{Ds===void 0&&(Ds=zr("canvas")),Ds.width=t.width,Ds.height=t.height;let s=Ds.getContext("2d");t instanceof ImageData?s.putImageData(t,0,0):s.drawImage(t,0,0,t.width,t.height),n=Ds}return n.toDataURL(e)}static sRGBToLinear(t){if(typeof HTMLImageElement<"u"&&t instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&t instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&t instanceof ImageBitmap){let e=zr("canvas");e.width=t.width,e.height=t.height;let n=e.getContext("2d");n.drawImage(t,0,0,t.width,t.height);let s=n.getImageData(0,0,t.width,t.height),r=s.data;for(let a=0;a<r.length;a++)r[a]=Fi(r[a]/255)*255;return n.putImageData(s,0,0),e}else if(t.data){let e=t.data.slice(0);for(let n=0;n<e.length;n++)e instanceof Uint8Array||e instanceof Uint8ClampedArray?e[n]=Math.floor(Fi(e[n]/255)*255):e[n]=Fi(e[n]);return{data:e,width:t.width,height:t.height}}else return ie("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),t}},Gf=0,er=class{constructor(t=null){this.isTextureSource=!0,Object.defineProperty(this,"id",{value:Gf++}),this.uuid=fi(),this.data=t,this.dataReady=!0,this.version=0}getSize(t){let e=this.data;return typeof HTMLVideoElement<"u"&&e instanceof HTMLVideoElement?t.set(e.videoWidth,e.videoHeight,0):typeof VideoFrame<"u"&&e instanceof VideoFrame?t.set(e.displayWidth,e.displayHeight,0):e!==null?t.set(e.width,e.height,e.depth||0):t.set(0,0,0),t}set needsUpdate(t){t===!0&&this.version++}toJSON(t){let e=t===void 0||typeof t=="string";if(!e&&t.images[this.uuid]!==void 0)return t.images[this.uuid];let n={uuid:this.uuid,url:""},s=this.data;if(s!==null){let r;if(Array.isArray(s)){r=[];for(let a=0,o=s.length;a<o;a++)s[a].isDataTexture?r.push(Kc(s[a].image)):r.push(Kc(s[a]))}else r=Kc(s);n.url=r}return e||(t.images[this.uuid]=n),n}};function Kc(i){return typeof HTMLImageElement<"u"&&i instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&i instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&i instanceof ImageBitmap?mo.getDataURL(i):i.data?{data:Array.from(i.data),width:i.width,height:i.height,type:i.data.constructor.name}:(ie("Texture: Unable to serialize Texture."),{})}var Wf=0,Qc=new C,En=class i extends mi{constructor(t=i.DEFAULT_IMAGE,e=i.DEFAULT_MAPPING,n=Wn,s=Wn,r=Ke,a=cs,o=Yn,c=Ln,l=i.DEFAULT_ANISOTROPY,u=ki){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Wf++}),this.uuid=fi(),this.name="",this.source=new er(t),this.mipmaps=[],this.mapping=e,this.channel=0,this.wrapS=n,this.wrapT=s,this.magFilter=r,this.minFilter=a,this.anisotropy=l,this.format=o,this.internalFormat=null,this.type=c,this.offset=new vt(0,0),this.repeat=new vt(1,1),this.center=new vt(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new he,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=u,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(t&&t.depth&&t.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(Qc).x}get height(){return this.source.getSize(Qc).y}get depth(){return this.source.getSize(Qc).z}get image(){return this.source.data}set image(t){this.source.data=t}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(t,e){this.updateRanges.push({start:t,count:e})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(t){return this.name=t.name,this.source=t.source,this.mipmaps=t.mipmaps.slice(0),this.mapping=t.mapping,this.channel=t.channel,this.wrapS=t.wrapS,this.wrapT=t.wrapT,this.magFilter=t.magFilter,this.minFilter=t.minFilter,this.anisotropy=t.anisotropy,this.format=t.format,this.internalFormat=t.internalFormat,this.type=t.type,this.normalized=t.normalized,this.offset.copy(t.offset),this.repeat.copy(t.repeat),this.center.copy(t.center),this.rotation=t.rotation,this.matrixAutoUpdate=t.matrixAutoUpdate,this.matrix.copy(t.matrix),this.generateMipmaps=t.generateMipmaps,this.premultiplyAlpha=t.premultiplyAlpha,this.flipY=t.flipY,this.unpackAlignment=t.unpackAlignment,this.colorSpace=t.colorSpace,this.renderTarget=t.renderTarget,this.isRenderTargetTexture=t.isRenderTargetTexture,this.isArrayTexture=t.isArrayTexture,this.userData=JSON.parse(JSON.stringify(t.userData)),this.needsUpdate=!0,this}setValues(t){for(let e in t){let n=t[e];if(n===void 0){ie(`Texture.setValues(): parameter '${e}' has value of undefined.`);continue}let s=this[e];if(s===void 0){ie(`Texture.setValues(): property '${e}' does not exist.`);continue}s&&n&&s.isVector2&&n.isVector2||s&&n&&s.isVector3&&n.isVector3||s&&n&&s.isMatrix3&&n.isMatrix3?s.copy(n):this[e]=n}}toJSON(t){let e=t===void 0||typeof t=="string";if(!e&&t.textures[this.uuid]!==void 0)return t.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(t).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),e||(t.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(t){if(this.mapping!==ql)return t;if(t.applyMatrix3(this.matrix),t.x<0||t.x>1)switch(this.wrapS){case Js:t.x=t.x-Math.floor(t.x);break;case Wn:t.x=t.x<0?0:1;break;case fo:Math.abs(Math.floor(t.x)%2)===1?t.x=Math.ceil(t.x)-t.x:t.x=t.x-Math.floor(t.x);break}if(t.y<0||t.y>1)switch(this.wrapT){case Js:t.y=t.y-Math.floor(t.y);break;case Wn:t.y=t.y<0?0:1;break;case fo:Math.abs(Math.floor(t.y)%2)===1?t.y=Math.ceil(t.y)-t.y:t.y=t.y-Math.floor(t.y);break}return this.flipY&&(t.y=1-t.y),t}set needsUpdate(t){t===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(t){t===!0&&this.pmremVersion++}};En.DEFAULT_IMAGE=null;En.DEFAULT_MAPPING=ql;En.DEFAULT_ANISOTROPY=1;var hh=class hh{constructor(t=0,e=0,n=0,s=1){this.x=t,this.y=e,this.z=n,this.w=s}get width(){return this.z}set width(t){this.z=t}get height(){return this.w}set height(t){this.w=t}set(t,e,n,s){return this.x=t,this.y=e,this.z=n,this.w=s,this}setScalar(t){return this.x=t,this.y=t,this.z=t,this.w=t,this}setX(t){return this.x=t,this}setY(t){return this.y=t,this}setZ(t){return this.z=t,this}setW(t){return this.w=t,this}setComponent(t,e){switch(t){case 0:this.x=e;break;case 1:this.y=e;break;case 2:this.z=e;break;case 3:this.w=e;break;default:throw new Error("THREE.Vector4: index is out of range: "+t)}return this}getComponent(t){switch(t){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("THREE.Vector4: index is out of range: "+t)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(t){return this.x=t.x,this.y=t.y,this.z=t.z,this.w=t.w!==void 0?t.w:1,this}add(t){return this.x+=t.x,this.y+=t.y,this.z+=t.z,this.w+=t.w,this}addScalar(t){return this.x+=t,this.y+=t,this.z+=t,this.w+=t,this}addVectors(t,e){return this.x=t.x+e.x,this.y=t.y+e.y,this.z=t.z+e.z,this.w=t.w+e.w,this}addScaledVector(t,e){return this.x+=t.x*e,this.y+=t.y*e,this.z+=t.z*e,this.w+=t.w*e,this}sub(t){return this.x-=t.x,this.y-=t.y,this.z-=t.z,this.w-=t.w,this}subScalar(t){return this.x-=t,this.y-=t,this.z-=t,this.w-=t,this}subVectors(t,e){return this.x=t.x-e.x,this.y=t.y-e.y,this.z=t.z-e.z,this.w=t.w-e.w,this}multiply(t){return this.x*=t.x,this.y*=t.y,this.z*=t.z,this.w*=t.w,this}multiplyScalar(t){return this.x*=t,this.y*=t,this.z*=t,this.w*=t,this}applyMatrix4(t){let e=this.x,n=this.y,s=this.z,r=this.w,a=t.elements;return this.x=a[0]*e+a[4]*n+a[8]*s+a[12]*r,this.y=a[1]*e+a[5]*n+a[9]*s+a[13]*r,this.z=a[2]*e+a[6]*n+a[10]*s+a[14]*r,this.w=a[3]*e+a[7]*n+a[11]*s+a[15]*r,this}divide(t){return this.x/=t.x,this.y/=t.y,this.z/=t.z,this.w/=t.w,this}divideScalar(t){return this.multiplyScalar(1/t)}setAxisAngleFromQuaternion(t){this.w=2*Math.acos(t.w);let e=Math.sqrt(1-t.w*t.w);return e<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=t.x/e,this.y=t.y/e,this.z=t.z/e),this}setAxisAngleFromRotationMatrix(t){let e,n,s,r,c=t.elements,l=c[0],u=c[4],d=c[8],h=c[1],f=c[5],g=c[9],x=c[2],p=c[6],m=c[10];if(Math.abs(u-h)<.01&&Math.abs(d-x)<.01&&Math.abs(g-p)<.01){if(Math.abs(u+h)<.1&&Math.abs(d+x)<.1&&Math.abs(g+p)<.1&&Math.abs(l+f+m-3)<.1)return this.set(1,0,0,0),this;e=Math.PI;let E=(l+1)/2,v=(f+1)/2,b=(m+1)/2,M=(u+h)/4,A=(d+x)/4,_=(g+p)/4;return E>v&&E>b?E<.01?(n=0,s=.707106781,r=.707106781):(n=Math.sqrt(E),s=M/n,r=A/n):v>b?v<.01?(n=.707106781,s=0,r=.707106781):(s=Math.sqrt(v),n=M/s,r=_/s):b<.01?(n=.707106781,s=.707106781,r=0):(r=Math.sqrt(b),n=A/r,s=_/r),this.set(n,s,r,e),this}let y=Math.sqrt((p-g)*(p-g)+(d-x)*(d-x)+(h-u)*(h-u));return Math.abs(y)<.001&&(y=1),this.x=(p-g)/y,this.y=(d-x)/y,this.z=(h-u)/y,this.w=Math.acos((l+f+m-1)/2),this}setFromMatrixPosition(t){let e=t.elements;return this.x=e[12],this.y=e[13],this.z=e[14],this.w=e[15],this}min(t){return this.x=Math.min(this.x,t.x),this.y=Math.min(this.y,t.y),this.z=Math.min(this.z,t.z),this.w=Math.min(this.w,t.w),this}max(t){return this.x=Math.max(this.x,t.x),this.y=Math.max(this.y,t.y),this.z=Math.max(this.z,t.z),this.w=Math.max(this.w,t.w),this}clamp(t,e){return this.x=le(this.x,t.x,e.x),this.y=le(this.y,t.y,e.y),this.z=le(this.z,t.z,e.z),this.w=le(this.w,t.w,e.w),this}clampScalar(t,e){return this.x=le(this.x,t,e),this.y=le(this.y,t,e),this.z=le(this.z,t,e),this.w=le(this.w,t,e),this}clampLength(t,e){let n=this.length();return this.divideScalar(n||1).multiplyScalar(le(n,t,e))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(t){return this.x*t.x+this.y*t.y+this.z*t.z+this.w*t.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(t){return this.normalize().multiplyScalar(t)}lerp(t,e){return this.x+=(t.x-this.x)*e,this.y+=(t.y-this.y)*e,this.z+=(t.z-this.z)*e,this.w+=(t.w-this.w)*e,this}lerpVectors(t,e,n){return this.x=t.x+(e.x-t.x)*n,this.y=t.y+(e.y-t.y)*n,this.z=t.z+(e.z-t.z)*n,this.w=t.w+(e.w-t.w)*n,this}equals(t){return t.x===this.x&&t.y===this.y&&t.z===this.z&&t.w===this.w}fromArray(t,e=0){return this.x=t[e],this.y=t[e+1],this.z=t[e+2],this.w=t[e+3],this}toArray(t=[],e=0){return t[e]=this.x,t[e+1]=this.y,t[e+2]=this.z,t[e+3]=this.w,t}fromBufferAttribute(t,e){return this.x=t.getX(e),this.y=t.getY(e),this.z=t.getZ(e),this.w=t.getW(e),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};hh.prototype.isVector4=!0;var xe=hh,go=class extends mi{constructor(t=1,e=1,n={}){super(),n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:Ke,depthBuffer:!0,stencilBuffer:!1,resolveColorBuffer:!0,resolveDepthBuffer:!0,resolveStencilBuffer:!0,storeMultisampledColorBuffer:!0,storeMultisampledDepthBuffer:!0,storeMultisampledStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1,useArrayDepthTexture:!1},n),this.isRenderTarget=!0,this.width=t,this.height=e,this.depth=n.depth,this.scissor=new xe(0,0,t,e),this.scissorTest=!1,this.viewport=new xe(0,0,t,e),this.textures=[];let s={width:t,height:e,depth:n.depth},r=new En(s),a=n.count;for(let o=0;o<a;o++)this.textures[o]=r.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveColorBuffer=n.resolveColorBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this.storeMultisampledColorBuffer=n.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=n.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=n.storeMultisampledStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview,this.useArrayDepthTexture=n.useArrayDepthTexture}_setTextureOptions(t={}){let e={minFilter:Ke,generateMipmaps:!1,flipY:!1,internalFormat:null};t.mapping!==void 0&&(e.mapping=t.mapping),t.wrapS!==void 0&&(e.wrapS=t.wrapS),t.wrapT!==void 0&&(e.wrapT=t.wrapT),t.wrapR!==void 0&&(e.wrapR=t.wrapR),t.magFilter!==void 0&&(e.magFilter=t.magFilter),t.minFilter!==void 0&&(e.minFilter=t.minFilter),t.format!==void 0&&(e.format=t.format),t.type!==void 0&&(e.type=t.type),t.anisotropy!==void 0&&(e.anisotropy=t.anisotropy),t.colorSpace!==void 0&&(e.colorSpace=t.colorSpace),t.flipY!==void 0&&(e.flipY=t.flipY),t.generateMipmaps!==void 0&&(e.generateMipmaps=t.generateMipmaps),t.internalFormat!==void 0&&(e.internalFormat=t.internalFormat);for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(e)}get texture(){return this.textures[0]}set texture(t){this.textures[0]=t}set depthTexture(t){this._depthTexture!==null&&this._depthTexture.renderTarget===this&&(this._depthTexture.renderTarget=null),t!==null&&t.renderTarget===null&&(t.renderTarget=this),this._depthTexture=t}get depthTexture(){return this._depthTexture}setSize(t,e,n=1){if(this.width!==t||this.height!==e||this.depth!==n){this.width=t,this.height=e,this.depth=n;for(let s=0,r=this.textures.length;s<r;s++)this.textures[s].image.width=t,this.textures[s].image.height=e,this.textures[s].image.depth=n,this.textures[s].isData3DTexture!==!0&&(this.textures[s].isArrayTexture=this.textures[s].image.depth>1);this.dispose()}this.viewport.set(0,0,t,e),this.scissor.set(0,0,t,e)}clone(){return new this.constructor().copy(this)}copy(t){this.width=t.width,this.height=t.height,this.depth=t.depth,this.scissor.copy(t.scissor),this.scissorTest=t.scissorTest,this.viewport.copy(t.viewport),this.textures.length=0;for(let e=0,n=t.textures.length;e<n;e++){this.textures[e]=t.textures[e].clone(),this.textures[e].isRenderTargetTexture=!0,this.textures[e].renderTarget=this;let s=Object.assign({},t.textures[e].image);this.textures[e].source=new er(s)}if(this.depthBuffer=t.depthBuffer,this.stencilBuffer=t.stencilBuffer,this.resolveColorBuffer=t.resolveColorBuffer,this.resolveDepthBuffer=t.resolveDepthBuffer,this.resolveStencilBuffer=t.resolveStencilBuffer,this.storeMultisampledColorBuffer=t.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=t.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=t.storeMultisampledStencilBuffer,t.depthTexture!==null)if(t.depthTexture.renderTarget===t){let e=t.depthTexture.clone();e.renderTarget=null,this.depthTexture=e}else this.depthTexture=t.depthTexture;return this.samples=t.samples,this.multiview=t.multiview,this.useArrayDepthTexture=t.useArrayDepthTexture,this}dispose(){this.dispatchEvent({type:"dispose"})}},In=class extends go{constructor(t=1,e=1,n={}){super(t,e,n),this.isWebGLRenderTarget=!0}},Br=class extends En{constructor(t=null,e=1,n=1,s=1){super(null),this.isDataArrayTexture=!0,this.image={data:t,width:e,height:n,depth:s},this.magFilter=nn,this.minFilter=nn,this.wrapR=Wn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}copy(t){return super.copy(t),this.wrapR=t.wrapR,this}addLayerUpdate(t){this.layerUpdates.add(t)}clearLayerUpdates(){this.layerUpdates.clear()}};var vo=class extends En{constructor(t=null,e=1,n=1,s=1){super(null),this.isData3DTexture=!0,this.image={data:t,width:e,height:n,depth:s},this.magFilter=nn,this.minFilter=nn,this.wrapR=Wn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}copy(t){return super.copy(t),this.wrapR=t.wrapR,this}};var Vo=class Vo{constructor(t,e,n,s,r,a,o,c,l,u,d,h,f,g,x,p){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],t!==void 0&&this.set(t,e,n,s,r,a,o,c,l,u,d,h,f,g,x,p)}set(t,e,n,s,r,a,o,c,l,u,d,h,f,g,x,p){let m=this.elements;return m[0]=t,m[4]=e,m[8]=n,m[12]=s,m[1]=r,m[5]=a,m[9]=o,m[13]=c,m[2]=l,m[6]=u,m[10]=d,m[14]=h,m[3]=f,m[7]=g,m[11]=x,m[15]=p,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new Vo().fromArray(this.elements)}copy(t){let e=this.elements,n=t.elements;return e[0]=n[0],e[1]=n[1],e[2]=n[2],e[3]=n[3],e[4]=n[4],e[5]=n[5],e[6]=n[6],e[7]=n[7],e[8]=n[8],e[9]=n[9],e[10]=n[10],e[11]=n[11],e[12]=n[12],e[13]=n[13],e[14]=n[14],e[15]=n[15],this}copyPosition(t){let e=this.elements,n=t.elements;return e[12]=n[12],e[13]=n[13],e[14]=n[14],this}setFromMatrix3(t){let e=t.elements;return this.set(e[0],e[3],e[6],0,e[1],e[4],e[7],0,e[2],e[5],e[8],0,0,0,0,1),this}extractBasis(t,e,n){return this.determinantAffine()===0?(t.set(1,0,0),e.set(0,1,0),n.set(0,0,1),this):(t.setFromMatrixColumn(this,0),e.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this)}makeBasis(t,e,n){return this.set(t.x,e.x,n.x,0,t.y,e.y,n.y,0,t.z,e.z,n.z,0,0,0,0,1),this}extractRotation(t){if(t.determinantAffine()===0)return this.identity();let e=this.elements,n=t.elements,s=1/Us.setFromMatrixColumn(t,0).length(),r=1/Us.setFromMatrixColumn(t,1).length(),a=1/Us.setFromMatrixColumn(t,2).length();return e[0]=n[0]*s,e[1]=n[1]*s,e[2]=n[2]*s,e[3]=0,e[4]=n[4]*r,e[5]=n[5]*r,e[6]=n[6]*r,e[7]=0,e[8]=n[8]*a,e[9]=n[9]*a,e[10]=n[10]*a,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,this}makeRotationFromEuler(t){let e=this.elements,n=t.x,s=t.y,r=t.z,a=Math.cos(n),o=Math.sin(n),c=Math.cos(s),l=Math.sin(s),u=Math.cos(r),d=Math.sin(r);if(t.order==="XYZ"){let h=a*u,f=a*d,g=o*u,x=o*d;e[0]=c*u,e[4]=-c*d,e[8]=l,e[1]=f+g*l,e[5]=h-x*l,e[9]=-o*c,e[2]=x-h*l,e[6]=g+f*l,e[10]=a*c}else if(t.order==="YXZ"){let h=c*u,f=c*d,g=l*u,x=l*d;e[0]=h+x*o,e[4]=g*o-f,e[8]=a*l,e[1]=a*d,e[5]=a*u,e[9]=-o,e[2]=f*o-g,e[6]=x+h*o,e[10]=a*c}else if(t.order==="ZXY"){let h=c*u,f=c*d,g=l*u,x=l*d;e[0]=h-x*o,e[4]=-a*d,e[8]=g+f*o,e[1]=f+g*o,e[5]=a*u,e[9]=x-h*o,e[2]=-a*l,e[6]=o,e[10]=a*c}else if(t.order==="ZYX"){let h=a*u,f=a*d,g=o*u,x=o*d;e[0]=c*u,e[4]=g*l-f,e[8]=h*l+x,e[1]=c*d,e[5]=x*l+h,e[9]=f*l-g,e[2]=-l,e[6]=o*c,e[10]=a*c}else if(t.order==="YZX"){let h=a*c,f=a*l,g=o*c,x=o*l;e[0]=c*u,e[4]=x-h*d,e[8]=g*d+f,e[1]=d,e[5]=a*u,e[9]=-o*u,e[2]=-l*u,e[6]=f*d+g,e[10]=h-x*d}else if(t.order==="XZY"){let h=a*c,f=a*l,g=o*c,x=o*l;e[0]=c*u,e[4]=-d,e[8]=l*u,e[1]=h*d+x,e[5]=a*u,e[9]=f*d-g,e[2]=g*d-f,e[6]=o*u,e[10]=x*d+h}return e[3]=0,e[7]=0,e[11]=0,e[12]=0,e[13]=0,e[14]=0,e[15]=1,this}makeRotationFromQuaternion(t){return this.compose(Xf,t,qf)}lookAt(t,e,n){let s=this.elements;return Un.subVectors(t,e),Un.lengthSq()===0&&(Un.z=1),Un.normalize(),Xi.crossVectors(n,Un),Xi.lengthSq()===0&&(Math.abs(n.z)===1?Un.x+=1e-4:Un.z+=1e-4,Un.normalize(),Xi.crossVectors(n,Un)),Xi.normalize(),La.crossVectors(Un,Xi),s[0]=Xi.x,s[4]=La.x,s[8]=Un.x,s[1]=Xi.y,s[5]=La.y,s[9]=Un.y,s[2]=Xi.z,s[6]=La.z,s[10]=Un.z,this}multiply(t){return this.multiplyMatrices(this,t)}premultiply(t){return this.multiplyMatrices(t,this)}multiplyMatrices(t,e){let n=t.elements,s=e.elements,r=this.elements,a=n[0],o=n[4],c=n[8],l=n[12],u=n[1],d=n[5],h=n[9],f=n[13],g=n[2],x=n[6],p=n[10],m=n[14],y=n[3],E=n[7],v=n[11],b=n[15],M=s[0],A=s[4],_=s[8],T=s[12],P=s[1],L=s[5],F=s[9],V=s[13],I=s[2],z=s[6],q=s[10],j=s[14],at=s[3],K=s[7],st=s[11],it=s[15];return r[0]=a*M+o*P+c*I+l*at,r[4]=a*A+o*L+c*z+l*K,r[8]=a*_+o*F+c*q+l*st,r[12]=a*T+o*V+c*j+l*it,r[1]=u*M+d*P+h*I+f*at,r[5]=u*A+d*L+h*z+f*K,r[9]=u*_+d*F+h*q+f*st,r[13]=u*T+d*V+h*j+f*it,r[2]=g*M+x*P+p*I+m*at,r[6]=g*A+x*L+p*z+m*K,r[10]=g*_+x*F+p*q+m*st,r[14]=g*T+x*V+p*j+m*it,r[3]=y*M+E*P+v*I+b*at,r[7]=y*A+E*L+v*z+b*K,r[11]=y*_+E*F+v*q+b*st,r[15]=y*T+E*V+v*j+b*it,this}multiplyScalar(t){let e=this.elements;return e[0]*=t,e[4]*=t,e[8]*=t,e[12]*=t,e[1]*=t,e[5]*=t,e[9]*=t,e[13]*=t,e[2]*=t,e[6]*=t,e[10]*=t,e[14]*=t,e[3]*=t,e[7]*=t,e[11]*=t,e[15]*=t,this}determinant(){let t=this.elements,e=t[0],n=t[4],s=t[8],r=t[12],a=t[1],o=t[5],c=t[9],l=t[13],u=t[2],d=t[6],h=t[10],f=t[14],g=t[3],x=t[7],p=t[11],m=t[15],y=c*f-l*h,E=o*f-l*d,v=o*h-c*d,b=a*f-l*u,M=a*h-c*u,A=a*d-o*u;return e*(x*y-p*E+m*v)-n*(g*y-p*b+m*M)+s*(g*E-x*b+m*A)-r*(g*v-x*M+p*A)}determinantAffine(){let t=this.elements,e=t[0],n=t[4],s=t[8],r=t[1],a=t[5],o=t[9],c=t[2],l=t[6],u=t[10];return e*(a*u-o*l)-n*(r*u-o*c)+s*(r*l-a*c)}transpose(){let t=this.elements,e;return e=t[1],t[1]=t[4],t[4]=e,e=t[2],t[2]=t[8],t[8]=e,e=t[6],t[6]=t[9],t[9]=e,e=t[3],t[3]=t[12],t[12]=e,e=t[7],t[7]=t[13],t[13]=e,e=t[11],t[11]=t[14],t[14]=e,this}setPosition(t,e,n){let s=this.elements;return t.isVector3?(s[12]=t.x,s[13]=t.y,s[14]=t.z):(s[12]=t,s[13]=e,s[14]=n),this}invert(){let t=this.elements,e=t[0],n=t[1],s=t[2],r=t[3],a=t[4],o=t[5],c=t[6],l=t[7],u=t[8],d=t[9],h=t[10],f=t[11],g=t[12],x=t[13],p=t[14],m=t[15],y=e*o-n*a,E=e*c-s*a,v=e*l-r*a,b=n*c-s*o,M=n*l-r*o,A=s*l-r*c,_=u*x-d*g,T=u*p-h*g,P=u*m-f*g,L=d*p-h*x,F=d*m-f*x,V=h*m-f*p,I=y*V-E*F+v*L+b*P-M*T+A*_;if(I===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let z=1/I;return t[0]=(o*V-c*F+l*L)*z,t[1]=(s*F-n*V-r*L)*z,t[2]=(x*A-p*M+m*b)*z,t[3]=(h*M-d*A-f*b)*z,t[4]=(c*P-a*V-l*T)*z,t[5]=(e*V-s*P+r*T)*z,t[6]=(p*v-g*A-m*E)*z,t[7]=(u*A-h*v+f*E)*z,t[8]=(a*F-o*P+l*_)*z,t[9]=(n*P-e*F-r*_)*z,t[10]=(g*M-x*v+m*y)*z,t[11]=(d*v-u*M-f*y)*z,t[12]=(o*T-a*L-c*_)*z,t[13]=(e*L-n*T+s*_)*z,t[14]=(x*E-g*b-p*y)*z,t[15]=(u*b-d*E+h*y)*z,this}scale(t){let e=this.elements,n=t.x,s=t.y,r=t.z;return e[0]*=n,e[4]*=s,e[8]*=r,e[1]*=n,e[5]*=s,e[9]*=r,e[2]*=n,e[6]*=s,e[10]*=r,e[3]*=n,e[7]*=s,e[11]*=r,this}getMaxScaleOnAxis(){let t=this.elements,e=t[0]*t[0]+t[1]*t[1]+t[2]*t[2],n=t[4]*t[4]+t[5]*t[5]+t[6]*t[6],s=t[8]*t[8]+t[9]*t[9]+t[10]*t[10];return Math.sqrt(Math.max(e,n,s))}makeTranslation(t,e,n){return t.isVector3?this.set(1,0,0,t.x,0,1,0,t.y,0,0,1,t.z,0,0,0,1):this.set(1,0,0,t,0,1,0,e,0,0,1,n,0,0,0,1),this}makeRotationX(t){let e=Math.cos(t),n=Math.sin(t);return this.set(1,0,0,0,0,e,-n,0,0,n,e,0,0,0,0,1),this}makeRotationY(t){let e=Math.cos(t),n=Math.sin(t);return this.set(e,0,n,0,0,1,0,0,-n,0,e,0,0,0,0,1),this}makeRotationZ(t){let e=Math.cos(t),n=Math.sin(t);return this.set(e,-n,0,0,n,e,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(t,e){let n=Math.cos(e),s=Math.sin(e),r=1-n,a=t.x,o=t.y,c=t.z,l=r*a,u=r*o;return this.set(l*a+n,l*o-s*c,l*c+s*o,0,l*o+s*c,u*o+n,u*c-s*a,0,l*c-s*o,u*c+s*a,r*c*c+n,0,0,0,0,1),this}makeScale(t,e,n){return this.set(t,0,0,0,0,e,0,0,0,0,n,0,0,0,0,1),this}makeShear(t,e,n,s,r,a){return this.set(1,n,r,0,t,1,a,0,e,s,1,0,0,0,0,1),this}compose(t,e,n){let s=this.elements,r=e._x,a=e._y,o=e._z,c=e._w,l=r+r,u=a+a,d=o+o,h=r*l,f=r*u,g=r*d,x=a*u,p=a*d,m=o*d,y=c*l,E=c*u,v=c*d,b=n.x,M=n.y,A=n.z;return s[0]=(1-(x+m))*b,s[1]=(f+v)*b,s[2]=(g-E)*b,s[3]=0,s[4]=(f-v)*M,s[5]=(1-(h+m))*M,s[6]=(p+y)*M,s[7]=0,s[8]=(g+E)*A,s[9]=(p-y)*A,s[10]=(1-(h+x))*A,s[11]=0,s[12]=t.x,s[13]=t.y,s[14]=t.z,s[15]=1,this}decompose(t,e,n){let s=this.elements;t.x=s[12],t.y=s[13],t.z=s[14];let r=this.determinantAffine();if(r===0)return n.set(1,1,1),e.identity(),this;let a=Us.set(s[0],s[1],s[2]).length(),o=Us.set(s[4],s[5],s[6]).length(),c=Us.set(s[8],s[9],s[10]).length();r<0&&(a=-a),Qn.copy(this);let l=1/a,u=1/o,d=1/c;return Qn.elements[0]*=l,Qn.elements[1]*=l,Qn.elements[2]*=l,Qn.elements[4]*=u,Qn.elements[5]*=u,Qn.elements[6]*=u,Qn.elements[8]*=d,Qn.elements[9]*=d,Qn.elements[10]*=d,e.setFromRotationMatrix(Qn),n.x=a,n.y=o,n.z=c,this}makePerspective(t,e,n,s,r,a,o=si,c=!1){let l=this.elements,u=2*r/(e-t),d=2*r/(n-s),h=(e+t)/(e-t),f=(n+s)/(n-s),g,x;if(c)g=r/(a-r),x=a*r/(a-r);else if(o===si)g=-(a+r)/(a-r),x=-2*a*r/(a-r);else if(o===Ks)g=-a/(a-r),x=-a*r/(a-r);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return l[0]=u,l[4]=0,l[8]=h,l[12]=0,l[1]=0,l[5]=d,l[9]=f,l[13]=0,l[2]=0,l[6]=0,l[10]=g,l[14]=x,l[3]=0,l[7]=0,l[11]=-1,l[15]=0,this}makeOrthographic(t,e,n,s,r,a,o=si,c=!1){let l=this.elements,u=2/(e-t),d=2/(n-s),h=-(e+t)/(e-t),f=-(n+s)/(n-s),g,x;if(c)g=1/(a-r),x=a/(a-r);else if(o===si)g=-2/(a-r),x=-(a+r)/(a-r);else if(o===Ks)g=-1/(a-r),x=-r/(a-r);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return l[0]=u,l[4]=0,l[8]=0,l[12]=h,l[1]=0,l[5]=d,l[9]=0,l[13]=f,l[2]=0,l[6]=0,l[10]=g,l[14]=x,l[3]=0,l[7]=0,l[11]=0,l[15]=1,this}equals(t){let e=this.elements,n=t.elements;for(let s=0;s<16;s++)if(e[s]!==n[s])return!1;return!0}fromArray(t,e=0){for(let n=0;n<16;n++)this.elements[n]=t[n+e];return this}toArray(t=[],e=0){let n=this.elements;return t[e]=n[0],t[e+1]=n[1],t[e+2]=n[2],t[e+3]=n[3],t[e+4]=n[4],t[e+5]=n[5],t[e+6]=n[6],t[e+7]=n[7],t[e+8]=n[8],t[e+9]=n[9],t[e+10]=n[10],t[e+11]=n[11],t[e+12]=n[12],t[e+13]=n[13],t[e+14]=n[14],t[e+15]=n[15],t}};Vo.prototype.isMatrix4=!0;var de=Vo,Us=new C,Qn=new de,Xf=new C(0,0,0),qf=new C(1,1,1),Xi=new C,La=new C,Un=new C,Xh=new de,qh=new sn,ri=class i{constructor(t=0,e=0,n=0,s=i.DEFAULT_ORDER){this.isEuler=!0,this._x=t,this._y=e,this._z=n,this._order=s}get x(){return this._x}set x(t){this._x=t,this._onChangeCallback()}get y(){return this._y}set y(t){this._y=t,this._onChangeCallback()}get z(){return this._z}set z(t){this._z=t,this._onChangeCallback()}get order(){return this._order}set order(t){this._order=t,this._onChangeCallback()}set(t,e,n,s=this._order){return this._x=t,this._y=e,this._z=n,this._order=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(t){return this._x=t._x,this._y=t._y,this._z=t._z,this._order=t._order,this._onChangeCallback(),this}setFromRotationMatrix(t,e=this._order,n=!0){let s=t.elements,r=s[0],a=s[4],o=s[8],c=s[1],l=s[5],u=s[9],d=s[2],h=s[6],f=s[10];switch(e){case"XYZ":this._y=Math.asin(le(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-u,f),this._z=Math.atan2(-a,r)):(this._x=Math.atan2(h,l),this._z=0);break;case"YXZ":this._x=Math.asin(-le(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(o,f),this._z=Math.atan2(c,l)):(this._y=Math.atan2(-d,r),this._z=0);break;case"ZXY":this._x=Math.asin(le(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(-d,f),this._z=Math.atan2(-a,l)):(this._y=0,this._z=Math.atan2(c,r));break;case"ZYX":this._y=Math.asin(-le(d,-1,1)),Math.abs(d)<.9999999?(this._x=Math.atan2(h,f),this._z=Math.atan2(c,r)):(this._x=0,this._z=Math.atan2(-a,l));break;case"YZX":this._z=Math.asin(le(c,-1,1)),Math.abs(c)<.9999999?(this._x=Math.atan2(-u,l),this._y=Math.atan2(-d,r)):(this._x=0,this._y=Math.atan2(o,f));break;case"XZY":this._z=Math.asin(-le(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(h,l),this._y=Math.atan2(o,r)):(this._x=Math.atan2(-u,f),this._y=0);break;default:ie("Euler: .setFromRotationMatrix() encountered an unknown order: "+e)}return this._order=e,n===!0&&this._onChangeCallback(),this}setFromQuaternion(t,e,n){return Xh.makeRotationFromQuaternion(t),this.setFromRotationMatrix(Xh,e,n)}setFromVector3(t,e=this._order){return this.set(t.x,t.y,t.z,e)}reorder(t){return qh.setFromEuler(this),this.setFromQuaternion(qh,t)}equals(t){return t._x===this._x&&t._y===this._y&&t._z===this._z&&t._order===this._order}fromArray(t){return this._x=t[0],this._y=t[1],this._z=t[2],t[3]!==void 0&&(this._order=t[3]),this._onChangeCallback(),this}toArray(t=[],e=0){return t[e]=this._x,t[e+1]=this._y,t[e+2]=this._z,t[e+3]=this._order,t}_onChange(t){return this._onChangeCallback=t,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}};ri.DEFAULT_ORDER="XYZ";var kr=class{constructor(){this.mask=1}set(t){this.mask=(1<<t|0)>>>0}enable(t){this.mask|=1<<t|0}enableAll(){this.mask=-1}toggle(t){this.mask^=1<<t|0}disable(t){this.mask&=~(1<<t|0)}disableAll(){this.mask=0}test(t){return(this.mask&t.mask)!==0}isEnabled(t){return(this.mask&(1<<t|0))!==0}},Yf=0,Yh=new C,Ns=new sn,Pi=new de,Da=new C,br=new C,jf=new C,Zf=new sn,jh=new C(1,0,0),Zh=new C(0,1,0),$h=new C(0,0,1),Jh={type:"added"},$f={type:"removed"},Fs={type:"childadded",child:null},tl={type:"childremoved",child:null},rn=class i extends mi{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Yf++}),this.uuid=fi(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=i.DEFAULT_UP.clone();let t=new C,e=new ri,n=new sn,s=new C(1,1,1);function r(){n.setFromEuler(e,!1)}function a(){e.setFromQuaternion(n,void 0,!1)}e._onChange(r),n._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:t},rotation:{configurable:!0,enumerable:!0,value:e},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:s},modelViewMatrix:{value:new de},normalMatrix:{value:new he}}),this.matrix=new de,this.matrixWorld=new de,this.matrixAutoUpdate=i.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=i.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new kr,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(t){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(t),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(t){return this.quaternion.premultiply(t),this}setRotationFromAxisAngle(t,e){this.quaternion.setFromAxisAngle(t,e)}setRotationFromEuler(t){this.quaternion.setFromEuler(t,!0)}setRotationFromMatrix(t){this.quaternion.setFromRotationMatrix(t)}setRotationFromQuaternion(t){this.quaternion.copy(t)}rotateOnAxis(t,e){return Ns.setFromAxisAngle(t,e),this.quaternion.multiply(Ns),this}rotateOnWorldAxis(t,e){return Ns.setFromAxisAngle(t,e),this.quaternion.premultiply(Ns),this}rotateX(t){return this.rotateOnAxis(jh,t)}rotateY(t){return this.rotateOnAxis(Zh,t)}rotateZ(t){return this.rotateOnAxis($h,t)}translateOnAxis(t,e){return Yh.copy(t).applyQuaternion(this.quaternion),this.position.add(Yh.multiplyScalar(e)),this}translateX(t){return this.translateOnAxis(jh,t)}translateY(t){return this.translateOnAxis(Zh,t)}translateZ(t){return this.translateOnAxis($h,t)}localToWorld(t){return this.updateWorldMatrix(!0,!1),t.applyMatrix4(this.matrixWorld)}worldToLocal(t){return this.updateWorldMatrix(!0,!1),t.applyMatrix4(Pi.copy(this.matrixWorld).invert())}lookAt(t,e,n){t.isVector3?Da.copy(t):Da.set(t,e,n);let s=this.parent;this.updateWorldMatrix(!0,!1),br.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?Pi.lookAt(br,Da,this.up):Pi.lookAt(Da,br,this.up),this.quaternion.setFromRotationMatrix(Pi),s&&(Pi.extractRotation(s.matrixWorld),Ns.setFromRotationMatrix(Pi),this.quaternion.premultiply(Ns.invert()))}add(t){if(arguments.length>1){for(let e=0;e<arguments.length;e++)this.add(arguments[e]);return this}return t===this?(ae("Object3D.add: object can't be added as a child of itself.",t),this):(t&&t.isObject3D?(t.removeFromParent(),t.parent=this,this.children.push(t),t.dispatchEvent(Jh),Fs.child=t,this.dispatchEvent(Fs),Fs.child=null):ae("Object3D.add: object not an instance of THREE.Object3D.",t),this)}remove(t){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let e=this.children.indexOf(t);return e!==-1&&(t.parent=null,this.children.splice(e,1),t.dispatchEvent($f),tl.child=t,this.dispatchEvent(tl),tl.child=null),this}removeFromParent(){let t=this.parent;return t!==null&&t.remove(this),this}clear(){return this.remove(...this.children)}attach(t){return this.updateWorldMatrix(!0,!1),Pi.copy(this.matrixWorld).invert(),t.parent!==null&&(t.parent.updateWorldMatrix(!0,!1),Pi.multiply(t.parent.matrixWorld)),t.applyMatrix4(Pi),t.removeFromParent(),t.parent=this,this.children.push(t),t.updateWorldMatrix(!1,!0),t.dispatchEvent(Jh),Fs.child=t,this.dispatchEvent(Fs),Fs.child=null,this}getObjectById(t){return this.getObjectByProperty("id",t)}getObjectByName(t){return this.getObjectByProperty("name",t)}getObjectByProperty(t,e){if(this[t]===e)return this;for(let n=0,s=this.children.length;n<s;n++){let a=this.children[n].getObjectByProperty(t,e);if(a!==void 0)return a}}getObjectsByProperty(t,e,n=[]){this[t]===e&&n.push(this);let s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].getObjectsByProperty(t,e,n);return n}getWorldPosition(t){return this.updateWorldMatrix(!0,!1),t.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(t){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(br,t,jf),t}getWorldScale(t){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(br,Zf,t),t}getWorldDirection(t){this.updateWorldMatrix(!0,!1);let e=this.matrixWorld.elements;return t.set(e[8],e[9],e[10]).normalize()}raycast(){}intersectsFrustum(){}traverse(t){t(this);let e=this.children;for(let n=0,s=e.length;n<s;n++)e[n].traverse(t)}traverseVisible(t){if(this.visible===!1)return;t(this);let e=this.children;for(let n=0,s=e.length;n<s;n++)e[n].traverseVisible(t)}traverseAncestors(t){let e=this.parent;e!==null&&(t(e),e.traverseAncestors(t))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);let t=this.pivot;if(t!==null){let e=t.x,n=t.y,s=t.z,r=this.matrix.elements;r[12]+=e-r[0]*e-r[4]*n-r[8]*s,r[13]+=n-r[1]*e-r[5]*n-r[9]*s,r[14]+=s-r[2]*e-r[6]*n-r[10]*s}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(t){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||t)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,t=!0);let e=this.children;for(let n=0,s=e.length;n<s;n++)e[n].updateMatrixWorld(t)}updateWorldMatrix(t,e,n=!1){let s=this.parent;if(t===!0&&s!==null&&s.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||n)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,n=!0),e===!0){let r=this.children;for(let a=0,o=r.length;a<o;a++)r[a].updateWorldMatrix(!1,!0,n)}}toJSON(t){let e=t===void 0||typeof t=="string",n={};e&&(t={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});let s={};s.uuid=this.uuid,s.type=this.type,s.name=this.name,s.castShadow=this.castShadow,s.receiveShadow=this.receiveShadow,s.visible=this.visible,s.frustumCulled=this.frustumCulled,s.renderOrder=this.renderOrder,s.static=this.static,s.matrixAutoUpdate=this.matrixAutoUpdate,Object.keys(this.userData).length>0&&(s.userData=this.userData),s.layers=this.layers.mask,s.matrix=this.matrix.toArray(),s.up=this.up.toArray(),this.pivot!==null&&(s.pivot=this.pivot.toArray()),this.morphTargetDictionary!==void 0&&(s.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(s.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(s.type="InstancedMesh",s.count=this.count,s.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(s.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(s.type="BatchedMesh",s.perObjectFrustumCulled=this.perObjectFrustumCulled,s.sortObjects=this.sortObjects,s.drawRanges=this._drawRanges,s.reservedRanges=this._reservedRanges,s.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),s.instanceInfo=this._instanceInfo.map(o=>({...o})),s.availableInstanceIds=this._availableInstanceIds.slice(),s.availableGeometryIds=this._availableGeometryIds.slice(),s.nextIndexStart=this._nextIndexStart,s.nextVertexStart=this._nextVertexStart,s.geometryCount=this._geometryCount,s.maxInstanceCount=this._maxInstanceCount,s.maxVertexCount=this._maxVertexCount,s.maxIndexCount=this._maxIndexCount,s.geometryInitialized=this._geometryInitialized,s.matricesTexture=this._matricesTexture.toJSON(t),s.indirectTexture=this._indirectTexture.toJSON(t),this._colorsTexture!==null&&(s.colorsTexture=this._colorsTexture.toJSON(t)),this.boundingSphere!==null&&(s.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(s.boundingBox=this.boundingBox.toJSON()));function r(o,c){return o[c.uuid]===void 0&&(o[c.uuid]=c.toJSON(t)),c.uuid}if(this.isScene)this.background&&(this.background.isColor?s.background=this.background.toJSON():this.background.isTexture&&(s.background=this.background.toJSON(t).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(s.environment=this.environment.toJSON(t).uuid);else if(this.isMesh||this.isLine||this.isPoints){s.geometry=r(t.geometries,this.geometry);let o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){let c=o.shapes;if(Array.isArray(c))for(let l=0,u=c.length;l<u;l++){let d=c[l];r(t.shapes,d)}else r(t.shapes,c)}}if(this.isSkinnedMesh&&(s.bindMode=this.bindMode,s.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(r(t.skeletons,this.skeleton),s.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){let o=[];for(let c=0,l=this.material.length;c<l;c++)o.push(r(t.materials,this.material[c]));s.material=o}else s.material=r(t.materials,this.material);if(this.children.length>0){s.children=[];for(let o=0;o<this.children.length;o++)s.children.push(this.children[o].toJSON(t).object)}if(this.animations.length>0){s.animations=[];for(let o=0;o<this.animations.length;o++){let c=this.animations[o];s.animations.push(r(t.animations,c))}}if(e){let o=a(t.geometries),c=a(t.materials),l=a(t.textures),u=a(t.images),d=a(t.shapes),h=a(t.skeletons),f=a(t.animations),g=a(t.nodes);o.length>0&&(n.geometries=o),c.length>0&&(n.materials=c),l.length>0&&(n.textures=l),u.length>0&&(n.images=u),d.length>0&&(n.shapes=d),h.length>0&&(n.skeletons=h),f.length>0&&(n.animations=f),g.length>0&&(n.nodes=g)}return n.object=s,n;function a(o){let c=[];for(let l in o){let u=o[l];delete u.metadata,c.push(u)}return c}}clone(t){return new this.constructor().copy(this,t)}copy(t,e=!0){if(this.name=t.name,this.up.copy(t.up),this.position.copy(t.position),this.rotation.order=t.rotation.order,this.quaternion.copy(t.quaternion),this.scale.copy(t.scale),this.pivot=t.pivot!==null?t.pivot.clone():null,this.matrix.copy(t.matrix),this.matrixWorld.copy(t.matrixWorld),this.matrixAutoUpdate=t.matrixAutoUpdate,this.matrixWorldAutoUpdate=t.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=t.matrixWorldNeedsUpdate,this.layers.mask=t.layers.mask,this.visible=t.visible,this.castShadow=t.castShadow,this.receiveShadow=t.receiveShadow,this.frustumCulled=t.frustumCulled,this.renderOrder=t.renderOrder,this.static=t.static,this.animations=t.animations.slice(),this.userData=JSON.parse(JSON.stringify(t.userData)),e===!0)for(let n=0;n<t.children.length;n++){let s=t.children[n];this.add(s.clone())}return this}dispose(){this.dispatchEvent({type:"dispose"})}};rn.DEFAULT_UP=new C(0,1,0);rn.DEFAULT_MATRIX_AUTO_UPDATE=!0;rn.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var oe=class extends rn{constructor(){super(),this.isGroup=!0,this.type="Group"}},Jf={type:"move"},nr=class{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new oe,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new oe,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new C,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new C),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new oe,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new C,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new C,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(t){return this._targetRay!==null&&this._targetRay.dispatchEvent(t),this._grip!==null&&this._grip.dispatchEvent(t),this._hand!==null&&this._hand.dispatchEvent(t),this}connect(t){if(t&&t.hand){let e=this._hand;if(e)for(let n of t.hand.values())this._getHandJoint(e,n)}return this.dispatchEvent({type:"connected",data:t}),this}disconnect(t){return this.dispatchEvent({type:"disconnected",data:t}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(t,e,n){let s=null,r=null,a=null,o=this._targetRay,c=this._grip,l=this._hand;if(t&&e.session.visibilityState!=="visible-blurred"){if(l&&t.hand){a=!0;for(let x of t.hand.values()){let p=e.getJointPose(x,n),m=this._getHandJoint(l,x);p!==null&&(m.matrix.fromArray(p.transform.matrix),m.matrix.decompose(m.position,m.rotation,m.scale),m.matrixWorldNeedsUpdate=!0,m.jointRadius=p.radius),m.visible=p!==null}let u=l.joints["index-finger-tip"],d=l.joints["thumb-tip"],h=u.position.distanceTo(d.position),f=.02,g=.005;l.inputState.pinching&&h>f+g?(l.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:t.handedness,target:this})):!l.inputState.pinching&&h<=f-g&&(l.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:t.handedness,target:this}))}else c!==null&&t.gripSpace&&(r=e.getPose(t.gripSpace,n),r!==null&&(c.matrix.fromArray(r.transform.matrix),c.matrix.decompose(c.position,c.rotation,c.scale),c.matrixWorldNeedsUpdate=!0,r.linearVelocity?(c.hasLinearVelocity=!0,c.linearVelocity.copy(r.linearVelocity)):c.hasLinearVelocity=!1,r.angularVelocity?(c.hasAngularVelocity=!0,c.angularVelocity.copy(r.angularVelocity)):c.hasAngularVelocity=!1,c.eventsEnabled&&c.dispatchEvent({type:"gripUpdated",data:t,target:this})));o!==null&&(s=e.getPose(t.targetRaySpace,n),s===null&&r!==null&&(s=r),s!==null&&(o.matrix.fromArray(s.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,s.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(s.linearVelocity)):o.hasLinearVelocity=!1,s.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(s.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(Jf)))}return o!==null&&(o.visible=s!==null),c!==null&&(c.visible=r!==null),l!==null&&(l.visible=a!==null),this}_getHandJoint(t,e){if(t.joints[e.jointName]===void 0){let n=new oe;n.matrixAutoUpdate=!1,n.visible=!1,t.joints[e.jointName]=n,t.add(n)}return t.joints[e.jointName]}},id={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},qi={h:0,s:0,l:0},Ua={h:0,s:0,l:0};function el(i,t,e){return e<0&&(e+=1),e>1&&(e-=1),e<1/6?i+(t-i)*6*e:e<1/2?t:e<2/3?i+(t-i)*6*(2/3-e):i}var Wt=class{constructor(t,e,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(t,e,n)}set(t,e,n){if(e===void 0&&n===void 0){let s=t;s&&s.isColor?this.copy(s):typeof s=="number"?this.setHex(s):typeof s=="string"&&this.setStyle(s)}else this.setRGB(t,e,n);return this}setScalar(t){return this.r=t,this.g=t,this.b=t,this}setHex(t,e=bn){return t=Math.floor(t),this.r=(t>>16&255)/255,this.g=(t>>8&255)/255,this.b=(t&255)/255,Me.colorSpaceToWorking(this,e),this}setRGB(t,e,n,s=Me.workingColorSpace){return this.r=t,this.g=e,this.b=n,Me.colorSpaceToWorking(this,s),this}setHSL(t,e,n,s=Me.workingColorSpace){if(t=eh(t,1),e=le(e,0,1),n=le(n,0,1),e===0)this.r=this.g=this.b=n;else{let r=n<=.5?n*(1+e):n+e-n*e,a=2*n-r;this.r=el(a,r,t+1/3),this.g=el(a,r,t),this.b=el(a,r,t-1/3)}return Me.colorSpaceToWorking(this,s),this}setStyle(t,e=bn){function n(r){r!==void 0&&parseFloat(r)<1&&ie("Color: Alpha component of "+t+" will be ignored.")}let s;if(s=/^(\w+)\(([^\)]*)\)/.exec(t)){let r,a=s[1],o=s[2];switch(a){case"rgb":case"rgba":if(r=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(255,parseInt(r[1],10))/255,Math.min(255,parseInt(r[2],10))/255,Math.min(255,parseInt(r[3],10))/255,e);if(r=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(100,parseInt(r[1],10))/100,Math.min(100,parseInt(r[2],10))/100,Math.min(100,parseInt(r[3],10))/100,e);break;case"hsl":case"hsla":if(r=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setHSL(parseFloat(r[1])/360,parseFloat(r[2])/100,parseFloat(r[3])/100,e);break;default:ie("Color: Unknown color model "+t)}}else if(s=/^\#([A-Fa-f\d]+)$/.exec(t)){let r=s[1],a=r.length;if(a===3)return this.setRGB(parseInt(r.charAt(0),16)/15,parseInt(r.charAt(1),16)/15,parseInt(r.charAt(2),16)/15,e);if(a===6)return this.setHex(parseInt(r,16),e);ie("Color: Invalid hex color "+t)}else if(t&&t.length>0)return this.setColorName(t,e);return this}setColorName(t,e=bn){let n=id[t.toLowerCase()];return n!==void 0?this.setHex(n,e):ie("Color: Unknown color "+t),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(t){return this.r=t.r,this.g=t.g,this.b=t.b,this}copySRGBToLinear(t){return this.r=Fi(t.r),this.g=Fi(t.g),this.b=Fi(t.b),this}copyLinearToSRGB(t){return this.r=Zs(t.r),this.g=Zs(t.g),this.b=Zs(t.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(t=bn){return Me.workingToColorSpace(gn.copy(this),t),Math.round(le(gn.r*255,0,255))*65536+Math.round(le(gn.g*255,0,255))*256+Math.round(le(gn.b*255,0,255))}getHexString(t=bn){return("000000"+this.getHex(t).toString(16)).slice(-6)}getHSL(t,e=Me.workingColorSpace){Me.workingToColorSpace(gn.copy(this),e);let n=gn.r,s=gn.g,r=gn.b,a=Math.max(n,s,r),o=Math.min(n,s,r),c,l,u=(o+a)/2;if(o===a)c=0,l=0;else{let d=a-o;switch(l=u<=.5?d/(a+o):d/(2-a-o),a){case n:c=(s-r)/d+(s<r?6:0);break;case s:c=(r-n)/d+2;break;case r:c=(n-s)/d+4;break}c/=6}return t.h=c,t.s=l,t.l=u,t}getRGB(t,e=Me.workingColorSpace){return Me.workingToColorSpace(gn.copy(this),e),t.r=gn.r,t.g=gn.g,t.b=gn.b,t}getStyle(t=bn){Me.workingToColorSpace(gn.copy(this),t);let e=gn.r,n=gn.g,s=gn.b;return t!==bn?`color(${t} ${e.toFixed(3)} ${n.toFixed(3)} ${s.toFixed(3)})`:`rgb(${Math.round(e*255)},${Math.round(n*255)},${Math.round(s*255)})`}offsetHSL(t,e,n){return this.getHSL(qi),this.setHSL(qi.h+t,qi.s+e,qi.l+n)}add(t){return this.r+=t.r,this.g+=t.g,this.b+=t.b,this}addColors(t,e){return this.r=t.r+e.r,this.g=t.g+e.g,this.b=t.b+e.b,this}addScalar(t){return this.r+=t,this.g+=t,this.b+=t,this}sub(t){return this.r=Math.max(0,this.r-t.r),this.g=Math.max(0,this.g-t.g),this.b=Math.max(0,this.b-t.b),this}multiply(t){return this.r*=t.r,this.g*=t.g,this.b*=t.b,this}multiplyScalar(t){return this.r*=t,this.g*=t,this.b*=t,this}lerp(t,e){return this.r+=(t.r-this.r)*e,this.g+=(t.g-this.g)*e,this.b+=(t.b-this.b)*e,this}lerpColors(t,e,n){return this.r=t.r+(e.r-t.r)*n,this.g=t.g+(e.g-t.g)*n,this.b=t.b+(e.b-t.b)*n,this}lerpHSL(t,e){this.getHSL(qi),t.getHSL(Ua);let n=Ir(qi.h,Ua.h,e),s=Ir(qi.s,Ua.s,e),r=Ir(qi.l,Ua.l,e);return this.setHSL(n,s,r),this}setFromVector3(t){return this.r=t.x,this.g=t.y,this.b=t.z,this}applyMatrix3(t){let e=this.r,n=this.g,s=this.b,r=t.elements;return this.r=r[0]*e+r[3]*n+r[6]*s,this.g=r[1]*e+r[4]*n+r[7]*s,this.b=r[2]*e+r[5]*n+r[8]*s,this}equals(t){return t.r===this.r&&t.g===this.g&&t.b===this.b}fromArray(t,e=0){return this.r=t[e],this.g=t[e+1],this.b=t[e+2],this}toArray(t=[],e=0){return t[e]=this.r,t[e+1]=this.g,t[e+2]=this.b,t}fromBufferAttribute(t,e){return this.r=t.getX(e),this.g=t.getY(e),this.b=t.getZ(e),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}},gn=new Wt;Wt.NAMES=id;var Hr=class i{constructor(t,e=1,n=1e3){this.isFog=!0,this.name="",this.color=new Wt(t),this.near=e,this.far=n}clone(){return new i(this.color,this.near,this.far)}toJSON(){return{type:"Fog",name:this.name,color:this.color.getHex(),near:this.near,far:this.far}}},zi=class extends rn{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new ri,this.environmentIntensity=1,this.environmentRotation=new ri,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(t,e){return super.copy(t,e),t.background!==null&&(this.background=t.background.clone()),t.environment!==null&&(this.environment=t.environment.clone()),t.fog!==null&&(this.fog=t.fog.clone()),this.backgroundBlurriness=t.backgroundBlurriness,this.backgroundIntensity=t.backgroundIntensity,this.backgroundRotation.copy(t.backgroundRotation),this.environmentIntensity=t.environmentIntensity,this.environmentRotation.copy(t.environmentRotation),t.overrideMaterial!==null&&(this.overrideMaterial=t.overrideMaterial.clone()),this.matrixAutoUpdate=t.matrixAutoUpdate,this}toJSON(t){let e=super.toJSON(t);return this.fog!==null&&(e.object.fog=this.fog.toJSON()),e.object.backgroundBlurriness=this.backgroundBlurriness,e.object.backgroundIntensity=this.backgroundIntensity,e.object.backgroundRotation=this.backgroundRotation.toArray(),e.object.environmentIntensity=this.environmentIntensity,e.object.environmentRotation=this.environmentRotation.toArray(),e}},ti=new C,Ii=new C,nl=new C,Li=new C,zs=new C,Os=new C,Kh=new C,il=new C,sl=new C,rl=new C,al=new xe,ol=new xe,cl=new xe,$i=class i{constructor(t=new C,e=new C,n=new C){this.a=t,this.b=e,this.c=n}static getNormal(t,e,n,s){s.subVectors(n,e),ti.subVectors(t,e),s.cross(ti);let r=s.lengthSq();return r>0?s.multiplyScalar(1/Math.sqrt(r)):s.set(0,0,0)}static getBarycoord(t,e,n,s,r){ti.subVectors(s,e),Ii.subVectors(n,e),nl.subVectors(t,e);let a=ti.dot(ti),o=ti.dot(Ii),c=ti.dot(nl),l=Ii.dot(Ii),u=Ii.dot(nl),d=a*l-o*o;if(d===0)return r.set(0,0,0),null;let h=1/d,f=(l*c-o*u)*h,g=(a*u-o*c)*h;return r.set(1-f-g,g,f)}static containsPoint(t,e,n,s){return this.getBarycoord(t,e,n,s,Li)===null?!1:Li.x>=0&&Li.y>=0&&Li.x+Li.y<=1}static getInterpolation(t,e,n,s,r,a,o,c){return this.getBarycoord(t,e,n,s,Li)===null?(c.x=0,c.y=0,"z"in c&&(c.z=0),"w"in c&&(c.w=0),null):(c.setScalar(0),c.addScaledVector(r,Li.x),c.addScaledVector(a,Li.y),c.addScaledVector(o,Li.z),c)}static getInterpolatedAttribute(t,e,n,s,r,a){return al.setScalar(0),ol.setScalar(0),cl.setScalar(0),al.fromBufferAttribute(t,e),ol.fromBufferAttribute(t,n),cl.fromBufferAttribute(t,s),a.setScalar(0),a.addScaledVector(al,r.x),a.addScaledVector(ol,r.y),a.addScaledVector(cl,r.z),a}static isFrontFacing(t,e,n,s){return ti.subVectors(n,e),Ii.subVectors(t,e),ti.cross(Ii).dot(s)<0}set(t,e,n){return this.a.copy(t),this.b.copy(e),this.c.copy(n),this}setFromPointsAndIndices(t,e,n,s){return this.a.copy(t[e]),this.b.copy(t[n]),this.c.copy(t[s]),this}setFromAttributeAndIndices(t,e,n,s){return this.a.fromBufferAttribute(t,e),this.b.fromBufferAttribute(t,n),this.c.fromBufferAttribute(t,s),this}clone(){return new this.constructor().copy(this)}copy(t){return this.a.copy(t.a),this.b.copy(t.b),this.c.copy(t.c),this}getArea(){return ti.subVectors(this.c,this.b),Ii.subVectors(this.a,this.b),ti.cross(Ii).length()*.5}getMidpoint(t){return t.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(t){return i.getNormal(this.a,this.b,this.c,t)}getPlane(t){return t.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(t,e){return i.getBarycoord(t,this.a,this.b,this.c,e)}getInterpolation(t,e,n,s,r){return i.getInterpolation(t,this.a,this.b,this.c,e,n,s,r)}containsPoint(t){return i.containsPoint(t,this.a,this.b,this.c)}isFrontFacing(t){return i.isFrontFacing(this.a,this.b,this.c,t)}intersectsBox(t){return t.intersectsTriangle(this)}closestPointToPoint(t,e){let n=this.a,s=this.b,r=this.c,a,o;zs.subVectors(s,n),Os.subVectors(r,n),il.subVectors(t,n);let c=zs.dot(il),l=Os.dot(il);if(c<=0&&l<=0)return e.copy(n);sl.subVectors(t,s);let u=zs.dot(sl),d=Os.dot(sl);if(u>=0&&d<=u)return e.copy(s);let h=c*d-u*l;if(h<=0&&c>=0&&u<=0)return a=c/(c-u),e.copy(n).addScaledVector(zs,a);rl.subVectors(t,r);let f=zs.dot(rl),g=Os.dot(rl);if(g>=0&&f<=g)return e.copy(r);let x=f*l-c*g;if(x<=0&&l>=0&&g<=0)return o=l/(l-g),e.copy(n).addScaledVector(Os,o);let p=u*g-f*d;if(p<=0&&d-u>=0&&f-g>=0)return Kh.subVectors(r,s),o=(d-u)/(d-u+(f-g)),e.copy(s).addScaledVector(Kh,o);let m=1/(p+x+h);return a=x*m,o=h*m,e.copy(n).addScaledVector(zs,a).addScaledVector(Os,o)}equals(t){return t.a.equals(this.a)&&t.b.equals(this.b)&&t.c.equals(this.c)}},an=class{constructor(t=new C(1/0,1/0,1/0),e=new C(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=t,this.max=e}set(t,e){return this.min.copy(t),this.max.copy(e),this}setFromArray(t){this.makeEmpty();for(let e=0,n=t.length;e<n;e+=3)this.expandByPoint(ei.fromArray(t,e));return this}setFromBufferAttribute(t){this.makeEmpty();for(let e=0,n=t.count;e<n;e++)this.expandByPoint(ei.fromBufferAttribute(t,e));return this}setFromPoints(t){this.makeEmpty();for(let e=0,n=t.length;e<n;e++)this.expandByPoint(t[e]);return this}setFromCenterAndSize(t,e){let n=ei.copy(e).multiplyScalar(.5);return this.min.copy(t).sub(n),this.max.copy(t).add(n),this}setFromObject(t,e=!1){return this.makeEmpty(),this.expandByObject(t,e)}clone(){return new this.constructor().copy(this)}copy(t){return this.min.copy(t.min),this.max.copy(t.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(t){return this.isEmpty()?t.set(0,0,0):t.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(t){return this.isEmpty()?t.set(0,0,0):t.subVectors(this.max,this.min)}expandByPoint(t){return this.min.min(t),this.max.max(t),this}expandByVector(t){return this.min.sub(t),this.max.add(t),this}expandByScalar(t){return this.min.addScalar(-t),this.max.addScalar(t),this}expandByObject(t,e=!1){t.updateWorldMatrix(!1,!1);let n=t.geometry;if(n!==void 0){let r=n.getAttribute("position");if(e===!0&&r!==void 0&&t.isInstancedMesh!==!0)for(let a=0,o=r.count;a<o;a++)t.isMesh===!0?t.getVertexPosition(a,ei):ei.fromBufferAttribute(r,a),ei.applyMatrix4(t.matrixWorld),this.expandByPoint(ei);else t.boundingBox!==void 0?(t.boundingBox===null&&t.computeBoundingBox(),Na.copy(t.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),Na.copy(n.boundingBox)),Na.applyMatrix4(t.matrixWorld),this.union(Na)}let s=t.children;for(let r=0,a=s.length;r<a;r++)this.expandByObject(s[r],e);return this}containsPoint(t){return t.x>=this.min.x&&t.x<=this.max.x&&t.y>=this.min.y&&t.y<=this.max.y&&t.z>=this.min.z&&t.z<=this.max.z}containsBox(t){return this.min.x<=t.min.x&&t.max.x<=this.max.x&&this.min.y<=t.min.y&&t.max.y<=this.max.y&&this.min.z<=t.min.z&&t.max.z<=this.max.z}getParameter(t,e){return e.set((t.x-this.min.x)/(this.max.x-this.min.x),(t.y-this.min.y)/(this.max.y-this.min.y),(t.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(t){return t.max.x>=this.min.x&&t.min.x<=this.max.x&&t.max.y>=this.min.y&&t.min.y<=this.max.y&&t.max.z>=this.min.z&&t.min.z<=this.max.z}intersectsSphere(t){return this.clampPoint(t.center,ei),ei.distanceToSquared(t.center)<=t.radius*t.radius}intersectsPlane(t){let e,n;return t.normal.x>0?(e=t.normal.x*this.min.x,n=t.normal.x*this.max.x):(e=t.normal.x*this.max.x,n=t.normal.x*this.min.x),t.normal.y>0?(e+=t.normal.y*this.min.y,n+=t.normal.y*this.max.y):(e+=t.normal.y*this.max.y,n+=t.normal.y*this.min.y),t.normal.z>0?(e+=t.normal.z*this.min.z,n+=t.normal.z*this.max.z):(e+=t.normal.z*this.max.z,n+=t.normal.z*this.min.z),e<=-t.constant&&n>=-t.constant}intersectsTriangle(t){if(this.isEmpty())return!1;this.getCenter(Er),Fa.subVectors(this.max,Er),Bs.subVectors(t.a,Er),ks.subVectors(t.b,Er),Hs.subVectors(t.c,Er),Yi.subVectors(ks,Bs),ji.subVectors(Hs,ks),ps.subVectors(Bs,Hs);let e=[0,-Yi.z,Yi.y,0,-ji.z,ji.y,0,-ps.z,ps.y,Yi.z,0,-Yi.x,ji.z,0,-ji.x,ps.z,0,-ps.x,-Yi.y,Yi.x,0,-ji.y,ji.x,0,-ps.y,ps.x,0];return!ll(e,Bs,ks,Hs,Fa)||(e=[1,0,0,0,1,0,0,0,1],!ll(e,Bs,ks,Hs,Fa))?!1:(za.crossVectors(Yi,ji),e=[za.x,za.y,za.z],ll(e,Bs,ks,Hs,Fa))}clampPoint(t,e){return e.copy(t).clamp(this.min,this.max)}distanceToPoint(t){return this.clampPoint(t,ei).distanceTo(t)}getBoundingSphere(t){return this.isEmpty()?t.makeEmpty():(this.getCenter(t.center),t.radius=this.getSize(ei).length()*.5),t}intersect(t){return this.min.max(t.min),this.max.min(t.max),this.isEmpty()&&this.makeEmpty(),this}union(t){return this.min.min(t.min),this.max.max(t.max),this}applyMatrix4(t){return this.isEmpty()?this:(Di[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(t),Di[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(t),Di[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(t),Di[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(t),Di[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(t),Di[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(t),Di[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(t),Di[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(t),this.setFromPoints(Di),this)}translate(t){return this.min.add(t),this.max.add(t),this}equals(t){return t.min.equals(this.min)&&t.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(t){return this.min.fromArray(t.min),this.max.fromArray(t.max),this}},Di=[new C,new C,new C,new C,new C,new C,new C,new C],ei=new C,Na=new an,Bs=new C,ks=new C,Hs=new C,Yi=new C,ji=new C,ps=new C,Er=new C,Fa=new C,za=new C,ms=new C;function ll(i,t,e,n,s){for(let r=0,a=i.length-3;r<=a;r+=3){ms.fromArray(i,r);let o=s.x*Math.abs(ms.x)+s.y*Math.abs(ms.y)+s.z*Math.abs(ms.z),c=t.dot(ms),l=e.dot(ms),u=n.dot(ms);if(Math.max(-Math.max(c,l,u),Math.min(c,l,u))>o)return!1}return!0}var Ni=Kf();function Kf(){let i=new ArrayBuffer(4),t=new Float32Array(i),e=new Uint32Array(i),n=new Uint32Array(512),s=new Uint32Array(512);for(let c=0;c<256;++c){let l=c-127;l<-27?(n[c]=0,n[c|256]=32768,s[c]=24,s[c|256]=24):l<-14?(n[c]=1024>>-l-14,n[c|256]=1024>>-l-14|32768,s[c]=-l-1,s[c|256]=-l-1):l<=15?(n[c]=l+15<<10,n[c|256]=l+15<<10|32768,s[c]=13,s[c|256]=13):l<128?(n[c]=31744,n[c|256]=64512,s[c]=24,s[c|256]=24):(n[c]=31744,n[c|256]=64512,s[c]=13,s[c|256]=13)}let r=new Uint32Array(2048),a=new Uint32Array(64),o=new Uint32Array(64);for(let c=1;c<1024;++c){let l=c<<13,u=0;for(;(l&8388608)===0;)l<<=1,u-=8388608;l&=-8388609,u+=947912704,r[c]=l|u}for(let c=1024;c<2048;++c)r[c]=939524096+(c-1024<<13);for(let c=1;c<31;++c)a[c]=c<<23;a[31]=1199570944,a[32]=2147483648;for(let c=33;c<63;++c)a[c]=2147483648+(c-32<<23);a[63]=3347054592;for(let c=1;c<64;++c)c!==32&&(o[c]=1024);return{floatView:t,uint32View:e,baseTable:n,shiftTable:s,mantissaTable:r,exponentTable:a,offsetTable:o}}function Qf(i){Math.abs(i)>65504&&ie("DataUtils.toHalfFloat(): Value out of range."),i=le(i,-65504,65504),Ni.floatView[0]=i;let t=Ni.uint32View[0],e=t>>23&511;return Ni.baseTable[e]+((t&8388607)>>Ni.shiftTable[e])}function tp(i){let t=i>>10;return Ni.uint32View[0]=Ni.mantissaTable[Ni.offsetTable[t]+(i&1023)]+Ni.exponentTable[t],Ni.floatView[0]}var ir=class{static toHalfFloat(t){return Qf(t)}static fromHalfFloat(t){return tp(t)}},$e=new C,Oa=new vt,ep=0,Ue=class extends mi{constructor(t,e,n=!1){if(super(),Array.isArray(t))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:ep++}),this.name="",this.array=t,this.itemSize=e,this.count=t!==void 0?t.length/e:0,this.normalized=n,this.usage=Ql,this.updateRanges=[],this.gpuType=qn,this.version=0}onUploadCallback(){}set needsUpdate(t){t===!0&&this.version++}setUsage(t){return this.usage=t,this}addUpdateRange(t,e){this.updateRanges.push({start:t,count:e})}clearUpdateRanges(){this.updateRanges.length=0}copy(t){return this.name=t.name,this.array=new t.array.constructor(t.array),this.itemSize=t.itemSize,this.count=t.count,this.normalized=t.normalized,this.usage=t.usage,this.gpuType=t.gpuType,this}copyAt(t,e,n){t*=this.itemSize,n*=e.itemSize;for(let s=0,r=this.itemSize;s<r;s++)this.array[t+s]=e.array[n+s];return this}copyArray(t){return this.array.set(t),this}applyMatrix3(t){if(this.itemSize===2)for(let e=0,n=this.count;e<n;e++)Oa.fromBufferAttribute(this,e),Oa.applyMatrix3(t),this.setXY(e,Oa.x,Oa.y);else if(this.itemSize===3)for(let e=0,n=this.count;e<n;e++)$e.fromBufferAttribute(this,e),$e.applyMatrix3(t),this.setXYZ(e,$e.x,$e.y,$e.z);return this}applyMatrix4(t){for(let e=0,n=this.count;e<n;e++)$e.fromBufferAttribute(this,e),$e.applyMatrix4(t),this.setXYZ(e,$e.x,$e.y,$e.z);return this}applyNormalMatrix(t){for(let e=0,n=this.count;e<n;e++)$e.fromBufferAttribute(this,e),$e.applyNormalMatrix(t),this.setXYZ(e,$e.x,$e.y,$e.z);return this}transformDirection(t){for(let e=0,n=this.count;e<n;e++)$e.fromBufferAttribute(this,e),$e.transformDirection(t),this.setXYZ(e,$e.x,$e.y,$e.z);return this}set(t,e=0){return this.array.set(t,e),this}getComponent(t,e){let n=this.array[t*this.itemSize+e];return this.normalized&&(n=ii(n,this.array)),n}setComponent(t,e,n){return this.normalized&&(n=De(n,this.array)),this.array[t*this.itemSize+e]=n,this}getX(t){let e=this.array[t*this.itemSize];return this.normalized&&(e=ii(e,this.array)),e}setX(t,e){return this.normalized&&(e=De(e,this.array)),this.array[t*this.itemSize]=e,this}getY(t){let e=this.array[t*this.itemSize+1];return this.normalized&&(e=ii(e,this.array)),e}setY(t,e){return this.normalized&&(e=De(e,this.array)),this.array[t*this.itemSize+1]=e,this}getZ(t){let e=this.array[t*this.itemSize+2];return this.normalized&&(e=ii(e,this.array)),e}setZ(t,e){return this.normalized&&(e=De(e,this.array)),this.array[t*this.itemSize+2]=e,this}getW(t){let e=this.array[t*this.itemSize+3];return this.normalized&&(e=ii(e,this.array)),e}setW(t,e){return this.normalized&&(e=De(e,this.array)),this.array[t*this.itemSize+3]=e,this}setXY(t,e,n){return t*=this.itemSize,this.normalized&&(e=De(e,this.array),n=De(n,this.array)),this.array[t+0]=e,this.array[t+1]=n,this}setXYZ(t,e,n,s){return t*=this.itemSize,this.normalized&&(e=De(e,this.array),n=De(n,this.array),s=De(s,this.array)),this.array[t+0]=e,this.array[t+1]=n,this.array[t+2]=s,this}setXYZW(t,e,n,s,r){return t*=this.itemSize,this.normalized&&(e=De(e,this.array),n=De(n,this.array),s=De(s,this.array),r=De(r,this.array)),this.array[t+0]=e,this.array[t+1]=n,this.array[t+2]=s,this.array[t+3]=r,this}onUpload(t){return this.onUploadCallback=t,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let t={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return t.name=this.name,t.usage=this.usage,t.gpuType=this.gpuType,t}dispose(){this.dispatchEvent({type:"dispose"})}};var Vr=class extends Ue{constructor(t,e,n){super(new Uint16Array(t),e,n)}};var Gr=class extends Ue{constructor(t,e,n){super(new Uint32Array(t),e,n)}};var te=class extends Ue{constructor(t,e,n){super(new Float32Array(t),e,n)}},np=new an,wr=new C,hl=new C,wn=class{constructor(t=new C,e=-1){this.isSphere=!0,this.center=t,this.radius=e}set(t,e){return this.center.copy(t),this.radius=e,this}setFromPoints(t,e){let n=this.center;e!==void 0?n.copy(e):np.setFromPoints(t).getCenter(n);let s=0;for(let r=0,a=t.length;r<a;r++)s=Math.max(s,n.distanceToSquared(t[r]));return this.radius=Math.sqrt(s),this}copy(t){return this.center.copy(t.center),this.radius=t.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(t){return t.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(t){return t.distanceTo(this.center)-this.radius}intersectsSphere(t){let e=this.radius+t.radius;return t.center.distanceToSquared(this.center)<=e*e}intersectsBox(t){return t.intersectsSphere(this)}intersectsPlane(t){return Math.abs(t.distanceToPoint(this.center))<=this.radius}clampPoint(t,e){let n=this.center.distanceToSquared(t);return e.copy(t),n>this.radius*this.radius&&(e.sub(this.center).normalize(),e.multiplyScalar(this.radius).add(this.center)),e}getBoundingBox(t){return this.isEmpty()?(t.makeEmpty(),t):(t.set(this.center,this.center),t.expandByScalar(this.radius),t)}applyMatrix4(t){return this.center.applyMatrix4(t),this.radius=this.radius*t.getMaxScaleOnAxis(),this}translate(t){return this.center.add(t),this}expandByPoint(t){if(this.isEmpty())return this.center.copy(t),this.radius=0,this;wr.subVectors(t,this.center);let e=wr.lengthSq();if(e>this.radius*this.radius){let n=Math.sqrt(e),s=(n-this.radius)*.5;this.center.addScaledVector(wr,s/n),this.radius+=s}return this}union(t){return t.isEmpty()?this:this.isEmpty()?(this.copy(t),this):(this.center.equals(t.center)===!0?this.radius=Math.max(this.radius,t.radius):(hl.subVectors(t.center,this.center).setLength(t.radius),this.expandByPoint(wr.copy(t.center).add(hl)),this.expandByPoint(wr.copy(t.center).sub(hl))),this)}equals(t){return t.center.equals(this.center)&&t.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(t){return this.radius=t.radius,this.center.fromArray(t.center),this}},ip=0,Gn=new de,ul=new rn,Vs=new C,Nn=new an,Tr=new an,en=new C,ge=class i extends mi{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:ip++}),this.uuid=fi(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(t){return Array.isArray(t)?this.index=new(Ef(t)?Gr:Vr)(t,1):this.index=t,this}setIndirect(t,e=0){return this.indirect=t,this.indirectOffset=e,this}getIndirect(){return this.indirect}getAttribute(t){return this.attributes[t]}setAttribute(t,e){return this.attributes[t]=e,this}deleteAttribute(t){return delete this.attributes[t],this}hasAttribute(t){return this.attributes[t]!==void 0}addGroup(t,e,n=0){this.groups.push({start:t,count:e,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(t,e){this.drawRange.start=t,this.drawRange.count=e}applyMatrix4(t){let e=this.attributes.position;e!==void 0&&(e.applyMatrix4(t),e.needsUpdate=!0);let n=this.attributes.normal;if(n!==void 0){let r=new he().getNormalMatrix(t);n.applyNormalMatrix(r),n.needsUpdate=!0}let s=this.attributes.tangent;return s!==void 0&&(s.transformDirection(t),s.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this._transformed=!0,this}applyQuaternion(t){return Gn.makeRotationFromQuaternion(t),this.applyMatrix4(Gn),this}rotateX(t){return Gn.makeRotationX(t),this.applyMatrix4(Gn),this}rotateY(t){return Gn.makeRotationY(t),this.applyMatrix4(Gn),this}rotateZ(t){return Gn.makeRotationZ(t),this.applyMatrix4(Gn),this}translate(t,e,n){return Gn.makeTranslation(t,e,n),this.applyMatrix4(Gn),this}scale(t,e,n){return Gn.makeScale(t,e,n),this.applyMatrix4(Gn),this}lookAt(t){return ul.lookAt(t),ul.updateMatrix(),this.applyMatrix4(ul.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(Vs).negate(),this.translate(Vs.x,Vs.y,Vs.z),this}setFromPoints(t){let e=this.getAttribute("position");if(e===void 0){let n=[];for(let s=0,r=t.length;s<r;s++){let a=t[s];n.push(a.x,a.y,a.z||0)}this.setAttribute("position",new te(n,3))}else{let n=Math.min(t.length,e.count);for(let s=0;s<n;s++){let r=t[s];e.setXYZ(s,r.x,r.y,r.z||0)}t.length>e.count&&ie("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),e.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new an);let t=this.attributes.position,e=this.morphAttributes.position;if(t&&t.isGLBufferAttribute){ae("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new C(-1/0,-1/0,-1/0),new C(1/0,1/0,1/0));return}if(t!==void 0){if(this.boundingBox.setFromBufferAttribute(t),e)for(let n=0,s=e.length;n<s;n++){let r=e[n];Nn.setFromBufferAttribute(r),this.morphTargetsRelative?(en.addVectors(this.boundingBox.min,Nn.min),this.boundingBox.expandByPoint(en),en.addVectors(this.boundingBox.max,Nn.max),this.boundingBox.expandByPoint(en)):(this.boundingBox.expandByPoint(Nn.min),this.boundingBox.expandByPoint(Nn.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&ae('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new wn);let t=this.attributes.position,e=this.morphAttributes.position;if(t&&t.isGLBufferAttribute){ae("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new C,1/0);return}if(t){let n=this.boundingSphere.center;if(Nn.setFromBufferAttribute(t),e)for(let r=0,a=e.length;r<a;r++){let o=e[r];Tr.setFromBufferAttribute(o),this.morphTargetsRelative?(en.addVectors(Nn.min,Tr.min),Nn.expandByPoint(en),en.addVectors(Nn.max,Tr.max),Nn.expandByPoint(en)):(Nn.expandByPoint(Tr.min),Nn.expandByPoint(Tr.max))}Nn.getCenter(n);let s=0;for(let r=0,a=t.count;r<a;r++)en.fromBufferAttribute(t,r),s=Math.max(s,n.distanceToSquared(en));if(e)for(let r=0,a=e.length;r<a;r++){let o=e[r],c=this.morphTargetsRelative;for(let l=0,u=o.count;l<u;l++)en.fromBufferAttribute(o,l),c&&(Vs.fromBufferAttribute(t,l),en.add(Vs)),s=Math.max(s,n.distanceToSquared(en))}this.boundingSphere.radius=Math.sqrt(s),isNaN(this.boundingSphere.radius)&&ae('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let t=this.index,e=this.attributes;if(t===null||e.position===void 0||e.normal===void 0||e.uv===void 0){ae("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let n=e.position,s=e.normal,r=e.uv,a=this.getAttribute("tangent");(a===void 0||a.count!==n.count)&&(a=new Ue(new Float32Array(4*n.count),4),this.setAttribute("tangent",a));let o=[],c=[];for(let _=0;_<n.count;_++)o[_]=new C,c[_]=new C;let l=new C,u=new C,d=new C,h=new vt,f=new vt,g=new vt,x=new C,p=new C;function m(_,T,P){l.fromBufferAttribute(n,_),u.fromBufferAttribute(n,T),d.fromBufferAttribute(n,P),h.fromBufferAttribute(r,_),f.fromBufferAttribute(r,T),g.fromBufferAttribute(r,P),u.sub(l),d.sub(l),f.sub(h),g.sub(h);let L=1/(f.x*g.y-g.x*f.y);isFinite(L)&&(x.copy(u).multiplyScalar(g.y).addScaledVector(d,-f.y).multiplyScalar(L),p.copy(d).multiplyScalar(f.x).addScaledVector(u,-g.x).multiplyScalar(L),o[_].add(x),o[T].add(x),o[P].add(x),c[_].add(p),c[T].add(p),c[P].add(p))}let y=this.groups;y.length===0&&(y=[{start:0,count:t.count}]);for(let _=0,T=y.length;_<T;++_){let P=y[_],L=P.start,F=P.count;for(let V=L,I=L+F;V<I;V+=3)m(t.getX(V+0),t.getX(V+1),t.getX(V+2))}let E=new C,v=new C,b=new C,M=new C;function A(_){b.fromBufferAttribute(s,_),M.copy(b);let T=o[_];E.copy(T),E.sub(b.multiplyScalar(b.dot(T))).normalize(),v.crossVectors(M,T);let L=v.dot(c[_])<0?-1:1;a.setXYZW(_,E.x,E.y,E.z,L)}for(let _=0,T=y.length;_<T;++_){let P=y[_],L=P.start,F=P.count;for(let V=L,I=L+F;V<I;V+=3)A(t.getX(V+0)),A(t.getX(V+1)),A(t.getX(V+2))}this._transformed=!0}computeVertexNormals(){let t=this.index,e=this.getAttribute("position");if(e!==void 0){let n=this.getAttribute("normal");if(n===void 0||n.count!==e.count)n=new Ue(new Float32Array(e.count*3),3),this.setAttribute("normal",n);else for(let h=0,f=n.count;h<f;h++)n.setXYZ(h,0,0,0);let s=new C,r=new C,a=new C,o=new C,c=new C,l=new C,u=new C,d=new C;if(t)for(let h=0,f=t.count;h<f;h+=3){let g=t.getX(h+0),x=t.getX(h+1),p=t.getX(h+2);s.fromBufferAttribute(e,g),r.fromBufferAttribute(e,x),a.fromBufferAttribute(e,p),u.subVectors(a,r),d.subVectors(s,r),u.cross(d),o.fromBufferAttribute(n,g),c.fromBufferAttribute(n,x),l.fromBufferAttribute(n,p),o.add(u),c.add(u),l.add(u),n.setXYZ(g,o.x,o.y,o.z),n.setXYZ(x,c.x,c.y,c.z),n.setXYZ(p,l.x,l.y,l.z)}else for(let h=0,f=e.count;h<f;h+=3)s.fromBufferAttribute(e,h+0),r.fromBufferAttribute(e,h+1),a.fromBufferAttribute(e,h+2),u.subVectors(a,r),d.subVectors(s,r),u.cross(d),n.setXYZ(h+0,u.x,u.y,u.z),n.setXYZ(h+1,u.x,u.y,u.z),n.setXYZ(h+2,u.x,u.y,u.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let t=this.attributes.normal;for(let e=0,n=t.count;e<n;e++)en.fromBufferAttribute(t,e),en.normalize(),t.setXYZ(e,en.x,en.y,en.z)}toNonIndexed(){function t(o,c){let l=o.array,u=o.itemSize,d=o.normalized,h=new l.constructor(c.length*u),f=0,g=0;for(let x=0,p=c.length;x<p;x++){o.isInterleavedBufferAttribute?f=c[x]*o.data.stride+o.offset:f=c[x]*u;for(let m=0;m<u;m++)h[g++]=l[f++]}return new Ue(h,u,d)}if(this.index===null)return ie("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let e=new i,n=this.index.array,s=this.attributes;for(let o in s){let c=s[o],l=t(c,n);e.setAttribute(o,l)}let r=this.morphAttributes;for(let o in r){let c=[],l=r[o];for(let u=0,d=l.length;u<d;u++){let h=l[u],f=t(h,n);c.push(f)}e.morphAttributes[o]=c}e.morphTargetsRelative=this.morphTargetsRelative;let a=this.groups;for(let o=0,c=a.length;o<c;o++){let l=a[o];e.addGroup(l.start,l.count,l.materialIndex)}return e}toJSON(){let t={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(t.uuid=this.uuid,t.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,t.name=this.name,Object.keys(this.userData).length>0&&(t.userData=this.userData),this.parameters!==void 0&&this._transformed!==!0){let c=this.parameters;for(let l in c)c[l]!==void 0&&(t[l]=c[l]);return t}t.data={attributes:{}};let e=this.index;e!==null&&(t.data.index={type:e.array.constructor.name,array:Array.prototype.slice.call(e.array)});let n=this.attributes;for(let c in n){let l=n[c];t.data.attributes[c]=l.toJSON(t.data)}let s={},r=!1;for(let c in this.morphAttributes){let l=this.morphAttributes[c],u=[];for(let d=0,h=l.length;d<h;d++){let f=l[d];u.push(f.toJSON(t.data))}u.length>0&&(s[c]=u,r=!0)}r&&(t.data.morphAttributes=s,t.data.morphTargetsRelative=this.morphTargetsRelative);let a=this.groups;a.length>0&&(t.data.groups=JSON.parse(JSON.stringify(a)));let o=this.boundingSphere;return o!==null&&(t.data.boundingSphere=o.toJSON()),t}clone(){return new this.constructor().copy(this)}copy(t){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let e={};this.name=t.name;let n=t.index;n!==null&&this.setIndex(n.clone());let s=t.attributes;for(let l in s){let u=s[l];this.setAttribute(l,u.clone(e))}let r=t.morphAttributes;for(let l in r){let u=[],d=r[l];for(let h=0,f=d.length;h<f;h++)u.push(d[h].clone(e));this.morphAttributes[l]=u}this.morphTargetsRelative=t.morphTargetsRelative;let a=t.groups;for(let l=0,u=a.length;l<u;l++){let d=a[l];this.addGroup(d.start,d.count,d.materialIndex)}let o=t.boundingBox;o!==null&&(this.boundingBox=o.clone());let c=t.boundingSphere;return c!==null&&(this.boundingSphere=c.clone()),this.drawRange.start=t.drawRange.start,this.drawRange.count=t.drawRange.count,this.userData=t.userData,this._transformed=t._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}},xo=class{constructor(t,e){this.isInterleavedBuffer=!0,this.array=t,this.stride=e,this.count=t!==void 0?t.length/e:0,this.usage=Ql,this.updateRanges=[],this.version=0,this.uuid=fi()}onUploadCallback(){}set needsUpdate(t){t===!0&&this.version++}setUsage(t){return this.usage=t,this}addUpdateRange(t,e){this.updateRanges.push({start:t,count:e})}clearUpdateRanges(){this.updateRanges.length=0}copy(t){return this.array=new t.array.constructor(t.array),this.count=t.count,this.stride=t.stride,this.usage=t.usage,this}copyAt(t,e,n){t*=this.stride,n*=e.stride;for(let s=0,r=this.stride;s<r;s++)this.array[t+s]=e.array[n+s];return this}set(t,e=0){return this.array.set(t,e),this}clone(t){t.arrayBuffers===void 0&&(t.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=fi()),t.arrayBuffers[this.array.buffer._uuid]===void 0&&(t.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer);let e=new this.array.constructor(t.arrayBuffers[this.array.buffer._uuid]),n=new this.constructor(e,this.stride);return n.setUsage(this.usage),n}onUpload(t){return this.onUploadCallback=t,this}toJSON(t){t.arrayBuffers===void 0&&(t.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=fi()),t.arrayBuffers[this.array.buffer._uuid]===void 0&&(t.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer)));let e={uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride};return e.usage=this.usage,e}},Sn=new C,ai=class i{constructor(t,e,n,s=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=t,this.itemSize=e,this.offset=n,this.normalized=s}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(t){this.data.needsUpdate=t}applyMatrix4(t){for(let e=0,n=this.data.count;e<n;e++)Sn.fromBufferAttribute(this,e),Sn.applyMatrix4(t),this.setXYZ(e,Sn.x,Sn.y,Sn.z);return this}applyNormalMatrix(t){for(let e=0,n=this.count;e<n;e++)Sn.fromBufferAttribute(this,e),Sn.applyNormalMatrix(t),this.setXYZ(e,Sn.x,Sn.y,Sn.z);return this}transformDirection(t){for(let e=0,n=this.count;e<n;e++)Sn.fromBufferAttribute(this,e),Sn.transformDirection(t),this.setXYZ(e,Sn.x,Sn.y,Sn.z);return this}getComponent(t,e){let n=this.array[t*this.data.stride+this.offset+e];return this.normalized&&(n=ii(n,this.array)),n}setComponent(t,e,n){return this.normalized&&(n=De(n,this.array)),this.data.array[t*this.data.stride+this.offset+e]=n,this}setX(t,e){return this.normalized&&(e=De(e,this.array)),this.data.array[t*this.data.stride+this.offset]=e,this}setY(t,e){return this.normalized&&(e=De(e,this.array)),this.data.array[t*this.data.stride+this.offset+1]=e,this}setZ(t,e){return this.normalized&&(e=De(e,this.array)),this.data.array[t*this.data.stride+this.offset+2]=e,this}setW(t,e){return this.normalized&&(e=De(e,this.array)),this.data.array[t*this.data.stride+this.offset+3]=e,this}getX(t){let e=this.data.array[t*this.data.stride+this.offset];return this.normalized&&(e=ii(e,this.array)),e}getY(t){let e=this.data.array[t*this.data.stride+this.offset+1];return this.normalized&&(e=ii(e,this.array)),e}getZ(t){let e=this.data.array[t*this.data.stride+this.offset+2];return this.normalized&&(e=ii(e,this.array)),e}getW(t){let e=this.data.array[t*this.data.stride+this.offset+3];return this.normalized&&(e=ii(e,this.array)),e}setXY(t,e,n){return t=t*this.data.stride+this.offset,this.normalized&&(e=De(e,this.array),n=De(n,this.array)),this.data.array[t+0]=e,this.data.array[t+1]=n,this}setXYZ(t,e,n,s){return t=t*this.data.stride+this.offset,this.normalized&&(e=De(e,this.array),n=De(n,this.array),s=De(s,this.array)),this.data.array[t+0]=e,this.data.array[t+1]=n,this.data.array[t+2]=s,this}setXYZW(t,e,n,s,r){return t=t*this.data.stride+this.offset,this.normalized&&(e=De(e,this.array),n=De(n,this.array),s=De(s,this.array),r=De(r,this.array)),this.data.array[t+0]=e,this.data.array[t+1]=n,this.data.array[t+2]=s,this.data.array[t+3]=r,this}clone(t){if(t===void 0){Or("InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");let e=[];for(let n=0;n<this.count;n++){let s=n*this.data.stride+this.offset;for(let r=0;r<this.itemSize;r++)e.push(this.data.array[s+r])}return new Ue(new this.array.constructor(e),this.itemSize,this.normalized)}else return t.interleavedBuffers===void 0&&(t.interleavedBuffers={}),t.interleavedBuffers[this.data.uuid]===void 0&&(t.interleavedBuffers[this.data.uuid]=this.data.clone(t)),new i(t.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}toJSON(t){if(t===void 0){Or("InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");let e=[];for(let n=0;n<this.count;n++){let s=n*this.data.stride+this.offset;for(let r=0;r<this.itemSize;r++)e.push(this.data.array[s+r])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:e,normalized:this.normalized}}else return t.interleavedBuffers===void 0&&(t.interleavedBuffers={}),t.interleavedBuffers[this.data.uuid]===void 0&&(t.interleavedBuffers[this.data.uuid]=this.data.toJSON(t)),{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}},dl=new C,sp=new C,rp=new he,ni=class{constructor(t=new C(1,0,0),e=0){this.isPlane=!0,this.normal=t,this.constant=e}set(t,e){return this.normal.copy(t),this.constant=e,this}setComponents(t,e,n,s){return this.normal.set(t,e,n),this.constant=s,this}setFromNormalAndCoplanarPoint(t,e){return this.normal.copy(t),this.constant=-e.dot(this.normal),this}setFromCoplanarPoints(t,e,n){let s=dl.subVectors(n,e).cross(sp.subVectors(t,e)).normalize();return this.setFromNormalAndCoplanarPoint(s,t),this}copy(t){return this.normal.copy(t.normal),this.constant=t.constant,this}normalize(){let t=1/this.normal.length();return this.normal.multiplyScalar(t),this.constant*=t,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(t){return this.normal.dot(t)+this.constant}distanceToSphere(t){return this.distanceToPoint(t.center)-t.radius}projectPoint(t,e){return e.copy(t).addScaledVector(this.normal,-this.distanceToPoint(t))}intersectLine(t,e,n=!0){let s=t.delta(dl),r=this.normal.dot(s);if(r===0)return this.distanceToPoint(t.start)===0?e.copy(t.start):null;let a=-(t.start.dot(this.normal)+this.constant)/r;return n===!0&&(a<0||a>1)?null:e.copy(t.start).addScaledVector(s,a)}intersectsLine(t){let e=this.distanceToPoint(t.start),n=this.distanceToPoint(t.end);return e<0&&n>0||n<0&&e>0}intersectsBox(t){return t.intersectsPlane(this)}intersectsSphere(t){return t.intersectsPlane(this)}coplanarPoint(t){return t.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(t,e){let n=e||rp.getNormalMatrix(t),s=this.coplanarPoint(dl).applyMatrix4(t),r=this.normal.applyMatrix3(n).normalize();return this.constant=-s.dot(r),this}translate(t){return this.constant-=t.dot(this.normal),this}equals(t){return t.normal.equals(this.normal)&&t.constant===this.constant}clone(){return new this.constructor().copy(this)}toJSON(){return{normal:this.normal.toArray(),constant:this.constant}}fromJSON(t){return this.normal.fromArray(t.normal),this.constant=t.constant,this}},ap=0,Oi=class extends mi{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:ap++}),this.uuid=fi(),this.name="",this.type="Material",this.blending=ur,this.side=rs,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=zl,this.blendDst=Ol,this.blendEquation=bs,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new Wt(0,0,0),this.blendAlpha=0,this.depthFunc=$s,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=qu,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=so,this.stencilZFail=so,this.stencilZPass=so,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(t){this._alphaTest>0!=t>0&&this.version++,this._alphaTest=t}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(t){if(t!==void 0)for(let e in t){let n=t[e];if(n===void 0){ie(`Material: parameter '${e}' has value of undefined.`);continue}let s=this[e];if(s===void 0){ie(`Material: '${e}' is not a property of THREE.${this.type}.`);continue}s&&s.isColor?s.set(n):s&&s.isVector2&&n&&n.isVector2||s&&s.isEuler&&n&&n.isEuler||s&&s.isVector3&&n&&n.isVector3?s.copy(n):this[e]=n}}toJSON(t){let e=t===void 0||typeof t=="string";e&&(t={textures:{},images:{}});let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,n.blending=this.blending,n.side=this.side,n.shadowSide=this.shadowSide,n.vertexColors=this.vertexColors,n.opacity=this.opacity,n.transparent=this.transparent,n.blendSrc=this.blendSrc,n.blendDst=this.blendDst,n.blendEquation=this.blendEquation,n.blendSrcAlpha=this.blendSrcAlpha,n.blendDstAlpha=this.blendDstAlpha,n.blendEquationAlpha=this.blendEquationAlpha,n.blendColor=this.blendColor.getHex(),n.blendAlpha=this.blendAlpha,n.depthFunc=this.depthFunc,n.depthTest=this.depthTest,n.depthWrite=this.depthWrite,n.colorWrite=this.colorWrite,n.clipIntersection=this.clipIntersection,n.clipShadows=this.clipShadows,n.stencilWriteMask=this.stencilWriteMask,n.stencilFunc=this.stencilFunc,n.stencilRef=this.stencilRef,n.stencilFuncMask=this.stencilFuncMask,n.stencilFail=this.stencilFail,n.stencilZFail=this.stencilZFail,n.stencilZPass=this.stencilZPass,n.stencilWrite=this.stencilWrite,n.polygonOffset=this.polygonOffset,n.polygonOffsetFactor=this.polygonOffsetFactor,n.polygonOffsetUnits=this.polygonOffsetUnits,n.dithering=this.dithering,n.alphaTest=this.alphaTest,n.alphaHash=this.alphaHash,n.alphaToCoverage=this.alphaToCoverage,n.premultipliedAlpha=this.premultipliedAlpha,n.forceSinglePass=this.forceSinglePass,n.allowOverride=this.allowOverride,n.visible=this.visible,n.toneMapped=this.toneMapped,n.name=this.name,this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(t).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(t).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(t).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(t).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(t).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.retroreflectivity!==void 0&&(n.retroreflectivity=this.retroreflectivity),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(t).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(t).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(t).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(t).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(t).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(t).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(t).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(t).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(t).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(t).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(t).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(t).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(t).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(t).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(t).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(t).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(t).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(t).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(t).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(t).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(t).uuid),this.attenuationDistance!==void 0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),Array.isArray(this.clippingPlanes)&&this.clippingPlanes.length>0&&(n.clippingPlanes=this.clippingPlanes.map(r=>r.toJSON())),this.rotation!==void 0&&(n.rotation=this.rotation),this.depthPacking!==void 0&&(n.depthPacking=this.depthPacking),this.linewidth!==void 0&&(n.linewidth=this.linewidth),this.linecap!==void 0&&(n.linecap=this.linecap),this.linejoin!==void 0&&(n.linejoin=this.linejoin),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.wireframe!==void 0&&(n.wireframe=this.wireframe),this.wireframeLinewidth!==void 0&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!==void 0&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!==void 0&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading!==void 0&&(n.flatShading=this.flatShading),this.fog!==void 0&&(n.fog=this.fog),Object.keys(this.userData).length>0&&(n.userData=this.userData);function s(r){let a=[];for(let o in r){let c=r[o];delete c.metadata,a.push(c)}return a}if(e){let r=s(t.textures),a=s(t.images);r.length>0&&(n.textures=r),a.length>0&&(n.images=a)}return n}fromJSON(t,e){if(t.uuid!==void 0&&(this.uuid=t.uuid),t.name!==void 0&&(this.name=t.name),t.color!==void 0&&this.color!==void 0&&this.color.setHex(t.color),t.roughness!==void 0&&(this.roughness=t.roughness),t.metalness!==void 0&&(this.metalness=t.metalness),t.sheen!==void 0&&(this.sheen=t.sheen),t.sheenColor!==void 0&&(this.sheenColor=new Wt().setHex(t.sheenColor)),t.sheenRoughness!==void 0&&(this.sheenRoughness=t.sheenRoughness),t.emissive!==void 0&&this.emissive!==void 0&&this.emissive.setHex(t.emissive),t.specular!==void 0&&this.specular!==void 0&&this.specular.setHex(t.specular),t.specularIntensity!==void 0&&(this.specularIntensity=t.specularIntensity),t.specularColor!==void 0&&this.specularColor!==void 0&&this.specularColor.setHex(t.specularColor),t.shininess!==void 0&&(this.shininess=t.shininess),t.clearcoat!==void 0&&(this.clearcoat=t.clearcoat),t.clearcoatRoughness!==void 0&&(this.clearcoatRoughness=t.clearcoatRoughness),t.dispersion!==void 0&&(this.dispersion=t.dispersion),t.retroreflectivity!==void 0&&(this.retroreflectivity=t.retroreflectivity),t.iridescence!==void 0&&(this.iridescence=t.iridescence),t.iridescenceIOR!==void 0&&(this.iridescenceIOR=t.iridescenceIOR),t.iridescenceThicknessRange!==void 0&&(this.iridescenceThicknessRange=t.iridescenceThicknessRange),t.transmission!==void 0&&(this.transmission=t.transmission),t.thickness!==void 0&&(this.thickness=t.thickness),t.attenuationDistance!==void 0&&(this.attenuationDistance=t.attenuationDistance),t.attenuationColor!==void 0&&this.attenuationColor!==void 0&&this.attenuationColor.setHex(t.attenuationColor),t.anisotropy!==void 0&&(this.anisotropy=t.anisotropy),t.anisotropyRotation!==void 0&&(this.anisotropyRotation=t.anisotropyRotation),t.fog!==void 0&&(this.fog=t.fog),t.flatShading!==void 0&&(this.flatShading=t.flatShading),t.blending!==void 0&&(this.blending=t.blending),t.combine!==void 0&&(this.combine=t.combine),t.side!==void 0&&(this.side=t.side),t.shadowSide!==void 0&&(this.shadowSide=t.shadowSide),t.opacity!==void 0&&(this.opacity=t.opacity),t.transparent!==void 0&&(this.transparent=t.transparent),t.alphaTest!==void 0&&(this.alphaTest=t.alphaTest),t.alphaHash!==void 0&&(this.alphaHash=t.alphaHash),t.depthFunc!==void 0&&(this.depthFunc=t.depthFunc),t.depthTest!==void 0&&(this.depthTest=t.depthTest),t.depthWrite!==void 0&&(this.depthWrite=t.depthWrite),t.colorWrite!==void 0&&(this.colorWrite=t.colorWrite),t.clippingPlanes!==void 0&&(this.clippingPlanes=t.clippingPlanes.map(n=>new ni().fromJSON(n))),t.clipIntersection!==void 0&&(this.clipIntersection=t.clipIntersection),t.clipShadows!==void 0&&(this.clipShadows=t.clipShadows),t.depthPacking!==void 0&&(this.depthPacking=t.depthPacking),t.blendSrc!==void 0&&(this.blendSrc=t.blendSrc),t.blendDst!==void 0&&(this.blendDst=t.blendDst),t.blendEquation!==void 0&&(this.blendEquation=t.blendEquation),t.blendSrcAlpha!==void 0&&(this.blendSrcAlpha=t.blendSrcAlpha),t.blendDstAlpha!==void 0&&(this.blendDstAlpha=t.blendDstAlpha),t.blendEquationAlpha!==void 0&&(this.blendEquationAlpha=t.blendEquationAlpha),t.blendColor!==void 0&&this.blendColor!==void 0&&this.blendColor.setHex(t.blendColor),t.blendAlpha!==void 0&&(this.blendAlpha=t.blendAlpha),t.stencilWriteMask!==void 0&&(this.stencilWriteMask=t.stencilWriteMask),t.stencilFunc!==void 0&&(this.stencilFunc=t.stencilFunc),t.stencilRef!==void 0&&(this.stencilRef=t.stencilRef),t.stencilFuncMask!==void 0&&(this.stencilFuncMask=t.stencilFuncMask),t.stencilFail!==void 0&&(this.stencilFail=t.stencilFail),t.stencilZFail!==void 0&&(this.stencilZFail=t.stencilZFail),t.stencilZPass!==void 0&&(this.stencilZPass=t.stencilZPass),t.stencilWrite!==void 0&&(this.stencilWrite=t.stencilWrite),t.wireframe!==void 0&&(this.wireframe=t.wireframe),t.wireframeLinewidth!==void 0&&(this.wireframeLinewidth=t.wireframeLinewidth),t.wireframeLinecap!==void 0&&(this.wireframeLinecap=t.wireframeLinecap),t.wireframeLinejoin!==void 0&&(this.wireframeLinejoin=t.wireframeLinejoin),t.rotation!==void 0&&(this.rotation=t.rotation),t.linewidth!==void 0&&(this.linewidth=t.linewidth),t.linecap!==void 0&&(this.linecap=t.linecap),t.linejoin!==void 0&&(this.linejoin=t.linejoin),t.dashSize!==void 0&&(this.dashSize=t.dashSize),t.gapSize!==void 0&&(this.gapSize=t.gapSize),t.scale!==void 0&&(this.scale=t.scale),t.polygonOffset!==void 0&&(this.polygonOffset=t.polygonOffset),t.polygonOffsetFactor!==void 0&&(this.polygonOffsetFactor=t.polygonOffsetFactor),t.polygonOffsetUnits!==void 0&&(this.polygonOffsetUnits=t.polygonOffsetUnits),t.dithering!==void 0&&(this.dithering=t.dithering),t.alphaToCoverage!==void 0&&(this.alphaToCoverage=t.alphaToCoverage),t.premultipliedAlpha!==void 0&&(this.premultipliedAlpha=t.premultipliedAlpha),t.forceSinglePass!==void 0&&(this.forceSinglePass=t.forceSinglePass),t.allowOverride!==void 0&&(this.allowOverride=t.allowOverride),t.visible!==void 0&&(this.visible=t.visible),t.toneMapped!==void 0&&(this.toneMapped=t.toneMapped),t.userData!==void 0&&(this.userData=t.userData),t.vertexColors!==void 0&&(typeof t.vertexColors=="number"?this.vertexColors=t.vertexColors>0:this.vertexColors=t.vertexColors),t.size!==void 0&&(this.size=t.size),t.sizeAttenuation!==void 0&&(this.sizeAttenuation=t.sizeAttenuation),t.map!==void 0&&(this.map=e[t.map]||null),t.matcap!==void 0&&(this.matcap=e[t.matcap]||null),t.alphaMap!==void 0&&(this.alphaMap=e[t.alphaMap]||null),t.bumpMap!==void 0&&(this.bumpMap=e[t.bumpMap]||null),t.bumpScale!==void 0&&(this.bumpScale=t.bumpScale),t.normalMap!==void 0&&(this.normalMap=e[t.normalMap]||null),t.normalMapType!==void 0&&(this.normalMapType=t.normalMapType),t.normalScale!==void 0){let n=t.normalScale;Array.isArray(n)===!1&&(n=[n,n]),this.normalScale=new vt().fromArray(n)}return t.displacementMap!==void 0&&(this.displacementMap=e[t.displacementMap]||null),t.displacementScale!==void 0&&(this.displacementScale=t.displacementScale),t.displacementBias!==void 0&&(this.displacementBias=t.displacementBias),t.roughnessMap!==void 0&&(this.roughnessMap=e[t.roughnessMap]||null),t.metalnessMap!==void 0&&(this.metalnessMap=e[t.metalnessMap]||null),t.emissiveMap!==void 0&&(this.emissiveMap=e[t.emissiveMap]||null),t.emissiveIntensity!==void 0&&(this.emissiveIntensity=t.emissiveIntensity),t.specularMap!==void 0&&(this.specularMap=e[t.specularMap]||null),t.specularIntensityMap!==void 0&&(this.specularIntensityMap=e[t.specularIntensityMap]||null),t.specularColorMap!==void 0&&(this.specularColorMap=e[t.specularColorMap]||null),t.envMap!==void 0&&(this.envMap=e[t.envMap]||null),t.envMapRotation!==void 0&&this.envMapRotation.fromArray(t.envMapRotation),t.envMapIntensity!==void 0&&(this.envMapIntensity=t.envMapIntensity),t.reflectivity!==void 0&&(this.reflectivity=t.reflectivity),t.refractionRatio!==void 0&&(this.refractionRatio=t.refractionRatio),t.lightMap!==void 0&&(this.lightMap=e[t.lightMap]||null),t.lightMapIntensity!==void 0&&(this.lightMapIntensity=t.lightMapIntensity),t.aoMap!==void 0&&(this.aoMap=e[t.aoMap]||null),t.aoMapIntensity!==void 0&&(this.aoMapIntensity=t.aoMapIntensity),t.gradientMap!==void 0&&(this.gradientMap=e[t.gradientMap]||null),t.clearcoatMap!==void 0&&(this.clearcoatMap=e[t.clearcoatMap]||null),t.clearcoatRoughnessMap!==void 0&&(this.clearcoatRoughnessMap=e[t.clearcoatRoughnessMap]||null),t.clearcoatNormalMap!==void 0&&(this.clearcoatNormalMap=e[t.clearcoatNormalMap]||null),t.clearcoatNormalScale!==void 0&&(this.clearcoatNormalScale=new vt().fromArray(t.clearcoatNormalScale)),t.iridescenceMap!==void 0&&(this.iridescenceMap=e[t.iridescenceMap]||null),t.iridescenceThicknessMap!==void 0&&(this.iridescenceThicknessMap=e[t.iridescenceThicknessMap]||null),t.transmissionMap!==void 0&&(this.transmissionMap=e[t.transmissionMap]||null),t.thicknessMap!==void 0&&(this.thicknessMap=e[t.thicknessMap]||null),t.anisotropyMap!==void 0&&(this.anisotropyMap=e[t.anisotropyMap]||null),t.sheenColorMap!==void 0&&(this.sheenColorMap=e[t.sheenColorMap]||null),t.sheenRoughnessMap!==void 0&&(this.sheenRoughnessMap=e[t.sheenRoughnessMap]||null),this}clone(){return new this.constructor().copy(this)}copy(t){this.name=t.name,this.blending=t.blending,this.side=t.side,this.vertexColors=t.vertexColors,this.opacity=t.opacity,this.transparent=t.transparent,this.blendSrc=t.blendSrc,this.blendDst=t.blendDst,this.blendEquation=t.blendEquation,this.blendSrcAlpha=t.blendSrcAlpha,this.blendDstAlpha=t.blendDstAlpha,this.blendEquationAlpha=t.blendEquationAlpha,this.blendColor.copy(t.blendColor),this.blendAlpha=t.blendAlpha,this.depthFunc=t.depthFunc,this.depthTest=t.depthTest,this.depthWrite=t.depthWrite,this.stencilWriteMask=t.stencilWriteMask,this.stencilFunc=t.stencilFunc,this.stencilRef=t.stencilRef,this.stencilFuncMask=t.stencilFuncMask,this.stencilFail=t.stencilFail,this.stencilZFail=t.stencilZFail,this.stencilZPass=t.stencilZPass,this.stencilWrite=t.stencilWrite;let e=t.clippingPlanes,n=null;if(e!==null){let s=e.length;n=new Array(s);for(let r=0;r!==s;++r)n[r]=e[r].clone()}return this.clippingPlanes=n,this.clipIntersection=t.clipIntersection,this.clipShadows=t.clipShadows,this.shadowSide=t.shadowSide,this.colorWrite=t.colorWrite,this.precision=t.precision,this.polygonOffset=t.polygonOffset,this.polygonOffsetFactor=t.polygonOffsetFactor,this.polygonOffsetUnits=t.polygonOffsetUnits,this.dithering=t.dithering,this.alphaTest=t.alphaTest,this.alphaHash=t.alphaHash,this.alphaToCoverage=t.alphaToCoverage,this.premultipliedAlpha=t.premultipliedAlpha,this.forceSinglePass=t.forceSinglePass,this.allowOverride=t.allowOverride,this.visible=t.visible,this.toneMapped=t.toneMapped,this.userData=JSON.parse(JSON.stringify(t.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(t){t===!0&&this.version++}};var Ui=new C,fl=new C,Ba=new C,ka=new C,Wr=class{constructor(t=new C,e=new C(0,0,-1)){this.origin=t,this.direction=e}set(t,e){return this.origin.copy(t),this.direction.copy(e),this}copy(t){return this.origin.copy(t.origin),this.direction.copy(t.direction),this}at(t,e){return e.copy(this.origin).addScaledVector(this.direction,t)}lookAt(t){return this.direction.copy(t).sub(this.origin).normalize(),this}recast(t){return this.origin.copy(this.at(t,Ui)),this}closestPointToPoint(t,e){e.subVectors(t,this.origin);let n=e.dot(this.direction);return n<0?e.copy(this.origin):e.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(t){return Math.sqrt(this.distanceSqToPoint(t))}distanceSqToPoint(t){let e=Ui.subVectors(t,this.origin).dot(this.direction);return e<0?this.origin.distanceToSquared(t):(Ui.copy(this.origin).addScaledVector(this.direction,e),Ui.distanceToSquared(t))}distanceSqToSegment(t,e,n,s){fl.copy(t).add(e).multiplyScalar(.5),Ba.copy(e).sub(t).normalize(),ka.copy(this.origin).sub(fl);let r=t.distanceTo(e)*.5,a=-this.direction.dot(Ba),o=ka.dot(this.direction),c=-ka.dot(Ba),l=ka.lengthSq(),u=Math.abs(1-a*a),d,h,f,g;if(u>0)if(d=a*c-o,h=a*o-c,g=r*u,d>=0)if(h>=-g)if(h<=g){let x=1/u;d*=x,h*=x,f=d*(d+a*h+2*o)+h*(a*d+h+2*c)+l}else h=r,d=Math.max(0,-(a*h+o)),f=-d*d+h*(h+2*c)+l;else h=-r,d=Math.max(0,-(a*h+o)),f=-d*d+h*(h+2*c)+l;else h<=-g?(d=Math.max(0,-(-a*r+o)),h=d>0?-r:Math.min(Math.max(-r,-c),r),f=-d*d+h*(h+2*c)+l):h<=g?(d=0,h=Math.min(Math.max(-r,-c),r),f=h*(h+2*c)+l):(d=Math.max(0,-(a*r+o)),h=d>0?r:Math.min(Math.max(-r,-c),r),f=-d*d+h*(h+2*c)+l);else h=a>0?-r:r,d=Math.max(0,-(a*h+o)),f=-d*d+h*(h+2*c)+l;return n&&n.copy(this.origin).addScaledVector(this.direction,d),s&&s.copy(fl).addScaledVector(Ba,h),f}intersectSphere(t,e){if(t.radius<0)return null;Ui.subVectors(t.center,this.origin);let n=Ui.dot(this.direction),s=Ui.dot(Ui)-n*n,r=t.radius*t.radius;if(s>r)return null;let a=Math.sqrt(r-s),o=n-a,c=n+a;return c<0?null:o<0?this.at(c,e):this.at(o,e)}intersectsSphere(t){return t.radius<0?!1:this.distanceSqToPoint(t.center)<=t.radius*t.radius}distanceToPlane(t){let e=t.normal.dot(this.direction);if(e===0)return t.distanceToPoint(this.origin)===0?0:null;let n=-(this.origin.dot(t.normal)+t.constant)/e;return n>=0?n:null}intersectPlane(t,e){let n=this.distanceToPlane(t);return n===null?null:this.at(n,e)}intersectsPlane(t){let e=t.distanceToPoint(this.origin);return e===0||t.normal.dot(this.direction)*e<0}intersectBox(t,e){let n,s,r,a,o,c,l=1/this.direction.x,u=1/this.direction.y,d=1/this.direction.z,h=this.origin;return l>=0?(n=(t.min.x-h.x)*l,s=(t.max.x-h.x)*l):(n=(t.max.x-h.x)*l,s=(t.min.x-h.x)*l),u>=0?(r=(t.min.y-h.y)*u,a=(t.max.y-h.y)*u):(r=(t.max.y-h.y)*u,a=(t.min.y-h.y)*u),n>a||r>s||((r>n||isNaN(n))&&(n=r),(a<s||isNaN(s))&&(s=a),d>=0?(o=(t.min.z-h.z)*d,c=(t.max.z-h.z)*d):(o=(t.max.z-h.z)*d,c=(t.min.z-h.z)*d),n>c||o>s)||((o>n||n!==n)&&(n=o),(c<s||s!==s)&&(s=c),s<0)?null:this.at(n>=0?n:s,e)}intersectsBox(t){return this.intersectBox(t,Ui)!==null}intersectTriangle(t,e,n,s,r){let a=this.origin,o=this.direction,c=o.x,l=o.y,u=o.z,d=t.x-a.x,h=t.y-a.y,f=t.z-a.z,g=e.x-a.x,x=e.y-a.y,p=e.z-a.z,m=n.x-a.x,y=n.y-a.y,E=n.z-a.z,v=Math.abs(c),b=Math.abs(l),M=Math.abs(u),A,_,T,P,L,F,V,I,z,q,j,at;if(v>=b&&v>=M?(T=c,F=d,z=g,at=m,c>=0?(A=l,_=u,P=h,L=f,V=x,I=p,q=y,j=E):(A=u,_=l,P=f,L=h,V=p,I=x,q=E,j=y)):b>=M?(T=l,F=h,z=x,at=y,l>=0?(A=u,_=c,P=f,L=d,V=p,I=g,q=E,j=m):(A=c,_=u,P=d,L=f,V=g,I=p,q=m,j=E)):(T=u,F=f,z=p,at=E,u>=0?(A=c,_=l,P=d,L=h,V=g,I=x,q=m,j=y):(A=l,_=c,P=h,L=d,V=x,I=g,q=y,j=m)),T===0)return null;let K=A/T,st=_/T,it=1/T,Rt=P-K*F,mt=L-st*F,Ut=V-K*z,Dt=I-st*z,ft=q-K*at,N=j-st*at,k=ft*Dt-N*Ut,dt=Rt*N-mt*ft,St=Ut*mt-Dt*Rt;if(s){if(k<0||dt<0||St<0)return null}else if((k<0||dt<0||St<0)&&(k>0||dt>0||St>0))return null;let Mt=k+dt+St;if(Mt===0)return null;let Ft=it*(k*F+dt*z+St*at);return(Mt>0?Ft<0:Ft>0)?null:this.at(Ft/Mt,r)}applyMatrix4(t){return this.origin.applyMatrix4(t),this.direction.transformDirection(t),this}equals(t){return t.origin.equals(this.origin)&&t.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}},oi=class extends Oi{constructor(t){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new Wt(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new ri,this.combine=Bl,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(t)}copy(t){return super.copy(t),this.color.copy(t.color),this.map=t.map,this.lightMap=t.lightMap,this.lightMapIntensity=t.lightMapIntensity,this.aoMap=t.aoMap,this.aoMapIntensity=t.aoMapIntensity,this.specularMap=t.specularMap,this.alphaMap=t.alphaMap,this.envMap=t.envMap,this.envMapRotation.copy(t.envMapRotation),this.combine=t.combine,this.reflectivity=t.reflectivity,this.refractionRatio=t.refractionRatio,this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this.wireframeLinecap=t.wireframeLinecap,this.wireframeLinejoin=t.wireframeLinejoin,this.fog=t.fog,this}},Qh=new de,gs=new Wr,Ha=new wn,tu=new C,Va=new C,Ga=new C,Wa=new C,pl=new C,Xa=new C,eu=new C,qa=new C,ct=class extends rn{constructor(t=new ge,e=new oi){super(),this.isMesh=!0,this.type="Mesh",this.geometry=t,this.material=e,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(t,e){return super.copy(t,e),t.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=t.morphTargetInfluences.slice()),t.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},t.morphTargetDictionary)),this.material=Array.isArray(t.material)?t.material.slice():t.material,this.geometry=t.geometry,this}updateMorphTargets(){let e=this.geometry.morphAttributes,n=Object.keys(e);if(n.length>0){let s=e[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}getVertexPosition(t,e){let n=this.geometry,s=n.attributes.position,r=n.morphAttributes.position,a=n.morphTargetsRelative;e.fromBufferAttribute(s,t);let o=this.morphTargetInfluences;if(r&&o){Xa.set(0,0,0);for(let c=0,l=r.length;c<l;c++){let u=o[c],d=r[c];u!==0&&(pl.fromBufferAttribute(d,t),a?Xa.addScaledVector(pl,u):Xa.addScaledVector(pl.sub(e),u))}e.add(Xa)}return e}intersectsFrustum(t){return t.intersectsObject(this)}raycast(t,e){let n=this.geometry,s=this.material,r=this.matrixWorld;s!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),Ha.copy(n.boundingSphere),Ha.applyMatrix4(r),gs.copy(t.ray).recast(t.near),!(Ha.containsPoint(gs.origin)===!1&&(gs.intersectSphere(Ha,tu)===null||gs.origin.distanceToSquared(tu)>(t.far-t.near)**2))&&(Qh.copy(r).invert(),gs.copy(t.ray).applyMatrix4(Qh),!(n.boundingBox!==null&&gs.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(t,e,gs)))}_computeIntersections(t,e,n){let s,r=this.geometry,a=this.material,o=r.index,c=r.attributes.position,l=r.attributes.uv,u=r.attributes.uv1,d=r.attributes.normal,h=r.groups,f=r.drawRange;if(o!==null)if(Array.isArray(a))for(let g=0,x=h.length;g<x;g++){let p=h[g],m=a[p.materialIndex],y=Math.max(p.start,f.start),E=Math.min(o.count,Math.min(p.start+p.count,f.start+f.count));for(let v=y,b=E;v<b;v+=3){let M=o.getX(v),A=o.getX(v+1),_=o.getX(v+2);s=Ya(this,m,t,n,l,u,d,M,A,_),s&&(s.faceIndex=Math.floor(v/3),s.face.materialIndex=p.materialIndex,e.push(s))}}else{let g=Math.max(0,f.start),x=Math.min(o.count,f.start+f.count);for(let p=g,m=x;p<m;p+=3){let y=o.getX(p),E=o.getX(p+1),v=o.getX(p+2);s=Ya(this,a,t,n,l,u,d,y,E,v),s&&(s.faceIndex=Math.floor(p/3),e.push(s))}}else if(c!==void 0)if(Array.isArray(a))for(let g=0,x=h.length;g<x;g++){let p=h[g],m=a[p.materialIndex],y=Math.max(p.start,f.start),E=Math.min(c.count,Math.min(p.start+p.count,f.start+f.count));for(let v=y,b=E;v<b;v+=3){let M=v,A=v+1,_=v+2;s=Ya(this,m,t,n,l,u,d,M,A,_),s&&(s.faceIndex=Math.floor(v/3),s.face.materialIndex=p.materialIndex,e.push(s))}}else{let g=Math.max(0,f.start),x=Math.min(c.count,f.start+f.count);for(let p=g,m=x;p<m;p+=3){let y=p,E=p+1,v=p+2;s=Ya(this,a,t,n,l,u,d,y,E,v),s&&(s.faceIndex=Math.floor(p/3),e.push(s))}}}};function op(i,t,e,n,s,r,a,o){let c;if(t.side===on?c=n.intersectTriangle(a,r,s,!0,o):c=n.intersectTriangle(s,r,a,t.side===rs,o),c===null)return null;qa.copy(o),qa.applyMatrix4(i.matrixWorld);let l=e.ray.origin.distanceTo(qa);return l<e.near||l>e.far?null:{distance:l,point:qa.clone(),object:i}}function Ya(i,t,e,n,s,r,a,o,c,l){i.getVertexPosition(o,Va),i.getVertexPosition(c,Ga),i.getVertexPosition(l,Wa);let u=op(i,t,e,n,Va,Ga,Wa,eu);if(u){let d=new C;$i.getBarycoord(eu,Va,Ga,Wa,d),s&&(u.uv=$i.getInterpolatedAttribute(s,o,c,l,d,new vt)),r&&(u.uv1=$i.getInterpolatedAttribute(r,o,c,l,d,new vt)),a&&(u.normal=$i.getInterpolatedAttribute(a,o,c,l,d,new C),u.normal.dot(n.direction)>0&&u.normal.multiplyScalar(-1));let h={a:o,b:c,c:l,normal:new C,materialIndex:0};$i.getNormal(Va,Ga,Wa,h.normal),u.face=h,u.barycoord=d}return u}var ys=class extends En{constructor(t=null,e=1,n=1,s,r,a,o,c,l=nn,u=nn,d,h){super(null,a,o,c,l,u,s,r,d,h),this.isDataTexture=!0,this.image={data:t,width:e,height:n},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var Xr=class extends Ue{constructor(t,e,n,s=1){super(t,e,n),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=s}copy(t){return super.copy(t),this.meshPerAttribute=t.meshPerAttribute,this}toJSON(){let t=super.toJSON();return t.meshPerAttribute=this.meshPerAttribute,t.isInstancedBufferAttribute=!0,t}},Gs=new de,nu=new de,ja=[],iu=new an,cp=new de,Ar=new ct,Rr=new wn,Tn=class extends ct{constructor(t,e,n){super(t,e),this.isInstancedMesh=!0,this.instanceMatrix=new Xr(new Float32Array(n*16),16),this.instanceColor=null,this.morphTexture=null,this.count=n,this.boundingBox=null,this.boundingSphere=null;for(let s=0;s<n;s++)this.setMatrixAt(s,cp)}computeBoundingBox(){let t=this.geometry,e=this.count;this.boundingBox===null&&(this.boundingBox=new an),t.boundingBox===null&&t.computeBoundingBox(),this.boundingBox.makeEmpty();for(let n=0;n<e;n++)this.getMatrixAt(n,Gs),iu.copy(t.boundingBox).applyMatrix4(Gs),this.boundingBox.union(iu)}computeBoundingSphere(){let t=this.geometry,e=this.count;this.boundingSphere===null&&(this.boundingSphere=new wn),t.boundingSphere===null&&t.computeBoundingSphere(),this.boundingSphere.makeEmpty();for(let n=0;n<e;n++)this.getMatrixAt(n,Gs),Rr.copy(t.boundingSphere).applyMatrix4(Gs),this.boundingSphere.union(Rr)}copy(t,e){return super.copy(t,e),this.instanceMatrix.copy(t.instanceMatrix),t.morphTexture!==null&&(this.morphTexture=t.morphTexture.clone()),t.instanceColor!==null&&(this.instanceColor=t.instanceColor.clone()),this.count=t.count,t.boundingBox!==null&&(this.boundingBox=t.boundingBox.clone()),t.boundingSphere!==null&&(this.boundingSphere=t.boundingSphere.clone()),this}getColorAt(t,e){return this.instanceColor===null?e.setRGB(1,1,1):e.fromArray(this.instanceColor.array,t*3)}getMatrixAt(t,e){return e.fromArray(this.instanceMatrix.array,t*16)}getMorphAt(t,e){let n=e.morphTargetInfluences,s=this.morphTexture.source.data.data,r=n.length+1,a=t*r+1;for(let o=0;o<n.length;o++)n[o]=s[a+o]}raycast(t,e){let n=this.matrixWorld,s=this.count;if(Ar.geometry=this.geometry,Ar.material=this.material,Ar.material!==void 0&&(this.boundingSphere===null&&this.computeBoundingSphere(),Rr.copy(this.boundingSphere),Rr.applyMatrix4(n),t.ray.intersectsSphere(Rr)!==!1))for(let r=0;r<s;r++){this.getMatrixAt(r,Gs),nu.multiplyMatrices(n,Gs),Ar.matrixWorld=nu,Ar.raycast(t,ja);for(let a=0,o=ja.length;a<o;a++){let c=ja[a];c.instanceId=r,c.object=this,e.push(c)}ja.length=0}}setColorAt(t,e){return this.instanceColor===null&&(this.instanceColor=new Xr(new Float32Array(this.instanceMatrix.count*3).fill(1),3)),e.toArray(this.instanceColor.array,t*3),this}setMatrixAt(t,e){return e.toArray(this.instanceMatrix.array,t*16),this}setMorphAt(t,e){let n=e.morphTargetInfluences,s=n.length+1;this.morphTexture===null&&(this.morphTexture=new ys(new Float32Array(s*this.count),s,this.count,Zo,qn));let r=this.morphTexture.source.data.data,a=0;for(let l=0;l<n.length;l++)a+=n[l];let o=this.geometry.morphTargetsRelative?1:1-a,c=s*t;return r[c]=o,r.set(n,c+1),this}updateMorphTargets(){}dispose(){super.dispose(),this.morphTexture!==null&&(this.morphTexture.dispose(),this.morphTexture=null)}},vs=new wn,lp=new vt(.5,.5),Za=new C,sr=class{constructor(t=new ni,e=new ni,n=new ni,s=new ni,r=new ni,a=new ni){this.planes=[t,e,n,s,r,a]}set(t,e,n,s,r,a){let o=this.planes;return o[0].copy(t),o[1].copy(e),o[2].copy(n),o[3].copy(s),o[4].copy(r),o[5].copy(a),this}copy(t){let e=this.planes;for(let n=0;n<6;n++)e[n].copy(t.planes[n]);return this}setFromProjectionMatrix(t,e=si,n=!1){let s=this.planes,r=t.elements,a=r[0],o=r[1],c=r[2],l=r[3],u=r[4],d=r[5],h=r[6],f=r[7],g=r[8],x=r[9],p=r[10],m=r[11],y=r[12],E=r[13],v=r[14],b=r[15];if(s[0].setComponents(l-a,f-u,m-g,b-y).normalize(),s[1].setComponents(l+a,f+u,m+g,b+y).normalize(),s[2].setComponents(l+o,f+d,m+x,b+E).normalize(),s[3].setComponents(l-o,f-d,m-x,b-E).normalize(),n)s[4].setComponents(c,h,p,v).normalize(),s[5].setComponents(l-c,f-h,m-p,b-v).normalize();else if(s[4].setComponents(l-c,f-h,m-p,b-v).normalize(),e===si)s[5].setComponents(l+c,f+h,m+p,b+v).normalize();else if(e===Ks)s[5].setComponents(c,h,p,v).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+e);return this}intersectsObject(t){if(t.boundingSphere!==void 0)t.boundingSphere===null&&t.computeBoundingSphere(),vs.copy(t.boundingSphere).applyMatrix4(t.matrixWorld);else{let e=t.geometry;e.boundingSphere===null&&e.computeBoundingSphere(),vs.copy(e.boundingSphere).applyMatrix4(t.matrixWorld)}return this.intersectsSphere(vs)}intersectsSprite(t){vs.center.set(0,0,0);let e=lp.distanceTo(t.center);return vs.radius=.7071067811865476+e,vs.applyMatrix4(t.matrixWorld),this.intersectsSphere(vs)}intersectsSphere(t){let e=this.planes,n=t.center,s=-t.radius;for(let r=0;r<6;r++)if(e[r].distanceToPoint(n)<s)return!1;return!0}intersectsBox(t){let e=this.planes;for(let n=0;n<6;n++){let s=e[n];if(Za.x=s.normal.x>0?t.max.x:t.min.x,Za.y=s.normal.y>0?t.max.y:t.min.y,Za.z=s.normal.z>0?t.max.z:t.min.z,s.distanceToPoint(Za)<0)return!1}return!0}containsPoint(t){let e=this.planes;for(let n=0;n<6;n++)if(e[n].distanceToPoint(t)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}};var _o=class extends Oi{constructor(t){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new Wt(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(t)}copy(t){return super.copy(t),this.color.copy(t.color),this.map=t.map,this.alphaMap=t.alphaMap,this.size=t.size,this.sizeAttenuation=t.sizeAttenuation,this.fog=t.fog,this}},su=new de,wl=new Wr,$a=new wn,Ja=new C,qr=class extends rn{constructor(t=new ge,e=new _o){super(),this.isPoints=!0,this.type="Points",this.geometry=t,this.material=e,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(t,e){return super.copy(t,e),this.material=Array.isArray(t.material)?t.material.slice():t.material,this.geometry=t.geometry,this}intersectsFrustum(t){return t.intersectsObject(this)}raycast(t,e){let n=this.geometry,s=this.matrixWorld,r=t.params.Points.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),$a.copy(n.boundingSphere),$a.applyMatrix4(s),$a.radius+=r,t.ray.intersectsSphere($a)===!1)return;su.copy(s).invert(),wl.copy(t.ray).applyMatrix4(su);let o=r/((this.scale.x+this.scale.y+this.scale.z)/3),c=o*o,l=n.index,d=n.attributes.position;if(l!==null){let h=Math.max(0,a.start),f=Math.min(l.count,a.start+a.count);for(let g=h,x=f;g<x;g++){let p=l.getX(g);Ja.fromBufferAttribute(d,p),ru(Ja,p,c,s,t,e,this)}}else{let h=Math.max(0,a.start),f=Math.min(d.count,a.start+a.count);for(let g=h,x=f;g<x;g++)Ja.fromBufferAttribute(d,g),ru(Ja,g,c,s,t,e,this)}}updateMorphTargets(){let e=this.geometry.morphAttributes,n=Object.keys(e);if(n.length>0){let s=e[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}};function ru(i,t,e,n,s,r,a){let o=wl.distanceSqToPoint(i);if(o<e){let c=new C;wl.closestPointToPoint(i,c),c.applyMatrix4(n);let l=s.ray.origin.distanceTo(c);if(l<s.near||l>s.far)return;r.push({distance:l,distanceToRay:Math.sqrt(o),point:c,index:t,face:null,faceIndex:null,barycoord:null,object:a})}}var Yr=class extends En{constructor(t=[],e=os,n,s,r,a,o,c,l,u){super(t,e,n,s,r,a,o,c,l,u),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(t){this.image=t}},jr=class extends En{constructor(t,e,n,s,r,a,o,c,l){super(t,e,n,s,r,a,o,c,l),this.isCanvasTexture=!0,this.needsUpdate=!0}};var Ji=class extends En{constructor(t,e,n=li,s,r,a,o=nn,c=nn,l,u=pi,d=1){if(u!==pi&&u!==ls)throw new Error("THREE.DepthTexture: format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let h={width:t,height:e,depth:d};super(h,s,r,a,o,c,u,n,l),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(t){return super.copy(t),this.source=new er(Object.assign({},t.image)),this.compareFunction=t.compareFunction,this}toJSON(t){let e=super.toJSON(t);return e.compareFunction=this.compareFunction,e}},yo=class extends Ji{constructor(t,e=li,n=os,s,r,a=nn,o=nn,c,l=pi){let u={width:t,height:t,depth:1},d=[u,u,u,u,u,u];super(t,t,e,n,s,r,a,o,c,l),this.image=d,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(t){this.image=t}},Zr=class extends En{constructor(t=null){super(),this.sourceTexture=t,this.isExternalTexture=!0}copy(t){return super.copy(t),this.sourceTexture=t.sourceTexture,this}},Ce=class i extends ge{constructor(t=1,e=1,n=1,s=1,r=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:t,height:e,depth:n,widthSegments:s,heightSegments:r,depthSegments:a};let o=this;s=Math.floor(s),r=Math.floor(r),a=Math.floor(a);let c=[],l=[],u=[],d=[],h=0,f=0;g("z","y","x",-1,-1,n,e,t,a,r,0),g("z","y","x",1,-1,n,e,-t,a,r,1),g("x","z","y",1,1,t,n,e,s,a,2),g("x","z","y",1,-1,t,n,-e,s,a,3),g("x","y","z",1,-1,t,e,n,s,r,4),g("x","y","z",-1,-1,t,e,-n,s,r,5),this.setIndex(c),this.setAttribute("position",new te(l,3)),this.setAttribute("normal",new te(u,3)),this.setAttribute("uv",new te(d,2));function g(x,p,m,y,E,v,b,M,A,_,T){let P=v/A,L=b/_,F=v/2,V=b/2,I=M/2,z=A+1,q=_+1,j=0,at=0,K=new C;for(let st=0;st<q;st++){let it=st*L-V;for(let Rt=0;Rt<z;Rt++){let mt=Rt*P-F;K[x]=mt*y,K[p]=it*E,K[m]=I,l.push(K.x,K.y,K.z),K[x]=0,K[p]=0,K[m]=M>0?1:-1,u.push(K.x,K.y,K.z),d.push(Rt/A),d.push(1-st/_),j+=1}}for(let st=0;st<_;st++)for(let it=0;it<A;it++){let Rt=h+it+z*st,mt=h+it+z*(st+1),Ut=h+(it+1)+z*(st+1),Dt=h+(it+1)+z*st;c.push(Rt,mt,Dt),c.push(mt,Ut,Dt),at+=6}o.addGroup(f,at,T),f+=at,h+=j}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.width,t.height,t.depth,t.widthSegments,t.heightSegments,t.depthSegments)}};var gi=class i extends ge{constructor(t=1,e=32,n=0,s=Math.PI*2){super(),this.type="CircleGeometry",this.parameters={radius:t,segments:e,thetaStart:n,thetaLength:s},e=Math.max(3,e);let r=[],a=[],o=[],c=[],l=new C,u=new vt;a.push(0,0,0),o.push(0,0,1),c.push(.5,.5);for(let d=0,h=3;d<=e;d++,h+=3){let f=n+d/e*s;l.x=t*Math.cos(f),l.y=t*Math.sin(f),a.push(l.x,l.y,l.z),o.push(0,0,1),u.x=(a[h]/t+1)/2,u.y=(a[h+1]/t+1)/2,c.push(u.x,u.y)}for(let d=1;d<=e;d++)r.push(d,d+1,0);this.setIndex(r),this.setAttribute("position",new te(a,3)),this.setAttribute("normal",new te(o,3)),this.setAttribute("uv",new te(c,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.radius,t.segments,t.thetaStart,t.thetaLength)}},ve=class i extends ge{constructor(t=1,e=1,n=1,s=32,r=1,a=!1,o=0,c=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:t,radiusBottom:e,height:n,radialSegments:s,heightSegments:r,openEnded:a,thetaStart:o,thetaLength:c};let l=this;s=Math.floor(s),r=Math.floor(r);let u=[],d=[],h=[],f=[],g=0,x=[],p=n/2,m=0;y(),a===!1&&(t>0&&E(!0),e>0&&E(!1)),this.setIndex(u),this.setAttribute("position",new te(d,3)),this.setAttribute("normal",new te(h,3)),this.setAttribute("uv",new te(f,2));function y(){let v=new C,b=new C,M=0,A=(e-t)/n;for(let _=0;_<=r;_++){let T=[],P=_/r,L=P*(e-t)+t;for(let F=0;F<=s;F++){let V=F/s,I=V*c+o,z=Math.sin(I),q=Math.cos(I);b.x=L*z,b.y=-P*n+p,b.z=L*q,d.push(b.x,b.y,b.z),v.set(z,A,q).normalize(),h.push(v.x,v.y,v.z),f.push(V,1-P),T.push(g++)}x.push(T)}for(let _=0;_<s;_++)for(let T=0;T<r;T++){let P=x[T][_],L=x[T+1][_],F=x[T+1][_+1],V=x[T][_+1];(t>0||T!==0)&&(u.push(P,L,V),M+=3),(e>0||T!==r-1)&&(u.push(L,F,V),M+=3)}l.addGroup(m,M,0),m+=M}function E(v){let b=g,M=new vt,A=new C,_=0,T=v===!0?t:e,P=v===!0?1:-1;for(let F=1;F<=s;F++)d.push(0,p*P,0),h.push(0,P,0),f.push(.5,.5),g++;let L=g;for(let F=0;F<=s;F++){let I=F/s*c+o,z=Math.cos(I),q=Math.sin(I);A.x=T*q,A.y=p*P,A.z=T*z,d.push(A.x,A.y,A.z),h.push(0,P,0),M.x=z*.5+.5,M.y=q*.5*P+.5,f.push(M.x,M.y),g++}for(let F=0;F<s;F++){let V=b+F,I=L+F;v===!0?u.push(I,I+1,V):u.push(I+1,I,V),_+=3}l.addGroup(m,_,v===!0?1:2),m+=_}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.radiusTop,t.radiusBottom,t.height,t.radialSegments,t.heightSegments,t.openEnded,t.thetaStart,t.thetaLength)}},Ki=class i extends ve{constructor(t=1,e=1,n=32,s=1,r=!1,a=0,o=Math.PI*2){super(0,t,e,n,s,r,a,o),this.type="ConeGeometry",this.parameters={radius:t,height:e,radialSegments:n,heightSegments:s,openEnded:r,thetaStart:a,thetaLength:o}}static fromJSON(t){return new i(t.radius,t.height,t.radialSegments,t.heightSegments,t.openEnded,t.thetaStart,t.thetaLength)}},Mo=class i extends ge{constructor(t=[],e=[],n=1,s=0){super(),this.type="PolyhedronGeometry",this.parameters={vertices:t,indices:e,radius:n,detail:s};let r=[],a=[];o(s),l(n),u(),this.setAttribute("position",new te(r,3)),this.setAttribute("normal",new te(r.slice(),3)),this.setAttribute("uv",new te(a,2)),s===0?this.computeVertexNormals():this.normalizeNormals();function o(y){let E=new C,v=new C,b=new C;for(let M=0;M<e.length;M+=3)f(e[M+0],E),f(e[M+1],v),f(e[M+2],b),c(E,v,b,y)}function c(y,E,v,b){let M=b+1,A=[];for(let _=0;_<=M;_++){A[_]=[];let T=y.clone().lerp(v,_/M),P=E.clone().lerp(v,_/M),L=M-_;for(let F=0;F<=L;F++)F===0&&_===M?A[_][F]=T:A[_][F]=T.clone().lerp(P,F/L)}for(let _=0;_<M;_++)for(let T=0;T<2*(M-_)-1;T++){let P=Math.floor(T/2);T%2===0?(h(A[_][P+1]),h(A[_+1][P]),h(A[_][P])):(h(A[_][P+1]),h(A[_+1][P+1]),h(A[_+1][P]))}}function l(y){let E=new C;for(let v=0;v<r.length;v+=3)E.x=r[v+0],E.y=r[v+1],E.z=r[v+2],E.normalize().multiplyScalar(y),r[v+0]=E.x,r[v+1]=E.y,r[v+2]=E.z}function u(){let y=new C;for(let E=0;E<r.length;E+=3){y.x=r[E+0],y.y=r[E+1],y.z=r[E+2];let v=p(y)/2/Math.PI+.5,b=m(y)/Math.PI+.5;a.push(v,1-b)}g(),d()}function d(){for(let y=0;y<a.length;y+=6){let E=a[y+0],v=a[y+2],b=a[y+4],M=Math.max(E,v,b),A=Math.min(E,v,b);M>.9&&A<.1&&(E<.2&&(a[y+0]+=1),v<.2&&(a[y+2]+=1),b<.2&&(a[y+4]+=1))}}function h(y){r.push(y.x,y.y,y.z)}function f(y,E){let v=y*3;E.x=t[v+0],E.y=t[v+1],E.z=t[v+2]}function g(){let y=new C,E=new C,v=new C,b=new C,M=new vt,A=new vt,_=new vt;for(let T=0,P=0;T<r.length;T+=9,P+=6){y.set(r[T+0],r[T+1],r[T+2]),E.set(r[T+3],r[T+4],r[T+5]),v.set(r[T+6],r[T+7],r[T+8]),M.set(a[P+0],a[P+1]),A.set(a[P+2],a[P+3]),_.set(a[P+4],a[P+5]),b.copy(y).add(E).add(v).divideScalar(3);let L=p(b);x(M,P+0,y,L),x(A,P+2,E,L),x(_,P+4,v,L)}}function x(y,E,v,b){b<0&&y.x===1&&(a[E]=y.x-1),v.x===0&&v.z===0&&(a[E]=b/2/Math.PI+.5)}function p(y){return Math.atan2(y.z,-y.x)}function m(y){return Math.atan2(-y.y,Math.sqrt(y.x*y.x+y.z*y.z))}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.vertices,t.indices,t.radius,t.detail)}};var Fn=class{constructor(){this.type="Curve",this.arcLengthDivisions=200,this.needsUpdate=!1,this.cacheArcLengths=null}getPoint(){ie("Curve: .getPoint() not implemented.")}getPointAt(t,e){let n=this.getUtoTmapping(t);return this.getPoint(n,e)}getPoints(t=5){let e=[];for(let n=0;n<=t;n++)e.push(this.getPoint(n/t));return e}getSpacedPoints(t=5){let e=[];for(let n=0;n<=t;n++)e.push(this.getPointAt(n/t));return e}getLength(){let t=this.getLengths();return t[t.length-1]}getLengths(t=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===t+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;let e=[],n,s=this.getPoint(0),r=0;e.push(0);for(let a=1;a<=t;a++)n=this.getPoint(a/t),r+=n.distanceTo(s),e.push(r),s=n;return this.cacheArcLengths=e,e}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(t,e=null){let n=this.getLengths(),s=0,r=n.length,a;e?a=e:a=t*n[r-1];let o=0,c=r-1,l;for(;o<=c;)if(s=Math.floor(o+(c-o)/2),l=n[s]-a,l<0)o=s+1;else if(l>0)c=s-1;else{c=s;break}if(s=c,n[s]===a)return s/(r-1);let u=n[s],h=n[s+1]-u,f=(a-u)/h;return(s+f)/(r-1)}getTangent(t,e){let s=t-1e-4,r=t+1e-4;s<0&&(s=0),r>1&&(r=1);let a=this.getPoint(s),o=this.getPoint(r),c=e||(a.isVector2?new vt:new C);return c.copy(o).sub(a).normalize(),c}getTangentAt(t,e){let n=this.getUtoTmapping(t);return this.getTangent(n,e)}computeFrenetFrames(t,e=!1){let n=new C,s=[],r=[],a=[],o=new C,c=new de;for(let f=0;f<=t;f++){let g=f/t;s[f]=this.getTangentAt(g,new C)}r[0]=new C,a[0]=new C;let l=Number.MAX_VALUE,u=Math.abs(s[0].x),d=Math.abs(s[0].y),h=Math.abs(s[0].z);u<=l&&(l=u,n.set(1,0,0)),d<=l&&(l=d,n.set(0,1,0)),h<=l&&n.set(0,0,1),o.crossVectors(s[0],n).normalize(),r[0].crossVectors(s[0],o),a[0].crossVectors(s[0],r[0]);for(let f=1;f<=t;f++){if(r[f]=r[f-1].clone(),a[f]=a[f-1].clone(),o.crossVectors(s[f-1],s[f]),o.length()>Number.EPSILON){o.normalize();let g=Math.acos(le(s[f-1].dot(s[f]),-1,1));r[f].applyMatrix4(c.makeRotationAxis(o,g))}a[f].crossVectors(s[f],r[f])}if(e===!0){let f=Math.acos(le(r[0].dot(r[t]),-1,1));f/=t,s[0].dot(o.crossVectors(r[0],r[t]))>0&&(f=-f);for(let g=1;g<=t;g++)r[g].applyMatrix4(c.makeRotationAxis(s[g],f*g)),a[g].crossVectors(s[g],r[g])}return{tangents:s,normals:r,binormals:a}}clone(){return new this.constructor().copy(this)}copy(t){return this.arcLengthDivisions=t.arcLengthDivisions,this}toJSON(){let t={metadata:{version:4.7,type:"Curve",generator:"Curve.toJSON"}};return t.arcLengthDivisions=this.arcLengthDivisions,t.type=this.type,t}fromJSON(t){return this.arcLengthDivisions=t.arcLengthDivisions,this}},rr=class extends Fn{constructor(t=0,e=0,n=1,s=1,r=0,a=Math.PI*2,o=!1,c=0){super(),this.isEllipseCurve=!0,this.type="EllipseCurve",this.aX=t,this.aY=e,this.xRadius=n,this.yRadius=s,this.aStartAngle=r,this.aEndAngle=a,this.aClockwise=o,this.aRotation=c}getPoint(t,e=new vt){let n=e,s=Math.PI*2,r=this.aEndAngle-this.aStartAngle,a=Math.abs(r)<Number.EPSILON;for(;r<0;)r+=s;for(;r>s;)r-=s;r<Number.EPSILON&&(a?r=0:r=s),this.aClockwise===!0&&!a&&(r===s?r=-s:r=r-s);let o=this.aStartAngle+t*r,c=this.aX+this.xRadius*Math.cos(o),l=this.aY+this.yRadius*Math.sin(o);if(this.aRotation!==0){let u=Math.cos(this.aRotation),d=Math.sin(this.aRotation),h=c-this.aX,f=l-this.aY;c=h*u-f*d+this.aX,l=h*d+f*u+this.aY}return n.set(c,l)}copy(t){return super.copy(t),this.aX=t.aX,this.aY=t.aY,this.xRadius=t.xRadius,this.yRadius=t.yRadius,this.aStartAngle=t.aStartAngle,this.aEndAngle=t.aEndAngle,this.aClockwise=t.aClockwise,this.aRotation=t.aRotation,this}toJSON(){let t=super.toJSON();return t.aX=this.aX,t.aY=this.aY,t.xRadius=this.xRadius,t.yRadius=this.yRadius,t.aStartAngle=this.aStartAngle,t.aEndAngle=this.aEndAngle,t.aClockwise=this.aClockwise,t.aRotation=this.aRotation,t}fromJSON(t){return super.fromJSON(t),this.aX=t.aX,this.aY=t.aY,this.xRadius=t.xRadius,this.yRadius=t.yRadius,this.aStartAngle=t.aStartAngle,this.aEndAngle=t.aEndAngle,this.aClockwise=t.aClockwise,this.aRotation=t.aRotation,this}},So=class extends rr{constructor(t,e,n,s,r,a){super(t,e,n,n,s,r,a),this.isArcCurve=!0,this.type="ArcCurve"}};function nh(){let i=0,t=0,e=0,n=0;function s(r,a,o,c){i=r,t=o,e=-3*r+3*a-2*o-c,n=2*r-2*a+o+c}return{initCatmullRom:function(r,a,o,c,l){s(a,o,l*(o-r),l*(c-a))},initNonuniformCatmullRom:function(r,a,o,c,l,u,d){let h=(a-r)/l-(o-r)/(l+u)+(o-a)/u,f=(o-a)/u-(c-a)/(u+d)+(c-o)/d;h*=u,f*=u,s(a,o,h,f)},calc:function(r){let a=r*r,o=a*r;return i+t*r+e*a+n*o}}}var au=new C,ou=new C,ml=new nh,gl=new nh,vl=new nh,Qi=class extends Fn{constructor(t=[],e=!1,n="centripetal",s=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=t,this.closed=e,this.curveType=n,this.tension=s}getPoint(t,e=new C){let n=e,s=this.points,r=s.length,a=(r-(this.closed?0:1))*t,o=Math.floor(a),c=a-o;this.closed?o+=o>0?0:(Math.floor(Math.abs(o)/r)+1)*r:c===0&&o===r-1&&(o=r-2,c=1);let l,u;this.closed||o>0?l=s[(o-1)%r]:(ou.subVectors(s[0],s[1]).add(s[0]),l=ou);let d=s[o%r],h=s[(o+1)%r];if(this.closed||o+2<r?u=s[(o+2)%r]:(au.subVectors(s[r-1],s[r-2]).add(s[r-1]),u=au),this.curveType==="centripetal"||this.curveType==="chordal"){let f=this.curveType==="chordal"?.5:.25,g=Math.pow(l.distanceToSquared(d),f),x=Math.pow(d.distanceToSquared(h),f),p=Math.pow(h.distanceToSquared(u),f);x<1e-4&&(x=1),g<1e-4&&(g=x),p<1e-4&&(p=x),ml.initNonuniformCatmullRom(l.x,d.x,h.x,u.x,g,x,p),gl.initNonuniformCatmullRom(l.y,d.y,h.y,u.y,g,x,p),vl.initNonuniformCatmullRom(l.z,d.z,h.z,u.z,g,x,p)}else this.curveType==="catmullrom"&&(ml.initCatmullRom(l.x,d.x,h.x,u.x,this.tension),gl.initCatmullRom(l.y,d.y,h.y,u.y,this.tension),vl.initCatmullRom(l.z,d.z,h.z,u.z,this.tension));return n.set(ml.calc(c),gl.calc(c),vl.calc(c)),n}copy(t){super.copy(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let s=t.points[e];this.points.push(s.clone())}return this.closed=t.closed,this.curveType=t.curveType,this.tension=t.tension,this}toJSON(){let t=super.toJSON();t.points=[];for(let e=0,n=this.points.length;e<n;e++){let s=this.points[e];t.points.push(s.toArray())}return t.closed=this.closed,t.curveType=this.curveType,t.tension=this.tension,t}fromJSON(t){super.fromJSON(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let s=t.points[e];this.points.push(new C().fromArray(s))}return this.closed=t.closed,this.curveType=t.curveType,this.tension=t.tension,this}};function cu(i,t,e,n,s){let r=(n-t)*.5,a=(s-e)*.5,o=i*i,c=i*o;return(2*e-2*n+r+a)*c+(-3*e+3*n-2*r-a)*o+r*i+e}function hp(i,t){let e=1-i;return e*e*t}function up(i,t){return 2*(1-i)*i*t}function dp(i,t){return i*i*t}function Lr(i,t,e,n){return hp(i,t)+up(i,e)+dp(i,n)}function fp(i,t){let e=1-i;return e*e*e*t}function pp(i,t){let e=1-i;return 3*e*e*i*t}function mp(i,t){return 3*(1-i)*i*i*t}function gp(i,t){return i*i*i*t}function Dr(i,t,e,n,s){return fp(i,t)+pp(i,e)+mp(i,n)+gp(i,s)}var $r=class extends Fn{constructor(t=new vt,e=new vt,n=new vt,s=new vt){super(),this.isCubicBezierCurve=!0,this.type="CubicBezierCurve",this.v0=t,this.v1=e,this.v2=n,this.v3=s}getPoint(t,e=new vt){let n=e,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(Dr(t,s.x,r.x,a.x,o.x),Dr(t,s.y,r.y,a.y,o.y)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this.v3.copy(t.v3),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t.v3=this.v3.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this.v3.fromArray(t.v3),this}},bo=class extends Fn{constructor(t=new C,e=new C,n=new C,s=new C){super(),this.isCubicBezierCurve3=!0,this.type="CubicBezierCurve3",this.v0=t,this.v1=e,this.v2=n,this.v3=s}getPoint(t,e=new C){let n=e,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(Dr(t,s.x,r.x,a.x,o.x),Dr(t,s.y,r.y,a.y,o.y),Dr(t,s.z,r.z,a.z,o.z)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this.v3.copy(t.v3),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t.v3=this.v3.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this.v3.fromArray(t.v3),this}},Jr=class extends Fn{constructor(t=new vt,e=new vt){super(),this.isLineCurve=!0,this.type="LineCurve",this.v1=t,this.v2=e}getPoint(t,e=new vt){let n=e;return t===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(t).add(this.v1)),n}getPointAt(t,e){return this.getPoint(t,e)}getTangent(t,e=new vt){return e.subVectors(this.v2,this.v1).normalize()}getTangentAt(t,e){return this.getTangent(t,e)}copy(t){return super.copy(t),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},Eo=class extends Fn{constructor(t=new C,e=new C){super(),this.isLineCurve3=!0,this.type="LineCurve3",this.v1=t,this.v2=e}getPoint(t,e=new C){let n=e;return t===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(t).add(this.v1)),n}getPointAt(t,e){return this.getPoint(t,e)}getTangent(t,e=new C){return e.subVectors(this.v2,this.v1).normalize()}getTangentAt(t,e){return this.getTangent(t,e)}copy(t){return super.copy(t),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},Kr=class extends Fn{constructor(t=new vt,e=new vt,n=new vt){super(),this.isQuadraticBezierCurve=!0,this.type="QuadraticBezierCurve",this.v0=t,this.v1=e,this.v2=n}getPoint(t,e=new vt){let n=e,s=this.v0,r=this.v1,a=this.v2;return n.set(Lr(t,s.x,r.x,a.x),Lr(t,s.y,r.y,a.y)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},wo=class extends Fn{constructor(t=new C,e=new C,n=new C){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=t,this.v1=e,this.v2=n}getPoint(t,e=new C){let n=e,s=this.v0,r=this.v1,a=this.v2;return n.set(Lr(t,s.x,r.x,a.x),Lr(t,s.y,r.y,a.y),Lr(t,s.z,r.z,a.z)),n}copy(t){return super.copy(t),this.v0.copy(t.v0),this.v1.copy(t.v1),this.v2.copy(t.v2),this}toJSON(){let t=super.toJSON();return t.v0=this.v0.toArray(),t.v1=this.v1.toArray(),t.v2=this.v2.toArray(),t}fromJSON(t){return super.fromJSON(t),this.v0.fromArray(t.v0),this.v1.fromArray(t.v1),this.v2.fromArray(t.v2),this}},Qr=class extends Fn{constructor(t=[]){super(),this.isSplineCurve=!0,this.type="SplineCurve",this.points=t}getPoint(t,e=new vt){let n=e,s=this.points,r=(s.length-1)*t,a=Math.floor(r),o=r-a,c=s[a===0?a:a-1],l=s[a],u=s[a>s.length-2?s.length-1:a+1],d=s[a>s.length-3?s.length-1:a+2];return n.set(cu(o,c.x,l.x,u.x,d.x),cu(o,c.y,l.y,u.y,d.y)),n}copy(t){super.copy(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let s=t.points[e];this.points.push(s.clone())}return this}toJSON(){let t=super.toJSON();t.points=[];for(let e=0,n=this.points.length;e<n;e++){let s=this.points[e];t.points.push(s.toArray())}return t}fromJSON(t){super.fromJSON(t),this.points=[];for(let e=0,n=t.points.length;e<n;e++){let s=t.points[e];this.points.push(new vt().fromArray(s))}return this}},Tl=Object.freeze({__proto__:null,ArcCurve:So,CatmullRomCurve3:Qi,CubicBezierCurve:$r,CubicBezierCurve3:bo,EllipseCurve:rr,LineCurve:Jr,LineCurve3:Eo,QuadraticBezierCurve:Kr,QuadraticBezierCurve3:wo,SplineCurve:Qr}),To=class extends Fn{constructor(){super(),this.type="CurvePath",this.curves=[],this.autoClose=!1}add(t){this.curves.push(t)}closePath(){let t=this.curves[0].getPoint(0),e=this.curves[this.curves.length-1].getPoint(1);if(!t.equals(e)){let n=t.isVector2===!0?"LineCurve":"LineCurve3";this.curves.push(new Tl[n](e,t))}return this}getPoint(t,e){let n=t*this.getLength(),s=this.getCurveLengths(),r=0;for(;r<s.length;){if(s[r]>=n){let a=s[r]-n,o=this.curves[r],c=o.getLength(),l=c===0?0:1-a/c;return o.getPointAt(l,e)}r++}return null}getLength(){let t=this.getCurveLengths();return t[t.length-1]}updateArcLengths(){this.needsUpdate=!0,this.cacheLengths=null,this.getCurveLengths()}getCurveLengths(){if(this.cacheLengths&&this.cacheLengths.length===this.curves.length)return this.cacheLengths;let t=[],e=0;for(let n=0,s=this.curves.length;n<s;n++)e+=this.curves[n].getLength(),t.push(e);return this.cacheLengths=t,t}getSpacedPoints(t=40){let e=[];for(let n=0;n<=t;n++)e.push(this.getPoint(n/t));return this.autoClose&&e.push(e[0]),e}getPoints(t=12){let e=[],n;for(let s=0,r=this.curves;s<r.length;s++){let a=r[s],o=a.isEllipseCurve?t*2:a.isLineCurve||a.isLineCurve3?1:a.isSplineCurve?t*a.points.length:t,c=a.getPoints(o);for(let l=0;l<c.length;l++){let u=c[l];n&&n.equals(u)||(e.push(u),n=u)}}return this.autoClose&&e.length>1&&!e[e.length-1].equals(e[0])&&e.push(e[0]),e}copy(t){super.copy(t),this.curves=[];for(let e=0,n=t.curves.length;e<n;e++){let s=t.curves[e];this.curves.push(s.clone())}return this.autoClose=t.autoClose,this}toJSON(){let t=super.toJSON();t.autoClose=this.autoClose,t.curves=[];for(let e=0,n=this.curves.length;e<n;e++){let s=this.curves[e];t.curves.push(s.toJSON())}return t}fromJSON(t){super.fromJSON(t),this.autoClose=t.autoClose,this.curves=[];for(let e=0,n=t.curves.length;e<n;e++){let s=t.curves[e];this.curves.push(new Tl[s.type]().fromJSON(s))}return this}},ta=class extends To{constructor(t){super(),this.type="Path",this.currentPoint=new vt,t&&this.setFromPoints(t)}setFromPoints(t){this.moveTo(t[0].x,t[0].y);for(let e=1,n=t.length;e<n;e++)this.lineTo(t[e].x,t[e].y);return this}moveTo(t,e){return this.currentPoint.set(t,e),this}lineTo(t,e){let n=new Jr(this.currentPoint.clone(),new vt(t,e));return this.curves.push(n),this.currentPoint.set(t,e),this}quadraticCurveTo(t,e,n,s){let r=new Kr(this.currentPoint.clone(),new vt(t,e),new vt(n,s));return this.curves.push(r),this.currentPoint.set(n,s),this}bezierCurveTo(t,e,n,s,r,a){let o=new $r(this.currentPoint.clone(),new vt(t,e),new vt(n,s),new vt(r,a));return this.curves.push(o),this.currentPoint.set(r,a),this}splineThru(t){let e=[this.currentPoint.clone()].concat(t),n=new Qr(e);return this.curves.push(n),this.currentPoint.copy(t[t.length-1]),this}arc(t,e,n,s,r,a){let o=this.currentPoint.x,c=this.currentPoint.y;return this.absarc(t+o,e+c,n,s,r,a),this}absarc(t,e,n,s,r,a){return this.absellipse(t,e,n,n,s,r,a),this}ellipse(t,e,n,s,r,a,o,c){let l=this.currentPoint.x,u=this.currentPoint.y;return this.absellipse(t+l,e+u,n,s,r,a,o,c),this}absellipse(t,e,n,s,r,a,o,c){let l=new rr(t,e,n,s,r,a,o,c);if(this.curves.length>0){let d=l.getPoint(0);d.equals(this.currentPoint)||this.lineTo(d.x,d.y)}this.curves.push(l);let u=l.getPoint(1);return this.currentPoint.copy(u),this}copy(t){return super.copy(t),this.currentPoint.copy(t.currentPoint),this}toJSON(){let t=super.toJSON();return t.currentPoint=this.currentPoint.toArray(),t}fromJSON(t){return super.fromJSON(t),this.currentPoint.fromArray(t.currentPoint),this}},vi=class extends ta{constructor(t){super(t),this.uuid=fi(),this.type="Shape",this.holes=[]}getPointsHoles(t){let e=[];for(let n=0,s=this.holes.length;n<s;n++)e[n]=this.holes[n].getPoints(t);return e}extractPoints(t){return{shape:this.getPoints(t),holes:this.getPointsHoles(t)}}copy(t){super.copy(t),this.holes=[];for(let e=0,n=t.holes.length;e<n;e++){let s=t.holes[e];this.holes.push(s.clone())}return this}toJSON(){let t=super.toJSON();t.uuid=this.uuid,t.holes=[];for(let e=0,n=this.holes.length;e<n;e++){let s=this.holes[e];t.holes.push(s.toJSON())}return t}fromJSON(t){super.fromJSON(t),this.uuid=t.uuid,this.holes=[];for(let e=0,n=t.holes.length;e<n;e++){let s=t.holes[e];this.holes.push(new ta().fromJSON(s))}return this}};function vp(i,t,e=2){let n=t&&t.length,s=n?t[0]*e:i.length,r=sd(i,0,s,e,!0),a=[];if(!r||r.next===r.prev)return a;let o,c,l;if(n&&(r=Sp(i,t,r,e)),i.length>80*e){o=i[0],c=i[1];let u=o,d=c;for(let h=e;h<s;h+=e){let f=i[h],g=i[h+1];f<o&&(o=f),g<c&&(c=g),f>u&&(u=f),g>d&&(d=g)}l=Math.max(u-o,d-c),l=l!==0?32767/l:0}return ea(r,a,e,o,c,l,0),a}function sd(i,t,e,n,s){let r;if(s===Dp(i,t,e,n)>0)for(let a=t;a<e;a+=n)r=lu(a/n|0,i[a],i[a+1],r);else for(let a=e-n;a>=t;a-=n)r=lu(a/n|0,i[a],i[a+1],r);return r&&ar(r,r.next)&&(ia(r),r=r.next),r}function Ms(i,t){if(!i)return i;t||(t=i);let e=i,n;do if(n=!1,!e.steiner&&(ar(e,e.next)||Xe(e.prev,e,e.next)===0)){if(ia(e),e=t=e.prev,e===e.next)break;n=!0}else e=e.next;while(n||e!==t);return t}function ea(i,t,e,n,s,r,a){if(!i)return;!a&&r&&Ap(i,n,s,r);let o=i;for(;i.prev!==i.next;){let c=i.prev,l=i.next;if(r?_p(i,n,s,r):xp(i)){t.push(c.i,i.i,l.i),ia(i),i=l.next,o=l.next;continue}if(i=l,i===o){a?a===1?(i=yp(Ms(i),t),ea(i,t,e,n,s,r,2)):a===2&&Mp(i,t,e,n,s,r):ea(Ms(i),t,e,n,s,r,1);break}}}function xp(i){let t=i.prev,e=i,n=i.next;if(Xe(t,e,n)>=0)return!1;let s=t.x,r=e.x,a=n.x,o=t.y,c=e.y,l=n.y,u=Math.min(s,r,a),d=Math.min(o,c,l),h=Math.max(s,r,a),f=Math.max(o,c,l),g=n.next;for(;g!==t;){if(g.x>=u&&g.x<=h&&g.y>=d&&g.y<=f&&Cr(s,o,r,c,a,l,g.x,g.y)&&Xe(g.prev,g,g.next)>=0)return!1;g=g.next}return!0}function _p(i,t,e,n){let s=i.prev,r=i,a=i.next;if(Xe(s,r,a)>=0)return!1;let o=s.x,c=r.x,l=a.x,u=s.y,d=r.y,h=a.y,f=Math.min(o,c,l),g=Math.min(u,d,h),x=Math.max(o,c,l),p=Math.max(u,d,h),m=Al(f,g,t,e,n),y=Al(x,p,t,e,n),E=i.prevZ,v=i.nextZ;for(;E&&E.z>=m&&v&&v.z<=y;){if(E.x>=f&&E.x<=x&&E.y>=g&&E.y<=p&&E!==s&&E!==a&&Cr(o,u,c,d,l,h,E.x,E.y)&&Xe(E.prev,E,E.next)>=0||(E=E.prevZ,v.x>=f&&v.x<=x&&v.y>=g&&v.y<=p&&v!==s&&v!==a&&Cr(o,u,c,d,l,h,v.x,v.y)&&Xe(v.prev,v,v.next)>=0))return!1;v=v.nextZ}for(;E&&E.z>=m;){if(E.x>=f&&E.x<=x&&E.y>=g&&E.y<=p&&E!==s&&E!==a&&Cr(o,u,c,d,l,h,E.x,E.y)&&Xe(E.prev,E,E.next)>=0)return!1;E=E.prevZ}for(;v&&v.z<=y;){if(v.x>=f&&v.x<=x&&v.y>=g&&v.y<=p&&v!==s&&v!==a&&Cr(o,u,c,d,l,h,v.x,v.y)&&Xe(v.prev,v,v.next)>=0)return!1;v=v.nextZ}return!0}function yp(i,t){let e=i;do{let n=e.prev,s=e.next.next;!ar(n,s)&&ad(n,e,e.next,s)&&na(n,s)&&na(s,n)&&(t.push(n.i,e.i,s.i),ia(e),ia(e.next),e=i=s),e=e.next}while(e!==i);return Ms(e)}function Mp(i,t,e,n,s,r){let a=i;do{let o=a.next.next;for(;o!==a.prev;){if(a.i!==o.i&&Pp(a,o)){let c=od(a,o);a=Ms(a,a.next),c=Ms(c,c.next),ea(a,t,e,n,s,r,0),ea(c,t,e,n,s,r,0);return}o=o.next}a=a.next}while(a!==i)}function Sp(i,t,e,n){let s=[];for(let r=0,a=t.length;r<a;r++){let o=t[r]*n,c=r<a-1?t[r+1]*n:i.length,l=sd(i,o,c,n,!1);l===l.next&&(l.steiner=!0),s.push(Cp(l))}s.sort(bp);for(let r=0;r<s.length;r++)e=Ep(s[r],e);return e}function bp(i,t){let e=i.x-t.x;if(e===0&&(e=i.y-t.y,e===0)){let n=(i.next.y-i.y)/(i.next.x-i.x),s=(t.next.y-t.y)/(t.next.x-t.x);e=n-s}return e}function Ep(i,t){let e=wp(i,t);if(!e)return t;let n=od(e,i);return Ms(n,n.next),Ms(e,e.next)}function wp(i,t){let e=t,n=i.x,s=i.y,r=-1/0,a;if(ar(i,e))return e;do{if(ar(i,e.next))return e.next;if(s<=e.y&&s>=e.next.y&&e.next.y!==e.y){let d=e.x+(s-e.y)*(e.next.x-e.x)/(e.next.y-e.y);if(d<=n&&d>r&&(r=d,a=e.x<e.next.x?e:e.next,d===n))return a}e=e.next}while(e!==t);if(!a)return null;let o=a,c=a.x,l=a.y,u=1/0;e=a;do{if(n>=e.x&&e.x>=c&&n!==e.x&&rd(s<l?n:r,s,c,l,s<l?r:n,s,e.x,e.y)){let d=Math.abs(s-e.y)/(n-e.x);na(e,i)&&(d<u||d===u&&(e.x>a.x||e.x===a.x&&Tp(a,e)))&&(a=e,u=d)}e=e.next}while(e!==o);return a}function Tp(i,t){return Xe(i.prev,i,t.prev)<0&&Xe(t.next,i,i.next)<0}function Ap(i,t,e,n){let s=i;do s.z===0&&(s.z=Al(s.x,s.y,t,e,n)),s.prevZ=s.prev,s.nextZ=s.next,s=s.next;while(s!==i);s.prevZ.nextZ=null,s.prevZ=null,Rp(s)}function Rp(i){let t,e=1;do{let n=i,s;i=null;let r=null;for(t=0;n;){t++;let a=n,o=0;for(let l=0;l<e&&(o++,a=a.nextZ,!!a);l++);let c=e;for(;o>0||c>0&&a;)o!==0&&(c===0||!a||n.z<=a.z)?(s=n,n=n.nextZ,o--):(s=a,a=a.nextZ,c--),r?r.nextZ=s:i=s,s.prevZ=r,r=s;n=a}r.nextZ=null,e*=2}while(t>1);return i}function Al(i,t,e,n,s){return i=(i-e)*s|0,t=(t-n)*s|0,i=(i|i<<8)&16711935,i=(i|i<<4)&252645135,i=(i|i<<2)&858993459,i=(i|i<<1)&1431655765,t=(t|t<<8)&16711935,t=(t|t<<4)&252645135,t=(t|t<<2)&858993459,t=(t|t<<1)&1431655765,i|t<<1}function Cp(i){let t=i,e=i;do(t.x<e.x||t.x===e.x&&t.y<e.y)&&(e=t),t=t.next;while(t!==i);return e}function rd(i,t,e,n,s,r,a,o){return(s-a)*(t-o)>=(i-a)*(r-o)&&(i-a)*(n-o)>=(e-a)*(t-o)&&(e-a)*(r-o)>=(s-a)*(n-o)}function Cr(i,t,e,n,s,r,a,o){return!(i===a&&t===o)&&rd(i,t,e,n,s,r,a,o)}function Pp(i,t){return i.next.i!==t.i&&i.prev.i!==t.i&&!Ip(i,t)&&(na(i,t)&&na(t,i)&&Lp(i,t)&&(Xe(i.prev,i,t.prev)||Xe(i,t.prev,t))||ar(i,t)&&Xe(i.prev,i,i.next)>0&&Xe(t.prev,t,t.next)>0)}function Xe(i,t,e){return(t.y-i.y)*(e.x-t.x)-(t.x-i.x)*(e.y-t.y)}function ar(i,t){return i.x===t.x&&i.y===t.y}function ad(i,t,e,n){let s=Qa(Xe(i,t,e)),r=Qa(Xe(i,t,n)),a=Qa(Xe(e,n,i)),o=Qa(Xe(e,n,t));return!!(s!==r&&a!==o||s===0&&Ka(i,e,t)||r===0&&Ka(i,n,t)||a===0&&Ka(e,i,n)||o===0&&Ka(e,t,n))}function Ka(i,t,e){return t.x<=Math.max(i.x,e.x)&&t.x>=Math.min(i.x,e.x)&&t.y<=Math.max(i.y,e.y)&&t.y>=Math.min(i.y,e.y)}function Qa(i){return i>0?1:i<0?-1:0}function Ip(i,t){let e=i;do{if(e.i!==i.i&&e.next.i!==i.i&&e.i!==t.i&&e.next.i!==t.i&&ad(e,e.next,i,t))return!0;e=e.next}while(e!==i);return!1}function na(i,t){return Xe(i.prev,i,i.next)<0?Xe(i,t,i.next)>=0&&Xe(i,i.prev,t)>=0:Xe(i,t,i.prev)<0||Xe(i,i.next,t)<0}function Lp(i,t){let e=i,n=!1,s=(i.x+t.x)/2,r=(i.y+t.y)/2;do e.y>r!=e.next.y>r&&e.next.y!==e.y&&s<(e.next.x-e.x)*(r-e.y)/(e.next.y-e.y)+e.x&&(n=!n),e=e.next;while(e!==i);return n}function od(i,t){let e=Rl(i.i,i.x,i.y),n=Rl(t.i,t.x,t.y),s=i.next,r=t.prev;return i.next=t,t.prev=i,e.next=s,s.prev=e,n.next=e,e.prev=n,r.next=n,n.prev=r,n}function lu(i,t,e,n){let s=Rl(i,t,e);return n?(s.next=n.next,s.prev=n,n.next.prev=s,n.next=s):(s.prev=s,s.next=s),s}function ia(i){i.next.prev=i.prev,i.prev.next=i.next,i.prevZ&&(i.prevZ.nextZ=i.nextZ),i.nextZ&&(i.nextZ.prevZ=i.prevZ)}function Rl(i,t,e){return{i,x:t,y:e,prev:null,next:null,z:0,prevZ:null,nextZ:null,steiner:!1}}function Dp(i,t,e,n){let s=0;for(let r=t,a=e-n;r<e;r+=n)s+=(i[a]-i[r])*(i[r+1]+i[a+1]),a=r;return s}var Cl=class{static triangulate(t,e,n=2){return vp(t,e,n)}},xs=class i{static area(t){let e=t.length,n=0;for(let s=e-1,r=0;r<e;s=r++)n+=t[s].x*t[r].y-t[r].x*t[s].y;return n*.5}static isClockWise(t){return i.area(t)<0}static triangulateShape(t,e){let n=[],s=[],r=[];hu(t),uu(n,t);let a=t.length;e.forEach(hu);for(let c=0;c<e.length;c++)s.push(a),a+=e[c].length,uu(n,e[c]);let o=Cl.triangulate(n,s);for(let c=0;c<o.length;c+=3)r.push(o.slice(c,c+3));return r}};function hu(i){let t=i.length;t>2&&i[t-1].equals(i[0])&&i.pop()}function uu(i,t){for(let e=0;e<t.length;e++)i.push(t[e].x),i.push(t[e].y)}var Bi=class i extends ge{constructor(t=new vi([new vt(.5,.5),new vt(-.5,.5),new vt(-.5,-.5),new vt(.5,-.5)]),e={}){super(),this.type="ExtrudeGeometry",this.parameters={shapes:t,options:e},t=Array.isArray(t)?t:[t];let n=this,s=[],r=[];for(let o=0,c=t.length;o<c;o++){let l=t[o];a(l)}this.setAttribute("position",new te(s,3)),this.setAttribute("uv",new te(r,2)),this.computeVertexNormals();function a(o){let c=[],l=e.curveSegments!==void 0?e.curveSegments:12,u=e.steps!==void 0?e.steps:1,d=e.depth!==void 0?e.depth:1,h=e.bevelEnabled!==void 0?e.bevelEnabled:!0,f=e.bevelThickness!==void 0?e.bevelThickness:.2,g=e.bevelSize!==void 0?e.bevelSize:f-.1,x=e.bevelOffset!==void 0?e.bevelOffset:0,p=e.bevelSegments!==void 0?e.bevelSegments:3,m=e.extrudePath,y=e.UVGenerator!==void 0?e.UVGenerator:Up,E,v=!1,b,M,A,_;if(m){E=m.getSpacedPoints(u),v=!0,h=!1;let X=m.isCatmullRomCurve3?m.closed:!1;b=m.computeFrenetFrames(u,X),M=new C,A=new C,_=new C}h||(p=0,f=0,g=0,x=0);let T=o.extractPoints(l),P=T.shape,L=T.holes;if(!xs.isClockWise(P)){P=P.reverse();for(let X=0,tt=L.length;X<tt;X++){let G=L[X];xs.isClockWise(G)&&(L[X]=G.reverse())}}function V(X){let G=10000000000000001e-36,et=X[0];for(let gt=1;gt<=X.length;gt++){let Bt=gt%X.length,bt=X[Bt],jt=bt.x-et.x,ne=bt.y-et.y,U=jt*jt+ne*ne,Ee=Math.max(Math.abs(bt.x),Math.abs(bt.y),Math.abs(et.x),Math.abs(et.y)),se=G*Ee*Ee;if(U<=se){X.splice(Bt,1),gt--;continue}et=bt}}V(P),L.forEach(V);let I=L.length,z=P;for(let X=0;X<I;X++){let tt=L[X];P=P.concat(tt)}function q(X,tt,G){return tt||ae("ExtrudeGeometry: vec does not exist"),X.clone().addScaledVector(tt,G)}let j=P.length;function at(X,tt,G){let et,gt,Bt,bt=X.x-tt.x,jt=X.y-tt.y,ne=G.x-X.x,U=G.y-X.y,Ee=bt*bt+jt*jt,se=bt*U-jt*ne;if(Math.abs(se)>Number.EPSILON){let R=Math.sqrt(Ee),S=Math.sqrt(ne*ne+U*U),H=tt.x-jt/R,Y=tt.y+bt/R,rt=G.x-U/S,_t=G.y+ne/S,Et=((rt-H)*U-(_t-Y)*ne)/(bt*U-jt*ne);et=H+bt*Et-X.x,gt=Y+jt*Et-X.y;let nt=et*et+gt*gt;if(nt<=2)return new vt(et,gt);Bt=Math.sqrt(nt/2)}else{let R=!1;bt>Number.EPSILON?ne>Number.EPSILON&&(R=!0):bt<-Number.EPSILON?ne<-Number.EPSILON&&(R=!0):Math.sign(jt)===Math.sign(U)&&(R=!0),R?(et=-jt,gt=bt,Bt=Math.sqrt(Ee)):(et=bt,gt=jt,Bt=Math.sqrt(Ee/2))}return new vt(et/Bt,gt/Bt)}let K=[];for(let X=0,tt=z.length,G=tt-1,et=X+1;X<tt;X++,G++,et++)G===tt&&(G=0),et===tt&&(et=0),K[X]=at(z[X],z[G],z[et]);let st=[],it,Rt=K.concat();for(let X=0,tt=I;X<tt;X++){let G=L[X];it=[];for(let et=0,gt=G.length,Bt=gt-1,bt=et+1;et<gt;et++,Bt++,bt++)Bt===gt&&(Bt=0),bt===gt&&(bt=0),it[et]=at(G[et],G[Bt],G[bt]);st.push(it),Rt=Rt.concat(it)}let mt;if(p===0)mt=xs.triangulateShape(z,L);else{let X=[],tt=[];for(let G=0;G<p;G++){let et=G/p,gt=f*Math.cos(et*Math.PI/2),Bt=g*Math.sin(et*Math.PI/2)+x;for(let bt=0,jt=z.length;bt<jt;bt++){let ne=q(z[bt],K[bt],Bt);dt(ne.x,ne.y,-gt),et===0&&X.push(ne)}for(let bt=0,jt=I;bt<jt;bt++){let ne=L[bt];it=st[bt];let U=[];for(let Ee=0,se=ne.length;Ee<se;Ee++){let R=q(ne[Ee],it[Ee],Bt);dt(R.x,R.y,-gt),et===0&&U.push(R)}et===0&&tt.push(U)}}mt=xs.triangulateShape(X,tt)}let Ut=mt.length,Dt=g+x;for(let X=0;X<j;X++){let tt=h?q(P[X],Rt[X],Dt):P[X];v?(A.copy(b.normals[0]).multiplyScalar(tt.x),M.copy(b.binormals[0]).multiplyScalar(tt.y),_.copy(E[0]).add(A).add(M),dt(_.x,_.y,_.z)):dt(tt.x,tt.y,0)}for(let X=1;X<=u;X++)for(let tt=0;tt<j;tt++){let G=h?q(P[tt],Rt[tt],Dt):P[tt];v?(A.copy(b.normals[X]).multiplyScalar(G.x),M.copy(b.binormals[X]).multiplyScalar(G.y),_.copy(E[X]).add(A).add(M),dt(_.x,_.y,_.z)):dt(G.x,G.y,d/u*X)}for(let X=p-1;X>=0;X--){let tt=X/p,G=f*Math.cos(tt*Math.PI/2),et=g*Math.sin(tt*Math.PI/2)+x;for(let gt=0,Bt=z.length;gt<Bt;gt++){let bt=q(z[gt],K[gt],et);dt(bt.x,bt.y,d+G)}for(let gt=0,Bt=L.length;gt<Bt;gt++){let bt=L[gt];it=st[gt];for(let jt=0,ne=bt.length;jt<ne;jt++){let U=q(bt[jt],it[jt],et);v?dt(U.x,U.y+E[u-1].y,E[u-1].x+G):dt(U.x,U.y,d+G)}}}ft(),N();function ft(){let X=s.length/3;if(h){let tt=0,G=j*tt;for(let et=0;et<Ut;et++){let gt=mt[et];St(gt[2]+G,gt[1]+G,gt[0]+G)}tt=u+p*2,G=j*tt;for(let et=0;et<Ut;et++){let gt=mt[et];St(gt[0]+G,gt[1]+G,gt[2]+G)}}else{for(let tt=0;tt<Ut;tt++){let G=mt[tt];St(G[2],G[1],G[0])}for(let tt=0;tt<Ut;tt++){let G=mt[tt];St(G[0]+j*u,G[1]+j*u,G[2]+j*u)}}n.addGroup(X,s.length/3-X,0)}function N(){let X=s.length/3,tt=0;k(z,tt),tt+=z.length;for(let G=0,et=L.length;G<et;G++){let gt=L[G];k(gt,tt),tt+=gt.length}n.addGroup(X,s.length/3-X,1)}function k(X,tt){let G=X.length;for(;--G>=0;){let et=G,gt=G-1;gt<0&&(gt=X.length-1);for(let Bt=0,bt=u+p*2;Bt<bt;Bt++){let jt=j*Bt,ne=j*(Bt+1),U=tt+et+jt,Ee=tt+gt+jt,se=tt+gt+ne,R=tt+et+ne;Mt(U,Ee,se,R)}}}function dt(X,tt,G){c.push(X),c.push(tt),c.push(G)}function St(X,tt,G){Ft(X),Ft(tt),Ft(G);let et=s.length/3,gt=y.generateTopUV(n,s,et-3,et-2,et-1);xt(gt[0]),xt(gt[1]),xt(gt[2])}function Mt(X,tt,G,et){Ft(X),Ft(tt),Ft(et),Ft(tt),Ft(G),Ft(et);let gt=s.length/3,Bt=y.generateSideWallUV(n,s,gt-6,gt-3,gt-2,gt-1);xt(Bt[0]),xt(Bt[1]),xt(Bt[3]),xt(Bt[1]),xt(Bt[2]),xt(Bt[3])}function Ft(X){s.push(c[X*3+0]),s.push(c[X*3+1]),s.push(c[X*3+2])}function xt(X){r.push(X.x),r.push(X.y)}}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}toJSON(){let t=super.toJSON(),e=this.parameters.shapes,n=this.parameters.options;return Np(e,n,t)}static fromJSON(t,e){let n=[];for(let r=0,a=t.shapes.length;r<a;r++){let o=e[t.shapes[r]];n.push(o)}let s=t.options.extrudePath;return s!==void 0&&(t.options.extrudePath=new Tl[s.type]().fromJSON(s)),new i(n,t.options)}},Up={generateTopUV:function(i,t,e,n,s){let r=t[e*3],a=t[e*3+1],o=t[n*3],c=t[n*3+1],l=t[s*3],u=t[s*3+1];return[new vt(r,a),new vt(o,c),new vt(l,u)]},generateSideWallUV:function(i,t,e,n,s,r){let a=t[e*3],o=t[e*3+1],c=t[e*3+2],l=t[n*3],u=t[n*3+1],d=t[n*3+2],h=t[s*3],f=t[s*3+1],g=t[s*3+2],x=t[r*3],p=t[r*3+1],m=t[r*3+2];return Math.abs(o-u)<Math.abs(a-l)?[new vt(a,1-c),new vt(l,1-d),new vt(h,1-g),new vt(x,1-m)]:[new vt(o,1-c),new vt(u,1-d),new vt(f,1-g),new vt(p,1-m)]}};function Np(i,t,e){if(e.shapes=[],Array.isArray(i))for(let n=0,s=i.length;n<s;n++){let r=i[n];e.shapes.push(r.uuid)}else e.shapes.push(i.uuid);return e.options=Object.assign({},t),t.extrudePath!==void 0&&(e.options.extrudePath=t.extrudePath.toJSON()),e}var or=class i extends Mo{constructor(t=1,e=0){let n=(1+Math.sqrt(5))/2,s=[-1,n,0,1,n,0,-1,-n,0,1,-n,0,0,-1,n,0,1,n,0,-1,-n,0,1,-n,n,0,-1,n,0,1,-n,0,-1,-n,0,1],r=[0,11,5,0,5,1,0,1,7,0,7,10,0,10,11,1,5,9,5,11,4,11,10,2,10,7,6,7,1,8,3,9,4,3,4,2,3,2,6,3,6,8,3,8,9,4,9,5,2,4,11,6,2,10,8,6,7,9,8,1];super(s,r,t,e),this.type="IcosahedronGeometry",this.parameters={radius:t,detail:e}}static fromJSON(t){return new i(t.radius,t.detail)}},xi=class i extends ge{constructor(t=[new vt(0,-.5),new vt(.5,0),new vt(0,.5)],e=12,n=0,s=Math.PI*2){super(),this.type="LatheGeometry",this.parameters={points:t,segments:e,phiStart:n,phiLength:s},e=Math.floor(e),s=le(s,0,Math.PI*2);let r=[],a=[],o=[],c=[],l=[],u=1/e,d=new C,h=new vt,f=new C,g=new C,x=new C,p=0,m=0;for(let y=0;y<=t.length-1;y++)switch(y){case 0:p=t[y+1].x-t[y].x,m=t[y+1].y-t[y].y,f.x=m*1,f.y=-p,f.z=m*0,x.copy(f),f.normalize(),c.push(f.x,f.y,f.z);break;case t.length-1:c.push(x.x,x.y,x.z);break;default:p=t[y+1].x-t[y].x,m=t[y+1].y-t[y].y,f.x=m*1,f.y=-p,f.z=m*0,g.copy(f),f.x+=x.x,f.y+=x.y,f.z+=x.z,f.normalize(),c.push(f.x,f.y,f.z),x.copy(g)}for(let y=0;y<=e;y++){let E=n+y*u*s,v=Math.sin(E),b=Math.cos(E);for(let M=0;M<=t.length-1;M++){d.x=t[M].x*v,d.y=t[M].y,d.z=t[M].x*b,a.push(d.x,d.y,d.z),h.x=y/e,h.y=M/(t.length-1),o.push(h.x,h.y);let A=c[3*M+0]*v,_=c[3*M+1],T=c[3*M+0]*b;l.push(A,_,T)}}for(let y=0;y<e;y++)for(let E=0;E<t.length-1;E++){let v=E+y*t.length,b=v,M=v+t.length,A=v+t.length+1,_=v+1;r.push(b,M,_),r.push(A,_,M)}this.setIndex(r),this.setAttribute("position",new te(a,3)),this.setAttribute("uv",new te(o,2)),this.setAttribute("normal",new te(l,3))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.points,t.segments,t.phiStart,t.phiLength)}};var je=class i extends ge{constructor(t=1,e=1,n=1,s=1){super(),this.type="PlaneGeometry",this.parameters={width:t,height:e,widthSegments:n,heightSegments:s};let r=t/2,a=e/2,o=Math.floor(n),c=Math.floor(s),l=o+1,u=c+1,d=t/o,h=e/c,f=[],g=[],x=[],p=[];for(let m=0;m<u;m++){let y=m*h-a;for(let E=0;E<l;E++){let v=E*d-r;g.push(v,-y,0),x.push(0,0,1),p.push(E/o),p.push(1-m/c)}}for(let m=0;m<c;m++)for(let y=0;y<o;y++){let E=y+l*m,v=y+l*(m+1),b=y+1+l*(m+1),M=y+1+l*m;f.push(E,v,M),f.push(v,b,M)}this.setIndex(f),this.setAttribute("position",new te(g,3)),this.setAttribute("normal",new te(x,3)),this.setAttribute("uv",new te(p,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.width,t.height,t.widthSegments,t.heightSegments)}},sa=class i extends ge{constructor(t=.5,e=1,n=32,s=1,r=0,a=Math.PI*2){super(),this.type="RingGeometry",this.parameters={innerRadius:t,outerRadius:e,thetaSegments:n,phiSegments:s,thetaStart:r,thetaLength:a},n=Math.max(3,n),s=Math.max(1,s);let o=[],c=[],l=[],u=[],d=t,h=(e-t)/s,f=new C,g=new vt;for(let x=0;x<=s;x++){for(let p=0;p<=n;p++){let m=r+p/n*a;f.x=d*Math.cos(m),f.y=d*Math.sin(m),c.push(f.x,f.y,f.z),l.push(0,0,1),g.x=(f.x/e+1)/2,g.y=(f.y/e+1)/2,u.push(g.x,g.y)}d+=h}for(let x=0;x<s;x++){let p=x*(n+1);for(let m=0;m<n;m++){let y=m+p,E=y,v=y+n+1,b=y+n+2,M=y+1;o.push(E,v,M),o.push(v,b,M)}}this.setIndex(o),this.setAttribute("position",new te(c,3)),this.setAttribute("normal",new te(l,3)),this.setAttribute("uv",new te(u,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.innerRadius,t.outerRadius,t.thetaSegments,t.phiSegments,t.thetaStart,t.thetaLength)}};var Xn=class i extends ge{constructor(t=1,e=32,n=16,s=0,r=Math.PI*2,a=0,o=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:t,widthSegments:e,heightSegments:n,phiStart:s,phiLength:r,thetaStart:a,thetaLength:o},e=Math.max(3,Math.floor(e)),n=Math.max(2,Math.floor(n));let c=Math.min(a+o,Math.PI),l=0,u=[],d=new C,h=new C,f=[],g=[],x=[],p=[];for(let m=0;m<=n;m++){let y=[],E=m/n,v=a+E*o,b=t*Math.cos(v),M=Math.sqrt(t*t-b*b),A=0;m===0&&a===0?A=.5/e:m===n&&c===Math.PI&&(A=-.5/e);for(let _=0;_<=e;_++){let T=_/e,P=s+T*r;d.x=-M*Math.cos(P),d.y=b,d.z=M*Math.sin(P),g.push(d.x,d.y,d.z),h.copy(d).normalize(),x.push(h.x,h.y,h.z),p.push(T+A,1-E),y.push(l++)}u.push(y)}for(let m=0;m<n;m++)for(let y=0;y<e;y++){let E=u[m][y+1],v=u[m][y],b=u[m+1][y],M=u[m+1][y+1];(m!==0||a>0)&&f.push(E,v,M),(m!==n-1||c<Math.PI)&&f.push(v,b,M)}this.setIndex(f),this.setAttribute("position",new te(g,3)),this.setAttribute("normal",new te(x,3)),this.setAttribute("uv",new te(p,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.radius,t.widthSegments,t.heightSegments,t.phiStart,t.phiLength,t.thetaStart,t.thetaLength)}};var ci=class i extends ge{constructor(t=1,e=.4,n=12,s=48,r=Math.PI*2,a=0,o=Math.PI*2){super(),this.type="TorusGeometry",this.parameters={radius:t,tube:e,radialSegments:n,tubularSegments:s,arc:r,thetaStart:a,thetaLength:o},n=Math.floor(n),s=Math.floor(s);let c=[],l=[],u=[],d=[],h=new C,f=new C,g=new C;for(let x=0;x<=n;x++){let p=a+x/n*o;for(let m=0;m<=s;m++){let y=m/s*r;f.x=(t+e*Math.cos(p))*Math.cos(y),f.y=(t+e*Math.cos(p))*Math.sin(y),f.z=e*Math.sin(p),l.push(f.x,f.y,f.z),h.x=t*Math.cos(y),h.y=t*Math.sin(y),g.subVectors(f,h).normalize(),u.push(g.x,g.y,g.z),d.push(m/s),d.push(x/n)}}for(let x=1;x<=n;x++)for(let p=1;p<=s;p++){let m=(s+1)*x+p-1,y=(s+1)*(x-1)+p-1,E=(s+1)*(x-1)+p,v=(s+1)*x+p;c.push(m,y,v),c.push(y,E,v)}this.setIndex(c),this.setAttribute("position",new te(l,3)),this.setAttribute("normal",new te(u,3)),this.setAttribute("uv",new te(d,2))}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}static fromJSON(t){return new i(t.radius,t.tube,t.radialSegments,t.tubularSegments,t.arc,t.thetaStart,t.thetaLength)}};var ra=class extends ge{constructor(t=null){if(super(),this.type="WireframeGeometry",this.parameters={geometry:t},t!==null){let e=[],n=new Set,s=new C,r=new C;if(t.index!==null){let a=t.attributes.position,o=t.index,c=t.groups;c.length===0&&(c=[{start:0,count:o.count,materialIndex:0}]);for(let l=0,u=c.length;l<u;++l){let d=c[l],h=d.start,f=d.count;for(let g=h,x=h+f;g<x;g+=3)for(let p=0;p<3;p++){let m=o.getX(g+p),y=o.getX(g+(p+1)%3);s.fromBufferAttribute(a,m),r.fromBufferAttribute(a,y),du(s,r,n)===!0&&(e.push(s.x,s.y,s.z),e.push(r.x,r.y,r.z))}}}else{let a=t.attributes.position;for(let o=0,c=a.count/3;o<c;o++)for(let l=0;l<3;l++){let u=3*o+l,d=3*o+(l+1)%3;s.fromBufferAttribute(a,u),r.fromBufferAttribute(a,d),du(s,r,n)===!0&&(e.push(s.x,s.y,s.z),e.push(r.x,r.y,r.z))}}this.setAttribute("position",new te(e,3))}}copy(t){return super.copy(t),this.parameters=Object.assign({},t.parameters),this}};function du(i,t,e){let n=`${i.x},${i.y},${i.z}-${t.x},${t.y},${t.z}`,s=`${t.x},${t.y},${t.z}-${i.x},${i.y},${i.z}`;return e.has(n)===!0||e.has(s)===!0?!1:(e.add(n),e.add(s),!0)}function ws(i){let t={};for(let e in i){t[e]={};for(let n in i[e]){let s=i[e][n];if(fu(s))s.isRenderTargetTexture?(ie("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),t[e][n]=null):t[e][n]=s.clone();else if(Array.isArray(s))if(fu(s[0])){let r=[];for(let a=0,o=s.length;a<o;a++)r[a]=s[a].clone();t[e][n]=r}else t[e][n]=s.slice();else t[e][n]=s}}return t}function xn(i){let t={};for(let e=0;e<i.length;e++){let n=ws(i[e]);for(let s in n)t[s]=n[s]}return t}function fu(i){return i&&(i.isColor||i.isMatrix3||i.isMatrix4||i.isVector2||i.isVector3||i.isVector4||i.isTexture||i.isQuaternion)}function Fp(i){let t=[];for(let e=0;e<i.length;e++)t.push(i[e].clone());return t}function ih(i){let t=i.getRenderTarget();return t===null?i.outputColorSpace:t.isXRRenderTarget===!0?t.texture.colorSpace:Me.workingColorSpace}var ba={clone:ws,merge:xn},zp=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Op=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`,Oe=class extends Oi{constructor(t){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=zp,this.fragmentShader=Op,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,t!==void 0&&this.setValues(t)}copy(t){return super.copy(t),this.fragmentShader=t.fragmentShader,this.vertexShader=t.vertexShader,this.uniforms=ws(t.uniforms),this.uniformsGroups=Fp(t.uniformsGroups),this.defines=Object.assign({},t.defines),this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this.fog=t.fog,this.lights=t.lights,this.clipping=t.clipping,this.extensions=Object.assign({},t.extensions),this.glslVersion=t.glslVersion,this.defaultAttributeValues=Object.assign({},t.defaultAttributeValues),this.index0AttributeName=t.index0AttributeName,this.uniformsNeedUpdate=t.uniformsNeedUpdate,this}toJSON(t){let e=super.toJSON(t);e.glslVersion=this.glslVersion,e.uniforms={};for(let s in this.uniforms){let a=this.uniforms[s].value;a&&a.isTexture?e.uniforms[s]={type:"t",value:a.toJSON(t).uuid}:a&&a.isColor?e.uniforms[s]={type:"c",value:a.getHex()}:a&&a.isVector2?e.uniforms[s]={type:"v2",value:a.toArray()}:a&&a.isVector3?e.uniforms[s]={type:"v3",value:a.toArray()}:a&&a.isVector4?e.uniforms[s]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?e.uniforms[s]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?e.uniforms[s]={type:"m4",value:a.toArray()}:e.uniforms[s]={value:a}}Object.keys(this.defines).length>0&&(e.defines=this.defines),e.vertexShader=this.vertexShader,e.fragmentShader=this.fragmentShader,e.lights=this.lights,e.clipping=this.clipping;let n={};for(let s in this.extensions)this.extensions[s]===!0&&(n[s]=!0);return Object.keys(n).length>0&&(e.extensions=n),e}fromJSON(t,e){if(super.fromJSON(t,e),t.uniforms!==void 0)for(let n in t.uniforms){let s=t.uniforms[n];switch(this.uniforms[n]={},s.type){case"t":this.uniforms[n].value=e[s.value]||null;break;case"c":this.uniforms[n].value=new Wt().setHex(s.value);break;case"v2":this.uniforms[n].value=new vt().fromArray(s.value);break;case"v3":this.uniforms[n].value=new C().fromArray(s.value);break;case"v4":this.uniforms[n].value=new xe().fromArray(s.value);break;case"m3":this.uniforms[n].value=new he().fromArray(s.value);break;case"m4":this.uniforms[n].value=new de().fromArray(s.value);break;default:this.uniforms[n].value=s.value}}if(t.defines!==void 0&&(this.defines=t.defines),t.vertexShader!==void 0&&(this.vertexShader=t.vertexShader),t.fragmentShader!==void 0&&(this.fragmentShader=t.fragmentShader),t.glslVersion!==void 0&&(this.glslVersion=t.glslVersion),t.extensions!==void 0)for(let n in t.extensions)this.extensions[n]=t.extensions[n];return t.lights!==void 0&&(this.lights=t.lights),t.clipping!==void 0&&(this.clipping=t.clipping),this}},Ao=class extends Oe{constructor(t){super(t),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}},Ot=class extends Oi{constructor(t){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new Wt(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new Wt(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Cc,this.normalScale=new vt(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new ri,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(t)}copy(t){return super.copy(t),this.defines={STANDARD:""},this.color.copy(t.color),this.roughness=t.roughness,this.metalness=t.metalness,this.map=t.map,this.lightMap=t.lightMap,this.lightMapIntensity=t.lightMapIntensity,this.aoMap=t.aoMap,this.aoMapIntensity=t.aoMapIntensity,this.emissive.copy(t.emissive),this.emissiveMap=t.emissiveMap,this.emissiveIntensity=t.emissiveIntensity,this.bumpMap=t.bumpMap,this.bumpScale=t.bumpScale,this.normalMap=t.normalMap,this.normalMapType=t.normalMapType,this.normalScale.copy(t.normalScale),this.displacementMap=t.displacementMap,this.displacementScale=t.displacementScale,this.displacementBias=t.displacementBias,this.roughnessMap=t.roughnessMap,this.metalnessMap=t.metalnessMap,this.alphaMap=t.alphaMap,this.envMap=t.envMap,this.envMapRotation.copy(t.envMapRotation),this.envMapIntensity=t.envMapIntensity,this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this.wireframeLinecap=t.wireframeLinecap,this.wireframeLinejoin=t.wireframeLinejoin,this.flatShading=t.flatShading,this.fog=t.fog,this}},ts=class extends Ot{constructor(t){super(),this.isMeshPhysicalMaterial=!0,this.defines={STANDARD:"",PHYSICAL:""},this.type="MeshPhysicalMaterial",this.anisotropyRotation=0,this.anisotropyMap=null,this.clearcoatMap=null,this.clearcoatRoughness=0,this.clearcoatRoughnessMap=null,this.clearcoatNormalScale=new vt(1,1),this.clearcoatNormalMap=null,this.ior=1.5,Object.defineProperty(this,"reflectivity",{get:function(){return le(2.5*(this.ior-1)/(this.ior+1),0,1)},set:function(e){this.ior=(1+.4*e)/(1-.4*e)}}),this.iridescenceMap=null,this.iridescenceIOR=1.3,this.iridescenceThicknessRange=[100,400],this.iridescenceThicknessMap=null,this.sheenColor=new Wt(0),this.sheenColorMap=null,this.sheenRoughness=1,this.sheenRoughnessMap=null,this.transmissionMap=null,this.thickness=0,this.thicknessMap=null,this.attenuationDistance=1/0,this.attenuationColor=new Wt(1,1,1),this.specularIntensity=1,this.specularIntensityMap=null,this.specularColor=new Wt(1,1,1),this.specularColorMap=null,this._anisotropy=0,this._clearcoat=0,this._dispersion=0,this._iridescence=0,this._retroreflectivity=0,this._sheen=0,this._transmission=0,this.setValues(t)}get anisotropy(){return this._anisotropy}set anisotropy(t){this._anisotropy>0!=t>0&&this.version++,this._anisotropy=t}get clearcoat(){return this._clearcoat}set clearcoat(t){this._clearcoat>0!=t>0&&this.version++,this._clearcoat=t}get iridescence(){return this._iridescence}set iridescence(t){this._iridescence>0!=t>0&&this.version++,this._iridescence=t}get dispersion(){return this._dispersion}set dispersion(t){this._dispersion>0!=t>0&&this.version++,this._dispersion=t}get retroreflectivity(){return this._retroreflectivity}set retroreflectivity(t){this._retroreflectivity>0!=t>0&&this.version++,this._retroreflectivity=t}get sheen(){return this._sheen}set sheen(t){this._sheen>0!=t>0&&this.version++,this._sheen=t}get transmission(){return this._transmission}set transmission(t){this._transmission>0!=t>0&&this.version++,this._transmission=t}copy(t){return super.copy(t),this.defines={STANDARD:"",PHYSICAL:""},this.anisotropy=t.anisotropy,this.anisotropyRotation=t.anisotropyRotation,this.anisotropyMap=t.anisotropyMap,this.clearcoat=t.clearcoat,this.clearcoatMap=t.clearcoatMap,this.clearcoatRoughness=t.clearcoatRoughness,this.clearcoatRoughnessMap=t.clearcoatRoughnessMap,this.clearcoatNormalMap=t.clearcoatNormalMap,this.clearcoatNormalScale.copy(t.clearcoatNormalScale),this.dispersion=t.dispersion,this.ior=t.ior,this.iridescence=t.iridescence,this.iridescenceMap=t.iridescenceMap,this.iridescenceIOR=t.iridescenceIOR,this.iridescenceThicknessRange=[...t.iridescenceThicknessRange],this.iridescenceThicknessMap=t.iridescenceThicknessMap,this.retroreflectivity=t.retroreflectivity,this.sheen=t.sheen,this.sheenColor.copy(t.sheenColor),this.sheenColorMap=t.sheenColorMap,this.sheenRoughness=t.sheenRoughness,this.sheenRoughnessMap=t.sheenRoughnessMap,this.transmission=t.transmission,this.transmissionMap=t.transmissionMap,this.thickness=t.thickness,this.thicknessMap=t.thicknessMap,this.attenuationDistance=t.attenuationDistance,this.attenuationColor.copy(t.attenuationColor),this.specularIntensity=t.specularIntensity,this.specularIntensityMap=t.specularIntensityMap,this.specularColor.copy(t.specularColor),this.specularColorMap=t.specularColorMap,this}};var Ro=class extends Oi{constructor(t){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=Wu,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(t)}copy(t){return super.copy(t),this.depthPacking=t.depthPacking,this.map=t.map,this.alphaMap=t.alphaMap,this.displacementMap=t.displacementMap,this.displacementScale=t.displacementScale,this.displacementBias=t.displacementBias,this.wireframe=t.wireframe,this.wireframeLinewidth=t.wireframeLinewidth,this}},Co=class extends Oi{constructor(t){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(t)}copy(t){return super.copy(t),this.map=t.map,this.alphaMap=t.alphaMap,this.displacementMap=t.displacementMap,this.displacementScale=t.displacementScale,this.displacementBias=t.displacementBias,this}};function Ws(i,t){return!i||i.constructor===t?i:typeof t.BYTES_PER_ELEMENT=="number"?new t(i):Array.prototype.slice.call(i)}function xl(i){return i!==void 0&&i.inTangents!==void 0&&i.outTangents!==void 0}var es=class{constructor(t,e,n,s){this.parameterPositions=t,this._cachedIndex=0,this.resultBuffer=s!==void 0?s:new e.constructor(n),this.sampleValues=e,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(t){let e=this.parameterPositions,n=this._cachedIndex,s=e[n],r=e[n-1];n:{t:{let a;e:{i:if(!(t<s)){for(let o=n+2;;){if(s===void 0){if(t<r)break i;return n=e.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===o)break;if(r=s,s=e[++n],t<s)break t}a=e.length;break e}if(!(t>=r)){let o=e[1];t<o&&(n=2,r=o);for(let c=n-2;;){if(r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===c)break;if(s=r,r=e[--n-1],t>=r)break t}a=n,n=0;break e}break n}for(;n<a;){let o=n+a>>>1;t<e[o]?a=o:n=o+1}if(s=e[n],r=e[n-1],r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(s===void 0)return n=e.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,r,s)}return this.interpolate_(n,r,t,s)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(t){let e=this.resultBuffer,n=this.sampleValues,s=this.valueSize,r=t*s;for(let a=0;a!==s;++a)e[a]=n[r+a];return e}interpolate_(){throw new Error("THREE.Interpolant: Call to abstract method.")}intervalChanged_(){}},Po=class extends es{constructor(t,e,n,s){super(t,e,n,s),this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:Sl,endingEnd:Sl}}intervalChanged_(t,e,n){let s=this.parameterPositions,r=t-2,a=t+1,o=s[r],c=s[a];if(o===void 0)switch(this.getSettings_().endingStart){case bl:r=t,o=2*e-n;break;case El:r=s.length-2,o=e+s[r]-s[r+1];break;default:r=t,o=n}if(c===void 0)switch(this.getSettings_().endingEnd){case bl:a=t,c=2*n-e;break;case El:a=1,c=n+s[1]-s[0];break;default:a=t-1,c=e}let l=(n-e)*.5,u=this.valueSize;this._weightPrev=l/(e-o),this._weightNext=l/(c-n),this._offsetPrev=r*u,this._offsetNext=a*u}interpolate_(t,e,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=t*o,l=c-o,u=this._offsetPrev,d=this._offsetNext,h=this._weightPrev,f=this._weightNext,g=(n-e)/(s-e),x=g*g,p=x*g,m=-h*p+2*h*x-h*g,y=(1+h)*p+(-1.5-2*h)*x+(-.5+h)*g+1,E=(-1-f)*p+(1.5+f)*x+.5*g,v=f*p-f*x;for(let b=0;b!==o;++b)r[b]=m*a[u+b]+y*a[l+b]+E*a[c+b]+v*a[d+b];return r}},Io=class extends es{constructor(t,e,n,s){super(t,e,n,s)}interpolate_(t,e,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=t*o,l=c-o,u=(n-e)/(s-e),d=1-u;for(let h=0;h!==o;++h)r[h]=a[l+h]*d+a[c+h]*u;return r}},Lo=class extends es{constructor(t,e,n,s){super(t,e,n,s)}interpolate_(t){return this.copySampleValue_(t-1)}},Do=class extends es{interpolate_(t,e,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=t*o,l=c-o,u=this.inTangents,d=this.outTangents;if(!u||!d){let g=(n-e)/(s-e),x=1-g;for(let p=0;p!==o;++p)r[p]=a[l+p]*x+a[c+p]*g;return r}let h=o*2,f=t-1;for(let g=0;g!==o;++g){let x=a[l+g],p=a[c+g],m=f*h+g*2,y=d[m],E=d[m+1],v=t*h+g*2,b=u[v],M=u[v+1],A=kp(n,e,y,b,s);r[g]=cd(A,x,E,M,p)}return r}};function cd(i,t,e,n,s){let r=1-i;return r*r*r*t+3*r*r*i*e+3*r*i*i*n+i*i*i*s}function Bp(i,t,e,n,s){let r=1-i;return 3*r*r*(e-t)+6*r*i*(n-e)+3*i*i*(s-n)}function kp(i,t,e,n,s){let r=(i-t)/(s-t);for(let a=0;a<8;a++){let o=cd(r,t,e,n,s)-i;if(Math.abs(o)<1e-10)break;let c=Bp(r,t,e,n,s);if(Math.abs(c)<1e-10)break;r=Math.max(0,Math.min(1,r-o/c))}return r}var zn=class{constructor(t,e,n,s){if(t===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(e===void 0||e.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+t);this.name=t,this.times=Ws(e,this.TimeBufferType),this.values=Ws(n,this.ValueBufferType),this.setInterpolation(s||this.DefaultInterpolation)}static toJSON(t){let e=t.constructor,n;if(e.toJSON!==this.toJSON)n=e.toJSON(t);else{n={name:t.name,times:Ws(t.times,Array),values:Ws(t.values,Array)};let s=t.getInterpolation();s!==t.DefaultInterpolation&&(n.interpolation=s),xl(t.settings)&&(n.settings={inTangents:Ws(t.settings.inTangents,Array),outTangents:Ws(t.settings.outTangents,Array)})}return n.type=t.ValueTypeName,n}InterpolantFactoryMethodDiscrete(t){return new Lo(this.times,this.values,this.getValueSize(),t)}InterpolantFactoryMethodLinear(t){return new Io(this.times,this.values,this.getValueSize(),t)}InterpolantFactoryMethodSmooth(t){return new Po(this.times,this.values,this.getValueSize(),t)}InterpolantFactoryMethodBezier(t){let e=new Do(this.times,this.values,this.getValueSize(),t);return this.settings&&(e.inTangents=this.settings.inTangents,e.outTangents=this.settings.outTangents),e}setInterpolation(t){let e;switch(t){case Ur:e=this.InterpolantFactoryMethodDiscrete;break;case po:e=this.InterpolantFactoryMethodLinear;break;case io:e=this.InterpolantFactoryMethodSmooth;break;case Ml:e=this.InterpolantFactoryMethodBezier;break}if(e===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(t!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error(n);return ie("KeyframeTrack:",n),this}return this.createInterpolant=e,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return Ur;case this.InterpolantFactoryMethodLinear:return po;case this.InterpolantFactoryMethodSmooth:return io;case this.InterpolantFactoryMethodBezier:return Ml}}getValueSize(){return this.values.length/this.times.length}shift(t){if(t!==0){let e=this.times;for(let n=0,s=e.length;n!==s;++n)e[n]+=t}return this}scale(t){if(t!==1){let e=this.times;for(let n=0,s=e.length;n!==s;++n)e[n]*=t;xl(this.settings)&&(pu(this.settings.inTangents,t),pu(this.settings.outTangents,t))}return this}trim(t,e){let n=this.times,s=n.length,r=0,a=s-1;for(;r!==s&&n[r]<t;)++r;for(;a!==-1&&n[a]>e;)--a;if(++a,r!==0||a!==s){r>=a&&(a=Math.max(a,1),r=a-1);let o=this.getValueSize();this.times=n.slice(r,a),this.values=this.values.slice(r*o,a*o)}return this}validate(){let t=!0,e=this.getValueSize();e-Math.floor(e)!==0&&(ae("KeyframeTrack: Invalid value size in track.",this),t=!1);let n=this.times,s=this.values,r=n.length;r===0&&(ae("KeyframeTrack: Track is empty.",this),t=!1);let a=null;for(let o=0;o!==r;o++){let c=n[o];if(typeof c=="number"&&isNaN(c)){ae("KeyframeTrack: Time is not a valid number.",this,o,c),t=!1;break}if(a!==null&&a>c){ae("KeyframeTrack: Out of order keys.",this,o,c,a),t=!1;break}a=c}if(s!==void 0&&wf(s))for(let o=0,c=s.length;o!==c;++o){let l=s[o];if(isNaN(l)){ae("KeyframeTrack: Value is not a valid number.",this,o,l),t=!1;break}}return t}optimize(){let t=this.times.slice(),e=this.values.slice(),n=this.getValueSize(),s=this.getInterpolation()===io,r=t.length-1,a=1;for(let o=1;o<r;++o){let c=!1,l=t[o],u=t[o+1];if(l!==u&&(o!==1||l!==t[0]))if(s)c=!0;else{let d=o*n,h=d-n,f=d+n;for(let g=0;g!==n;++g){let x=e[d+g];if(x!==e[h+g]||x!==e[f+g]){c=!0;break}}}if(c){if(o!==a){t[a]=t[o];let d=o*n,h=a*n;for(let f=0;f!==n;++f)e[h+f]=e[d+f]}++a}}if(r>0){t[a]=t[r];for(let o=r*n,c=a*n,l=0;l!==n;++l)e[c+l]=e[o+l];++a}return a!==t.length?(this.times=t.slice(0,a),this.values=e.slice(0,a*n)):(this.times=t,this.values=e),this}clone(){let t=this.times.slice(),e=this.values.slice(),n=this.constructor,s=new n(this.name,t,e);return s.createInterpolant=this.createInterpolant,xl(this.settings)&&(s.settings={inTangents:this.settings.inTangents.slice(),outTangents:this.settings.outTangents.slice()}),s}};function pu(i,t){for(let e=0,n=i.length;e!==n;e+=2)i[e]*=t}zn.prototype.ValueTypeName="";zn.prototype.TimeBufferType=Float32Array;zn.prototype.ValueBufferType=Float32Array;zn.prototype.DefaultInterpolation=po;var ns=class extends zn{constructor(t,e,n){super(t,e,n)}};ns.prototype.ValueTypeName="bool";ns.prototype.ValueBufferType=Array;ns.prototype.DefaultInterpolation=Ur;ns.prototype.InterpolantFactoryMethodLinear=void 0;ns.prototype.InterpolantFactoryMethodSmooth=void 0;var Uo=class extends zn{constructor(t,e,n,s){super(t,e,n,s)}};Uo.prototype.ValueTypeName="color";var No=class extends zn{constructor(t,e,n,s){super(t,e,n,s)}};No.prototype.ValueTypeName="number";var Fo=class extends es{constructor(t,e,n,s){super(t,e,n,s)}interpolate_(t,e,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=(n-e)/(s-e),l=t*o;for(let u=l+o;l!==u;l+=4)sn.slerpFlat(r,0,a,l-o,a,l,c);return r}},aa=class extends zn{constructor(t,e,n,s){super(t,e,n,s)}InterpolantFactoryMethodLinear(t){return new Fo(this.times,this.values,this.getValueSize(),t)}};aa.prototype.ValueTypeName="quaternion";aa.prototype.InterpolantFactoryMethodSmooth=void 0;var is=class extends zn{constructor(t,e,n){super(t,e,n)}};is.prototype.ValueTypeName="string";is.prototype.ValueBufferType=Array;is.prototype.DefaultInterpolation=Ur;is.prototype.InterpolantFactoryMethodLinear=void 0;is.prototype.InterpolantFactoryMethodSmooth=void 0;var zo=class extends zn{constructor(t,e,n,s){super(t,e,n,s)}};zo.prototype.ValueTypeName="vector";var Oo=class{constructor(t,e,n){let s=this,r=!1,a=0,o=0,c,l=[];this.onStart=void 0,this.onLoad=t,this.onProgress=e,this.onError=n,this._abortController=null,this.itemStart=function(u){o++,r===!1&&s.onStart!==void 0&&s.onStart(u,a,o),r=!0},this.itemEnd=function(u){a++,s.onProgress!==void 0&&s.onProgress(u,a,o),a===o&&(r=!1,s.onLoad!==void 0&&s.onLoad())},this.itemError=function(u){s.onError!==void 0&&s.onError(u)},this.resolveURL=function(u){return u=u.normalize("NFC"),c?c(u):u},this.setURLModifier=function(u){return c=u,this},this.addHandler=function(u,d){return l.push(u,d),this},this.removeHandler=function(u){let d=l.indexOf(u);return d!==-1&&l.splice(d,2),this},this.getHandler=function(u){for(let d=0,h=l.length;d<h;d+=2){let f=l[d],g=l[d+1];if(f.global&&(f.lastIndex=0),f.test(u))return g}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){return this._abortController||(this._abortController=new AbortController),this._abortController}},ld=new Oo,Bo=class{constructor(t){this.manager=t!==void 0?t:ld,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}load(){}loadAsync(t,e){let n=this;return new Promise(function(s,r){n.load(t,s,e,r)})}parse(){}setCrossOrigin(t){return this.crossOrigin=t,this}setWithCredentials(t){return this.withCredentials=t,this}setPath(t){return this.path=t,this}setResourcePath(t){return this.resourcePath=t,this}setRequestHeader(t){return this.requestHeader=t,this}abort(){return this}};Bo.DEFAULT_MATERIAL_NAME="__DEFAULT";var cr=class extends rn{constructor(t,e=1){super(),this.isLight=!0,this.type="Light",this.color=new Wt(t),this.intensity=e}copy(t,e){return super.copy(t,e),this.color.copy(t.color),this.intensity=t.intensity,this}toJSON(t){let e=super.toJSON(t);return e.object.color=this.color.getHex(),e.object.intensity=this.intensity,e}},oa=class extends cr{constructor(t,e,n){super(t,n),this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(rn.DEFAULT_UP),this.updateMatrix(),this.groundColor=new Wt(e)}copy(t,e){return super.copy(t,e),this.groundColor.copy(t.groundColor),this}toJSON(t){let e=super.toJSON(t);return e.object.groundColor=this.groundColor.getHex(),e}},_l=new de,mu=new C,gu=new C,ca=class{constructor(t){this.camera=t,this.intensity=1,this.bias=0,this.biasNode=null,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new vt(512,512),this.mapType=Ln,this.map=null,this.mapPass=null,this.matrix=new de,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new sr,this._frameExtents=new vt(1,1),this._viewportCount=1,this._viewports=[new xe(0,0,1,1)]}getViewportCount(){return this._viewportCount}getCamera(){return this.camera}getFrustum(){return this._frustum}updateMatrices(t){let e=this.camera;mu.setFromMatrixPosition(t.matrixWorld),e.position.copy(mu),gu.setFromMatrixPosition(t.target.matrixWorld),e.lookAt(gu),e.updateMatrixWorld(),this._updateMatrix(e,this.matrix,this._frustum)}_updateMatrix(t,e,n,s){_l.multiplyMatrices(t.projectionMatrix,t.matrixWorldInverse),n.setFromProjectionMatrix(_l,t.coordinateSystem,t.reversedDepth);let r=this._frameExtents,a=s?s.z/r.x:1,o=s?s.w/r.y:1,c=s?s.x/r.x:0,l=s?s.y/r.y:0;t.coordinateSystem===Ks||t.reversedDepth?e.set(.5*a,0,0,.5*a+c,0,.5*o,0,.5*o+l,0,0,1,0,0,0,0,1):e.set(.5*a,0,0,.5*a+c,0,.5*o,0,.5*o+l,0,0,.5,.5,0,0,0,1),e.multiply(_l)}getViewport(t){return this._viewports[t]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(t){return this.camera=t.camera.clone(),this.intensity=t.intensity,this.bias=t.bias,this.radius=t.radius,this.autoUpdate=t.autoUpdate,this.needsUpdate=t.needsUpdate,this.normalBias=t.normalBias,this.blurSamples=t.blurSamples,this.mapSize.copy(t.mapSize),this.biasNode=t.biasNode,this}clone(){return new this.constructor().copy(this)}toJSON(){let t={};return t.intensity=this.intensity,t.bias=this.bias,t.normalBias=this.normalBias,t.radius=this.radius,t.blurSamples=this.blurSamples,t.mapSize=this.mapSize.toArray(),t.camera=this.camera.toJSON(!1).object,delete t.camera.matrix,t}},to=new C,eo=new sn,di=new C,la=class extends rn{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new de,this.projectionMatrix=new de,this.projectionMatrixInverse=new de,this.coordinateSystem=si,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(t,e){return super.copy(t,e),this.matrixWorldInverse.copy(t.matrixWorldInverse),this.projectionMatrix.copy(t.projectionMatrix),this.projectionMatrixInverse.copy(t.projectionMatrixInverse),this.coordinateSystem=t.coordinateSystem,this}getWorldDirection(t){return super.getWorldDirection(t).negate()}updateMatrixWorld(t){super.updateMatrixWorld(t),this.matrixWorld.decompose(to,eo,di),di.x===1&&di.y===1&&di.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(to,eo,di.set(1,1,1)).invert()}updateWorldMatrix(t,e,n=!1){super.updateWorldMatrix(t,e,n),this.matrixWorld.decompose(to,eo,di),di.x===1&&di.y===1&&di.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(to,eo,di.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}},Zi=new C,vu=new vt,xu=new vt,Je=class extends la{constructor(t=50,e=1,n=.1,s=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=t,this.zoom=1,this.near=n,this.far=s,this.focus=10,this.aspect=e,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(t,e){return super.copy(t,e),this.fov=t.fov,this.zoom=t.zoom,this.near=t.near,this.far=t.far,this.focus=t.focus,this.aspect=t.aspect,this.view=t.view===null?null:Object.assign({},t.view),this.filmGauge=t.filmGauge,this.filmOffset=t.filmOffset,this}setFocalLength(t){let e=.5*this.getFilmHeight()/t;this.fov=tr*2*Math.atan(e),this.updateProjectionMatrix()}getFocalLength(){let t=Math.tan(Pr*.5*this.fov);return .5*this.getFilmHeight()/t}getEffectiveFOV(){return tr*2*Math.atan(Math.tan(Pr*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(t,e,n){Zi.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),e.set(Zi.x,Zi.y).multiplyScalar(-t/Zi.z),Zi.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(Zi.x,Zi.y).multiplyScalar(-t/Zi.z)}getViewSize(t,e){return this.getViewBounds(t,vu,xu),e.subVectors(xu,vu)}setViewOffset(t,e,n,s,r,a){this.aspect=t/e,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=t,this.view.fullHeight=e,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let t=this.near,e=t*Math.tan(Pr*.5*this.fov)/this.zoom,n=2*e,s=this.aspect*n,r=-.5*s,a=this.view;if(this.view!==null&&this.view.enabled){let c=a.fullWidth,l=a.fullHeight;r+=a.offsetX*s/c,e-=a.offsetY*n/l,s*=a.width/c,n*=a.height/l}let o=this.filmOffset;o!==0&&(r+=t*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(r,r+s,e,e-n,t,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(t){let e=super.toJSON(t);return e.object.fov=this.fov,e.object.zoom=this.zoom,e.object.near=this.near,e.object.far=this.far,e.object.focus=this.focus,e.object.aspect=this.aspect,this.view!==null&&(e.object.view=Object.assign({},this.view)),e.object.filmGauge=this.filmGauge,e.object.filmOffset=this.filmOffset,e}};var Pl=class extends ca{constructor(){super(new Je(90,1,.5,500)),this.isPointLightShadow=!0}},ha=class extends cr{constructor(t,e,n=0,s=2){super(t,e),this.isPointLight=!0,this.type="PointLight",this.distance=n,this.decay=s,this.shadow=new Pl}get power(){return this.intensity*4*Math.PI}set power(t){this.intensity=t/(4*Math.PI)}dispose(){super.dispose(),this.shadow.dispose()}copy(t,e){return super.copy(t,e),this.distance=t.distance,this.decay=t.decay,this.shadow=t.shadow.clone(),this}toJSON(t){let e=super.toJSON(t);return e.object.distance=this.distance,e.object.decay=this.decay,e.object.shadow=this.shadow.toJSON(),e}},lr=class extends la{constructor(t=-1,e=1,n=1,s=-1,r=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=t,this.right=e,this.top=n,this.bottom=s,this.near=r,this.far=a,this.updateProjectionMatrix()}copy(t,e){return super.copy(t,e),this.left=t.left,this.right=t.right,this.top=t.top,this.bottom=t.bottom,this.near=t.near,this.far=t.far,this.zoom=t.zoom,this.view=t.view===null?null:Object.assign({},t.view),this}setViewOffset(t,e,n,s,r,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=t,this.view.fullHeight=e,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let t=(this.right-this.left)/(2*this.zoom),e=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,s=(this.top+this.bottom)/2,r=n-t,a=n+t,o=s+e,c=s-e;if(this.view!==null&&this.view.enabled){let l=(this.right-this.left)/this.view.fullWidth/this.zoom,u=(this.top-this.bottom)/this.view.fullHeight/this.zoom;r+=l*this.view.offsetX,a=r+l*this.view.width,o-=u*this.view.offsetY,c=o-u*this.view.height}this.projectionMatrix.makeOrthographic(r,a,o,c,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(t){let e=super.toJSON(t);return e.object.zoom=this.zoom,e.object.left=this.left,e.object.right=this.right,e.object.top=this.top,e.object.bottom=this.bottom,e.object.near=this.near,e.object.far=this.far,this.view!==null&&(e.object.view=Object.assign({},this.view)),e}},Il=class extends ca{constructor(){super(new lr(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}},ua=class extends cr{constructor(t,e){super(t,e),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(rn.DEFAULT_UP),this.updateMatrix(),this.target=new rn,this.shadow=new Il}dispose(){super.dispose(),this.shadow.dispose()}copy(t){return super.copy(t),this.target=t.target.clone(),this.shadow=t.shadow.clone(),this}toJSON(t){let e=super.toJSON(t);return e.object.shadow=this.shadow.toJSON(),e.object.target=this.target.uuid,e}};var da=class extends ge{constructor(){super(),this.isInstancedBufferGeometry=!0,this.type="InstancedBufferGeometry",this.instanceCount=1/0}copy(t){return super.copy(t),this.instanceCount=t.instanceCount,this}toJSON(){let t=super.toJSON();return t.instanceCount=this.instanceCount,t.isInstancedBufferGeometry=!0,t}};var Xs=-90,qs=1,ko=class extends rn{constructor(t,e,n){super(),this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;let s=new Je(Xs,qs,t,e);s.layers=this.layers,this.add(s);let r=new Je(Xs,qs,t,e);r.layers=this.layers,this.add(r);let a=new Je(Xs,qs,t,e);a.layers=this.layers,this.add(a);let o=new Je(Xs,qs,t,e);o.layers=this.layers,this.add(o);let c=new Je(Xs,qs,t,e);c.layers=this.layers,this.add(c);let l=new Je(Xs,qs,t,e);l.layers=this.layers,this.add(l)}updateCoordinateSystem(){let t=this.coordinateSystem,e=this.children.concat(),[n,s,r,a,o,c]=e;for(let l of e)this.remove(l);if(t===si)n.up.set(0,1,0),n.lookAt(1,0,0),s.up.set(0,1,0),s.lookAt(-1,0,0),r.up.set(0,0,-1),r.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),c.up.set(0,1,0),c.lookAt(0,0,-1);else if(t===Ks)n.up.set(0,-1,0),n.lookAt(-1,0,0),s.up.set(0,-1,0),s.lookAt(1,0,0),r.up.set(0,0,1),r.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),c.up.set(0,-1,0),c.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+t);for(let l of e)this.add(l),l.updateMatrixWorld()}update(t,e){this.parent===null&&this.updateMatrixWorld();let{renderTarget:n,activeMipmapLevel:s}=this;this.coordinateSystem!==t.coordinateSystem&&(this.coordinateSystem=t.coordinateSystem,this.updateCoordinateSystem());let[r,a,o,c,l,u]=this.children,d=t.getRenderTarget(),h=t.getActiveCubeFace(),f=t.getActiveMipmapLevel(),g=t.xr.enabled;t.xr.enabled=!1;let x=n.texture.generateMipmaps;n.texture.generateMipmaps=!1;let p=!1;t.isWebGLRenderer===!0?p=t.state.buffers.depth.getReversed():p=t.reversedDepthBuffer,t.setRenderTarget(n,0,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,r),t.setRenderTarget(n,1,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,a),t.setRenderTarget(n,2,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,o),t.setRenderTarget(n,3,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,c),t.setRenderTarget(n,4,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,l),n.texture.generateMipmaps=x,t.setRenderTarget(n,5,s),p&&t.autoClear===!1&&t.clearDepth(),t.render(e,u),t.setRenderTarget(d,h,f),t.xr.enabled=g,n.texture.needsPMREMUpdate=!0}},Ho=class extends Je{constructor(t=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=t}};var sh="\\[\\]\\.:\\/",Hp=new RegExp("["+sh+"]","g"),rh="[^"+sh+"]",Vp="[^"+sh.replace("\\.","")+"]",Gp=/((?:WC+[\/:])*)/.source.replace("WC",rh),Wp=/(WCOD+)?/.source.replace("WCOD",Vp),Xp=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",rh),qp=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",rh),Yp=new RegExp("^"+Gp+Wp+Xp+qp+"$"),jp=["material","materials","bones","map"],Ll=class{constructor(t,e,n){let s=n||Ge.parseTrackName(e);this._targetGroup=t,this._bindings=t.subscribe_(e,s)}getValue(t,e){this.bind();let n=this._targetGroup.nCachedObjects_,s=this._bindings[n];s!==void 0&&s.getValue(t,e)}setValue(t,e){let n=this._bindings;for(let s=this._targetGroup.nCachedObjects_,r=n.length;s!==r;++s)n[s].setValue(t,e)}bind(){let t=this._bindings;for(let e=this._targetGroup.nCachedObjects_,n=t.length;e!==n;++e)t[e].bind()}unbind(){let t=this._bindings;for(let e=this._targetGroup.nCachedObjects_,n=t.length;e!==n;++e)t[e].unbind()}},Ge=class i{constructor(t,e,n){this.path=e,this.parsedPath=n||i.parseTrackName(e),this.node=i.findNode(t,this.parsedPath.nodeName),this.rootNode=t,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(t,e,n){return t&&t.isAnimationObjectGroup?new i.Composite(t,e,n):new i(t,e,n)}static sanitizeNodeName(t){return t.replace(/\s/g,"_").replace(Hp,"")}static parseTrackName(t){let e=Yp.exec(t);if(e===null)throw new Error("THREE.PropertyBinding: Cannot parse trackName: "+t);let n={nodeName:e[2],objectName:e[3],objectIndex:e[4],propertyName:e[5],propertyIndex:e[6]},s=n.nodeName&&n.nodeName.lastIndexOf(".");if(s!==void 0&&s!==-1){let r=n.nodeName.substring(s+1);jp.indexOf(r)!==-1&&(n.nodeName=n.nodeName.substring(0,s),n.objectName=r)}if(n.propertyName===null||n.propertyName.length===0)throw new Error("THREE.PropertyBinding: can not parse propertyName from trackName: "+t);return n}static findNode(t,e){if(e===void 0||e===""||e==="."||e===-1||e===t.name||e===t.uuid)return t;if(t.skeleton){let n=t.skeleton.getBoneByName(e);if(n!==void 0)return n}if(t.children){let n=function(r){for(let a=0;a<r.length;a++){let o=r[a];if(o.name===e||o.uuid===e)return o;let c=n(o.children);if(c)return c}return null},s=n(t.children);if(s)return s}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(t,e){t[e]=this.targetObject[this.propertyName]}_getValue_array(t,e){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)t[e++]=n[s]}_getValue_arrayElement(t,e){t[e]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(t,e){this.resolvedProperty.toArray(t,e)}_setValue_direct(t,e){this.targetObject[this.propertyName]=t[e]}_setValue_direct_setNeedsUpdate(t,e){this.targetObject[this.propertyName]=t[e],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(t,e){this.targetObject[this.propertyName]=t[e],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(t,e){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=t[e++]}_setValue_array_setNeedsUpdate(t,e){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=t[e++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(t,e){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=t[e++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(t,e){this.resolvedProperty[this.propertyIndex]=t[e]}_setValue_arrayElement_setNeedsUpdate(t,e){this.resolvedProperty[this.propertyIndex]=t[e],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(t,e){this.resolvedProperty[this.propertyIndex]=t[e],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(t,e){this.resolvedProperty.fromArray(t,e)}_setValue_fromArray_setNeedsUpdate(t,e){this.resolvedProperty.fromArray(t,e),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(t,e){this.resolvedProperty.fromArray(t,e),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(t,e){this.bind(),this.getValue(t,e)}_setValue_unbound(t,e){this.bind(),this.setValue(t,e)}bind(){let t=this.node,e=this.parsedPath,n=e.objectName,s=e.propertyName,r=e.propertyIndex;if(t||(t=i.findNode(this.rootNode,e.nodeName),this.node=t),this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!t){ie("PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let l=e.objectIndex;switch(n){case"materials":if(!t.material){ae("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!t.material.materials){ae("PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}t=t.material.materials;break;case"bones":if(!t.skeleton){ae("PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}t=t.skeleton.bones;for(let u=0;u<t.length;u++)if(t[u].name===l){l=u;break}break;case"map":if("map"in t){t=t.map;break}if(!t.material){ae("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!t.material.map){ae("PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}t=t.material.map;break;default:if(t[n]===void 0){ae("PropertyBinding: Can not bind to objectName of node undefined.",this);return}t=t[n]}if(l!==void 0){if(t[l]===void 0){ae("PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,t);return}t=t[l]}}let a=t[s];if(a===void 0){let l=e.nodeName;ae("PropertyBinding: Trying to update property for track: "+l+"."+s+" but it wasn't found.",t);return}let o=this.Versioning.None;this.targetObject=t,t.isMaterial===!0?o=this.Versioning.NeedsUpdate:t.isObject3D===!0&&(o=this.Versioning.MatrixWorldNeedsUpdate);let c=this.BindingType.Direct;if(r!==void 0){if(s==="morphTargetInfluences"){if(!t.geometry){ae("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!t.geometry.morphAttributes){ae("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}t.morphTargetDictionary[r]!==void 0&&(r=t.morphTargetDictionary[r])}c=this.BindingType.ArrayElement,this.resolvedProperty=a,this.propertyIndex=r}else a.fromArray!==void 0&&a.toArray!==void 0?(c=this.BindingType.HasFromToArray,this.resolvedProperty=a):Array.isArray(a)?(c=this.BindingType.EntireArray,this.resolvedProperty=a):this.propertyName=s;this.getValue=this.GetterByBindingType[c],this.setValue=this.SetterByBindingTypeAndVersioning[c][o]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}};Ge.Composite=Ll;Ge.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};Ge.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};Ge.prototype.GetterByBindingType=[Ge.prototype._getValue_direct,Ge.prototype._getValue_array,Ge.prototype._getValue_arrayElement,Ge.prototype._getValue_toArray];Ge.prototype.SetterByBindingTypeAndVersioning=[[Ge.prototype._setValue_direct,Ge.prototype._setValue_direct_setNeedsUpdate,Ge.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[Ge.prototype._setValue_array,Ge.prototype._setValue_array_setNeedsUpdate,Ge.prototype._setValue_array_setMatrixWorldNeedsUpdate],[Ge.prototype._setValue_arrayElement,Ge.prototype._setValue_arrayElement_setNeedsUpdate,Ge.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[Ge.prototype._setValue_fromArray,Ge.prototype._setValue_fromArray_setNeedsUpdate,Ge.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var L_=new Float32Array(1);var ss=class extends xo{constructor(t,e,n=1){super(t,e),this.isInstancedInterleavedBuffer=!0,this.meshPerAttribute=n}copy(t){return super.copy(t),this.meshPerAttribute=t.meshPerAttribute,this}clone(t){let e=super.clone(t);return e.meshPerAttribute=this.meshPerAttribute,e}toJSON(t){let e=super.toJSON(t);return e.isInstancedInterleavedBuffer=!0,e.meshPerAttribute=this.meshPerAttribute,e}};var uh=class uh{constructor(t,e,n,s){this.elements=[1,0,0,1],t!==void 0&&this.set(t,e,n,s)}identity(){return this.set(1,0,0,1),this}fromArray(t,e=0){for(let n=0;n<4;n++)this.elements[n]=t[n+e];return this}set(t,e,n,s){let r=this.elements;return r[0]=t,r[2]=e,r[1]=n,r[3]=s,this}};uh.prototype.isMatrix2=!0;var Dl=uh;var _u=new C,no=new C,Ys=new C,js=new C,yl=new C,Zp=new C,$p=new C,fa=class{constructor(t=new C,e=new C){this.start=t,this.end=e}set(t,e){return this.start.copy(t),this.end.copy(e),this}copy(t){return this.start.copy(t.start),this.end.copy(t.end),this}getCenter(t){return t.addVectors(this.start,this.end).multiplyScalar(.5)}delta(t){return t.subVectors(this.end,this.start)}distanceSq(){return this.start.distanceToSquared(this.end)}distance(){return this.start.distanceTo(this.end)}at(t,e){return this.delta(e).multiplyScalar(t).add(this.start)}closestPointToPointParameter(t,e){_u.subVectors(t,this.start),no.subVectors(this.end,this.start);let n=no.dot(no);if(n===0)return 0;let r=no.dot(_u)/n;return e&&(r=le(r,0,1)),r}closestPointToPoint(t,e,n){let s=this.closestPointToPointParameter(t,e);return this.delta(n).multiplyScalar(s).add(this.start)}distanceSqToLine3(t,e=Zp,n=$p){let s=10000000000000001e-32,r,a,o=this.start,c=t.start,l=this.end,u=t.end;Ys.subVectors(l,o),js.subVectors(u,c),yl.subVectors(o,c);let d=Ys.dot(Ys),h=js.dot(js),f=js.dot(yl);if(d<=s&&h<=s)return e.copy(o),n.copy(c),e.sub(n),e.dot(e);if(d<=s)r=0,a=f/h,a=le(a,0,1);else{let g=Ys.dot(yl);if(h<=s)a=0,r=le(-g/d,0,1);else{let x=Ys.dot(js),p=d*h-x*x;p!==0?r=le((x*f-g*h)/p,0,1):r=0,a=(x*r+f)/h,a<0?(a=0,r=le(-g/d,0,1)):a>1&&(a=1,r=le((x-g)/d,0,1))}}return e.copy(o).addScaledVector(Ys,r),n.copy(c).addScaledVector(js,a),e.distanceToSquared(n)}applyMatrix4(t){return this.start.applyMatrix4(t),this.end.applyMatrix4(t),this}equals(t){return t.start.equals(this.start)&&t.end.equals(this.end)}clone(){return new this.constructor().copy(this)}};function ah(i,t,e,n){let s=Jp(n);switch(e){case Jl:return i*t;case Zo:return i*t/s.components*s.byteLength;case $o:return i*t/s.components*s.byteLength;case yi:return i*t*2/s.components*s.byteLength;case Jo:return i*t*2/s.components*s.byteLength;case Kl:return i*t*3/s.components*s.byteLength;case Yn:return i*t*4/s.components*s.byteLength;case Ko:return i*t*4/s.components*s.byteLength;case va:case xa:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*8;case _a:case ya:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*16;case tc:case nc:return Math.max(i,16)*Math.max(t,8)/4;case Qo:case ec:return Math.max(i,8)*Math.max(t,8)/2;case ic:case sc:case ac:case oc:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*8;case rc:case Ma:case cc:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*16;case lc:return Math.floor((i+3)/4)*Math.floor((t+3)/4)*16;case hc:return Math.floor((i+4)/5)*Math.floor((t+3)/4)*16;case uc:return Math.floor((i+4)/5)*Math.floor((t+4)/5)*16;case dc:return Math.floor((i+5)/6)*Math.floor((t+4)/5)*16;case fc:return Math.floor((i+5)/6)*Math.floor((t+5)/6)*16;case pc:return Math.floor((i+7)/8)*Math.floor((t+4)/5)*16;case mc:return Math.floor((i+7)/8)*Math.floor((t+5)/6)*16;case gc:return Math.floor((i+7)/8)*Math.floor((t+7)/8)*16;case vc:return Math.floor((i+9)/10)*Math.floor((t+4)/5)*16;case xc:return Math.floor((i+9)/10)*Math.floor((t+5)/6)*16;case _c:return Math.floor((i+9)/10)*Math.floor((t+7)/8)*16;case yc:return Math.floor((i+9)/10)*Math.floor((t+9)/10)*16;case Mc:return Math.floor((i+11)/12)*Math.floor((t+9)/10)*16;case Sc:return Math.floor((i+11)/12)*Math.floor((t+11)/12)*16;case bc:case Ec:case wc:return Math.ceil(i/4)*Math.ceil(t/4)*16;case Tc:case Ac:return Math.ceil(i/4)*Math.ceil(t/4)*8;case Sa:case Rc:return Math.ceil(i/4)*Math.ceil(t/4)*16}throw new Error(`Unable to determine texture byte length for ${e} format.`)}function Jp(i){switch(i){case Ln:case Yl:return{byteLength:1,components:1};case dr:case jl:case Bn:return{byteLength:2,components:1};case Yo:case jo:return{byteLength:2,components:4};case li:case qo:case qn:return{byteLength:4,components:1};case Zl:case $l:return{byteLength:4,components:3}}throw new Error(`THREE.TextureUtils: Unknown texture type ${i}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"186"}}));typeof window<"u"&&(window.__THREE__?ie("WARNING: Multiple instances of Three.js being imported."):window.__THREE__="186");function Id(){let i=null,t=!1,e=null,n=null;function s(r,a){n=i.requestAnimationFrame(s),e(r,a)}return{start:function(){t!==!0&&e!==null&&i!==null&&(n=i.requestAnimationFrame(s),t=!0)},stop:function(){i!==null&&i.cancelAnimationFrame(n),t=!1},setAnimationLoop:function(r){e=r},setContext:function(r){i=r}}}function Qp(i){let t=new WeakMap;function e(o,c){let l=o.array,u=o.usage,d=l.byteLength,h=i.createBuffer();i.bindBuffer(c,h),i.bufferData(c,l,u),o.onUploadCallback();let f;if(l instanceof Float32Array)f=i.FLOAT;else if(typeof Float16Array<"u"&&l instanceof Float16Array)f=i.HALF_FLOAT;else if(l instanceof Uint16Array)o.isFloat16BufferAttribute?f=i.HALF_FLOAT:f=i.UNSIGNED_SHORT;else if(l instanceof Int16Array)f=i.SHORT;else if(l instanceof Uint32Array)f=i.UNSIGNED_INT;else if(l instanceof Int32Array)f=i.INT;else if(l instanceof Int8Array)f=i.BYTE;else if(l instanceof Uint8Array)f=i.UNSIGNED_BYTE;else if(l instanceof Uint8ClampedArray)f=i.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+l);return{buffer:h,type:f,bytesPerElement:l.BYTES_PER_ELEMENT,version:o.version,size:d}}function n(o,c,l){let u=c.array,d=c.updateRanges;if(i.bindBuffer(l,o),d.length===0)i.bufferSubData(l,0,u);else{d.sort((f,g)=>f.start-g.start);let h=0;for(let f=1;f<d.length;f++){let g=d[h],x=d[f];x.start<=g.start+g.count+1?g.count=Math.max(g.count,x.start+x.count-g.start):(++h,d[h]=x)}d.length=h+1;for(let f=0,g=d.length;f<g;f++){let x=d[f];i.bufferSubData(l,x.start*u.BYTES_PER_ELEMENT,u,x.start,x.count)}c.clearUpdateRanges()}c.onUploadCallback()}function s(o){return o.isInterleavedBufferAttribute&&(o=o.data),t.get(o)}function r(o){o.isInterleavedBufferAttribute&&(o=o.data);let c=t.get(o);c&&(i.deleteBuffer(c.buffer),t.delete(o))}function a(o,c){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){let u=t.get(o);(!u||u.version<o.version)&&t.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}let l=t.get(o);if(l===void 0)t.set(o,e(o,c));else if(l.version<o.version){if(l.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");n(l.buffer,o,c),l.version=o.version}}return{get:s,remove:r,update:a}}var t0=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,e0=`#ifdef USE_ALPHAHASH
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
#endif`,n0=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,i0=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,s0=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,r0=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,a0=`#ifdef USE_AOMAP
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
#endif`,o0=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,c0=`#ifdef USE_BATCHING
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
#endif`,l0=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,h0=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,u0=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,d0=`float G_BlinnPhong_Implicit( ) {
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
} // validated`,f0=`#ifdef USE_IRIDESCENCE
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
#endif`,p0=`#ifdef USE_BUMPMAP
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
#endif`,m0=`#if NUM_CLIPPING_PLANES > 0
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
#endif`,g0=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,v0=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,x0=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,_0=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,y0=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,M0=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,S0=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
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
#endif`,b0=`#define PI 3.141592653589793
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
} // validated`,E0=`#ifdef ENVMAP_TYPE_CUBE_UV
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
#endif`,w0=`vec3 transformedNormal = objectNormal;
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
#endif`,T0=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,A0=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,R0=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,C0=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,P0="gl_FragColor = linearToOutputTexel( gl_FragColor );",I0=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,L0=`#ifdef USE_ENVMAP
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
#endif`,D0=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,U0=`#ifdef USE_ENVMAP
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
#endif`,N0=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,F0=`#ifdef USE_ENVMAP
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
#endif`,z0=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,O0=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,B0=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,k0=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,H0=`#ifdef USE_GRADIENTMAP
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
}`,V0=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,G0=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,W0=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,X0=`uniform bool receiveShadow;
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
#include <lightprobes_pars_fragment>`,q0=`#ifdef USE_ENVMAP
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
#endif`,Y0=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,j0=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,Z0=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,$0=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,J0=`PhysicalMaterial material;
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
#endif`,K0=`uniform sampler2D dfgLUT;
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
}`,Q0=`
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
#endif`,tm=`#if defined( RE_IndirectDiffuse )
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
#endif`,em=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,nm=`#ifdef USE_LIGHT_PROBES_GRID
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
#endif`,im=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,sm=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,rm=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,am=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,om=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,cm=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,lm=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
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
#endif`,hm=`#if defined( USE_POINTS_UV )
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
#endif`,um=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,dm=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,fm=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,pm=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,mm=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,gm=`#ifdef USE_MORPHTARGETS
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
#endif`,vm=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,xm=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
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
vec3 nonPerturbedNormal = normal;`,_m=`#ifdef USE_NORMALMAP_OBJECTSPACE
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
#endif`,ym=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Mm=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Sm=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
		#ifdef FLIP_SIDED
			vBitangent = - vBitangent;
		#endif
	#endif
#endif`,bm=`#ifdef USE_NORMALMAP
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
#endif`,Em=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,wm=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,Tm=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,Am=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,Rm=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,Cm=`vec3 packNormalToRGB( const in vec3 normal ) {
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
}`,Pm=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,Im=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,Lm=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,Dm=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,Um=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,Nm=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,Fm=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,zm=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,Om=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_SUN_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
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
#endif`,Bm=`float getShadowMask() {
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
}`,km=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,Hm=`#ifdef USE_SKINNING
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
#endif`,Vm=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,Gm=`#ifdef USE_SKINNING
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
#endif`,Wm=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,Xm=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,qm=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,Ym=`#ifndef saturate
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
vec3 CustomToneMapping( vec3 color ) { return color; }`,jm=`#ifdef USE_TRANSMISSION
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
#endif`,Zm=`#ifdef USE_TRANSMISSION
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
#endif`,$m=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,Jm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,Km=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,Qm=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,tg=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,eg=`uniform sampler2D t2D;
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
}`,ng=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,ig=`#ifdef ENVMAP_TYPE_CUBE
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
}`,sg=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,rg=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,ag=`#include <common>
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
}`,og=`#if DEPTH_PACKING == 3200
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
}`,cg=`#define DISTANCE
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
}`,lg=`#define DISTANCE
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
}`,hg=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,ug=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,dg=`uniform float scale;
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
}`,fg=`uniform vec3 diffuse;
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
}`,pg=`#include <common>
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
}`,mg=`uniform vec3 diffuse;
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
}`,gg=`#define LAMBERT
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
}`,vg=`#define LAMBERT
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
}`,xg=`#define MATCAP
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
}`,_g=`#define MATCAP
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
}`,yg=`#define NORMAL
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
}`,Mg=`#define NORMAL
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
}`,Sg=`#define PHONG
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
}`,bg=`#define PHONG
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
}`,Eg=`#define STANDARD
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
}`,wg=`#define STANDARD
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
}`,Tg=`#define TOON
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
}`,Ag=`#define TOON
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
}`,Rg=`uniform float size;
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
}`,Cg=`uniform vec3 diffuse;
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
}`,Pg=`#include <common>
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
}`,Ig=`uniform vec3 color;
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
}`,Lg=`uniform float rotation;
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
}`,Dg=`uniform vec3 diffuse;
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
}`,me={alphahash_fragment:t0,alphahash_pars_fragment:e0,alphamap_fragment:n0,alphamap_pars_fragment:i0,alphatest_fragment:s0,alphatest_pars_fragment:r0,aomap_fragment:a0,aomap_pars_fragment:o0,batching_pars_vertex:c0,batching_vertex:l0,begin_vertex:h0,beginnormal_vertex:u0,bsdfs:d0,iridescence_fragment:f0,bumpmap_pars_fragment:p0,clipping_planes_fragment:m0,clipping_planes_pars_fragment:g0,clipping_planes_pars_vertex:v0,clipping_planes_vertex:x0,color_fragment:_0,color_pars_fragment:y0,color_pars_vertex:M0,color_vertex:S0,common:b0,cube_uv_reflection_fragment:E0,defaultnormal_vertex:w0,displacementmap_pars_vertex:T0,displacementmap_vertex:A0,emissivemap_fragment:R0,emissivemap_pars_fragment:C0,colorspace_fragment:P0,colorspace_pars_fragment:I0,envmap_fragment:L0,envmap_common_pars_fragment:D0,envmap_pars_fragment:U0,envmap_pars_vertex:N0,envmap_physical_pars_fragment:q0,envmap_vertex:F0,fog_vertex:z0,fog_pars_vertex:O0,fog_fragment:B0,fog_pars_fragment:k0,gradientmap_pars_fragment:H0,lightmap_pars_fragment:V0,lights_lambert_fragment:G0,lights_lambert_pars_fragment:W0,lights_pars_begin:X0,lights_toon_fragment:Y0,lights_toon_pars_fragment:j0,lights_phong_fragment:Z0,lights_phong_pars_fragment:$0,lights_physical_fragment:J0,lights_physical_pars_fragment:K0,lights_fragment_begin:Q0,lights_fragment_maps:tm,lights_fragment_end:em,lightprobes_pars_fragment:nm,logdepthbuf_fragment:im,logdepthbuf_pars_fragment:sm,logdepthbuf_pars_vertex:rm,logdepthbuf_vertex:am,map_fragment:om,map_pars_fragment:cm,map_particle_fragment:lm,map_particle_pars_fragment:hm,metalnessmap_fragment:um,metalnessmap_pars_fragment:dm,morphinstance_vertex:fm,morphcolor_vertex:pm,morphnormal_vertex:mm,morphtarget_pars_vertex:gm,morphtarget_vertex:vm,normal_fragment_begin:xm,normal_fragment_maps:_m,normal_pars_fragment:ym,normal_pars_vertex:Mm,normal_vertex:Sm,normalmap_pars_fragment:bm,clearcoat_normal_fragment_begin:Em,clearcoat_normal_fragment_maps:wm,clearcoat_pars_fragment:Tm,iridescence_pars_fragment:Am,opaque_fragment:Rm,packing:Cm,premultiplied_alpha_fragment:Pm,project_vertex:Im,dithering_fragment:Lm,dithering_pars_fragment:Dm,roughnessmap_fragment:Um,roughnessmap_pars_fragment:Nm,shadowmap_pars_fragment:Fm,shadowmap_pars_vertex:zm,shadowmap_vertex:Om,shadowmask_pars_fragment:Bm,skinbase_vertex:km,skinning_pars_vertex:Hm,skinning_vertex:Vm,skinnormal_vertex:Gm,specularmap_fragment:Wm,specularmap_pars_fragment:Xm,tonemapping_fragment:qm,tonemapping_pars_fragment:Ym,transmission_fragment:jm,transmission_pars_fragment:Zm,uv_pars_fragment:$m,uv_pars_vertex:Jm,uv_vertex:Km,worldpos_vertex:Qm,background_vert:tg,background_frag:eg,backgroundCube_vert:ng,backgroundCube_frag:ig,cube_vert:sg,cube_frag:rg,depth_vert:ag,depth_frag:og,distance_vert:cg,distance_frag:lg,equirect_vert:hg,equirect_frag:ug,linedashed_vert:dg,linedashed_frag:fg,meshbasic_vert:pg,meshbasic_frag:mg,meshlambert_vert:gg,meshlambert_frag:vg,meshmatcap_vert:xg,meshmatcap_frag:_g,meshnormal_vert:yg,meshnormal_frag:Mg,meshphong_vert:Sg,meshphong_frag:bg,meshphysical_vert:Eg,meshphysical_frag:wg,meshtoon_vert:Tg,meshtoon_frag:Ag,points_vert:Rg,points_frag:Cg,shadow_vert:Pg,shadow_frag:Ig,sprite_vert:Lg,sprite_frag:Dg},Nt={common:{diffuse:{value:new Wt(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new he},alphaMap:{value:null},alphaMapTransform:{value:new he},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new he}},envmap:{envMap:{value:null},envMapRotation:{value:new he},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new he}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new he}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new he},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new he},normalScale:{value:new vt(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new he},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new he}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new he}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new he}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new Wt(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},sunLights:{value:[],properties:{direction:{},color:{}}},sunLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},sunShadowMatrix:{value:[]},sunShadowCascade:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new C},probesMax:{value:new C},probesResolution:{value:new C}},points:{diffuse:{value:new Wt(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new he},alphaTest:{value:0},uvTransform:{value:new he}},sprite:{diffuse:{value:new Wt(16777215)},opacity:{value:1},center:{value:new vt(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new he},alphaMap:{value:null},alphaMapTransform:{value:new he},alphaTest:{value:0}}},An={basic:{uniforms:xn([Nt.common,Nt.specularmap,Nt.envmap,Nt.aomap,Nt.lightmap,Nt.fog]),vertexShader:me.meshbasic_vert,fragmentShader:me.meshbasic_frag},lambert:{uniforms:xn([Nt.common,Nt.specularmap,Nt.envmap,Nt.aomap,Nt.lightmap,Nt.emissivemap,Nt.bumpmap,Nt.normalmap,Nt.displacementmap,Nt.fog,Nt.lights,{emissive:{value:new Wt(0)},envMapIntensity:{value:1}}]),vertexShader:me.meshlambert_vert,fragmentShader:me.meshlambert_frag},phong:{uniforms:xn([Nt.common,Nt.specularmap,Nt.envmap,Nt.aomap,Nt.lightmap,Nt.emissivemap,Nt.bumpmap,Nt.normalmap,Nt.displacementmap,Nt.fog,Nt.lights,{emissive:{value:new Wt(0)},specular:{value:new Wt(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:me.meshphong_vert,fragmentShader:me.meshphong_frag},standard:{uniforms:xn([Nt.common,Nt.envmap,Nt.aomap,Nt.lightmap,Nt.emissivemap,Nt.bumpmap,Nt.normalmap,Nt.displacementmap,Nt.roughnessmap,Nt.metalnessmap,Nt.fog,Nt.lights,{emissive:{value:new Wt(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:me.meshphysical_vert,fragmentShader:me.meshphysical_frag},toon:{uniforms:xn([Nt.common,Nt.aomap,Nt.lightmap,Nt.emissivemap,Nt.bumpmap,Nt.normalmap,Nt.displacementmap,Nt.gradientmap,Nt.fog,Nt.lights,{emissive:{value:new Wt(0)}}]),vertexShader:me.meshtoon_vert,fragmentShader:me.meshtoon_frag},matcap:{uniforms:xn([Nt.common,Nt.bumpmap,Nt.normalmap,Nt.displacementmap,Nt.fog,{matcap:{value:null}}]),vertexShader:me.meshmatcap_vert,fragmentShader:me.meshmatcap_frag},points:{uniforms:xn([Nt.points,Nt.fog]),vertexShader:me.points_vert,fragmentShader:me.points_frag},dashed:{uniforms:xn([Nt.common,Nt.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:me.linedashed_vert,fragmentShader:me.linedashed_frag},depth:{uniforms:xn([Nt.common,Nt.displacementmap]),vertexShader:me.depth_vert,fragmentShader:me.depth_frag},normal:{uniforms:xn([Nt.common,Nt.bumpmap,Nt.normalmap,Nt.displacementmap,{opacity:{value:1}}]),vertexShader:me.meshnormal_vert,fragmentShader:me.meshnormal_frag},sprite:{uniforms:xn([Nt.sprite,Nt.fog]),vertexShader:me.sprite_vert,fragmentShader:me.sprite_frag},background:{uniforms:{uvTransform:{value:new he},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:me.background_vert,fragmentShader:me.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new he}},vertexShader:me.backgroundCube_vert,fragmentShader:me.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:me.cube_vert,fragmentShader:me.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:me.equirect_vert,fragmentShader:me.equirect_frag},distance:{uniforms:xn([Nt.common,Nt.displacementmap,{referencePosition:{value:new C},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:me.distance_vert,fragmentShader:me.distance_frag},shadow:{uniforms:xn([Nt.lights,Nt.fog,{color:{value:new Wt(0)},opacity:{value:1}}]),vertexShader:me.shadow_vert,fragmentShader:me.shadow_frag}};An.physical={uniforms:xn([An.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new he},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new he},clearcoatNormalScale:{value:new vt(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new he},dispersion:{value:0},retroreflectivity:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new he},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new he},sheen:{value:0},sheenColor:{value:new Wt(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new he},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new he},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new he},transmissionSamplerSize:{value:new vt},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new he},attenuationDistance:{value:0},attenuationColor:{value:new Wt(0)},specularColor:{value:new Wt(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new he},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new he},anisotropyVector:{value:new vt},anisotropyMap:{value:null},anisotropyMapTransform:{value:new he}}]),vertexShader:me.meshphysical_vert,fragmentShader:me.meshphysical_frag};var Lc={r:0,b:0,g:0},Ug=new de,Ld=new he;Ld.set(-1,0,0,0,1,0,0,0,1);function Ng(i,t,e,n,s,r){let a=new Wt(0),o=s===!0?0:1,c,l,u=null,d=0,h=null;function f(y){let E=y.isScene===!0?y.background:null;if(E&&E.isTexture){let v=y.backgroundBlurriness>0;E=t.get(E,v)}return E}function g(y){let E=!1,v=f(y);v===null?p(a,o):v&&v.isColor&&(p(v,1),E=!0);let b=i.xr.getEnvironmentBlendMode();b==="additive"?e.buffers.color.setClear(0,0,0,1,r):b==="alpha-blend"&&e.buffers.color.setClear(0,0,0,0,r),(i.autoClear||E)&&(e.buffers.depth.setTest(!0),e.buffers.depth.setMask(!0),e.buffers.color.setMask(!0),i.clear(i.autoClearColor,i.autoClearDepth,i.autoClearStencil))}function x(y,E){let v=f(E);v&&(v.isCubeTexture||v.mapping===ma)?(l===void 0&&(l=new ct(new Ce(1,1,1),new Oe({name:"BackgroundCubeMaterial",uniforms:ws(An.backgroundCube.uniforms),vertexShader:An.backgroundCube.vertexShader,fragmentShader:An.backgroundCube.fragmentShader,side:on,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),l.geometry.deleteAttribute("uv"),l.onBeforeRender=function(b,M,A){this.matrixWorld.copyPosition(A.matrixWorld)},Object.defineProperty(l.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),n.update(l)),l.material.uniforms.envMap.value=v,l.material.uniforms.backgroundBlurriness.value=E.backgroundBlurriness,l.material.uniforms.backgroundIntensity.value=E.backgroundIntensity,l.material.uniforms.backgroundRotation.value.setFromMatrix4(Ug.makeRotationFromEuler(E.backgroundRotation)).transpose(),v.isCubeTexture&&v.isRenderTargetTexture===!1&&l.material.uniforms.backgroundRotation.value.premultiply(Ld),l.material.toneMapped=Me.getTransfer(v.colorSpace)!==Ie,(u!==v||d!==v.version||h!==i.toneMapping)&&(l.material.needsUpdate=!0,u=v,d=v.version,h=i.toneMapping),l.layers.enableAll(),y.unshift(l,l.geometry,l.material,0,0,null)):v&&v.isTexture&&(c===void 0&&(c=new ct(new je(2,2),new Oe({name:"BackgroundMaterial",uniforms:ws(An.background.uniforms),vertexShader:An.background.vertexShader,fragmentShader:An.background.fragmentShader,side:rs,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),Object.defineProperty(c.material,"map",{get:function(){return this.uniforms.t2D.value}}),n.update(c)),c.material.uniforms.t2D.value=v,c.material.uniforms.backgroundIntensity.value=E.backgroundIntensity,c.material.toneMapped=Me.getTransfer(v.colorSpace)!==Ie,v.matrixAutoUpdate===!0&&v.updateMatrix(),c.material.uniforms.uvTransform.value.copy(v.matrix),(u!==v||d!==v.version||h!==i.toneMapping)&&(c.material.needsUpdate=!0,u=v,d=v.version,h=i.toneMapping),c.layers.enableAll(),y.unshift(c,c.geometry,c.material,0,0,null))}function p(y,E){y.getRGB(Lc,ih(i)),e.buffers.color.setClear(Lc.r,Lc.g,Lc.b,E,r)}function m(){l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0),c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0)}return{getClearColor:function(){return a},setClearColor:function(y,E=1){a.set(y),o=E,p(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(y){o=y,p(a,o)},render:g,addToRenderList:x,dispose:m}}function Fg(i,t){let e=i.getParameter(i.MAX_VERTEX_ATTRIBS),n={},s=h(null),r=s,a=!1;function o(L,F,V,I,z){let q=!1,j=d(L,I,V,F);r!==j&&(r=j,l(r.object)),q=f(L,I,V,z),q&&g(L,I,V,z),z!==null&&t.update(z,i.ELEMENT_ARRAY_BUFFER),(q||a)&&(a=!1,v(L,F,V,I),z!==null&&i.bindBuffer(i.ELEMENT_ARRAY_BUFFER,t.get(z).buffer))}function c(){return i.createVertexArray()}function l(L){return i.bindVertexArray(L)}function u(L){return i.deleteVertexArray(L)}function d(L,F,V,I){let z=I.wireframe===!0,q=n[F.id];q===void 0&&(q={},n[F.id]=q);let j=L.isInstancedMesh===!0?L.id:0,at=q[j];at===void 0&&(at={},q[j]=at);let K=at[V.id];K===void 0&&(K={},at[V.id]=K);let st=K[z];return st===void 0&&(st=h(c()),K[z]=st),st}function h(L){let F=[],V=[],I=[];for(let z=0;z<e;z++)F[z]=0,V[z]=0,I[z]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:F,enabledAttributes:V,attributeDivisors:I,object:L,attributes:{},index:null}}function f(L,F,V,I){let z=r.attributes,q=F.attributes,j=0,at=V.getAttributes();for(let K in at)if(at[K].location>=0){let it=z[K],Rt=q[K];if(Rt===void 0&&(K==="instanceMatrix"&&L.instanceMatrix&&(Rt=L.instanceMatrix),K==="instanceColor"&&L.instanceColor&&(Rt=L.instanceColor)),it===void 0||it.attribute!==Rt||Rt&&it.data!==Rt.data)return!0;j++}return r.attributesNum!==j||r.index!==I}function g(L,F,V,I){let z={},q=F.attributes,j=0,at=V.getAttributes();for(let K in at)if(at[K].location>=0){let it=q[K];it===void 0&&(K==="instanceMatrix"&&L.instanceMatrix&&(it=L.instanceMatrix),K==="instanceColor"&&L.instanceColor&&(it=L.instanceColor));let Rt={};Rt.attribute=it,it&&it.data&&(Rt.data=it.data),z[K]=Rt,j++}r.attributes=z,r.attributesNum=j,r.index=I}function x(){let L=r.newAttributes;for(let F=0,V=L.length;F<V;F++)L[F]=0}function p(L){m(L,0)}function m(L,F){let V=r.newAttributes,I=r.enabledAttributes,z=r.attributeDivisors;V[L]=1,I[L]===0&&(i.enableVertexAttribArray(L),I[L]=1),z[L]!==F&&(i.vertexAttribDivisor(L,F),z[L]=F)}function y(){let L=r.newAttributes,F=r.enabledAttributes;for(let V=0,I=F.length;V<I;V++)F[V]!==L[V]&&(i.disableVertexAttribArray(V),F[V]=0)}function E(L,F,V,I,z,q,j){j===!0?i.vertexAttribIPointer(L,F,V,z,q):i.vertexAttribPointer(L,F,V,I,z,q)}function v(L,F,V,I){x();let z=I.attributes,q=V.getAttributes(),j=F.defaultAttributeValues;for(let at in q){let K=q[at];if(K.location>=0){let st=z[at];if(st===void 0&&(at==="instanceMatrix"&&L.instanceMatrix&&(st=L.instanceMatrix),at==="instanceColor"&&L.instanceColor&&(st=L.instanceColor)),st!==void 0){let it=st.normalized,Rt=st.itemSize,mt=t.get(st);if(mt===void 0)continue;let Ut=mt.buffer,Dt=mt.type,ft=mt.bytesPerElement,N=Dt===i.INT||Dt===i.UNSIGNED_INT||st.gpuType===qo;if(st.isInterleavedBufferAttribute){let k=st.data,dt=k.stride,St=st.offset;if(k.isInstancedInterleavedBuffer){for(let Mt=0;Mt<K.locationSize;Mt++)m(K.location+Mt,k.meshPerAttribute);L.isInstancedMesh!==!0&&I._maxInstanceCount===void 0&&(I._maxInstanceCount=k.meshPerAttribute*k.count)}else for(let Mt=0;Mt<K.locationSize;Mt++)p(K.location+Mt);i.bindBuffer(i.ARRAY_BUFFER,Ut);for(let Mt=0;Mt<K.locationSize;Mt++)E(K.location+Mt,Rt/K.locationSize,Dt,it,dt*ft,(St+Rt/K.locationSize*Mt)*ft,N)}else{if(st.isInstancedBufferAttribute){for(let k=0;k<K.locationSize;k++)m(K.location+k,st.meshPerAttribute);L.isInstancedMesh!==!0&&I._maxInstanceCount===void 0&&(I._maxInstanceCount=st.meshPerAttribute*st.count)}else for(let k=0;k<K.locationSize;k++)p(K.location+k);i.bindBuffer(i.ARRAY_BUFFER,Ut);for(let k=0;k<K.locationSize;k++)E(K.location+k,Rt/K.locationSize,Dt,it,Rt*ft,Rt/K.locationSize*k*ft,N)}}else if(j!==void 0){let it=j[at];if(it!==void 0)switch(it.length){case 2:i.vertexAttrib2fv(K.location,it);break;case 3:i.vertexAttrib3fv(K.location,it);break;case 4:i.vertexAttrib4fv(K.location,it);break;default:i.vertexAttrib1fv(K.location,it)}}}}y()}function b(){T();for(let L in n){let F=n[L];for(let V in F){let I=F[V];for(let z in I){let q=I[z];for(let j in q)u(q[j].object),delete q[j];delete I[z]}}delete n[L]}}function M(L){if(n[L.id]===void 0)return;let F=n[L.id];for(let V in F){let I=F[V];for(let z in I){let q=I[z];for(let j in q)u(q[j].object),delete q[j];delete I[z]}}delete n[L.id]}function A(L){for(let F in n){let V=n[F];for(let I in V){let z=V[I];if(z[L.id]===void 0)continue;let q=z[L.id];for(let j in q)u(q[j].object),delete q[j];delete z[L.id]}}}function _(L){for(let F in n){let V=n[F],I=L.isInstancedMesh===!0?L.id:0,z=V[I];if(z!==void 0){for(let q in z){let j=z[q];for(let at in j)u(j[at].object),delete j[at];delete z[q]}delete V[I],Object.keys(V).length===0&&delete n[F]}}}function T(){P(),a=!0,r!==s&&(r=s,l(r.object))}function P(){s.geometry=null,s.program=null,s.wireframe=!1}return{setup:o,reset:T,resetDefaultState:P,dispose:b,releaseStatesOfGeometry:M,releaseStatesOfObject:_,releaseStatesOfProgram:A,initAttributes:x,enableAttribute:p,disableUnusedAttributes:y}}function zg(i,t,e){let n;function s(c){n=c}function r(c,l){i.drawArrays(n,c,l),e.update(l,n,1)}function a(c,l,u){u!==0&&(i.drawArraysInstanced(n,c,l,u),e.update(l,n,u))}function o(c,l,u){if(u===0)return;t.get("WEBGL_multi_draw").multiDrawArraysWEBGL(n,c,0,l,0,u);let h=0;for(let f=0;f<u;f++)h+=l[f];e.update(h,n,1)}this.setMode=s,this.render=r,this.renderInstances=a,this.renderMultiDraw=o}function Og(i,t,e,n){let s;function r(){if(s!==void 0)return s;if(t.has("EXT_texture_filter_anisotropic")===!0){let A=t.get("EXT_texture_filter_anisotropic");s=i.getParameter(A.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else s=0;return s}function a(A){return!(A!==Yn&&n.convert(A)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(A){let _=A===Bn&&(t.has("EXT_color_buffer_half_float")||t.has("EXT_color_buffer_float"));return!(A!==Ln&&A!==qn&&!_&&n.convert(A)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_TYPE))}function c(A){if(A==="highp"){if(i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.HIGH_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.HIGH_FLOAT).precision>0)return"highp";A="mediump"}return A==="mediump"&&i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.MEDIUM_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let l=e.precision!==void 0?e.precision:"highp",u=c(l);u!==l&&(ie("WebGLRenderer:",l,"not supported, using",u,"instead."),l=u);let d=e.logarithmicDepthBuffer===!0,h=e.reversedDepthBuffer===!0&&t.has("EXT_clip_control");e.reversedDepthBuffer===!0&&h===!1&&ie("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");let f=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),g=i.getParameter(i.MAX_VERTEX_TEXTURE_IMAGE_UNITS),x=i.getParameter(i.MAX_TEXTURE_SIZE),p=i.getParameter(i.MAX_CUBE_MAP_TEXTURE_SIZE),m=i.getParameter(i.MAX_VERTEX_ATTRIBS),y=i.getParameter(i.MAX_VERTEX_UNIFORM_VECTORS),E=i.getParameter(i.MAX_VARYING_VECTORS),v=i.getParameter(i.MAX_FRAGMENT_UNIFORM_VECTORS),b=i.getParameter(i.MAX_SAMPLES),M=i.getParameter(i.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:r,getMaxPrecision:c,textureFormatReadable:a,textureTypeReadable:o,precision:l,logarithmicDepthBuffer:d,reversedDepthBuffer:h,maxTextures:f,maxVertexTextures:g,maxTextureSize:x,maxCubemapSize:p,maxAttributes:m,maxVertexUniforms:y,maxVaryings:E,maxFragmentUniforms:v,maxSamples:b,samples:M}}function Bg(i){let t=this,e=null,n=0,s=!1,r=!1,a=new ni,o=new he,c={value:null,needsUpdate:!1};this.uniform=c,this.numPlanes=0,this.numIntersection=0,this.init=function(d,h){let f=d.length!==0||h||n!==0||s;return s=h,n=d.length,f},this.beginShadows=function(){r=!0,u(null)},this.endShadows=function(){r=!1},this.setGlobalState=function(d,h){e=u(d,h,0)},this.setState=function(d,h,f){let g=d.clippingPlanes,x=d.clipIntersection,p=d.clipShadows,m=i.get(d);if(!s||g===null||g.length===0||r&&!p)r?u(null):l();else{let y=r?0:n,E=y*4,v=m.clippingState||null;c.value=v,v=u(g,h,E,f);for(let b=0;b!==E;++b)v[b]=e[b];m.clippingState=v,this.numIntersection=x?this.numPlanes:0,this.numPlanes+=y}};function l(){c.value!==e&&(c.value=e,c.needsUpdate=n>0),t.numPlanes=n,t.numIntersection=0}function u(d,h,f,g){let x=d!==null?d.length:0,p=null;if(x!==0){if(p=c.value,g!==!0||p===null){let m=f+x*4,y=h.matrixWorldInverse;o.getNormalMatrix(y),(p===null||p.length<m)&&(p=new Float32Array(m));for(let E=0,v=f;E!==x;++E,v+=4)a.copy(d[E]).applyMatrix4(y,o),a.normal.toArray(p,v),p[v+3]=a.constant}c.value=p,c.needsUpdate=!0}return t.numPlanes=x,t.numIntersection=0,p}}var mr=4,kg=6,Hg=20,Vg=256,Ea=new lr,hd=new Wt,dh=null,fh=0,ph=0,mh=!1,Gg=new C,Ts=new C,vr=class{constructor(t){this._renderer=t,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(t,e=0,n=.1,s=100,r={}){let{size:a=256,position:o=Gg}=r;dh=this._renderer.getRenderTarget(),fh=this._renderer.getActiveCubeFace(),ph=this._renderer.getActiveMipmapLevel(),mh=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);let c=this._allocateTargets();return c.depthBuffer=!0,this._sceneToCubeUV(t,n,s,c,o),e>0&&this._blur(c,0,0,e),this._applyPMREM(c),this._cleanup(c),c}fromEquirectangular(t,e=null){return this._fromTexture(t,e)}fromCubemap(t,e=null){return this._fromTexture(t,e)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=fd(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=dd(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(t){this._lodMax=Math.floor(Math.log2(t)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let t=0;t<this._lodMeshes.length;t++)this._lodMeshes[t].geometry.dispose()}_cleanup(t){this._renderer.setRenderTarget(dh,fh,ph),this._renderer.xr.enabled=mh,t.scissorTest=!1,pr(t,0,0,t.width,t.height)}_fromTexture(t,e){t.mapping===os||t.mapping===Es?this._setSize(t.image.length===0?16:t.image[0].width||t.image[0].image.width):this._setSize(t.image.width/4),dh=this._renderer.getRenderTarget(),fh=this._renderer.getActiveCubeFace(),ph=this._renderer.getActiveMipmapLevel(),mh=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let n=e||this._allocateTargets();return this._textureToCubeUV(t,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){let t=3*Math.max(this._cubeSize,112),e=4*this._cubeSize,n={magFilter:Ke,minFilter:Ke,generateMipmaps:!1,type:Bn,format:Yn,colorSpace:Nr,depthBuffer:!1},s=ud(t,e,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==t||this._pingPongRenderTarget.height!==e){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=ud(t,e,n);let{_lodMax:r}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods}=Wg(r)),this._blurMaterial=qg(r,t,e),this._ggxMaterial=Xg(r,t,e)}return s}_compileMaterial(t){let e=new ct(new ge,t);this._renderer.compile(e,Ea)}_sceneToCubeUV(t,e,n,s,r){let c=new Je(90,1,e,n),l=[1,-1,1,1,1,1],u=[1,1,1,-1,-1,-1],d=this._renderer,h=d.autoClear,f=d.toneMapping;d.getClearColor(hd),d.toneMapping=On,d.autoClear=!1,d.state.buffers.depth.getReversed()&&(d.setRenderTarget(s),d.clearDepth(),d.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new ct(new Ce,new oi({name:"PMREM.Background",side:on,depthWrite:!1,depthTest:!1})));let x=this._backgroundBox,p=x.material,m=!1,y=t.background;y?y.isColor&&(p.color.copy(y),t.background=null,m=!0):(p.color.copy(hd),m=!0);for(let E=0;E<6;E++){let v=E%3;v===0?(c.up.set(0,l[E],0),c.position.set(r.x,r.y,r.z),c.lookAt(r.x+u[E],r.y,r.z)):v===1?(c.up.set(0,0,l[E]),c.position.set(r.x,r.y,r.z),c.lookAt(r.x,r.y+u[E],r.z)):(c.up.set(0,l[E],0),c.position.set(r.x,r.y,r.z),c.lookAt(r.x,r.y,r.z+u[E]));let b=this._cubeSize;pr(s,v*b,E>2?b:0,b,b),d.setRenderTarget(s),m&&d.render(x,c),d.render(t,c)}d.toneMapping=f,d.autoClear=h,t.background=y}_textureToCubeUV(t,e){let n=this._renderer,s=t.mapping===os||t.mapping===Es;s?(this._cubemapMaterial===null&&(this._cubemapMaterial=fd()),this._cubemapMaterial.uniforms.flipEnvMap.value=t.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=dd());let r=s?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=r;let o=r.uniforms;o.envMap.value=t;let c=this._cubeSize;pr(e,0,0,3*c,2*c),n.setRenderTarget(e),n.render(a,Ea)}_applyPMREM(t){let e=this._renderer,n=e.autoClear;e.autoClear=!1;let s=this._lodMeshes.length;for(let r=1;r<s;r++)this._applyGGXFilter(t,r-1,r);e.autoClear=n}_applyGGXFilter(t,e,n){let s=this._renderer,r=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[n];o.material=a;let c=a.uniforms,l=n/(this._lodMeshes.length-1),u=e/(this._lodMeshes.length-1),d=Math.sqrt(l*l-u*u),h=l*1.25,f=d*h,{_lodMax:g}=this,x=this._sizeLods[n],p=3*x*(n>g-mr?n-g+mr:0),m=4*(this._cubeSize-x);c.envMap.value=t.texture,c.roughness.value=f,c.mipInt.value=g-e,pr(r,p,m,3*x,2*x),s.setRenderTarget(r),s.render(o,Ea),c.envMap.value=r.texture,c.roughness.value=0,c.mipInt.value=g-n,pr(t,p,m,3*x,2*x),s.setRenderTarget(t),s.render(o,Ea)}_blur(t,e,n,s){let r=this._pingPongRenderTarget,a=Math.min(s,Math.PI)/Math.SQRT2;this._blurPass(t,r,e,n,a),this._blurPass(r,t,n,n,a)}_blurPass(t,e,n,s,r){let a=this._renderer,o=this._blurMaterial,c=this._lodMeshes[s];c.material=o;let l=o.uniforms;l.envMap.value=t.texture,l.sigma.value=r,l.mipInt.value=this._lodMax-n;let u=this._sizeLods[s],d=3*u*(s>this._lodMax-mr?s-this._lodMax+mr:0),h=4*(this._cubeSize-u);pr(e,d,h,3*u,2*u),a.setRenderTarget(e),a.render(c,Ea)}};function Wg(i){let t=[],e=[],n=i,s=i-mr+1+kg;for(let r=0;r<s;r++){let a=Math.pow(2,n);t.push(a);let o=1/(a-2),c=-o,l=1+o,u=[c,c,l,c,l,l,c,c,l,l,c,l],d=6,h=6,f=3,g=new Float32Array(f*h*d),x=new Float32Array(f*h*d);for(let m=0;m<d;m++){let y=m%3*2/3-1,E=m>2?0:-1,v=[y,E,0,y+2/3,E,0,y+2/3,E+1,0,y,E,0,y+2/3,E+1,0,y,E+1,0];g.set(v,f*h*m);for(let b=0;b<h;b++){let M=u[b*2]*2-1,A=u[b*2+1]*2-1;m===0?Ts.set(1,A,M):m===1?Ts.set(-M,1,-A):m===2?Ts.set(-M,A,1):m===3?Ts.set(-1,A,-M):m===4?Ts.set(-M,-1,A):Ts.set(M,A,-1),Ts.toArray(x,(m*h+b)*f)}}let p=new ge;p.setAttribute("position",new Ue(g,f)),p.setAttribute("outputDirection",new Ue(x,f)),e.push(new ct(p,null)),n>mr&&n--}return{lodMeshes:e,sizeLods:t}}function ud(i,t,e){let n=new In(i,t,e);return n.texture.mapping=ma,n.texture.name="PMREM.cubeUv",n.scissorTest=!0,n}function pr(i,t,e,n,s){i.viewport.set(t,e,n,s),i.scissor.set(t,e,n,s)}function Xg(i,t,e){return new Oe({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:Vg,CUBEUV_TEXEL_WIDTH:1/t,CUBEUV_TEXEL_HEIGHT:1/e,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:Fc(),fragmentShader:`

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
		`,blending:_i,depthTest:!1,depthWrite:!1})}function qg(i,t,e){return new Oe({name:"SphericalGaussianBlur",defines:{SAMPLES:Hg,CUBEUV_TEXEL_WIDTH:1/t,CUBEUV_TEXEL_HEIGHT:1/e,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},sigma:{value:0},mipInt:{value:0}},vertexShader:Fc(),fragmentShader:`

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
		`,blending:_i,depthTest:!1,depthWrite:!1})}function dd(){return new Oe({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Fc(),fragmentShader:`

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
		`,blending:_i,depthTest:!1,depthWrite:!1})}function fd(){return new Oe({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Fc(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:_i,depthTest:!1,depthWrite:!1})}function Fc(){return`

		precision mediump float;
		precision mediump int;

		attribute vec3 outputDirection;

		varying vec3 vOutputDirection;

		void main() {

			vOutputDirection = outputDirection;
			gl_Position = vec4( position, 1.0 );

		}
	`}var Uc=class extends In{constructor(t=1,e={}){super(t,t,e),this.isWebGLCubeRenderTarget=!0;let n={width:t,height:t,depth:1},s=[n,n,n,n,n,n];this.texture=new Yr(s),this._setTextureOptions(e),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(t,e){this.texture.type=e.type,this.texture.colorSpace=e.colorSpace,this.texture.generateMipmaps=e.generateMipmaps,this.texture.minFilter=e.minFilter,this.texture.magFilter=e.magFilter;let n={uniforms:{tEquirect:{value:null}},vertexShader:`

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
			`},s=new Ce(5,5,5),r=new Oe({name:"CubemapFromEquirect",uniforms:ws(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:on,blending:_i});r.uniforms.tEquirect.value=e;let a=new ct(s,r),o=e.minFilter;return e.minFilter===cs&&(e.minFilter=Ke),new ko(1,10,this).update(t,a),e.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(t,e=!0,n=!0,s=!0){let r=t.getRenderTarget();for(let a=0;a<6;a++)t.setRenderTarget(this,a),t.clear(e,n,s);t.setRenderTarget(r)}};function Yg(i){let t=new WeakMap,e=new WeakMap,n=null;function s(h,f=!1){return h==null?null:f?a(h):r(h)}function r(h){if(h&&h.isTexture){let f=h.mapping;if(f===Go||f===Wo)if(t.has(h)){let g=t.get(h).texture;return o(g,h.mapping)}else{let g=h.image;if(g&&g.height>0){let x=new Uc(g.height);return x.fromEquirectangularTexture(i,h),t.set(h,x),h.addEventListener("dispose",l),o(x.texture,h.mapping)}else return null}}return h}function a(h){if(h&&h.isTexture){let f=h.mapping,g=f===Go||f===Wo,x=f===os||f===Es;if(g||x){let p=e.get(h),m=p!==void 0?p.texture.pmremVersion:0;if(h.isRenderTargetTexture&&h.pmremVersion!==m)return n===null&&(n=new vr(i)),p=g?n.fromEquirectangular(h,p):n.fromCubemap(h,p),p.texture.pmremVersion=h.pmremVersion,e.set(h,p),p.texture;if(p!==void 0)return p.texture;{let y=h.image;return g&&y&&y.height>0||x&&y&&c(y)?(n===null&&(n=new vr(i)),p=g?n.fromEquirectangular(h):n.fromCubemap(h),p.texture.pmremVersion=h.pmremVersion,e.set(h,p),h.addEventListener("dispose",u),p.texture):null}}}return h}function o(h,f){return f===Go?h.mapping=os:f===Wo&&(h.mapping=Es),h}function c(h){let f=0,g=6;for(let x=0;x<g;x++)h[x]!==void 0&&f++;return f===g}function l(h){let f=h.target;f.removeEventListener("dispose",l);let g=t.get(f);g!==void 0&&(t.delete(f),g.dispose())}function u(h){let f=h.target;f.removeEventListener("dispose",u);let g=e.get(f);g!==void 0&&(e.delete(f),g.dispose())}function d(){t=new WeakMap,e=new WeakMap,n!==null&&(n.dispose(),n=null)}return{get:s,dispose:d}}function jg(i){let t={};function e(n){if(t[n]!==void 0)return t[n];let s=i.getExtension(n);return t[n]=s,s}return{has:function(n){return e(n)!==null},init:function(){e("EXT_color_buffer_float"),e("WEBGL_clip_cull_distance"),e("OES_texture_float_linear"),e("EXT_color_buffer_half_float"),e("WEBGL_multisampled_render_to_texture"),e("WEBGL_render_shared_exponent")},get:function(n){let s=e(n);return s===null&&_s("WebGLRenderer: "+n+" extension not supported."),s}}}function Zg(i,t,e,n){let s={},r=new WeakMap;function a(d){let h=d.target;h.index!==null&&t.remove(h.index);for(let g in h.attributes)t.remove(h.attributes[g]);h.removeEventListener("dispose",a),delete s[h.id];let f=r.get(h);f&&(t.remove(f),r.delete(h)),n.releaseStatesOfGeometry(h),h.isInstancedBufferGeometry===!0&&delete h._maxInstanceCount,e.memory.geometries--}function o(d,h){return s[h.id]===!0||(h.addEventListener("dispose",a),s[h.id]=!0,e.memory.geometries++),h}function c(d){let h=d.attributes;for(let f in h)t.update(h[f],i.ARRAY_BUFFER)}function l(d){let h=[],f=d.index,g=d.attributes.position,x=0;if(g===void 0)return;if(f!==null){let y=f.array;x=f.version;for(let E=0,v=y.length;E<v;E+=3){let b=y[E+0],M=y[E+1],A=y[E+2];h.push(b,M,M,A,A,b)}}else{let y=g.array;x=g.version;for(let E=0,v=y.length/3-1;E<v;E+=3){let b=E+0,M=E+1,A=E+2;h.push(b,M,M,A,A,b)}}let p=new(g.count>=65535?Gr:Vr)(h,1);p.version=x;let m=r.get(d);m&&t.remove(m),r.set(d,p)}function u(d){let h=r.get(d);if(h){let f=d.index;f!==null&&h.version<f.version&&l(d)}else l(d);return r.get(d)}return{get:o,update:c,getWireframeAttribute:u}}function $g(i,t,e){let n;function s(d){n=d}let r,a;function o(d){r=d.type,a=d.bytesPerElement}function c(d,h){i.drawElements(n,h,r,d*a),e.update(h,n,1)}function l(d,h,f){f!==0&&(i.drawElementsInstanced(n,h,r,d*a,f),e.update(h,n,f))}function u(d,h,f){if(f===0)return;t.get("WEBGL_multi_draw").multiDrawElementsWEBGL(n,h,0,r,d,0,f);let x=0;for(let p=0;p<f;p++)x+=h[p];e.update(x,n,1)}this.setMode=s,this.setIndex=o,this.render=c,this.renderInstances=l,this.renderMultiDraw=u}function Jg(i){let t={geometries:0,textures:0},e={frame:0,calls:0,triangles:0,points:0,lines:0};function n(r,a,o){switch(e.calls++,a){case i.TRIANGLES:e.triangles+=o*(r/3);break;case i.LINES:e.lines+=o*(r/2);break;case i.LINE_STRIP:e.lines+=o*(r-1);break;case i.LINE_LOOP:e.lines+=o*r;break;case i.POINTS:e.points+=o*r;break;default:ae("WebGLInfo: Unknown draw mode:",a);break}}function s(){e.calls=0,e.triangles=0,e.points=0,e.lines=0}return{memory:t,render:e,programs:null,autoReset:!0,reset:s,update:n}}function Kg(i,t,e){let n=new WeakMap,s=new xe;function r(a,o,c){let l=a.morphTargetInfluences,u=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,d=u!==void 0?u.length:0,h=n.get(o);if(h===void 0||h.count!==d){let T=function(){A.dispose(),n.delete(o),o.removeEventListener("dispose",T)};h!==void 0&&h.texture.dispose();let f=o.morphAttributes.position!==void 0,g=o.morphAttributes.normal!==void 0,x=o.morphAttributes.color!==void 0,p=o.morphAttributes.position||[],m=o.morphAttributes.normal||[],y=o.morphAttributes.color||[],E=0;f===!0&&(E=1),g===!0&&(E=2),x===!0&&(E=3);let v=o.attributes.position.count*E,b=1;v>t.maxTextureSize&&(b=Math.ceil(v/t.maxTextureSize),v=t.maxTextureSize);let M=new Float32Array(v*b*4*d),A=new Br(M,v,b,d);A.type=qn,A.needsUpdate=!0;let _=E*4;for(let P=0;P<d;P++){let L=p[P],F=m[P],V=y[P],I=v*b*4*P;for(let z=0;z<L.count;z++){let q=z*_;f===!0&&(s.fromBufferAttribute(L,z),M[I+q+0]=s.x,M[I+q+1]=s.y,M[I+q+2]=s.z,M[I+q+3]=0),g===!0&&(s.fromBufferAttribute(F,z),M[I+q+4]=s.x,M[I+q+5]=s.y,M[I+q+6]=s.z,M[I+q+7]=0),x===!0&&(s.fromBufferAttribute(V,z),M[I+q+8]=s.x,M[I+q+9]=s.y,M[I+q+10]=s.z,M[I+q+11]=V.itemSize===4?s.w:1)}}h={count:d,texture:A,size:new vt(v,b)},n.set(o,h),o.addEventListener("dispose",T)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)c.getUniforms().setValue(i,"morphTexture",a.morphTexture,e);else{let f=0;for(let x=0;x<l.length;x++)f+=l[x];let g=o.morphTargetsRelative?1:1-f;c.getUniforms().setValue(i,"morphTargetBaseInfluence",g),c.getUniforms().setValue(i,"morphTargetInfluences",l)}c.getUniforms().setValue(i,"morphTargetsTexture",h.texture,e),c.getUniforms().setValue(i,"morphTargetsTextureSize",h.size)}return{update:r}}function Qg(i,t,e,n,s){let r=new WeakMap;function a(l){let u=s.render.frame,d=l.geometry,h=t.get(l,d);if(r.get(h)!==u&&(t.update(h),r.set(h,u)),l.isInstancedMesh&&(l.hasEventListener("dispose",c)===!1&&l.addEventListener("dispose",c),r.get(l)!==u&&(e.update(l.instanceMatrix,i.ARRAY_BUFFER),l.instanceColor!==null&&e.update(l.instanceColor,i.ARRAY_BUFFER),r.set(l,u))),l.isSkinnedMesh){let f=l.skeleton;r.get(f)!==u&&(f.update(),r.set(f,u))}return h}function o(){r=new WeakMap}function c(l){let u=l.target;u.removeEventListener("dispose",c),n.releaseStatesOfObject(u),e.remove(u.instanceMatrix),u.instanceColor!==null&&e.remove(u.instanceColor)}return{update:a,dispose:o}}var tv={[kl]:"LINEAR_TONE_MAPPING",[Hl]:"REINHARD_TONE_MAPPING",[Vl]:"CINEON_TONE_MAPPING",[Gl]:"ACES_FILMIC_TONE_MAPPING",[Xl]:"AGX_TONE_MAPPING",[pa]:"NEUTRAL_TONE_MAPPING",[Wl]:"CUSTOM_TONE_MAPPING"};function ev(i,t,e,n,s,r){let a=new In(t,e,{type:i,depthBuffer:s,stencilBuffer:r,samples:n?4:0,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,resolveDepthBuffer:!1,resolveStencilBuffer:!1}),o=null,c=null,l=new ge;l.setAttribute("position",new te([-1,3,0,-1,-1,0,3,-1,0],3)),l.setAttribute("uv",new te([0,2,0,0,2,0],2));let u=new Ao({uniforms:{tDiffuse:{value:null}},vertexShader:`
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
			}`,depthTest:!1,depthWrite:!1}),d=new ct(l,u),h=new lr(-1,1,1,-1,0,1),f=null,g=null,x=!1,p,m=null,y=[],E=!1;this.setSize=function(v,b){a.setSize(v,b),o!==null&&o.setSize(v,b),c!==null&&c.setSize(v,b);for(let M=0;M<y.length;M++){let A=y[M];A.setSize&&A.setSize(v,b)}},this.setEffects=function(v){y=v,E=y.length>0&&y[0].isRenderPass===!0;let b=a.width,M=a.height;y.length>0&&o===null&&(o=new In(b,M,{type:Bn,depthBuffer:!1,stencilBuffer:!1}),c=new In(b,M,{type:Bn,depthBuffer:!1,stencilBuffer:!1}));for(let A=0;A<y.length;A++){let _=y[A];_.setSize&&_.setSize(b,M)}},this.begin=function(v,b){if(x||v.toneMapping===On&&y.length===0)return!1;if(m=b,b!==null){let M=b.width,A=b.height;(a.width!==M||a.height!==A)&&this.setSize(M,A)}return E===!1&&v.setRenderTarget(a),p=v.toneMapping,v.toneMapping=On,!0},this.hasRenderPass=function(){return E},this.end=function(v,b){v.toneMapping=p,x=!0;let M=a,A=o;for(let _=0;_<y.length;_++){let T=y[_];T.enabled!==!1&&(T.render(v,A,M,b),T.needsSwap!==!1&&(M=A,A=A===o?c:o))}if(f!==v.outputColorSpace||g!==v.toneMapping){f=v.outputColorSpace,g=v.toneMapping,u.defines={},Me.getTransfer(f)===Ie&&(u.defines.SRGB_TRANSFER="");let _=tv[g];_&&(u.defines[_]=""),u.needsUpdate=!0}u.uniforms.tDiffuse.value=M.texture,v.setRenderTarget(m),v.render(d,h),m=null,x=!1},this.isCompositing=function(){return x},this.dispose=function(){a.dispose(),o!==null&&o.dispose(),c!==null&&c.dispose(),l.dispose(),u.dispose()}}var Dd=new En,xh=new Ji(1,1),Ud=new Br,Nd=new vo,Fd=new Yr,pd=[],md=[],gd=new Float32Array(16),vd=new Float32Array(9),xd=new Float32Array(4);function xr(i,t,e){let n=i[0];if(n<=0||n>0)return i;let s=t*e,r=pd[s];if(r===void 0&&(r=new Float32Array(s),pd[s]=r),t!==0){n.toArray(r,0);for(let a=1,o=0;a!==t;++a)o+=e,i[a].toArray(r,o)}return r}function Qe(i,t){if(i.length!==t.length)return!1;for(let e=0,n=i.length;e<n;e++)if(i[e]!==t[e])return!1;return!0}function tn(i,t){for(let e=0,n=t.length;e<n;e++)i[e]=t[e]}function zc(i,t){let e=md[t];e===void 0&&(e=new Int32Array(t),md[t]=e);for(let n=0;n!==t;++n)e[n]=i.allocateTextureUnit();return e}function nv(i,t){let e=this.cache;e[0]!==t&&(i.uniform1f(this.addr,t),e[0]=t)}function iv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y)&&(i.uniform2f(this.addr,t.x,t.y),e[0]=t.x,e[1]=t.y);else{if(Qe(e,t))return;i.uniform2fv(this.addr,t),tn(e,t)}}function sv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z)&&(i.uniform3f(this.addr,t.x,t.y,t.z),e[0]=t.x,e[1]=t.y,e[2]=t.z);else if(t.r!==void 0)(e[0]!==t.r||e[1]!==t.g||e[2]!==t.b)&&(i.uniform3f(this.addr,t.r,t.g,t.b),e[0]=t.r,e[1]=t.g,e[2]=t.b);else{if(Qe(e,t))return;i.uniform3fv(this.addr,t),tn(e,t)}}function rv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z||e[3]!==t.w)&&(i.uniform4f(this.addr,t.x,t.y,t.z,t.w),e[0]=t.x,e[1]=t.y,e[2]=t.z,e[3]=t.w);else{if(Qe(e,t))return;i.uniform4fv(this.addr,t),tn(e,t)}}function av(i,t){let e=this.cache,n=t.elements;if(n===void 0){if(Qe(e,t))return;i.uniformMatrix2fv(this.addr,!1,t),tn(e,t)}else{if(Qe(e,n))return;xd.set(n),i.uniformMatrix2fv(this.addr,!1,xd),tn(e,n)}}function ov(i,t){let e=this.cache,n=t.elements;if(n===void 0){if(Qe(e,t))return;i.uniformMatrix3fv(this.addr,!1,t),tn(e,t)}else{if(Qe(e,n))return;vd.set(n),i.uniformMatrix3fv(this.addr,!1,vd),tn(e,n)}}function cv(i,t){let e=this.cache,n=t.elements;if(n===void 0){if(Qe(e,t))return;i.uniformMatrix4fv(this.addr,!1,t),tn(e,t)}else{if(Qe(e,n))return;gd.set(n),i.uniformMatrix4fv(this.addr,!1,gd),tn(e,n)}}function lv(i,t){let e=this.cache;e[0]!==t&&(i.uniform1i(this.addr,t),e[0]=t)}function hv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y)&&(i.uniform2i(this.addr,t.x,t.y),e[0]=t.x,e[1]=t.y);else{if(Qe(e,t))return;i.uniform2iv(this.addr,t),tn(e,t)}}function uv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z)&&(i.uniform3i(this.addr,t.x,t.y,t.z),e[0]=t.x,e[1]=t.y,e[2]=t.z);else{if(Qe(e,t))return;i.uniform3iv(this.addr,t),tn(e,t)}}function dv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z||e[3]!==t.w)&&(i.uniform4i(this.addr,t.x,t.y,t.z,t.w),e[0]=t.x,e[1]=t.y,e[2]=t.z,e[3]=t.w);else{if(Qe(e,t))return;i.uniform4iv(this.addr,t),tn(e,t)}}function fv(i,t){let e=this.cache;e[0]!==t&&(i.uniform1ui(this.addr,t),e[0]=t)}function pv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y)&&(i.uniform2ui(this.addr,t.x,t.y),e[0]=t.x,e[1]=t.y);else{if(Qe(e,t))return;i.uniform2uiv(this.addr,t),tn(e,t)}}function mv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z)&&(i.uniform3ui(this.addr,t.x,t.y,t.z),e[0]=t.x,e[1]=t.y,e[2]=t.z);else{if(Qe(e,t))return;i.uniform3uiv(this.addr,t),tn(e,t)}}function gv(i,t){let e=this.cache;if(t.x!==void 0)(e[0]!==t.x||e[1]!==t.y||e[2]!==t.z||e[3]!==t.w)&&(i.uniform4ui(this.addr,t.x,t.y,t.z,t.w),e[0]=t.x,e[1]=t.y,e[2]=t.z,e[3]=t.w);else{if(Qe(e,t))return;i.uniform4uiv(this.addr,t),tn(e,t)}}function vv(i,t,e){let n=this.cache,s=e.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s);let r;this.type===i.SAMPLER_2D_SHADOW?(xh.compareFunction=e.isReversedDepthBuffer()?Ic:Pc,r=xh):r=Dd,e.setTexture2D(t||r,s)}function xv(i,t,e){let n=this.cache,s=e.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),e.setTexture3D(t||Nd,s)}function _v(i,t,e){let n=this.cache,s=e.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),e.setTextureCube(t||Fd,s)}function yv(i,t,e){let n=this.cache,s=e.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),e.setTexture2DArray(t||Ud,s)}function Mv(i){switch(i){case 5126:return nv;case 35664:return iv;case 35665:return sv;case 35666:return rv;case 35674:return av;case 35675:return ov;case 35676:return cv;case 5124:case 35670:return lv;case 35667:case 35671:return hv;case 35668:case 35672:return uv;case 35669:case 35673:return dv;case 5125:return fv;case 36294:return pv;case 36295:return mv;case 36296:return gv;case 35678:case 36198:case 36298:case 36306:case 35682:return vv;case 35679:case 36299:case 36307:return xv;case 35680:case 36300:case 36308:case 36293:return _v;case 36289:case 36303:case 36311:case 36292:return yv}}function Sv(i,t){i.uniform1fv(this.addr,t)}function bv(i,t){let e=xr(t,this.size,2);i.uniform2fv(this.addr,e)}function Ev(i,t){let e=xr(t,this.size,3);i.uniform3fv(this.addr,e)}function wv(i,t){let e=xr(t,this.size,4);i.uniform4fv(this.addr,e)}function Tv(i,t){let e=xr(t,this.size,4);i.uniformMatrix2fv(this.addr,!1,e)}function Av(i,t){let e=xr(t,this.size,9);i.uniformMatrix3fv(this.addr,!1,e)}function Rv(i,t){let e=xr(t,this.size,16);i.uniformMatrix4fv(this.addr,!1,e)}function Cv(i,t){i.uniform1iv(this.addr,t)}function Pv(i,t){i.uniform2iv(this.addr,t)}function Iv(i,t){i.uniform3iv(this.addr,t)}function Lv(i,t){i.uniform4iv(this.addr,t)}function Dv(i,t){i.uniform1uiv(this.addr,t)}function Uv(i,t){i.uniform2uiv(this.addr,t)}function Nv(i,t){i.uniform3uiv(this.addr,t)}function Fv(i,t){i.uniform4uiv(this.addr,t)}function zv(i,t,e){let n=this.cache,s=t.length,r=zc(e,s);Qe(n,r)||(i.uniform1iv(this.addr,r),tn(n,r));let a;this.type===i.SAMPLER_2D_SHADOW?a=xh:a=Dd;for(let o=0;o!==s;++o)e.setTexture2D(t[o]||a,r[o])}function Ov(i,t,e){let n=this.cache,s=t.length,r=zc(e,s);Qe(n,r)||(i.uniform1iv(this.addr,r),tn(n,r));for(let a=0;a!==s;++a)e.setTexture3D(t[a]||Nd,r[a])}function Bv(i,t,e){let n=this.cache,s=t.length,r=zc(e,s);Qe(n,r)||(i.uniform1iv(this.addr,r),tn(n,r));for(let a=0;a!==s;++a)e.setTextureCube(t[a]||Fd,r[a])}function kv(i,t,e){let n=this.cache,s=t.length,r=zc(e,s);Qe(n,r)||(i.uniform1iv(this.addr,r),tn(n,r));for(let a=0;a!==s;++a)e.setTexture2DArray(t[a]||Ud,r[a])}function Hv(i){switch(i){case 5126:return Sv;case 35664:return bv;case 35665:return Ev;case 35666:return wv;case 35674:return Tv;case 35675:return Av;case 35676:return Rv;case 5124:case 35670:return Cv;case 35667:case 35671:return Pv;case 35668:case 35672:return Iv;case 35669:case 35673:return Lv;case 5125:return Dv;case 36294:return Uv;case 36295:return Nv;case 36296:return Fv;case 35678:case 36198:case 36298:case 36306:case 35682:return zv;case 35679:case 36299:case 36307:return Ov;case 35680:case 36300:case 36308:case 36293:return Bv;case 36289:case 36303:case 36311:case 36292:return kv}}var _h=class{constructor(t,e,n){this.id=t,this.addr=n,this.cache=[],this.type=e.type,this.setValue=Mv(e.type)}},yh=class{constructor(t,e,n){this.id=t,this.addr=n,this.cache=[],this.type=e.type,this.size=e.size,this.setValue=Hv(e.type)}},Mh=class{constructor(t){this.id=t,this.seq=[],this.map={}}setValue(t,e,n){let s=this.seq;for(let r=0,a=s.length;r!==a;++r){let o=s[r];o.setValue(t,e[o.id],n)}}},gh=/(\w+)(\])?(\[|\.)?/g;function _d(i,t){i.seq.push(t),i.map[t.id]=t}function Vv(i,t,e){let n=i.name,s=n.length;for(gh.lastIndex=0;;){let r=gh.exec(n),a=gh.lastIndex,o=r[1],c=r[2]==="]",l=r[3];if(c&&(o=o|0),l===void 0||l==="["&&a+2===s){_d(e,l===void 0?new _h(o,i,t):new yh(o,i,t));break}else{let d=e.map[o];d===void 0&&(d=new Mh(o),_d(e,d)),e=d}}}var gr=class{constructor(t,e){this.seq=[],this.map={};let n=t.getProgramParameter(e,t.ACTIVE_UNIFORMS);for(let a=0;a<n;++a){let o=t.getActiveUniform(e,a),c=t.getUniformLocation(e,o.name);Vv(o,c,this)}let s=[],r=[];for(let a of this.seq)a.type===t.SAMPLER_2D_SHADOW||a.type===t.SAMPLER_CUBE_SHADOW||a.type===t.SAMPLER_2D_ARRAY_SHADOW?s.push(a):r.push(a);s.length>0&&(this.seq=s.concat(r))}setValue(t,e,n,s){let r=this.map[e];r!==void 0&&r.setValue(t,n,s)}setOptional(t,e,n){let s=e[n];s!==void 0&&this.setValue(t,n,s)}static upload(t,e,n,s){for(let r=0,a=e.length;r!==a;++r){let o=e[r],c=n[o.id];c.needsUpdate!==!1&&o.setValue(t,c.value,s)}}static seqWithValue(t,e){let n=[];for(let s=0,r=t.length;s!==r;++s){let a=t[s];a.id in e&&n.push(a)}return n}};function yd(i,t,e){let n=i.createShader(t);return i.shaderSource(n,e),i.compileShader(n),n}var Gv=37297,Wv=0;function Xv(i,t){let e=i.split(`
`),n=[],s=Math.max(t-6,0),r=Math.min(t+6,e.length);for(let a=s;a<r;a++){let o=a+1;n.push(`${o===t?">":" "} ${o}: ${e[a]}`)}return n.join(`
`)}var Md=new he;function qv(i){Me._getMatrix(Md,Me.workingColorSpace,i);let t=`mat3( ${Md.elements.map(e=>e.toFixed(4))} )`;switch(Me.getTransfer(i)){case Fr:return[t,"LinearTransferOETF"];case Ie:return[t,"sRGBTransferOETF"];default:return ie("WebGLProgram: Unsupported color space: ",i),[t,"LinearTransferOETF"]}}function Sd(i,t,e){let n=i.getShaderParameter(t,i.COMPILE_STATUS),r=(i.getShaderInfoLog(t)||"").trim();if(n&&r==="")return"";let a=/ERROR: 0:(\d+)/.exec(r);if(a){let o=parseInt(a[1]);return e.toUpperCase()+`

`+r+`

`+Xv(i.getShaderSource(t),o)}else return r}function Yv(i,t){let e=qv(t);return[`vec4 ${i}( vec4 value ) {`,`	return ${e[1]}( vec4( value.rgb * ${e[0]}, value.a ) );`,"}"].join(`
`)}var jv={[kl]:"Linear",[Hl]:"Reinhard",[Vl]:"Cineon",[Gl]:"ACESFilmic",[Xl]:"AgX",[pa]:"Neutral",[Wl]:"Custom"};function Zv(i,t){let e=jv[t];return e===void 0?(ie("WebGLProgram: Unsupported toneMapping:",t),"vec3 "+i+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+i+"( vec3 color ) { return "+e+"ToneMapping( color ); }"}var Dc=new C;function $v(){Me.getLuminanceCoefficients(Dc);let i=Dc.x.toFixed(4),t=Dc.y.toFixed(4),e=Dc.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${i}, ${t}, ${e} );`,"	return dot( weights, rgb );","}"].join(`
`)}function Jv(i){return[i.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",i.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Ta).join(`
`)}function Kv(i){let t=[];for(let e in i){let n=i[e];n!==!1&&t.push("#define "+e+" "+n)}return t.join(`
`)}function Qv(i,t){let e={},n=i.getProgramParameter(t,i.ACTIVE_ATTRIBUTES);for(let s=0;s<n;s++){let r=i.getActiveAttrib(t,s),a=r.name,o=1;r.type===i.FLOAT_MAT2&&(o=2),r.type===i.FLOAT_MAT3&&(o=3),r.type===i.FLOAT_MAT4&&(o=4),e[a]={type:r.type,location:i.getAttribLocation(t,a),locationSize:o}}return e}function Ta(i){return i!==""}function bd(i,t){let e=t.numSpotLightShadows+t.numSpotLightMaps-t.numSpotLightShadowsWithMaps;return i.replace(/NUM_SUN_LIGHTS/g,t.numSunLights).replace(/NUM_DIR_LIGHTS/g,t.numDirLights).replace(/NUM_SPOT_LIGHTS/g,t.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,t.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,e).replace(/NUM_RECT_AREA_LIGHTS/g,t.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,t.numPointLights).replace(/NUM_HEMI_LIGHTS/g,t.numHemiLights).replace(/NUM_SUN_LIGHT_SHADOWS/g,t.numSunLightShadows).replace(/NUM_DIR_LIGHT_SHADOWS/g,t.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,t.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,t.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,t.numPointLightShadows)}function Ed(i,t){return i.replace(/NUM_CLIPPING_PLANES/g,t.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,t.numClippingPlanes-t.numClipIntersection)}var tx=/^[ \t]*#include +<([\w\d./]+)>/gm;function Sh(i){return i.replace(tx,nx)}var ex=new Map;function nx(i,t){let e=me[t];if(e===void 0){let n=ex.get(t);if(n!==void 0)e=me[n],ie('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',t,n);else throw new Error("THREE.WebGLProgram: Can not resolve #include <"+t+">")}return Sh(e)}var ix=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function wd(i){return i.replace(ix,sx)}function sx(i,t,e,n){let s="";for(let r=parseInt(t);r<parseInt(e);r++)s+=n.replace(/\[\s*i\s*\]/g,"[ "+r+" ]").replace(/UNROLLED_LOOP_INDEX/g,r);return s}function Td(i){let t=`precision ${i.precision} float;
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
#define LOW_PRECISION`),t}var rx={[Ss]:"SHADOWMAP_TYPE_PCF",[hr]:"SHADOWMAP_TYPE_VSM"};function ax(i){return rx[i.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}var ox={[os]:"ENVMAP_TYPE_CUBE",[Es]:"ENVMAP_TYPE_CUBE",[ma]:"ENVMAP_TYPE_CUBE_UV"};function cx(i){return i.envMap===!1?"ENVMAP_TYPE_CUBE":ox[i.envMapMode]||"ENVMAP_TYPE_CUBE"}var lx={[Es]:"ENVMAP_MODE_REFRACTION"};function hx(i){return i.envMap===!1?"ENVMAP_MODE_REFLECTION":lx[i.envMapMode]||"ENVMAP_MODE_REFLECTION"}var ux={[Bl]:"ENVMAP_BLENDING_MULTIPLY",[Hu]:"ENVMAP_BLENDING_MIX",[Vu]:"ENVMAP_BLENDING_ADD"};function dx(i){return i.envMap===!1?"ENVMAP_BLENDING_NONE":ux[i.combine]||"ENVMAP_BLENDING_NONE"}function fx(i){let t=i.envMapCubeUVHeight;if(t===null)return null;let e=Math.log2(t)-2,n=1/t;return{texelWidth:1/(3*Math.max(Math.pow(2,e),112)),texelHeight:n,maxMip:e}}function px(i,t,e,n){let s=i.getContext(),r=e.defines,a=e.vertexShader,o=e.fragmentShader,c=ax(e),l=cx(e),u=hx(e),d=dx(e),h=fx(e),f=Jv(e),g=Kv(r),x=s.createProgram(),p,m,y=e.glslVersion?"#version "+e.glslVersion+`
`:"";e.isRawShaderMaterial?(p=["#define SHADER_TYPE "+e.shaderType,"#define SHADER_NAME "+e.shaderName,g].filter(Ta).join(`
`),p.length>0&&(p+=`
`),m=["#define SHADER_TYPE "+e.shaderType,"#define SHADER_NAME "+e.shaderName,g].filter(Ta).join(`
`),m.length>0&&(m+=`
`)):(p=[Td(e),"#define SHADER_TYPE "+e.shaderType,"#define SHADER_NAME "+e.shaderName,g,e.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",e.batching?"#define USE_BATCHING":"",e.batchingColor?"#define USE_BATCHING_COLOR":"",e.instancing?"#define USE_INSTANCING":"",e.instancingColor?"#define USE_INSTANCING_COLOR":"",e.instancingMorph?"#define USE_INSTANCING_MORPH":"",e.useFog&&e.fog?"#define USE_FOG":"",e.useFog&&e.fogExp2?"#define FOG_EXP2":"",e.map?"#define USE_MAP":"",e.envMap?"#define USE_ENVMAP":"",e.envMap?"#define "+u:"",e.lightMap?"#define USE_LIGHTMAP":"",e.aoMap?"#define USE_AOMAP":"",e.bumpMap?"#define USE_BUMPMAP":"",e.normalMap?"#define USE_NORMALMAP":"",e.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",e.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",e.displacementMap?"#define USE_DISPLACEMENTMAP":"",e.emissiveMap?"#define USE_EMISSIVEMAP":"",e.anisotropy?"#define USE_ANISOTROPY":"",e.anisotropyMap?"#define USE_ANISOTROPYMAP":"",e.clearcoatMap?"#define USE_CLEARCOATMAP":"",e.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",e.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",e.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",e.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",e.specularMap?"#define USE_SPECULARMAP":"",e.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",e.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",e.roughnessMap?"#define USE_ROUGHNESSMAP":"",e.metalnessMap?"#define USE_METALNESSMAP":"",e.alphaMap?"#define USE_ALPHAMAP":"",e.alphaHash?"#define USE_ALPHAHASH":"",e.transmission?"#define USE_TRANSMISSION":"",e.transmissionMap?"#define USE_TRANSMISSIONMAP":"",e.thicknessMap?"#define USE_THICKNESSMAP":"",e.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",e.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",e.mapUv?"#define MAP_UV "+e.mapUv:"",e.alphaMapUv?"#define ALPHAMAP_UV "+e.alphaMapUv:"",e.lightMapUv?"#define LIGHTMAP_UV "+e.lightMapUv:"",e.aoMapUv?"#define AOMAP_UV "+e.aoMapUv:"",e.emissiveMapUv?"#define EMISSIVEMAP_UV "+e.emissiveMapUv:"",e.bumpMapUv?"#define BUMPMAP_UV "+e.bumpMapUv:"",e.normalMapUv?"#define NORMALMAP_UV "+e.normalMapUv:"",e.displacementMapUv?"#define DISPLACEMENTMAP_UV "+e.displacementMapUv:"",e.metalnessMapUv?"#define METALNESSMAP_UV "+e.metalnessMapUv:"",e.roughnessMapUv?"#define ROUGHNESSMAP_UV "+e.roughnessMapUv:"",e.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+e.anisotropyMapUv:"",e.clearcoatMapUv?"#define CLEARCOATMAP_UV "+e.clearcoatMapUv:"",e.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+e.clearcoatNormalMapUv:"",e.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+e.clearcoatRoughnessMapUv:"",e.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+e.iridescenceMapUv:"",e.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+e.iridescenceThicknessMapUv:"",e.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+e.sheenColorMapUv:"",e.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+e.sheenRoughnessMapUv:"",e.specularMapUv?"#define SPECULARMAP_UV "+e.specularMapUv:"",e.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+e.specularColorMapUv:"",e.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+e.specularIntensityMapUv:"",e.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+e.transmissionMapUv:"",e.thicknessMapUv?"#define THICKNESSMAP_UV "+e.thicknessMapUv:"",e.vertexTangents&&e.flatShading===!1?"#define USE_TANGENT":"",e.vertexNormals?"#define HAS_NORMAL":"",e.vertexColors?"#define USE_COLOR":"",e.vertexAlphas?"#define USE_COLOR_ALPHA":"",e.vertexUv1s?"#define USE_UV1":"",e.vertexUv2s?"#define USE_UV2":"",e.vertexUv3s?"#define USE_UV3":"",e.pointsUvs?"#define USE_POINTS_UV":"",e.flatShading?"#define FLAT_SHADED":"",e.skinning?"#define USE_SKINNING":"",e.morphTargets?"#define USE_MORPHTARGETS":"",e.morphNormals&&e.flatShading===!1?"#define USE_MORPHNORMALS":"",e.morphColors?"#define USE_MORPHCOLORS":"",e.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+e.morphTextureStride:"",e.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+e.morphTargetsCount:"",e.doubleSided?"#define DOUBLE_SIDED":"",e.flipSided?"#define FLIP_SIDED":"",e.shadowMapEnabled?"#define USE_SHADOWMAP":"",e.shadowMapEnabled?"#define "+c:"",e.sizeAttenuation?"#define USE_SIZEATTENUATION":"",e.numLightProbes>0?"#define USE_LIGHT_PROBES":"",e.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",e.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Ta).join(`
`),m=[Td(e),"#define SHADER_TYPE "+e.shaderType,"#define SHADER_NAME "+e.shaderName,g,e.useFog&&e.fog?"#define USE_FOG":"",e.useFog&&e.fogExp2?"#define FOG_EXP2":"",e.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",e.map?"#define USE_MAP":"",e.matcap?"#define USE_MATCAP":"",e.envMap?"#define USE_ENVMAP":"",e.envMap?"#define "+l:"",e.envMap?"#define "+u:"",e.envMap?"#define "+d:"",h?"#define CUBEUV_TEXEL_WIDTH "+h.texelWidth:"",h?"#define CUBEUV_TEXEL_HEIGHT "+h.texelHeight:"",h?"#define CUBEUV_MAX_MIP "+h.maxMip+".0":"",e.lightMap?"#define USE_LIGHTMAP":"",e.aoMap?"#define USE_AOMAP":"",e.bumpMap?"#define USE_BUMPMAP":"",e.normalMap?"#define USE_NORMALMAP":"",e.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",e.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",e.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",e.emissiveMap?"#define USE_EMISSIVEMAP":"",e.anisotropy?"#define USE_ANISOTROPY":"",e.anisotropyMap?"#define USE_ANISOTROPYMAP":"",e.clearcoat?"#define USE_CLEARCOAT":"",e.clearcoatMap?"#define USE_CLEARCOATMAP":"",e.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",e.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",e.dispersion?"#define USE_DISPERSION":"",e.retroreflection?"#define USE_RETROREFLECTION":"",e.iridescence?"#define USE_IRIDESCENCE":"",e.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",e.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",e.specularMap?"#define USE_SPECULARMAP":"",e.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",e.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",e.roughnessMap?"#define USE_ROUGHNESSMAP":"",e.metalnessMap?"#define USE_METALNESSMAP":"",e.alphaMap?"#define USE_ALPHAMAP":"",e.alphaTest?"#define USE_ALPHATEST":"",e.alphaHash?"#define USE_ALPHAHASH":"",e.sheen?"#define USE_SHEEN":"",e.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",e.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",e.transmission?"#define USE_TRANSMISSION":"",e.transmissionMap?"#define USE_TRANSMISSIONMAP":"",e.thicknessMap?"#define USE_THICKNESSMAP":"",e.vertexTangents&&e.flatShading===!1?"#define USE_TANGENT":"",e.vertexColors||e.instancingColor?"#define USE_COLOR":"",e.vertexAlphas||e.batchingColor?"#define USE_COLOR_ALPHA":"",e.vertexUv1s?"#define USE_UV1":"",e.vertexUv2s?"#define USE_UV2":"",e.vertexUv3s?"#define USE_UV3":"",e.pointsUvs?"#define USE_POINTS_UV":"",e.gradientMap?"#define USE_GRADIENTMAP":"",e.flatShading?"#define FLAT_SHADED":"",e.doubleSided?"#define DOUBLE_SIDED":"",e.flipSided?"#define FLIP_SIDED":"",e.shadowMapEnabled?"#define USE_SHADOWMAP":"",e.shadowMapEnabled?"#define "+c:"",e.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",e.numLightProbes>0?"#define USE_LIGHT_PROBES":"",e.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",e.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",e.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",e.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",e.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",e.toneMapping!==On?"#define TONE_MAPPING":"",e.toneMapping!==On?me.tonemapping_pars_fragment:"",e.toneMapping!==On?Zv("toneMapping",e.toneMapping):"",e.dithering?"#define DITHERING":"",e.opaque?"#define OPAQUE":"",me.colorspace_pars_fragment,Yv("linearToOutputTexel",e.outputColorSpace),$v(),e.useDepthPacking?"#define DEPTH_PACKING "+e.depthPacking:"",`
`].filter(Ta).join(`
`)),a=Sh(a),a=bd(a,e),a=Ed(a,e),o=Sh(o),o=bd(o,e),o=Ed(o,e),a=wd(a),o=wd(o),e.isRawShaderMaterial!==!0&&(y=`#version 300 es
`,p=[f,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+p,m=["#define varying in",e.glslVersion===th?"":"layout(location = 0) out highp vec4 pc_fragColor;",e.glslVersion===th?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+m);let E=y+p+a,v=y+m+o,b=yd(s,s.VERTEX_SHADER,E),M=yd(s,s.FRAGMENT_SHADER,v);s.attachShader(x,b),s.attachShader(x,M),e.index0AttributeName!==void 0?s.bindAttribLocation(x,0,e.index0AttributeName):e.hasPositionAttribute===!0&&s.bindAttribLocation(x,0,"position"),s.linkProgram(x);function A(L){if(i.debug.checkShaderErrors){let F=s.getProgramInfoLog(x)||"",V=s.getShaderInfoLog(b)||"",I=s.getShaderInfoLog(M)||"",z=F.trim(),q=V.trim(),j=I.trim(),at=!0,K=!0;if(s.getProgramParameter(x,s.LINK_STATUS)===!1)if(at=!1,typeof i.debug.onShaderError=="function")i.debug.onShaderError(s,x,b,M);else{let st=Sd(s,b,"vertex"),it=Sd(s,M,"fragment");ae("WebGLProgram: Shader Error "+s.getError()+" - VALIDATE_STATUS "+s.getProgramParameter(x,s.VALIDATE_STATUS)+`

Material Name: `+L.name+`
Material Type: `+L.type+`

Program Info Log: `+z+`
`+st+`
`+it)}else z!==""?ie("WebGLProgram: Program Info Log:",z):(q===""||j==="")&&(K=!1);K&&(L.diagnostics={runnable:at,programLog:z,vertexShader:{log:q,prefix:p},fragmentShader:{log:j,prefix:m}})}s.deleteShader(b),s.deleteShader(M),_=new gr(s,x),T=Qv(s,x)}let _;this.getUniforms=function(){return _===void 0&&A(this),_};let T;this.getAttributes=function(){return T===void 0&&A(this),T};let P=e.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return P===!1&&(P=s.getProgramParameter(x,Gv)),P},this.destroy=function(){n.releaseStatesOfProgram(this),s.deleteProgram(x),this.program=void 0},this.type=e.shaderType,this.name=e.shaderName,this.id=Wv++,this.cacheKey=t,this.usedTimes=1,this.program=x,this.vertexShader=b,this.fragmentShader=M,this}var mx=0,bh=class{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(t,e,n){let s=this._getShaderCacheForMaterial(t);return s.has(e)===!1&&(s.add(e),e.usedTimes++),s.has(n)===!1&&(s.add(n),n.usedTimes++),this}remove(t){let e=this.materialCache.get(t);for(let n of e)n.usedTimes--,n.usedTimes===0&&this.shaderCache.delete(n.code);return this.materialCache.delete(t),this}getVertexShaderStage(t){return this._getShaderStage(t.vertexShader)}getFragmentShaderStage(t){return this._getShaderStage(t.fragmentShader)}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(t){let e=this.materialCache,n=e.get(t);return n===void 0&&(n=new Set,e.set(t,n)),n}_getShaderStage(t){let e=this.shaderCache,n=e.get(t);return n===void 0&&(n=new Eh(t),e.set(t,n)),n}},Eh=class{constructor(t){this.id=mx++,this.code=t,this.usedTimes=0}};function gx(i){return i===yi||i===Ma||i===Sa}function vx(i,t,e,n,s,r){let a=new kr,o=new bh,c=new Set,l=[],u=new Map,d=n.logarithmicDepthBuffer,h=n.precision,f={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function g(_){return c.add(_),_===0?"uv":`uv${_}`}function x(_,T,P,L,F,V){let I=L.fog,z=F.geometry,q=_.isMeshStandardMaterial||_.isMeshLambertMaterial||_.isMeshPhongMaterial?L.environment:null,j=_.isMeshStandardMaterial||_.isMeshLambertMaterial&&!_.envMap||_.isMeshPhongMaterial&&!_.envMap,at=t.get(_.envMap||q,j),K=at&&at.mapping===ma?at.image.height:null,st=f[_.type];_.precision!==null&&(h=n.getMaxPrecision(_.precision),h!==_.precision&&ie("WebGLProgram.getParameters:",_.precision,"not supported, using",h,"instead."));let it=z.morphAttributes.position||z.morphAttributes.normal||z.morphAttributes.color,Rt=it!==void 0?it.length:0,mt=0;z.morphAttributes.position!==void 0&&(mt=1),z.morphAttributes.normal!==void 0&&(mt=2),z.morphAttributes.color!==void 0&&(mt=3);let Ut,Dt,ft,N;if(st){let we=An[st];Ut=we.vertexShader,Dt=we.fragmentShader}else{Ut=_.vertexShader,Dt=_.fragmentShader;let we=o.getVertexShaderStage(_),ye=o.getFragmentShaderStage(_);o.update(_,we,ye),ft=we.id,N=ye.id}let k=i.getRenderTarget(),dt=i.state.buffers.depth.getReversed(),St=F.isInstancedMesh===!0,Mt=F.isBatchedMesh===!0,Ft=!!_.map,xt=!!_.matcap,X=!!at,tt=!!_.aoMap,G=!!_.lightMap,et=!!_.bumpMap&&_.wireframe===!1,gt=!!_.normalMap,Bt=!!_.displacementMap,bt=!!_.emissiveMap,jt=!!_.metalnessMap,ne=!!_.roughnessMap,U=_.anisotropy>0,Ee=_.clearcoat>0,se=_.dispersion>0,R=_.retroreflectivity>0,S=_.iridescence>0,H=_.sheen>0,Y=_.transmission>0,rt=U&&!!_.anisotropyMap,_t=Ee&&!!_.clearcoatMap,Et=Ee&&!!_.clearcoatNormalMap,nt=Ee&&!!_.clearcoatRoughnessMap,ut=S&&!!_.iridescenceMap,At=S&&!!_.iridescenceThicknessMap,Zt=H&&!!_.sheenColorMap,It=H&&!!_.sheenRoughnessMap,Lt=!!_.specularMap,$t=!!_.specularColorMap,ee=!!_.specularIntensityMap,ce=Y&&!!_.transmissionMap,B=Y&&!!_.thicknessMap,Ct=!!_.gradientMap,lt=!!_.alphaMap,Pt=_.alphaTest>0,yt=!!_.alphaHash,pt=!!_.extensions,Xt=On;_.toneMapped&&(k===null||k.isXRRenderTarget===!0)&&(Xt=i.toneMapping);let Ht={shaderID:st,shaderType:_.type,shaderName:_.name,vertexShader:Ut,fragmentShader:Dt,defines:_.defines,customVertexShaderID:ft,customFragmentShaderID:N,isRawShaderMaterial:_.isRawShaderMaterial===!0,glslVersion:_.glslVersion,precision:h,batching:Mt,batchingColor:Mt&&F._colorsTexture!==null,instancing:St,instancingColor:St&&F.instanceColor!==null,instancingMorph:St&&F.morphTexture!==null,outputColorSpace:k===null?i.outputColorSpace:k.isXRRenderTarget===!0?k.texture.colorSpace:Me.workingColorSpace,alphaToCoverage:!!_.alphaToCoverage,map:Ft,matcap:xt,envMap:X,envMapMode:X&&at.mapping,envMapCubeUVHeight:K,aoMap:tt,lightMap:G,bumpMap:et,normalMap:gt,displacementMap:Bt,emissiveMap:bt,normalMapObjectSpace:gt&&_.normalMapType===Xu,normalMapTangentSpace:gt&&_.normalMapType===Cc,packedNormalMap:gt&&_.normalMapType===Cc&&gx(_.normalMap.format),metalnessMap:jt,roughnessMap:ne,anisotropy:U,anisotropyMap:rt,clearcoat:Ee,clearcoatMap:_t,clearcoatNormalMap:Et,clearcoatRoughnessMap:nt,dispersion:se,retroreflection:R,iridescence:S,iridescenceMap:ut,iridescenceThicknessMap:At,sheen:H,sheenColorMap:Zt,sheenRoughnessMap:It,specularMap:Lt,specularColorMap:$t,specularIntensityMap:ee,transmission:Y,transmissionMap:ce,thicknessMap:B,gradientMap:Ct,opaque:_.transparent===!1&&_.blending===ur&&_.alphaToCoverage===!1,alphaMap:lt,alphaTest:Pt,alphaHash:yt,combine:_.combine,mapUv:Ft&&g(_.map.channel),aoMapUv:tt&&g(_.aoMap.channel),lightMapUv:G&&g(_.lightMap.channel),bumpMapUv:et&&g(_.bumpMap.channel),normalMapUv:gt&&g(_.normalMap.channel),displacementMapUv:Bt&&g(_.displacementMap.channel),emissiveMapUv:bt&&g(_.emissiveMap.channel),metalnessMapUv:jt&&g(_.metalnessMap.channel),roughnessMapUv:ne&&g(_.roughnessMap.channel),anisotropyMapUv:rt&&g(_.anisotropyMap.channel),clearcoatMapUv:_t&&g(_.clearcoatMap.channel),clearcoatNormalMapUv:Et&&g(_.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:nt&&g(_.clearcoatRoughnessMap.channel),iridescenceMapUv:ut&&g(_.iridescenceMap.channel),iridescenceThicknessMapUv:At&&g(_.iridescenceThicknessMap.channel),sheenColorMapUv:Zt&&g(_.sheenColorMap.channel),sheenRoughnessMapUv:It&&g(_.sheenRoughnessMap.channel),specularMapUv:Lt&&g(_.specularMap.channel),specularColorMapUv:$t&&g(_.specularColorMap.channel),specularIntensityMapUv:ee&&g(_.specularIntensityMap.channel),transmissionMapUv:ce&&g(_.transmissionMap.channel),thicknessMapUv:B&&g(_.thicknessMap.channel),alphaMapUv:lt&&g(_.alphaMap.channel),vertexTangents:!!z.attributes.tangent&&(gt||U),vertexNormals:!!z.attributes.normal,vertexColors:_.vertexColors,vertexAlphas:_.vertexColors===!0&&!!z.attributes.color&&z.attributes.color.itemSize===4,pointsUvs:F.isPoints===!0&&!!z.attributes.uv&&(Ft||lt),fog:!!I,useFog:_.fog===!0,fogExp2:!!I&&I.isFogExp2,flatShading:_.wireframe===!1&&(_.flatShading===!0||z.attributes.normal===void 0&&gt===!1&&(_.isMeshLambertMaterial||_.isMeshPhongMaterial||_.isMeshStandardMaterial||_.isMeshPhysicalMaterial)),sizeAttenuation:_.sizeAttenuation===!0,logarithmicDepthBuffer:d,reversedDepthBuffer:dt,skinning:F.isSkinnedMesh===!0,hasPositionAttribute:z.attributes.position!==void 0,morphTargets:z.morphAttributes.position!==void 0,morphNormals:z.morphAttributes.normal!==void 0,morphColors:z.morphAttributes.color!==void 0,morphTargetsCount:Rt,morphTextureStride:mt,numSunLights:T.sun.length,numDirLights:T.directional.length,numPointLights:T.point.length,numSpotLights:T.spot.length,numSpotLightMaps:T.spotLightMap.length,numRectAreaLights:T.rectArea.length,numHemiLights:T.hemi.length,numSunLightShadows:T.sunShadowMap.length,numDirLightShadows:T.directionalShadowMap.length,numPointLightShadows:T.pointShadowMap.length,numSpotLightShadows:T.spotShadowMap.length,numSpotLightShadowsWithMaps:T.numSpotLightShadowsWithMaps,numLightProbes:T.numLightProbes,numLightProbeGrids:V.length,numClippingPlanes:r.numPlanes,numClipIntersection:r.numIntersection,dithering:_.dithering,shadowMapEnabled:i.shadowMap.enabled&&P.length>0,shadowMapType:i.shadowMap.type,toneMapping:Xt,decodeVideoTexture:Ft&&_.map.isVideoTexture===!0&&Me.getTransfer(_.map.colorSpace)===Ie,decodeVideoTextureEmissive:bt&&_.emissiveMap.isVideoTexture===!0&&Me.getTransfer(_.emissiveMap.colorSpace)===Ie,premultipliedAlpha:_.premultipliedAlpha,doubleSided:_.side===vn,flipSided:_.side===on,useDepthPacking:_.depthPacking>=0,depthPacking:_.depthPacking||0,index0AttributeName:_.index0AttributeName,extensionClipCullDistance:pt&&_.extensions.clipCullDistance===!0&&e.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(pt&&_.extensions.multiDraw===!0||Mt)&&e.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:e.has("KHR_parallel_shader_compile"),customProgramCacheKey:_.customProgramCacheKey()};return Ht.vertexUv1s=c.has(1),Ht.vertexUv2s=c.has(2),Ht.vertexUv3s=c.has(3),c.clear(),Ht}function p(_){let T=[];if(_.shaderID?T.push(_.shaderID):(T.push(_.customVertexShaderID),T.push(_.customFragmentShaderID)),_.defines!==void 0)for(let P in _.defines)T.push(P),T.push(_.defines[P]);return _.isRawShaderMaterial===!1&&(m(T,_),y(T,_),T.push(i.outputColorSpace)),T.push(_.customProgramCacheKey),T.join()}function m(_,T){_.push(T.precision),_.push(T.outputColorSpace),_.push(T.envMapMode),_.push(T.envMapCubeUVHeight),_.push(T.mapUv),_.push(T.alphaMapUv),_.push(T.lightMapUv),_.push(T.aoMapUv),_.push(T.bumpMapUv),_.push(T.normalMapUv),_.push(T.displacementMapUv),_.push(T.emissiveMapUv),_.push(T.metalnessMapUv),_.push(T.roughnessMapUv),_.push(T.anisotropyMapUv),_.push(T.clearcoatMapUv),_.push(T.clearcoatNormalMapUv),_.push(T.clearcoatRoughnessMapUv),_.push(T.iridescenceMapUv),_.push(T.iridescenceThicknessMapUv),_.push(T.sheenColorMapUv),_.push(T.sheenRoughnessMapUv),_.push(T.specularMapUv),_.push(T.specularColorMapUv),_.push(T.specularIntensityMapUv),_.push(T.transmissionMapUv),_.push(T.thicknessMapUv),_.push(T.combine),_.push(T.fogExp2),_.push(T.sizeAttenuation),_.push(T.morphTargetsCount),_.push(T.morphAttributeCount),_.push(T.numSunLights),_.push(T.numDirLights),_.push(T.numPointLights),_.push(T.numSpotLights),_.push(T.numSpotLightMaps),_.push(T.numHemiLights),_.push(T.numRectAreaLights),_.push(T.numSunLightShadows),_.push(T.numDirLightShadows),_.push(T.numPointLightShadows),_.push(T.numSpotLightShadows),_.push(T.numSpotLightShadowsWithMaps),_.push(T.numLightProbes),_.push(T.shadowMapType),_.push(T.toneMapping),_.push(T.numClippingPlanes),_.push(T.numClipIntersection),_.push(T.depthPacking)}function y(_,T){a.disableAll(),T.instancing&&a.enable(0),T.instancingColor&&a.enable(1),T.instancingMorph&&a.enable(2),T.matcap&&a.enable(3),T.envMap&&a.enable(4),T.normalMapObjectSpace&&a.enable(5),T.normalMapTangentSpace&&a.enable(6),T.clearcoat&&a.enable(7),T.iridescence&&a.enable(8),T.alphaTest&&a.enable(9),T.vertexColors&&a.enable(10),T.vertexAlphas&&a.enable(11),T.vertexUv1s&&a.enable(12),T.vertexUv2s&&a.enable(13),T.vertexUv3s&&a.enable(14),T.vertexTangents&&a.enable(15),T.anisotropy&&a.enable(16),T.alphaHash&&a.enable(17),T.batching&&a.enable(18),T.dispersion&&a.enable(19),T.retroreflection&&a.enable(24),T.batchingColor&&a.enable(20),T.gradientMap&&a.enable(21),T.packedNormalMap&&a.enable(22),T.vertexNormals&&a.enable(23),_.push(a.mask),a.disableAll(),T.fog&&a.enable(0),T.useFog&&a.enable(1),T.flatShading&&a.enable(2),T.logarithmicDepthBuffer&&a.enable(3),T.reversedDepthBuffer&&a.enable(4),T.skinning&&a.enable(5),T.morphTargets&&a.enable(6),T.morphNormals&&a.enable(7),T.morphColors&&a.enable(8),T.premultipliedAlpha&&a.enable(9),T.shadowMapEnabled&&a.enable(10),T.doubleSided&&a.enable(11),T.flipSided&&a.enable(12),T.useDepthPacking&&a.enable(13),T.dithering&&a.enable(14),T.transmission&&a.enable(15),T.sheen&&a.enable(16),T.opaque&&a.enable(17),T.pointsUvs&&a.enable(18),T.decodeVideoTexture&&a.enable(19),T.decodeVideoTextureEmissive&&a.enable(20),T.alphaToCoverage&&a.enable(21),T.numLightProbeGrids>0&&a.enable(22),T.hasPositionAttribute&&a.enable(23),_.push(a.mask)}function E(_){let T=f[_.type],P;if(T){let L=An[T];P=ba.clone(L.uniforms)}else P=_.uniforms;return P}function v(_,T){let P=u.get(T);return P!==void 0?++P.usedTimes:(P=new px(i,T,_,s),l.push(P),u.set(T,P)),P}function b(_){if(--_.usedTimes===0){let T=l.indexOf(_);l[T]=l[l.length-1],l.pop(),u.delete(_.cacheKey),_.destroy()}}function M(_){o.remove(_)}function A(){o.dispose()}return{getParameters:x,getProgramCacheKey:p,getUniforms:E,acquireProgram:v,releaseProgram:b,releaseShaderCache:M,programs:l,dispose:A}}function xx(){let i=new WeakMap;function t(a){return i.has(a)}function e(a){let o=i.get(a);return o===void 0&&(o={},i.set(a,o)),o}function n(a){i.delete(a)}function s(a,o,c){i.get(a)[o]=c}function r(){i=new WeakMap}return{has:t,get:e,remove:n,update:s,dispose:r}}function _x(i,t){return i.groupOrder!==t.groupOrder?i.groupOrder-t.groupOrder:i.renderOrder!==t.renderOrder?i.renderOrder-t.renderOrder:i.material.id!==t.material.id?i.material.id-t.material.id:i.materialVariant!==t.materialVariant?i.materialVariant-t.materialVariant:i.z!==t.z?i.z-t.z:i.id-t.id}function Ad(i,t){return i.groupOrder!==t.groupOrder?i.groupOrder-t.groupOrder:i.renderOrder!==t.renderOrder?i.renderOrder-t.renderOrder:i.z!==t.z?t.z-i.z:i.id-t.id}function Rd(){let i=[],t=0,e=[],n=[],s=[];function r(){t=0,e.length=0,n.length=0,s.length=0}function a(h){let f=0;return h.isInstancedMesh&&(f+=2),h.isSkinnedMesh&&(f+=1),f}function o(h,f,g,x,p,m){let y=i[t];return y===void 0?(y={id:h.id,object:h,geometry:f,material:g,materialVariant:a(h),groupOrder:x,renderOrder:h.renderOrder,z:p,group:m},i[t]=y):(y.id=h.id,y.object=h,y.geometry=f,y.material=g,y.materialVariant=a(h),y.groupOrder=x,y.renderOrder=h.renderOrder,y.z=p,y.group=m),t++,y}function c(h,f,g,x,p,m,y){y.reversedDepth===!0&&(p=-p);let E=o(h,f,g,x,p,m);g.transmission>0?n.push(E):g.transparent===!0?s.push(E):e.push(E)}function l(h,f,g,x,p,m){let y=o(h,f,g,x,p,m);g.transmission>0?n.unshift(y):g.transparent===!0?s.unshift(y):e.unshift(y)}function u(h,f){e.length>1&&e.sort(h||_x),n.length>1&&n.sort(f||Ad),s.length>1&&s.sort(f||Ad)}function d(){for(let h=t,f=i.length;h<f;h++){let g=i[h];if(g.id===null)break;g.id=null,g.object=null,g.geometry=null,g.material=null,g.group=null}}return{opaque:e,transmissive:n,transparent:s,init:r,push:c,unshift:l,finish:d,sort:u}}function yx(){let i=new WeakMap;function t(n,s){let r=i.get(n),a;return r===void 0?(a=new Rd,i.set(n,[a])):s>=r.length?(a=new Rd,r.push(a)):a=r[s],a}function e(){i=new WeakMap}return{get:t,dispose:e}}function Mx(){let i={};return{get:function(t){if(i[t.id]!==void 0)return i[t.id];let e;switch(t.type){case"SunLight":case"DirectionalLight":e={direction:new C,color:new Wt};break;case"SpotLight":e={position:new C,direction:new C,color:new Wt,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":e={position:new C,color:new Wt,distance:0,decay:0};break;case"HemisphereLight":e={direction:new C,skyColor:new Wt,groundColor:new Wt};break;case"RectAreaLight":e={color:new Wt,position:new C,halfWidth:new C,halfHeight:new C};break}return i[t.id]=e,e}}}function Sx(){let i={};return{get:function(t){if(i[t.id]!==void 0)return i[t.id];let e;switch(t.type){case"SunLight":case"DirectionalLight":e={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new vt};break;case"SpotLight":e={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new vt};break;case"PointLight":e={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new vt,shadowCameraNear:1,shadowCameraFar:1e3};break}return i[t.id]=e,e}}}var bx=0;function Ex(i,t){return(t.castShadow?2:0)-(i.castShadow?2:0)+(t.map?1:0)-(i.map?1:0)}function wx(i){let t=new Mx,e=Sx(),n={version:0,hash:{sunLength:-1,directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numSunShadows:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],sun:[],sunShadow:[],sunShadowMap:[],sunShadowMatrix:[],sunShadowCascade:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let l=0;l<9;l++)n.probe.push(new C);let s=new C,r=new de,a=new de;function o(l){let u=0,d=0,h=0;for(let F=0;F<9;F++)n.probe[F].set(0,0,0);let f=0,g=0,x=0,p=0,m=0,y=0,E=0,v=0,b=0,M=0,A=0,_=0,T=0,P=0;l.sort(Ex);for(let F=0,V=l.length;F<V;F++){let I=l[F],z=I.color,q=I.intensity,j=I.distance,at=null;if(I.shadow&&I.shadow.map&&(I.shadow.map.texture.format===yi?at=I.shadow.map.texture:at=I.shadow.map.depthTexture||I.shadow.map.texture),I.isAmbientLight)u+=z.r*q,d+=z.g*q,h+=z.b*q;else if(I.isLightProbe){for(let K=0;K<9;K++)n.probe[K].addScaledVector(I.sh.coefficients[K],q);P++}else if(I.isSunLight){let K=t.get(I);if(K.color.copy(I.color).multiplyScalar(I.intensity),I.castShadow){let st=I.shadow,it=e.get(I);it.shadowIntensity=st.intensity,it.shadowBias=st.bias,it.shadowNormalBias=st.normalBias,it.shadowRadius=st.radius,it.shadowMapSize.copy(st.mapSize).multiply(st.getFrameExtents()),n.sunShadow[g]=it,n.sunShadowMap[g]=at;let Rt=st.getViewportCount();for(let mt=0;mt<Rt;mt++)n.sunShadowMatrix[x+mt]=st.getMatrix(mt),n.sunShadowCascade[x+mt]=st._cascadeData[mt];x+=Rt,g++}n.sun[f]=K,f++}else if(I.isDirectionalLight){let K=t.get(I);if(K.color.copy(I.color).multiplyScalar(I.intensity),I.castShadow){let st=I.shadow,it=e.get(I);it.shadowIntensity=st.intensity,it.shadowBias=st.bias,it.shadowNormalBias=st.normalBias,it.shadowRadius=st.radius,it.shadowMapSize=st.mapSize,n.directionalShadow[p]=it,n.directionalShadowMap[p]=at,n.directionalShadowMatrix[p]=I.shadow.matrix,b++}n.directional[p]=K,p++}else if(I.isSpotLight){let K=t.get(I);K.position.setFromMatrixPosition(I.matrixWorld),K.color.copy(z).multiplyScalar(q),K.distance=j,K.coneCos=Math.cos(I.angle),K.penumbraCos=Math.cos(I.angle*(1-I.penumbra)),K.decay=I.decay,n.spot[y]=K;let st=I.shadow;if(I.map&&(n.spotLightMap[_]=I.map,_++,st.updateMatrices(I),I.castShadow&&T++),n.spotLightMatrix[y]=st.matrix,I.castShadow){let it=e.get(I);it.shadowIntensity=st.intensity,it.shadowBias=st.bias,it.shadowNormalBias=st.normalBias,it.shadowRadius=st.radius,it.shadowMapSize=st.mapSize,n.spotShadow[y]=it,n.spotShadowMap[y]=at,A++}y++}else if(I.isRectAreaLight){let K=t.get(I);K.color.copy(z).multiplyScalar(q),K.halfWidth.set(I.width*.5,0,0),K.halfHeight.set(0,I.height*.5,0),n.rectArea[E]=K,E++}else if(I.isPointLight){let K=t.get(I);if(K.color.copy(I.color).multiplyScalar(I.intensity),K.distance=I.distance,K.decay=I.decay,I.castShadow){let st=I.shadow,it=e.get(I);it.shadowIntensity=st.intensity,it.shadowBias=st.bias,it.shadowNormalBias=st.normalBias,it.shadowRadius=st.radius,it.shadowMapSize=st.mapSize,it.shadowCameraNear=st.camera.near,it.shadowCameraFar=st.camera.far,n.pointShadow[m]=it,n.pointShadowMap[m]=at,n.pointShadowMatrix[m]=I.shadow.matrix,M++}n.point[m]=K,m++}else if(I.isHemisphereLight){let K=t.get(I);K.skyColor.copy(I.color).multiplyScalar(q),K.groundColor.copy(I.groundColor).multiplyScalar(q),n.hemi[v]=K,v++}}E>0&&(i.has("OES_texture_float_linear")===!0?(n.rectAreaLTC1=Nt.LTC_FLOAT_1,n.rectAreaLTC2=Nt.LTC_FLOAT_2):(n.rectAreaLTC1=Nt.LTC_HALF_1,n.rectAreaLTC2=Nt.LTC_HALF_2)),n.ambient[0]=u,n.ambient[1]=d,n.ambient[2]=h;let L=n.hash;(L.sunLength!==f||L.directionalLength!==p||L.pointLength!==m||L.spotLength!==y||L.rectAreaLength!==E||L.hemiLength!==v||L.numSunShadows!==g||L.numDirectionalShadows!==b||L.numPointShadows!==M||L.numSpotShadows!==A||L.numSpotMaps!==_||L.numLightProbes!==P)&&(n.sun.length=f,n.directional.length=p,n.spot.length=y,n.rectArea.length=E,n.point.length=m,n.hemi.length=v,n.sunShadow.length=g,n.sunShadowMap.length=g,n.sunShadowMatrix.length=x,n.sunShadowCascade.length=x,n.directionalShadow.length=b,n.directionalShadowMap.length=b,n.directionalShadowMatrix.length=b,n.pointShadow.length=M,n.pointShadowMap.length=M,n.pointShadowMatrix.length=M,n.spotShadow.length=A,n.spotShadowMap.length=A,n.spotLightMatrix.length=A+_-T,n.spotLightMap.length=_,n.numSpotLightShadowsWithMaps=T,n.numLightProbes=P,L.sunLength=f,L.directionalLength=p,L.pointLength=m,L.spotLength=y,L.rectAreaLength=E,L.hemiLength=v,L.numSunShadows=g,L.numDirectionalShadows=b,L.numPointShadows=M,L.numSpotShadows=A,L.numSpotMaps=_,L.numLightProbes=P,n.version=bx++)}function c(l,u){let d=0,h=0,f=0,g=0,x=0,p=0,m=u.matrixWorldInverse;for(let y=0,E=l.length;y<E;y++){let v=l[y];if(v.isSunLight){let b=n.sun[d];b.direction.setFromMatrixPosition(v.matrixWorld),b.direction.transformDirection(m),d++}else if(v.isDirectionalLight){let b=n.directional[h];b.direction.setFromMatrixPosition(v.matrixWorld),s.setFromMatrixPosition(v.target.matrixWorld),b.direction.sub(s),b.direction.transformDirection(m),h++}else if(v.isSpotLight){let b=n.spot[g];b.position.setFromMatrixPosition(v.matrixWorld),b.position.applyMatrix4(m),b.direction.setFromMatrixPosition(v.matrixWorld),s.setFromMatrixPosition(v.target.matrixWorld),b.direction.sub(s),b.direction.transformDirection(m),g++}else if(v.isRectAreaLight){let b=n.rectArea[x];b.position.setFromMatrixPosition(v.matrixWorld),b.position.applyMatrix4(m),a.identity(),r.copy(v.matrixWorld),r.premultiply(m),a.extractRotation(r),b.halfWidth.set(v.width*.5,0,0),b.halfHeight.set(0,v.height*.5,0),b.halfWidth.applyMatrix4(a),b.halfHeight.applyMatrix4(a),x++}else if(v.isPointLight){let b=n.point[f];b.position.setFromMatrixPosition(v.matrixWorld),b.position.applyMatrix4(m),f++}else if(v.isHemisphereLight){let b=n.hemi[p];b.direction.setFromMatrixPosition(v.matrixWorld),b.direction.transformDirection(m),p++}}}return{setup:o,setupView:c,state:n}}function Cd(i){let t=new wx(i),e=[],n=[],s=[];function r(h){d.camera=h,e.length=0,n.length=0,s.length=0}function a(h){e.push(h)}function o(h){n.push(h)}function c(h){s.push(h)}function l(){t.setup(e)}function u(h){t.setupView(e,h)}let d={lightsArray:e,shadowsArray:n,lightProbeGridArray:s,camera:null,lights:t,transmissionRenderTarget:{},textureUnits:0};return{init:r,state:d,setupLights:l,setupLightsView:u,pushLight:a,pushShadow:o,pushLightProbeGrid:c}}function Tx(i){let t=new WeakMap;function e(s,r=0){let a=t.get(s),o;return a===void 0?(o=new Cd(i),t.set(s,[o])):r>=a.length?(o=new Cd(i),a.push(o)):o=a[r],o}function n(){t=new WeakMap}return{get:e,dispose:n}}var Ax=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,Rx=`uniform sampler2D shadow_pass;
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
}`,Cx=[new C(1,0,0),new C(-1,0,0),new C(0,1,0),new C(0,-1,0),new C(0,0,1),new C(0,0,-1)],Px=[new C(0,-1,0),new C(0,-1,0),new C(0,0,1),new C(0,0,-1),new C(0,-1,0),new C(0,-1,0)],Pd=new de,wa=new C,vh=new C;function Ix(i,t,e){let n=new sr,s=new vt,r=new vt,a=new xe,o=new Ro,c=new Co,l={},u=e.maxTextureSize,d={[rs]:on,[on]:rs,[vn]:vn},h=new Oe({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new vt},radius:{value:4}},vertexShader:Ax,fragmentShader:Rx}),f=h.clone();f.defines.HORIZONTAL_PASS=1;let g=new ge;g.setAttribute("position",new Ue(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));let x=new ct(g,h),p=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Ss;let m=this.type;this.render=function(M,A,_){if(p.enabled===!1||p.autoUpdate===!1&&p.needsUpdate===!1||M.length===0)return;this.type===Su&&(ie("WebGLShadowMap: PCFSoftShadowMap has been removed. Using PCFShadowMap instead."),this.type=Ss);let T=i.getRenderTarget(),P=i.getActiveCubeFace(),L=i.getActiveMipmapLevel(),F=i.state;F.setBlending(_i),F.buffers.depth.getReversed()===!0?F.buffers.color.setClear(0,0,0,0):F.buffers.color.setClear(1,1,1,1),F.buffers.depth.setTest(!0),F.setScissorTest(!1);let V=m!==this.type;V&&A.traverse(function(I){I.material&&(Array.isArray(I.material)?I.material.forEach(z=>z.needsUpdate=!0):I.material.needsUpdate=!0)});for(let I=0,z=M.length;I<z;I++){let q=M[I],j=q.shadow;if(j===void 0){ie("WebGLShadowMap:",q,"has no shadow.");continue}if(j.autoUpdate===!1&&j.needsUpdate===!1)continue;s.copy(j.mapSize);let at=j.getFrameExtents();s.multiply(at),r.copy(j.mapSize),(s.x>u||s.y>u)&&(s.x>u&&(r.x=Math.floor(u/at.x),s.x=r.x*at.x,j.mapSize.x=r.x),s.y>u&&(r.y=Math.floor(u/at.y),s.y=r.y*at.y,j.mapSize.y=r.y));let K=i.state.buffers.depth.getReversed();if(j.camera._reversedDepth=K,j.map===null||V===!0){if(j.map!==null&&(j.map.depthTexture!==null&&(j.map.depthTexture.dispose(),j.map.depthTexture=null),j.map.dispose()),this.type===hr){if(q.isPointLight){ie("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}j.map=new In(s.x,s.y,{format:yi,type:Bn,minFilter:Ke,magFilter:Ke,generateMipmaps:!1}),j.map.texture.name=q.name+".shadowMap",j.map.depthTexture=new Ji(s.x,s.y,qn),j.map.depthTexture.name=q.name+".shadowMapDepth",j.map.depthTexture.format=pi,j.map.depthTexture.compareFunction=null,j.map.depthTexture.minFilter=nn,j.map.depthTexture.magFilter=nn}else q.isPointLight?(j.map=new Uc(s.x),j.map.depthTexture=new yo(s.x,li)):(j.map=new In(s.x,s.y),j.map.depthTexture=new Ji(s.x,s.y,li)),j.map.depthTexture.name=q.name+".shadowMap",j.map.depthTexture.format=pi,this.type===Ss?(j.map.depthTexture.compareFunction=K?Ic:Pc,j.map.depthTexture.minFilter=Ke,j.map.depthTexture.magFilter=Ke):(j.map.depthTexture.compareFunction=null,j.map.depthTexture.minFilter=nn,j.map.depthTexture.magFilter=nn);j.camera.updateProjectionMatrix()}j.map.isWebGLCubeRenderTarget!==!0&&(j.map.width!==s.x||j.map.height!==s.y)&&j.map.setSize(s.x,s.y);let st=j.map.isWebGLCubeRenderTarget?6:j.getViewportCount();q.isPointLight!==!0&&j.updateMatrices(q,_);for(let it=0;it<st;it++){let Rt=j.getCamera(it);if(q.isPointLight){let mt=j.camera,Ut=j.matrix,Dt=q.distance||mt.far;Dt!==mt.far&&(mt.far=Dt,mt.updateProjectionMatrix()),wa.setFromMatrixPosition(q.matrixWorld),mt.position.copy(wa),vh.copy(mt.position),vh.add(Cx[it]),mt.up.copy(Px[it]),mt.lookAt(vh),mt.updateMatrixWorld(),Ut.makeTranslation(-wa.x,-wa.y,-wa.z),Pd.multiplyMatrices(mt.projectionMatrix,mt.matrixWorldInverse),j._frustum.setFromProjectionMatrix(Pd,mt.coordinateSystem,mt.reversedDepth)}if(j.map.isWebGLCubeRenderTarget)i.setRenderTarget(j.map,it),i.clear();else{it===0&&(i.setRenderTarget(j.map),i.clear());let mt=j.getViewport(it);a.set(r.x*mt.x,r.y*mt.y,r.x*mt.z,r.y*mt.w),F.viewport(a)}n=j.getFrustum(it),v(A,_,Rt,q,this.type)}j.isPointLightShadow!==!0&&this.type===hr&&y(j,_),j.needsUpdate=!1}m=this.type,p.needsUpdate=!1,i.setRenderTarget(T,P,L)};function y(M,A){let _=t.update(x);h.defines.VSM_SAMPLES!==M.blurSamples&&(h.defines.VSM_SAMPLES=M.blurSamples,f.defines.VSM_SAMPLES=M.blurSamples,h.needsUpdate=!0,f.needsUpdate=!0),M.mapPass===null?M.mapPass=new In(s.x,s.y,{format:yi,type:Bn}):(M.mapPass.width!==M.map.width||M.mapPass.height!==M.map.height)&&M.mapPass.setSize(M.map.width,M.map.height),h.uniforms.shadow_pass.value=M.map.depthTexture,h.uniforms.resolution.value.set(M.map.width,M.map.height),h.uniforms.radius.value=M.radius,i.setRenderTarget(M.mapPass),i.clear(),i.renderBufferDirect(A,null,_,h,x,null),f.uniforms.shadow_pass.value=M.mapPass.texture,f.uniforms.resolution.value.set(M.map.width,M.map.height),f.uniforms.radius.value=M.radius,i.setRenderTarget(M.map),i.clear(),i.renderBufferDirect(A,null,_,f,x,null)}function E(M,A,_,T){let P=null,L=_.isPointLight===!0?M.customDistanceMaterial:M.customDepthMaterial;if(L!==void 0)P=L;else if(P=_.isPointLight===!0?c:o,i.localClippingEnabled&&A.clipShadows===!0&&Array.isArray(A.clippingPlanes)&&A.clippingPlanes.length!==0||A.displacementMap&&A.displacementScale!==0||A.alphaMap&&A.alphaTest>0||A.map&&A.alphaTest>0||A.alphaToCoverage===!0){let F=P.uuid,V=A.uuid,I=l[F];I===void 0&&(I={},l[F]=I);let z=I[V];z===void 0&&(z=P.clone(),I[V]=z,A.addEventListener("dispose",b)),P=z}if(P.visible=A.visible,P.wireframe=A.wireframe,T===hr?P.side=A.shadowSide!==null?A.shadowSide:A.side:P.side=A.shadowSide!==null?A.shadowSide:d[A.side],P.alphaMap=A.alphaMap,P.alphaTest=A.alphaToCoverage===!0?.5:A.alphaTest,P.map=A.map,P.clipShadows=A.clipShadows,P.clippingPlanes=A.clippingPlanes,P.clipIntersection=A.clipIntersection,P.displacementMap=A.displacementMap,P.displacementScale=A.displacementScale,P.displacementBias=A.displacementBias,P.wireframeLinewidth=A.wireframeLinewidth,P.linewidth=A.linewidth,_.isPointLight===!0&&P.isMeshDistanceMaterial===!0){let F=i.properties.get(P);F.light=_}return P}function v(M,A,_,T,P){if(M.visible===!1)return;if(M.layers.test(A.layers)&&(M.isMesh||M.isLine||M.isPoints)&&(M.castShadow||M.receiveShadow&&P===hr)&&(!M.frustumCulled||M.intersectsFrustum(n))){M.modelViewMatrix.multiplyMatrices(_.matrixWorldInverse,M.matrixWorld);let V=t.update(M),I=M.material;if(Array.isArray(I)){let z=V.groups;for(let q=0,j=z.length;q<j;q++){let at=z[q],K=I[at.materialIndex];if(K&&K.visible){let st=E(M,K,T,P);M.onBeforeShadow(i,M,A,_,V,st,at),i.renderBufferDirect(_,null,V,st,M,at),M.onAfterShadow(i,M,A,_,V,st,at)}}}else if(I.visible){let z=E(M,I,T,P);M.onBeforeShadow(i,M,A,_,V,z,null),i.renderBufferDirect(_,null,V,z,M,null),M.onAfterShadow(i,M,A,_,V,z,null)}}let F=M.children;for(let V=0,I=F.length;V<I;V++)v(F[V],A,_,T,P)}function b(M){M.target.removeEventListener("dispose",b);for(let _ in l){let T=l[_],P=M.target.uuid;P in T&&(T[P].dispose(),delete T[P])}}}function Lx(i,t){function e(){let B=!1,Ct=new xe,lt=null,Pt=new xe(0,0,0,0);return{setMask:function(yt){lt!==yt&&!B&&(i.colorMask(yt,yt,yt,yt),lt=yt)},setLocked:function(yt){B=yt},setClear:function(yt,pt,Xt,Ht,we){we===!0&&(yt*=Ht,pt*=Ht,Xt*=Ht),Ct.set(yt,pt,Xt,Ht),Pt.equals(Ct)===!1&&(i.clearColor(yt,pt,Xt,Ht),Pt.copy(Ct))},reset:function(){B=!1,lt=null,Pt.set(-1,0,0,0)}}}function n(){let B=!1,Ct=!1,lt=null,Pt=null,yt=null;return{setReversed:function(pt){if(Ct!==pt){let Xt=t.get("EXT_clip_control");pt?Xt.clipControlEXT(Xt.LOWER_LEFT_EXT,Xt.ZERO_TO_ONE_EXT):Xt.clipControlEXT(Xt.LOWER_LEFT_EXT,Xt.NEGATIVE_ONE_TO_ONE_EXT),Ct=pt;let Ht=yt;yt=null,this.setClear(Ht)}},getReversed:function(){return Ct},setTest:function(pt){pt?k(i.DEPTH_TEST):dt(i.DEPTH_TEST)},setMask:function(pt){lt!==pt&&!B&&(i.depthMask(pt),lt=pt)},setFunc:function(pt){if(Ct&&(pt=nd[pt]),Pt!==pt){switch(pt){case ro:i.depthFunc(i.NEVER);break;case ao:i.depthFunc(i.ALWAYS);break;case oo:i.depthFunc(i.LESS);break;case $s:i.depthFunc(i.LEQUAL);break;case co:i.depthFunc(i.EQUAL);break;case lo:i.depthFunc(i.GEQUAL);break;case ho:i.depthFunc(i.GREATER);break;case uo:i.depthFunc(i.NOTEQUAL);break;default:i.depthFunc(i.LEQUAL)}Pt=pt}},setLocked:function(pt){B=pt},setClear:function(pt){yt!==pt&&(yt=pt,Ct&&(pt=1-pt),i.clearDepth(pt))},reset:function(){B=!1,lt=null,Pt=null,yt=null,Ct=!1}}}function s(){let B=!1,Ct=null,lt=null,Pt=null,yt=null,pt=null,Xt=null,Ht=null,we=null;return{setTest:function(ye){B||(ye?k(i.STENCIL_TEST):dt(i.STENCIL_TEST))},setMask:function(ye){Ct!==ye&&!B&&(i.stencilMask(ye),Ct=ye)},setFunc:function(ye,dn,fn){(lt!==ye||Pt!==dn||yt!==fn)&&(i.stencilFunc(ye,dn,fn),lt=ye,Pt=dn,yt=fn)},setOp:function(ye,dn,fn){(pt!==ye||Xt!==dn||Ht!==fn)&&(i.stencilOp(ye,dn,fn),pt=ye,Xt=dn,Ht=fn)},setLocked:function(ye){B=ye},setClear:function(ye){we!==ye&&(i.clearStencil(ye),we=ye)},reset:function(){B=!1,Ct=null,lt=null,Pt=null,yt=null,pt=null,Xt=null,Ht=null,we=null}}}let r=new e,a=new n,o=new s,c=new WeakMap,l=new WeakMap,u={},d={},h={},f=new WeakMap,g=[],x=null,p=!1,m=null,y=null,E=null,v=null,b=null,M=null,A=null,_=new Wt(0,0,0),T=0,P=!1,L=null,F=null,V=null,I=null,z=null,q=i.getParameter(i.MAX_COMBINED_TEXTURE_IMAGE_UNITS),j=!1,at=0,K=i.getParameter(i.VERSION);K.indexOf("WebGL")!==-1?(at=parseFloat(/^WebGL (\d)/.exec(K)[1]),j=at>=1):K.indexOf("OpenGL ES")!==-1&&(at=parseFloat(/^OpenGL ES (\d)/.exec(K)[1]),j=at>=2);let st=null,it={},Rt=i.getParameter(i.SCISSOR_BOX),mt=i.getParameter(i.VIEWPORT),Ut=new xe().fromArray(Rt),Dt=new xe().fromArray(mt);function ft(B,Ct,lt,Pt){let yt=new Uint8Array(4),pt=i.createTexture();i.bindTexture(B,pt),i.texParameteri(B,i.TEXTURE_MIN_FILTER,i.NEAREST),i.texParameteri(B,i.TEXTURE_MAG_FILTER,i.NEAREST);for(let Xt=0;Xt<lt;Xt++)B===i.TEXTURE_3D||B===i.TEXTURE_2D_ARRAY?i.texImage3D(Ct,0,i.RGBA,1,1,Pt,0,i.RGBA,i.UNSIGNED_BYTE,yt):i.texImage2D(Ct+Xt,0,i.RGBA,1,1,0,i.RGBA,i.UNSIGNED_BYTE,yt);return pt}let N={};N[i.TEXTURE_2D]=ft(i.TEXTURE_2D,i.TEXTURE_2D,1),N[i.TEXTURE_CUBE_MAP]=ft(i.TEXTURE_CUBE_MAP,i.TEXTURE_CUBE_MAP_POSITIVE_X,6),N[i.TEXTURE_2D_ARRAY]=ft(i.TEXTURE_2D_ARRAY,i.TEXTURE_2D_ARRAY,1,1),N[i.TEXTURE_3D]=ft(i.TEXTURE_3D,i.TEXTURE_3D,1,1),r.setClear(0,0,0,1),a.setClear(1),o.setClear(0),k(i.DEPTH_TEST),a.setFunc($s),et(!1),gt(Ul),k(i.CULL_FACE),tt(_i);function k(B){u[B]!==!0&&(i.enable(B),u[B]=!0)}function dt(B){u[B]!==!1&&(i.disable(B),u[B]=!1)}function St(B,Ct){return h[B]!==Ct?(i.bindFramebuffer(B,Ct),h[B]=Ct,B===i.DRAW_FRAMEBUFFER&&(h[i.FRAMEBUFFER]=Ct),B===i.FRAMEBUFFER&&(h[i.DRAW_FRAMEBUFFER]=Ct),!0):!1}function Mt(B,Ct){let lt=g,Pt=!1;if(B){lt=f.get(Ct),lt===void 0&&(lt=[],f.set(Ct,lt));let yt=B.textures;if(lt.length!==yt.length||lt[0]!==i.COLOR_ATTACHMENT0){for(let pt=0,Xt=yt.length;pt<Xt;pt++)lt[pt]=i.COLOR_ATTACHMENT0+pt;lt.length=yt.length,Pt=!0}}else lt[0]!==i.BACK&&(lt[0]=i.BACK,Pt=!0);Pt&&i.drawBuffers(lt)}function Ft(B){return x!==B?(i.useProgram(B),x=B,!0):!1}let xt={[bs]:i.FUNC_ADD,[Eu]:i.FUNC_SUBTRACT,[wu]:i.FUNC_REVERSE_SUBTRACT};xt[Tu]=i.MIN,xt[Au]=i.MAX;let X={[Ru]:i.ZERO,[Cu]:i.ONE,[Pu]:i.SRC_COLOR,[zl]:i.SRC_ALPHA,[Fu]:i.SRC_ALPHA_SATURATE,[Uu]:i.DST_COLOR,[Lu]:i.DST_ALPHA,[Iu]:i.ONE_MINUS_SRC_COLOR,[Ol]:i.ONE_MINUS_SRC_ALPHA,[Nu]:i.ONE_MINUS_DST_COLOR,[Du]:i.ONE_MINUS_DST_ALPHA,[zu]:i.CONSTANT_COLOR,[Ou]:i.ONE_MINUS_CONSTANT_COLOR,[Bu]:i.CONSTANT_ALPHA,[ku]:i.ONE_MINUS_CONSTANT_ALPHA};function tt(B,Ct,lt,Pt,yt,pt,Xt,Ht,we,ye){if(B===_i){p===!0&&(dt(i.BLEND),p=!1);return}if(p===!1&&(k(i.BLEND),p=!0),B!==bu){if(B!==m||ye!==P){if((y!==bs||b!==bs)&&(i.blendEquation(i.FUNC_ADD),y=bs,b=bs),ye)switch(B){case ur:i.blendFuncSeparate(i.ONE,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case as:i.blendFunc(i.ONE,i.ONE);break;case Nl:i.blendFuncSeparate(i.ZERO,i.ONE_MINUS_SRC_COLOR,i.ZERO,i.ONE);break;case Fl:i.blendFuncSeparate(i.DST_COLOR,i.ONE_MINUS_SRC_ALPHA,i.ZERO,i.ONE);break;default:ae("WebGLState: Invalid blending: ",B);break}else switch(B){case ur:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case as:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE,i.ONE,i.ONE);break;case Nl:ae("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case Fl:ae("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:ae("WebGLState: Invalid blending: ",B);break}E=null,v=null,M=null,A=null,_.set(0,0,0),T=0,m=B,P=ye}return}yt=yt||Ct,pt=pt||lt,Xt=Xt||Pt,(Ct!==y||yt!==b)&&(i.blendEquationSeparate(xt[Ct],xt[yt]),y=Ct,b=yt),(lt!==E||Pt!==v||pt!==M||Xt!==A)&&(i.blendFuncSeparate(X[lt],X[Pt],X[pt],X[Xt]),E=lt,v=Pt,M=pt,A=Xt),(Ht.equals(_)===!1||we!==T)&&(i.blendColor(Ht.r,Ht.g,Ht.b,we),_.copy(Ht),T=we),m=B,P=!1}function G(B,Ct){B.side===vn?dt(i.CULL_FACE):k(i.CULL_FACE);let lt=B.side===on;Ct&&(lt=!lt),et(lt),B.blending===ur&&B.transparent===!1?tt(_i):tt(B.blending,B.blendEquation,B.blendSrc,B.blendDst,B.blendEquationAlpha,B.blendSrcAlpha,B.blendDstAlpha,B.blendColor,B.blendAlpha,B.premultipliedAlpha),a.setFunc(B.depthFunc),a.setTest(B.depthTest),a.setMask(B.depthWrite),r.setMask(B.colorWrite);let Pt=B.stencilWrite;o.setTest(Pt),Pt&&(o.setMask(B.stencilWriteMask),o.setFunc(B.stencilFunc,B.stencilRef,B.stencilFuncMask),o.setOp(B.stencilFail,B.stencilZFail,B.stencilZPass)),bt(B.polygonOffset,B.polygonOffsetFactor,B.polygonOffsetUnits),B.alphaToCoverage===!0?k(i.SAMPLE_ALPHA_TO_COVERAGE):dt(i.SAMPLE_ALPHA_TO_COVERAGE)}function et(B){L!==B&&(B?i.frontFace(i.CW):i.frontFace(i.CCW),L=B)}function gt(B){B!==yu?(k(i.CULL_FACE),B!==F&&(B===Ul?i.cullFace(i.BACK):B===Mu?i.cullFace(i.FRONT):i.cullFace(i.FRONT_AND_BACK))):dt(i.CULL_FACE),F=B}function Bt(B){B!==V&&(j&&i.lineWidth(B),V=B)}function bt(B,Ct,lt){B?(k(i.POLYGON_OFFSET_FILL),(I!==Ct||z!==lt)&&(I=Ct,z=lt,a.getReversed()&&(Ct=-Ct),i.polygonOffset(Ct,lt))):dt(i.POLYGON_OFFSET_FILL)}function jt(B){B?k(i.SCISSOR_TEST):dt(i.SCISSOR_TEST)}function ne(B){B===void 0&&(B=i.TEXTURE0+q-1),st!==B&&(i.activeTexture(B),st=B)}function U(B,Ct,lt){lt===void 0&&(st===null?lt=i.TEXTURE0+q-1:lt=st);let Pt=it[lt];Pt===void 0&&(Pt={type:void 0,texture:void 0},it[lt]=Pt),(Pt.type!==B||Pt.texture!==Ct)&&(st!==lt&&(i.activeTexture(lt),st=lt),i.bindTexture(B,Ct||N[B]),Pt.type=B,Pt.texture=Ct)}function Ee(){let B=it[st];B!==void 0&&B.type!==void 0&&(i.bindTexture(B.type,null),B.type=void 0,B.texture=void 0)}function se(){try{i.compressedTexImage2D(...arguments)}catch(B){ae("WebGLState:",B)}}function R(){try{i.compressedTexImage3D(...arguments)}catch(B){ae("WebGLState:",B)}}function S(){try{i.texSubImage2D(...arguments)}catch(B){ae("WebGLState:",B)}}function H(){try{i.texSubImage3D(...arguments)}catch(B){ae("WebGLState:",B)}}function Y(){try{i.compressedTexSubImage2D(...arguments)}catch(B){ae("WebGLState:",B)}}function rt(){try{i.compressedTexSubImage3D(...arguments)}catch(B){ae("WebGLState:",B)}}function _t(){try{i.texStorage2D(...arguments)}catch(B){ae("WebGLState:",B)}}function Et(){try{i.texStorage3D(...arguments)}catch(B){ae("WebGLState:",B)}}function nt(){try{i.texImage2D(...arguments)}catch(B){ae("WebGLState:",B)}}function ut(){try{i.texImage3D(...arguments)}catch(B){ae("WebGLState:",B)}}function At(B){return d[B]!==void 0?d[B]:i.getParameter(B)}function Zt(B,Ct){d[B]!==Ct&&(i.pixelStorei(B,Ct),d[B]=Ct)}function It(B){Ut.equals(B)===!1&&(i.scissor(B.x,B.y,B.z,B.w),Ut.copy(B))}function Lt(B){Dt.equals(B)===!1&&(i.viewport(B.x,B.y,B.z,B.w),Dt.copy(B))}function $t(B,Ct){let lt=l.get(Ct);lt===void 0&&(lt=new WeakMap,l.set(Ct,lt));let Pt=lt.get(B);Pt===void 0&&(Pt=i.getUniformBlockIndex(Ct,B.name),lt.set(B,Pt))}function ee(B,Ct){let Pt=l.get(Ct).get(B);c.get(Ct)!==Pt&&(i.uniformBlockBinding(Ct,Pt,B.__bindingPointIndex),c.set(Ct,Pt))}function ce(){i.disable(i.BLEND),i.disable(i.CULL_FACE),i.disable(i.DEPTH_TEST),i.disable(i.POLYGON_OFFSET_FILL),i.disable(i.SCISSOR_TEST),i.disable(i.STENCIL_TEST),i.disable(i.SAMPLE_ALPHA_TO_COVERAGE),i.blendEquation(i.FUNC_ADD),i.blendFunc(i.ONE,i.ZERO),i.blendFuncSeparate(i.ONE,i.ZERO,i.ONE,i.ZERO),i.blendColor(0,0,0,0),i.colorMask(!0,!0,!0,!0),i.clearColor(0,0,0,0),i.depthMask(!0),i.depthFunc(i.LESS),a.setReversed(!1),i.clearDepth(1),i.stencilMask(4294967295),i.stencilFunc(i.ALWAYS,0,4294967295),i.stencilOp(i.KEEP,i.KEEP,i.KEEP),i.clearStencil(0),i.cullFace(i.BACK),i.frontFace(i.CCW),i.polygonOffset(0,0),i.activeTexture(i.TEXTURE0),i.bindFramebuffer(i.FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.useProgram(null),i.lineWidth(1),i.scissor(0,0,i.canvas.width,i.canvas.height),i.viewport(0,0,i.canvas.width,i.canvas.height),i.pixelStorei(i.PACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,!1),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,i.BROWSER_DEFAULT_WEBGL),i.pixelStorei(i.PACK_ROW_LENGTH,0),i.pixelStorei(i.PACK_SKIP_PIXELS,0),i.pixelStorei(i.PACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_ROW_LENGTH,0),i.pixelStorei(i.UNPACK_IMAGE_HEIGHT,0),i.pixelStorei(i.UNPACK_SKIP_PIXELS,0),i.pixelStorei(i.UNPACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_SKIP_IMAGES,0),u={},d={},st=null,it={},h={},f=new WeakMap,g=[],x=null,p=!1,m=null,y=null,E=null,v=null,b=null,M=null,A=null,_=new Wt(0,0,0),T=0,P=!1,L=null,F=null,V=null,I=null,z=null,Ut.set(0,0,i.canvas.width,i.canvas.height),Dt.set(0,0,i.canvas.width,i.canvas.height),r.reset(),a.reset(),o.reset()}return{buffers:{color:r,depth:a,stencil:o},enable:k,disable:dt,bindFramebuffer:St,drawBuffers:Mt,useProgram:Ft,setBlending:tt,setMaterial:G,setFlipSided:et,setCullFace:gt,setLineWidth:Bt,setPolygonOffset:bt,setScissorTest:jt,activeTexture:ne,bindTexture:U,unbindTexture:Ee,compressedTexImage2D:se,compressedTexImage3D:R,texImage2D:nt,texImage3D:ut,pixelStorei:Zt,getParameter:At,updateUBOMapping:$t,uniformBlockBinding:ee,texStorage2D:_t,texStorage3D:Et,texSubImage2D:S,texSubImage3D:H,compressedTexSubImage2D:Y,compressedTexSubImage3D:rt,scissor:It,viewport:Lt,reset:ce}}function Dx(i,t,e,n,s,r,a){let o=t.has("WEBGL_multisampled_render_to_texture")?t.get("WEBGL_multisampled_render_to_texture"):null,c=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),l=new vt,u=new WeakMap,d=new Set,h,f=new WeakMap,g=!1;try{g=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function x(R,S){return g?new OffscreenCanvas(R,S):zr("canvas")}function p(R,S,H){let Y=1,rt=se(R);if((rt.width>H||rt.height>H)&&(Y=H/Math.max(rt.width,rt.height)),Y<1)if(typeof HTMLImageElement<"u"&&R instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&R instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&R instanceof ImageBitmap||typeof VideoFrame<"u"&&R instanceof VideoFrame){let _t=Math.floor(Y*rt.width),Et=Math.floor(Y*rt.height);h===void 0&&(h=x(_t,Et));let nt=S?x(_t,Et):h;return nt.width=_t,nt.height=Et,nt.getContext("2d").drawImage(R,0,0,_t,Et),ie("WebGLRenderer: Texture has been resized from ("+rt.width+"x"+rt.height+") to ("+_t+"x"+Et+")."),nt}else return"data"in R&&ie("WebGLRenderer: Image in DataTexture is too big ("+rt.width+"x"+rt.height+")."),R;return R}function m(R){return R.generateMipmaps}function y(R){i.generateMipmap(R)}function E(R){return R.isWebGLCubeRenderTarget?i.TEXTURE_CUBE_MAP:R.isWebGL3DRenderTarget?i.TEXTURE_3D:R.isWebGLArrayRenderTarget||R.isCompressedArrayTexture?i.TEXTURE_2D_ARRAY:i.TEXTURE_2D}function v(R,S,H,Y,rt,_t=!1){if(R!==null){if(i[R]!==void 0)return i[R];ie("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+R+"'")}let Et;Y&&(Et=t.get("EXT_texture_norm16"),Et||ie("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let nt=S;if(S===i.RED&&(H===i.FLOAT&&(nt=i.R32F),H===i.HALF_FLOAT&&(nt=i.R16F),H===i.UNSIGNED_BYTE&&(nt=i.R8),H===i.UNSIGNED_SHORT&&Et&&(nt=Et.R16_EXT),H===i.SHORT&&Et&&(nt=Et.R16_SNORM_EXT)),S===i.RED_INTEGER&&(H===i.UNSIGNED_BYTE&&(nt=i.R8UI),H===i.UNSIGNED_SHORT&&(nt=i.R16UI),H===i.UNSIGNED_INT&&(nt=i.R32UI),H===i.BYTE&&(nt=i.R8I),H===i.SHORT&&(nt=i.R16I),H===i.INT&&(nt=i.R32I)),S===i.RG&&(H===i.FLOAT&&(nt=i.RG32F),H===i.HALF_FLOAT&&(nt=i.RG16F),H===i.UNSIGNED_BYTE&&(nt=i.RG8),H===i.UNSIGNED_SHORT&&Et&&(nt=Et.RG16_EXT),H===i.SHORT&&Et&&(nt=Et.RG16_SNORM_EXT)),S===i.RG_INTEGER&&(H===i.UNSIGNED_BYTE&&(nt=i.RG8UI),H===i.UNSIGNED_SHORT&&(nt=i.RG16UI),H===i.UNSIGNED_INT&&(nt=i.RG32UI),H===i.BYTE&&(nt=i.RG8I),H===i.SHORT&&(nt=i.RG16I),H===i.INT&&(nt=i.RG32I)),S===i.RGB_INTEGER&&(H===i.UNSIGNED_BYTE&&(nt=i.RGB8UI),H===i.UNSIGNED_SHORT&&(nt=i.RGB16UI),H===i.UNSIGNED_INT&&(nt=i.RGB32UI),H===i.BYTE&&(nt=i.RGB8I),H===i.SHORT&&(nt=i.RGB16I),H===i.INT&&(nt=i.RGB32I)),S===i.RGBA_INTEGER&&(H===i.UNSIGNED_BYTE&&(nt=i.RGBA8UI),H===i.UNSIGNED_SHORT&&(nt=i.RGBA16UI),H===i.UNSIGNED_INT&&(nt=i.RGBA32UI),H===i.BYTE&&(nt=i.RGBA8I),H===i.SHORT&&(nt=i.RGBA16I),H===i.INT&&(nt=i.RGBA32I)),S===i.RGB&&(H===i.UNSIGNED_SHORT&&Et&&(nt=Et.RGB16_EXT),H===i.SHORT&&Et&&(nt=Et.RGB16_SNORM_EXT),H===i.UNSIGNED_INT_5_9_9_9_REV&&(nt=i.RGB9_E5),H===i.UNSIGNED_INT_10F_11F_11F_REV&&(nt=i.R11F_G11F_B10F)),S===i.RGBA){let ut=_t?Fr:Me.getTransfer(rt);H===i.FLOAT&&(nt=i.RGBA32F),H===i.HALF_FLOAT&&(nt=i.RGBA16F),H===i.UNSIGNED_BYTE&&(nt=ut===Ie?i.SRGB8_ALPHA8:i.RGBA8),H===i.UNSIGNED_SHORT&&Et&&(nt=Et.RGBA16_EXT),H===i.SHORT&&Et&&(nt=Et.RGBA16_SNORM_EXT),H===i.UNSIGNED_SHORT_4_4_4_4&&(nt=i.RGBA4),H===i.UNSIGNED_SHORT_5_5_5_1&&(nt=i.RGB5_A1)}return(nt===i.R16F||nt===i.R32F||nt===i.RG16F||nt===i.RG32F||nt===i.RGBA16F||nt===i.RGBA32F)&&t.get("EXT_color_buffer_float"),nt}function b(R,S){let H;return R?S===null||S===li||S===fr?H=i.DEPTH24_STENCIL8:S===qn?H=i.DEPTH32F_STENCIL8:S===dr&&(H=i.DEPTH24_STENCIL8,ie("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):S===null||S===li||S===fr?H=i.DEPTH_COMPONENT24:S===qn?H=i.DEPTH_COMPONENT32F:S===dr&&(H=i.DEPTH_COMPONENT16),H}function M(R,S){return m(R)===!0||R.isFramebufferTexture&&R.minFilter!==nn&&R.minFilter!==Ke?Math.log2(Math.max(S.width,S.height))+1:R.mipmaps!==void 0&&R.mipmaps.length>0?R.mipmaps.length:R.isCompressedTexture&&Array.isArray(R.image)?S.mipmaps.length:1}function A(R){let S=R.target;S.removeEventListener("dispose",A),T(S),S.isVideoTexture&&u.delete(S),S.isHTMLTexture&&d.delete(S)}function _(R){let S=R.target;S.removeEventListener("dispose",_),L(S)}function T(R){let S=n.get(R);if(S.__webglInit===void 0)return;let H=R.source,Y=f.get(H);if(Y){let rt=Y[S.__cacheKey];rt.usedTimes--,rt.usedTimes===0&&P(R),Object.keys(Y).length===0&&f.delete(H)}n.remove(R)}function P(R){let S=n.get(R);i.deleteTexture(S.__webglTexture);let H=R.source,Y=f.get(H);delete Y[S.__cacheKey],a.memory.textures--}function L(R){let S=n.get(R);if(R.depthTexture&&(R.depthTexture.dispose(),n.remove(R.depthTexture)),R.isWebGLCubeRenderTarget)for(let Y=0;Y<6;Y++){if(Array.isArray(S.__webglFramebuffer[Y]))for(let rt=0;rt<S.__webglFramebuffer[Y].length;rt++)i.deleteFramebuffer(S.__webglFramebuffer[Y][rt]);else i.deleteFramebuffer(S.__webglFramebuffer[Y]);S.__webglDepthbuffer&&i.deleteRenderbuffer(S.__webglDepthbuffer[Y])}else{if(Array.isArray(S.__webglFramebuffer))for(let Y=0;Y<S.__webglFramebuffer.length;Y++)i.deleteFramebuffer(S.__webglFramebuffer[Y]);else i.deleteFramebuffer(S.__webglFramebuffer);if(S.__webglDepthbuffer&&i.deleteRenderbuffer(S.__webglDepthbuffer),S.__webglMultisampledFramebuffer&&i.deleteFramebuffer(S.__webglMultisampledFramebuffer),S.__webglColorRenderbuffer)for(let Y=0;Y<S.__webglColorRenderbuffer.length;Y++)S.__webglColorRenderbuffer[Y]&&i.deleteRenderbuffer(S.__webglColorRenderbuffer[Y]);S.__webglDepthRenderbuffer&&i.deleteRenderbuffer(S.__webglDepthRenderbuffer)}let H=R.textures;for(let Y=0,rt=H.length;Y<rt;Y++){let _t=n.get(H[Y]);_t.__webglTexture&&(i.deleteTexture(_t.__webglTexture),a.memory.textures--),n.remove(H[Y])}n.remove(R)}let F=0;function V(){F=0}function I(){return F}function z(R){F=R}function q(){let R=F;return R>=s.maxTextures&&ie("WebGLTextures: Trying to use "+(R+1)+" texture units while this GPU supports only "+s.maxTextures),F+=1,R}function j(R){let S=[];return S.push(R.wrapS),S.push(R.wrapT),S.push(R.wrapR||0),S.push(R.magFilter),S.push(R.minFilter),S.push(R.anisotropy),S.push(R.internalFormat),S.push(R.format),S.push(R.type),S.push(R.generateMipmaps),S.push(R.premultiplyAlpha),S.push(R.flipY),S.push(R.unpackAlignment),S.push(R.colorSpace),S.join()}function at(R,S){let H=n.get(R);if(R.isVideoTexture&&U(R),R.isRenderTargetTexture===!1&&R.isExternalTexture!==!0&&R.version>0&&H.__version!==R.version){let Y=R.image;if(Y===null)ie("WebGLRenderer: Texture marked for update but no image data found.");else if(Y.complete===!1)ie("WebGLRenderer: Texture marked for update but image is incomplete");else{dt(H,R,S);return}}else R.isExternalTexture&&(H.__webglTexture=R.sourceTexture?R.sourceTexture:null);e.bindTexture(i.TEXTURE_2D,H.__webglTexture,i.TEXTURE0+S)}function K(R,S){let H=n.get(R);if(R.isRenderTargetTexture===!1&&R.version>0&&H.__version!==R.version){dt(H,R,S);return}else R.isExternalTexture&&(H.__webglTexture=R.sourceTexture?R.sourceTexture:null);e.bindTexture(i.TEXTURE_2D_ARRAY,H.__webglTexture,i.TEXTURE0+S)}function st(R,S){let H=n.get(R);if(R.isRenderTargetTexture===!1&&R.version>0&&H.__version!==R.version){dt(H,R,S);return}e.bindTexture(i.TEXTURE_3D,H.__webglTexture,i.TEXTURE0+S)}function it(R,S){let H=n.get(R);if(R.isCubeDepthTexture!==!0&&R.version>0&&H.__version!==R.version){St(H,R,S);return}e.bindTexture(i.TEXTURE_CUBE_MAP,H.__webglTexture,i.TEXTURE0+S)}let Rt={[Js]:i.REPEAT,[Wn]:i.CLAMP_TO_EDGE,[fo]:i.MIRRORED_REPEAT},mt={[nn]:i.NEAREST,[Gu]:i.NEAREST_MIPMAP_NEAREST,[ga]:i.NEAREST_MIPMAP_LINEAR,[Ke]:i.LINEAR,[Xo]:i.LINEAR_MIPMAP_NEAREST,[cs]:i.LINEAR_MIPMAP_LINEAR},Ut={[Yu]:i.NEVER,[Ku]:i.ALWAYS,[ju]:i.LESS,[Pc]:i.LEQUAL,[Zu]:i.EQUAL,[Ic]:i.GEQUAL,[$u]:i.GREATER,[Ju]:i.NOTEQUAL};function Dt(R,S){if(S.type===qn&&t.has("OES_texture_float_linear")===!1&&(S.magFilter===Ke||S.magFilter===Xo||S.magFilter===ga||S.magFilter===cs||S.minFilter===Ke||S.minFilter===Xo||S.minFilter===ga||S.minFilter===cs)&&ie("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),i.texParameteri(R,i.TEXTURE_WRAP_S,Rt[S.wrapS]),i.texParameteri(R,i.TEXTURE_WRAP_T,Rt[S.wrapT]),(R===i.TEXTURE_3D||R===i.TEXTURE_2D_ARRAY)&&i.texParameteri(R,i.TEXTURE_WRAP_R,Rt[S.wrapR]),i.texParameteri(R,i.TEXTURE_MAG_FILTER,mt[S.magFilter]),i.texParameteri(R,i.TEXTURE_MIN_FILTER,mt[S.minFilter]),S.compareFunction&&(i.texParameteri(R,i.TEXTURE_COMPARE_MODE,i.COMPARE_REF_TO_TEXTURE),i.texParameteri(R,i.TEXTURE_COMPARE_FUNC,Ut[S.compareFunction])),t.has("EXT_texture_filter_anisotropic")===!0){if(S.magFilter===nn||S.minFilter!==ga&&S.minFilter!==cs||S.type===qn&&t.has("OES_texture_float_linear")===!1)return;if(S.anisotropy>1||n.get(S).__currentAnisotropy){let H=t.get("EXT_texture_filter_anisotropic");i.texParameterf(R,H.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(S.anisotropy,s.getMaxAnisotropy())),n.get(S).__currentAnisotropy=S.anisotropy}}}function ft(R,S){let H=!1;R.__webglInit===void 0&&(R.__webglInit=!0,S.addEventListener("dispose",A));let Y=S.source,rt=f.get(Y);rt===void 0&&(rt={},f.set(Y,rt));let _t=j(S);if(_t!==R.__cacheKey){rt[_t]===void 0&&(rt[_t]={texture:i.createTexture(),usedTimes:0},a.memory.textures++,H=!0),rt[_t].usedTimes++;let Et=rt[R.__cacheKey];Et!==void 0&&(rt[R.__cacheKey].usedTimes--,Et.usedTimes===0&&P(S)),R.__cacheKey=_t,R.__webglTexture=rt[_t].texture}return H}function N(R,S,H){return Math.floor(Math.floor(R/H)/S)}function k(R,S,H,Y){let _t=R.updateRanges;if(_t.length===0)e.texSubImage2D(i.TEXTURE_2D,0,0,0,S.width,S.height,H,Y,S.data);else{_t.sort((Zt,It)=>Zt.start-It.start);let Et=0;for(let Zt=1;Zt<_t.length;Zt++){let It=_t[Et],Lt=_t[Zt],$t=It.start+It.count,ee=N(Lt.start,S.width,4),ce=N(It.start,S.width,4);Lt.start<=$t+1&&ee===ce&&N(Lt.start+Lt.count-1,S.width,4)===ee?It.count=Math.max(It.count,Lt.start+Lt.count-It.start):(++Et,_t[Et]=Lt)}_t.length=Et+1;let nt=e.getParameter(i.UNPACK_ROW_LENGTH),ut=e.getParameter(i.UNPACK_SKIP_PIXELS),At=e.getParameter(i.UNPACK_SKIP_ROWS);e.pixelStorei(i.UNPACK_ROW_LENGTH,S.width);for(let Zt=0,It=_t.length;Zt<It;Zt++){let Lt=_t[Zt],$t=Math.floor(Lt.start/4),ee=Math.ceil(Lt.count/4),ce=$t%S.width,B=Math.floor($t/S.width),Ct=ee,lt=1;e.pixelStorei(i.UNPACK_SKIP_PIXELS,ce),e.pixelStorei(i.UNPACK_SKIP_ROWS,B),e.texSubImage2D(i.TEXTURE_2D,0,ce,B,Ct,lt,H,Y,S.data)}R.clearUpdateRanges(),e.pixelStorei(i.UNPACK_ROW_LENGTH,nt),e.pixelStorei(i.UNPACK_SKIP_PIXELS,ut),e.pixelStorei(i.UNPACK_SKIP_ROWS,At)}}function dt(R,S,H){let Y=i.TEXTURE_2D;(S.isDataArrayTexture||S.isCompressedArrayTexture)&&(Y=i.TEXTURE_2D_ARRAY),S.isData3DTexture&&(Y=i.TEXTURE_3D);let rt=ft(R,S),_t=S.source;e.bindTexture(Y,R.__webglTexture,i.TEXTURE0+H);let Et=n.get(_t);if(_t.version!==Et.__version||rt===!0){if(e.activeTexture(i.TEXTURE0+H),(typeof ImageBitmap<"u"&&S.image instanceof ImageBitmap)===!1){let lt=Me.getPrimaries(Me.workingColorSpace),Pt=S.colorSpace===ki?null:Me.getPrimaries(S.colorSpace),yt=S.colorSpace===ki||lt===Pt?i.NONE:i.BROWSER_DEFAULT_WEBGL;e.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,S.flipY),e.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,S.premultiplyAlpha),e.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,yt)}e.pixelStorei(i.UNPACK_ALIGNMENT,S.unpackAlignment);let ut=p(S.image,!1,s.maxTextureSize);ut=Ee(S,ut);let At=r.convert(S.format,S.colorSpace),Zt=r.convert(S.type),It=v(S.internalFormat,At,Zt,S.normalized,S.colorSpace,S.isVideoTexture);Dt(Y,S);let Lt,$t=S.mipmaps,ee=S.isVideoTexture!==!0,ce=Et.__version===void 0||rt===!0,B=_t.dataReady,Ct=M(S,ut);if(S.isDepthTexture)It=b(S.format===ls,S.type),ce&&(ee?e.texStorage2D(i.TEXTURE_2D,1,It,ut.width,ut.height):e.texImage2D(i.TEXTURE_2D,0,It,ut.width,ut.height,0,At,Zt,null));else if(S.isDataTexture)if($t.length>0){ee&&ce&&e.texStorage2D(i.TEXTURE_2D,Ct,It,$t[0].width,$t[0].height);for(let lt=0,Pt=$t.length;lt<Pt;lt++)Lt=$t[lt],ee?B&&e.texSubImage2D(i.TEXTURE_2D,lt,0,0,Lt.width,Lt.height,At,Zt,Lt.data):e.texImage2D(i.TEXTURE_2D,lt,It,Lt.width,Lt.height,0,At,Zt,Lt.data);S.generateMipmaps=!1}else ee?(ce&&e.texStorage2D(i.TEXTURE_2D,Ct,It,ut.width,ut.height),B&&k(S,ut,At,Zt)):e.texImage2D(i.TEXTURE_2D,0,It,ut.width,ut.height,0,At,Zt,ut.data);else if(S.isCompressedTexture)if(S.isCompressedArrayTexture){ee&&ce&&e.texStorage3D(i.TEXTURE_2D_ARRAY,Ct,It,$t[0].width,$t[0].height,ut.depth);for(let lt=0,Pt=$t.length;lt<Pt;lt++)if(Lt=$t[lt],S.format!==Yn)if(At!==null)if(ee){if(B)if(S.layerUpdates.size>0){let yt=ah(Lt.width,Lt.height,S.format,S.type);for(let pt of S.layerUpdates){let Xt=Lt.data.subarray(pt*yt/Lt.data.BYTES_PER_ELEMENT,(pt+1)*yt/Lt.data.BYTES_PER_ELEMENT);e.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,lt,0,0,pt,Lt.width,Lt.height,1,At,Xt)}}else e.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,lt,0,0,0,Lt.width,Lt.height,ut.depth,At,Lt.data)}else e.compressedTexImage3D(i.TEXTURE_2D_ARRAY,lt,It,Lt.width,Lt.height,ut.depth,0,Lt.data,0,0);else ie("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else ee?B&&e.texSubImage3D(i.TEXTURE_2D_ARRAY,lt,0,0,0,Lt.width,Lt.height,ut.depth,At,Zt,Lt.data):e.texImage3D(i.TEXTURE_2D_ARRAY,lt,It,Lt.width,Lt.height,ut.depth,0,At,Zt,Lt.data);S.layerUpdates.size>0&&S.clearLayerUpdates()}else{ee&&ce&&e.texStorage2D(i.TEXTURE_2D,Ct,It,$t[0].width,$t[0].height);for(let lt=0,Pt=$t.length;lt<Pt;lt++)Lt=$t[lt],S.format!==Yn?At!==null?ee?B&&e.compressedTexSubImage2D(i.TEXTURE_2D,lt,0,0,Lt.width,Lt.height,At,Lt.data):e.compressedTexImage2D(i.TEXTURE_2D,lt,It,Lt.width,Lt.height,0,Lt.data):ie("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):ee?B&&e.texSubImage2D(i.TEXTURE_2D,lt,0,0,Lt.width,Lt.height,At,Zt,Lt.data):e.texImage2D(i.TEXTURE_2D,lt,It,Lt.width,Lt.height,0,At,Zt,Lt.data)}else if(S.isDataArrayTexture)if(ee){if(ce&&e.texStorage3D(i.TEXTURE_2D_ARRAY,Ct,It,ut.width,ut.height,ut.depth),B)if(S.layerUpdates.size>0){let lt=ah(ut.width,ut.height,S.format,S.type);for(let Pt of S.layerUpdates){let yt=ut.data.subarray(Pt*lt/ut.data.BYTES_PER_ELEMENT,(Pt+1)*lt/ut.data.BYTES_PER_ELEMENT);e.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,Pt,ut.width,ut.height,1,At,Zt,yt)}S.clearLayerUpdates()}else e.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,0,ut.width,ut.height,ut.depth,At,Zt,ut.data)}else e.texImage3D(i.TEXTURE_2D_ARRAY,0,It,ut.width,ut.height,ut.depth,0,At,Zt,ut.data);else if(S.isData3DTexture)ee?(ce&&e.texStorage3D(i.TEXTURE_3D,Ct,It,ut.width,ut.height,ut.depth),B&&e.texSubImage3D(i.TEXTURE_3D,0,0,0,0,ut.width,ut.height,ut.depth,At,Zt,ut.data)):e.texImage3D(i.TEXTURE_3D,0,It,ut.width,ut.height,ut.depth,0,At,Zt,ut.data);else if(S.isFramebufferTexture){if(ce)if(ee)e.texStorage2D(i.TEXTURE_2D,Ct,It,ut.width,ut.height);else{let lt=ut.width,Pt=ut.height;for(let yt=0;yt<Ct;yt++)e.texImage2D(i.TEXTURE_2D,yt,It,lt,Pt,0,At,Zt,null),lt>>=1,Pt>>=1}}else if(S.isHTMLTexture){if("texElementImage2D"in i){let lt=i.canvas;if(lt.hasAttribute("layoutsubtree")||lt.setAttribute("layoutsubtree","true"),ut.parentNode!==lt){lt.appendChild(ut),d.add(S),lt.onpaint=Pt=>{let yt=Pt.changedElements;for(let pt of d)yt.includes(pt.image)&&(pt.needsUpdate=!0)},lt.requestPaint();return}if(i.texElementImage2D.length===3)i.texElementImage2D(i.TEXTURE_2D,i.RGBA8,ut);else{let yt=i.RGBA,pt=i.RGBA,Xt=i.UNSIGNED_BYTE;i.texElementImage2D(i.TEXTURE_2D,0,yt,pt,Xt,ut)}i.texParameteri(i.TEXTURE_2D,i.TEXTURE_MIN_FILTER,i.LINEAR),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_S,i.CLAMP_TO_EDGE),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_T,i.CLAMP_TO_EDGE)}}else if($t.length>0){if(ee&&ce){let lt=se($t[0]);e.texStorage2D(i.TEXTURE_2D,Ct,It,lt.width,lt.height)}for(let lt=0,Pt=$t.length;lt<Pt;lt++)Lt=$t[lt],ee?B&&e.texSubImage2D(i.TEXTURE_2D,lt,0,0,At,Zt,Lt):e.texImage2D(i.TEXTURE_2D,lt,It,At,Zt,Lt);S.generateMipmaps=!1}else if(ee){if(ce){let lt=se(ut);e.texStorage2D(i.TEXTURE_2D,Ct,It,lt.width,lt.height)}B&&e.texSubImage2D(i.TEXTURE_2D,0,0,0,At,Zt,ut)}else e.texImage2D(i.TEXTURE_2D,0,It,At,Zt,ut);m(S)&&y(Y),Et.__version=_t.version,S.onUpdate&&S.onUpdate(S)}R.__version=S.version}function St(R,S,H){if(S.image.length!==6)return;let Y=ft(R,S),rt=S.source;e.bindTexture(i.TEXTURE_CUBE_MAP,R.__webglTexture,i.TEXTURE0+H);let _t=n.get(rt);if(rt.version!==_t.__version||Y===!0){e.activeTexture(i.TEXTURE0+H);let Et=Me.getPrimaries(Me.workingColorSpace),nt=S.colorSpace===ki?null:Me.getPrimaries(S.colorSpace),ut=S.colorSpace===ki||Et===nt?i.NONE:i.BROWSER_DEFAULT_WEBGL;e.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,S.flipY),e.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,S.premultiplyAlpha),e.pixelStorei(i.UNPACK_ALIGNMENT,S.unpackAlignment),e.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,ut);let At=S.isCompressedTexture||S.image[0].isCompressedTexture,Zt=S.image[0]&&S.image[0].isDataTexture,It=[];for(let pt=0;pt<6;pt++)!At&&!Zt?It[pt]=p(S.image[pt],!0,s.maxCubemapSize):It[pt]=Zt?S.image[pt].image:S.image[pt],It[pt]=Ee(S,It[pt]);let Lt=It[0],$t=r.convert(S.format,S.colorSpace),ee=r.convert(S.type),ce=v(S.internalFormat,$t,ee,S.normalized,S.colorSpace),B=S.isVideoTexture!==!0,Ct=_t.__version===void 0||Y===!0,lt=rt.dataReady,Pt=M(S,Lt);Dt(i.TEXTURE_CUBE_MAP,S);let yt;if(At){B&&Ct&&e.texStorage2D(i.TEXTURE_CUBE_MAP,Pt,ce,Lt.width,Lt.height);for(let pt=0;pt<6;pt++){yt=It[pt].mipmaps;for(let Xt=0;Xt<yt.length;Xt++){let Ht=yt[Xt];S.format!==Yn?$t!==null?B?lt&&e.compressedTexSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,Xt,0,0,Ht.width,Ht.height,$t,Ht.data):e.compressedTexImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,Xt,ce,Ht.width,Ht.height,0,Ht.data):ie("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):B?lt&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,Xt,0,0,Ht.width,Ht.height,$t,ee,Ht.data):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,Xt,ce,Ht.width,Ht.height,0,$t,ee,Ht.data)}}}else{if(yt=S.mipmaps,B&&Ct){yt.length>0&&Pt++;let pt=se(It[0]);e.texStorage2D(i.TEXTURE_CUBE_MAP,Pt,ce,pt.width,pt.height)}for(let pt=0;pt<6;pt++)if(Zt){B?lt&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,0,0,0,It[pt].width,It[pt].height,$t,ee,It[pt].data):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,0,ce,It[pt].width,It[pt].height,0,$t,ee,It[pt].data);for(let Xt=0;Xt<yt.length;Xt++){let we=yt[Xt].image[pt].image;B?lt&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,Xt+1,0,0,we.width,we.height,$t,ee,we.data):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,Xt+1,ce,we.width,we.height,0,$t,ee,we.data)}}else{B?lt&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,0,0,0,$t,ee,It[pt]):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,0,ce,$t,ee,It[pt]);for(let Xt=0;Xt<yt.length;Xt++){let Ht=yt[Xt];B?lt&&e.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,Xt+1,0,0,$t,ee,Ht.image[pt]):e.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pt,Xt+1,ce,$t,ee,Ht.image[pt])}}}m(S)&&y(i.TEXTURE_CUBE_MAP),_t.__version=rt.version,S.onUpdate&&S.onUpdate(S)}R.__version=S.version}function Mt(R,S,H,Y,rt,_t){let Et=r.convert(H.format,H.colorSpace),nt=r.convert(H.type),ut=v(H.internalFormat,Et,nt,H.normalized,H.colorSpace),At=n.get(S),Zt=n.get(H);if(Zt.__renderTarget=S,!At.__hasExternalTextures){let It=Math.max(1,S.width>>_t),Lt=Math.max(1,S.height>>_t);rt===i.TEXTURE_3D||rt===i.TEXTURE_2D_ARRAY?e.texImage3D(rt,_t,ut,It,Lt,S.depth,0,Et,nt,null):e.texImage2D(rt,_t,ut,It,Lt,0,Et,nt,null)}e.bindFramebuffer(i.FRAMEBUFFER,R),ne(S)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,Y,rt,Zt.__webglTexture,0,jt(S)):(rt===i.TEXTURE_2D||rt>=i.TEXTURE_CUBE_MAP_POSITIVE_X&&rt<=i.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&i.framebufferTexture2D(i.FRAMEBUFFER,Y,rt,Zt.__webglTexture,_t),e.bindFramebuffer(i.FRAMEBUFFER,null)}function Ft(R,S,H){if(i.bindRenderbuffer(i.RENDERBUFFER,R),S.depthBuffer){let Y=S.depthTexture,rt=Y&&Y.isDepthTexture?Y.type:null,_t=b(S.stencilBuffer,rt),Et=S.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;ne(S)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,jt(S),_t,S.width,S.height):H?i.renderbufferStorageMultisample(i.RENDERBUFFER,jt(S),_t,S.width,S.height):i.renderbufferStorage(i.RENDERBUFFER,_t,S.width,S.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,Et,i.RENDERBUFFER,R)}else{let Y=S.textures;for(let rt=0;rt<Y.length;rt++){let _t=Y[rt],Et=r.convert(_t.format,_t.colorSpace),nt=r.convert(_t.type),ut=v(_t.internalFormat,Et,nt,_t.normalized,_t.colorSpace);ne(S)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,jt(S),ut,S.width,S.height):H?i.renderbufferStorageMultisample(i.RENDERBUFFER,jt(S),ut,S.width,S.height):i.renderbufferStorage(i.RENDERBUFFER,ut,S.width,S.height)}}i.bindRenderbuffer(i.RENDERBUFFER,null)}function xt(R,S,H){let Y=S.isWebGLCubeRenderTarget===!0;if(e.bindFramebuffer(i.FRAMEBUFFER,R),!(S.depthTexture&&S.depthTexture.isDepthTexture))throw new Error("THREE.WebGLTextures: renderTarget.depthTexture must be an instance of THREE.DepthTexture.");let rt=n.get(S.depthTexture);if(rt.__renderTarget=S,(!rt.__webglTexture||S.depthTexture.image.width!==S.width||S.depthTexture.image.height!==S.height)&&(S.depthTexture.image.width=S.width,S.depthTexture.image.height=S.height,S.depthTexture.needsUpdate=!0),Y){if(rt.__webglInit===void 0&&(rt.__webglInit=!0,S.depthTexture.addEventListener("dispose",A)),rt.__webglTexture===void 0){rt.__webglTexture=i.createTexture(),e.bindTexture(i.TEXTURE_CUBE_MAP,rt.__webglTexture),Dt(i.TEXTURE_CUBE_MAP,S.depthTexture);let At=r.convert(S.depthTexture.format),Zt=r.convert(S.depthTexture.type),It;S.depthTexture.format===pi?It=i.DEPTH_COMPONENT24:S.depthTexture.format===ls&&(It=i.DEPTH24_STENCIL8);for(let Lt=0;Lt<6;Lt++)i.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Lt,0,It,S.width,S.height,0,At,Zt,null)}}else at(S.depthTexture,0);let _t=rt.__webglTexture,Et=jt(S),nt=Y?i.TEXTURE_CUBE_MAP_POSITIVE_X+H:i.TEXTURE_2D,ut=S.depthTexture.format===ls?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;if(S.depthTexture.format===pi)ne(S)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,ut,nt,_t,0,Et):i.framebufferTexture2D(i.FRAMEBUFFER,ut,nt,_t,0);else if(S.depthTexture.format===ls)ne(S)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,ut,nt,_t,0,Et):i.framebufferTexture2D(i.FRAMEBUFFER,ut,nt,_t,0);else throw new Error("THREE.WebGLTextures: Unknown depthTexture format.")}function X(R){let S=n.get(R),H=R.isWebGLCubeRenderTarget===!0;if(S.__boundDepthTexture!==R.depthTexture){let Y=R.depthTexture;if(S.__depthDisposeCallback&&S.__depthDisposeCallback(),Y){let rt=()=>{delete S.__boundDepthTexture,delete S.__depthDisposeCallback,Y.removeEventListener("dispose",rt)};Y.addEventListener("dispose",rt),S.__depthDisposeCallback=rt}S.__boundDepthTexture=Y}if(R.depthTexture&&!S.__autoAllocateDepthBuffer)if(H)for(let Y=0;Y<6;Y++)xt(S.__webglFramebuffer[Y],R,Y);else{let Y=R.texture.mipmaps;Y&&Y.length>0?xt(S.__webglFramebuffer[0],R,0):xt(S.__webglFramebuffer,R,0)}else if(H){S.__webglDepthbuffer=[];for(let Y=0;Y<6;Y++)if(e.bindFramebuffer(i.FRAMEBUFFER,S.__webglFramebuffer[Y]),S.__webglDepthbuffer[Y]===void 0)S.__webglDepthbuffer[Y]=i.createRenderbuffer(),Ft(S.__webglDepthbuffer[Y],R,!1);else{let rt=R.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,_t=S.__webglDepthbuffer[Y];i.bindRenderbuffer(i.RENDERBUFFER,_t),i.framebufferRenderbuffer(i.FRAMEBUFFER,rt,i.RENDERBUFFER,_t)}}else{let Y=R.texture.mipmaps;if(Y&&Y.length>0?e.bindFramebuffer(i.FRAMEBUFFER,S.__webglFramebuffer[0]):e.bindFramebuffer(i.FRAMEBUFFER,S.__webglFramebuffer),S.__webglDepthbuffer===void 0)S.__webglDepthbuffer=i.createRenderbuffer(),Ft(S.__webglDepthbuffer,R,!1);else{let rt=R.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,_t=S.__webglDepthbuffer;i.bindRenderbuffer(i.RENDERBUFFER,_t),i.framebufferRenderbuffer(i.FRAMEBUFFER,rt,i.RENDERBUFFER,_t)}}e.bindFramebuffer(i.FRAMEBUFFER,null)}function tt(R,S,H){let Y=n.get(R);S!==void 0&&Mt(Y.__webglFramebuffer,R,R.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,0),H!==void 0&&X(R)}function G(R){let S=R.texture,H=n.get(R),Y=n.get(S);R.addEventListener("dispose",_);let rt=R.textures,_t=R.isWebGLCubeRenderTarget===!0,Et=rt.length>1;if(Et||(Y.__webglTexture===void 0&&(Y.__webglTexture=i.createTexture()),Y.__version=S.version,a.memory.textures++),_t){H.__webglFramebuffer=[];for(let nt=0;nt<6;nt++)if(S.mipmaps&&S.mipmaps.length>0){H.__webglFramebuffer[nt]=[];for(let ut=0;ut<S.mipmaps.length;ut++)H.__webglFramebuffer[nt][ut]=i.createFramebuffer()}else H.__webglFramebuffer[nt]=i.createFramebuffer()}else{if(S.mipmaps&&S.mipmaps.length>0){H.__webglFramebuffer=[];for(let nt=0;nt<S.mipmaps.length;nt++)H.__webglFramebuffer[nt]=i.createFramebuffer()}else H.__webglFramebuffer=i.createFramebuffer();if(Et)for(let nt=0,ut=rt.length;nt<ut;nt++){let At=n.get(rt[nt]);At.__webglTexture===void 0&&(At.__webglTexture=i.createTexture(),a.memory.textures++)}if(R.samples>0&&ne(R)===!1){H.__webglMultisampledFramebuffer=i.createFramebuffer(),H.__webglColorRenderbuffer=[],e.bindFramebuffer(i.FRAMEBUFFER,H.__webglMultisampledFramebuffer);for(let nt=0;nt<rt.length;nt++){let ut=rt[nt];H.__webglColorRenderbuffer[nt]=i.createRenderbuffer(),i.bindRenderbuffer(i.RENDERBUFFER,H.__webglColorRenderbuffer[nt]);let At=r.convert(ut.format,ut.colorSpace),Zt=r.convert(ut.type),It=v(ut.internalFormat,At,Zt,ut.normalized,ut.colorSpace,R.isXRRenderTarget===!0),Lt=jt(R);i.renderbufferStorageMultisample(i.RENDERBUFFER,Lt,It,R.width,R.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+nt,i.RENDERBUFFER,H.__webglColorRenderbuffer[nt])}i.bindRenderbuffer(i.RENDERBUFFER,null),R.depthBuffer&&(H.__webglDepthRenderbuffer=i.createRenderbuffer(),Ft(H.__webglDepthRenderbuffer,R,!0)),e.bindFramebuffer(i.FRAMEBUFFER,null)}}if(_t){e.bindTexture(i.TEXTURE_CUBE_MAP,Y.__webglTexture),Dt(i.TEXTURE_CUBE_MAP,S);for(let nt=0;nt<6;nt++)if(S.mipmaps&&S.mipmaps.length>0)for(let ut=0;ut<S.mipmaps.length;ut++)Mt(H.__webglFramebuffer[nt][ut],R,S,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+nt,ut);else Mt(H.__webglFramebuffer[nt],R,S,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+nt,0);m(S)&&y(i.TEXTURE_CUBE_MAP),e.unbindTexture()}else if(Et){for(let nt=0,ut=rt.length;nt<ut;nt++){let At=rt[nt],Zt=n.get(At),It=i.TEXTURE_2D;(R.isWebGL3DRenderTarget||R.isWebGLArrayRenderTarget)&&(It=R.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),e.bindTexture(It,Zt.__webglTexture),Dt(It,At),Mt(H.__webglFramebuffer,R,At,i.COLOR_ATTACHMENT0+nt,It,0),m(At)&&y(It)}e.unbindTexture()}else{let nt=i.TEXTURE_2D;if((R.isWebGL3DRenderTarget||R.isWebGLArrayRenderTarget)&&(nt=R.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),e.bindTexture(nt,Y.__webglTexture),Dt(nt,S),S.mipmaps&&S.mipmaps.length>0)for(let ut=0;ut<S.mipmaps.length;ut++)Mt(H.__webglFramebuffer[ut],R,S,i.COLOR_ATTACHMENT0,nt,ut);else Mt(H.__webglFramebuffer,R,S,i.COLOR_ATTACHMENT0,nt,0);m(S)&&y(nt),e.unbindTexture()}R.depthBuffer&&X(R)}function et(R){let S=R.textures;for(let H=0,Y=S.length;H<Y;H++){let rt=S[H];if(m(rt)){let _t=E(R),Et=n.get(rt).__webglTexture;e.bindTexture(_t,Et),y(_t),e.unbindTexture()}}}let gt=[],Bt=[];function bt(R){if(R.samples>0){if(ne(R)===!1){let S=R.textures,H=R.width,Y=R.height,rt=i.COLOR_BUFFER_BIT,_t=R.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,Et=n.get(R),nt=S.length>1;if(nt)for(let At=0;At<S.length;At++)e.bindFramebuffer(i.FRAMEBUFFER,Et.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+At,i.RENDERBUFFER,null),e.bindFramebuffer(i.FRAMEBUFFER,Et.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+At,i.TEXTURE_2D,null,0);e.bindFramebuffer(i.READ_FRAMEBUFFER,Et.__webglMultisampledFramebuffer);let ut=R.texture.mipmaps;ut&&ut.length>0?e.bindFramebuffer(i.DRAW_FRAMEBUFFER,Et.__webglFramebuffer[0]):e.bindFramebuffer(i.DRAW_FRAMEBUFFER,Et.__webglFramebuffer);for(let At=0;At<S.length;At++){if(R.resolveDepthBuffer&&(R.depthBuffer&&(rt|=i.DEPTH_BUFFER_BIT),R.stencilBuffer&&R.resolveStencilBuffer&&(rt|=i.STENCIL_BUFFER_BIT)),nt){i.framebufferRenderbuffer(i.READ_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.RENDERBUFFER,Et.__webglColorRenderbuffer[At]);let Zt=n.get(S[At]).__webglTexture;i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,Zt,0)}i.blitFramebuffer(0,0,H,Y,0,0,H,Y,rt,i.NEAREST),c===!0&&(gt.length=0,Bt.length=0,gt.push(i.COLOR_ATTACHMENT0+At),R.depthBuffer&&R.storeMultisampledDepthBuffer===!1&&(gt.push(_t),Bt.push(_t),i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,Bt)),i.invalidateFramebuffer(i.READ_FRAMEBUFFER,gt))}if(e.bindFramebuffer(i.READ_FRAMEBUFFER,null),e.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),nt)for(let At=0;At<S.length;At++){e.bindFramebuffer(i.FRAMEBUFFER,Et.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+At,i.RENDERBUFFER,Et.__webglColorRenderbuffer[At]);let Zt=n.get(S[At]).__webglTexture;e.bindFramebuffer(i.FRAMEBUFFER,Et.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+At,i.TEXTURE_2D,Zt,0)}e.bindFramebuffer(i.DRAW_FRAMEBUFFER,Et.__webglMultisampledFramebuffer)}else if(R.depthBuffer&&R.storeMultisampledDepthBuffer===!1&&c){let S=R.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,[S])}}}function jt(R){return Math.min(s.maxSamples,R.samples)}function ne(R){let S=n.get(R);return R.samples>0&&t.has("WEBGL_multisampled_render_to_texture")===!0&&S.__useRenderToTexture!==!1}function U(R){let S=a.render.frame;u.get(R)!==S&&(u.set(R,S),R.update())}function Ee(R,S){let H=R.colorSpace,Y=R.format,rt=R.type;return R.isCompressedTexture===!0||R.isVideoTexture===!0||H!==Nr&&H!==ki&&(Me.getTransfer(H)===Ie?(Y!==Yn||rt!==Ln)&&ie("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):ae("WebGLTextures: Unsupported texture color space:",H)),S}function se(R){return typeof HTMLImageElement<"u"&&R instanceof HTMLImageElement?(l.width=R.naturalWidth||R.width,l.height=R.naturalHeight||R.height):typeof VideoFrame<"u"&&R instanceof VideoFrame?(l.width=R.displayWidth,l.height=R.displayHeight):(l.width=R.width,l.height=R.height),l}this.allocateTextureUnit=q,this.resetTextureUnits=V,this.getTextureUnits=I,this.setTextureUnits=z,this.setTexture2D=at,this.setTexture2DArray=K,this.setTexture3D=st,this.setTextureCube=it,this.rebindTextures=tt,this.setupRenderTarget=G,this.updateRenderTargetMipmap=et,this.updateMultisampleRenderTarget=bt,this.setupDepthRenderbuffer=X,this.setupFrameBufferTexture=Mt,this.useMultisampledRTT=ne,this.isReversedDepthBuffer=function(){return e.buffers.depth.getReversed()}}function Ux(i,t){function e(n,s=ki){let r,a=Me.getTransfer(s);if(n===Ln)return i.UNSIGNED_BYTE;if(n===Yo)return i.UNSIGNED_SHORT_4_4_4_4;if(n===jo)return i.UNSIGNED_SHORT_5_5_5_1;if(n===Zl)return i.UNSIGNED_INT_5_9_9_9_REV;if(n===$l)return i.UNSIGNED_INT_10F_11F_11F_REV;if(n===Yl)return i.BYTE;if(n===jl)return i.SHORT;if(n===dr)return i.UNSIGNED_SHORT;if(n===qo)return i.INT;if(n===li)return i.UNSIGNED_INT;if(n===qn)return i.FLOAT;if(n===Bn)return i.HALF_FLOAT;if(n===Jl)return i.ALPHA;if(n===Kl)return i.RGB;if(n===Yn)return i.RGBA;if(n===pi)return i.DEPTH_COMPONENT;if(n===ls)return i.DEPTH_STENCIL;if(n===Zo)return i.RED;if(n===$o)return i.RED_INTEGER;if(n===yi)return i.RG;if(n===Jo)return i.RG_INTEGER;if(n===Ko)return i.RGBA_INTEGER;if(n===va||n===xa||n===_a||n===ya)if(a===Ie)if(r=t.get("WEBGL_compressed_texture_s3tc_srgb"),r!==null){if(n===va)return r.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(n===xa)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(n===_a)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(n===ya)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(r=t.get("WEBGL_compressed_texture_s3tc"),r!==null){if(n===va)return r.COMPRESSED_RGB_S3TC_DXT1_EXT;if(n===xa)return r.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(n===_a)return r.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(n===ya)return r.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(n===Qo||n===tc||n===ec||n===nc)if(r=t.get("WEBGL_compressed_texture_pvrtc"),r!==null){if(n===Qo)return r.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(n===tc)return r.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(n===ec)return r.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(n===nc)return r.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(n===ic||n===sc||n===rc||n===ac||n===oc||n===Ma||n===cc)if(r=t.get("WEBGL_compressed_texture_etc"),r!==null){if(n===ic||n===sc)return a===Ie?r.COMPRESSED_SRGB8_ETC2:r.COMPRESSED_RGB8_ETC2;if(n===rc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:r.COMPRESSED_RGBA8_ETC2_EAC;if(n===ac)return r.COMPRESSED_R11_EAC;if(n===oc)return r.COMPRESSED_SIGNED_R11_EAC;if(n===Ma)return r.COMPRESSED_RG11_EAC;if(n===cc)return r.COMPRESSED_SIGNED_RG11_EAC}else return null;if(n===lc||n===hc||n===uc||n===dc||n===fc||n===pc||n===mc||n===gc||n===vc||n===xc||n===_c||n===yc||n===Mc||n===Sc)if(r=t.get("WEBGL_compressed_texture_astc"),r!==null){if(n===lc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:r.COMPRESSED_RGBA_ASTC_4x4_KHR;if(n===hc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:r.COMPRESSED_RGBA_ASTC_5x4_KHR;if(n===uc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:r.COMPRESSED_RGBA_ASTC_5x5_KHR;if(n===dc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:r.COMPRESSED_RGBA_ASTC_6x5_KHR;if(n===fc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:r.COMPRESSED_RGBA_ASTC_6x6_KHR;if(n===pc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:r.COMPRESSED_RGBA_ASTC_8x5_KHR;if(n===mc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:r.COMPRESSED_RGBA_ASTC_8x6_KHR;if(n===gc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:r.COMPRESSED_RGBA_ASTC_8x8_KHR;if(n===vc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:r.COMPRESSED_RGBA_ASTC_10x5_KHR;if(n===xc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:r.COMPRESSED_RGBA_ASTC_10x6_KHR;if(n===_c)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:r.COMPRESSED_RGBA_ASTC_10x8_KHR;if(n===yc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:r.COMPRESSED_RGBA_ASTC_10x10_KHR;if(n===Mc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:r.COMPRESSED_RGBA_ASTC_12x10_KHR;if(n===Sc)return a===Ie?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:r.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(n===bc||n===Ec||n===wc)if(r=t.get("EXT_texture_compression_bptc"),r!==null){if(n===bc)return a===Ie?r.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:r.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(n===Ec)return r.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(n===wc)return r.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(n===Tc||n===Ac||n===Sa||n===Rc)if(r=t.get("EXT_texture_compression_rgtc"),r!==null){if(n===Tc)return r.COMPRESSED_RED_RGTC1_EXT;if(n===Ac)return r.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(n===Sa)return r.COMPRESSED_RED_GREEN_RGTC2_EXT;if(n===Rc)return r.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return n===fr?i.UNSIGNED_INT_24_8:i[n]!==void 0?i[n]:null}return{convert:e}}var Nx=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,Fx=`
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

}`,wh=class{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(t,e){if(this.texture===null){let n=new Zr(t.texture);(t.depthNear!==e.depthNear||t.depthFar!==e.depthFar)&&(this.depthNear=t.depthNear,this.depthFar=t.depthFar),this.texture=n}}getMesh(t){if(this.texture!==null&&this.mesh===null){let e=t.cameras[0].viewport,n=new Oe({vertexShader:Nx,fragmentShader:Fx,uniforms:{depthColor:{value:this.texture},depthWidth:{value:e.z},depthHeight:{value:e.w}}});this.mesh=new ct(new je(20,20),n)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}},Th=class extends mi{constructor(t,e){super();let n=this,s=null,r=1,a=null,o="local-floor",c=1,l=null,u=null,d=null,h=null,f=null,g=null,x=typeof XRWebGLBinding<"u",p=new wh,m={},y=e.getContextAttributes(),E=null,v=null,b=[],M=[],A=new vt,_=null,T=null,P=new Je;P.viewport=new xe;let L=new Je;L.viewport=new xe;let F=[P,L],V=new Ho,I=null,z=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(N){let k=b[N];return k===void 0&&(k=new nr,b[N]=k),k.getTargetRaySpace()},this.getControllerGrip=function(N){let k=b[N];return k===void 0&&(k=new nr,b[N]=k),k.getGripSpace()},this.getHand=function(N){let k=b[N];return k===void 0&&(k=new nr,b[N]=k),k.getHandSpace()};function q(N){let k=M.indexOf(N.inputSource);if(k===-1)return;let dt=b[k];dt!==void 0&&(dt.update(N.inputSource,N.frame,l||a),dt.dispatchEvent({type:N.type,data:N.inputSource}))}function j(){s.removeEventListener("select",q),s.removeEventListener("selectstart",q),s.removeEventListener("selectend",q),s.removeEventListener("squeeze",q),s.removeEventListener("squeezestart",q),s.removeEventListener("squeezeend",q),s.removeEventListener("end",j),s.removeEventListener("inputsourceschange",at);for(let N=0;N<b.length;N++){let k=M[N];k!==null&&(M[N]=null,b[N].disconnect(k))}I=null,z=null,p.reset();for(let N in m)delete m[N];if(t.setRenderTarget(E),f=null,h=null,d=null,s=null,v=null,ft.stop(),n.isPresenting=!1,t.setPixelRatio(_),t.setSize(A.width,A.height,!1),T!==null){let N=T.camera;N.fov=T.fov,N.zoom=T.zoom,N.updateProjectionMatrix(),T=null}n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(N){r=N,n.isPresenting===!0&&ie("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(N){o=N,n.isPresenting===!0&&ie("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return l||a},this.setReferenceSpace=function(N){l=N},this.getBaseLayer=function(){return h!==null?h:f},this.getBinding=function(){return d===null&&x&&(d=new XRWebGLBinding(s,e)),d},this.getFrame=function(){return g},this.getSession=function(){return s},this.setSession=async function(N){if(s=N,s!==null){if(E=t.getRenderTarget(),s.addEventListener("select",q),s.addEventListener("selectstart",q),s.addEventListener("selectend",q),s.addEventListener("squeeze",q),s.addEventListener("squeezestart",q),s.addEventListener("squeezeend",q),s.addEventListener("end",j),s.addEventListener("inputsourceschange",at),y.xrCompatible!==!0&&await e.makeXRCompatible(),_=t.getPixelRatio(),t.getSize(A),x&&"createProjectionLayer"in XRWebGLBinding.prototype){let dt=null,St=null,Mt=null;y.depth&&(Mt=y.stencil?e.DEPTH24_STENCIL8:e.DEPTH_COMPONENT24,dt=y.stencil?ls:pi,St=y.stencil?fr:li);let Ft={colorFormat:e.RGBA8,depthFormat:Mt,scaleFactor:r};d=this.getBinding(),h=d.createProjectionLayer(Ft),s.updateRenderState({layers:[h]}),t.setPixelRatio(1),t.setSize(h.textureWidth,h.textureHeight,!1),v=new In(h.textureWidth,h.textureHeight,{format:Yn,type:Ln,depthTexture:new Ji(h.textureWidth,h.textureHeight,St,void 0,void 0,void 0,void 0,void 0,void 0,dt),stencilBuffer:y.stencil,colorSpace:t.outputColorSpace,samples:y.antialias?4:0,resolveDepthBuffer:h.ignoreDepthValues===!1,resolveStencilBuffer:h.ignoreDepthValues===!1,storeMultisampledDepthBuffer:h.ignoreDepthValues===!1,storeMultisampledStencilBuffer:h.ignoreDepthValues===!1})}else{let dt={antialias:y.antialias,alpha:!0,depth:y.depth,stencil:y.stencil,framebufferScaleFactor:r};f=new XRWebGLLayer(s,e,dt),s.updateRenderState({baseLayer:f}),t.setPixelRatio(1),t.setSize(f.framebufferWidth,f.framebufferHeight,!1),v=new In(f.framebufferWidth,f.framebufferHeight,{format:Yn,type:Ln,colorSpace:t.outputColorSpace,stencilBuffer:y.stencil,resolveDepthBuffer:f.ignoreDepthValues===!1,resolveStencilBuffer:f.ignoreDepthValues===!1,storeMultisampledDepthBuffer:f.ignoreDepthValues===!1,storeMultisampledStencilBuffer:f.ignoreDepthValues===!1})}v.isXRRenderTarget=!0,this.setFoveation(c),l=null,a=await s.requestReferenceSpace(o),ft.setContext(s),ft.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(s!==null)return s.environmentBlendMode},this.getDepthTexture=function(){return p.getDepthTexture()};function at(N){for(let k=0;k<N.removed.length;k++){let dt=N.removed[k],St=M.indexOf(dt);St>=0&&(M[St]=null,b[St].disconnect(dt))}for(let k=0;k<N.added.length;k++){let dt=N.added[k],St=M.indexOf(dt);if(St===-1){for(let Ft=0;Ft<b.length;Ft++)if(Ft>=M.length){M.push(dt),St=Ft;break}else if(M[Ft]===null){M[Ft]=dt,St=Ft;break}if(St===-1)break}let Mt=b[St];Mt&&Mt.connect(dt)}}let K=new C,st=new C;function it(N,k,dt){K.setFromMatrixPosition(k.matrixWorld),st.setFromMatrixPosition(dt.matrixWorld);let St=K.distanceTo(st),Mt=k.projectionMatrix.elements,Ft=dt.projectionMatrix.elements,xt=Mt[14]/(Mt[10]-1),X=Mt[14]/(Mt[10]+1),tt=(Mt[9]+1)/Mt[5],G=(Mt[9]-1)/Mt[5],et=(Mt[8]-1)/Mt[0],gt=(Ft[8]+1)/Ft[0],Bt=xt*et,bt=xt*gt,jt=St/(-et+gt),ne=jt*-et;if(k.matrixWorld.decompose(N.position,N.quaternion,N.scale),N.translateX(ne),N.translateZ(jt),N.matrixWorld.compose(N.position,N.quaternion,N.scale),N.matrixWorldInverse.copy(N.matrixWorld).invert(),Mt[10]===-1)N.projectionMatrix.copy(k.projectionMatrix),N.projectionMatrixInverse.copy(k.projectionMatrixInverse);else{let U=xt+jt,Ee=X+jt,se=Bt-ne,R=bt+(St-ne),S=tt*X/Ee*U,H=G*X/Ee*U;N.projectionMatrix.makePerspective(se,R,S,H,U,Ee),N.projectionMatrixInverse.copy(N.projectionMatrix).invert()}}function Rt(N,k){k===null?N.matrixWorld.copy(N.matrix):N.matrixWorld.multiplyMatrices(k.matrixWorld,N.matrix),N.matrixWorldInverse.copy(N.matrixWorld).invert()}this.updateCamera=function(N){if(s===null)return;let k=N.near,dt=N.far;p.texture!==null&&(p.depthNear>0&&(k=p.depthNear),p.depthFar>0&&(dt=p.depthFar)),V.near=L.near=P.near=k,V.far=L.far=P.far=dt,(I!==V.near||z!==V.far)&&(s.updateRenderState({depthNear:V.near,depthFar:V.far}),I=V.near,z=V.far),V.layers.mask=N.layers.mask|6,P.layers.mask=V.layers.mask&-5,L.layers.mask=V.layers.mask&-3;let St=N.parent,Mt=V.cameras;Rt(V,St);for(let Ft=0;Ft<Mt.length;Ft++)Rt(Mt[Ft],St);Mt.length===2?it(V,P,L):V.projectionMatrix.copy(P.projectionMatrix),T===null&&N.isPerspectiveCamera&&(T={camera:N,fov:N.fov,zoom:N.zoom}),mt(N,V,St)};function mt(N,k,dt){dt===null?N.matrix.copy(k.matrixWorld):(N.matrix.copy(dt.matrixWorld),N.matrix.invert(),N.matrix.multiply(k.matrixWorld)),N.matrix.decompose(N.position,N.quaternion,N.scale),N.updateMatrixWorld(!0),N.projectionMatrix.copy(k.projectionMatrix),N.projectionMatrixInverse.copy(k.projectionMatrixInverse),N.isPerspectiveCamera&&(N.fov=tr*2*Math.atan(1/N.projectionMatrix.elements[5]),N.zoom=1)}this.getCamera=function(){return V},this.getFoveation=function(){if(!(h===null&&f===null))return c},this.setFoveation=function(N){c=N,h!==null&&(h.fixedFoveation=N),f!==null&&f.fixedFoveation!==void 0&&(f.fixedFoveation=N)},this.hasDepthSensing=function(){return p.texture!==null},this.getDepthSensingMesh=function(){return p.getMesh(V)},this.getCameraTexture=function(N){return m[N]};let Ut=null;function Dt(N,k){if(u=k.getViewerPose(l||a),g=k,u!==null){let dt=u.views;f!==null&&(t.setRenderTargetFramebuffer(v,f.framebuffer),t.setRenderTarget(v));let St=!1;dt.length!==V.cameras.length&&(V.cameras.length=0,St=!0);for(let X=0;X<dt.length;X++){let tt=dt[X],G=null;if(f!==null)G=f.getViewport(tt);else{let gt=d.getViewSubImage(h,tt);G=gt.viewport,X===0&&(t.setRenderTargetTextures(v,gt.colorTexture,gt.depthStencilTexture),t.setRenderTarget(v))}let et=F[X];et===void 0&&(et=new Je,et.layers.enable(X),et.viewport=new xe,F[X]=et),et.matrix.fromArray(tt.transform.matrix),et.matrix.decompose(et.position,et.quaternion,et.scale),et.projectionMatrix.fromArray(tt.projectionMatrix),et.projectionMatrixInverse.copy(et.projectionMatrix).invert(),et.viewport.set(G.x,G.y,G.width,G.height),X===0&&(V.matrix.copy(et.matrix),V.matrix.decompose(V.position,V.quaternion,V.scale)),St===!0&&V.cameras.push(et)}let Mt=s.enabledFeatures;if(Mt&&Mt.includes("depth-sensing")&&s.depthUsage=="gpu-optimized"&&x){d=n.getBinding();let X=d.getDepthInformation(dt[0]);X&&X.isValid&&X.texture&&p.init(X,s.renderState)}if(Mt&&Mt.includes("camera-access")&&x){t.state.unbindTexture(),d=n.getBinding();for(let X=0;X<dt.length;X++){let tt=dt[X].camera;if(tt){let G=m[tt];G||(G=new Zr,m[tt]=G);let et=d.getCameraImage(tt);G.sourceTexture=et}}}}for(let dt=0;dt<b.length;dt++){let St=M[dt],Mt=b[dt];St!==null&&Mt!==void 0&&Mt.update(St,k,l||a)}Ut&&Ut(N,k),k.detectedPlanes&&n.dispatchEvent({type:"planesdetected",data:k}),g=null}let ft=new Id;ft.setAnimationLoop(Dt),this.setAnimationLoop=function(N){Ut=N},this.dispose=function(){}}},zx=new de,zd=new he;zd.set(-1,0,0,0,1,0,0,0,1);function Ox(i,t){function e(p,m){p.matrixAutoUpdate===!0&&p.updateMatrix(),m.value.copy(p.matrix)}function n(p,m){m.color.getRGB(p.fogColor.value,ih(i)),m.isFog?(p.fogNear.value=m.near,p.fogFar.value=m.far):m.isFogExp2&&(p.fogDensity.value=m.density)}function s(p,m,y,E,v){m.isNodeMaterial?m.uniformsNeedUpdate=!1:m.isMeshBasicMaterial?r(p,m):m.isMeshLambertMaterial?(r(p,m),m.envMap&&(p.envMapIntensity.value=m.envMapIntensity)):m.isMeshToonMaterial?(r(p,m),d(p,m)):m.isMeshPhongMaterial?(r(p,m),u(p,m),m.envMap&&(p.envMapIntensity.value=m.envMapIntensity)):m.isMeshStandardMaterial?(r(p,m),h(p,m),m.isMeshPhysicalMaterial&&f(p,m,v)):m.isMeshMatcapMaterial?(r(p,m),g(p,m)):m.isMeshDepthMaterial?r(p,m):m.isMeshDistanceMaterial?(r(p,m),x(p,m)):m.isMeshNormalMaterial?r(p,m):m.isLineBasicMaterial?(a(p,m),m.isLineDashedMaterial&&o(p,m)):m.isPointsMaterial?c(p,m,y,E):m.isSpriteMaterial?l(p,m):m.isShadowMaterial?(p.color.value.copy(m.color),p.opacity.value=m.opacity):m.isShaderMaterial&&(m.uniformsNeedUpdate=!1)}function r(p,m){p.opacity.value=m.opacity,m.color&&p.diffuse.value.copy(m.color),m.emissive&&p.emissive.value.copy(m.emissive).multiplyScalar(m.emissiveIntensity),m.map&&(p.map.value=m.map,e(m.map,p.mapTransform)),m.alphaMap&&(p.alphaMap.value=m.alphaMap,e(m.alphaMap,p.alphaMapTransform)),m.bumpMap&&(p.bumpMap.value=m.bumpMap,e(m.bumpMap,p.bumpMapTransform),p.bumpScale.value=m.bumpScale,m.side===on&&(p.bumpScale.value*=-1)),m.normalMap&&(p.normalMap.value=m.normalMap,e(m.normalMap,p.normalMapTransform),p.normalScale.value.copy(m.normalScale),m.side===on&&p.normalScale.value.negate()),m.displacementMap&&(p.displacementMap.value=m.displacementMap,e(m.displacementMap,p.displacementMapTransform),p.displacementScale.value=m.displacementScale,p.displacementBias.value=m.displacementBias),m.emissiveMap&&(p.emissiveMap.value=m.emissiveMap,e(m.emissiveMap,p.emissiveMapTransform)),m.specularMap&&(p.specularMap.value=m.specularMap,e(m.specularMap,p.specularMapTransform)),m.alphaTest>0&&(p.alphaTest.value=m.alphaTest);let y=t.get(m),E=y.envMap,v=y.envMapRotation;E&&(p.envMap.value=E,p.envMapRotation.value.setFromMatrix4(zx.makeRotationFromEuler(v)).transpose(),E.isCubeTexture&&E.isRenderTargetTexture===!1&&p.envMapRotation.value.premultiply(zd),p.reflectivity.value=m.reflectivity,p.ior.value=m.ior,p.refractionRatio.value=m.refractionRatio),m.lightMap&&(p.lightMap.value=m.lightMap,p.lightMapIntensity.value=m.lightMapIntensity,e(m.lightMap,p.lightMapTransform)),m.aoMap&&(p.aoMap.value=m.aoMap,p.aoMapIntensity.value=m.aoMapIntensity,e(m.aoMap,p.aoMapTransform))}function a(p,m){p.diffuse.value.copy(m.color),p.opacity.value=m.opacity,m.map&&(p.map.value=m.map,e(m.map,p.mapTransform))}function o(p,m){p.dashSize.value=m.dashSize,p.totalSize.value=m.dashSize+m.gapSize,p.scale.value=m.scale}function c(p,m,y,E){p.diffuse.value.copy(m.color),p.opacity.value=m.opacity,p.size.value=m.size*y,p.scale.value=E*.5,m.map&&(p.map.value=m.map,e(m.map,p.uvTransform)),m.alphaMap&&(p.alphaMap.value=m.alphaMap,e(m.alphaMap,p.alphaMapTransform)),m.alphaTest>0&&(p.alphaTest.value=m.alphaTest)}function l(p,m){p.diffuse.value.copy(m.color),p.opacity.value=m.opacity,p.rotation.value=m.rotation,m.map&&(p.map.value=m.map,e(m.map,p.mapTransform)),m.alphaMap&&(p.alphaMap.value=m.alphaMap,e(m.alphaMap,p.alphaMapTransform)),m.alphaTest>0&&(p.alphaTest.value=m.alphaTest)}function u(p,m){p.specular.value.copy(m.specular),p.shininess.value=Math.max(m.shininess,1e-4)}function d(p,m){m.gradientMap&&(p.gradientMap.value=m.gradientMap)}function h(p,m){p.metalness.value=m.metalness,m.metalnessMap&&(p.metalnessMap.value=m.metalnessMap,e(m.metalnessMap,p.metalnessMapTransform)),p.roughness.value=m.roughness,m.roughnessMap&&(p.roughnessMap.value=m.roughnessMap,e(m.roughnessMap,p.roughnessMapTransform)),m.envMap&&(p.envMapIntensity.value=m.envMapIntensity)}function f(p,m,y){p.ior.value=m.ior,m.sheen>0&&(p.sheenColor.value.copy(m.sheenColor).multiplyScalar(m.sheen),p.sheenRoughness.value=m.sheenRoughness,m.sheenColorMap&&(p.sheenColorMap.value=m.sheenColorMap,e(m.sheenColorMap,p.sheenColorMapTransform)),m.sheenRoughnessMap&&(p.sheenRoughnessMap.value=m.sheenRoughnessMap,e(m.sheenRoughnessMap,p.sheenRoughnessMapTransform))),m.clearcoat>0&&(p.clearcoat.value=m.clearcoat,p.clearcoatRoughness.value=m.clearcoatRoughness,m.clearcoatMap&&(p.clearcoatMap.value=m.clearcoatMap,e(m.clearcoatMap,p.clearcoatMapTransform)),m.clearcoatRoughnessMap&&(p.clearcoatRoughnessMap.value=m.clearcoatRoughnessMap,e(m.clearcoatRoughnessMap,p.clearcoatRoughnessMapTransform)),m.clearcoatNormalMap&&(p.clearcoatNormalMap.value=m.clearcoatNormalMap,e(m.clearcoatNormalMap,p.clearcoatNormalMapTransform),p.clearcoatNormalScale.value.copy(m.clearcoatNormalScale),m.side===on&&p.clearcoatNormalScale.value.negate())),m.dispersion>0&&(p.dispersion.value=m.dispersion),m.retroreflectivity>0&&(p.retroreflectivity.value=m.retroreflectivity),m.iridescence>0&&(p.iridescence.value=m.iridescence,p.iridescenceIOR.value=m.iridescenceIOR,p.iridescenceThicknessMinimum.value=m.iridescenceThicknessRange[0],p.iridescenceThicknessMaximum.value=m.iridescenceThicknessRange[1],m.iridescenceMap&&(p.iridescenceMap.value=m.iridescenceMap,e(m.iridescenceMap,p.iridescenceMapTransform)),m.iridescenceThicknessMap&&(p.iridescenceThicknessMap.value=m.iridescenceThicknessMap,e(m.iridescenceThicknessMap,p.iridescenceThicknessMapTransform))),m.transmission>0&&(p.transmission.value=m.transmission,p.transmissionSamplerMap.value=y.texture,p.transmissionSamplerSize.value.set(y.width,y.height),m.transmissionMap&&(p.transmissionMap.value=m.transmissionMap,e(m.transmissionMap,p.transmissionMapTransform)),p.thickness.value=m.thickness,m.thicknessMap&&(p.thicknessMap.value=m.thicknessMap,e(m.thicknessMap,p.thicknessMapTransform)),p.attenuationDistance.value=m.attenuationDistance,p.attenuationColor.value.copy(m.attenuationColor)),m.anisotropy>0&&(p.anisotropyVector.value.set(m.anisotropy*Math.cos(m.anisotropyRotation),m.anisotropy*Math.sin(m.anisotropyRotation)),m.anisotropyMap&&(p.anisotropyMap.value=m.anisotropyMap,e(m.anisotropyMap,p.anisotropyMapTransform))),p.specularIntensity.value=m.specularIntensity,p.specularColor.value.copy(m.specularColor),m.specularColorMap&&(p.specularColorMap.value=m.specularColorMap,e(m.specularColorMap,p.specularColorMapTransform)),m.specularIntensityMap&&(p.specularIntensityMap.value=m.specularIntensityMap,e(m.specularIntensityMap,p.specularIntensityMapTransform))}function g(p,m){m.matcap&&(p.matcap.value=m.matcap)}function x(p,m){let y=t.get(m).light;p.referencePosition.value.setFromMatrixPosition(y.matrixWorld),p.nearDistance.value=y.shadow.camera.near,p.farDistance.value=y.shadow.camera.far}return{refreshFogUniforms:n,refreshMaterialUniforms:s}}function Bx(i,t,e,n){let s={},r={},a=[],o=i.getParameter(i.MAX_UNIFORM_BUFFER_BINDINGS);function c(v,b){let M=b.program;n.uniformBlockBinding(v,M)}function l(v,b){let M=s[v.id];M===void 0&&(p(v),M=u(v),s[v.id]=M,v.addEventListener("dispose",y));let A=b.program;n.updateUBOMapping(v,A);let _=t.render.frame;r[v.id]!==_&&(h(v),r[v.id]=_)}function u(v){let b=d();v.__bindingPointIndex=b;let M=i.createBuffer(),A=v.__size,_=v.usage;return i.bindBuffer(i.UNIFORM_BUFFER,M),i.bufferData(i.UNIFORM_BUFFER,A,_),i.bindBuffer(i.UNIFORM_BUFFER,null),i.bindBufferBase(i.UNIFORM_BUFFER,b,M),M}function d(){for(let v=0;v<o;v++)if(a.indexOf(v)===-1)return a.push(v),v;return ae("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function h(v){let b=s[v.id],M=v.uniforms,A=v.__cache;i.bindBuffer(i.UNIFORM_BUFFER,b);for(let _=0,T=M.length;_<T;_++){let P=M[_];if(Array.isArray(P))for(let L=0,F=P.length;L<F;L++)f(P[L],_,L,A);else f(P,_,0,A)}i.bindBuffer(i.UNIFORM_BUFFER,null)}function f(v,b,M,A){if(x(v,b,M,A)===!0){let _=v.__offset,T=v.value;if(Array.isArray(T)){let P=0;for(let L=0;L<T.length;L++){let F=T[L],V=m(F);g(F,v.__data,P),typeof F!="number"&&typeof F!="boolean"&&!F.isMatrix3&&!ArrayBuffer.isView(F)&&(P+=V.storage/Float32Array.BYTES_PER_ELEMENT)}}else g(T,v.__data,0);i.bufferSubData(i.UNIFORM_BUFFER,_,v.__data)}}function g(v,b,M){typeof v=="number"||typeof v=="boolean"?b[0]=v:v.isMatrix3?(b[0]=v.elements[0],b[1]=v.elements[1],b[2]=v.elements[2],b[3]=0,b[4]=v.elements[3],b[5]=v.elements[4],b[6]=v.elements[5],b[7]=0,b[8]=v.elements[6],b[9]=v.elements[7],b[10]=v.elements[8],b[11]=0):ArrayBuffer.isView(v)?b.set(new v.constructor(v.buffer,v.byteOffset,b.length)):v.toArray(b,M)}function x(v,b,M,A){let _=v.value,T=b+"_"+M;if(A[T]===void 0)return typeof _=="number"||typeof _=="boolean"?A[T]=_:ArrayBuffer.isView(_)?A[T]=_.slice():A[T]=_.clone(),!0;{let P=A[T];if(typeof _=="number"||typeof _=="boolean"){if(P!==_)return A[T]=_,!0}else{if(ArrayBuffer.isView(_))return!0;if(P.equals(_)===!1)return P.copy(_),!0}}return!1}function p(v){let b=v.uniforms,M=0,A=16;for(let T=0,P=b.length;T<P;T++){let L=Array.isArray(b[T])?b[T]:[b[T]];for(let F=0,V=L.length;F<V;F++){let I=L[F],z=Array.isArray(I.value)?I.value:[I.value];for(let q=0,j=z.length;q<j;q++){let at=z[q],K=m(at),st=M%A,it=st%K.boundary,Rt=st+it;M+=it,Rt!==0&&A-Rt<K.storage&&(M+=A-Rt),I.__data=new Float32Array(K.storage/Float32Array.BYTES_PER_ELEMENT),I.__offset=M,M+=K.storage}}}let _=M%A;return _>0&&(M+=A-_),v.__size=M,v.__cache={},this}function m(v){let b={boundary:0,storage:0};return typeof v=="number"||typeof v=="boolean"?(b.boundary=4,b.storage=4):v.isVector2?(b.boundary=8,b.storage=8):v.isVector3||v.isColor?(b.boundary=16,b.storage=12):v.isVector4?(b.boundary=16,b.storage=16):v.isMatrix3?(b.boundary=48,b.storage=48):v.isMatrix4?(b.boundary=64,b.storage=64):v.isTexture?ie("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(v)?(b.boundary=16,b.storage=v.byteLength):ie("WebGLRenderer: Unsupported uniform value type.",v),b}function y(v){let b=v.target;b.removeEventListener("dispose",y);let M=a.indexOf(b.__bindingPointIndex);a.splice(M,1),i.deleteBuffer(s[b.id]),delete s[b.id],delete r[b.id]}function E(){for(let v in s)i.deleteBuffer(s[v]);a=[],s={},r={}}return{bind:c,update:l,dispose:E}}var kx=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]),Si=null;function Hx(){return Si===null&&(Si=new ys(kx,16,16,yi,Bn),Si.name="DFG_LUT",Si.minFilter=Ke,Si.magFilter=Ke,Si.wrapS=Wn,Si.wrapT=Wn,Si.generateMipmaps=!1,Si.needsUpdate=!0),Si}var Nc=class{constructor(t={}){let{canvas:e=Qu(),context:n=null,depth:s=!0,stencil:r=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:c=!0,preserveDrawingBuffer:l=!1,powerPreference:u="default",failIfMajorPerformanceCaveat:d=!1,reversedDepthBuffer:h=!1,outputBufferType:f=Ln}=t;this.isWebGLRenderer=!0;let g;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");g=n.getContextAttributes().alpha}else g=a;let x=f,p=new Set([Ko,Jo,$o]),m=new Set([Ln,li,dr,fr,Yo,jo]),y=new Uint32Array(4),E=new Int32Array(4),v=new C,b=null,M=null,A=[],_=[],T=null;this.domElement=e,this.debug={checkShaderErrors:!0,diagnostics:{keywords:!1},onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=On,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let P=this,L=!1,F=null,V=null,I=null,z=null;this._outputColorSpace=bn;let q=0,j=0,at=null,K=-1,st=null,it=new xe,Rt=new xe,mt=null,Ut=new Wt(0),Dt=0,ft=e.width,N=e.height,k=1,dt=null,St=null,Mt=new xe(0,0,ft,N),Ft=new xe(0,0,ft,N),xt=!1,X=new sr,tt=!1,G=!1,et=new de,gt=new C,Bt=new xe,bt={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},jt=!1;function ne(){return at===null?k:1}let U=n;function Ee(w,O){return e.getContext(w,O)}let se,R,S,H,Y,rt,_t,Et,nt,ut,At,Zt,It,Lt,$t,ee,ce,B,Ct,lt,Pt,yt,pt;try{let w={alpha:!0,depth:s,stencil:r,antialias:o,premultipliedAlpha:c,preserveDrawingBuffer:l,powerPreference:u,failIfMajorPerformanceCaveat:d};if("setAttribute"in e&&e.setAttribute("data-engine",`three.js r${"186"}`),e.addEventListener("webglcontextlost",we,!1),e.addEventListener("webglcontextrestored",ye,!1),e.addEventListener("webglcontextcreationerror",dn,!1),U===null){let O="webgl2";if(U=Ee(O,w),U===null)throw Ee(O)?new Error("THREE.WebGLRenderer: Error creating WebGL context with your selected attributes."):new Error("THREE.WebGLRenderer: Error creating WebGL context.")}Xt()}catch(w){throw e.removeEventListener("webglcontextlost",we,!1),e.removeEventListener("webglcontextrestored",ye,!1),e.removeEventListener("webglcontextcreationerror",dn,!1),ae("WebGLRenderer: "+w.message),w}function Xt(){se=new jg(U),se.init(),Pt=new Ux(U,se),R=new Og(U,se,t,Pt),S=new Lx(U,se),R.reversedDepthBuffer&&h&&S.buffers.depth.setReversed(!0),V=U.createFramebuffer(),I=U.createFramebuffer(),z=U.createFramebuffer(),H=new Jg(U),Y=new xx,rt=new Dx(U,se,S,Y,R,Pt,H),_t=new Yg(P),Et=new Qp(U),yt=new Fg(U,Et),nt=new Zg(U,Et,H,yt),ut=new Qg(U,nt,Et,yt,H),B=new Kg(U,R,rt),$t=new Bg(Y),At=new vx(P,_t,se,R,yt,$t),Zt=new Ox(P,Y),It=new yx,Lt=new Tx(se),ce=new Ng(P,_t,S,ut,g,c),ee=new Ix(P,ut,R),pt=new Bx(U,H,R,S),Ct=new zg(U,se,H),lt=new $g(U,se,H),H.programs=At.programs,P.capabilities=R,P.extensions=se,P.properties=Y,P.renderLists=It,P.shadowMap=ee,P.state=S,P.info=H}x!==Ln&&(T=new ev(x,e.width,e.height,o,s,r));let Ht=new Th(P,U);this.xr=Ht,this.getContext=function(){return U},this.getContextAttributes=function(){return U.getContextAttributes()},this.forceContextLoss=function(){let w=se.get("WEBGL_lose_context");w&&w.loseContext()},this.forceContextRestore=function(){let w=se.get("WEBGL_lose_context");w&&w.restoreContext()},this.getPixelRatio=function(){return k},this.setPixelRatio=function(w){w!==void 0&&(k=w,this.setSize(ft,N,!1))},this.getSize=function(w){return w.set(ft,N)},this.setSize=function(w,O,Q=!0){if(Ht.isPresenting){ie("WebGLRenderer: Can't change size while VR device is presenting.");return}ft=w,N=O,e.width=Math.floor(w*k),e.height=Math.floor(O*k),Q===!0&&(e.style.width=w+"px",e.style.height=O+"px"),T!==null&&T.setSize(e.width,e.height),this.setViewport(0,0,w,O)},this.getDrawingBufferSize=function(w){return w.set(ft*k,N*k).floor()},this.setDrawingBufferSize=function(w,O,Q){ft=w,N=O,k=Q,e.width=Math.floor(w*Q),e.height=Math.floor(O*Q),this.setViewport(0,0,w,O)},this.setEffects=function(w){if(x===Ln){ae("WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(w){for(let O=0;O<w.length;O++)if(w[O].isOutputPass===!0){ie("WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}T.setEffects(w||[])},this.getCurrentViewport=function(w){return w.copy(it)},this.getViewport=function(w){return w.copy(Mt)},this.setViewport=function(w,O,Q,$){w.isVector4?Mt.set(w.x,w.y,w.z,w.w):Mt.set(w,O,Q,$),S.viewport(it.copy(Mt).multiplyScalar(k).round())},this.getScissor=function(w){return w.copy(Ft)},this.setScissor=function(w,O,Q,$){w.isVector4?Ft.set(w.x,w.y,w.z,w.w):Ft.set(w,O,Q,$),S.scissor(Rt.copy(Ft).multiplyScalar(k).round())},this.getScissorTest=function(){return xt},this.setScissorTest=function(w){S.setScissorTest(xt=w)},this.setOpaqueSort=function(w){dt=w},this.setTransparentSort=function(w){St=w},this.getClearColor=function(w){return w.copy(ce.getClearColor())},this.setClearColor=function(){ce.setClearColor(...arguments)},this.getClearAlpha=function(){return ce.getClearAlpha()},this.setClearAlpha=function(){ce.setClearAlpha(...arguments)},this.clear=function(w=!0,O=!0,Q=!0){let $=0;if(w){let Z=!1;if(at!==null){let Tt=at.texture.format;Z=p.has(Tt)}if(Z){let Tt=at.texture.type,kt=m.has(Tt),zt=ce.getClearColor(),Yt=ce.getClearAlpha(),Qt=zt.r,pe=zt.g,_e=zt.b;kt?(y[0]=Qt,y[1]=pe,y[2]=_e,y[3]=Yt,U.clearBufferuiv(U.COLOR,0,y)):(E[0]=Qt,E[1]=pe,E[2]=_e,E[3]=Yt,U.clearBufferiv(U.COLOR,0,E))}else $|=U.COLOR_BUFFER_BIT}O&&($|=U.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),Q&&($|=U.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),$!==0&&U.clear($)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(w){w.setRenderer(this),F=w},this.dispose=function(){e.removeEventListener("webglcontextlost",we,!1),e.removeEventListener("webglcontextrestored",ye,!1),e.removeEventListener("webglcontextcreationerror",dn,!1),ce.dispose(),It.dispose(),Lt.dispose(),Y.dispose(),_t.dispose(),ut.dispose(),yt.dispose(),pt.dispose(),At.dispose(),Ht.dispose(),Ht.removeEventListener("sessionstart",kn),Ht.removeEventListener("sessionend",Ci),Kn.stop()};function we(w){w.preventDefault(),Or("WebGLRenderer: Context Lost."),L=!0}function ye(){Or("WebGLRenderer: Context Restored."),L=!1;let w=H.autoReset,O=ee.enabled,Q=ee.autoUpdate,$=ee.needsUpdate,Z=ee.type;Xt(),H.autoReset=w,ee.enabled=O,ee.autoUpdate=Q,ee.needsUpdate=$,ee.type=Z}function dn(w){ae("WebGLRenderer: A WebGL context could not be created. Reason: ",w.statusMessage)}function fn(w){let O=w.target;O.removeEventListener("dispose",fn),Ps(O)}function Ps(w){Ai(w),Y.remove(w)}function Ai(w){let O=Y.get(w).programs;O!==void 0&&(O.forEach(function(Q){At.releaseProgram(Q)}),w.isShaderMaterial&&At.releaseShaderCache(w))}this.renderBufferDirect=function(w,O,Q,$,Z,Tt){O===null&&(O=bt);let kt=Z.isMesh&&Z.matrixWorld.determinantAffine()<0,zt=Kt(w,O,Q,$,Z);S.setMaterial($,kt);let Yt=Q.index,Qt=1;if($.wireframe===!0){if(Yt=nt.getWireframeAttribute(Q),Yt===void 0)return;Qt=2}let pe=Q.drawRange,_e=Q.attributes.position,Jt=pe.start*Qt,Pe=(pe.start+pe.count)*Qt;Tt!==null&&(Jt=Math.max(Jt,Tt.start*Qt),Pe=Math.min(Pe,(Tt.start+Tt.count)*Qt)),Yt!==null?(Jt=Math.max(Jt,0),Pe=Math.min(Pe,Yt.count)):_e!=null&&(Jt=Math.max(Jt,0),Pe=Math.min(Pe,_e.count));let Ze=Pe-Jt;if(Ze<0||Ze===1/0)return;yt.setup(Z,$,zt,Q,Yt);let Ve,ze=Ct;if(Yt!==null&&(Ve=Et.get(Yt),ze=lt,ze.setIndex(Ve)),Z.isMesh)$.wireframe===!0?(S.setLineWidth($.wireframeLinewidth*ne()),ze.setMode(U.LINES)):ze.setMode(U.TRIANGLES);else if(Z.isLine){let pn=$.linewidth;pn===void 0&&(pn=1),S.setLineWidth(pn*ne()),Z.isLineSegments?ze.setMode(U.LINES):Z.isLineLoop?ze.setMode(U.LINE_LOOP):ze.setMode(U.LINE_STRIP)}else Z.isPoints?ze.setMode(U.POINTS):Z.isSprite&&ze.setMode(U.TRIANGLES);if(Z.isBatchedMesh)if(se.get("WEBGL_multi_draw"))ze.renderMultiDraw(Z._multiDrawStarts,Z._multiDrawCounts,Z._multiDrawCount);else{let pn=Z._multiDrawStarts,Gt=Z._multiDrawCounts,Mn=Z._multiDrawCount,Te=Yt?Et.get(Yt).bytesPerElement:1,Vn=Y.get($).currentProgram.getUniforms();for(let ui=0;ui<Mn;ui++)Vn.setValue(U,"_gl_DrawID",ui),ze.render(pn[ui]/Te,Gt[ui])}else if(Z.isInstancedMesh)ze.renderInstances(Jt,Ze,Z.count);else if(Q.isInstancedBufferGeometry){let pn=Q._maxInstanceCount!==void 0?Q._maxInstanceCount:1/0,Gt=Math.min(Q.instanceCount,pn);ze.renderInstances(Jt,Ze,Gt)}else ze.render(Jt,Ze)};function Ri(w,O,Q,$){F!==null&&w.isNodeMaterial&&F.setObject($,w),tt===!0&&$t.setState(w,Q,!1),w.transparent===!0&&w.side===vn&&w.forceSinglePass===!1?(w.side=on,w.needsUpdate=!0,J(w,O,$),w.side=rs,w.needsUpdate=!0,J(w,O,$),w.side=vn):J(w,O,$)}this.compile=function(w,O,Q=null){Q===null&&(Q=w),F!==null&&F.renderStart(w,O,Q),M=Lt.get(Q),M.init(O),_.push(M),Q.traverseVisible(function(Z){Z.isLight&&Z.layers.test(O.layers)&&(M.pushLight(Z),Z.castShadow&&M.pushShadow(Z))}),w!==Q&&w.traverseVisible(function(Z){Z.isLight&&Z.layers.test(O.layers)&&(M.pushLight(Z),Z.castShadow&&M.pushShadow(Z))}),M.setupLights(),F!==null&&F.updateLights(M.state.lightsArray),G=this.localClippingEnabled,tt=$t.init(this.clippingPlanes,G),tt===!0&&$t.setGlobalState(this.clippingPlanes,O),F!==null&&ee.render(M.state.shadowsArray,Q,O);let $=new Set;return w.traverse(function(Z){if(!(Z.isMesh||Z.isPoints||Z.isLine||Z.isSprite))return;let Tt=Z.material;if(Tt)if(Array.isArray(Tt))for(let kt=0;kt<Tt.length;kt++){let zt=Tt[kt];Ri(zt,Q,O,Z),$.add(zt)}else Ri(Tt,Q,O,Z),$.add(Tt)}),M=_.pop(),F!==null&&F.renderEnd(),$},this.compileAsync=function(w,O,Q=null){let $=this.compile(w,O,Q);return new Promise(Z=>{function Tt(){if($.forEach(function(kt){let Yt=Y.get(kt).currentProgram;(Yt===void 0||Yt.isReady())&&$.delete(kt)}),$.size===0){Z(w);return}setTimeout(Tt,10)}se.get("KHR_parallel_shader_compile")!==null?Tt():setTimeout(Tt,10)})};let Pn=null;function Jn(w){Pn&&Pn(w)}function kn(){Kn.stop()}function Ci(){Kn.start()}let Kn=new Id;Kn.setAnimationLoop(Jn),typeof self<"u"&&Kn.setContext(self),this.setAnimationLoop=function(w){Pn=w,Ht.setAnimationLoop(w),w===null?Kn.stop():Kn.start()},Ht.addEventListener("sessionstart",kn),Ht.addEventListener("sessionend",Ci),this.render=function(w,O){if(O!==void 0&&O.isCamera!==!0){ae("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(L===!0)return;F!==null&&F.renderStart(w,O);let Q=Ht.enabled===!0&&Ht.isPresenting===!0,$=T!==null&&(at===null||Q)&&T.begin(P,at);if(w.matrixWorldAutoUpdate===!0&&w.updateMatrixWorld(),O.parent===null&&O.matrixWorldAutoUpdate===!0&&O.updateMatrixWorld(),Ht.enabled===!0&&Ht.isPresenting===!0&&(T===null||T.isCompositing()===!1)&&(Ht.cameraAutoUpdate===!0&&Ht.updateCamera(O),O=Ht.getCamera()),w.isScene===!0&&w.onBeforeRender(P,w,O,at),M=Lt.get(w,_.length),M.init(O),M.state.textureUnits=rt.getTextureUnits(),_.push(M),et.multiplyMatrices(O.projectionMatrix,O.matrixWorldInverse),X.setFromProjectionMatrix(et,si,O.reversedDepth),G=this.localClippingEnabled,tt=$t.init(this.clippingPlanes,G),b=It.get(w,A.length),b.init(),A.push(b),Ht.enabled===!0&&Ht.isPresenting===!0){let kt=P.xr.getDepthSensingMesh();kt!==null&&Hn(kt,O,-1/0,P.sortObjects)}Hn(w,O,0,P.sortObjects),b.finish(),F!==null&&F.updateLights(M.state.lightsArray),P.sortObjects===!0&&b.sort(dt,St),jt=Ht.enabled===!1||Ht.isPresenting===!1||Ht.hasDepthSensing()===!1,jt&&ce.addToRenderList(b,w),this.info.render.frame++,this.info.autoReset===!0&&this.info.reset(),tt===!0&&$t.beginShadows();let Z=M.state.shadowsArray;if(ee.render(Z,w,O),tt===!0&&$t.endShadows(),($&&T.hasRenderPass())===!1){let kt=b.opaque,zt=b.transmissive;if(M.setupLights(),O.isArrayCamera){let Yt=O.cameras;if(zt.length>0)for(let Qt=0,pe=Yt.length;Qt<pe;Qt++){let _e=Yt[Qt];ot(kt,zt,w,_e)}jt&&ce.render(w);for(let Qt=0,pe=Yt.length;Qt<pe;Qt++){let _e=Yt[Qt];fs(b,w,_e,_e.viewport)}}else zt.length>0&&ot(kt,zt,w,O),jt&&ce.render(w),fs(b,w,O)}at!==null&&j===0&&(rt.updateMultisampleRenderTarget(at),rt.updateRenderTargetMipmap(at)),$&&T.end(P),w.isScene===!0&&w.onAfterRender(P,w,O),yt.resetDefaultState(),K=-1,st=null,_.pop(),_.length>0?(M=_[_.length-1],rt.setTextureUnits(M.state.textureUnits),tt===!0&&$t.setGlobalState(P.clippingPlanes,M.state.camera)):M=null,A.pop(),A.length>0?b=A[A.length-1]:b=null,F!==null&&F.renderEnd()};function Hn(w,O,Q,$){if(w.visible===!1)return;if(w.layers.test(O.layers)){if(w.isGroup)Q=w.renderOrder;else if(w.isLOD)w.autoUpdate===!0&&w.update(O);else if(w.isLightProbeGrid)M.pushLightProbeGrid(w);else if(w.isLight)M.pushLight(w),w.castShadow&&M.pushShadow(w);else if(w.isSprite){if(!w.frustumCulled||w.intersectsFrustum(X)){$&&Bt.setFromMatrixPosition(w.matrixWorld).applyMatrix4(et);let kt=ut.update(w),zt=w.material;zt.visible&&b.push(w,kt,zt,Q,Bt.z,null,O)}}else if((w.isMesh||w.isLine||w.isPoints)&&(!w.frustumCulled||w.intersectsFrustum(X))){let kt=ut.update(w),zt=w.material;if($&&(w.boundingSphere!==void 0?(w.boundingSphere===null&&w.computeBoundingSphere(),Bt.copy(w.boundingSphere.center)):(kt.boundingSphere===null&&kt.computeBoundingSphere(),Bt.copy(kt.boundingSphere.center)),Bt.applyMatrix4(w.matrixWorld).applyMatrix4(et)),Array.isArray(zt)){let Yt=kt.groups;for(let Qt=0,pe=Yt.length;Qt<pe;Qt++){let _e=Yt[Qt],Jt=zt[_e.materialIndex];Jt&&Jt.visible&&b.push(w,kt,Jt,Q,Bt.z,_e,O)}}else zt.visible&&b.push(w,kt,zt,Q,Bt.z,null,O)}}let Tt=w.children;for(let kt=0,zt=Tt.length;kt<zt;kt++)Hn(Tt[kt],O,Q,$)}function fs(w,O,Q,$){let{opaque:Z,transmissive:Tt,transparent:kt}=w;M.setupLightsView(Q),tt===!0&&$t.setGlobalState(P.clippingPlanes,Q),$&&S.viewport(it.copy($)),Z.length>0&&D(Z,O,Q),Tt.length>0&&D(Tt,O,Q),kt.length>0&&D(kt,O,Q),S.buffers.depth.setTest(!0),S.buffers.depth.setMask(!0),S.buffers.color.setMask(!0),S.setPolygonOffset(!1)}function ot(w,O,Q,$){if((Q.isScene===!0?Q.overrideMaterial:null)!==null)return;if(M.state.transmissionRenderTarget[$.id]===void 0){let Jt=se.has("EXT_color_buffer_half_float")||se.has("EXT_color_buffer_float");M.state.transmissionRenderTarget[$.id]=new In(1,1,{generateMipmaps:!0,type:Jt?Bn:Ln,minFilter:cs,samples:Math.max(4,R.samples),stencilBuffer:r,resolveDepthBuffer:!1,resolveStencilBuffer:!1,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,colorSpace:Me.workingColorSpace})}let Tt=M.state.transmissionRenderTarget[$.id],kt=$.viewport||it;Tt.setSize(kt.z*P.transmissionResolutionScale,kt.w*P.transmissionResolutionScale);let zt=P.getRenderTarget(),Yt=P.getActiveCubeFace(),Qt=P.getActiveMipmapLevel();P.setRenderTarget(Tt),P.getClearColor(Ut),Dt=P.getClearAlpha(),Dt<1&&P.setClearColor(16777215,.5),P.clear(),jt&&ce.render(Q);let pe=P.toneMapping;P.toneMapping=On;let _e=$.viewport;if($.viewport!==void 0&&($.viewport=void 0),M.setupLightsView($),tt===!0&&$t.setGlobalState(P.clippingPlanes,$),D(w,Q,$),rt.updateMultisampleRenderTarget(Tt),rt.updateRenderTargetMipmap(Tt),se.has("WEBGL_multisampled_render_to_texture")===!1){let Jt=!1;for(let Pe=0,Ze=O.length;Pe<Ze;Pe++){let Ve=O[Pe],{object:ze,geometry:pn,material:Gt,group:Mn}=Ve;if(Gt.side===vn&&ze.layers.test($.layers)){let Te=Gt.side;Gt.side=on,Gt.needsUpdate=!0,W(ze,Q,$,pn,Gt,Mn),Gt.side=Te,Gt.needsUpdate=!0,Jt=!0}}Jt===!0&&(rt.updateMultisampleRenderTarget(Tt),rt.updateRenderTargetMipmap(Tt))}P.setRenderTarget(zt,Yt,Qt),P.setClearColor(Ut,Dt),_e!==void 0&&($.viewport=_e),P.toneMapping=pe}function D(w,O,Q){let $=O.isScene===!0?O.overrideMaterial:null;for(let Z=0,Tt=w.length;Z<Tt;Z++){let kt=w[Z],{object:zt,geometry:Yt,group:Qt}=kt,pe=kt.material;pe.allowOverride===!0&&$!==null&&(pe=$),zt.layers.test(Q.layers)&&W(zt,O,Q,Yt,pe,Qt)}}function W(w,O,Q,$,Z,Tt){F!==null&&Z.isNodeMaterial&&F.setObject(w,Z),w.onBeforeRender(P,O,Q,$,Z,Tt),w.modelViewMatrix.multiplyMatrices(Q.matrixWorldInverse,w.matrixWorld),w.normalMatrix.getNormalMatrix(w.modelViewMatrix),Z.onBeforeRender(P,O,Q,$,w,Tt),Z.transparent===!0&&Z.side===vn&&Z.forceSinglePass===!1?(Z.side=on,Z.needsUpdate=!0,P.renderBufferDirect(Q,O,$,Z,w,Tt),Z.side=rs,Z.needsUpdate=!0,P.renderBufferDirect(Q,O,$,Z,w,Tt),Z.side=vn):P.renderBufferDirect(Q,O,$,Z,w,Tt),w.onAfterRender(P,O,Q,$,Z,Tt)}function J(w,O,Q){O.isScene!==!0&&(O=bt);let $=Y.get(w),Z=M.state.lights,Tt=M.state.shadowsArray,kt=Z.state.version,zt=At.getParameters(w,Z.state,Tt,O,Q,M.state.lightProbeGridArray),Yt=At.getProgramCacheKey(zt),Qt=$.programs;$.environment=w.isMeshStandardMaterial||w.isMeshLambertMaterial||w.isMeshPhongMaterial?O.environment:null,$.fog=O.fog;let pe=w.isMeshStandardMaterial||w.isMeshLambertMaterial&&!w.envMap||w.isMeshPhongMaterial&&!w.envMap;$.envMap=_t.get(w.envMap||$.environment,pe),$.envMapRotation=$.environment!==null&&w.envMap===null?O.environmentRotation:w.envMapRotation,Qt===void 0&&(w.addEventListener("dispose",fn),Qt=new Map,$.programs=Qt);let _e=Qt.get(Yt);if(_e!==void 0){if($.currentProgram===_e&&$.lightsStateVersion===kt)return wt(w,zt),_e}else zt.uniforms=At.getUniforms(w),F!==null&&w.isNodeMaterial&&F.build(w,Q,zt),w.onBeforeCompile(zt,P),_e=At.acquireProgram(zt,Yt),Qt.set(Yt,_e),$.uniforms=zt.uniforms;let Jt=$.uniforms;return(!w.isShaderMaterial&&!w.isRawShaderMaterial||w.clipping===!0)&&(Jt.clippingPlanes=$t.uniform),wt(w,zt),$.needsLights=Re(w),$.lightsStateVersion=kt,$.needsLights&&(Jt.ambientLightColor.value=Z.state.ambient,Jt.lightProbe.value=Z.state.probe,Jt.sunLights.value=Z.state.sun,Jt.sunLightShadows.value=Z.state.sunShadow,Jt.directionalLights.value=Z.state.directional,Jt.directionalLightShadows.value=Z.state.directionalShadow,Jt.spotLights.value=Z.state.spot,Jt.spotLightShadows.value=Z.state.spotShadow,Jt.rectAreaLights.value=Z.state.rectArea,Jt.ltc_1.value=Z.state.rectAreaLTC1,Jt.ltc_2.value=Z.state.rectAreaLTC2,Jt.pointLights.value=Z.state.point,Jt.pointLightShadows.value=Z.state.pointShadow,Jt.hemisphereLights.value=Z.state.hemi,Jt.sunShadowMatrix.value=Z.state.sunShadowMatrix,Jt.sunShadowCascade.value=Z.state.sunShadowCascade,Jt.directionalShadowMatrix.value=Z.state.directionalShadowMatrix,Jt.spotLightMatrix.value=Z.state.spotLightMatrix,Jt.spotLightMap.value=Z.state.spotLightMap,Jt.pointShadowMatrix.value=Z.state.pointShadowMatrix),$.lightProbeGrid=M.state.lightProbeGridArray.length>0,$.currentProgram=_e,$.uniformsList=null,_e}function ht(w){if(w.uniformsList===null){let O=w.currentProgram.getUniforms();w.uniformsList=gr.seqWithValue(O.seq,w.uniforms)}return w.uniformsList}function wt(w,O){let Q=Y.get(w);Q.outputColorSpace=O.outputColorSpace,Q.batching=O.batching,Q.batchingColor=O.batchingColor,Q.instancing=O.instancing,Q.instancingColor=O.instancingColor,Q.instancingMorph=O.instancingMorph,Q.skinning=O.skinning,Q.morphTargets=O.morphTargets,Q.morphNormals=O.morphNormals,Q.morphColors=O.morphColors,Q.morphTargetsCount=O.morphTargetsCount,Q.numClippingPlanes=O.numClippingPlanes,Q.numIntersection=O.numClipIntersection,Q.vertexAlphas=O.vertexAlphas,Q.vertexTangents=O.vertexTangents,Q.toneMapping=O.toneMapping}function Vt(w,O){if(w.length===0)return null;if(w.length===1)return w[0].texture!==null?w[0]:null;v.setFromMatrixPosition(O.matrixWorld);for(let Q=0,$=w.length;Q<$;Q++){let Z=w[Q];if(Z.texture!==null&&Z.boundingBox.containsPoint(v))return Z}return null}function Kt(w,O,Q,$,Z){O.isScene!==!0&&(O=bt),rt.resetTextureUnits();let Tt=O.fog,kt=$.isMeshStandardMaterial||$.isMeshLambertMaterial||$.isMeshPhongMaterial?O.environment:null,zt=at===null?P.outputColorSpace:at.isXRRenderTarget===!0?at.texture.colorSpace:Me.workingColorSpace,Yt=$.isMeshStandardMaterial||$.isMeshLambertMaterial&&!$.envMap||$.isMeshPhongMaterial&&!$.envMap,Qt=_t.get($.envMap||kt,Yt),pe=$.vertexColors===!0&&!!Q.attributes.color&&Q.attributes.color.itemSize===4,_e=!!Q.attributes.tangent&&(!!$.normalMap||$.anisotropy>0),Jt=!!Q.morphAttributes.position,Pe=!!Q.morphAttributes.normal,Ze=!!Q.morphAttributes.color,Ve=On;$.toneMapped&&(at===null||at.isXRRenderTarget===!0)&&(Ve=P.toneMapping);let ze=Q.morphAttributes.position||Q.morphAttributes.normal||Q.morphAttributes.color,pn=ze!==void 0?ze.length:0,Gt=Y.get($),Mn=M.state.lights;if(tt===!0&&(G===!0||w!==st)){let ke=w===st&&$.id===K;$t.setState($,w,ke)}let Te=!1;$.version===Gt.__version?(Gt.needsLights&&Gt.lightsStateVersion!==Mn.state.version||Gt.outputColorSpace!==zt||Z.isBatchedMesh&&Gt.batching===!1||!Z.isBatchedMesh&&Gt.batching===!0||Z.isBatchedMesh&&Gt.batchingColor===!0&&Z._colorsTexture===null||Z.isBatchedMesh&&Gt.batchingColor===!1&&Z._colorsTexture!==null||Z.isInstancedMesh&&Gt.instancing===!1||!Z.isInstancedMesh&&Gt.instancing===!0||Z.isSkinnedMesh&&Gt.skinning===!1||!Z.isSkinnedMesh&&Gt.skinning===!0||Z.isInstancedMesh&&Gt.instancingColor===!0&&Z.instanceColor===null||Z.isInstancedMesh&&Gt.instancingColor===!1&&Z.instanceColor!==null||Z.isInstancedMesh&&Gt.instancingMorph===!0&&Z.morphTexture===null||Z.isInstancedMesh&&Gt.instancingMorph===!1&&Z.morphTexture!==null||Gt.envMap!==Qt||$.fog===!0&&Gt.fog!==Tt||Gt.numClippingPlanes!==void 0&&(Gt.numClippingPlanes!==$t.numPlanes||Gt.numIntersection!==$t.numIntersection)||Gt.vertexAlphas!==pe||Gt.vertexTangents!==_e||Gt.morphTargets!==Jt||Gt.morphNormals!==Pe||Gt.morphColors!==Ze||Gt.toneMapping!==Ve||Gt.morphTargetsCount!==pn||!!Gt.lightProbeGrid!=M.state.lightProbeGridArray.length>0)&&(Te=!0):(Te=!0,Gt.__version=$.version);let Vn=Gt.currentProgram;Te===!0&&(Vn=J($,O,Z),F&&$.isNodeMaterial&&F.onUpdateProgram($,Vn,Gt));let ui=!1,Vi=!1,Is=!1,Ne=Vn.getUniforms(),Ye=Gt.uniforms;if(S.useProgram(Vn.program)&&(ui=!0,Vi=!0,Is=!0),$.id!==K&&(K=$.id,Vi=!0),Gt.needsLights){let ke=Vt(M.state.lightProbeGridArray,Z);Gt.lightProbeGrid!==ke&&(Gt.lightProbeGrid=ke,Vi=!0)}if(ui||st!==w){S.buffers.depth.getReversed()&&w.reversedDepth!==!0&&(w._reversedDepth=!0,w.updateProjectionMatrix()),Ne.setValue(U,"projectionMatrix",w.projectionMatrix),Ne.setValue(U,"viewMatrix",w.matrixWorldInverse);let Wi=Ne.map.cameraPosition;Wi!==void 0&&Wi.setValue(U,gt.setFromMatrixPosition(w.matrixWorld)),R.logarithmicDepthBuffer&&Ne.setValue(U,"logDepthBufFC",2/(Math.log(w.far+1)/Math.LN2)),($.isMeshPhongMaterial||$.isMeshToonMaterial||$.isMeshLambertMaterial||$.isMeshBasicMaterial||$.isMeshStandardMaterial||$.isShaderMaterial)&&Ne.setValue(U,"isOrthographic",w.isOrthographicCamera===!0),st!==w&&(st=w,Vi=!0,Is=!0)}if(Gt.needsLights&&(Mn.state.sunShadowMap.length>0&&Ne.setValue(U,"sunShadowMap",Mn.state.sunShadowMap,rt),Mn.state.directionalShadowMap.length>0&&Ne.setValue(U,"directionalShadowMap",Mn.state.directionalShadowMap,rt),Mn.state.spotShadowMap.length>0&&Ne.setValue(U,"spotShadowMap",Mn.state.spotShadowMap,rt),Mn.state.pointShadowMap.length>0&&Ne.setValue(U,"pointShadowMap",Mn.state.pointShadowMap,rt)),Z.isSkinnedMesh){Ne.setOptional(U,Z,"bindMatrix"),Ne.setOptional(U,Z,"bindMatrixInverse");let ke=Z.skeleton;ke&&(ke.boneTexture===null&&ke.computeBoneTexture(),Ne.setValue(U,"boneTexture",ke.boneTexture,rt))}Z.isBatchedMesh&&(Ne.setOptional(U,Z,"batchingTexture"),Ne.setValue(U,"batchingTexture",Z._matricesTexture,rt),Ne.setOptional(U,Z,"batchingIdTexture"),Ne.setValue(U,"batchingIdTexture",Z._indirectTexture,rt),Ne.setOptional(U,Z,"batchingColorTexture"),Z._colorsTexture!==null&&Ne.setValue(U,"batchingColorTexture",Z._colorsTexture,rt));let Gi=Q.morphAttributes;if((Gi.position!==void 0||Gi.normal!==void 0||Gi.color!==void 0)&&B.update(Z,Q,Vn),(Vi||Gt.receiveShadow!==Z.receiveShadow)&&(Gt.receiveShadow=Z.receiveShadow,Ne.setValue(U,"receiveShadow",Z.receiveShadow)),($.isMeshStandardMaterial||$.isMeshLambertMaterial||$.isMeshPhongMaterial)&&$.envMap===null&&O.environment!==null&&(Ye.envMapIntensity.value=O.environmentIntensity),Ye.dfgLUT!==void 0&&(Ye.dfgLUT.value=Hx()),Vi){if(Ne.setValue(U,"toneMappingExposure",P.toneMappingExposure),Gt.needsLights&&be(Ye,Is),Tt&&$.fog===!0&&Zt.refreshFogUniforms(Ye,Tt),Zt.refreshMaterialUniforms(Ye,$,k,N,M.state.transmissionRenderTarget[w.id]),Gt.needsLights&&Gt.lightProbeGrid){let ke=Gt.lightProbeGrid;Ye.probesSH.value=ke.texture,Ye.probesMin.value.copy(ke.boundingBox.min),Ye.probesMax.value.copy(ke.boundingBox.max),Ye.probesResolution.value.copy(ke.resolution)}gr.upload(U,ht(Gt),Ye,rt)}if($.isShaderMaterial&&$.uniformsNeedUpdate===!0&&(gr.upload(U,ht(Gt),Ye,rt),$.uniformsNeedUpdate=!1),$.isSpriteMaterial&&Ne.setValue(U,"center",Z.center),Ne.setValue(U,"modelViewMatrix",Z.modelViewMatrix),Ne.setValue(U,"normalMatrix",Z.normalMatrix),Ne.setValue(U,"modelMatrix",Z.matrixWorld),$.uniformsGroups!==void 0){let ke=$.uniformsGroups;for(let Wi=0,Ls=ke.length;Wi<Ls;Wi++){let Bh=ke[Wi];pt.update(Bh,Vn),pt.bind(Bh,Vn)}}return Vn}function be(w,O){w.ambientLightColor.needsUpdate=O,w.lightProbe.needsUpdate=O,w.sunLights.needsUpdate=O,w.sunLightShadows.needsUpdate=O,w.directionalLights.needsUpdate=O,w.directionalLightShadows.needsUpdate=O,w.pointLights.needsUpdate=O,w.pointLightShadows.needsUpdate=O,w.spotLights.needsUpdate=O,w.spotLightShadows.needsUpdate=O,w.rectAreaLights.needsUpdate=O,w.hemisphereLights.needsUpdate=O}function Re(w){return w.isMeshLambertMaterial||w.isMeshToonMaterial||w.isMeshPhongMaterial||w.isMeshStandardMaterial||w.isShadowMaterial||w.isShaderMaterial&&w.lights===!0}this.getActiveCubeFace=function(){return q},this.getActiveMipmapLevel=function(){return j},this.getRenderTarget=function(){return at},this.setRenderTargetTextures=function(w,O,Q){let $=Y.get(w);$.__autoAllocateDepthBuffer=w.resolveDepthBuffer===!1,$.__autoAllocateDepthBuffer===!1&&($.__useRenderToTexture=!1),Y.get(w.texture).__webglTexture=O,Y.get(w.depthTexture).__webglTexture=$.__autoAllocateDepthBuffer?void 0:Q,$.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(w,O){let Q=Y.get(w);Q.__webglFramebuffer=O,Q.__useDefaultFramebuffer=O===void 0},this.setRenderTarget=function(w,O=0,Q=0){at=w,q=O,j=Q;let $=null,Z=!1,Tt=!1;if(w){let zt=Y.get(w);if(zt.__useDefaultFramebuffer!==void 0){S.bindFramebuffer(U.FRAMEBUFFER,zt.__webglFramebuffer),it.copy(w.viewport),Rt.copy(w.scissor),mt=w.scissorTest,S.viewport(it),S.scissor(Rt),S.setScissorTest(mt),K=-1;return}else if(zt.__webglFramebuffer===void 0)rt.setupRenderTarget(w);else if(zt.__hasExternalTextures)rt.rebindTextures(w,Y.get(w.texture).__webglTexture,Y.get(w.depthTexture).__webglTexture);else if(w.depthBuffer){let pe=w.depthTexture;if(zt.__boundDepthTexture!==pe){if(pe!==null&&Y.has(pe)&&(w.width!==pe.image.width||w.height!==pe.image.height))throw new Error("THREE.WebGLRenderer: Attached DepthTexture is initialized to the incorrect size.");rt.setupDepthRenderbuffer(w)}}let Yt=w.texture;(Yt.isData3DTexture||Yt.isDataArrayTexture||Yt.isCompressedArrayTexture)&&(Tt=!0);let Qt=Y.get(w).__webglFramebuffer;w.isWebGLCubeRenderTarget?(Array.isArray(Qt[O])?$=Qt[O][Q]:$=Qt[O],Z=!0):w.samples>0&&rt.useMultisampledRTT(w)===!1?$=Y.get(w).__webglMultisampledFramebuffer:Array.isArray(Qt)?$=Qt[Q]:$=Qt,it.copy(w.viewport),Rt.copy(w.scissor),mt=w.scissorTest}else it.copy(Mt).multiplyScalar(k).floor(),Rt.copy(Ft).multiplyScalar(k).floor(),mt=xt;if(Q!==0&&($=V),S.bindFramebuffer(U.FRAMEBUFFER,$)&&S.drawBuffers(w,$),S.viewport(it),S.scissor(Rt),S.setScissorTest(mt),Z){let zt=Y.get(w.texture);U.framebufferTexture2D(U.FRAMEBUFFER,U.COLOR_ATTACHMENT0,U.TEXTURE_CUBE_MAP_POSITIVE_X+O,zt.__webglTexture,Q)}else if(Tt){let zt=O;for(let Yt=0;Yt<w.textures.length;Yt++){let Qt=Y.get(w.textures[Yt]);U.framebufferTextureLayer(U.FRAMEBUFFER,U.COLOR_ATTACHMENT0+Yt,Qt.__webglTexture,Q,zt)}}else if(w!==null&&Q!==0){let zt=Y.get(w.texture);U.framebufferTexture2D(U.FRAMEBUFFER,U.COLOR_ATTACHMENT0,U.TEXTURE_2D,zt.__webglTexture,Q)}K=-1};function Le(w){let O=Y.get(w);return(O.__readFormat!==w.format||O.__readType!==w.type)&&(O.__readFormat=w.format,O.__readType=w.type,O.__formatReadable=R.textureFormatReadable(w.format),O.__typeReadable=R.textureTypeReadable(w.type)),O}this.readRenderTargetPixels=function(w,O,Q,$,Z,Tt,kt,zt=0){if(!(w&&w.isWebGLRenderTarget)){ae("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let Yt=Y.get(w).__webglFramebuffer;if(w.isWebGLCubeRenderTarget&&kt!==void 0&&(Yt=Yt[kt]),Yt){S.bindFramebuffer(U.FRAMEBUFFER,Yt);try{let Qt=w.textures[zt],pe=Qt.format,_e=Qt.type;w.textures.length>1&&U.readBuffer(U.COLOR_ATTACHMENT0+zt);let Jt=Le(Qt);if(Jt.__formatReadable===!1){ae("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(Jt.__typeReadable===!1){ae("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}O>=0&&O<=w.width-$&&Q>=0&&Q<=w.height-Z&&U.readPixels(O,Q,$,Z,Pt.convert(pe),Pt.convert(_e),Tt)}finally{let Qt=at!==null?Y.get(at).__webglFramebuffer:null;S.bindFramebuffer(U.FRAMEBUFFER,Qt)}}},this.readRenderTargetPixelsAsync=async function(w,O,Q,$,Z,Tt,kt,zt=0){if(!(w&&w.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let Yt=Y.get(w).__webglFramebuffer;if(w.isWebGLCubeRenderTarget&&kt!==void 0&&(Yt=Yt[kt]),Yt)if(O>=0&&O<=w.width-$&&Q>=0&&Q<=w.height-Z){S.bindFramebuffer(U.FRAMEBUFFER,Yt);let Qt=w.textures[zt],pe=Qt.format,_e=Qt.type;w.textures.length>1&&U.readBuffer(U.COLOR_ATTACHMENT0+zt);let Jt=Le(Qt);if(Jt.__formatReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(Jt.__typeReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let Pe=U.createBuffer();U.bindBuffer(U.PIXEL_PACK_BUFFER,Pe),U.bufferData(U.PIXEL_PACK_BUFFER,Tt.byteLength,U.STREAM_READ),U.readPixels(O,Q,$,Z,Pt.convert(pe),Pt.convert(_e),0),U.bindBuffer(U.PIXEL_PACK_BUFFER,null);let Ze=at!==null?Y.get(at).__webglFramebuffer:null;S.bindFramebuffer(U.FRAMEBUFFER,Ze);let Ve=U.fenceSync(U.SYNC_GPU_COMMANDS_COMPLETE,0);return U.flush(),await ed(U,Ve,4),U.bindBuffer(U.PIXEL_PACK_BUFFER,Pe),U.getBufferSubData(U.PIXEL_PACK_BUFFER,0,Tt),U.bindBuffer(U.PIXEL_PACK_BUFFER,null),U.deleteBuffer(Pe),U.deleteSync(Ve),Tt}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(w,O=null,Q=0){let $=Math.pow(2,-Q),Z=Math.floor(w.image.width*$),Tt=Math.floor(w.image.height*$),kt=O!==null?O.x:0,zt=O!==null?O.y:0;rt.setTexture2D(w,0),U.copyTexSubImage2D(U.TEXTURE_2D,Q,0,0,kt,zt,Z,Tt),S.unbindTexture()},this.copyTextureToTexture=function(w,O,Q=null,$=null,Z=0,Tt=0){let kt,zt,Yt,Qt,pe,_e,Jt,Pe,Ze,Ve=w.isCompressedTexture?w.mipmaps[Tt]:w.image;if(Q!==null)kt=Q.max.x-Q.min.x,zt=Q.max.y-Q.min.y,Yt=Q.isBox3?Q.max.z-Q.min.z:1,Qt=Q.min.x,pe=Q.min.y,_e=Q.isBox3?Q.min.z:0;else{let Ye=Math.pow(2,-Z);kt=Math.floor(Ve.width*Ye),zt=Math.floor(Ve.height*Ye),w.isDataArrayTexture?Yt=Ve.depth:w.isData3DTexture?Yt=Math.floor(Ve.depth*Ye):Yt=1,Qt=0,pe=0,_e=0}$!==null?(Jt=$.x,Pe=$.y,Ze=$.z):(Jt=0,Pe=0,Ze=0);let ze=Pt.convert(O.format),pn=Pt.convert(O.type),Gt;O.isData3DTexture?(rt.setTexture3D(O,0),Gt=U.TEXTURE_3D):O.isDataArrayTexture||O.isCompressedArrayTexture?(rt.setTexture2DArray(O,0),Gt=U.TEXTURE_2D_ARRAY):(rt.setTexture2D(O,0),Gt=U.TEXTURE_2D),S.activeTexture(U.TEXTURE0),S.pixelStorei(U.UNPACK_FLIP_Y_WEBGL,O.flipY),S.pixelStorei(U.UNPACK_PREMULTIPLY_ALPHA_WEBGL,O.premultiplyAlpha),S.pixelStorei(U.UNPACK_ALIGNMENT,O.unpackAlignment);let Mn=S.getParameter(U.UNPACK_ROW_LENGTH),Te=S.getParameter(U.UNPACK_IMAGE_HEIGHT),Vn=S.getParameter(U.UNPACK_SKIP_PIXELS),ui=S.getParameter(U.UNPACK_SKIP_ROWS),Vi=S.getParameter(U.UNPACK_SKIP_IMAGES);S.pixelStorei(U.UNPACK_ROW_LENGTH,Ve.width),S.pixelStorei(U.UNPACK_IMAGE_HEIGHT,Ve.height),S.pixelStorei(U.UNPACK_SKIP_PIXELS,Qt),S.pixelStorei(U.UNPACK_SKIP_ROWS,pe),S.pixelStorei(U.UNPACK_SKIP_IMAGES,_e);let Is=w.isDataArrayTexture||w.isData3DTexture,Ne=O.isDataArrayTexture||O.isData3DTexture;if(w.isDepthTexture){let Ye=Y.get(w),Gi=Y.get(O),ke=Y.get(Ye.__renderTarget),Wi=Y.get(Gi.__renderTarget);S.bindFramebuffer(U.READ_FRAMEBUFFER,ke.__webglFramebuffer),S.bindFramebuffer(U.DRAW_FRAMEBUFFER,Wi.__webglFramebuffer);for(let Ls=0;Ls<Yt;Ls++)Is&&(U.framebufferTextureLayer(U.READ_FRAMEBUFFER,U.COLOR_ATTACHMENT0,Y.get(w).__webglTexture,Z,_e+Ls),U.framebufferTextureLayer(U.DRAW_FRAMEBUFFER,U.COLOR_ATTACHMENT0,Y.get(O).__webglTexture,Tt,Ze+Ls)),U.blitFramebuffer(Qt,pe,kt,zt,Jt,Pe,kt,zt,U.DEPTH_BUFFER_BIT,U.NEAREST);S.bindFramebuffer(U.READ_FRAMEBUFFER,null),S.bindFramebuffer(U.DRAW_FRAMEBUFFER,null)}else if(Z!==0||w.isRenderTargetTexture||Y.has(w)){let Ye=Y.get(w),Gi=Y.get(O);S.bindFramebuffer(U.READ_FRAMEBUFFER,I),S.bindFramebuffer(U.DRAW_FRAMEBUFFER,z);for(let ke=0;ke<Yt;ke++)Is?U.framebufferTextureLayer(U.READ_FRAMEBUFFER,U.COLOR_ATTACHMENT0,Ye.__webglTexture,Z,_e+ke):U.framebufferTexture2D(U.READ_FRAMEBUFFER,U.COLOR_ATTACHMENT0,U.TEXTURE_2D,Ye.__webglTexture,Z),Ne?U.framebufferTextureLayer(U.DRAW_FRAMEBUFFER,U.COLOR_ATTACHMENT0,Gi.__webglTexture,Tt,Ze+ke):U.framebufferTexture2D(U.DRAW_FRAMEBUFFER,U.COLOR_ATTACHMENT0,U.TEXTURE_2D,Gi.__webglTexture,Tt),Z!==0?U.blitFramebuffer(Qt,pe,kt,zt,Jt,Pe,kt,zt,U.COLOR_BUFFER_BIT,U.NEAREST):Ne?U.copyTexSubImage3D(Gt,Tt,Jt,Pe,Ze+ke,Qt,pe,kt,zt):U.copyTexSubImage2D(Gt,Tt,Jt,Pe,Qt,pe,kt,zt);S.bindFramebuffer(U.READ_FRAMEBUFFER,null),S.bindFramebuffer(U.DRAW_FRAMEBUFFER,null)}else Ne?w.isDataTexture||w.isData3DTexture?U.texSubImage3D(Gt,Tt,Jt,Pe,Ze,kt,zt,Yt,ze,pn,Ve.data):O.isCompressedArrayTexture?U.compressedTexSubImage3D(Gt,Tt,Jt,Pe,Ze,kt,zt,Yt,ze,Ve.data):U.texSubImage3D(Gt,Tt,Jt,Pe,Ze,kt,zt,Yt,ze,pn,Ve):w.isDataTexture?U.texSubImage2D(U.TEXTURE_2D,Tt,Jt,Pe,kt,zt,ze,pn,Ve.data):w.isCompressedTexture?U.compressedTexSubImage2D(U.TEXTURE_2D,Tt,Jt,Pe,Ve.width,Ve.height,ze,Ve.data):U.texSubImage2D(U.TEXTURE_2D,Tt,Jt,Pe,kt,zt,ze,pn,Ve);S.pixelStorei(U.UNPACK_ROW_LENGTH,Mn),S.pixelStorei(U.UNPACK_IMAGE_HEIGHT,Te),S.pixelStorei(U.UNPACK_SKIP_PIXELS,Vn),S.pixelStorei(U.UNPACK_SKIP_ROWS,ui),S.pixelStorei(U.UNPACK_SKIP_IMAGES,Vi),Tt===0&&O.generateMipmaps&&U.generateMipmap(Gt),S.unbindTexture()},this.initRenderTarget=function(w){Y.get(w).__webglFramebuffer===void 0&&rt.setupRenderTarget(w)},this.initTexture=function(w){w.isCubeTexture?rt.setTextureCube(w,0):w.isData3DTexture?rt.setTexture3D(w,0):w.isDataArrayTexture||w.isCompressedArrayTexture?rt.setTexture2DArray(w,0):rt.setTexture2D(w,0),S.unbindTexture()},this.resetState=function(){q=0,j=0,at=null,S.reset(),yt.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return si}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(t){this._outputColorSpace=t;let e=this.getContext();e.drawingBufferColorSpace=Me._getDrawingBufferColorSpace(t),e.unpackColorSpace=Me._getUnpackColorSpace()}};var Be=(i,t=0,e=1)=>Math.min(e,Math.max(t,i)),fe=(i,t,e)=>i+(t-i)*e,Se=(i,t,e)=>{let n=Be((e-i)/(t-i));return n*n*(3-2*n)},Od=(i,t,e)=>{let n=Be((e-i)/(t-i));return n*n*n*(n*(n*6-15)+10)},Rn=(i,t,e,n,s)=>Se(t,e,i)*(1-Se(n,s,i));function _n(i=1){let t=i>>>0;return()=>{t=t+1831565813>>>0;let e=t;return e=Math.imul(e^e>>>15,e|1),e^=e+Math.imul(e^e>>>7,e|61),((e^e>>>14)>>>0)/4294967296}}function jn(i=7){let t=new Uint8Array(512),e=_n(i),n=[...Array(256).keys()];for(let a=255;a>0;a--){let o=Math.floor(e()*(a+1));[n[a],n[o]]=[n[o],n[a]]}for(let a=0;a<512;a++)t[a]=n[a&255];let s=new Float32Array(256).map(()=>e()*2-1),r=a=>a*a*a*(a*(a*6-15)+10);return(a,o)=>{let c=Math.floor(a),l=Math.floor(o),u=a-c,d=o-l,h=c&255,f=l&255,g=s[t[t[h]+f]],x=s[t[t[h+1]+f]],p=s[t[t[h]+f+1]],m=s[t[t[h+1]+f+1]],y=r(u),E=r(d);return fe(fe(g,x,y),fe(p,m,y),E)}}function Cn(i,t,e,n=4,s=2,r=.5){let a=0,o=1,c=0;for(let l=0;l<n;l++)a+=i(t,e)*o,c+=o,t*=s,e*=s,o*=r;return a/c}function He(i,t){let e=document.createElement("canvas");return e.width=i,e.height=t,[e,e.getContext("2d")]}function qe(i,{srgb:t=!0,ponavljaj:e=!1,aniz:n=8}={}){let s=new jr(i);return t&&(s.colorSpace=bn),e&&(s.wrapS=s.wrapT=Js),s.anisotropy=n,s}function Aa(i,t=2){let e=i.width,n=i.height,s=i.getContext("2d").getImageData(0,0,e,n).data,[r,a]=He(e,n),o=a.createImageData(e,n),c=new Float64Array(e*n);for(let u=0;u<e*n;u++)c[u]=s[u*4]/255;let l=o.data;for(let u=0;u<n;u++){let d=(u-1+n)%n*e,h=u*e,f=(u+1)%n*e;for(let g=0;g<e;g++){let x=(g-1+e)%e,p=(g+1)%e,m=c[d+p]+2*c[h+p]+c[f+p]-(c[d+x]+2*c[h+x]+c[f+x]),y=c[f+x]+2*c[f+g]+c[f+p]-(c[d+x]+2*c[d+g]+c[d+p]),E=-m*t,v=y*t,b=1/Math.sqrt(E*E+v*v+1),M=(h+g)*4;l[M]=(E*b*.5+.5)*255,l[M+1]=(v*b*.5+.5)*255,l[M+2]=(b*.5+.5)*255,l[M+3]=255}}return a.putImageData(o,0,0),r}function re(i,t,e,n=.02,s=2){let r=new Ce(i,t,e,1,1,1);return n<=0?r:Vx(i,t,e,n,s)}function Vx(i,t,e,n,s){let r=new Ce(i,t,e,s*2+1,s*2+1,s*2+1),a=r.attributes.position,o=new C,c=new C,l=i/2-n,u=t/2-n,d=e/2-n;for(let h=0;h<a.count;h++){o.fromBufferAttribute(a,h),c.set(Be(o.x,-l,l),Be(o.y,-u,u),Be(o.z,-d,d));let f=o.clone().sub(c);f.lengthSq()>1e-12&&o.copy(c).add(f.normalize().multiplyScalar(n)),a.setXYZ(h,o.x,o.y,o.z)}return r.computeVertexNormals(),r}function We(i){let t=[];for(let[s,r,a]of i){let o=s.index?s.toNonIndexed():s.clone();a&&o.applyMatrix4(a);let c=o.attributes.position.count,l=new Float32Array(c*3),u=new Wt(r);for(let d=0;d<c;d++)l.set([u.r,u.g,u.b],d*3);o.setAttribute("color",new Ue(l,3));for(let d of Object.keys(o.attributes))["position","normal","color","uv"].includes(d)||o.deleteAttribute(d);o.attributes.uv||o.setAttribute("uv",new Ue(new Float32Array(c*2),2)),t.push(o)}let e=t.reduce((s,r)=>s+r.attributes.position.count,0),n=new ge;for(let[s,r]of[["position",3],["normal",3],["color",3],["uv",2]]){let a=new Float32Array(e*r),o=0;for(let c of t)a.set(c.attributes[s].array,o),o+=c.attributes[s].array.length;n.setAttribute(s,new Ue(a,r))}return n}function Oc(i,t){let e=i.attributes.position,n=i.index,s=new C;return t.map(([r,a])=>{let o=new ge;for(let[d,h]of Object.entries(i.attributes))o.setAttribute(d,h);o.setIndex(n),o.setDrawRange(r,a-r);let c=new an;for(let d=r;d<a;d++)c.expandByPoint(s.fromBufferAttribute(e,n.getX(d)));let l=c.getCenter(new C),u=0;for(let d=r;d<a;d++)u=Math.max(u,l.distanceToSquared(s.fromBufferAttribute(e,n.getX(d))));return o.boundingBox=c,o.boundingSphere=new wn(l,Math.sqrt(u)),o})}var qt=(i=0,t=0,e=0,n=0,s=0,r=0,a=1)=>{let o=new de;return o.compose(new C(i,t,e),new sn().setFromEuler(new ri(n,s,r)),new C(a,a,a)),o};function Bc(i){let t=i.length,e=i[0].v.length,n=i.map((s,r)=>{if(s.mir)return new Array(e).fill(0);let a=i[Math.max(0,r-1)],o=i[Math.min(t-1,r+1)],c=o.t-a.t||1;return s.v.map((l,u)=>{let d=(o.v[u]-a.v[u])/c;if(r===0||r===t-1)return d;let h=(s.v[u]-a.v[u])/(s.t-a.t||1),f=(o.v[u]-s.v[u])/(o.t-s.t||1);if(h*f<=0)return 0;let g=3*Math.min(Math.abs(h),Math.abs(f));return Math.sign(d)*Math.min(Math.abs(d),g)})});return(s,r=new Array(e))=>{if(s<=i[0].t){for(let m=0;m<e;m++)r[m]=i[0].v[m];return r}if(s>=i[t-1].t){for(let m=0;m<e;m++)r[m]=i[t-1].v[m];return r}let a=0;for(;i[a+1].t<s;)a++;let o=i[a],c=i[a+1],l=c.t-o.t,u=(s-o.t)/l,d=u*u,h=d*u,f=2*h-3*d+1,g=h-2*d+u,x=-2*h+3*d,p=h-d;for(let m=0;m<e;m++)r[m]=f*o.v[m]+g*l*n[a][m]+x*c.v[m]+p*l*n[a+1][m];return r}}var Ah=`
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
`,Rh=Ah,kc={zora:{sonceVis:6.5,sonceAz:104,zenit:"#6f93c4",obzorje:"#e7c9ae",sij:"#ffb36b",soncBarva:"#ffd9a8",sonceI:2.7,sonceC:"#ffc890",nebI:.62,nebZg:"#a9c4e6",nebSp:"#6e6252",meglaGost:.0019,meglaVis:.022,meglaY0:0,meglaMax:.97,oblaki:.42,zvezde:0,izp:1,okolje:.65},jutro:{sonceVis:12,sonceAz:112,zenit:"#5d8cc8",obzorje:"#dcd6cc",sij:"#ffd29a",soncBarva:"#fff0d8",sonceI:2.9,sonceC:"#ffe4bf",nebI:.7,nebZg:"#b5cdea",nebSp:"#6f6a5c",meglaGost:9e-4,meglaVis:.012,meglaY0:0,meglaMax:.95,oblaki:.38,zvezde:0,izp:1,okolje:.75},noc:{sonceVis:28,sonceAz:210,zenit:"#050a16",obzorje:"#17233a",sij:"#30486e",soncBarva:"#9fb4d8",sonceI:.38,sonceC:"#9db6e8",nebI:.24,nebZg:"#2a3c62",nebSp:"#0c0e12",meglaGost:.0014,meglaVis:.016,meglaY0:0,meglaMax:.9,oblaki:.2,zvezde:1,izp:1.15,okolje:.35}},Bd=new Wt,kd=new Wt;function Hd(i,t,e){let n={};for(let s of Object.keys(i))typeof i[s]=="string"?(Bd.set(i[s]),kd.set(t[s]),n[s]=Bd.clone().lerp(kd,e)):n[s]=fe(i[s],t[s],e);return n}var Hc=class{constructor(){this.U={uSonce:{value:new C(0,.1,1)},uZenit:{value:new Wt},uObzorje:{value:new Wt},uSij:{value:new Wt},uSoncBarva:{value:new Wt},uMeglaGost:{value:.002},uMeglaVis:{value:.02},uMeglaY0:{value:0},uMeglaMax:{value:1},uOblaki:{value:.4},uCasN:{value:0},uZvezde:{value:0}};let t=new Oe({uniforms:this.U,vertexShader:`
        varying vec3 vSmer;
        void main() {
          vSmer = normalize((modelMatrix * vec4(position, 0.0)).xyz);
          vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          gl_Position = p.xyww;
        }`,fragmentShader:Ah+`
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
        }`,side:on,depthWrite:!1,depthTest:!0});this.kupola=new ct(new Xn(1,48,24),t),this.kupola.scale.setScalar(9e3),this.kupola.frustumCulled=!1,this.kupola.renderOrder=-1e3,this.sonce=new ua("#fff",2),this.sonce.castShadow=!0,this.sonce.shadow.bias=-3e-4,this.sonce.shadow.normalBias=.03,this.nebesna=new oa("#bcd","#554",.6),this.stanje=null}popravi(t){if(t.userData.atm||!("fog"in t)||t.isShaderMaterial)return;t.userData.atm=!0;let e=t.onBeforeCompile,n=this.U;t.onBeforeCompile=(r,a)=>{e&&e.call(t,r,a),Object.assign(r.uniforms,n),r.vertexShader=r.vertexShader.replace("#include <fog_pars_vertex>",`#include <fog_pars_vertex>
varying vec3 vAtmPog;`).replace("#include <fog_vertex>",`#include <fog_vertex>
vAtmPog = mvPosition.xyz;`),r.fragmentShader=r.fragmentShader.replace("#include <fog_pars_fragment>",`#include <fog_pars_fragment>
varying vec3 vAtmPog;
`+Ah).replace("#include <fog_fragment>",`#ifdef USE_FOG
 gl_FragColor.rgb = atmosfera(gl_FragColor.rgb, cameraPosition, (vec4(vAtmPog, 0.0) * viewMatrix).xyz);
#endif`)};let s=t.customProgramCacheKey.bind(t);t.customProgramCacheKey=()=>s()+"|atm",t.needsUpdate=!0}nastavi(t,e=null,n=0){let s=e?Hd(kc[t],kc[e],n):Hd(kc[t],kc[t],0),r=this.U,a=Mi.degToRad(s.sonceVis),o=Mi.degToRad(s.sonceAz);return r.uSonce.value.set(Math.sin(o)*Math.cos(a),Math.sin(a),-Math.cos(o)*Math.cos(a)),r.uZenit.value.copy(s.zenit),r.uObzorje.value.copy(s.obzorje),r.uSij.value.copy(s.sij),r.uSoncBarva.value.copy(s.soncBarva),r.uMeglaGost.value=s.meglaGost,r.uMeglaVis.value=s.meglaVis,r.uMeglaY0.value=s.meglaY0,r.uMeglaMax.value=s.meglaMax,r.uOblaki.value=s.oblaki,r.uZvezde.value=s.zvezde,this.sonce.color.copy(s.sonceC),this.sonce.intensity=s.sonceI,this.nebesna.color.copy(s.nebZg),this.nebesna.groundColor.copy(s.nebSp),this.nebesna.intensity=s.nebI,this.stanje=s,s}okolje(t){let e=new zi,n=this.kupola.clone();n.scale.setScalar(100),e.add(n);let s=new ct(new gi(90,32),new oi({color:this.U.uObzorje.value.clone().multiplyScalar(.35)}));s.rotation.x=-Math.PI/2,s.position.y=-2,e.add(s);let r=new vr(t),a=t.toneMapping;t.toneMapping=On;let o=r.fromScene(e,0,.1,400);return t.toneMapping=a,r.dispose(),o.texture}};var Vd=.7175,Gx=[[1400,0],[900,0],[500,0],[250,0],[0,0],[-250,0],[-480,0],[-800,-25],[-1150,-120],[-1550,-190],[-1950,-170],[-2350,-80],[-2750,-15],[-3050,0],[-3300,0],[-3600,0],[-4e3,0]];function Wd(){let i=new Qi(Gx.map(([f,g])=>new C(f,0,g)),!1,"centripetal");i.arcLengthDivisions=4e3;let t=i.getLength(),e=4e3,n=[],s=[];for(let f=0;f<=e;f++){let g=f/e;n.push(i.getPointAt(g)),s.push(i.getTangentAt(g))}let r=(f,g=new C)=>{let x=Math.min(Math.max(f/t,0),1)*e,p=Math.min(Math.floor(x),e-1),m=x-p;return g.lerpVectors(n[p],n[p+1],m)},a=(f,g=new C)=>{let x=Math.min(Math.max(f/t,0),1)*e,p=Math.min(Math.floor(x),e-1),m=x-p;return g.lerpVectors(s[p],s[p+1],m).normalize()},o=f=>{let g=0,x=t;for(let p=0;p<40;p++){let m=(g+x)/2;r(m).x>f?g=m:x=m}return(g+x)/2},c=-4e3,l=1400,u=2,d=new Float32Array(Math.round((l-c)/u)+1);for(let f=0;f<d.length;f++)d[f]=r(o(c+f*u)).z;return{L:t,tocka:r,smer:a,sPriX:o,zPriX:f=>{let g=(Math.min(Math.max(f,c),l)-c)/u,x=Math.min(Math.floor(g),d.length-2),p=g-x;return d[x]*(1-p)+d[x+1]*p},krivulja:i}}var Ch=new C(0,1,0);function Ph(i,t=new C){return t.crossVectors(i,Ch).normalize()}function Wx(){let i=jn(11),t=_n(5),e=256,[n,s]=He(e,e),r=s.createImageData(e,e),a=[...Array(260)].map(()=>[t()*e,t()*e,.55+t()*.45,t()]),o=16,c=3*e/o,l=a.length*5,u=new Float64Array(l),d=new Float64Array(l),h=new Float64Array(l),f=new Float64Array(l),g=0;for(let[v,b,M,A]of a)for(let[_,T]of[[0,0],[e,0],[-e,0],[0,e],[0,-e]])u[g]=v+_,d[g]=b+T,h[g]=M,f[g]=A,g++;let x=v=>Math.floor((d[v]+e)/o)*c+Math.floor((u[v]+e)/o),p=new Int32Array(c*c+1);for(let v=0;v<l;v++)p[x(v)+1]++;for(let v=0;v<c*c;v++)p[v+1]+=p[v];let m=new Int32Array(l),y=p.slice(0,c*c);for(let v=0;v<l;v++)m[y[x(v)]++]=v;for(let v=0;v<e;v++)for(let b=0;b<e;b++){let M=1e9,A=1e9,_=0,T=0,P=Math.floor((b+e)/o),L=Math.floor((v+e)/o);for(let q=0;q<c;q++){for(let j=Math.max(0,L-q);j<=Math.min(c-1,L+q);j++){let at=j===L-q||j===L+q?1:2*q;for(let K=P-q;K<=P+q;K+=at)if(!(K<0||K>=c))for(let st=p[j*c+K],it=p[j*c+K+1];st<it;st++){let Rt=m[st],mt=(b-u[Rt])**2+(v-d[Rt])**2;mt<M?(A=M,M=mt,_=h[Rt],T=f[Rt]):mt<A&&(A=mt)}}if(A<=(q*o)**2)break}let F=Math.sqrt(A)-Math.sqrt(M),V=Math.min(1,F/5)*_*(.85+.15*Cn(i,b/9,v/9,3)),I=(v*e+b)*4,z=T>.8?1:0;r.data[I]=(118+40*z)*V+18,r.data[I+1]=(114+22*z)*V+17,r.data[I+2]=(108+4*z)*V+16,r.data[I+3]=255}s.putImageData(r,0,0);let E=Aa(n,3);return{barva:qe(n,{ponavljaj:!0}),normala:qe(E,{srgb:!1,ponavljaj:!0})}}function Gd(i,t,e,n,s,r=0,a=1){let o=[],c=[],l=[],u=new C,d=new C,h=new C,f=Math.ceil((e-t)/n),g=s.length;for(let p=0;p<=f;p++){let m=t+(e-t)*p/f;i.tocka(m,u),i.smer(m,d),Ph(d,h);for(let[y,E,v]of s)o.push(u.x+h.x*(y+r),E,u.z+h.z*(y+r)),c.push(m/a,v);if(p<f)for(let y=0;y<g-1;y++){let E=p*g+y,v=E+g;l.push(E,v,E+1,E+1,v,v+1)}}let x=new ge;return x.setAttribute("position",new te(o,3)),x.setAttribute("uv",new te(c,2)),x.setIndex(l),x.computeVertexNormals(),x}function Xd(i,{atmU:t,NEBO:e}={}){let n=new oe,s=i.L,r=Wx();r.barva.repeat.set(1,1);let a=Gd(i,0,s,2,[[-3.4,-.85,0],[-2,-.22,.32],[2,-.22,.68],[3.4,-.85,1]],0,4),o=new Ot({map:r.barva,normalMap:r.normala,normalScale:new vt(1.2,1.2),roughness:.95,color:"#c9c4bc"});o.map.repeat.set(1,3),o.normalMap.repeat.set(1,3);let c=new ct(a,o);c.receiveShadow=!0,n.add(c);let l=[[-.075,-.17,0],[.075,-.17,.1],[.075,-.155,.2],[.012,-.14,.3],[.01,-.04,.4],[.036,-.03,.5],[.036,-.004,.6],[.026,0,.7],[-.026,0,.8],[-.036,-.004,.9],[-.036,-.03,.92],[-.01,-.04,.94],[-.012,-.14,.96],[-.075,-.155,.98],[-.075,-.17,1]],u=new Ot({color:"#7d6a5a",metalness:.75,roughness:.42});u.onBeforeCompile=xt=>{xt.fragmentShader=xt.fragmentShader.replace("#include <color_fragment>",`#include <color_fragment>
        float _vrh = smoothstep(0.86, 0.97, dot(normalize(vNormal), normalize((viewMatrix * vec4(0.0, 1.0, 0.0, 0.0)).xyz)))
                   * (1.0 - smoothstep(35.0, 140.0, length(vViewPosition)));
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.74, 0.75, 0.77), _vrh);`).replace("#include <roughnessmap_fragment>",`#include <roughnessmap_fragment>
float _dal = smoothstep(30.0, 150.0, length(vViewPosition));
roughnessFactor = mix(mix(roughnessFactor, 0.2, _vrh), 0.8, _dal);`).replace("#include <metalnessmap_fragment>",`#include <metalnessmap_fragment>
metalnessFactor = mix(mix(metalnessFactor, 1.0, _vrh), 0.3, _dal);`)},u.customProgramCacheKey=()=>"tirnica",u.polygonOffset=!0,u.polygonOffsetFactor=-2,u.polygonOffsetUnits=-2;for(let xt of[-Vd,Vd]){let X=Gd(i,0,s,2,l.map(([gt,Bt,bt])=>[gt+xt,Bt,bt]),0,1),tt=6*(l.length-1),G=X.index.count/tt,et=[];for(let gt=0;gt<G;gt+=150)et.push([gt*tt,Math.min(gt+150,G)*tt]);for(let gt of Oc(X,et)){let Bt=new ct(gt,u);Bt.castShadow=!1,Bt.receiveShadow=!0,n.add(Bt)}}let d=re(.26,.19,2.6,.02),h=new Ce(.26,.19,2.6),f=new Ot({color:"#a7a39b",roughness:.9});f.onBeforeCompile=xt=>{xt.fragmentShader=xt.fragmentShader.replace("#include <color_fragment>",`#include <color_fragment>
diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.45, 0.43, 0.4), smoothstep(25.0, 110.0, length(vViewPosition)));`)},f.customProgramCacheKey=()=>"prag",f.polygonOffset=!0,f.polygonOffsetFactor=-1,f.polygonOffsetUnits=-1;let g=300,x=new de,p=new sn,m=new C,y=new C,E=_n(3),v=[],b=[],M=[],A=[];for(let xt=0;xt<s;xt+=g){let X=Math.floor(Math.min(g,s-xt)/.6),tt=new Tn(h,f,X);for(let G=0;G<X;G++){let et=xt+G*.6;i.tocka(et,m),i.smer(et,y),p.setFromAxisAngle(Ch,Math.atan2(-y.z,y.x)+(E()-.5)*.01),m.y=-.24,x.compose(m,p,new C(1,1,1)),tt.setMatrixAt(G,x),b.push(et),M.push([v.length,G]),A.push(...x.elements)}tt.receiveShadow=!0,tt.computeBoundingSphere(),n.add(tt),v.push(tt)}let _=40,T=Math.ceil(2*_/.6)+2,P=new Tn(d,f,T);P.receiveShadow=!0,P.frustumCulled=!1,P.visible=!1,n.add(P);let L=new Float32Array(A),F=new Float32Array(16),V=xt=>{let X=0,tt=b.length;for(;X<tt;){let G=X+tt>>1;b[G]<xt?X=G+1:tt=G}return X},I=0,z=0,q=new C;function j(xt){let X=i.sPriX(xt.x);i.tocka(X,q).setY(-.24);let tt=xt.distanceTo(q),G=0,et=0;if(tt<_){let bt=Math.sqrt(_*_-tt*tt);G=V(X-bt),et=Math.min(V(X+bt),G+T)}if(G===I&&et===z)return;let gt=new Set,Bt=(bt,jt)=>{let[ne,U]=M[bt];v[ne].instanceMatrix.array.set(jt,U*16),gt.add(ne)};for(let bt=I;bt<z;bt++)(bt<G||bt>=et)&&Bt(bt,L.subarray(bt*16,bt*16+16));for(let bt=G;bt<et;bt++)(bt<I||bt>=z)&&Bt(bt,F);for(let bt of gt)v[bt].instanceMatrix.needsUpdate=!0;P.instanceMatrix.array.set(L.subarray(G*16,et*16)),P.instanceMatrix.needsUpdate=!0,P.count=et-G,P.visible=et>G,I=G,z=et}let at=55,K=Math.atan2(.7,3.4),st=We([[re(.22,8.2,.22,.01),"#8e9496",qt(0,4.1,0)],[re(.5,.25,.5,.02),"#7f8486",qt(0,.1,0)],[new ve(.035,.035,3.6,6),"#7c8183",qt(0,7.8,1.7,Math.PI/2,0,0)],[new ve(.04,.04,Math.hypot(3.4,.7),6),"#7c8183",qt(0,7.15,1.7,Math.PI/2-K,0,0)],[new ve(.025,.025,.93,6),"#7c8183",qt(0,6.865,2.6)],[new ve(.018,.018,.95,6),"#7c8183",qt(0,6.33,3.075,Math.PI/2,0,0)],[new ve(.05,.05,.4,8),"#a5462f",qt(0,7.8,.35,Math.PI/2,0,0)],[new ve(.05,.05,.35,8),"#a5462f",qt(0,6.87,.35,Math.PI/2-K,0,0)]]),it=new Ot({vertexColors:!0,roughness:.6,metalness:.5}),Rt=Math.floor((s-20)/at),mt=new Tn(st,it,Rt),Ut=new C;for(let xt=0;xt<Rt;xt++){let X=xt*at+10;i.tocka(X,m),i.smer(X,y),Ph(y,Ut);let tt=m.clone().addScaledVector(Ut,3.3);tt.y=-.8,p.setFromAxisAngle(Ch,Math.atan2(-y.z,y.x)+Math.PI),x.compose(tt,p,new C(1,1,1)),mt.setMatrixAt(xt,x)}mt.castShadow=!0,mt.computeBoundingSphere(),n.add(mt);let Dt=5.5,ft=6.62,N=[],k=(xt,X,tt)=>(i.tocka(xt,m),i.smer(xt,y),Ph(y,Ut),m.clone().addScaledVector(Ut,X).setY(tt)),dt=xt=>{let X=(xt-10)/at;return .2*(1-2*Math.abs(X%2-1))},St=xt=>{let X=(xt-10)/at%1;return ft-.5*4*X*(1-X)},Mt=3;for(let xt=10;xt<10+(Rt-1)*at-1e-6;xt+=Mt){let X=Math.min(xt+Mt,10+(Rt-1)*at);N.push(k(xt,dt(xt),Dt),k(X,dt(X),Dt));let tt=(xt-10)/at%1,G=Math.abs((X-10)/at%1)<1e-6?ft:St(X);N.push(k(xt,dt(xt)*.3,tt<1e-6?ft:St(xt)),k(X,dt(X)*.3,G))}for(let xt=10+4.5;xt<10+(Rt-1)*at;xt+=9)N.push(k(xt,dt(xt),Dt),k(xt,dt(xt)*.3,St(xt)));let Ft=Xx(N,t,e);return n.add(Ft),{skupina:n,VOD_Y:Dt,zice:Ft,pragoviBlizu:j}}function Xx(i,t,e){let n=i.length/2,s=new Float32Array(n*4*3),r=new Float32Array(n*4*3),a=new Float32Array(n*4*2),o=new Uint32Array(n*6);for(let d=0;d<n;d++){let h=i[2*d],f=i[2*d+1];for(let g=0;g<4;g++){let x=(d*4+g)*3;s.set([h.x,h.y,h.z],x),r.set([f.x,f.y,f.z],x),a.set([g>>1,g&1?1:-1],(d*4+g)*2)}o.set([d*4,d*4+2,d*4+1,d*4+1,d*4+2,d*4+3],d*6)}let c=new ge;c.setAttribute("position",new Ue(s,3)),c.setAttribute("aB",new Ue(r,3)),c.setAttribute("aK",new Ue(a,2)),c.setIndex(new Ue(o,1));let l=new Oe({uniforms:{...t,uLoc:{value:new vt(1e3,1e3)},uSir:{value:.014},uBarva:{value:new Wt("#2c2824")}},vertexShader:`
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
      }`,transparent:!0,depthWrite:!1}),u=new ct(c,l);return u.frustumCulled=!1,u.renderOrder=2,u}var Fe={sir:1.4,Lc:27,Lv:26,rega:.9,aVozF:5.1,rVoz:2.85,medOsjem:2.4,rKolo:.46};Fe.dolzina=Fe.Lc*2+Fe.Lv+Fe.rega*2;var As={modra:"#1a9be6",bela:"#e8e6df",streha:"#3d4247",crna:"#0b0d10",steklo:"#0b1117",temna:"#23272b"},Ae={pasSp:[.93,1.11],crn:[1.11,2.5],okSp:[1.13,1.76],pasZg:[2.5,2.68],okZg:[2.86,3.8],vrata:[.45,2.48],okV:[1.14,2.09],okVm:[1.74,2.45],streha:4.34},Ca={z:.64,y0:.45,y1:1.33,glob:.86},Vc=.3,qx=[.45,.645,.93,1.11,1.125,1.3,1.33,1.42,1.565,1.63,1.7,1.72,1.9,2.07,2.2,2.31,2.38,2.5,2.68,2.75],Yx=[2.86,3.15,3.45,3.53,3.76,3.84,3.88,4.05,4.07];function jx(){let i=Fe.sir,t=[],e=.12;for(let a=0;a<=4;a++){let o=-Math.PI/2+a/4*(Math.PI/2);t.push([i-e+e*Math.cos(o),Vc+e+e*Math.sin(o)])}let n=[];for(let a=.5;a<2.75;a+=.1)n.push(+a.toFixed(3));n=[...new Set([...n,...qx])].filter(a=>a>Vc+e+.01).sort((a,o)=>a-o);for(let a of n)t.push([i,a]);let s=[];for(let a=2.85;a<4.1;a+=.1)s.push(+a.toFixed(3));s=[...new Set([...s,...Yx,4.1])].sort((a,o)=>a-o);for(let a of s)t.push([fe(i,1.24,(a-2.75)/1.35),a]);let r=.3;for(let a=1;a<=7;a++){let o=a/8*(Math.PI/2);t.push([.94+r*Math.cos(o),4.1+r*Math.sin(o)])}return t}var yn=jx(),us=yn.length,ds=4.4,Pa=.94,yr=(()=>{let i=[];for(let e=0;e<=24;e++)i.push(Math.sin(Math.PI/2*(2*e/24-1)));let t=Ca.z/Fe.sir;for(let e of[-t,t,-.1,.1])i.push(e);return[...new Set(i.map(e=>+e.toFixed(5)))].sort((e,n)=>e-n)})(),_r=yr.length-1,qd=i=>ds+.05*(1-(i/Pa)**2);function Yd(i){let t=yn[Math.max(0,i-1)],e=yn[Math.min(us-1,i+1)],n=e[0]-t[0],s=e[1]-t[1],r=Math.hypot(n,s)||1;return[s/r,-n/r]}function Ih(i,t){let[e,n]=yn[i];return{w:t>Vc+.05&&n<t+.12?Fe.sir:e,y:Math.max(n,t),pod:n<t}}var Kd=[[.3,.04],[.45,.02],[.8,0],[1.3,0],[1.33,.13],[1.42,.15],[1.7,.21],[2.07,.38],[2.38,.47],[3.45,1.02],[3.84,1.25],[4.05,1.4]],Ra=(()=>{let n=Math.hypot(.72,1),s=(ds-4.05)/(1-.72/n);return{R:s,cd:1.4+s/n,cy:4.05-.72/n*s,y0:4.05}})(),jd=(()=>{let i=Kd,t=[];for(let e=0;e<i.length;e++){if(e===i.length-1){t.push(.72);continue}if(e===0){t.push((i[1][1]-i[0][1])/(i[1][0]-i[0][0]));continue}let n=(i[e][1]-i[e-1][1])/(i[e][0]-i[e-1][0]),s=(i[e+1][1]-i[e][1])/(i[e+1][0]-i[e][0]);t.push(n*s<=0?0:2*n*s/(n+s))}return t})();function Zx(i){if(i>=Ra.y0){let d=Math.max(0,Ra.R*Ra.R-(Math.min(i,ds)-Ra.cy)**2);return Ra.cd-Math.sqrt(d)}let t=Kd,e=0;for(;e<t.length-2&&i>t[e+1][0];)e++;let[n,s]=t[e],[r,a]=t[e+1],o=r-n,c=Be((i-n)/o),l=c*c,u=l*c;return(2*u-3*l+1)*s+(u-2*l+c)*o*jd[e]+(-2*u+3*l)*a+(u-l)*o*jd[e+1]}function $x(i){if(i>=ds)return Pa;if(i<=yn[0][1])return yn[0][0];for(let t=0;t<us-1;t++)if(i<=yn[t+1][1]){let e=(i-yn[t][1])/(yn[t+1][1]-yn[t][1]||1);return fe(yn[t][0],yn[t+1][0],Be(e))}return fe(yn[us-1][0],Pa,Be((i-yn[us-1][1])/(ds-yn[us-1][1])))}function Jx(i,t){let e=i<.45?Fe.sir:$x(i),n,s,r;if(i<=1.315)n=.3,s=.17,r=.03;else{let l=Be((i-1.33)/1.1);n=fe(.46,.66,l),s=fe(.3,.56,l),r=.07}n=Math.min(n,e*.7);let a=Math.min(Math.abs(t),e),o=r*(a/e)**2,c=e-n;return a>c&&(o+=s*(1-Math.sqrt(Math.max(0,1-((a-c)/n)**2)))),o}var Dn=(i,t)=>Zx(i)+Jx(i,t);function Zd(i,t){let e=[],n=[],s=[],r=[],l=t?[[0,1],[4.5,1],[4.65,.32],[i-6.82,.32],[i-6.67,1],[i-3.25,1],[i-3.1,.45],[i-2.9,.45]]:[[0,1],[4.5,1],[4.65,.32],[i-4.65,.32],[i-4.5,1],[i,1]],u=(x,p,m)=>{let y=[],E=(b,M)=>m?i-Dn(b,M):x;for(let b=0;b<us;b++){let M=Ih(b,p),[A,_]=Yd(b);y.push([E(M.y,-M.w),M.y,-M.w,0,M.pod?0:_,M.pod?-1:-A,-.5])}for(let b=0;b<=_r;b++){let M=yr[b]*Pa;y.push([E(ds,M),qd(M),M,0,1,0,0])}for(let b=us-1;b>=0;b--){let M=Ih(b,p),[A,_]=Yd(b);y.push([E(M.y,M.w),M.y,M.w,0,M.pod?0:_,M.pod?1:A,0])}let v=p>Vc+.05?Fe.sir:yn[0][0];for(let b=_r;b>=0;b--){let M=yr[b]*v;y.push([E(p,M),p,M,0,-1,0,0])}return y},d=l.map(([x,p])=>u(x,p,!1));t&&d.push(u(0,.45,!0));let h=d[0].length;for(let x of d)for(let[p,m,y,E,v,b,M]of x)e.push(p,m,y),n.push(E,v,b),s.push(p,m,M);for(let x=0;x<d.length-1;x++)for(let p=0;p<h-1;p++){let m=x*h+p,y=m+1,E=m+h,v=E+1;r.push(m,y,E,y,v,E)}let f=(x,p)=>{let m=d[x],y=e.length/3,E=m[0][0];e.push(E,2.3,0),n.push(p?1:-1,0,0),s.push(E,2.3,2);let v=e.length/3;for(let[b,M,A]of m)e.push(b,M,A),n.push(p?1:-1,0,0),s.push(b,M,2);for(let b=0;b<h-1;b++)p?r.push(y,v+b,v+b+1):r.push(y,v+b+1,v+b)};if(f(0,!1),t||f(d.length-1,!0),t){let x=e.length/3,p=[];for(let v=0;v<us;v++){let b=Ih(v,.45);p.push([b.w,b.y])}p.push([Pa,ds]);let m=p.length,y=.001;for(let v=0;v<m;v++){let[b,M]=p[v];for(let A=0;A<=_r;A++){let _=yr[A]*b,T=v===m-1?qd(_):M,P=i-Dn(T,_),L=Math.max(T-y,.45),F=Math.min(T+y,ds),V=F>L?(Dn(F,_)-Dn(L,_))/(F-L):0,I=Be(_,-b+y,b-y),z=(Dn(T,I+y)-Dn(T,I-y))/(2*y),q=new C(1,Math.min(V,60),Math.max(-60,Math.min(60,z))).normalize();e.push(P,T,_),n.push(q.x,q.y,q.z),s.push(_,T,1)}}let E=Ca.z/Fe.sir+1e-4;for(let v=0;v<m-1;v++){let b=p[v][1],M=p[v+1][1],A=b>=Ca.y0-1e-4&&M<=Ca.y1+1e-4;for(let _=0;_<_r;_++){if(A&&Math.abs(yr[_])<=E&&Math.abs(yr[_+1])<=E)continue;let T=x+v*(_r+1)+_,P=T+1,L=T+_r+1,F=L+1;r.push(T,L,P,P,L,F)}}}let g=new ge;return g.setAttribute("position",new te(e,3)),g.setAttribute("normal",new te(n,3)),g.setAttribute("aLiv",new te(s,3)),g.setIndex(r),g}function Kx(i){let t=[],e=[],{z:n,y0:s,y1:r,glob:a}=Ca,o=i-a,c=(d,h,f,g)=>{let x=t.length/3;t.push(...d,...h,...f,...g),e.push(x,x+1,x+2,x,x+2,x+3)},l=8;for(let d=0;d<l;d++){let h=fe(s,r,d/l),f=fe(s,r,(d+1)/l);for(let g of[-1,1]){let x=i-Dn(h,g*n),p=i-Dn(f,g*n);g>0?c([x,h,n],[o,h,n],[o,f,n],[p,f,n]):c([o,h,-n],[x,h,-n],[p,f,-n],[o,f,-n])}}for(let d=0;d<l;d++){let h=fe(-n,n,d/l),f=fe(-n,n,(d+1)/l),g=i-Dn(r,h),x=i-Dn(r,f);c([g,r,h],[x,r,f],[o,r,f],[o,r,h])}c([o,s,-n],[o,r,-n],[o,r,n],[o,s,n]);let u=new ge;return u.setAttribute("position",new te(t,3)),u.setIndex(e),u.computeVertexNormals(),u}var Qx=`
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
  if (tip < 1.5) return vrstaOken(H.x, H.y, gP0 + 0.2, gP1 - 0.2, 1.36, ${Ae.okSp[0]}, ${Ae.okSp[1]}, 0.10, 0.0, id);
  if (tip < 2.5) return vrstaOken(H.x, H.y, gP0 - 0.35, gP1 + 0.35, 1.80, ${Ae.okZg[0]}, ${Ae.okZg[1]}, 0.16, 0.10, id);
  if (tip < 4.5) return skatla2(H.xy, vec2(gOkA, ${Ae.okVm[0]}), vec2(gOkB, ${Ae.okVm[1]}), 0.10);
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
    float streha = smoothstep(${Ae.streha.toFixed(2)} - aa, ${Ae.streha.toFixed(2)} + aa, y);
    float zac = uCelni > 0.5 ? 3.62 : -1.0;
    col = mix(col, cModra, max(pasY(y, ${Ae.pasZg[0]}, ${Ae.pasZg[1]}) * step(zac, a), pasY(y, ${Ae.pasSp[0]}, ${Ae.pasSp[1]}) * step(zac + 0.9, a)));
    // dvonadstropni del med vrati
    float p0 = 5.95;
    float p1 = uCelni > 0.5 ? uL - 8.05 : uL - 5.95;
    gP0 = p0; gP1 = p1;
    korSp = (p1 - p0 - 0.4) / max(1.0, floor((p1 - p0 - 0.4) / 1.95 + 0.3));
    korZg = (p1 - p0 + 0.7) / max(1.0, floor((p1 - p0 + 0.7) / 1.95 + 0.3));
    float vPasu = step(p0, x) * step(x, p1);
    col = mix(col, cCrna * 1.5, pasY(y, ${Ae.crn[0]}, ${Ae.crn[1]}) * vPasu);
    float id;
    float sp = vrstaOken(x, y, p0 + 0.2, p1 - 0.2, 1.36, ${Ae.okSp[0]}, ${Ae.okSp[1]}, 0.10, 0.0, id) * vPasu;
    col = mix(col, cCrna, vrstaOken(x, y, p0 + 0.2, p1 - 0.2, 1.46, ${Ae.okSp[0]} - 0.04, ${Ae.okSp[1]} + 0.05, 0.13, 0.0, id) * vPasu);
    steklo = max(steklo, sp);
    if (sp > wOkna) { wOkna = sp; tipOkna = 1.0; }
    // zgornja okna: \u010Drn okvir z zaobljenima koncema, okna z rahlo nagnjenimi stebri\u010Dki
    float q0 = p0 - 0.45, q1 = p1 + 0.45;
    float okvirZg = skatla2(vec2(x, y), vec2(q0, ${Ae.okZg[0]} - 0.06), vec2(q1, ${Ae.okZg[1]} + 0.06), 0.34);
    col = mix(col, cCrna, okvirZg);
    float zgo = vrstaOken(x, y, q0 + 0.1, q1 - 0.1, 1.80, ${Ae.okZg[0]}, ${Ae.okZg[1]}, 0.16, 0.10, id) * okvirZg;
    steklo = max(steklo, zgo);
    if (zgo > wOkna) { wOkna = zgo; tipOkna = 2.0; }
    // okna vmesne eta\u017Ee nad vozi\u010Dki
    float okv = skatla2(vec2(e, y), vec2(1.55, ${Ae.okVm[0]}), vec2(3.35, ${Ae.okVm[1]}), 0.10);
    col = mix(col, cCrna, skatla2(vec2(e, y), vec2(1.49, ${Ae.okVm[0]} - 0.06), vec2(3.41, ${Ae.okVm[1]} + 0.06), 0.13));
    steklo = max(steklo, okv);
    if (okv > wOkna) { wOkna = okv; tipOkna = 3.0; }
    if (uCelni > 0.5) {
      vrata(a, y, 6.75, 8.05, 1.0, col, steklo);
      vrata(x, y, 4.65, 5.95, 0.0, col, steklo);
      // modro polje za kabino: sprednji rob nagnjen naprej (vrh bli\u017Ee nosu)
      float rob = 4.75 - (y - ${Ae.pasSp[0]}) * 0.62;
      float polje = smoothstep(rob - aa, rob + aa, a) * (1.0 - smoothstep(6.68 - aa, 6.68 + aa, a)) * pasY(y, ${Ae.pasSp[0]}, ${Ae.pasZg[1]});
      col = mix(col, cModra, polje);
      float okP = skatla2(vec2(a, y), vec2(5.05, ${Ae.okVm[0]}), vec2(6.30, ${Ae.okVm[1]}), 0.10);
      col = mix(col, cCrna, skatla2(vec2(a, y), vec2(4.99, ${Ae.okVm[0]} - 0.06), vec2(6.36, ${Ae.okVm[1]} + 0.06), 0.13));
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
`,t_=`
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
`,e_=`
#ifdef USE_ENVMAP
  if (LV.zun > 0.001) totalEmissiveRadiance += LV.zun * PREPUSTNOST * PREPUSTNOST * textureCubeUV(envMap, envMapRotation * normalize(uRot * LV.dz), 0.3).rgb * envMapIntensity;
#endif
`;function n_(){let[i,t]=He(1024,512);t.clearRect(0,0,1024,512),t.fillStyle="#fff";let e=[[90,340],[255,170],[575,170],[715,35],[800,120],[580,340]],n=f=>{t.beginPath(),f.forEach(([g,x],p)=>p?t.lineTo(g,x):t.moveTo(g,x)),t.closePath(),t.fill()},s=512/1425,r=256/515,a=(f,g)=>[f*s,g*r];n(e.map(([f,g])=>a(f,g))),n(e.map(([f,g])=>a(1425-f,515-g))),t.font='500 104px "IBM Plex Sans", Arial, sans-serif',t.textAlign="center",t.textBaseline="middle",t.fillText("313-005",256,322),t.save(),t.translate(512,128);let o=.075;t.translate(8,18);let c=(f,g)=>[f*o*1.2,g*o*1.2];n(e.map(([f,g])=>c(f,g))),n(e.map(([f,g])=>c(1425-f,515-g))),t.restore(),t.font='500 54px "IBM Plex Sans", Arial, sans-serif',t.textAlign="left",t.fillText("Slovenske \u017Eeleznice",650,176);let[l,u]=He(512,128);u.fillStyle="#000",u.fillRect(0,0,512,128),u.fillStyle="#fff",u.font='600 78px "IBM Plex Mono", monospace',u.textAlign="center",u.textBaseline="middle",u.fillText("V \u0160OLO",256,66);let d=u.getImageData(0,0,512,128).data;t.fillStyle="#000",t.fillRect(512,0,512,128);let h=6;for(let f=0;f<128;f+=h)for(let g=0;g<512;g+=h){let x=d[((f+3)*512+g+3)*4];t.fillStyle=x>90?"#ffa31a":"#1a0d00",t.beginPath(),t.arc(512+g+3,f+3,x>90?2.4:1.4,0,Math.PI*2),t.fill()}return qe(i,{srgb:!0,aniz:8})}var Gc=null;function Lh(i,t,e,n={zar:0,rdece:0}){let s=new ts({color:"#ffffff",roughness:.35,metalness:0,clearcoat:.7,clearcoatRoughness:.1}),r={uL:{value:i},uCelni:{value:t?1:0},uNoc:e.uNoc,uSvetloba:e.uSvetloba,uZarometi:{value:n.zar},uRdece:{value:n.rdece},uNapisi:{value:Gc},cModra:{value:new Wt(As.modra)},cBela:{value:new Wt(As.bela)},cStreha:{value:new Wt(As.streha)},cCrna:{value:new Wt(As.crna)},cSteklo:{value:new Wt(As.steklo)},cTemna:{value:new Wt(As.temna)},uKam:{value:new C(0,2,-20)},uRot:{value:new he},uVrata:{value:new xe(0,0,0,0)},uStrop:e.uStrop,uStropY:e.uStropY,uStropLuc:e.uStropLuc,uStropBarva:e.uStropBarva};return s.userData.u=r,s.onBeforeCompile=a=>{Object.assign(a.uniforms,r),a.vertexShader=a.vertexShader.replace("#include <common>",`#include <common>
attribute vec3 aLiv;
varying vec3 vLiv;
varying vec3 vLok;
varying vec3 vNorLok;
varying vec3 vSvetPos;`).replace("#include <begin_vertex>",`#include <begin_vertex>
vLiv = aLiv;
vLok = position;
vNorLok = normal;
vSvetPos = (modelMatrix * vec4(position, 1.0)).xyz;`),a.fragmentShader=a.fragmentShader.replace("#include <common>",`#include <common>
`+Qx+`
Liv LV;`).replace("#include <color_fragment>",`#include <color_fragment>
LV = liv();
diffuseColor.rgb = LV.col;`).replace("#include <roughnessmap_fragment>",`#include <roughnessmap_fragment>
roughnessFactor = LV.rough;`).replace("#include <emissivemap_fragment>",`#include <emissivemap_fragment>
totalEmissiveRadiance += LV.emis;`).replace("#include <lights_physical_fragment>",`#include <lights_physical_fragment>
material.clearcoat = LV.coat;
material.specularColor = max(material.specularColor, vec3(LV.spec));`).replace("#include <lights_fragment_maps>",`#include <lights_fragment_maps>
`+t_).replace("#include <lights_fragment_end>",`#include <lights_fragment_end>
`+e_)},s.customProgramCacheKey=()=>"kiss-liv",s}function i_(){let i=[];i.push([re(.035,.48,.37,.05),"#25282c",qt(.0175,0,0)]);let t=new vi;t.moveTo(0,-.028),t.lineTo(.03,-.028),t.lineTo(.055,-.012),t.lineTo(.055,.018),t.lineTo(.035,.028),t.lineTo(0,.028),t.closePath();let e=new Bi(t,{depth:.33,bevelEnabled:!1});e.translate(0,0,-.165);for(let n=0;n<7;n++)i.push([e,"#33373c",qt(.02,-.2+n*.0665,0)]);return We(i)}function s_(i){let t=[],e=[[.45,1.3,i-.06],[.12,.98,i-.22]],n=new ge,s=(g,x,p)=>[p,g,x],[[r,a,o],[c,l,u]]=e,d=.07,h=[s(r,-a,o),s(r,a,o),s(c,l,u),s(c,-l,u),s(r,-a,o-d),s(r,a,o-d),s(c,l,u-d),s(c,-l,u-d)],f=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[3,7,6,2],[0,4,7,3],[1,2,6,5]];for(let[g,x,p,m]of f)t.push(...h[g],...h[x],...h[p],...h[g],...h[p],...h[m]);return n.setAttribute("position",new te(t,3)),n.computeVertexNormals(),n}function r_(i){let t=[],s="#6c7074",r="#24272a",a="#121416";t.push([new ve(.085,.1,.95,14),r,qt(i-.42,.92,-.03,0,0,Math.PI/2)]);let o=[];for(let l=0;l<=10;l++)o.push(new vt(.15+l%2*.035,l*.03));let c=new xi(o,18);t.push([c,"#2b2a2c",qt(i-.78,.92,-.03,0,0,-Math.PI/2)]),t.push([re(.12,.36,.44,.02),s,qt(i+.08,.92,-.03)]),t.push([new ve(.105,.105,.03,20),a,qt(i+.145,.92,-.03+.1,0,0,Math.PI/2)]),t.push([new ci(.105,.018,8,22),"#55595d",qt(i+.145,.92,-.03+.1,0,Math.PI/2,0)]),t.push([new ve(.09,.09,.05,18),"#5d6165",qt(i+.16,.92,-.03-.11,0,0,Math.PI/2)]),t.push([re(.06,.03,.1,.005),"#2a2d30",qt(i+.2,.92,-.03-.11)]),t.push([re(.26,.12,.46,.02),"#1d1f22",qt(i+.02,.92+.25,-.03)]);for(let l of[-1,1])t.push([new gi(.022,3),"#e8b400",qt(i+.152,.92+.26,-.03+l*.15,0,Math.PI/2,Math.PI/2)]);return t.push([new ci(.14,.022,8,16,Math.PI),a,qt(i-.05,.92-.3,-.03-.12,0,Math.PI/2,Math.PI)]),t.push([new ci(.12,.02,8,16,Math.PI),a,qt(i-.1,.92-.28,-.03+.16,0,Math.PI/2,Math.PI)]),t.push([new ve(.014,.014,.42,6),"#7b7f83",qt(i+.22,.92-.2,-.03+.06,.55,0,.35)]),We(t)}function a_(){let i=Fe.rKolo,t=[[0,-.07],[i-.05,-.07],[i,-.065],[i,.04],[i+.03,.045],[i+.03,.065],[i-.06,.07],[i-.08,.03],[.16,.025],[.13,.08],[0,.08]],e=new xi(t.map(([n,s])=>new vt(n,s)),28);return e.rotateX(Math.PI/2),e}function o_(i){let t=new oe,e=[],n="#2c3035",s="#4a5057",r="#16171a",a="#9c8a45",o=Fe.medOsjem/2,c=new vi;c.moveTo(-1.55,.62),c.lineTo(-1.05,.62),c.lineTo(-.7,.44),c.lineTo(.7,.44),c.lineTo(1.05,.62),c.lineTo(1.55,.62),c.lineTo(1.55,.84),c.lineTo(1,.84),c.lineTo(.65,.7),c.lineTo(-.65,.7),c.lineTo(-1,.84),c.lineTo(-1.55,.84),c.closePath();let l=new Bi(c,{depth:.16,bevelEnabled:!0,bevelThickness:.015,bevelSize:.015,bevelSegments:1});for(let p of[-1,1])e.push([l,n,qt(0,0,p*1-.08)]);e.push([re(.5,.2,1.9,.03),n,qt(0,.52,0)]);for(let p of[-o,o])for(let m of[-1,1])e.push([re(.34,.28,.22,.04),s,qt(p,Fe.rKolo,m*1.04)]),e.push([new ve(.1,.1,.22,10),a,qt(p+.22*Math.sign(p),.7,m*1.04)]),e.push([new ve(.075,.075,.16,10),s,qt(p,Fe.rKolo,m*1.18,Math.PI/2)]);for(let p of[-1,1])e.push([new ve(.27,.29,.24,18),r,qt(0,.96,p*.98)]),e.push([new ve(.045,.045,1.3,8),"#5d636a",qt(0,.78,p*1.27,0,0,Math.PI/2)]);if(i)for(let p of[-o,o])e.push([re(.62,.5,.95,.05),"#33373c",qt(p*.42,.45,.15)]);else for(let p of[-o,o])for(let m of[-1,1])e.push([new ve(.31,.31,.05,20),"#5a5f66",qt(p,Fe.rKolo,m*.3,Math.PI/2)]);let u=new ct(We(e),new Ot({vertexColors:!0,roughness:.62,metalness:.35}));u.castShadow=!0,t.add(u);let d=a_(),h=new ve(.085,.085,1.5,12);h.rotateX(Math.PI/2);let f=We([[d,"#9aa0a6",qt(0,0,.75)],[d,"#9aa0a6",qt(0,0,-.75,0,Math.PI,0)],[h,"#3a3e43"]]),g=new Ot({vertexColors:!0,roughness:.32,metalness:.9}),x=[];for(let p of[-o,o]){let m=new ct(f,g);m.position.set(p,Fe.rKolo,0),m.castShadow=!0,t.add(m),x.push(m)}return t.userData.dvojici=x,t}function $d(){let i=new oe,t=new Ot({color:"#8b9198",roughness:.4,metalness:.7}),e=new Ot({color:"#7a2f24",roughness:.55}),n=new Ot({color:"#2a2e33",roughness:.6,metalness:.3});for(let[c,l]of[[-.5,-.45],[-.5,.45],[.5,-.45],[.5,.45]]){let u=new ct(new ve(.06,.07,.26,10),e);u.position.set(c,.13,l),i.add(u)}let s=new ct(re(1.3,.08,1.05,.02),n);s.position.y=.3,i.add(s);let r=new ct(new ve(.035,.045,1,8),t),a=new ct(new ve(.022,.03,1,8),t),o=new oe;for(let c of[-.11,.11]){let l=new ct(re(.06,.05,1.5,.01),new Ot({color:"#31343a",roughness:.5}));l.position.x=c,o.add(l)}for(let c of[-1,1]){let l=new ct(new ci(.16,.012,6,12,Math.PI/2),t);l.position.set(0,-.16,c*.75),l.rotation.y=Math.PI/2,l.rotation.z=c>0?0:Math.PI/2,o.add(l)}return i.add(r,a,o),i.userData.dvigni=c=>{let f=Math.max(.12,c-.3),g=-.35,x=Math.hypot(g- -.2,f),p=Math.atan2(f,g- -.2)-Math.acos(Be((1.2*1.2+x*x-1.3*1.3)/(2*1.2*x),-1,1)),m=-.2+1.2*Math.cos(p),y=.3+1.2*Math.sin(p),E=(v,b,M,A,_)=>{v.position.set((b+A)/2,(M+_)/2,0),v.rotation.z=Math.atan2(_-M,A-b)-Math.PI/2,v.scale.y=Math.hypot(A-b,_-M)};E(r,-.2,.3,m,y),E(a,m,y,g,.3+f),o.position.set(g,.3+f+.03,0)},i.userData.dvigni(1),i.traverse(c=>{c.isMesh&&(c.castShadow=!0)}),i}function c_(i,t,e){let n=new oe,s=(i+t)/2,r=i-.9,a=t+.9,o=(M,A,_,T,P,L,F)=>[new Ce(T-M,P-A,L-_),F,qt((M+T)/2,(A+P)/2,(_+L)/2)],c=[o(r,.5,-1.37,a,.58,1.37,"#41454a"),o(i,.58,-1.37,t,.586,-1.27,"#d8a817"),o(i,.58,1.27,t,.586,1.37,"#d8a817"),o(i-.02,.555,-1.43,t+.02,.587,-1.3,"#8e949a"),o(i,.44,-1.42,t,.555,-1.36,"#16181b"),o(r,2.5,-1.37,a,2.58,1.37,"#d5d6d3"),o(r,.58,1.33,a,2.5,1.37,"#c5c8c9"),o(i,.58,1.31,t,2.48,1.33,"#33475f"),o(s-.006,.58,1.304,s+.006,2.48,1.31,"#121416"),o(i-.07,.44,-1.42,i,2.56,-1.29,"#2b2e33"),o(t,.44,-1.42,t+.07,2.56,-1.29,"#2b2e33"),o(i-.07,2.48,-1.42,t+.07,2.56,-1.29,"#2b2e33"),o(r-.05,.58,-1.37,r,2.5,-.56,"#cfd2d4"),o(r-.05,.58,.56,r,2.5,1.37,"#cfd2d4"),o(r-.05,2.22,-.56,r,2.5,.56,"#cfd2d4"),o(r-.06,.58,-.58,r+.01,2.24,-.55,"#8b9196"),o(r-.06,.58,.55,r+.01,2.24,.58,"#8b9196"),o(r-.06,2.21,-.58,r+.01,2.24,.58,"#8b9196"),o(r+.002,2.27,-.42,r+.014,2.43,.42,"#0c0d0f"),o(r-2.6,.58,-.62,r-.05,4.1,-.56,"#c7cacc"),o(r-2.6,.58,.56,r-.05,4.1,.62,"#c7cacc"),o(r-2.65,2.4,-.62,r-2.6,4.1,.62,"#cfd2d4"),o(r-2.6,4.1,-.62,r-.05,4.16,.62,"#d5d6d3"),o(a,.58,-1.37,a+.05,2.5,1.37,"#cfd2d4")];for(let M=0;M<8;M++){let A=.58+.245*(M+1);c.push(o(r-.27*(M+1),.58,-.55,r-.27*M,A,.55,"#555a60")),c.push(o(r-.27*M-.035,A-.012,-.55,r-.27*M,A+.002,.55,"#d8a817"))}let l=new Ot({vertexColors:!0,roughness:.72});l.onBeforeCompile=M=>{M.uniforms.uNotrSv=e.uNotrSv,M.fragmentShader=M.fragmentShader.replace("#include <common>",`#include <common>
uniform float uNotrSv;`).replace("#include <emissivemap_fragment>",`#include <emissivemap_fragment>
totalEmissiveRadiance += diffuseColor.rgb * uNotrSv;`)},l.customProgramCacheKey=()=>"preddverje";let u=new ct(We(c),l);u.receiveShadow=!0,n.add(u);let d=new Ot({color:"#000",emissive:"#fff3df",emissiveIntensity:2.2}),h=(t-i)*.25,f=We([o(s-.55,2.486,-.3,s+.55,2.5,.3,"#fff"),o(r-2,4.085,-.06,r-.6,4.1,.06,"#fff")]);n.add(new ct(f,d));let g=new Ot({color:"#000",emissive:"#c4d1dc",emissiveIntensity:.8}),x=We([o(i+h-.11,1.14,1.298,i+h+.11,2.09,1.305,"#fff"),o(s+h-.11,1.14,1.298,s+h+.11,2.09,1.305,"#fff")]);n.add(new ct(x,g));let p=new Ot({color:"#c3c8cd",metalness:.8,roughness:.3}),m=[];for(let[M,A]of[[i+.08,-1.2],[t-.08,-1.2],[i+.08,1.2],[t-.08,1.2]])m.push([new ve(.018,.018,1.92,10),"#c3c8cd",qt(M,1.54,A)]);let y=Math.hypot(2.2,1.9);m.push([new ve(.02,.02,y,8),"#c3c8cd",qt(r-1.1,2.45,-.5,0,0,Math.atan2(2.2,1.9))]),n.add(new ct(We(m),p));let E=new je(.8,.2),v=E.attributes.uv;for(let M=0;M<v.count;M++)v.setXY(M,.5+v.getX(M)*.5,.75+v.getY(M)*.25);let b=new ct(E,new Ot({color:"#000",emissive:"#ffffff",emissiveMap:Gc,emissiveIntensity:1.6}));return b.rotation.y=Math.PI/2,b.position.set(r+.016,2.35,0),n.add(b),n.visible=!1,n.userData={zunajMat:g,lucMat:d},n}function l_(i,t){let[e,n]=He(64,200);n.fillStyle=As.modra,n.fillRect(0,0,64,200),n.fillStyle="#0b0f14",n.beginPath(),n.roundRect(22,66,20,94,8),n.fill();let s=new ts({map:qe(e),roughness:.3,clearcoat:.7}),r=(i+t)/2,a=(t-i)/2,o=new oe,c=[-1,1].map(l=>{let u=new ct(new Ce(a,2.02,.025),s);return u.position.set(r+l*a/2,.46+1.01,-1.42),u.userData={x:r+l*a/2,st:l},u.castShadow=!0,o.add(u),u});return o.visible=!1,o.userData.krila=c,o}function Qd(){Gc=Gc||n_();let i={uNoc:{value:0},uSvetloba:{value:1},uNotrSv:{value:.24},uStrop:{value:new xe(-31,31,2.35,7.4)},uStropY:{value:4.1},uStropLuc:{value:.6},uStropBarva:{value:new Wt(.15,.145,.14)}},t=Zd(Fe.Lc,!0),e=Zd(Fe.Lv,!1),n=Lh(Fe.Lc,!0,i,{zar:1,rdece:0}),s=Lh(Fe.Lc,!0,i,{zar:0,rdece:1}),r=Lh(Fe.Lv,!1,i),a=new oe;a.name="vlak";let o=new Ot({vertexColors:!0,roughness:.55,metalness:.25}),c=new Ot({color:"#141618",roughness:.85,side:vn}),l=new Ot({color:"#1b1d20",roughness:.6,metalness:.2,side:vn}),u=i_();function d(ft,N){ft.add(new ct(Kx(N),c));let k=new ct(s_(N),l);k.castShadow=!0,ft.add(k);for(let xt of[-1,1]){let X=xt*.955,tt=.885,G=new ct(u,o);G.position.set(N-Dn(tt,X),tt,X),G.rotation.y=-Math.atan2(Dn(tt,X+.02)-Dn(tt,X-.02),.04),G.castShadow=!0,ft.add(G)}let dt=new ct(r_(N),o);dt.castShadow=!0,ft.add(dt);let St=new ct(re(.025,.85,.03,.008),new Ot({color:"#0d0d0e",roughness:.5})),Mt=2.75,Ft=-.42;St.position.set(N-Dn(Mt,Ft)+.03,Mt,Ft),St.rotation.z=Math.atan2(1,.51)-Math.PI/2,St.rotation.x=.45,ft.add(St)}function h(ft,N){let k=[],dt="#5b6168";N?(k.push([re(3.4,.16,1.3,.05),"#3d4248",qt(2.4,4.44,0)]),k.push([re(2,.14,1.2,.05),dt,qt(ft-7.2,4.46,0)])):(k.push([re(2.6,.2,1.5,.06),dt,qt(2.3,4.45,0)]),k.push([re(2.6,.2,1.5,.06),dt,qt(ft-2.3,4.45,0)]));let Mt=new ct(We(k),o);return Mt.castShadow=!0,Mt}function f(){let ft=[];for(let k=0;k<7;k++)ft.push([re(.08,3.3,2.35,.03),k%2?"#1c1e21":"#2a2d31",qt(-.42+k*.14,2.5,0)]);let N=new ct(We(ft),o);return N.castShadow=!0,N}let g=[],x=[{L:Fe.Lc,celni:!0,obrnjen:!1,mat:n},{L:Fe.Lv,celni:!1,obrnjen:!1,mat:r},{L:Fe.Lc,celni:!0,obrnjen:!0,mat:s}];for(let ft of x){let N=new oe,k=new oe,dt=new ct(ft.celni?t:e,ft.mat);dt.castShadow=!0,dt.receiveShadow=!0,k.add(dt),k.add(h(ft.L,ft.celni)),ft.celni&&d(k,ft.L),k.position.x=-ft.L/2,N.add(k),ft.obrnjen&&(N.rotation.y=Math.PI);let St=new oe;St.add(N),a.add(St),g.push({...ft,ovoj:St,notr:k})}let p=$d();p.position.set(4.2,4.4,0),p.rotation.y=Math.PI,p.userData.dvigni(1.07),g[2].notr.add(p);let m=$d();m.position.set(4.2,4.4,0),m.rotation.y=Math.PI,m.userData.dvigni(.2),g[0].notr.add(m);let y=[f(),f()];y.forEach(ft=>a.add(ft));let E=[],v=ft=>{let N=o_(ft);return a.add(N),E.push(N),N},b=[v(!1),v(!0),v(!1),v(!1),v(!0),v(!1)],M=new C,A=new C,_=new C,T=new C(0,1,0),P=new C,L=new C,F=new de,V=null,I=0,z=(ft,N)=>{P.crossVectors(N,T).normalize(),L.crossVectors(P,N).normalize(),F.makeBasis(N,L,P),ft.quaternion.setFromRotationMatrix(F)};function q(ft,N){let{Lc:k,Lv:dt,rega:St,aVozF:Mt,rVoz:Ft}=Fe,xt=[N,N-k-St,N-k-St-dt-St],X=[[xt[0]-Mt,xt[0]-k+Ft],[xt[1]-Ft,xt[1]-dt+Ft],[xt[2]-Ft,xt[2]-k+Mt]];g.forEach((G,et)=>{let[gt,Bt]=X[et];ft.tocka(gt,M),ft.tocka(Bt,A),_.subVectors(M,A).normalize();let bt=et===2?G.L/2-Ft:G.L/2-(et===0?Mt:Ft),jt=et===2?-(G.L/2-Mt):-(G.L/2-Ft),ne=(0-jt)/(bt-jt);G.ovoj.position.lerpVectors(A,M,ne),z(G.ovoj,_)});for(let G=0;G<2;G++){let et=xt[G+1]+St/2;ft.tocka(et,M),ft.smer(et,_),y[G].position.copy(M),z(y[G],_)}let tt=X.flat();V!==null&&(I-=(N-V)/Fe.rKolo),V=N,tt.forEach((G,et)=>{ft.tocka(G,M),ft.smer(G,_),b[et].position.copy(M),z(b[et],_);for(let gt of b[et].userData.dvojici)gt.rotation.z=I})}let j=Fe.Lv-5.95,at=Fe.Lv-4.65,K=c_(j,at,i),st=l_(j,at);g[1].notr.add(K,st);function it(ft){r.userData.u.uVrata.value.set(j,at,ft,0),K.visible=st.visible=ft>.001;let N=Jd(ft/.18);for(let k of st.userData.krila)k.position.x=k.userData.x+k.userData.st*.63*Jd((ft-.12)/.88),k.position.z=-1.42-.045*N}let Rt=(ft,N,k,dt=new C)=>(g[1].notr.updateWorldMatrix(!0,!1),g[1].notr.localToWorld(dt.set(ft,N,k)));function mt(ft=!0,N=0){i.uNoc.value=N,i.uNotrSv.value=fe(.24,.55,N),i.uStropLuc.value=fe(.6,2.4,N),i.uStropBarva.value.setRGB(fe(.15,.2,N),fe(.145,.17,N),fe(.14,.13,N)),K.userData.zunajMat.emissiveIntensity=fe(.8,.05,N),n.userData.u.uZarometi.value=ft?1:0}let Ut=new de;function Dt(ft){for(let N of g){N.notr.updateWorldMatrix(!0,!1);let k=N.mat.userData.u;Ut.copy(N.notr.matrixWorld).invert(),k.uKam.value.copy(ft.position).applyMatrix4(Ut),k.uRot.value.setFromMatrix4(N.notr.matrixWorld)}}return{skupina:a,postavi:q,nastaviLuci:mt,skupni:i,vozovi:g,pant:p,odpriVrata:it,vrataLok:Rt,kamera:Dt,zadnjiS:()=>V,VRATA:{xa:j,xb:at}}}var Jd=i=>{let t=Be(i);return t*t*(3-2*t)};var ue={z0:1.68,z1:8.2,y:.55,x0:-95,x1:95},Wc={x:0,y:3.32,z:3.05,r:.4},Dh={x:5.2,y:3.38,z:4.3};function h_(){let[e,n]=He(512,1664),[s,r]=He(512,1664),a=jn(21),o=_n(9),c=256;n.fillStyle="#9b9890",n.fillRect(0,0,512,1664),r.fillStyle="#808080",r.fillRect(0,0,512,1664);let l=.4*c;for(let f=.32*c;f<1664;f+=l)for(let g=0;g<512;g+=l){let x=140+o()*26-13;n.fillStyle=`rgb(${x},${x-3},${x-9})`,n.fillRect(g+2,f+2,l-4,l-4),r.fillStyle="#9a9a9a",r.fillRect(g+3,f+3,l-6,l-6)}n.fillStyle="#d9d6cd",n.fillRect(0,0,512,.32*c),r.fillStyle="#b0b0b0",r.fillRect(0,0,512,.32*c),n.fillStyle="#e3b419",n.fillRect(0,.82*c,512,.1*c),n.fillStyle="#cfcbc0",n.fillRect(0,1.02*c,512,.4*c);for(let f=0;f<512;f+=18)r.fillStyle="#c8c8c8",r.fillRect(f+3,1.04*c,9,.36*c),n.fillStyle="#e2ded3",n.fillRect(f+3,1.04*c,9,.36*c);let u=n.getImageData(0,0,512,1664);for(let f=0;f<1664;f++)for(let g=0;g<512;g++){let x=(f*512+g)*4,p=.9+.12*Cn(a,g/60,f/60,4)+.04*(o()-.5);u.data[x]*=p,u.data[x+1]*=p,u.data[x+2]*=p}n.putImageData(u,0,0);let d=qe(e,{ponavljaj:!0}),h=qe(Aa(s,2.2),{srgb:!1,ponavljaj:!0});return{bar:d,nor:h}}function u_(){let[t,e]=He(1024,1024),n=1024/2,s=e.createRadialGradient(n,n,0,n,n,n);s.addColorStop(0,"#fbfbf8"),s.addColorStop(.85,"#f1f0ea"),s.addColorStop(1,"#d9d7cf"),e.fillStyle=s,e.beginPath(),e.arc(n,n,n,0,Math.PI*2),e.fill(),e.translate(n,n);for(let r=0;r<60;r++)e.save(),e.rotate(r/60*Math.PI*2),e.fillStyle="#121212",r%5===0?e.fillRect(-n*.034,-n*.94,n*.068,n*.24):e.fillRect(-n*.011,-n*.94,n*.022,n*.075),e.restore();return qe(t,{aniz:16})}function d_(){let[e,n]=He(1024,300),s=document.createElement("canvas");s.width=1024,s.height=300;let r=s.getContext("2d",{willReadFrequently:!0}),a=qe(e,{aniz:8}),o=6,c=(g,x)=>{let[p,m]=He(o,o);return m.fillStyle=g,m.beginPath(),m.arc(3,3,x,0,Math.PI*2),m.fill(),p},l={zgoraj:c("#ffb21f",2.5),spodaj:c("#ff7a1a",2.5)},[u,d]=He(1024,300);d.fillStyle="#050403",d.fillRect(0,0,1024,300),d.fillStyle=d.createPattern(c("#140b02",1.5),"repeat"),d.fillRect(0,0,1024,300);let h=null;function f(g,x="07:42"){let p=g+x;if(p===h)return;h=p,r.fillStyle="#000",r.fillRect(0,0,1024,300),r.fillStyle="#fff",r.textBaseline="middle",r.font='600 46px "IBM Plex Mono", monospace',r.fillText("ODHOD",36,52),r.fillText("SMER",270,52),r.fillText("TIR",880,52),r.font='600 92px "IBM Plex Mono", monospace',r.fillText(x,30,150),r.fillText("V \u0161olo",300,150),r.fillText("1",905,150),r.font='600 62px "IBM Plex Mono", monospace',g>0&&r.fillText(`zamuda ${g} min`,300,245);let m=r.getImageData(0,0,1024,300).data;n.drawImage(u,0,0);for(let y=0;y<300;y+=o)for(let E=0;E<1024;E+=o)m[((y+3)*1024+E+3)*4]>100&&n.drawImage(y>200?l.spodaj:l.zgoraj,E,y);a.needsUpdate=!0}return f(0),{tex:a,narisi:f}}function tf(i,t,e,n={}){let r=Math.round(i*48),a=Math.round((t*3.6+1)*48),[o,c]=He(r,a),[l,u]=He(r,a),d=_n(n.seme||4),h=jn(n.seme||4);c.fillStyle=n.omet||"#e6d6b4",c.fillRect(0,0,r,a),u.fillStyle="#000",u.fillRect(0,0,r,a),c.fillStyle=n.podstavek||"#b7ab94",c.fillRect(0,a-.7*48,r,.7*48);for(let x=1;x<t;x++){let p=a-(.7+x*3.6)*48;c.fillStyle="#f2ecdf",c.fillRect(0,p-6,r,12)}c.fillStyle="#f4efe4",c.fillRect(0,0,r,.35*48);let f=i/e;for(let x=0;x<t;x++)for(let p=0;p<e;p++){let m=(p+.5)*f*48,y=a-(.7+x*3.6+.9)*48,E=1.15*48,v=(x===0&&n.loki?2.1:1.6)*48,b=x===0&&n.vrata&&n.vrata.includes(p),M=b?2.6*48:v,A=b?a-.7*48-M:y-v;c.fillStyle="#f6f2e8",c.fillRect(m-E/2-7,A-7,E+14,M+14),x===0&&n.loki&&(c.beginPath(),c.arc(m,A,E/2+7,Math.PI,0),c.fill()),c.fillStyle=b?"#3d4a3a":"#283035",c.fillRect(m-E/2,A,E,M),x===0&&n.loki&&(c.beginPath(),c.arc(m,A,E/2,Math.PI,0),c.fill()),b||(c.fillStyle="#e9e4d8",c.fillRect(m-2,A,4,M),c.fillRect(m-E/2,A+M*.38,E,4),d()<(n.svetijo??.35)&&(u.fillStyle=`rgb(${200+d()*55},${150+d()*50},${80+d()*40})`,u.fillRect(m-E/2+3,A+3,E-6,M-6)))}let g=c.getImageData(0,0,r,a);for(let x=0;x<a;x++)for(let p=0;p<r;p++){let m=(x*r+p)*4,y=.93+.09*Cn(h,p/40,x/40,3)-.06*Math.max(0,(x-a*.8)/(a*.2))*0;g.data[m]*=y,g.data[m+1]*=y,g.data[m+2]*=y}return c.putImageData(g,0,0),{bar:qe(o),emis:qe(l)}}var Uh=null;function Mr(i=[150,66,44]){let[n,s]=He(256,256),r=Uh?null:He(256,256),a=_n(13),o=32,c=24;for(let l=0;l<256;l+=o){let u=l/o%2?c/2:0;for(let d=-c;d<256+c;d+=c){let h=.82+a()*.3;if(s.fillStyle=`rgb(${i[0]*h|0},${i[1]*h|0},${i[2]*h|0})`,s.fillRect(d+u,l,c-1,o),!r)continue;let f=r[1],g=f.createLinearGradient(0,l,0,l+o);g.addColorStop(0,"#202020"),g.addColorStop(1,"#d0d0d0"),f.fillStyle=g,f.fillRect(d+u,l,c-1,o),f.fillStyle="#404040",f.fillRect(d+u+c-2,l,2,o)}}return r&&(Uh=Aa(r[0],2.5)),{bar:qe(n,{ponavljaj:!0}),nor:qe(Uh,{srgb:!1,ponavljaj:!0})}}function Rs(i,t,e,n=.5){let s=i/2+n,r=t/2+n,a=r>s;a&&([s,r]=[r,s]);let o=r,c=Math.hypot(o,e)/o,l=[-s+o,e,0],u=[s-o,e,0],d=[[[s,0,-r],[-s,0,-r],l,u],[[-s,0,r],[s,0,r],u,l],[[-s,0,-r],[-s,0,r],l],[[s,0,r],[s,0,-r],u]],h=[],f=[],g=(p,m)=>m<2?[p[0],(r-Math.abs(p[2]))*c]:[p[2],(s-Math.abs(p[0]))*c];if(d.forEach((p,m)=>{let y=p.length===4?[[0,1,2],[0,2,3]]:[[0,1,2]];for(let E of y)for(let v of E)h.push(...p[v]),f.push(...g(p[v],m))}),a)for(let p=0;p<h.length;p+=3){let m=h[p];h[p]=-h[p+2],h[p+2]=m}let x=new ge;return x.setAttribute("position",new te(h,3)),x.setAttribute("uv",new te(f,2)),x.computeVertexNormals(),x}function f_(){let i=new oe,t=Wc.r,e=new Ot({color:"#2a2d31",roughness:.38,metalness:.6}),n=new ct(new ve(t+.04,t+.04,.17,64,1,!0),e);n.rotation.z=Math.PI/2;let s=new ct(new ci(t+.025,.02,12,64),e),r=s.clone();s.rotation.y=Math.PI/2,s.position.x=.085,r.rotation.y=Math.PI/2,r.position.x=-.085,i.add(n,s,r);let a=u_(),o=new Ot({map:a,emissiveMap:a,emissive:"#fff8ea",emissiveIntensity:.35,roughness:.6}),c=[],l=new Ot({color:"#0e0e0e",roughness:.5}),u=new Ot({color:"#c81e14",roughness:.45,emissive:"#3a0500"}),d=new oi({color:"#000",transparent:!0,opacity:.16,depthWrite:!1}),h=(p,m,y,E=0)=>{let v=new vi;return v.moveTo(-m/2,-E),v.lineTo(m/2,-E),v.lineTo(y/2,p),v.lineTo(-y/2,p),v.closePath(),new Bi(v,{depth:.004,bevelEnabled:!1})},f=()=>{let p=new vi;p.moveTo(-.0035,-.11*t/.4),p.lineTo(.0035,-.11*t/.4),p.lineTo(.002,t*.86),p.lineTo(-.002,t*.86),p.closePath();let m=new Bi(p,{depth:.003,bevelEnabled:!1}),y=new ve(.022,.022,.003,24);return y.rotateX(Math.PI/2),y.translate(0,-.085*t/.4,.0015),We([[m,"#c81e14"],[y,"#c81e14"]])};for(let p of[1,-1]){let m=new oe,y=new ct(new gi(t,72),o);m.add(y);let E=new ct(h(t*.64,.036,.026,t*.16),l),v=new ct(h(t*.9,.028,.017,t*.18),l),b=new ct(f(),new Ot({vertexColors:!0,roughness:.45,emissive:"#2a0400"}));E.position.z=.006,v.position.z=.011,b.position.z=.016;let M=new ct(E.geometry,d),A=new ct(v.geometry,d),_=new ct(b.geometry,d);for(let L of[M,A,_])L.position.set(.006,-.008,.0015),L.scale.set(1.04,1.02,.2);let T=new ct(new ve(.012,.012,.006,16),l);T.rotation.x=Math.PI/2,T.position.z=.02,m.add(M,A,_,E,v,b,T);let P=new ct(new gi(t+.005,64),new ts({color:"#ffffff",transparent:!0,opacity:.08,roughness:.05,metalness:0,clearcoat:1,depthWrite:!1}));P.position.z=.03,m.add(P),m.rotation.y=p>0?-Math.PI/2:Math.PI/2,m.position.x=p*-.07,i.add(m),c.push({ure:E,min:v,sek:b,sU:M,sM:A,sS:_})}let g=new ct(We([[new ve(.025,.025,.55,10),"#2a2d31",qt(0,t+.32,0)],[re(.06,.06,.3,.01),"#2a2d31",qt(0,t+.6,0)]]),new Ot({vertexColors:!0,roughness:.4,metalness:.6}));i.add(g),i.position.set(Wc.x,Wc.y,Wc.z),i.traverse(p=>{p.isMesh&&p.material!==d&&(p.castShadow=!0)});function x(p){let m=Math.floor(p/3600)%12,y=Math.floor(p/60)%60,E=p%60,v=E<58.5?E/58.5*Math.PI*2:0,b=y/60*Math.PI*2,M=(m+y/60)/12*Math.PI*2;for(let A of c)A.ure.rotation.z=-M,A.min.rotation.z=-b,A.sek.rotation.z=-v,A.sU.rotation.z=-M,A.sM.rotation.z=-b,A.sS.rotation.z=-v}return{skupina:i,nastavi:x,obraz:o}}var p_={prsi:.199,pas:.153,globina:.69,nad:.062,pod:.049,vrat:.054,stegno:.079,meca:.058,trap:.014,kolk:.095};function Xc(i,t,e,n=10,s=0,r=.4){let a=[];for(let o=0;o<=6;o++){let c=o/6*Math.PI/2;a.push(new vt(t*Math.sin(c),-e-t*Math.cos(c)))}if(s)for(let[o,c]of[[.8,fe(t,s,.55)],[r+.12,s*.985],[r,s],[r*.45,fe(i,s,.7)]])a.push(new vt(c,-e*o));for(let o=0;o<=6;o++){let c=o/6*Math.PI/2;a.push(new vt(i*Math.cos(c),i*Math.sin(c)))}return new xi(a,n)}function m_(){let[i,t]=He(512,320);t.fillStyle="#1d2127",t.fillRect(0,0,512,320),t.fillStyle="#252a31",t.fillRect(0,0,512,22),t.fillRect(0,22,34,298),t.fillStyle="#f0934f",t.fillRect(40,4,90,14);let e=[[["#c678dd","def "],["#61afef","zamuda"],["#abb2bf","(vlak, postaja):"]],[["#7f848e","    # koliko vlak res zamuja"]],[["#abb2bf","    red = urnik[vlak][postaja]"]],[["#abb2bf","    res = meritve.zadnja(vlak)"]],[["#c678dd","    return "],["#abb2bf","res - red"]],[],[["#c678dd","for "],["#abb2bf","vlak "],["#c678dd","in "],["#61afef","vlaki_danes"],["#abb2bf","():"]],[["#abb2bf","    z = "],["#61afef","zamuda"],["#abb2bf","(vlak, "],["#98c379",'"\u0161ola"'],["#abb2bf",")"]],[["#61afef","    zapisi"],["#abb2bf","(vlak, z)"]],[],[["#7f848e","# +13 min"]]];return t.font='500 17px "IBM Plex Mono", monospace',t.textBaseline="middle",e.forEach((n,s)=>{let r=40+s*25;t.fillStyle="#5c6370",t.fillText(String(s+1).padStart(2," "),6,r);let a=44;for(let[o,c]of n)t.fillStyle=o,t.fillText(c,a,r),a+=t.measureText(c).width}),t.fillStyle="#abb2bf",t.fillRect(44+11*10.2,281,2,18),qe(i,{aniz:4})}function ef(i=p_){let t=new oe,e=(Ut,Dt=.75)=>new Ot({color:Ut,roughness:Dt}),n=e("#2c3850"),s=e("#4a5461",.85),r=e("#dcae92",.62),a=e("#3a2a1e",.8),o=e("#f0934f",.7),c=e("#b9622c",.7),l=e("#e6e4df",.6),u=e("#9c9890",.7),d=new oe;t.add(d);let h=.89,f=Ut=>Ut.map(([Dt,ft])=>new vt(Dt,ft)),g=new ct(new xi(f([[0,.78],[i.pas-.03,.79],[i.pas-.012,.84],[i.pas-.014,.9],[0,.92]]),18),n);g.scale.set(.66,1,1);let x=new ct(new xi(f([[0,.835],[i.pas+.002,.84],[i.pas+.009,.9],[i.pas+.006,.97],[i.pas,1.05],[fe(i.pas,i.prsi,.45),1.15],[i.prsi-.008,1.26],[i.prsi,1.34],[i.prsi-.02+i.trap*.6,1.41],[.11+i.trap,1.455],[.05+i.trap*.5,1.475],[0,1.476]]),22),s);x.scale.set(i.globina,1,1);let p=new ct((()=>{let Ut=new ci(.088+i.trap*.8,.044+i.trap*.3,8,14,Math.PI);return Ut.rotateX(Math.PI/2),Ut.rotateY(-Math.PI/2),Ut.scale(1,1.05,1.05),Ut})(),s);p.position.set(-.02,1.468,0);let m=new ct(new ve(i.vrat,i.vrat*1.12,.1,14),r);m.position.y=1.5;let y=new oe;y.position.y=1.54;let E=new ct(new Xn(.1,24,18),r);E.scale.set(.92,1.1,.84),E.position.set(.012,.085,0);let v=new ct(new Xn(.106,24,16,0,Math.PI*2,0,Math.PI*.56),a);v.scale.set(.95,1.08,.9),v.position.set(0,.1,0),v.rotation.z=.42;let b=new ct(new Xn(.104,20,14,-Math.PI/2,Math.PI,0,Math.PI*.74),a);b.scale.set(.95,1.1,.89),b.position.set(.006,.088,0);for(let Ut of[-1,1]){let Dt=new ct(new Xn(.022,10,8),r);Dt.scale.set(.9,1.5,.55),Dt.position.set(-.004,.075,Ut*.083),y.add(Dt)}let M=new ct(new Xn(.06,14,10,0,Math.PI*2,0,Math.PI*.5),a);M.scale.set(.9,.55,1.3),M.position.set(.055,.15,0),M.rotation.z=-.5,y.add(E,v,b,M);let A=i.prsi*i.globina,_=new oe,T=new ct(re(.15,.4,.29,.05),o),P=new ct(re(.05,.16,.22,.03),c);P.position.set(-.085,-.09,0),_.add(T,P);let L=-(A+.07);_.position.set(L,1.17,0),d.add(g,x,p,m,y,_);let F=[];for(let Ut of[-1,1]){let Dt=new ct(re(.014,.3,.042,.006),c);Dt.position.set(A-.006,1.2,Ut*(.085+i.trap)),Dt.rotation.z=.08;let ft=new ct(re(A*2+.02,.014,.042,.006),c);ft.position.set(0,1.43+i.trap*.5,Ut*(.09+i.trap)),d.add(Dt,ft),F.push(Dt,ft)}let V=[];for(let Ut of[-1,1]){let Dt=new oe;Dt.position.set(0,h,Ut*i.kolk),Dt.add(new ct(Xc(i.stegno,i.stegno*.72,.43,12,i.stegno*1.03,.3),n));let ft=new oe;ft.position.y=-.43,ft.add(new ct(Xc(i.meca*.9,i.meca*.66,.415,12,i.meca,.3),n));let N=new oe;N.position.y=-.415;let k=new ct(re(.25,.07,.094,.03),l);k.position.set(.055,-.03,0);let dt=new ct(re(.255,.022,.098,.01),u);dt.position.set(.055,-.064,0),N.add(k,dt),ft.add(N),Dt.add(ft),d.add(Dt),V.push({kolk:Dt,koleno:ft,gleznjar:N})}let I=[],z=.07+(i.nad-.047)*1.5;for(let Ut of[-1,1]){let Dt=new oe;Dt.position.set(0,1.375,Ut*(i.prsi+i.nad-.024)),Dt.rotation.x=-Ut*z;let ft=new oe;ft.add(new ct(Xc(i.nad*1.14,i.nad*.78,.27,12,i.nad*1.06,.45),s));let N=new oe;N.position.y=-.27,N.add(new ct(Xc(i.pod,i.pod*.76,.23,12,i.pod*1.05,.25),s));let k=new ct(new Xn(.045,12,10),r);k.scale.set(.42,1.75,.88),k.position.set(.004,-.305,0),N.add(k),ft.add(N),Dt.add(ft),d.add(Dt),I.push({rama:Dt,zamah:ft,komolec:N,dlan:k})}let q=new ct(re(.009,.15,.072,.008),new Ot({color:"#111",roughness:.3,emissive:"#5c7da8",emissiveIntensity:.6}));q.position.set(.035,-.32,0),q.rotation.z=-.2,I[1].komolec.add(q);let j=new Ot({color:"#9aa0a6",roughness:.35,metalness:.6}),at=new oe,K=new ct(re(.24,.018,.33,.006),j),st=new oe,it=new ct(re(.012,.21,.33,.005),j);it.position.set(.006,.105,0);let Rt=new ct(new je(.31,.19),new Ot({color:"#000",emissive:"#ffffff",emissiveMap:m_(),emissiveIntensity:1.15}));Rt.rotation.y=-Math.PI/2,Rt.position.set(-.002,.108,0),st.add(it,Rt),st.position.set(.12,.009,0),st.rotation.z=-.3,at.add(K,st),at.visible=!1,d.add(at),t.traverse(Ut=>{Ut.isMesh&&(Ut.castShadow=!0)});function mt(Ut=0,Dt=0,ft=1,N=0){let k=Ut/1.4*Math.PI*2,dt=Ut>0?1-N:0;V.forEach((St,Mt)=>{let Ft=k+(Mt?Math.PI:0),xt=.4*Math.sin(Ft)*dt,X=-(.06+.8*Math.max(0,Math.cos(Ft))**2)*dt;St.kolk.rotation.z=xt*(1-N)+N*1.48,St.koleno.rotation.z=X*(1-N)-N*1.5,St.gleznjar.rotation.z=-(St.kolk.rotation.z+St.koleno.rotation.z)*(dt?.75:1)}),I.forEach((St,Mt)=>{let Ft=k+(Mt?0:Math.PI),xt=Mt===1?ft:0,X=.32*Math.sin(Ft)*dt;St.zamah.rotation.z=(X*(1-xt)+xt*.25)*(1-N)+N*.25,St.komolec.rotation.z=((.18+.2*Math.max(0,Math.sin(Ft))*dt)*(1-xt)+xt*1.75)*(1-N)+N*.78,St.rama.rotation.x=-(Mt?1:-1)*(z-xt*.1)}),q.visible=N<.5,at.visible=N>.5;for(let St of F)St.visible=N<.5;N>.5?(_.position.set(-.04,1.035,-.52),_.rotation.set(0,.35,0)):(_.position.set(L,1.17,0),_.rotation.set(0,0,0)),d.position.y=N*-.36+(dt?-.018*Math.abs(Math.sin(k)):0),d.rotation.y=dt*.05*Math.sin(k),at.position.set(.27,h+.009+i.stegno,0),y.rotation.y=Dt,y.rotation.z=-.42*ft*(1-N)-N*.32}return mt(0),{skupina:t,poza:mt,tel:q,zaslon:Rt}}function nf(){let i=new oe,t=_n(17),e=h_();e.bar.repeat.set((ue.x1-ue.x0)/2,1),e.nor.repeat.copy(e.bar.repeat);let n=ue.z1-ue.z0,s=ue.x1-ue.x0,r=new je(s,n);r.rotateX(-Math.PI/2);let a=r.attributes.uv;for(let G=0;G<a.count;G++)a.setXY(G,a.getX(G),1-a.getY(G));let o=new ct(r,new Ot({map:e.bar,normalMap:e.nor,roughness:.88}));o.material.map.wrapT=Wn,o.position.set((ue.x0+ue.x1)/2,ue.y,(ue.z0+ue.z1)/2),o.receiveShadow=!0,i.add(o);let c=new Ot({color:"#8f8b83",roughness:.92}),l=new ct(new Ce(s,1.45,n),c);l.position.set((ue.x0+ue.x1)/2,ue.y-.75,(ue.z0+ue.z1)/2),l.receiveShadow=!0,i.add(l);let u=new ct(new Ce(s,.12,.34),new Ot({color:"#cfccc4",roughness:.8}));u.position.set((ue.x0+ue.x1)/2,ue.y-.07,ue.z0+.13),u.receiveShadow=!0,i.add(u);for(let G of[-1,1]){let et=new ct(new Ce(8,.1,n),c);et.position.set(G*(s/2+3.6),ue.y-.32,(ue.z0+ue.z1)/2),et.rotation.z=G*.07,et.receiveShadow=!0,i.add(et)}let d=-31,h=31,f=2.35,g=7.4,x=ue.y+3.55,p=new Ot({color:"#3a3f45",roughness:.5,metalness:.55}),m=new ct(re(h-d,.28,g-f,.03),new Ot({color:"#d4d2cc",roughness:.7}));m.position.set(0,x+.14,(f+g)/2),m.castShadow=!0,m.receiveShadow=!0;let y=new ct(re(h-d+.1,.34,.08,.02),p);y.position.set(0,x+.15,f),i.add(m,y);let E=new Tn(re(.2,x-ue.y,.2,.02),p,9),v=new de;for(let G=0;G<9;G++)v.makeTranslation(d+3+G*7,ue.y+(x-ue.y)/2,6.3),E.setMatrixAt(G,v);E.castShadow=!0,i.add(E);let b=new Ot({color:"#fff",emissive:"#fff3dc",emissiveIntensity:.6});for(let G of[3.1,6]){let et=new ct(new Ce(h-d-2,.04,.16),b);et.position.set(0,x-.02,G),i.add(et)}let M=f_();i.add(M.skupina);let A=d_(),_=new oe,T=new ct(re(2.3,.72,.16,.03),new Ot({color:"#202327",roughness:.45,metalness:.4})),P=new Ot({color:"#000",emissive:"#ffffff",emissiveMap:A.tex,emissiveIntensity:1.5,roughness:.25,map:A.tex});for(let G of[1,-1]){let et=new ct(new je(2.14,.6),P);et.position.z=G*.081,G<0&&(et.rotation.y=Math.PI),_.add(et)}let L=new ct(new ve(.02,.02,.3,8),p);for(let G of[-.8,.8]){let et=L.clone();et.position.set(G,.5,0),_.add(et)}_.add(T),_.rotation.y=-Math.PI/2,_.position.set(Dh.x,Dh.y,Dh.z),i.add(_);let F=We([[new ve(.05,.07,5.6,10),"#3a3f45",qt(0,2.8,0)],[re(.7,.1,.22,.03),"#3a3f45",qt(-.25,5.62,0)]]),V=new Ot({vertexColors:!0,roughness:.5,metalness:.5}),I=[];for(let G=-88;G<=88;G+=16)Math.abs(G)>33&&I.push(G);let z=new Tn(F,V,I.length),q=new Ce(.6,.03,.16),j=new Tn(q,new Ot({color:"#fff",emissive:"#ffe2b0",emissiveIntensity:.4}),I.length);I.forEach((G,et)=>{v.makeTranslation(G,ue.y,7),z.setMatrixAt(et,v),v.makeTranslation(G-.25,ue.y+5.56,7),j.setMatrixAt(et,v)}),z.castShadow=!0,i.add(z,j);let at=We([[re(1.8,.05,.42,.01),"#8b5a35",qt(0,.45,0)],[re(1.8,.4,.05,.01),"#8b5a35",qt(0,.75,.2,-.12,0,0)],[re(.06,.45,.4,.01),"#2f3338",qt(-.75,.22,0)],[re(.06,.45,.4,.01),"#2f3338",qt(.75,.22,0)]]),K=new Ot({vertexColors:!0,roughness:.7});for(let G of[-17.5,10.5,24.5]){let et=new ct(at,K);et.position.set(G,ue.y,6.9),et.castShadow=!0,i.add(et)}let[st,it]=He(128,128);it.fillStyle="#f4f4f0",it.fillRect(0,0,128,128),it.strokeStyle="#1b3f8b",it.lineWidth=8,it.strokeRect(4,4,120,120),it.fillStyle="#1b3f8b",it.font='600 92px "IBM Plex Sans", sans-serif',it.textAlign="center",it.textBaseline="middle",it.fillText("1",64,70);let Rt=new Ot({map:qe(st),roughness:.6});for(let G of[-36,36]){let et=new oe,gt=new ct(new ve(.04,.04,3.2,8),p);gt.position.y=1.6;let Bt=new ct(new Ce(.03,.5,.5),[p,p,p,p,Rt,Rt]);Bt.position.y=2.9;let bt=Bt.clone();bt.rotation.y=Math.PI/2,bt.position.y=2.9,et.add(gt,bt),et.position.set(G,ue.y,2.9),et.traverse(jt=>{jt.isMesh&&(jt.castShadow=!0)}),i.add(et)}let mt={x:0,z:17.5,w:30,d:10,h:8.2},Ut=tf(mt.w,2,9,{loki:!0,vrata:[4],seme:3}),Dt=tf(mt.d,2,3,{loki:!0,seme:5}),ft=G=>new Ot({map:G.bar,emissiveMap:G.emis,emissive:"#ffffff",emissiveIntensity:0,roughness:.85}),N=ft(Ut),k=ft(Dt),dt=new ct(new Ce(mt.w,mt.h,mt.d),[k,k,c,c,N,N]);dt.position.set(mt.x,ue.y+mt.h/2-.3,mt.z),dt.castShadow=!0,dt.receiveShadow=!0,i.add(dt);let St=Mr();St.bar.repeat.set(.5,.5),St.nor.repeat.set(.5,.5);let Mt=new Ot({map:St.bar,normalMap:St.nor,roughness:.8}),Ft=new ct(Rs(mt.w,mt.d,3.4,.7),Mt);Ft.position.set(mt.x,ue.y+mt.h-.3,mt.z),Ft.castShadow=!0,Ft.receiveShadow=!0,i.add(Ft);for(let G of[-9,7]){let et=new ct(re(.6,1.6,.6,.02),new Ot({color:"#b9a98f",roughness:.9}));et.position.set(G,ue.y+mt.h+2.2,mt.z+1.5),et.castShadow=!0,i.add(et)}let xt=new ct(new Ce(9,4.6,8),[k,k,c,c,N,N]);xt.position.set(mt.x+mt.w/2+4.5,ue.y+2,mt.z+.6),xt.castShadow=!0,xt.receiveShadow=!0;let X=new ct(Rs(9,8,2.2,.5),Mt);X.position.set(mt.x+mt.w/2+4.5,ue.y+4.3,mt.z+.6),X.castShadow=!0,i.add(xt,X);let tt=new ct(new je(70,6),new Ot({color:"#8a8780",roughness:.95}));return tt.rotation.x=-Math.PI/2,tt.position.set(5,ue.y-.01,10.6),tt.receiveShadow=!0,i.add(tt),{skupina:i,ura:M,tabla:A,fasade:[N,k],luci:[b,j.material]}}var sf=jn(101),Nh=jn(202),g_=jn(303),Zn={x:-1520,z:-430},Sr={x:-3290,z:62};function Hi(i,t,e){let n=e.zPriX(Math.max(-3990,Math.min(1390,i))),s=n-t,r=-.85+1.4*Cn(sf,i/380,t/380,3),a=Se(220,1500,s);r+=a*(110+190*(.5+.5*Cn(Nh,i/1100,t/1100,4))),r+=a*40*Cn(g_,i/260,t/260,3);let o=Se(500,1700,-s);r+=o*(40+80*(.5+.5*Cn(Nh,i/900+7,t/900,3)));let c=Math.hypot(i-Zn.x,t-Zn.z);r+=34*Math.exp(-(c*c)/(300*150));let l=Se(16,70,Math.abs(s));r=fe(-.85,r,l);let u=(f,g,x,p)=>{let m=Math.max(Math.abs(i-f)/x,Math.abs(t-g)/p);return 1-Se(.75,1,m)},d=u(30,120,190,112),h=u(-3260,150,200,140);return r=fe(r,.25+.6*Cn(sf,i/200,t/200,2),Math.max(d,h)*Se(9,14,t-n)),i>-48&&i<72&&t-n>6&&t-n<30&&(r=Math.min(r,.4)),r}function rf(i,t,e){let n=Cn(Nh,i/520+3.1,t/520-1.7,3);return Be((n+Se(8,60,e)*.55-.08)*3)}var v_=`
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
`;function af(i){let a=Math.round(320),o=Math.round(5e3/20),c=new je(6400,5e3,a,o);c.rotateX(-Math.PI/2),c.translate(-2800/2,0,-1400/2);let l=c.attributes.position,u=new Float32Array(l.count);for(let m=0;m<l.count;m++){let y=l.getX(m),E=l.getZ(m),v=Hi(y,E,i);l.setY(m,v),u[m]=rf(y,E,v)*Se(28,70,Math.abs(i.zPriX(Math.max(-3990,Math.min(1390,y)))-E))}c.setAttribute("aGozd",new Ue(u,1)),c.computeVertexNormals();let d=new Ot({color:"#ffffff",roughness:.95});d.onBeforeCompile=m=>{m.vertexShader=m.vertexShader.replace("#include <common>",`#include <common>
attribute float aGozd;
varying float vGozd;
varying vec3 vSvet;`).replace("#include <begin_vertex>",`#include <begin_vertex>
vGozd = aGozd;
vSvet = (modelMatrix * vec4(position, 1.0)).xyz;`),m.fragmentShader=m.fragmentShader.replace("#include <common>",`#include <common>
varying float vGozd;
`+v_+`
float _hr;`).replace("#include <color_fragment>",`#include <color_fragment>
diffuseColor.rgb = teren(vSvet, vGozd, _hr);`).replace("#include <roughnessmap_fragment>",`#include <roughnessmap_fragment>
roughnessFactor = _hr;`)},d.customProgramCacheKey=()=>"teren";let h=64,f=50,g=[],x=[];for(let m=0;m<o;m+=f)for(let y=0;y<a;y+=h){let E=g.length;for(let v=m;v<Math.min(m+f,o);v++)for(let b=y;b<Math.min(y+h,a);b++){let M=b+(a+1)*v,A=b+(a+1)*(v+1);g.push(M,A,M+1,A,A+1,M+1)}x.push([E,g.length])}c.setIndex(g);let p=new oe;for(let m of Oc(c,x)){let y=new ct(m,d);y.receiveShadow=!0,p.add(y)}return p}function x_(){let i=[];i.push([new ve(.12,.18,2.2,6),"#4a3626",qt(0,1.1,0)]);let t=[[1.7,3.6,2.4],[1.35,3.4,4.4],[.95,3.2,6.3],[.55,2.6,8]];for(let[e,n,s]of t)i.push([new Ki(e,n,8),"#ffffff",qt(0,s,0)]);return We(i)}function __(){return We([[new Ki(1.8,8.6,5),"#ffffff",qt(0,4.6,0)]])}function y_(){let i=new or(2.8,0);return i.scale(1,1.2,1),We([[i,"#ffffff",qt(0,5.2,0)]])}function M_(i){let t=_n(i),e=new or(2.6,1),n=e.attributes.position,s=jn(i);for(let a=0;a<n.count;a++){let o=new C().fromBufferAttribute(n,a),c=1+.28*s(o.x*.9+3,o.y*.9+o.z*.7);o.multiplyScalar(c),o.y*=1.15,n.setXYZ(a,o.x,o.y,o.z)}e.computeVertexNormals();let r=[[new ve(.16,.24,3.6,6),"#4d3b2b",qt(0,1.8,0)],[e,"#ffffff",qt(0,5+t(),0)]];return We(r)}var S_=["#a8641f","#c48a2c","#8c4a1c","#b5772a","#6f7a2c","#5d6b28","#d0a23a","#7f3f1a"],b_=["#2d4632","#26402c","#33503a","#2a3f2f"];function of(i,t=[],e=1){let n=(E,v)=>t.some(([b,M,A])=>(E-b)**2+(v-M)**2<A*A),s=new oe,r=_n(77),a=x_(),o=M_(5),c=__(),l=y_(),u=new Ot({vertexColors:!0,roughness:.92}),d=500,h=new Map,f=(E,v,b,M,A,_=A)=>{let T=`${Math.floor(E/d)},${Math.floor(v/d)},${b?1:0},${A?1:0},${_?1:0}`;h.has(T)||h.set(T,[]),h.get(T).push([E,v,M])};for(let E=0;E<3e4*e;E++){let v=-4400+r()*5900,b=i.zPriX(Math.max(-3990,Math.min(1390,v))),M=(r()<.75?-1:1)*(35+Math.pow(r(),1.6)*1400),A=b+M,_=Hi(v,A,i),T=rf(v,A,_);if(r()>T*.9||Math.abs(v-30)<220&&A>b&&A<b+240||Math.abs(v+3260)<230&&A>b&&A<b+300||Math.hypot(v-Zn.x,A-Zn.z)<70||n(v,A))continue;let P=r()<.38+.3*Se(40,200,_);f(v,A,P,.75+r()*.75,Math.abs(M)<150,Math.abs(M)<320||Math.hypot(v-Zn.x,A-Zn.z)<400)}for(let E=0;E<1600;E++){let v=-4300+r()*5600,b=i.zPriX(Math.max(-3990,Math.min(1390,v))),M=b+(r()<.5?-1:1)*(22+r()*600);Math.abs(v-30)<200&&M>b&&M<b+240||Math.abs(v+3260)<230&&M>b&&M<b+300||n(v,M)||f(v,M,r()<.2,.7+r()*.6,Math.abs(M-b)<160)}let g=new de,x=new sn,p=new Wt,m=new C(0,1,0),y=0;for(let[E,v]of h){let b=E.split(",")[2]==="1",M=E.split(",")[3]==="1",A=E.split(",")[4]==="1",_=new Tn(A?b?a:o:b?c:l,u,v.length);v.forEach(([T,P,L],F)=>{let V=Hi(T,P,i);x.setFromAxisAngle(m,r()*Math.PI*2);let I=L*(.85+r()*.3);g.compose(new C(T,V-.2,P),x,new C(I,L*(b?1.15+r()*.5:.9+r()*.35),I)),_.setMatrixAt(F,g),p.set((b?b_:S_)[Math.floor(r()*(b?4:8))]),p.offsetHSL(0,0,(r()-.5)*.06),_.setColorAt(F,p)}),_.castShadow=M,_.receiveShadow=!1,_.computeBoundingSphere(),s.add(_),y+=v.length}return s.userData.stevilo=y,s}function E_(){let[i,t]=He(256,256),[e,n]=He(256,256);t.fillStyle="#ffffff",t.fillRect(0,0,256,256),n.fillStyle="#000",n.fillRect(0,0,256,256);let s=_n(31);for(let r of[40,150])for(let a of[30,110,190])t.fillStyle="#d8d2c6",t.fillRect(a-4,r-4,44,56),t.fillStyle="#2b2a28",t.fillRect(a,r,36,48),t.fillStyle="#6b4a2f",t.fillRect(a-12,r,10,48),t.fillRect(a+38,r,10,48),s()<.45&&(n.fillStyle="#ffcf8a",n.fillRect(a+2,r+2,32,44));return{bar:qe(i),emis:qe(e)}}function cf(i){let t=new oe,e=_n(55),n=[],s=(E,v,b,M,A=0)=>{for(let _=0,T=0;_<b&&T<b*8;T++){let P=e()*Math.PI*2,L=Math.sqrt(e())*M,F=E+Math.cos(P)*L,V=v+Math.sin(P)*L,I=i.zPriX(Math.max(-3990,Math.min(1390,F)));Math.abs(V-I)<26||n.some(z=>Math.hypot(z.x-F,z.z-V)<17)||(n.push({x:F,z:V,w:8+e()*4,d:9+e()*3,h:5.5+e()*1.8,rot:A+(e()<.5?0:Math.PI/2)+(e()-.5)*.25}),_++)}};s(60,120,46,175),s(-60,-70,16,90),s(-1250,170,24,120),s(Zn.x+40,Zn.z+120,16,90),s(-3200,170,50,200),s(-2400,-260,12,80),s(-600,260,10,70);let r=new Ce(1,1,1);r.translate(0,.5,0);let a=E_(),o=new Ot({map:a.bar,emissiveMap:a.emis,emissive:"#ffffff",emissiveIntensity:0,roughness:.9}),c=new ge;{let M=[[-.56,0,-.56],[.56,0,-.56],[.56,.55,0],[-.56,.55,0],[.56,0,.56],[-.56,0,.56]],A=[[0,3,2],[0,2,1],[4,2,3],[4,3,5],[5,3,0],[1,2,4]],_=[],T=[];for(let P of A)for(let L of P)_.push(...M[L]),T.push(M[L][0]*6,(M[L][1]+Math.abs(M[L][2]))*6);c.setAttribute("position",new te(_,3)),c.setAttribute("uv",new te(T,2)),c.computeVertexNormals()}let l=Mr([160,70,46]),u=new Ot({map:l.bar,normalMap:l.nor,roughness:.82}),d=new Tn(r,o,n.length),h=new Tn(c,u,n.length),f=new de,g=new sn,x=new Wt,p=new C(0,1,0),m=["#ece6d8","#e9dfc4","#f1ede4","#e2d3b1","#dcd6cb","#efe2c6"],y=["#ffffff","#e8d6cf","#c9b8b0","#f0e4dc"];n.forEach((E,v)=>{let b=Hi(E.x,E.z,i)-.3;g.setFromAxisAngle(p,E.rot),f.compose(new C(E.x,b,E.z),g,new C(E.w,E.h,E.d)),d.setMatrixAt(v,f),x.set(m[Math.floor(e()*m.length)]),d.setColorAt(v,x),f.compose(new C(E.x,b+E.h,E.z),g,new C(E.w*1.05,E.w*.95,E.d*1.05)),h.setMatrixAt(v,f),x.set(y[Math.floor(e()*y.length)]),h.setColorAt(v,x)});for(let E of[d,h])E.castShadow=!0,E.receiveShadow=!0,E.computeBoundingSphere(),t.add(E);return t.userData.okna=o,t}function lf(i){let t=new oe,e=new Ot({color:"#efebe2",roughness:.85}),n=Mr([150,64,42]);n.bar.repeat.set(.4,.4),n.nor.repeat.set(.4,.4);let s=new Ot({map:n.bar,normalMap:n.nor,roughness:.8}),r=new Ot({color:"#3b4146",roughness:.55,metalness:.3}),a=new Ot({color:"#1d1f22",roughness:.8}),o=Hi(Zn.x,Zn.z,i)-.5,c=new ct(new Ce(20,8.5,9.5),e);c.position.set(0,4.25,0);let l=new ct(Rs(20,9.5,5.2,.6),s);l.position.set(0,8.5,0);let u=new ct(new Ce(7,7.2,7.5),e);u.position.set(13,3.6,0);let d=new ct(Rs(7,7.5,3.6,.5),s);d.position.set(13,7.2,0);let h=new ct(new Ce(5,24,5),e);h.position.set(-12,12,0);let f=new ct(new Ki(3.7,13,8),r);f.rotation.y=Math.PI/8,f.position.set(-12,24+6.5,0);let g=new ct(We([[re(.12,1.6,.12,0),"#c9a54a"],[re(.12,.12,.9,0),"#c9a54a",qt(0,.35,0)]]),new Ot({vertexColors:!0,metalness:.8,roughness:.3}));g.position.set(-12,37.8,0),t.add(c,l,u,d,h,f,g);for(let[x,p,m]of[[2.52,0,Math.PI/2],[-2.52,0,-Math.PI/2],[0,2.52,0],[0,-2.52,Math.PI]]){let y=new ct(new je(1.4,2.6),a);y.position.set(-12+x,20.5,p),y.rotation.y=m,t.add(y)}for(let x=0;x<4;x++)for(let p of[-1,1]){let m=new ct(new je(1.3,3.2),a);m.position.set(-6+x*4.2,5,p*4.77),m.rotation.y=p>0?0:Math.PI,t.add(m)}return t.position.set(Zn.x,o,Zn.z),t.rotation.y=.18,t.traverse(x=>{x.isMesh&&(x.castShadow=!0,x.receiveShadow=!0)}),t}function hf(){let i=[],t="#5d4330",e="#4a3626",n="#b8a050";for(let d=0;d<=3;d++){for(let h of[-1,1])i.push([re(.32,6.6,.32,.03),t,qt(-13/2+d*(13/3),6.6/2,h*5.2/2)]);i.push([re(.22,.25,5.2+.6,.02),e,qt(-13/2+d*(13/3),6.6-.3,0)]),i.push([re(.2,.22,5.2,.02),e,qt(-13/2+d*(13/3),2.3,0)])}for(let d of[-1,1]){for(let h=0;h<10;h++)i.push([re(13+.4,.07,.08,.01),t,qt(0,.9+h*.52,d*(5.2/2+.18))]);for(let h=0;h<4;h++)i.push([re(13*.9,.42,.18,.06),n,qt(.3,1.2+h*1.05,d*(5.2/2+.3))])}i.push([re(13+.4,.2,5.2-.4,.02),e,qt(0,3.4,0)]);let o=new oe,c=new ct(We(i),new Ot({vertexColors:!0,roughness:.92})),l=Mr([118,70,50]);l.bar.repeat.set(.5,.5),l.nor.repeat.set(.5,.5);let u=new ct(Rs(13+1.2,5.2+1.6,2.6,.2),new Ot({map:l.bar,normalMap:l.nor,roughness:.85}));return u.position.y=6.6,o.add(c,u),o.traverse(d=>{d.isMesh&&(d.castShadow=!0,d.receiveShadow=!0)}),o}function uf(i){let t=new oe,e=32,n=46,s=12.6,[r,a]=He(n*e,Math.round(s*e)),[o,c]=He(n*e,Math.round(s*e));a.fillStyle="#e8c87e",a.fillRect(0,0,r.width,r.height),c.fillStyle="#000",c.fillRect(0,0,r.width,r.height),a.fillStyle="#b39a6c",a.fillRect(0,r.height-.9*e,r.width,.9*e),a.fillStyle="#f5ead3";for(let y of[.25,4.1,8])a.fillRect(0,y*e,r.width,.22*e);let l=_n(8);for(let y=0;y<3;y++)for(let E=0;E<14;E++){let v=(1.6+E*3.08)*e,b=r.height-(1.6+y*3.85+2.2)*e;a.fillStyle="#f5ead3",a.fillRect(v-5,b-5,1.3*e+10,2.2*e+10),a.fillStyle="#2b3036",a.fillRect(v,b,1.3*e,2.2*e),a.fillStyle="#e9e2d0",a.fillRect(v+.63*e,b,3,2.2*e),a.fillRect(v,b+.7*e,1.3*e,3),c.fillStyle=l()<.8?"#ffe9c0":"#000",c.fillRect(v+2,b+2,1.3*e-4,2.2*e-4)}a.fillStyle="#5a3d2b",a.fillRect(r.width/2-1.2*e,r.height-3.6*e,2.4*e,2.7*e),a.fillStyle="#3a2f26",a.font=`600 ${.9*e}px "IBM Plex Sans", sans-serif`,a.textAlign="center",a.fillText("\u0160OLA",r.width/2,r.height-4.2*e);let u=new Ot({map:qe(r),emissiveMap:qe(o),emissive:"#ffffff",emissiveIntensity:0,roughness:.85}),d=new Ot({color:"#e5c57b",roughness:.85}),h=new ct(new Ce(n,s,15),[d,d,d,d,u,u]);h.position.y=s/2;let f=Mr([120,58,40]);f.bar.repeat.set(.5,.5),f.nor.repeat.set(.5,.5);let g=new ct(Rs(n,15,5.5,.7),new Ot({map:f.bar,normalMap:f.nor,roughness:.8}));g.position.y=s;let x=new ct(new Ce(2.4,3.2,2.4),new Ot({color:"#f5ead3",roughness:.8}));x.position.set(0,s+5.2,0);let p=new ct(new Ki(1.9,2.6,4),new Ot({color:"#3d4448",roughness:.5,metalness:.4}));p.rotation.y=Math.PI/4,p.position.set(0,s+8.1,0),t.add(h,g,x,p);let m=Hi(Sr.x,Sr.z,i)-.2;return t.position.set(Sr.x,m,Sr.z),t.rotation.y=Math.PI,t.traverse(y=>{y.isMesh&&(y.castShadow=!0,y.receiveShadow=!0)}),t.userData.okna=u,t.userData.zvonec=new C(Sr.x,m+s+5.2,Sr.z),t}function df(){let e=[],n=[],s=[],r=jn(909);for(let l=0;l<=26;l++){let u=5200+Math.pow(l/26,1.3)*32e3;for(let d=0;d<=256;d++){let h=d/256*Math.PI*2,f=Math.cos(h)*u-1400,g=Math.sin(h)*u-600,x=Se(-.2,.75,-Math.sin(h)),p=1-Math.abs(Cn(r,f/5200,g/5200,5)),m=(180+420*Cn(r,f/3e3+9,g/3e3,4))*Se(5200,9e3,u);m+=x*Math.pow(p,2.2)*2600*Se(9e3,2e4,u),m*=1-Se(3e4,37e3,u),e.push(f,m-30,g),s.push(m)}}for(let l=0;l<26;l++)for(let u=0;u<256;u++){let d=l*257+u,h=d+1,f=d+256+1,g=f+1;n.push(d,f,h,h,f,g)}let a=new ge;a.setAttribute("position",new te(e,3)),a.setAttribute("aVis",new te(s,1)),a.setIndex(n),a.computeVertexNormals();let o=new Ot({color:"#ffffff",roughness:.95});o.onBeforeCompile=l=>{l.vertexShader=l.vertexShader.replace("#include <common>",`#include <common>
attribute float aVis;
varying float vVis;
varying float vNY;`).replace("#include <begin_vertex>",`#include <begin_vertex>
vVis = aVis;
vNY = normal.y;`),l.fragmentShader=l.fragmentShader.replace("#include <common>",`#include <common>
varying float vVis;
varying float vNY;`).replace("#include <color_fragment>",`#include <color_fragment>
        vec3 c = mix(vec3(0.16, 0.2, 0.12), vec3(0.32, 0.3, 0.28), smoothstep(900.0, 1500.0, vVis));
        c = mix(c, vec3(0.92, 0.93, 0.95), smoothstep(1750.0, 2000.0, vVis + 160.0 * vNY));
        diffuseColor.rgb = c;`)},o.customProgramCacheKey=()=>"gore";let c=new ct(a,o);return c.frustumCulled=!1,c}function ff(i,t){let e=new oe,[n,s]=He(256,256),r=jn(404),a=s.createImageData(256,256);for(let d=0;d<256;d++)for(let h=0;h<256;h++){let f=Cn(r,h/48,d/48,4)*.5+.5,g=(h-128)/128,x=(d-128)/128,p=Be(1-Math.sqrt(g*g+x*x)),m=Be((f-.32)*1.8)*Math.pow(p,.6),y=(d*256+h)*4;a.data[y]=a.data[y+1]=a.data[y+2]=255,a.data[y+3]=m*255}s.putImageData(a,0,0);let o=qe(n,{srgb:!1}),c=new Oe({uniforms:{...i,uTex:{value:o},uMoc:{value:1}},vertexShader:`
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
      }`,transparent:!0,depthWrite:!1}),l=_n(12),u=[[400,-60],[180,60],[-300,40],[-700,-80],[-1100,60],[-1500,-120],[-1900,40],[-2300,-60],[-2700,30],[800,20],[-200,-260],[-1e3,-340]];for(let[d,h]of u){let f=700+l()*600,g=new ct(new je(f,f*.7),c);g.rotation.x=-Math.PI/2,g.rotation.z=l()*Math.PI,g.position.set(d,2+l()*7,h),g.renderOrder=5,e.add(g)}return e.userData.mat=c,e}var pf=new an,qc=new C,hi=class extends da{constructor(){super(),this.isLineSegmentsGeometry=!0,this.type="LineSegmentsGeometry";let t=[-1,2,0,1,2,0,-1,1,0,1,1,0,-1,0,0,1,0,0,-1,-1,0,1,-1,0],e=[-1,2,1,2,-1,1,1,1,-1,-1,1,-1,-1,-2,1,-2],n=[0,2,1,2,3,1,2,4,3,4,5,3,4,6,5,6,7,5];this.setIndex(n),this.setAttribute("position",new te(t,3)),this.setAttribute("uv",new te(e,2))}applyMatrix4(t){let e=this.attributes.instanceStart,n=this.attributes.instanceEnd;return e!==void 0&&(e.applyMatrix4(t),n.applyMatrix4(t),e.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}setPositions(t){let e;t instanceof Float32Array?e=t:Array.isArray(t)&&(e=new Float32Array(t));let n=new ss(e,6,1);return this.setAttribute("instanceStart",new ai(n,3,0)),this.setAttribute("instanceEnd",new ai(n,3,3)),this.instanceCount=this.attributes.instanceStart.count,this.computeBoundingBox(),this.computeBoundingSphere(),this}setColors(t){let e;t instanceof Float32Array?e=t:Array.isArray(t)&&(e=new Float32Array(t));let n=new ss(e,6,1);return this.setAttribute("instanceColorStart",new ai(n,3,0)),this.setAttribute("instanceColorEnd",new ai(n,3,3)),this}fromWireframeGeometry(t){return this.setPositions(t.attributes.position.array),this}fromEdgesGeometry(t){return this.setPositions(t.attributes.position.array),this}fromMesh(t){return this.fromWireframeGeometry(new ra(t.geometry)),this}fromLineSegments(t){let e=t.geometry;return this.setPositions(e.attributes.position.array),this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new an);let t=this.attributes.instanceStart,e=this.attributes.instanceEnd;t!==void 0&&e!==void 0&&(this.boundingBox.setFromBufferAttribute(t),pf.setFromBufferAttribute(e),this.boundingBox.union(pf))}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new wn),this.boundingBox===null&&this.computeBoundingBox();let t=this.attributes.instanceStart,e=this.attributes.instanceEnd;if(t!==void 0&&e!==void 0){let n=this.boundingSphere.center;this.boundingBox.getCenter(n);let s=0;for(let r=0,a=t.count;r<a;r++)qc.fromBufferAttribute(t,r),s=Math.max(s,n.distanceToSquared(qc)),qc.fromBufferAttribute(e,r),s=Math.max(s,n.distanceToSquared(qc));this.boundingSphere.radius=Math.sqrt(s),isNaN(this.boundingSphere.radius)&&console.error("THREE.LineSegmentsGeometry.computeBoundingSphere(): Computed radius is NaN. The instanced position data is likely to have NaN values.",this)}}toJSON(){}};Nt.line={worldUnits:{value:1},linewidth:{value:1},resolution:{value:new vt},dashOffset:{value:0},dashScale:{value:1},dashSize:{value:1},gapSize:{value:1}};An.line={uniforms:ba.merge([Nt.common,Nt.fog,Nt.line]),vertexShader:`
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
		`};var $n=class extends Oe{constructor(t){super({type:"LineMaterial",uniforms:ba.clone(An.line.uniforms),vertexShader:An.line.vertexShader,fragmentShader:An.line.fragmentShader,clipping:!0}),this.isLineMaterial=!0,this.setValues(t)}get color(){return this.uniforms.diffuse.value}set color(t){this.uniforms.diffuse.value=t}get worldUnits(){return"WORLD_UNITS"in this.defines}set worldUnits(t){t===!0!==this.worldUnits&&(this.needsUpdate=!0),t===!0?this.defines.WORLD_UNITS="":delete this.defines.WORLD_UNITS}get linewidth(){return this.uniforms.linewidth.value}set linewidth(t){this.uniforms.linewidth&&(this.uniforms.linewidth.value=t)}get dashed(){return"USE_DASH"in this.defines}set dashed(t){t===!0!==this.dashed&&(this.needsUpdate=!0),t===!0?this.defines.USE_DASH="":delete this.defines.USE_DASH}get dashScale(){return this.uniforms.dashScale.value}set dashScale(t){this.uniforms.dashScale.value=t}get dashSize(){return this.uniforms.dashSize.value}set dashSize(t){this.uniforms.dashSize.value=t}get dashOffset(){return this.uniforms.dashOffset.value}set dashOffset(t){this.uniforms.dashOffset.value=t}get gapSize(){return this.uniforms.gapSize.value}set gapSize(t){this.uniforms.gapSize.value=t}get opacity(){return this.uniforms.opacity.value}set opacity(t){this.uniforms&&(this.uniforms.opacity.value=t)}get resolution(){return this.uniforms.resolution.value}set resolution(t){this.uniforms.resolution.value.copy(t)}get alphaToCoverage(){return"USE_ALPHA_TO_COVERAGE"in this.defines}set alphaToCoverage(t){this.defines&&(t===!0!==this.alphaToCoverage&&(this.needsUpdate=!0),t===!0?this.defines.USE_ALPHA_TO_COVERAGE="":delete this.defines.USE_ALPHA_TO_COVERAGE)}};var Fh=new xe,mf=new C,gf=new C,cn=new xe,ln=new xe,bi=new xe,zh=new C,Oh=new de,hn=new fa,vf=new C,Yc=new an,jc=new wn,Ei=new xe,wi,Cs;function xf(i,t,e){return Ei.set(0,0,-t,1).applyMatrix4(i.projectionMatrix),Ei.multiplyScalar(1/Ei.w),Ei.x=Cs/e.width,Ei.y=Cs/e.height,Ei.applyMatrix4(i.projectionMatrixInverse),Ei.multiplyScalar(1/Ei.w),Math.abs(Math.max(Ei.x,Ei.y))}function w_(i,t){let e=i.matrixWorld,n=i.geometry,s=n.attributes.instanceStart,r=n.attributes.instanceEnd,a=Math.min(n.instanceCount,s.count);for(let o=0,c=a;o<c;o++){hn.start.fromBufferAttribute(s,o),hn.end.fromBufferAttribute(r,o),hn.applyMatrix4(e);let l=new C,u=new C;wi.distanceSqToSegment(hn.start,hn.end,u,l),u.distanceTo(l)<Cs*.5&&t.push({point:u,pointOnLine:l,distance:wi.origin.distanceTo(u),object:i,face:null,faceIndex:o,uv:null,uv1:null})}}function T_(i,t,e){let n=t.projectionMatrix,r=i.material.resolution,a=i.matrixWorld,o=i.geometry,c=o.attributes.instanceStart,l=o.attributes.instanceEnd,u=Math.min(o.instanceCount,c.count),d=-t.near;wi.at(1,bi),bi.w=1,bi.applyMatrix4(t.matrixWorldInverse),bi.applyMatrix4(n),bi.multiplyScalar(1/bi.w),bi.x*=r.x/2,bi.y*=r.y/2,bi.z=0,zh.copy(bi),Oh.multiplyMatrices(t.matrixWorldInverse,a);for(let h=0,f=u;h<f;h++){if(cn.fromBufferAttribute(c,h),ln.fromBufferAttribute(l,h),cn.w=1,ln.w=1,cn.applyMatrix4(Oh),ln.applyMatrix4(Oh),cn.z>d&&ln.z>d)continue;if(cn.z>d){let E=cn.z-ln.z,v=(cn.z-d)/E;cn.lerp(ln,v)}else if(ln.z>d){let E=ln.z-cn.z,v=(ln.z-d)/E;ln.lerp(cn,v)}cn.applyMatrix4(n),ln.applyMatrix4(n),cn.multiplyScalar(1/cn.w),ln.multiplyScalar(1/ln.w),cn.x*=r.x/2,cn.y*=r.y/2,ln.x*=r.x/2,ln.y*=r.y/2,hn.start.copy(cn),hn.start.z=0,hn.end.copy(ln),hn.end.z=0;let x=hn.closestPointToPointParameter(zh,!0);hn.at(x,vf);let p=Mi.lerp(cn.z,ln.z,x),m=p>=-1&&p<=1,y=zh.distanceTo(vf)<Cs*.5;if(m&&y){hn.start.fromBufferAttribute(c,h),hn.end.fromBufferAttribute(l,h),hn.start.applyMatrix4(a),hn.end.applyMatrix4(a);let E=new C,v=new C;wi.distanceSqToSegment(hn.start,hn.end,v,E),e.push({point:v,pointOnLine:E,distance:wi.origin.distanceTo(v),object:i,face:null,faceIndex:h,uv:null,uv1:null})}}}var Ti=class extends ct{constructor(t=new hi,e=new $n({color:Math.random()*16777215})){super(t,e),this.isLineSegments2=!0,this.type="LineSegments2"}computeLineDistances(){let t=this.geometry,e=t.attributes.instanceStart,n=t.attributes.instanceEnd,s=new Float32Array(2*e.count);for(let a=0,o=0,c=e.count;a<c;a++,o+=2)mf.fromBufferAttribute(e,a),gf.fromBufferAttribute(n,a),s[o]=o===0?0:s[o-1],s[o+1]=s[o]+mf.distanceTo(gf);let r=new ss(s,2,1);return t.setAttribute("instanceDistanceStart",new ai(r,1,0)),t.setAttribute("instanceDistanceEnd",new ai(r,1,1)),this}raycast(t,e){let n=this.material.worldUnits,s=t.camera;if(s===null&&!n&&console.error('LineSegments2: "Raycaster.camera" needs to be set in order to raycast against LineSegments2 while worldUnits is set to false.'),n===!1&&(this.material.resolution.x===0||this.material.resolution.y===0))return;let r=t.params.Line2!==void 0&&t.params.Line2.threshold||0;wi=t.ray;let a=this.matrixWorld,o=this.geometry,c=this.material;Cs=c.linewidth+r,o.boundingSphere===null&&o.computeBoundingSphere(),jc.copy(o.boundingSphere).applyMatrix4(a);let l;if(n)l=Cs*.5;else{let d=Math.max(s.near,jc.distanceToPoint(wi.origin));l=xf(s,d,c.resolution)}if(jc.radius+=l,wi.intersectsSphere(jc)===!1)return;o.boundingBox===null&&o.computeBoundingBox(),Yc.copy(o.boundingBox).applyMatrix4(a);let u;if(n)u=Cs*.5;else{let d=Math.max(s.near,Yc.distanceToPoint(wi.origin));u=xf(s,d,c.resolution)}Yc.expandByScalar(u),wi.intersectsBox(Yc)!==!1&&(n?w_(this,e):T_(this,s,e))}onBeforeRender(t){let e=this.material.uniforms;e&&e.resolution&&(t.getViewport(Fh),this.material.uniforms.resolution.value.set(Fh.z,Fh.w))}};var _f=3,A_=(()=>{let i=getComputedStyle(document.documentElement);return[["--d-ontime","#7c8698"],["--d-small","#f2a87e"],["--d-mid","#e07b45"],["--d-big","#b85417"]].map(([t,e])=>i.getPropertyValue(t).trim()||e)})();async function yf(i){let t=await(await fetch(i)).blob(),e=await createImageBitmap(t,{colorSpaceConversion:"none",premultiplyAlpha:"none"}),n=document.createElement("canvas");n.width=e.width,n.height=e.height;let s=n.getContext("2d",{willReadFrequently:!0});return s.drawImage(e,0,0),{w:e.width,h:e.height,px:s.getImageData(0,0,e.width,e.height).data}}function Mf(i){let t=Math.floor(i/60+.5);return t<=0?0:t<=5?1:t<=15?2:3}async function Sf(i){let[t,e,n]=await Promise.all([fetch(i.karta).then(ot=>ot.json()),yf(i.podatki),yf(i.relief)]),s=new Int16Array(t.n_int16);for(let ot=0;ot<t.n_int16;ot++)s[ot]=e.px[ot*4]*256+e.px[ot*4+1]-32768;let r=t.enota/1e3,a=t.relief,o=n.px,c=new Float32Array(a.nx*a.nz),l=new Float32Array(a.nx*a.nz);for(let ot=0;ot<a.nx*a.nz;ot++)c[ot]=(o[ot*4]*256+o[ot*4+1])*a.skala,l[ot]=o[ot*4+2]/255;let u=a.x0/1e3,d=a.x1/1e3,h=a.z0/1e3,f=a.z1/1e3;function g(ot,D){let W=Be((ot-u)/(d-u)*a.nx-.5,0,a.nx-1.001),J=Be((D-h)/(f-h)*a.nz-.5,0,a.nz-1.001),ht=Math.floor(W),wt=Math.floor(J),Vt=W-ht,Kt=J-wt,be=c[wt*a.nx+ht],Re=c[wt*a.nx+ht+1],Le=c[(wt+1)*a.nx+ht],w=c[(wt+1)*a.nx+ht+1];return((be*(1-Vt)+Re*Vt)*(1-Kt)+(Le*(1-Vt)+w*Vt)*Kt)/1e3*_f}let x=new Uint16Array(a.nx*a.nz*2);for(let ot=0;ot<a.nx*a.nz;ot++)x[ot*2]=ir.toHalfFloat(c[ot]),x[ot*2+1]=ir.toHalfFloat(l[ot]);let p=new ys(x,a.nx,a.nz,yi,Bn);p.magFilter=p.minFilter=Ke,p.flipY=!1,p.needsUpdate=!0;let m=new zi,y=new Wt("#05080d");m.background=y;let E=new Je(42,1,.05,3e3),v=d-u,b=f-h,M=new je(v,b,Math.round(a.nx/2),Math.round(a.nz/2));M.rotateX(-Math.PI/2),M.translate((u+d)/2,0,(h+f)/2);let A={uVis:{value:p},uE:{value:_f},uTexel:{value:new vt(1/a.nx,1/a.nz)},uKm:{value:new vt(v/a.nx,b/a.nz)},uOzadje:{value:y},uSvetlost:{value:1},uX0:{value:new xe(u,h,v,b)}},_=new ct(M,new Oe({uniforms:A,vertexShader:`
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
      }`}));m.add(_);let T=t.mesta.find(ot=>ot[0]==="Ljubljana"),P=new vt(T[1]/1e3,T[2]/1e3),L=(ot,D)=>{ot.onBeforeCompile=W=>{W.uniforms.uRaz=D,W.uniforms.uSr={value:P},W.vertexShader=W.vertexShader.replace("#include <common>",`#include <common>
uniform vec2 uSr; varying float vRaz;`).replace("vec4 start = modelViewMatrix * vec4( instanceStart, 1.0 );",`vRaz = mix(distance(instanceStart.xz, uSr), distance(instanceEnd.xz, uSr), position.y < 0.5 ? 0.0 : 1.0);
vec4 start = modelViewMatrix * vec4( instanceStart, 1.0 );`),W.fragmentShader=W.fragmentShader.replace("#include <common>",`#include <common>
uniform float uRaz; varying float vRaz;`).replace("vec4 diffuseColor = vec4( diffuse, alpha );",`if (vRaz > uRaz) discard;
vec4 diffuseColor = vec4( diffuse * (1.0 + 2.5 * smoothstep(uRaz - 9.0, uRaz, vRaz)), alpha );`)}},F={value:0},V={value:0},I=[],z=0,q=s.subarray(0,t.dolzina_prog);for(;z<q.length;){let ot=q[z++],D=null;for(let W=0;W<ot;W++){let J=q[z++]*r,ht=q[z++]*r,wt=g(J,ht)+.06;D&&I.push(...D,J,wt,ht),D=[J,wt,ht]}}let j=new hi().setPositions(I),at=new $n({color:"#ffd6ae",linewidth:1.9,transparent:!0,opacity:.95,depthWrite:!1}),K=new $n({color:"#f0934f",linewidth:7,transparent:!0,opacity:.16,depthWrite:!1,blending:as});L(at,F),L(K,F);let st=new Ti(j,at),it=new Ti(j,K);st.renderOrder=3,it.renderOrder=2,m.add(it,st);let Rt=[],mt=s.subarray(t.dolzina_prog,t.dolzina_prog+t.n_bus*4),Ut=.24;for(let ot=0;ot<mt.length;ot+=4){let D=mt[ot]*Ut,W=mt[ot+1]*Ut,J=mt[ot+2]*Ut,ht=mt[ot+3]*Ut;Rt.push(D,g(D,W)+.04,W,J,g(J,ht)+.04,ht)}let Dt=new hi().setPositions(Rt),ft=new $n({color:"#6f8fb3",linewidth:.9,transparent:!0,opacity:.32,depthWrite:!1});L(ft,V);let N=new Ti(Dt,ft);N.renderOrder=1,m.add(N);let k=t.obris,dt=[];for(let ot=0;ot<k.length;ot+=2){let D=ot,W=(ot+2)%k.length,J=k[D]/1e3,ht=k[D+1]/1e3,wt=k[W]/1e3,Vt=k[W+1]/1e3;dt.push(J,g(J,ht)+.1,ht,wt,g(wt,Vt)+.1,Vt)}let St=new $n({color:"#c8d3e4",linewidth:1.2,transparent:!0,opacity:.45,depthWrite:!1,dashed:!0,dashSize:1.2,gapSize:.8}),Mt=new hi().setPositions(dt),Ft=new Ti(Mt,St);Ft.computeLineDistances(),m.add(Ft);let xt=[at,K,ft,St],X=s.subarray(t.dolzina_prog+t.n_bus*4,t.dolzina_prog+t.n_bus*4+t.dolzina_vozenj),tt=[];for(z=0;z<X.length;){let ot=X[z++],D=X[z++],W=new Float32Array(D),J=new Float32Array(D),ht=new Float32Array(D),wt=new Float32Array(D);for(let Vt=0;Vt<D;Vt++)W[Vt]=X[z++],J[Vt]=X[z++]*r,ht[Vt]=X[z++]*r,wt[Vt]=X[z++]*10;tt.push({vrsta:ot,t:W,x:J,z:ht,d:wt})}let G=tt.length,et=new Float32Array(G*3),gt=new Float32Array(G*3),Bt=new Float32Array(G),bt=new ge;bt.setAttribute("position",new Ue(et,3)),bt.setAttribute("color",new Ue(gt,3)),bt.setAttribute("aVel",new Ue(Bt,1));let jt={uDpr:{value:1},uVid:{value:0}},ne=new qr(bt,new Oe({uniforms:jt,vertexShader:`
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
      }`,vertexColors:!0,transparent:!0,depthWrite:!1}));ne.frustumCulled=!1,ne.renderOrder=5,m.add(ne);let U=A_.map(ot=>new Wt(ot));function Ee(ot){for(let D=0;D<G;D++){let W=tt[D],J=W.t.length;if(ot<W.t[0]||ot>W.t[J-1]){Bt[D]=0;continue}let ht=0,wt=J-1;for(;wt-ht>1;){let w=ht+wt>>1;W.t[w]<=ot?ht=w:wt=w}let Vt=W.t[wt]>W.t[ht]?(ot-W.t[ht])/(W.t[wt]-W.t[ht]):0,Kt=W.x[ht]+(W.x[wt]-W.x[ht])*Vt,be=W.z[ht]+(W.z[wt]-W.z[ht])*Vt,Re=W.d[ht]+(W.d[wt]-W.d[ht])*Vt;et[D*3]=Kt,et[D*3+1]=g(Kt,be)+.18,et[D*3+2]=be;let Le=U[W.vrsta===0,Mf(Re)];gt[D*3]=Le.r,gt[D*3+1]=Le.g,gt[D*3+2]=Le.b,Bt[D]=W.vrsta===0?12:W.vrsta===2?4.2:5.2}bt.attributes.position.needsUpdate=!0,bt.attributes.color.needsUpdate=!0,bt.attributes.aVel.needsUpdate=!0}let se=t.vrsta,R=[];for(let ot=0;ot<se.pot.length;ot+=2)R.push([se.pot[ot]/1e3,se.pot[ot+1]/1e3]);let S=[0];for(let ot=1;ot<R.length;ot++)S.push(S[ot-1]+Math.hypot(R[ot][0]-R[ot-1][0],R[ot][1]-R[ot-1][1]));let H=se.postaje.map(([,ot,D])=>{let W=0,J=1e9;return R.forEach(([ht,wt],Vt)=>{let Kt=Math.hypot(ht-ot/1e3,wt-D/1e3);Kt<J&&(J=Kt,W=Vt)}),S[W]}),Y=.55,rt=(ot,D)=>{let W=null,J=null;for(let wt=0;wt<H.length;wt++)ot[wt]!=null&&(H[wt]<=D&&(W=wt),H[wt]>=D&&J===null&&(J=wt));if(W===null&&J===null)return null;if(W===null)return ot[J];if(J===null||H[J]===H[W])return ot[W];let ht=(D-H[W])/(H[J]-H[W]);return ot[W]+(ot[J]-ot[W])*ht},_t=new oe,Et=R.map(([ot,D])=>g(ot,D)+.12),nt=[];for(let[,ot]of se.dnevi){let D=[];for(let W=0;W<R.length-1;W++){let J=rt(ot,S[W]),ht=rt(ot,S[W+1]);J==null||ht==null||D.push(R[W][0],Et[W]+J/60*Y,R[W][1],R[W+1][0],Et[W+1]+ht/60*Y,R[W+1][1])}nt.push(...D)}let ut=new hi().setPositions(nt),At=new $n({color:"#f2a87e",linewidth:1.1,transparent:!0,opacity:.22,depthWrite:!1});_t.add(new Ti(ut,At));let Zt=R.map((ot,D)=>{let W=se.dnevi.map(([,J])=>rt(J,S[D])).filter(J=>J!=null).sort((J,ht)=>J-ht);return W.length?W[Math.floor(W.length/2)]:0}),It=[];for(let ot=0;ot<R.length-1;ot++)It.push(R[ot][0],Et[ot]+Zt[ot]/60*Y,R[ot][1],R[ot+1][0],Et[ot+1]+Zt[ot+1]/60*Y,R[ot+1][1]);let Lt=new $n({color:"#f0934f",linewidth:3.2,transparent:!0,depthWrite:!1});_t.add(new Ti(new hi().setPositions(It),Lt));{let ot=[],D=[],W=[];R.forEach(([wt,Vt],Kt)=>{ot.push(wt,Et[Kt],Vt,wt,Et[Kt]+Zt[Kt]/60*Y,Vt),W.push(0,1)});for(let wt=0;wt<R.length-1;wt++){let Vt=wt*2;D.push(Vt,Vt+2,Vt+1,Vt+1,Vt+2,Vt+3)}let J=new ge;J.setAttribute("position",new te(ot,3)),J.setAttribute("aA",new te(W,1)),J.setIndex(D);let ht=new Oe({uniforms:{uVid:{value:1}},vertexShader:"attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",fragmentShader:"uniform float uVid; varying float vA; void main(){ gl_FragColor = vec4(vec3(0.94,0.58,0.31), (0.05 + 0.32 * vA) * uVid); }",transparent:!0,depthWrite:!1,side:vn,blending:as});_t.add(new ct(J,ht)),_t.userData.zm=ht}let $t=[];H.forEach((ot,D)=>{let W=0;S.forEach((J,ht)=>{Math.abs(J-ot)<Math.abs(S[W]-ot)&&(W=ht)}),$t.push(R[W][0],Et[W],R[W][1],R[W][0],Et[W]+7.5,R[W][1])});let ee=new $n({color:"#c8d3e4",linewidth:.8,transparent:!0,opacity:.35,depthWrite:!1,dashed:!0,dashSize:.3,gapSize:.3}),ce=new Ti(new hi().setPositions($t),ee);ce.computeLineDistances(),_t.add(ce),_t.visible=!1,m.add(_t);let B=[At,Lt,ee],Ct=new oe,lt=T[1]/1e3,Pt=T[2]/1e3,yt=g(lt,Pt)+.2,pt=[];for(let ot=0;ot<3;ot++){let D=new ct(new sa(.92,1,64),new oi({color:"#f0934f",transparent:!0,depthWrite:!1,side:vn}));D.rotation.x=-Math.PI/2,D.position.set(lt,yt,Pt),Ct.add(D),pt.push(D)}m.add(Ct);let Xt=document.createElement("div");Xt.className="karta-oznake",document.body.appendChild(Xt);let Ht=t.mesta.map(([ot,D,W])=>{let J=document.createElement("div");J.className="mesto",J.textContent=ot,Xt.appendChild(J);let ht=D/1e3,wt=W/1e3;return{el:J,p:new C(ht,g(ht,wt)+.3,wt),ime:ot}}),we=[],ye=(ot,D,W,J,ht)=>{let wt=document.createElement("div");wt.className="oznaka3d "+(ht||""),wt.innerHTML=`<span>${ot}</span>`,Xt.appendChild(wt);let Vt={el:wt,p:new C(D,g(D,W)+J,W)};return we.push(Vt),Vt},dn=se.stat,fn=se.postaje[se.postaje.length-1],Ps=ye(`<em>${se.ime}</em><b>Ljubljana \u2192 Maribor \xB7 ${dn.dni} dni</b>`,fn[1]/1e3,fn[2]/1e3,8.5,""),Ai=ye("<em>budilka</em><b>7.15 \u2192 7.22</b>",lt,Pt,2.2,"oranzna"),Pn=Bc([{t:128,p:[4,430,270],c:[8,0,-4],f:40},{t:137,p:[-4,215,205],c:[6,0,0],f:40},{t:146,p:[-30,150,175],c:[6,0,2],f:40},{t:157,p:[40,150,175],c:[6,0,2],f:40},{t:168,p:[95,95,95],c:[14,0,-8],f:40},{t:177,p:[62,48,62],c:[22,3,-22],f:40,mir:!0},{t:186,p:[4,26,40],c:[-20,0,4],f:40},{t:193,p:[-14,11,20],c:[-23.5,0,6],f:40},{t:200,p:[-19.5,7,15.5],c:[-23.6,.2,6.6],f:40},{t:206,p:[-23.3,2.4,9.2],c:[-23.7,.2,6.8],f:40}].map(ot=>({t:ot.t,v:[...ot.p,...ot.c,ot.f],mir:ot.mir}))),Jn=new xe,kn=new vt,Ci=0;function Kn(ot,D,W,J){let ht=Pn(D);E.position.set(ht[0],ht[1],ht[2]),E.lookAt(ht[3],ht[4],ht[5]),E.fov=ht[6],E.near=Math.max(.02,ht[1]*.02),J(E),E.updateProjectionMatrix(),ot.getSize(kn);let wt=kn.x,Vt=kn.y;for(let Q of[...xt,...B])Q.resolution.set(wt,Vt);let Kt=ot.getPixelRatio();Kt!==Ci&&(jt.uDpr.value=Kt,Ci=Kt),F.value=fe(0,260,Se(129,141,D)),V.value=fe(0,260,Se(134,146,D));let be=D<146?fe(-300,0,Se(138,146,D)):D<168?fe(0,3600,(D-146)/22):3600+(D-168)*18;Ee(be),jt.uVid.value=Se(139,145,D)*(1-.55*Rn(D,169,173,182,186));let Re=Rn(D,168,173,184,188);_t.visible=Re>.001,_t.scale.y=1;for(let Q of B)Q.opacity=Q===Lt?Re:Q===ee?Re*.35:Re*.22;_t.userData.zm.uniforms.uVid.value=Re;let Le=Rn(D,195,197.5,204,206);Ct.visible=Le>.001,pt.forEach((Q,$)=>{let Z=(W*.6+$/3)%1;Q.scale.setScalar(.3+Z*3.2),Q.material.opacity=(1-Z)*.8*Le}),Xt.style.opacity=1;let w=Se(140,146,D)*(1-Se(203,205.5,D));for(let Q of Ht)Hn(Q,w*(Q.ime==="Ljubljana"||D<184?1:.4));Hn(Ps,Re),Hn(Ai,Le),ot.render(m,E);let O=Rn(D,144,147,168,171);return O>0?{vid:O,oznaka:"\u010Detrtek, 1. 10. 2026",cas:7*3600+Be(be,0,3600)}:null}function Hn(ot,D){if(D<=.001){ot.el.style.opacity=0;return}Jn.set(ot.p.x,ot.p.y,ot.p.z,1).applyMatrix4(E.matrixWorldInverse).applyMatrix4(E.projectionMatrix);let W=(Jn.x/Jn.w*.5+.5)*kn.x,J=(-Jn.y/Jn.w*.5+.5)*kn.y;ot.el.style.opacity=Jn.w>0?D.toFixed(3):0,ot.el.style.transform=`translate3d(${W.toFixed(1)}px, ${J.toFixed(1)}px, 0)`}function fs(){Xt.style.opacity=0}return{risi:Kn,skrij:fs,meta:t,scena:m,kamera:E}}var R_=()=>new Promise(i=>requestAnimationFrame(()=>i())),Ia=matchMedia("(pointer: coarse)").matches||innerWidth<700,Zc=matchMedia("(prefers-reduced-motion: reduce)").matches,un=(i,t,e=0)=>i*3600+t*60+e,C_=[[0,un(7,41,24)],[10,un(7,41,59.2)],[11,un(7,42,0)],[14,un(7,42,5)],[26,un(7,50,0)],[43,un(7,55,0)],[54,un(7,55,30)],[68,un(7,56,30)],[103,un(8,0,0)],[118,un(8,13,0)],[128,un(8,14,0)],[206,un(22,41,0)],[240,un(22,43,0)]];function bf(i){let t=C_;if(i<=t[0][0])return t[0][1];for(let e=0;e<t.length-1;e++)if(i<=t[e+1][0]){let n=(i-t[e][0])/(t[e+1][0]-t[e][0]);return t[e+1][1]<t[e][1]?t[e+1][1]:fe(t[e][1],t[e+1][1],n)}return t[t.length-1][1]}var P_=i=>{let t=Math.floor(i/3600)%24,e=Math.floor(i/60)%60;return`${String(t).padStart(2,"0")}.${String(e).padStart(2,"0")}`};async function I_(){let i=document.getElementById("oder"),t;try{t=new Nc({canvas:i,antialias:!0,powerPreference:"high-performance"})}catch{document.documentElement.classList.add("brez-3d");return}let e=+new URLSearchParams(location.search).get("dpr")||0,n=e||Math.min(devicePixelRatio||1,Ia?1.6:2),s=e||Math.min(n,Ia?1.3:2);t.setPixelRatio(s);let r=0,a=0;function o(){let D=i.clientWidth||innerWidth,W=i.clientHeight||innerHeight;return D===r&&W===a?!1:(r=D,a=W,t.setSize(r,a,!1),!0)}o(),t.toneMapping=pa,t.toneMappingExposure=1,t.shadowMap.enabled=!0,t.shadowMap.type=Ss;let c=document.querySelector(".nalaganje i"),l=null,u=Sf(i.dataset).then(D=>(l=D,D)).catch(D=>(console.warn("kajros: karta se ni nalo\u017Eila",D),null)),d=async D=>{c&&(c.style.width=`${D*100}%`),await R_()};await Promise.all([document.fonts.load('600 92px "IBM Plex Sans"'),document.fonts.load('600 80px "IBM Plex Mono"')]).catch(()=>{});let h=new zi,f=new Hc;f.nastavi("zora"),h.add(f.kupola,f.sonce,f.sonce.target,f.nebesna),h.fog=new Hr("#fff",1,2),f.sonce.shadow.mapSize.set(Ia?1024:2048,Ia?1024:2048),await d(.1);let g=Wd(),x=Xd(g,{atmU:f.U,NEBO:Rh});h.add(x.skupina),await d(.2);let p=Qd();h.add(p.skupina),await d(.3);let m=nf();h.add(m.skupina);let y=ef();h.add(y.skupina),await d(.4),h.add(af(g)),await d(.55);let E=[[-2140,-78,.15],[-880,-66,-.1],[-2260,66,.05]],v=of(g,[...E.map(([D,W])=>[D,W,28]),[-1380,240,50],[-1425,-60,45],[-2105,-45,32],[-2860,175,40],[-2990,160,40],[-3140,105,40],[-3060,330,30]],Ia?.7:1);h.add(v),await d(.7);let b=cf(g);h.add(b,lf(g));let M=hf();for(let[D,W,J]of E){let ht=M.parent?M.clone():M;ht.position.set(D,Hi(D,W,g)-.2,W),ht.rotation.y=J,h.add(ht)}let A=uf(g);h.add(A,df());let _=ff(f.U,Rh);h.add(_);{let D=new ct(new Ce(130,1.4,5),new Ot({color:"#9a968e",roughness:.9}));D.position.set(-3265,ue.y-.7,1.68+2.5),D.receiveShadow=!0,h.add(D)}await d(.82);let T=new Oe({uniforms:{uMoc:{value:1}},vertexShader:"varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",fragmentShader:"uniform float uMoc; varying vec2 vUv; void main(){ float d = length(vUv - 0.5) * 2.0; float a = exp(-d * d * 5.0) * 0.9 + exp(-d * 18.0) * 0.6; gl_FragColor = vec4(vec3(1.0, 0.95, 0.85) * a * uMoc, 1.0); }",transparent:!0,blending:as,depthWrite:!1}),P=[];for(let D of[-1,1]){let W=new ct(new je(3.2,3.2),T);W.renderOrder=10,h.add(W),P.push({m:W,z:D})}let L=[];for(let[D,W,J,ht,wt]of[[0,4,4.6,"#ffd7a0",26],[-14,4,4.8,"#ffd7a0",22],[14,4,4.8,"#ffd7a0",22],[-40,5.6,7,"#ffe2b8",14],[-17.25,1.3,6.55,"#a9c4ff",1.6],[-18.9,2.5,8.9,"#ffd9b0",2.4]]){let Vt=new ha(ht,wt,26,1.6);Vt.position.set(D,W,J),Vt.visible=!1,h.add(Vt),L.push(Vt)}h.traverse(D=>{if(D.material)for(let W of[].concat(D.material))f.popravi(W)}),await d(.88);let F={};f.nastavi("zora"),F.zora=f.okolje(t),h.environment=F.zora;let V=()=>(F.noc||(f.nastavi("noc"),F.noc=f.okolje(t)),F.noc),I=new Je(40,r/a,.05,6e4),z=g.sPriX(-40),q=g.sPriX(-3268);function j(D){if(D<206){if(D<28)return z-740-(28-D)*98;if(D<43){let W=(D-28)/15;return z-740*(1-W)*(1-W)}return D<68?z:D<118?z+(q-z)*Od(0,1,(D-68)/50):q}return z}let at=new C,K=new C,st=new C,it=new C(0,1,0),Rt=(D,W,J)=>{if(!D.v)return J.set(D[0],D[1],D[2]);let ht=j(W);return g.tocka(ht,at),g.smer(ht,K),st.crossVectors(K,it).normalize(),J.copy(at).addScaledVector(K,D.v[0]).addScaledVector(it,D.v[1]).addScaledVector(st,D.v[2])},mt=[{t:0,p:[-2.75,3.12,2.18],c:[0,3.3,3.05],f:34},{t:5,p:[-3.3,3,1.95],c:[0,3.26,3.1],f:35},{t:13,p:[-7.2,2.35,1.3],c:[2,3.25,3.7],f:40},{t:20,p:[-30,2.3,5.4],c:[10,2.9,2.8],f:40},{t:26,p:[-52,2.25,6.2],c:[20,2.6,1],f:38},{t:37,p:[-52,2.2,6.4],c:[-6,2.4,.6],f:38},{t:44,p:[-51.5,2,6.8],c:[-39,2.15,.2],f:40,mir:!0},{t:49,p:[-15,3.3,5.6],c:[1,3.1,3.5],f:42},{t:54,p:[-12,3.25,5.4],c:[2,3.1,3.6],f:42,mir:!0},{t:58,p:[-12.4,1.95,8.3],c:[-6.6,1.5,1.4],f:38},{t:64,p:[-11.8,1.9,8],c:[-6.4,1.55,1.2],f:38},{t:69,p:[-22,2.8,10],c:[-42,2.2,0],f:42},{t:75,p:{v:[-30,5,15]},c:{v:[-4,2,0]},f:42},{t:82,p:{v:[24,3.2,10]},c:{v:[-14,2,0]},f:42},{t:88,p:{v:[60,22,46]},c:{v:[-30,2,-20]},f:44},{t:89.4,p:{v:[86,40,76]},c:{v:[-20,2,-30]},f:44},{t:89.5,p:[-1415,26,-40],c:[-1500,4,-330],f:40,rez:!0},{t:94,p:[-1440,25,-48],c:[-1600,4,-320],f:40},{t:94,p:[-2105,3.2,-45],c:[-2170,4.5,-125],f:42,rez:!0},{t:100,p:[-2110,3.4,-48],c:[-2265,4.5,-110],f:42},{t:100,p:[-2860,48,175],c:[-3260,10,40],f:42,rez:!0},{t:110,p:[-2990,46,160],c:[-3270,8,40],f:42},{t:116,p:[-3140,46,105],c:[-3250,3,4],f:44},{t:122,p:[-3060,120,330],c:[-2600,0,-60],f:46},{t:128,p:[-2700,900,900],c:[-1800,0,-100],f:50},{t:206,p:[-30,34,48],c:[-6,2,2],f:44,rez:!0},{t:213.5,p:[-27.5,6.5,16],c:[-17,1.6,6.2],f:42},{t:222,p:[-20.1,2.05,8.3],c:[-17.3,1.4,6.55],f:40,mir:!0},{t:240,p:[-19.8,1.98,8.05],c:[-17.35,1.38,6.55],f:37}],Ut=new C,Dt=[];for(let D of mt)(D.rez||!Dt.length)&&Dt.push([]),Dt[Dt.length-1].push(D);function ft(D){let W=Dt[0];for(let ht of Dt)ht[0].t<=D&&(W=ht);let J=W.map(ht=>({t:ht.t,v:Rt(ht.p,D,Ut).toArray().concat(Rt(ht.c,D,Ut).toArray(),[ht.f]),mir:ht.mir}));return J.length===1?J[0].v:Bc(J)(D)}let N=[...document.querySelectorAll(".takt")],k=[];function dt(){let D=scrollY;k=N.map(W=>{let J=W.getBoundingClientRect();return{el:W,top:J.top+D,h:J.height,t0:+W.dataset.t0,t1:+W.dataset.t1,kart:W.querySelector(".kartica")}})}function St(D){let W=D+a*.5;if(!k.length)return 0;if(W<=k[0].top)return k[0].t0;for(let J of k)if(W<=J.top+J.h)return fe(J.t0,J.t1,Be((W-J.top)/J.h));return k[k.length-1].t1}function Mt(D){let W=D+a*.5;for(let J of k)if(W>=J.top&&W<J.top+J.h)return(J.t1-J.t0)/J.h;return 0}let Ft=10,xt=7,X=4,tt=scrollY,G=scrollY;function et(D,W){let J=Math.abs(D-G)>a;if(G=D,Zc||J){tt=D;return}let ht=St(tt),wt=Mt(tt),Vt=(ht>86&&ht<126?xt:Ft)*W,Kt=wt>0?Vt/wt:1.5*a*W;tt+=Be((D-tt)*(1-Math.exp(-W*6.5)),-Kt,Kt),Math.abs(D-tt)>X*a&&(tt=D-Math.sign(D-tt)*X*a),Math.abs(D-tt)<.05&&(tt=D)}function gt(D){let W=D+a*.5;for(let J of k){if(!J.kart)continue;let ht=(W-J.top)/J.h,wt=(Zc?ht>-.1&&ht<1.1?1:0:Rn(ht,-.02,.14,.84,1)).toFixed(3),Vt=((1-Se(-.02,.14,ht))*18).toFixed(1);wt===J.o&&Vt===J.ty||(J.o=wt,J.ty=Vt,J.kart.style.opacity=wt,J.kart.style.setProperty("--ty",`${Vt}px`))}}dt(),addEventListener("resize",o),new ResizeObserver(dt).observe(document.body);let Bt=[...document.querySelectorAll(".oznaka3d[data-p]")].map(D=>({el:D,p:new C(...D.dataset.p.split(",").map(Number)),t0:+D.dataset.t0,t1:+D.dataset.t1})),bt=[...document.querySelectorAll(".poglavja a")].map(D=>({a:D,od:+D.dataset.od})),jt=-1;function ne(D){let W=0;bt.forEach((J,ht)=>{D>=J.od-.01&&(W=ht)}),W!==jt&&(jt=W,bt.forEach((J,ht)=>J.a.setAttribute("aria-current",ht===W?"true":"false")))}let U=document.querySelector(".hud-ura"),Ee=U?.querySelector("b"),se=U?.querySelector("span"),R=document.querySelector(".prehod"),S=document.querySelector(".dodatek"),H=document.querySelector(".vrh"),Y=new xe,rt=new C,_t=new C,Et=new C,nt=null,ut=0,At=!1;function Zt(D,W){let J=ut?Be(W-ut,0,.25):0;if(ut=W,nt===null||Math.abs(D-nt)>1800||Zc)return nt=D,At=!1,nt;let ht=Math.floor(D/60)*60+60,wt=1-Math.exp(-J*7);return nt>=ht&&(At=!0),At&&nt>D+.3?nt=Math.max(D,nt-Math.max(J*2,(nt-D)*wt)):nt<D-.3?(At=!1,nt=Math.min(D,nt+Math.max(J,(D-nt)*wt))):(At=!1,nt=Math.min(nt+J,ht-.001)),nt}let It=null;function Lt(){if(It)return It;let D=p.zadnjiS();p.postavi(g,z);let{xa:W,xb:J}=p.VRATA,ht=(W+J)/2,wt=W-.9,Vt=p.vrataLok(ht,0,-2.25),Kt=[new C(-8.1,ue.y,4.3),new C(fe(-8.1,Vt.x,.55),ue.y,3.1),new C(Vt.x,ue.y,Vt.z),p.vrataLok(ht,.58,-1.3),p.vrataLok(ht-.2,.58,-.45),p.vrataLok(wt+.45,.58,-.08),p.vrataLok(wt-.25,.58+.25/.27*.245,0),p.vrataLok(wt-1.5,.58+1.5/.27*.245,0)],be=new Qi(Kt,!1,"centripetal",.5);return It={krivulja:be,dolzina:be.getLength()},D!==null&&p.postavi(g,D),It}let $t=-1,ee="zora";function ce(D,W){let J=D>=206;J?f.nastavi("noc"):f.nastavi("zora","jutro",Se(60,118,D));let ht=J?"noc":"zora";ht!==ee&&(h.environment=J?V():F.zora,ee=ht),h.environmentIntensity=f.stanje.okolje,f.U.uCasN.value=W,t.toneMappingExposure=f.stanje.izp;let wt=j(D);p.postavi(g,wt),p.nastaviLuci(!0,J?1:Se(0,1,0)*.2),g.tocka(wt,at),g.smer(wt,K),st.crossVectors(K,it).normalize();let Vt=J?0:Rn(D,24,30,42,48)*.6;T.uniforms.uMoc.value=Vt;for(let Tt of P)Tt.m.visible=Vt>.01,Tt.m.position.copy(at).addScaledVector(K,.25).addScaledVector(st,Tt.z).setY(1.56),Tt.m.lookAt(I.position);let Kt=bf(D);m.ura.nastavi(Zt(Kt,W)),m.ura.obraz.emissiveIntensity=J?1:.38;let be=J||Kt<un(7,42,30)?0:Kt<un(7,46)?5:Kt<un(7,49)?10:13;if(be!==$t&&(m.tabla.narisi(be),$t=be),J)y.skupina.visible=!0,y.skupina.position.set(-17.6,ue.y,6.98),y.skupina.rotation.y=Math.PI/2,y.poza(0,Math.sin(W*.4)*.08,0,1);else{let Tt=Lt(),kt=Se(57.8,63.3,D)*.55+Be((D-57.8)/5.5)*.45,zt=kt*Tt.dolzina;Tt.krivulja.getPointAt(Math.min(kt,1),Ut),Tt.krivulja.getTangentAt(Math.min(kt,.999),rt),y.skupina.visible=D<63.4,y.skupina.position.copy(Ut);let Yt=Math.atan2(-rt.z,rt.x);y.skupina.rotation.y=fe(.35,Yt,Se(57.2,58.3,D)),y.poza(D>57.8?zt:0,fe(-.3,.5,Rn(D,3,6,40,46))*(1-Se(57,58,D)),1-Se(56.8,57.9,D),0)}p.odpriVrata(J?0:Se(56.2,57.6,D)*(1-Se(63.6,65,D)));for(let Tt of m.luci)Tt.emissiveIntensity=J?2.6:.5;for(let Tt of m.fasade)Tt.emissiveIntensity=J?1.1:0;b.userData.okna.emissiveIntensity=J?.9:0,A.userData.okna.emissiveIntensity=J?0:Rn(D,98,104,120,128)*.25;for(let Tt of L)Tt.visible=J;_.userData.mat.uniforms.uMoc.value=J?.25:1-Se(70,120,D)*.6;let Re=f.U.uSonce.value,Le=D>84&&D<128?220:80,w=f.sonce.shadow.camera;w.left=-Le,w.right=Le,w.top=Le,w.bottom=-Le,w.near=1,w.far=1200,w.updateProjectionMatrix();let O=D>84&&D<128?at:I.position,Q=2*Le/f.sonce.shadow.mapSize.x;_t.crossVectors(it,Re).normalize(),Et.crossVectors(Re,_t),Ut.set(O.x,0,O.z);let $=Math.round(Ut.dot(_t)/Q)*Q,Z=Math.round(Ut.dot(Et)/Q)*Q;f.sonce.target.position.set(0,0,0).addScaledVector(_t,$).addScaledVector(Et,Z).addScaledVector(Re,Ut.dot(Re)),f.sonce.position.copy(f.sonce.target.position).addScaledVector(Re,500),p.kamera(I)}function B(D=I){let W=r,J=a;D.aspect=W/J;let ht=W/J<.85,wt=Se(3,12,yt),Vt=ht?.5:fe(.67,.6,wt),Kt=ht?fe(.33,.4,wt):.5,be=W*2*Math.max(Vt,1-Vt),Re=J*2*Math.max(Kt,1-Kt);D.setViewOffset(be,Re,be/2-Vt*W,Re/2-Kt*J,W,J)}let Ct=U?.querySelector("i"),lt="";function Pt(D,W,J){let ht=P_(W),wt=J?Math.floor((W-un(8,0))/60):0,Vt=`${D}|${ht}|${J}|${wt}`;if(Vt===lt)return;lt=Vt,se.textContent=D;let Kt=wt>5?"z-sred":"z-mala";Ee.innerHTML=wt>0?`${ht.slice(0,3)}<em class="${Kt}">${ht.slice(3)}</em>`:ht,Ct&&(Ct.innerHTML=J?wt>0?`pouk ob 8.00 \xB7 <em class="${Kt}">+${wt} min</em>`:"pouk ob 8.00":"")}let yt=0,pt=performance.now(),Xt=0,Ht=null,we=0,ye=!1,dn=4,fn=!1,Ps=!1,Ai=null;function Ri(D,W=!0){let J=Ai?[...Ai.p,...Ai.c,Ai.f]:ft(yt),ht=yt>=128&&yt<206,wt=null;if(ht)l?wt=l.risi(t,yt,D,B):(t.setClearColor("#0a0d12",1),t.clear());else{l?.skrij();let Kt=yt>=206?ue.y+1.1:yt>70?Hi(J[0],J[2],g)+2.2:-1e9;I.position.set(J[0],Math.max(J[1],Kt),J[2]);let be=Zc?0:1-Se(0,3,yt);be>0&&I.position.add(Ut.set(Math.sin(D*.33)*.03,Math.sin(D*.27)*.02,Math.cos(D*.21)*.02).multiplyScalar(be)),I.lookAt(J[3],J[4],J[5]);let Re=r/a,Le=Mi.degToRad(J[6]),w=2*Math.atan(Math.tan(Math.atan(Math.tan(Le/2)*1.6)*.78)/Re);I.fov=Mi.radToDeg(Math.min(Math.max(Le,w),Mi.degToRad(78))),B(),I.near=Be(Math.hypot(J[3]-J[0],J[4]-J[1],J[5]-J[2])*.02,.15,.6),I.updateProjectionMatrix(),ce(yt,D),x.pragoviBlizu(I.position),x.zice.material.uniforms.uLoc.value.set(i.width,i.height),W&&(t.shadowMap.needsUpdate=!0),t.render(h,I)}for(let Kt of Bt){let be=Rn(yt,Kt.t0,Kt.t0+1.5,Kt.t1-1.5,Kt.t1),Re="0",Le=Kt.tr;if(be>.001&&!ht){Y.set(Kt.p.x,Kt.p.y,Kt.p.z,1).applyMatrix4(I.matrixWorldInverse).applyMatrix4(I.projectionMatrix);let w=(Y.x/Y.w*.5+.5)*r,O=(-Y.y/Y.w*.5+.5)*a;Re=Y.w>0?be.toFixed(3):"0",Le=`translate3d(${w.toFixed(1)}px, ${O.toFixed(1)}px, 0)`}Re!==Kt.op&&(Kt.el.style.opacity=Re,Kt.op=Re),Le!==Kt.tr&&(Kt.el.style.transform=Le,Kt.tr=Le)}let Vt=S?S.getBoundingClientRect().top:1/0;if(H?.classList.toggle("nad-dodatkom",Vt<64),U){let Kt=(wt?wt.vid:Rn(yt,64,70,124,128)+Rn(yt,206,212,260,270))*(1-Se(a*.9,a*.55,Vt)),be=Kt.toFixed(3);be!==U.dataset.op&&(U.style.opacity=be,U.dataset.op=be),Kt>0&&(wt?Pt(wt.oznaka,wt.cas,!1):Pt("ura v zgodbi",nt??bf(yt),yt<206))}if(R){let Kt=Rn(yt,123,128,128,131.5),be=Rn(yt,202,206,206,209);R.style.opacity=Math.max(Kt,be).toFixed(3),R.style.background=Kt>be?"#e9e4dc":"#05070b"}}let Pn=16.7,Jn=40,kn=n,Ci=0;function Kn(D){if(Pn+=(D-Pn)*.1,e||--Jn>0)return;let W=s;Pn>24&&dn<Pn*.66&&s>.75?(kn=s-.1,W=Math.max(.75,s-.15)):Pn<18.5&&++Ci>180&&s<Math.min(n,kn)&&(W=Math.min(n,kn,s+.1)),Pn>=18.5&&(Ci=0),W!==s&&(s=W,Ci=0,Jn=30,Pn=16.7,t.setPixelRatio(s),t.setSize(r,a,!1))}let Hn=[];function fs(){let D=performance.now(),W=D-pt,J=Math.min(.1,W/1e3);pt=D,we++;let ht=yt;Ht!==null?yt=Ht:(et(scrollY,J),yt=St(tt)),gt(Ht!==null?scrollY:tt),ne(St(scrollY));let wt=Math.abs(yt-ht)>1e-4;wt&&(Xt=D);let Vt=we>10&&Hn.length>0;Vt&&Hn.shift()();let be=!(S&&S.getBoundingClientRect().top<=0)&&(Vt||wt||D-Xt<400||we%2===0);if(be){ye&&W<100&&Kn(W);let Re=wt||yt>=206&&we%6===0,Le=fn||Re&&(Pn<=22||we%2===0);fn=Re&&!Le;let w=performance.now();Ri(D/1e3,Le),dn=performance.now()-w}ye=be,Ps||(Ps=!0,document.documentElement.classList.add("pripravljeno"),window.__pripravljen=!0),requestAnimationFrame(fs)}function ot(D,W){let J=[];D.traverse(ht=>{!ht.visible&&!ht.isLight&&(ht.visible=!0,J.push(()=>{ht.visible=!1})),ht.frustumCulled&&(ht.frustumCulled=!1,J.push(()=>{ht.frustumCulled=!0}))}),t.setViewport(0,0,1,1),t.shadowMap.needsUpdate=!0,t.render(D,W),t.setViewport(0,0,r,a);for(let ht of J)ht()}t.shadowMap.autoUpdate=!1;try{I.position.set(-1.5,3.2,2.6),I.lookAt(0,3.3,3.05),await t.compileAsync(h,I)}catch{}ot(h,I),await d(1),Hn.push(()=>V(),()=>{for(let D of L)D.visible=!0;t.compileAsync(h,I).catch(()=>{});for(let D of L)D.visible=yt>=206}),u.then(D=>{D&&t.compileAsync(D.scena,D.kamera).catch(()=>{}).then(()=>Hn.push(()=>ot(D.scena,D.kamera)))}),dt(),tt=G=scrollY,yt=St(tt),Ri(performance.now()/1e3),requestAnimationFrame(fs),window.__film={pojdi(D){Ht=D,yt=D,Ri(performance.now()/1e3)},pogled(D,W,J=40){Ai=D?{p:D,c:W,f:J}:null,Ri(performance.now()/1e3)},skoci(){Ht=null,tt=G=scrollY,yt=St(tt),gt(tt),Ri(performance.now()/1e3)},T:()=>yt,kam:D=>ft(D),ura:()=>nt,vlakS:D=>j(D),vlakXZ:D=>{let W=g.tocka(j(D),new C);return[Math.round(W.x),Math.round(W.z)]},info:()=>({drevesa:v.userData.stevilo,dpr:s,klici:t.info.render.calls,tri:t.info.render.triangles})}}I_().catch(i=>{console.error(i),document.documentElement.classList.add("brez-3d"),window.__pripravljen=!0});})();
/*! Bundled license information:

three/build/three.core.js:
three/build/three.module.js:
  (**
   * @license
   * Copyright 2010-2026 Three.js Authors
   * SPDX-License-Identifier: MIT
   *)
*/
