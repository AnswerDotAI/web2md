from fasthtml.common import *
from fasthtml.js import HighlightJS
from html2text import HTML2Text
from textwrap import dedent
from json import dumps,loads
from trafilatura import html2txt, extract
from lxml.html.clean import Cleaner
import httpx, lxml
import re

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
)
app,rt = fast_app(hdrs=hdrs)

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
    gist_form = Form(Div(style='display: grid; grid-template-columns: 1fr auto; gap: 1em;')(
            Input(type='text', id='github_token', placeholder='GitHub Token', style='grid-column: 1;'),
            Button('Gist It', id='gist-button', style='grid-column: 2;', hx_post='/gistit', hx_vals='js:{cts: document.querySelector("#details pre code").textContent}')))
    return Titled('web2md', frm, Script(js), Div(id='details'), set_cm(samp), gist_form)

def get_body(url):
    body = lxml.html.fromstring(httpx.get(url).text).xpath('//body')[0]
    body = Cleaner(javascript=True, style=True).clean_html(body)
    return ''.join(lxml.html.tostring(c, encoding='unicode') for c in body)

@rt('/load')
def post(sess, url:str):
    if not url: return add_toast(sess, "Please enter a valid URL", "warning")
    return set_cm(get_body(url))

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
def post(cts: str='', url:str='', extractor:str='h2t'):
    if url: cts = get_body(url)
    return get_md(cts, extractor)


gist_js = '''
function gistIt() {
    let markdown = document.querySelector('#details pre code').textContent;

    // Create a temporary textarea element
    const tempTextArea = document.createElement('textarea');
    tempTextArea.value = markdown;
    document.body.appendChild(tempTextArea);

    // Select and copy the text
    tempTextArea.select();
    document.execCommand('copy');
    document.body.removeChild(tempTextArea);

    alert('Markdown copied to clipboard. You can now paste it into the Gist.');
    window.open('https://gist.github.com/', '_blank');
}
gistIt(); // Run the function as soon as it's defined
'''
@rt('/gistit')
def post(sess, cts:str, github_token:str = None):
    if github_token: sess['github_token'] = github_token
    github_token = sess.get('github_token', None)
    # simple automation if there is no token
    if not github_token:
        print(f"test! {cts}")
        return Script(gist_js)
    #Better automation if we have a token
    else:
        title = re.search(r'^(#{1,6})\s*(.+)', cts, re.MULTILINE)
        if title:
            heading = title.group(2).strip().lower().replace(' ', '_')
            filename = f"{heading}.md"
        else:
            return add_toast(sess, "No valid heading found for the gist title", "warning")

        # Prepare the gist payload
        payload = {"description": "Gist created from web2md",
                    "public": True,
                    "files": {filename: {"content": cts}}}

        headers = {"Authorization": f"token {github_token}",
                   "Accept": "application/vnd.github.v3+json"}

        # Send the request to create the gist
        response = httpx.post('https://api.github.com/gists', headers=headers, json=payload)

        if response.status_code == 201:
            gist_url = response.json().get('html_url')
            print(gist_url)
            return Script(f'window.open("{gist_url}", "_blank");')
        else:
            error_message = response.json().get('message', 'Failed to create gist')
            return add_toast(sess, error_message, "error")


serve()
