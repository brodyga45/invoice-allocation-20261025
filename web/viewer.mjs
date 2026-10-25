// Adapted from Shtops Receipt Review viewer, MIT (see THIRD_PARTY_NOTICES.md).
import * as pdfjs from './vendor/pdf.mjs';
pdfjs.GlobalWorkerOptions.workerSrc = new URL('./vendor/pdf.worker.mjs',import.meta.url).href;

const canvas=document.getElementById('pdf-canvas'),surface=document.getElementById('pdf-surface');
const status=document.getElementById('pdf-status'),count=document.getElementById('pdf-page');
const previous=document.getElementById('pdf-previous'),next=document.getElementById('pdf-next');
const smaller=document.getElementById('pdf-smaller'),larger=document.getElementById('pdf-larger');
let generation=0,drawGeneration=0,loading,current,renderTask,page=1,zoom=1,documentLabel="PDF";

function controls(disabled=false){
  previous.disabled=disabled||!current||page<=1;next.disabled=disabled||!current||page>=current.numPages;
  smaller.disabled=disabled||!current||zoom<=0.7;larger.disabled=disabled||!current||zoom>=2;
}

async function render(){
  if(!current)return;
  const g=generation,d=++drawGeneration,document=current;
  controls(true);status.textContent='Rendering PDF page…';
  try{
    const old=renderTask;if(old){old.cancel();await old.promise.catch(()=>{});}
    const source=await document.getPage(page);
    if(g!==generation||d!==drawGeneration)return;
    const base=source.getViewport({scale:1});
    const scale=Math.min(1.25,Math.max(0.25,(surface.clientWidth-20)/base.width))*zoom;
    const viewport=source.getViewport({scale}),ratio=Math.min(2,window.devicePixelRatio||1);
    canvas.width=Math.floor(viewport.width*ratio);canvas.height=Math.floor(viewport.height*ratio);
    canvas.style.width=viewport.width+'px';canvas.style.height=viewport.height+'px';
    canvas.hidden=false;canvas.setAttribute('aria-label',`${documentLabel} page ${page} of ${document.numPages}`);
    renderTask=source.render({canvas,viewport,transform:ratio===1?null:[ratio,0,0,ratio,0,0]});
    await renderTask.promise;
    if(g!==generation||d!==drawGeneration)return;
    count.textContent=`${page} / ${document.numPages}`;status.textContent=documentLabel+' · '+Math.round(zoom*100)+'%';
  }catch(error){
    if(g===generation&&d===drawGeneration&&error.name!=='RenderingCancelledException'){
      canvas.hidden=true;status.textContent='Preview unavailable. Use “Open PDF” to inspect the selected PDF.';
    }
  }finally{if(g===generation&&d===drawGeneration)controls();}
}

export function clearPDF(){
  ++generation;++drawGeneration;renderTask?.cancel();loading?.destroy().catch(()=>{});
  current=null;page=1;zoom=1;canvas.hidden=true;count.textContent='—';controls(true);
}

export async function openPDF(bytes,label='PDF'){
  clearPDF();const g=generation;documentLabel=label;
  status.textContent='Loading PDF…';
  try{
    loading=pdfjs.getDocument({data:new Uint8Array(bytes),useWasm:false,isEvalSupported:false,
      cMapUrl:new URL('./vendor/cmaps/',import.meta.url).href,cMapPacked:true,
      standardFontDataUrl:new URL('./vendor/standard_fonts/',import.meta.url).href,enableXfa:false});
    const document=await loading.promise;
    if(g!==generation){document.destroy().catch(()=>{});return;}
    current=document;await render();
  }catch(error){
    if(g===generation)status.textContent='Preview unavailable. Use “Open PDF” to inspect the selected PDF.';
  }
}

previous.addEventListener('click',()=>{if(current&&page>1){page--;surface.scrollTop=0;render();}});
next.addEventListener('click',()=>{if(current&&page<current.numPages){page++;surface.scrollTop=0;render();}});
smaller.addEventListener('click',()=>{zoom=Math.max(0.7,zoom-0.15);render();});
larger.addEventListener('click',()=>{zoom=Math.min(2,zoom+0.15);render();});
let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(render,150);});
