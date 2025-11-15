from flask import Flask, render_template, request
from archiver import WebPageArchiver

app = Flask(__name__)
archiver = WebPageArchiver('websites.db')

@app.route('/')
def index():
    query = request.args.get('query')
    if query:
        pages = [page for page in archiver.get_all_pages() if query.lower() in page['url'].lower()]
    else:
        pages = archiver.get_all_pages()
    return render_template('index.html', pages=pages)

@app.route('/site/<int:page_id>')
def site(page_id):
    page = archiver.get_page_by_id(page_id)
    history = archiver.get_version_history(page['url'])
    return render_template('site.html', page=page, history=history)

@app.route('/site/<int:page_id>/version/<int:version>')
def version(page_id, version):
    content = archiver.get_version_content(page_id, version)
    return content

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4444, debug=True)
