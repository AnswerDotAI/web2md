from fasthtml.common import *
from fasthtml.js import HighlightJS
from html2text import HTML2Text
from textwrap import dedent
from json import dumps,loads
from trafilatura import html2txt, extract
from lxml.html.clean import Cleaner
import httpx, lxml

cdn = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.1'
hdrs = (
    Script(src=f'{cdn}/codemirror.min.js'),
    Script(src=f'{cdn}/mode/xml/xml.min.js'),
    Script(src=f'{cdn}/mode/htmlmixed/htmlmixed.min.js'),
    Script(src=f'{cdn}/addon/fold/xml-fold.min.js'),
    Script(src=f'{cdn}/addon/fold/foldcode.min.js'),
    Script(src=f'{cdn}/addon/fold/foldgutter.min.js'),
    Link(rel='stylesheet', href=f'{cdn}/codemirror.min.css'),
    Link(rel='stylesheet', href=f'{cdn}/addon/fold/foldgutter.min.css'),
    Style('''.CodeMirror { height: auto; min-height: 100px; border: 1px solid #ddd; }
        pre { white-space: pre-wrap; }
        select { width: auto; min-width: max-content; padding-right: 2em; }'''),
    HighlightJS(langs=['markdown']),
    Style('''* { box-sizing: border-box; }
		html, body { width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; }
		body { font-family: system-ui, sans-serif; perspective: 1500px; background: linear-gradient(#666, #222); }'''),
)
app = FastHTML(hdrs=hdrs)
rt = app.route

setup_toasts(app)

js = '''let ed = me("#editor");
let cm = CodeMirror(ed, { mode: "htmlmixed", foldGutter: true, gutters: ["CodeMirror-foldgutter"] });
cm.on("change", _ => ed.send("edited"));'''

def set_cm(s): return run_js('cm.setValue({s});', s=s)

@rt('/')
def get():
    samp = Path('samp.html').read_text()
    ed_kw = dict(hx_post='/', target_id='details', hx_vals='js:{cts: cm.getValue()}')
    grp = Group(
            Input(type='text', id='url', value='https://example.org/'),
            Select(Option("html2text", value="h2t", selected=True),
                Option("trafilatura", value="traf"),
                id="extractor", **ed_kw),
            Button('Load', hx_swap='none', hx_post='/load'))
    frm = Form(grp, A('Go to markdown', href='#details'),
        Div(id='editor', **ed_kw, hx_trigger='edited delay:300ms, load delay:100ms'))
    return Titled('web2md', frm, Script(js), Div(id='details'), set_cm(samp))

@rt('/load')
def post(sess, url:str):
    if not url: return add_toast(sess, "Please enter a valid URL", "warning")
    body = lxml.html.fromstring(httpx.get(url).text).xpath('//body')[0]
    body = Cleaner(javascript=True, style=True).clean_html(body)
    return set_cm(''.join(lxml.html.tostring(c, encoding='unicode') for c in body))

def get_md(cts, extractor):
    if extractor=='traf':
        if '<article>' not in cts.lower(): cts = f'<article>{cts}</article>'
        res = extract(f'<html><body>{cts}</body></html>', output_format='markdown',
            favor_recall=True, include_tables=True, include_links=False, include_images=False, include_comments=True)
    else:
        h2t = HTML2Text(bodywidth=5000)
        h2t.ignore_links = True
        h2t.mark_code = True
        h2t.ignore_images = True
        res = h2t.handle(cts)
    def _f(m): return f'```\n{dedent(m.group(1))}\n```'
    return re.sub(r'\[code]\s*\n(.*?)\n\[/code]', _f, res or '', flags=re.DOTALL).strip()

@rt('/')
def post(cts: str, extractor:str): return Pre(Code(get_md(cts, extractor), lang='markdown'))

@rt('/api')
def post(cts: str, extractor:str='h2t'): return get_md(cts, extractor)

run_uv()
