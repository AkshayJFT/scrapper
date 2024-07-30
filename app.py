from flask import Flask, request, render_template, send_file
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    url = request.form['url']
    links = asyncio.run(extract_links(url))
    if links:
        # Create a CSV file in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Links'])
        for link in links:
            writer.writerow([link])
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='links.csv'
        )
    else:
        return 'Failed to extract links or no links found.'

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Request to {url} failed with status code {response.status}")
                return None
    except Exception as e:
        print(f"Request to {url} failed: {e}")
        return None

async def extract_links(url, depth=2, max_links=500):
    links = set()
    queue = [(url, 0)]

    async with aiohttp.ClientSession() as session:
        while queue and len(links) < max_links:
            current_url, current_depth = queue.pop(0)
            if current_depth > depth:
                continue

            html = await fetch(session, current_url)
            if not html:
                continue

            soup = BeautifulSoup(html, 'html.parser')
            page_links = [urljoin(current_url, a.get('href')) for a in soup.find_all('a', href=True)]
            for link in page_links:
                if link not in links:
                    links.add(link)
                    queue.append((link, current_depth + 1))
                    print(f"Found link: {link}")

    return list(links)

if __name__ == '__main__':
    app.run(debug=True)
