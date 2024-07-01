from fasthtml.common import *
from fasthtml.js import HighlightJS
from html2text import HTML2Text
from textwrap import dedent
from bs4 import BeautifulSoup
from json import dumps,loads
from trafilatura import html2txt, extract
import httpx, bleach

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
                id="extractor"),
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
    soup = BeautifulSoup(httpx.get(url).text, 'html.parser')
    body = soup.find('body').decode_contents()
    tags = [
        'a', 'abbr', 'acronym', 'address', 'area', 'article', 'aside', 'audio', 'b', 'bdi', 'bdo', 'big', 
        'blockquote', 'br', 'caption', 'cite', 'code', 'col', 'colgroup', 'data', 'datalist', 'dd', 'del', 
        'details', 'dfn', 'div', 'dl', 'dt', 'em', 'figcaption', 'figure', 'footer', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'header', 'hr', 'i', 'img', 'ins', 'kbd', 'li', 'main', 'mark', 'nav', 'ol', 'p', 'pre', 'q', 'rp', 'rt', 
        'ruby', 's', 'samp', 'section', 'small', 'span', 'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 
        'th', 'thead', 'time', 'tr', 'u', 'ul', 'var', 'wbr'
    ]
    attr = {
        '*': ['class', 'id', 'style', 'title', 'role', 'data-*', 'aria-*', 'src', 'alt', 'href', 'target', 'rel',
              'width', 'height', 'type', 'name', 'value', 'placeholder', 'disabled', 'readonly', 'required', 'checked', 
              'selected', 'max', 'min', 'step', 'maxlength', 'pattern', 'for', 'rows', 'cols', 'colspan', 'rowspan', 
              'controls', 'loop', 'muted', 'autoplay', 'poster']}
    return bleach.clean(body, tags=tags, attributes=attr, strip=True).strip()

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
