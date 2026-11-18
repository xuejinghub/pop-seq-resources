"""Render both language editions of PopSeq Atlas using Python's standard library."""
import csv
import json
import posixpath
from collections import Counter
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    '哺乳类': ('mammals', 'Mammals'), '鸟类': ('birds', 'Birds'), '鱼类': ('fish', 'Fish'),
    '头索动物': ('lancelets', 'Lancelets'), '昆虫': ('insects', 'Insects'), '植物': ('plants', 'Plants'),
    '线虫': ('nematodes', 'Nematodes'), '软体动物': ('molluscs', 'Molluscs'),
}
FIELDS = ['id','common','taxon','group','title','count','unit','design','vcf','reference','depth','sources']
NAV = [('index.html','Directory','资源目录'),('population.html','Populations','群体数据'),
       ('pedigree.html','Pedigrees','家系数据'),('lab.html','The lab','课题组')]
def e(value):
    return escape(str(value), quote=True)
def load(name):
    return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value,encoding='utf-8')
def url_to(target, directory):
    return posixpath.relpath(target, directory or '.')
def mark():
    return '<span class="brand-mark" aria-hidden="true"><b></b><b></b><b></b><b></b></span>'

class Edition:
    def __init__(self, lang, records, photos):
        self.lang = lang
        self.en = lang == 'en'
        self.prefix = '' if self.en else 'zh/'
        self.tsv = 'data/catalog.tsv' if self.en else 'data/catalog.zh.tsv'
        self.records = records
        self.photos = photos

    def t(self, en, zh):
        return en if self.en else zh

    def local(self, r):
        return r['en'] if self.en else r

    def taxgroup(self, r):
        return self.t(GROUPS[r['group']][1], r['group'])

    def design(self, r):
        labels = {'群体': 'Population', '家系': 'Pedigree'}
        return ' / '.join(labels[k] if self.en else k for k in r['design'])

    def size(self, r):
        return f"{r['count']:,}" if r['count'] is not None else '—'

    def fmt(self, r):
        v = self.local(r)
        return [r['id'],v['common'],v['taxon'],self.taxgroup(r),v['title'],r['count'],v['unit'],
                self.design(r),self.t('Public VCF','公开 VCF') if r['vcf'] else self.t('Sequence data','测序数据'),
                v['reference'],v['depth'],' | '.join(u for _,u in r['sources'])]

    def shell(self, path, title, body, section='', listing=False):
        t=self.t
        physical=self.prefix+path
        directory=posixpath.dirname(physical)
        asset=lambda f: url_to(f,directory)
        link=lambda f: url_to(self.prefix+f,directory)
        alternate=url_to(('zh/' if self.en else '')+path,directory)
        altlang=t('zh-CN','en')
        nav=''.join(f'<a href="{link(p)}"'+(' aria-current="page"' if p==section else '')+f'>{t(en,zh)}</a>' for p,en,zh in NAV)
        brand=f'<a class="brand" href="{link("index.html")}">{mark()}<span>PopSeq <em>Atlas</em></span></a>'
        langlinks=[]
        for en,lang,label in [(True,'en','EN'),(False,'zh-CN','中文')]:
            if self.en==en:
                langlinks.append(f'<span aria-current="true" lang="{lang}">{label}</span>')
            else:
                langlinks.append(f'<a class="lang-link" href="{alternate}" hreflang="{lang}" lang="{lang}" aria-label="{t("Switch to Chinese","Switch to English")}">{label}</a>')
        languages='<div class="languages" role="group" aria-label="'+t('Language','语言')+'">'+''.join(langlinks)+'</div>'
        js=f'<script defer src="{asset("assets/catalog.js")}"></script>' if listing else ''
        html=f'''<!DOCTYPE html>
<html lang="{t('en','zh-CN')}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · PopSeq Atlas</title><meta name="description" content="{t('Public population and pedigree sequencing resources with file manifests and study provenance.','检索公开的群体与家系测序资源、文件清单和研究来源。')}">
<link rel="alternate" hreflang="{altlang}" href="{alternate}"><link rel="icon" href="{asset('assets/favicon.png')}">
<link rel="stylesheet" href="{asset('assets/style.css')}">{js}</head><body>
<a class="skip" href="#main">{t('Skip to content','跳至正文')}</a>
<header><div class="frame top">{brand}<nav aria-label="{t('Main navigation','主导航')}">{nav}</nav><div class="utilities">{languages}<a class="download" href="{asset(self.tsv)}" download><span aria-hidden="true">↓</span> {t('Download TSV','下载目录')}</a></div></div></header>
<main id="main">{body}</main><footer><div class="frame foot">{brand}<span>{t('Cai Li Lab · Sun Yat-sen University','中山大学 · 李彩课题组')}</span><a href="{link('credits.html')}">{t('Photography','图片来源')}</a><a href="https://caililab.org/">{t('Lab website','课题组官网')} ↗</a></div></footer></body></html>'''
        write(ROOT/physical,html)

    def hero(self):
        t=self.t
        pics=[]
        for p in self.photos:
            lang=p[self.lang]
            pics.append(f'''<a class="specimen" href="credits.html#{e(p['id'])}" aria-label="{e(lang['name'])} · {e(lang['project'])}">
<img src="{url_to('assets/'+p['asset'], self.prefix)}" alt="{e(lang['name'])}" style="object-position:{e(p['position'])}">
<span class="img-caption"><strong>{e(lang['name'])}</strong><small>{e(lang['project'])}</small></span></a>''')
        stats=[(len(self.records),t('datasets','资源集')),(len({r['group'] for r in self.records}),t('taxonomic groups','生物类群')),
               (sum('家系' in r['design'] for r in self.records),t('pedigree datasets','家系资源集'))]
        figures=''.join(f'<div><dt>{label}</dt><dd>{value}</dd></div>' for value,label in stats)
        return f'''<section class="hero"><div class="frame hero-grid"><div class="hero-copy">
<p class="labline">{t('Cai Li Lab / Sun Yat-sen University','中山大学 / 李彩课题组')}</p>
<h1>{t('Population &amp; pedigree<br><em>sequencing atlas.</em>','跨物种群体与家系<br><em>测序资源图谱</em>')}</h1>
<p class="intro">{t('Find sequencing cohorts across species, from family-based studies to population-wide variant panels.','按物种查找家系测序队列和群体变异面板，获取数据、样本清单及原始研究。')}</p>
<dl class="stats">{figures}</dl></div><div class="mosaic" data-count="{len(pics)}">{''.join(pics)}</div></div></section>'''

    def pagehead(self, title, sub, home='index.html'):
        return f'<section class="pagehead"><div class="frame"><a class="crumb" href="{home}">{self.t("Directory","资源目录")}</a><h1>{e(title)}</h1><p>{e(sub)}</p></div></section>'

    def row(self,r):
        t=self.t; v=self.local(r); url='studies/'+r['id']+'.html'
        words=[r['id'],r['group'],r.get('aliases',''),*r['archive_ids'],GROUPS[r['group']][1]]
        for ver in [r,r['en']]:
            words.extend(ver[k] for k in ['common','taxon','title','summary','reference'])
        style='has-vcf' if r['vcf'] else 'reads'
        label=t('Public VCF','公开 VCF') if r['vcf'] else t('Sequence data','测序数据')
        return f'''<tr data-group="{GROUPS[r['group']][0]}" data-type="{'vcf' if r['vcf'] else 'reads'}" data-search="{e(' '.join(words))}" data-export="{e(json.dumps(self.fmt(r),ensure_ascii=False))}">
<td><a class="species" href="{url}">{e(v['common'])}</a><small class="latin">{e(v['taxon'])}</small></td>
<td><a class="study-title" href="{url}">{e(v['title'])}</a><small class="accession">{e(r['id'])} <span>· {e(self.design(r))}</span></small></td>
<td class="num">{self.size(r)}<small>{e(v['unit'])}</small></td><td><span class="pill {style}"><i></i>{label}</span></td>
<td class="open-cell"><a class="row-open" href="{url}" aria-label="{e(v['title'])}">↗</a></td></tr>'''

    def browse(self,path,title,subtitle,items,home=False):
        t=self.t
        counts=Counter(r['group'] for r in items)
        def option(group,value,label,count):
            checked=' checked' if not value else ''
            return f'<label class="facet"><input type="radio" name="{group}" value="{e(value)}"{checked}><span>{e(label)}</span><small>{count}</small></label>'
        taxa=option('group','',t('All groups','全部类群'),len(items))
        taxa+=''.join(option('group',slug,t(name,k),counts[k]) for k,(slug,name) in GROUPS.items() if counts[k])
        vcf=sum(r['vcf'] for r in items)
        avail=option('type','',t('All records','全部数据'),len(items))+option('type','vcf',t('Public VCF','有公开 VCF'),vcf)+option('type','reads',t('Sequence data only','仅收录测序入口'),len(items)-vcf)
        heading=t('Dataset directory','资源目录') if home else t('Datasets','资源清单')
        opening=self.hero() if home else self.pagehead(title,subtitle)
        search=t('Search species, study or accession','搜索物种、研究或项目编号')
        columns=(t('Species','物种'),t('Study / accession','研究 / 编号'),t('Cohort size','研究规模'),t('Availability','可用数据'))
        body=f'''{opening}<section class="frame catalog" id="catalog"><div class="catalog-heading"><h2>{heading}</h2><p>{t('Updated','更新于')} <time datetime="2026-11-18">{t('18 Nov 2026','2026-11-18')}</time></p></div>
<div class="catalog-grid"><aside id="filters"><div class="side-title"><h3>{t('Filters','筛选')}</h3><button class="reset" id="reset">{t('Reset','重置')}</button></div>
<fieldset><legend>{t('Taxonomic group','生物类群')}</legend>{taxa}</fieldset><fieldset><legend>{t('Data availability','数据可用性')}</legend>{avail}</fieldset></aside>
<div class="results"><form id="search-form" role="search"><span class="glass" aria-hidden="true"></span><input id="search" type="search" placeholder="{search}" aria-label="{search}" autocomplete="off"><button type="submit">{t('Search','检索')}</button></form>
<div class="result-line"><span id="count" role="status" aria-live="polite">{len(items)} {t('datasets','条资源')}</span><button type="button" class="filter-toggle" aria-controls="filters" aria-expanded="false">{t('Filters','筛选条件')}</button><a href="{url_to(self.tsv,self.prefix)}" id="export" download>{t('Export results','导出结果')} ↓</a></div>
<table id="catalog-table"><thead><tr>{''.join(f'<th scope="col">{c}</th>' for c in columns)}<th scope="col"><span class="sr-only">{t('Details','详情')}</span></th></tr></thead><tbody>{''.join(self.row(r) for r in items)}</tbody></table>
<div id="empty" hidden><h3>{t('No matching datasets','没有匹配的资源')}</h3><p>{t('Try a scientific name or an archive accession.','可以尝试物种学名或项目编号。')}</p><button id="clear-all">{t('Clear search and filters','清除搜索和筛选')}</button></div>
<div class="pager" hidden><button id="prev">← {t('Previous','上一页')}</button><span id="pages"></span><button id="next">{t('Next','下一页')} →</button></div></div></div></section>'''
        self.shell(path,title,body,section=path,listing=True)

    def detail(self,r):
        t=self.t; v=self.local(r); id=r['id']
        availability=t('Available from the study or archive','原研究或归档提供') if r['vcf'] else t('Only sequence data are listed','当前仅收录测序数据')
        if 'vcf_detail' in v: availability=v['vcf_detail']
        facts=[(t('Study design','研究设计'),self.design(r)),(t('Taxonomic group','生物类群'),self.taxgroup(r)),
               (t('Cohort size','研究规模'),f"{self.size(r)} {v['unit']}".strip()),(t('Public VCF','现成 VCF'),availability)]
        if v['reference']:facts.append((t('Reference genome','参考基因组'),v['reference']))
        if v['depth']:facts.append((t('Sequencing depth','测序深度'),v['depth']))
        if r['runs']:
            facts.extend([(t('Runs in manifest','清单中的 Run'),f"{r['runs']:,}"),(t('BioSamples in manifest','清单中的 BioSample'),f"{r['biosamples']:,}")])
        facts=''.join(f'<div><dt>{e(label)}</dt><dd>{e(value)}</dd></div>' for label,value in facts)
        files=[]
        for n,suffix,desc in [(r['runs'],'runs',t('Run and FASTQ manifest','Run 与 FASTQ 清单')),
                              (r['variant_files'],'variants',t('VCF file manifest','归档 VCF 清单'))]:
            if n:
                href=url_to(f'data/files/{id}-{suffix}.tsv',self.prefix+'studies')
                files.append(f'<a class="file-link" href="{href}" download>{desc} <small>{n:,} · TSV ↓</small></a>')
        links=[]
        for i,(label,url) in enumerate(r['sources']):
            name=v['source_labels'][i] if self.en else label
            links.append(f'<li><a href="{e(url)}">{e(name)}<small>{e(urlsplit(url).hostname)} ↗</small></a></li>')
        header=self.pagehead(v['title'],v['common']+'  ·  '+v['taxon'],'../index.html')
        body=f'''{header}<div class="frame detail-grid"><article><p class="study-id">{e(id)}</p><h2>{t('Study overview','研究概况')}</h2><p class="abstract">{e(v['summary'])}</p><dl class="facts">{facts}</dl></article>
<aside class="sources"><h2>{t('Data & sources','数据与来源')}</h2>{''.join(files)}<ul>{''.join(links)}</ul></aside></div>'''
        self.shell(f'studies/{id}.html',v['title'],body)

    def lab(self):
        t=self.t
        title=t('Cai Li Lab','李彩课题组')
        intro=self.pagehead(title,t('School of Life Sciences · Sun Yat-sen University','中山大学 · 生命科学学院'))
        excerpts=[
            ('https://caililab.org/',t('From the lab homepage','摘自课题组官网首页'),
             ['We are interested in genome regulation and evolution, particularly the interplay of the two aspects.']),
            ('https://caililab.org/research/',t('From the research page','摘自官网研究方向页'),
             ['How does genetic variation arise and evolve within and across species?',
              'How does genetic variation influence molecular functions, phenotypes, and evolutionary change?'])]
        quotations=[]
        for url,credit,quotes in excerpts:
            passages=''.join(f'<p lang="en">{e(q)}</p>' for q in quotes)
            quotations.append(f'<figure class="excerpt"><blockquote cite="{url}">{passages}</blockquote><figcaption><a href="{url}">{credit} ↗</a></figcaption></figure>')
        links=[('',t('Lab homepage','实验室主页')),('research/',t('Research','研究方向')),('people/',t('People','课题组成员')),('publications/',t('Publications','研究成果')),('contact/',t('Contact','联系方式'))]
        official=''.join(f'<li><a href="https://caililab.org/{p}">{label}<small>caililab.org ↗</small></a></li>' for p,label in links)
        body=f'''{intro}<div class="frame detail-grid"><article class="lab-copy">{''.join(quotations)}</article><aside class="sources"><h2>{t('Official website','课题组官网')}</h2><ul>{official}</ul></aside></div>'''
        self.shell('lab.html',title,body,section='lab.html')

    def credits(self):
        t=self.t
        title=t('Project photography','基因组计划摄影')
        intro=self.pagehead(title,t('Homepage photographs are displayed with responsive crops. Credits and source licences are listed below.','首页照片随屏幕尺寸裁切展示。下列信息标明原图、拍摄者和许可。'))
        cards=[]
        for p in self.photos:
            v=p[self.lang]
            img=url_to('assets/'+p['asset'],self.prefix)
            cards.append(f'''<article class="credit-card" id="{e(p['id'])}"><img src="{img}" alt="{e(v['name'])}">
<div><p class="study-id">{e(v['project'])}</p><h2>{e(v['name'])}</h2><p>{e(v['context'])}</p>
<p class="credit-line">{t('Photograph','摄影')} · {e(p['author'])} · <a href="{e(p['license_url'])}">{e(p['license'])}</a></p>
<p class="source-links"><a href="{e(p['source'])}">{t('Published image','图像原页')} ↗</a> <a href="{e(p['project_url'])}">{t('Genome project','项目主页')} ↗</a></p></div></article>''')
        self.shell('credits.html',title,intro+'<div class="frame credit-list">'+''.join(cards)+'</div>')

    def build(self):
        t=self.t
        self.browse('index.html',t('Dataset directory','资源目录'),'',self.records,True)
        for path,title,desc,tag in [
            ('population.html',t('Population datasets','群体数据'),t('Sequence and variant resources spanning populations, strains and breeds.','检索跨群体、品种和品系的测序与变异数据。'),'群体'),
            ('pedigree.html',t('Pedigree datasets','家系数据'),t('Sequenced families with documented parents, offspring or multigenerational pedigrees.','检索具有明确亲子关系或多代系谱的家系测序数据。'),'家系')]:
            self.browse(path,title,desc,[r for r in self.records if tag in r['design']])
        for r in self.records:self.detail(r)
        self.lab()
        self.credits()
        with (ROOT/self.tsv).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f,delimiter='\t',lineterminator='\n')
            w.writerow(FIELDS)
            w.writerows(self.fmt(r) for r in self.records)

if __name__=='__main__':
    records=load('catalog.json')
    photos=load('photos.json')
    for lang in ('en','zh'):
        Edition(lang,records,photos).build()
