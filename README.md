# web2md

A web application that converts HTML content to Markdown with support for multiple extraction methods and GitHub Gist integration. It features a browser-based editor with syntax highlighting and code folding capabilities.

## Features

- HTML to Markdown conversion using multiple extractors:
  - html2text
  - trafilatura
- Live preview of converted Markdown
- CodeMirror-based HTML editor with syntax highlighting
- Direct URL content loading
- GitHub Gist integration with optional token storage
- REST API endpoint for programmatic access

## Dependencies

- fasthtml - Web framework and HTML components
- html2text - HTML to Markdown conversion
- trafilatura - Web content extraction
- httpx - HTTP client
- lxml - HTML processing
- CodeMirror 5.65.1 (via CDN) - Code editor
- highlight.js - Syntax highlighting

## Installation

1. Install the required Python packages:
```bash
pip install fasthtml html2text trafilatura httpx lxml
```

2. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:8000` by default.

## Usage

### Web Interface

The main interface (`/`) provides:
- URL input field for loading web content
- Extractor selection (html2text or trafilatura)
- HTML editor with syntax highlighting
- Live Markdown preview
- GitHub Gist integration

#### GitHub Gist Integration
- Optional GitHub token storage for automated Gist creation
- Automatic filename generation from first Markdown heading
- Public Gist creation with content and title

### API Endpoints

#### 1. Main Interface (`GET /`)
Returns the web interface with the HTML editor and conversion tools.

#### 2. HTML to Markdown Conversion (`POST /`)
Converts HTML content to Markdown.

**Parameters:**
- `cts` (string): HTML content
- `extractor` (string): Extraction method (`h2t` or `traf`)

**Returns:** Formatted Markdown content

#### 3. URL Content Loading (`POST /load`)
Loads HTML content from a specified URL.

**Parameters:**
- `url` (string): Target URL

**Returns:** HTML content for the editor

#### 4. API Endpoint (`POST /api`)
RESTful endpoint for programmatic HTML to Markdown conversion.

**Parameters:**
- `cts` (string, optional): HTML content
- `url` (string, optional): URL to fetch content from
- `extractor` (string, default='h2t'): Extraction method

**Returns:** Plain text Markdown content

#### 5. Gist Creation (`POST /gistit`)
Creates a GitHub Gist from the converted Markdown.

**Parameters:**
- `cts` (string): Markdown content
- `github_token` (string, optional): GitHub API token
- `save_token` (boolean): Whether to save the token for future use

**Returns:** Redirect to created Gist or clipboard copy script

## Extraction Methods

### html2text
- Ignores links and images
- Marks code blocks
- No width limiting (5000 characters)

### trafilatura
- Includes tables
- Excludes links and images
- Includes comments
- Higher recall for content extraction
- Requires article tags (automatically added if missing)

## Code Features

- Toast notifications for errors and warnings
- Session-based GitHub token storage
- Automatic code block formatting
- Responsive design with CSS Grid
- Delayed content updates for better performance
- CodeMirror integration with code folding

## Security Notes

- GitHub tokens are stored in the session if requested
- JavaScript and styles are cleaned from loaded HTML content
- External resources are loaded only from trusted CDNs

## Development

The application uses a modular structure with:
- Route handlers for different endpoints
- Utility functions for content processing
- Client-side JavaScript for editor integration
- Custom styling for improved usability

## Error Handling

- URL validation for content loading
- GitHub API error handling with user feedback
- Markdown heading validation for Gist creation
- Invalid token handling with fallback to manual clipboard copy
