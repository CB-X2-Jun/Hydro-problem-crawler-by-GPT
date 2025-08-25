const tbody = document.getElementById('tbody');
const empty = document.getElementById('empty');
const search = document.getElementById('search');
const tagFilter = document.getElementById('tagFilter');

async function loadList(){
  try{
    const res = await fetch('../data/problems.json', {cache:'no-store'});
    const list = await res.json();
    render(list);
    setupFilter(list);
  }catch(e){
    tbody.innerHTML = `<tr><td colspan=3>加载失败：${e}</td></tr>`;
  }
}

function setupFilter(list){
  const allTags = Array.from(new Set(list.flatMap(x=>x.tags||[]))).sort();
  allTags.forEach(t=>{
    const opt = document.createElement('option');
    opt.value = t; opt.textContent = t;
    tagFilter.appendChild(opt);
  });

  function apply(){
    const q = search.value.toLowerCase();
    const tag = tagFilter.value;
    const filtered = list.filter(x=>{
      const hitText = (x.title||'').toLowerCase().includes(q) || (x.id||'').toLowerCase().includes(q);
      const hitTag = !tag || (x.tags||[]).includes(tag);
      return hitText && hitTag;
    });
    render(filtered);
  }

  search.addEventListener('input', apply);
  tagFilter.addEventListener('change', apply);
}

function render(list){
  if(!list || list.length===0){
    tbody.innerHTML = '';
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  tbody.innerHTML = list.map(x=>{
    const tags = (x.tags||[]).map(t=>`<span class="tag">${t}</span>`).join(' ');
    return `<tr>
      <td class="id">${x.id}</td>
      <td><a href="${x.href}">${escapeHtml(x.title)}</a></td>
      <td>${tags}</td>
    </tr>`;
  }).join('');
}

function escapeHtml(s){
  return (s||'').replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}

loadList();
