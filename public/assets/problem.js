function qs(k){
  const m = location.search.match(new RegExp(`[?&]${k}=([^&]+)`));
  return m ? decodeURIComponent(m[1]) : '';
}

const id = qs('id');
const titleEl = document.getElementById('title');
const contentEl = document.getElementById('content');
const tagsEl = document.getElementById('tags');
const sourceLink = document.getElementById('sourceLink');

async function load(){
  if(!id){
    titleEl.textContent = '未指定题号';
    return;
  }
  try{
    const res = await fetch(`../data/problems/${id}.json`, {cache:'no-store'});
    const data = await res.json();
    titleEl.textContent = data.title || id;
    sourceLink.href = data.source || '#';

    // 标签
    tagsEl.innerHTML = (data.tags||[]).map(t=>`<span class="tag">${t}</span>`).join(' ');

    // 直接使用原站 HTML（保留 KaTeX/Markdown 渲染结果），并进行代码高亮
    contentEl.innerHTML = data.html || '<p>无内容</p>';

    // 代码高亮
    document.querySelectorAll('pre code').forEach((el)=>{
      try{ window.hljs && window.hljs.highlightElement(el); }catch(e){}
    });

    // KaTeX 自动渲染（支持 $$...$$ 与 \(...\)）
    try{
      window.renderMathInElement && window.renderMathInElement(contentEl, {
        delimiters: [
          {left: '$$', right: '$$', display: true},
          {left: '$', right: '$', display: false},
          {left: '\\(', right: '\\)', display: false},
          {left: '\\[', right: '\\]', display: true}
        ],
        throwOnError: false
      });
    }catch(e){}
  }catch(e){
    titleEl.textContent = `加载失败：${e}`;
  }
}

load();
