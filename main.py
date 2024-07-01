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

js = '''window.cm = CodeMirror.fromTextArea(document.getElementById("editor"), {
    mode: "htmlmixed", foldGutter: true, gutters: ["CodeMirror-foldgutter"], viewportMargin: Infinity
});
cm.on("change", o => {
    o.save();
    o.getTextArea().dispatchEvent(new Event('change'));
});
function upd_editor(e) { cm.setValue(e.textContent); }
'''

@rt('/')
def get():
    samp = Path('samp.html').read_text()
    frm = Form(Group(
            Input(type='text', id='url', placeholder='url'),
            Select(Option("html2text", value="h2t", selected=True),
                Option("trafilatura", value="traf"),
                id="extractor", hx_on_change="htmx.trigger('#editor', 'change')"),
        Button('Load')),
        Hidden(id='hid_code', hx_on__after_swap='console.log(this); upd_editor(this)'),
        hx_post='/load', hx_target='#hid_code', hx_swap='textContent')
    trigger = "load delay:100ms, change delay:200ms"
    return Titled('web2md', frm, 
        A('Go to markdown', href='#details'),
        Textarea(samp, id='editor', hx_post='/',  hx_trigger=trigger, hx_target='#details', hx_include="#extractor"),
        Script(js), Div(id='details'))

@rt('/load')
def post(url:str):
    body = lxml.html.fromstring(httpx.get(url).text).xpath('//body')[0]
    body = Cleaner(javascript=True, style=True).clean_html(body)
    return ''.join(lxml.html.tostring(c, encoding='unicode') for c in body)

@rt('/')
def post(editor: str, extractor:str):
    if extractor=='traf':
        res = extract(editor, output_format='markdown', favor_recall=True, include_tables=True,
                      include_links=False, include_images=False, include_comments=True)
    else:
        h2t = HTML2Text(bodywidth=5000)
        h2t.ignore_links = True
        h2t.mark_code = True
        h2t.ignore_images = True
        res = h2t.handle(editor)
    def _f(m): return f'```\n{dedent(m.group(1))}\n```'
    res = re.sub(r'\[code]\s*\n(.*?)\n\[/code]', _f, res or '', flags=re.DOTALL)
    return Pre(Code(res.strip(), lang='markdown'))

run_uv()
