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
    HighlightJS(langs=['markdown'])
)
app = fast_app(hdrs=hdrs)
rt = app.route

setup_toasts(app)

js = '''
let cm = CodeMirror(me("#editor"), {
    mode: "htmlmixed", foldGutter: true, gutters: ["CodeMirror-foldgutter"]
})
function upd_editor() {
    htmx.ajax('POST', '/', {
        target:'#details', values: {editor: cm.getValue(), extractor: me("#extractor").value}
    });
}
cm.on("change", upd_editor);'''

def set_cm(s): return Script(f"cm.setValue({dumps(s)});", id='set_cm', hx_swap_oob='true')

@rt('/')
def get():
    samp = Path('samp.html').read_text()
    frm = Form(Group(
            Input(type='text', id='url', placeholder='url'),
            Select(Option("html2text", value="h2t", selected=True),
                Option("trafilatura", value="traf"),
                id="extractor", hx_on_change="upd_editor()"),
        Button('Load')),
        hx_post='/load', hx_swap='none')
    return Titled('web2md', frm, 
        A('Go to markdown', href='#details'),
        Div(id='editor'), Script(js), Div(id='details'), set_cm(samp))

@rt('/load')
def post(sess, url:str):
    if not url: return add_toast(sess, "Please enter a valid URL", "warning")
    body = lxml.html.fromstring(httpx.get(url).text).xpath('//body')[0]
    body = Cleaner(javascript=True, style=True).clean_html(body)
    return set_cm(''.join(lxml.html.tostring(c, encoding='unicode') for c in body))

def get_md(editor, extractor):
    if extractor=='traf':
        if '<article>' not in editor.lower(): editor = f'<article>{editor}</article>'
        res = extract(f'<html><body>{editor}</body></html>', output_format='markdown',
            favor_recall=True, include_tables=True, include_links=False, include_images=False, include_comments=True)
    else:
        h2t = HTML2Text(bodywidth=5000)
        h2t.ignore_links = True
        h2t.mark_code = True
        h2t.ignore_images = True
        res = h2t.handle(editor)
    def _f(m): return f'```\n{dedent(m.group(1))}\n```'
    return re.sub(r'\[code]\s*\n(.*?)\n\[/code]', _f, res or '', flags=re.DOTALL).strip()

@rt('/')
def post(editor: str, extractor:str): return Pre(Code(get_md(editor, extractor), lang='markdown'))

@rt('/api')
def post(editor: str, extractor:str='h2t'): return get_md(editor, extractor)

run_uv()
