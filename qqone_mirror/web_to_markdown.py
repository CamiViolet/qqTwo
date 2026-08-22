"""
web_to_markdown.py - Common library for fetching and converting web page content.
"""

from datetime import datetime
import os
import re
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse

CONFLUENCE_HOST = 'confluence.tttech.com'


def fetch_confluence_page(url, username, password):
    """
    Fetches the content of a Confluence page and converts it to Markdown.
    Uses HTTPBasicAuth with credentials from environment variables.
    Returns: content : in markdown format
    """
    try:
        parsed = urlparse(url)
        if parsed.hostname != CONFLUENCE_HOST:
            raise ValueError(f"Refusing to send credentials to untrusted host: {parsed.hostname}")
        response = requests.get(url, auth=(username, password))
        response.raise_for_status()  # Raise an error for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        modified_on = _extract_modified_on(soup)

        # Extract the page title
        title = None
        title_tag = soup.find('title') or soup.find('h1', {'id': 'title-text'}) or soup.find('h1')
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Try to find the specific content div to avoid navigation menus
        content_div = soup.find('div', {'id': 'main-content'}) or \
                      soup.find('div', {'class': 'wiki-content'}) or \
                      soup.body

        if not content_div:
            return None
            
            

        content = f"\nsource: {url}"
        content += f"\ntitle: {title}"
        content += f"\nupdated: {modified_on}\n"
        content += _html_to_markdown(content_div)

        return content

    except Exception as e:
        print(f"Exception occurred: {e}")
    return None


def fetch_web_page(url):
    """
    Fetches the content of a web page and converts it to Markdown.
    Returns: content : in markdown format
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup.find_all('script'):
            script.decompose()
        content_div = soup.find('div', {'id': 'main-content'}) or \
                      soup.find('div', {'class': 'wiki-content'}) or \
                      soup.body
        if not content_div:
            return None

        return _html_to_markdown(content_div)

    except Exception as e:
        print(f"Exception occurred: {e}")
    return None


def normalize_date(date_str):
    """Convert 'Mar 20, 2026' to '20/03/2026'"""
    try:
        parsed_date = datetime.strptime(date_str, '%b %d, %Y')
        return parsed_date.strftime('%d/%m/%Y')
    except ValueError:
        return date_str  # Return original if parsing fails


def _extract_modified_on(soup):
    pattern = re.compile(r"modified on (\w+ \d{1,2}, \d{4})", re.IGNORECASE)    # Example: 'Mar 20, 2026'
    match = pattern.search(str(soup))
    if match:
        date = match.group(1)
        date = normalize_date(date)
        return date
    return None


def _html_to_markdown(element):
    """
    Recursively converts an HTML element to Markdown text.
    """
    result = []

    for child in element.children:
        if isinstance(child, NavigableString):
            text = str(child)
            if text.strip():
                result.append(text)
            continue

        if not isinstance(child, Tag):
            continue

        tag = child.name

        # Headings
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag[1])
            text = child.get_text(strip=True)
            if text:
                result.append(f"\n\n{'#' * level} {text}\n\n")

        # Paragraphs
        elif tag == 'p':
            text = _inline_markdown(child)
            if text.strip():
                result.append(f"\n\n{text}\n\n")

        # Unordered lists
        elif tag == 'ul':
            result.append('\n')
            for li in child.find_all('li', recursive=False):
                li_text = _inline_markdown(li)
                result.append(f"- {li_text.strip()}\n")
            result.append('\n')

        # Ordered lists
        elif tag == 'ol':
            result.append('\n')
            for i, li in enumerate(child.find_all('li', recursive=False), 1):
                li_text = _inline_markdown(li)
                result.append(f"{i}. {li_text.strip()}\n")
            result.append('\n')

        # Code blocks
        elif tag == 'pre':
            code = child.get_text()
            result.append(f"\n\n```\n{code}\n```\n\n")

        # Inline code
        elif tag == 'code':
            code = child.get_text()
            result.append(f"`{code}`")

        # Blockquotes
        elif tag == 'blockquote':
            text = child.get_text(strip=True)
            quoted = '\n'.join(f"> {line}" for line in text.split('\n'))
            result.append(f"\n\n{quoted}\n\n")

        # Tables
        elif tag == 'table':
            result.append(_table_to_markdown(child))

        # Horizontal rules
        elif tag == 'hr':
            result.append("\n\n---\n\n")

        # Line breaks
        elif tag == 'br':
            result.append("  \n")

        # Images
        elif tag == 'img':
            alt = child.get('alt', '')
            src = child.get('src', '')
            result.append(f"![{alt}]({src})")

        # Links
        elif tag == 'a':
            text = child.get_text(strip=True)
            href = child.get('href', '')
            if text and href:
                result.append(f"[{text}]({href})")
            elif text:
                result.append(text)

        # Divs and other containers — recurse
        else:
            result.append(_html_to_markdown(child))

    md = ''.join(result)
    # Clean up excessive blank lines
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md.strip()


def _inline_markdown(element):
    """
    Converts inline HTML elements (bold, italic, code, links) to Markdown.
    """
    result = []
    for child in element.children:
        if isinstance(child, NavigableString):
            result.append(str(child))
            continue
        if not isinstance(child, Tag):
            continue

        tag = child.name
        text = child.get_text()

        if tag in ('strong', 'b'):
            result.append(f"**{text}**")
        elif tag in ('em', 'i'):
            result.append(f"*{text}*")
        elif tag == 'code':
            result.append(f"`{text}`")
        elif tag == 'a':
            href = child.get('href', '')
            link_text = child.get_text(strip=True)
            if link_text and href:
                result.append(f"[{link_text}]({href})")
            else:
                result.append(link_text)
        elif tag == 'br':
            result.append("  \n")
        elif tag == 'img':
            alt = child.get('alt', '')
            src = child.get('src', '')
            result.append(f"![{alt}]({src})")
        else:
            result.append(_inline_markdown(child))

    return ''.join(result)


def _table_to_markdown(table):
    """
    Converts an HTML table to a Markdown table.
    """
    rows = []
    for tr in table.find_all('tr'):
        cells = []
        for td in tr.find_all(['td', 'th']):
            cell_text = _inline_markdown(td).replace('|', '\\|')
            cells.append(cell_text)
        rows.append(cells)

    if not rows:
        return ''

    md_lines = []
    # First row as header
    md_lines.append('| ' + ' | '.join(rows[0]) + ' |')
    md_lines.append('| ' + ' | '.join(['---'] * len(rows[0])) + ' |')
    # Remaining rows
    for row in rows[1:]:
        # Pad row if it has fewer cells than header
        while len(row) < len(rows[0]):
            row.append('')
        md_lines.append('| ' + ' | '.join(row) + ' |')

    return '\n\n' + '\n'.join(md_lines) + '\n\n'
