'use strict';
(() => {
  const get = id => document.getElementById(id);
  const search = get('search');
  const english = document.documentElement.lang === 'en';
  const switcher = document.querySelector('.lang-link');
  const alternate = switcher.getAttribute('href');
  const rows = Array.from(get('catalog-table').tBodies[0].rows);
  const pageSize = 10;
  const controls = Array.from(document.querySelectorAll('#filters input[type=radio]'));
  const pager = document.querySelector('.pager');
  const toggle = document.querySelector('.filter-toggle');
  let matches = [];
  let page = 1;
  const normalize = value => value.normalize('NFKC').toLocaleLowerCase().trim();
  const keywords = new Map(rows.map(row => [row, normalize(row.dataset.search)]));
  const chosen = name => controls.find(ctrl => ctrl.name === name && ctrl.checked).value;
  const setChoice = (name, value) => {
    const ctrl = controls.find(ctrl => ctrl.name === name && ctrl.value === value);
    (ctrl || controls.find(ctrl => ctrl.name === name && !ctrl.value)).checked = true;
  };
  function render(updateUrl = true) {
    const terms = normalize(search.value).split(/\s+/).filter(Boolean);
    const group = chosen('group');
    const type = chosen('type');
    controls.forEach(ctrl => ctrl.parentElement.classList.toggle('selected',ctrl.checked));
    matches = rows.filter(row =>
      (!group || row.dataset.group === group) && (!type || row.dataset.type === type) &&
      terms.every(term => keywords.get(row).includes(term))
    );
    const totalPages = Math.max(1, Math.ceil(matches.length / pageSize));
    page = Math.max(1, Math.min(totalPages, page));
    const visible = new Set(matches.slice((page - 1) * pageSize, page * pageSize));
    rows.forEach(row => { row.hidden = !visible.has(row); });
    get('count').textContent = english ? matches.length + (matches.length === 1 ? ' dataset' : ' datasets') : '共 ' + matches.length + ' 条资源';
    get('empty').hidden = matches.length > 0;
    get('export').hidden = !matches.length;
    pager.hidden = totalPages === 1;
    get('pages').textContent = english ? 'Page ' + page + ' of ' + totalPages : '第 ' + page + ' / ' + totalPages + ' 页';
    get('prev').disabled = page === 1;
    get('next').disabled = page === totalPages;
    {
      const url = new URL(location.href);
      for (const [name,value] of Object.entries({q:search.value.trim(),group,type,page:page>1?String(page):''})) {
        if (value) url.searchParams.set(name,value);
        else url.searchParams.delete(name);
      }
      switcher.href = alternate + url.search + url.hash;
      try { if (updateUrl) history.replaceState(null,'',url); } catch { /* Local-file previews can restrict history. */ }
    }
  }
  function restore() {
    const params = new URLSearchParams(location.search);
    search.value = params.get('q') || '';
    setChoice('group', params.get('group') || '');
    setChoice('type', params.get('type') || '');
    page = parseInt(params.get('page'),10) || 1;
    render(false);
  }
  function reset() {
    search.value = '';
    setChoice('group',''); setChoice('type',''); page=1; render();
  }
  get('search-form').addEventListener('submit', event => {event.preventDefault();page=1;render();});
  search.addEventListener('input', () => {page=1;render();});
  controls.forEach(ctrl => ctrl.addEventListener('change', () => {page=1;render();}));
  get('reset').addEventListener('click',reset);
  get('clear-all').addEventListener('click',() => {reset();search.focus();});
  toggle.addEventListener('click', () => {
    const open = get('filters').classList.toggle('shown');
    toggle.setAttribute('aria-expanded',String(open));
    if (open) get('reset').focus();
  });
  for (const [button,delta] of [['prev',-1],['next',1]]) {
    get(button).addEventListener('click',() => {
      page+=delta;render();get('catalog').scrollIntoView({block:'start'});
    });
  }
  get('export').addEventListener('click', event => {
    event.preventDefault();
    const fields = ['id','common','taxon','group','title','count','unit','design','vcf','reference','depth','sources'];
    const escapeCell = cell => {
      const text = String(cell ?? '');
      return /[\t\n\r"]/.test(text) ? '"' + text.replaceAll('"','""') + '"' : text;
    };
    const lines = [fields,...matches.map(row => JSON.parse(row.dataset.export))];
    const tsv = lines.map(line => line.map(escapeCell).join('\t')).join('\n')+'\n';
    const url = URL.createObjectURL(new Blob(['\uFEFF',tsv],{type:'text/tab-separated-values;charset=utf-8'}));
    const a = document.createElement('a');
    a.href=url;a.download=english ? 'popseq-atlas-selection.tsv' : 'popseq-atlas-selection.zh.tsv';document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),2000);
  });
  window.addEventListener('popstate',restore);
  document.body.classList.add('enhanced');
  restore();
})();
